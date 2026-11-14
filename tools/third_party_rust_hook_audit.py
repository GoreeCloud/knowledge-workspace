#!/usr/bin/env python3
"""Offline, read-only Cargo.lock-to-crate-archive build-hook provenance audit.

Does not execute third-party code, network requests, package managers, scripts,
proc macros, or hooks. Source authenticity is bounded by Cargo.lock checksums;
neither lockfile provenance nor security of source contents is certified.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import sys
import tarfile
import tomllib
from pathlib import Path

DEFAULT_LOCK = Path(__file__).resolve().parents[1] / "frontend/rust-lib/Cargo.lock"
REGISTRY_SOURCE = "registry+https://github.com/rust-lang/crates.io-index"
CHECKSUM = re.compile(r"[0-9a-f]{64}\Z")
CRATE_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,127}\Z")
CRATE_VERSION = re.compile(r"[0-9][A-Za-z0-9.+-]{0,127}\Z")
MAX_ARCHIVE = 250_000_000
MAX_MANIFEST = 500_000
MAX_HOOK = 750_000
INDICATORS = {
    "process_invocation": re.compile(r"(?:std::process::Command|Command::new\s*\(|\.command\s*\()", re.I),
    "network_or_download_text": re.compile(r"\b(?:curl|wget|git\s+clone|https?://|reqwest|ureq|download|fetch_url)\b", re.I),
    "filesystem_write": re.compile(r"(?:std::fs::write|File::create|create_dir|write_all|fs::copy|fs::remove_|remove_file|remove_dir)", re.I),
    "native_toolchain": re.compile(r"(?:cc::Build|cmake::Config|bindgen::Builder|pkg_config::|vcpkg::)", re.I),
}

class AuditError(ValueError):
    pass


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def bounded_regular(path: Path, limit: int) -> bytes:
    if path.is_symlink() or not path.is_file():
        raise AuditError("missing, non-regular or symlinked file: " + path.name)
    if path.stat().st_size > limit:
        raise AuditError("oversized file: " + path.name)
    return path.read_bytes()


def locked_registry_packages(path: Path) -> dict[tuple[str, str], str]:
    doc = tomllib.loads(bounded_regular(path, 15_000_000).decode("utf-8"))
    items = {}
    for entry in doc["package"]:
        source = entry.get("source", "")
        if not source.startswith("registry+"):
            continue
        if source != REGISTRY_SOURCE:
            raise AuditError("unreviewed registry origin")
        name, version, checksum = entry["name"], entry["version"], entry.get("checksum", "")
        if (not isinstance(name, str) or not CRATE_NAME.fullmatch(name)
                or not isinstance(version, str) or not CRATE_VERSION.fullmatch(version)
                or ".." in version):
            raise AuditError("unsafe registry package path component")
        if not CHECKSUM.fullmatch(checksum):
            raise AuditError("missing registry archive checksum")
        key = (name, version)
        if key in items:
            raise AuditError("duplicate registry package name/version")
        items[key] = checksum
    if not items:
        raise AuditError("no registry packages in lockfile")
    return items


def safe_hook_path(value: object) -> str | None:
    if value is False:
        return None
    if value is None or value is True:
        return "build.rs"
    if not isinstance(value, str) or not value or len(value) > 180:
        raise AuditError("invalid custom build hook declaration")
    # Cargo-normalized manifests commonly spell a legitimate relative path
    # "./build.rs". Remove only that single prefix, never resolve '..'.
    if value.startswith("./"):
        value = value[2:]
    parts = value.split("/")
    if any(x in ("", ".", "..") for x in parts) or "\\" in value or value.startswith("/"):
        raise AuditError("unsafe build hook path")
    return value


def safe_cached_member(directory: Path, relative: str) -> Path:
    path = directory
    for part in relative.split("/"):
        path = path / part
        if path.is_symlink():
            raise AuditError("source path includes symlink")
    if not path.resolve().is_relative_to(directory.resolve()):
        raise AuditError("source path escapes cached crate")
    return path


def archive_member_bytes(tar: tarfile.TarFile, name: str, limit: int) -> bytes:
    try:
        member = tar.getmember(name)
    except KeyError as exc:
        raise AuditError("source missing from checksum-verified crate archive") from exc
    if not member.isfile() or member.size > limit:
        raise AuditError("archive member not a bounded regular file")
    handle = tar.extractfile(member)
    if handle is None:
        raise AuditError("unreadable archive member")
    with handle:
        data = handle.read(limit + 1)
    if len(data) != member.size or len(data) > limit:
        raise AuditError("archive member size mismatch")
    return data


def audit(lock: Path, source_root: Path | None, archive_root: Path | None, strict: bool = False) -> dict:
    locked = locked_registry_packages(lock)
    report = {
        "schema": "gc.third-party-rust-build-hook-audit.v1",
        "scope": "read-only exact Cargo.lock registry packages; no execution or security certification",
        "locked_registry_packages": len(locked),
        "cache_inspected": source_root is not None,
        "source_verified_against_locked_archive": 0,
        "sources_absent": 0,
        "archives_absent": 0,
        "build_scripts": 0,
        "proc_macro_crates": 0,
        "indicator_counts": {key: 0 for key in INDICATORS},
        "entries": [],
        "missing": [],
        "unverified": [],
        "full_security_review_complete": False,
    }
    if source_root is None:
        if strict:
            raise AuditError("strict audit requires source and archive directories")
        report["status"] = "lock_only_source_not_inspected"
        return report
    if archive_root is None:
        raise AuditError("source inspection requires registry archive cache")
    if source_root.is_symlink() or archive_root.is_symlink() or not source_root.is_dir() or not archive_root.is_dir():
        raise AuditError("source/archive roots must be regular directories, not symlinks")
    for (name, version), expected in sorted(locked.items()):
        label = f"{name}-{version}"
        directory = source_root / label
        archive = archive_root / (label + ".crate")
        if not directory.exists():
            report["sources_absent"] += 1
            report["missing"].append(label)
            continue
        if directory.is_symlink() or not directory.is_dir():
            raise AuditError("locked source directory replaced by symlink/non-directory: " + label)
        if not archive.exists():
            report["archives_absent"] += 1
            report["unverified"].append(label)
            continue
        content = bounded_regular(archive, MAX_ARCHIVE)
        if digest(content) != expected:
            raise AuditError("locked archive SHA-256 mismatch: " + label)
        manifest = bounded_regular(directory / "Cargo.toml", MAX_MANIFEST)
        try:
            doc = tomllib.loads(manifest.decode("utf-8"))
            manifest_name = doc["package"]["name"]
            manifest_version = doc["package"]["version"]
        except (ValueError, KeyError, UnicodeDecodeError) as exc:
            raise AuditError("source manifest unreadable: " + label) from exc
        if (manifest_name, manifest_version) != (name, version):
            raise AuditError("source package identity mismatch: " + label)
        try:
            hook_name = safe_hook_path(doc["package"].get("build"))
        except AuditError as exc:
            raise AuditError(f"{label}: {exc}") from exc
        is_proc_macro = doc.get("lib", {}).get("proc-macro") is True
        hook_path = safe_cached_member(directory, hook_name) if hook_name else None
        has_hook = hook_path is not None and hook_path.is_file()
        if doc["package"].get("build") not in (None, False) and not has_hook:
            raise AuditError("declared build hook absent from source: " + label)
        macro_path = (safe_hook_path(doc.get("lib", {}).get("path", "src/lib.rs"))
                      if is_proc_macro else None)
        record = {"package": name, "version": version, "build_hook": None, "proc_macro": is_proc_macro}
        with tarfile.open(fileobj=io.BytesIO(content), mode="r:gz") as tar:
            if archive_member_bytes(tar, f"{label}/Cargo.toml", MAX_MANIFEST) != manifest:
                raise AuditError("source Cargo.toml differs from locked archive: " + label)
            if hook_name:
                archive_hook_present = False
                try:
                    tar.getmember(f"{label}/{hook_name}")
                    archive_hook_present = True
                except KeyError:
                    pass
                if archive_hook_present != has_hook:
                    raise AuditError("cached build hook presence differs from locked archive: " + label)
            if has_hook:
                source = bounded_regular(hook_path, MAX_HOOK)
                archived = archive_member_bytes(tar, f"{label}/{hook_name}", MAX_HOOK)
                if source != archived:
                    raise AuditError("source build hook differs from locked archive: " + label)
                indicators = sorted(k for k, rx in INDICATORS.items() if rx.search(source.decode("utf-8", "replace")))
                record["build_hook"] = {
                    "path": hook_name,
                    "sha256": digest(source),
                    "bytes": len(source),
                    "indicators": indicators,
                }
                report["build_scripts"] += 1
                for flag in indicators:
                    report["indicator_counts"][flag] += 1
            if is_proc_macro:
                macro_source = bounded_regular(safe_cached_member(directory, macro_path), MAX_HOOK)
                macro_archive = archive_member_bytes(tar, f"{label}/{macro_path}", MAX_HOOK)
                if macro_source != macro_archive:
                    raise AuditError("proc-macro entry source differs from locked archive: " + label)
                record["proc_macro_entry"] = {
                    "path": macro_path,
                    "sha256": digest(macro_source),
                    "bytes": len(macro_source),
                }
        if is_proc_macro:
            report["proc_macro_crates"] += 1
        if has_hook or is_proc_macro:
            report["entries"].append(record)
        report["source_verified_against_locked_archive"] += 1
    report["status"] = ("complete_cache_provenance_verified" if
                        report["source_verified_against_locked_archive"] == len(locked)
                        else "partial_cache_provenance_verified")
    if strict and report["status"] != "complete_cache_provenance_verified":
        raise AuditError("strict audit requires complete verified source and archive coverage")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lock", type=Path, default=DEFAULT_LOCK)
    parser.add_argument("--source-root", type=Path)
    parser.add_argument("--archive-root", type=Path)
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        result = audit(args.lock, args.source_root, args.archive_root, args.strict)
    except (AuditError, OSError, EOFError, tarfile.TarError, ValueError) as exc:
        print(f"Rust hook provenance audit failed: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(result, sort_keys=True, indent=2))
    else:
        print("Rust registry hooks: locked={locked_registry_packages}, archives_verified={source_verified_against_locked_archive}, missing={sources_absent}, build_scripts={build_scripts}, proc_macros={proc_macro_crates}, status={status}".format(**result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
