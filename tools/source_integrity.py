#!/usr/bin/env python3
"""Offline source-snapshot integrity verification, not a security certification.

The reviewed baseline records bytes for all upstream-tracked AppFlowy files as
imported into this repository. Changes to those files require explicit checksum
review and update; new GoreeCloud-owned files may be added independently.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / ".goreecloud/upstream-source-digests.json"
HEXDIGEST = re.compile(r"[0-9a-f]{64}\Z")


class IntegrityError(Exception):
    """Unverifiable or changed source snapshot."""


def safe_path(value: str) -> str:
    if not isinstance(value, str) or not value or "\\" in value or "\0" in value:
        raise IntegrityError("manifest has an invalid source path")
    if value.startswith("/") or any(x in ("", ".", "..") for x in value.split("/")):
        raise IntegrityError(f"manifest contains a non-normalized source path: {value!r}")
    if ":" in value.split("/")[0]:
        raise IntegrityError("manifest contains a drive-relative source path")
    return value


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()


def checked_file(root: Path, relative: str) -> Path:
    path = root / safe_path(relative)
    if path.is_symlink() or not path.is_file():
        raise IntegrityError(f"missing, nonregular or symlinked upstream file: {relative}")
    if not path.resolve().is_relative_to(root.resolve()):
        raise IntegrityError(f"source file escaped repository root: {relative}")
    return path


def verify(root: Path, manifest: dict) -> tuple[int, int]:
    meta = manifest.get("upstream", {})
    if meta.get("repository") != "https://github.com/AppFlowy-IO/AppFlowy":
        raise IntegrityError("source repository provenance changed")
    if meta.get("revision") != "8fcee27d9bd93aad4ee0191d5d8d915d6a9a4e93":
        raise IntegrityError("upstream revision differs from pinned baseline")
    entries = manifest.get("files")
    if not isinstance(entries, list) or len(entries) != 4597:
        raise IntegrityError("upstream inventory is incomplete or invalid")
    sources, destinations, changed = set(), set(), 0
    for record in entries:
        if not isinstance(record, dict):
            raise IntegrityError("invalid inventory record")
        source = safe_path(record.get("source_path"))
        destination = safe_path(record.get("import_path"))
        if source in sources or destination in destinations:
            raise IntegrityError("duplicate source/destination in inventory")
        sources.add(source)
        destinations.add(destination)
        up_hash = record.get("upstream_sha256")
        import_hash = record.get("import_sha256")
        if (not isinstance(up_hash, str) or not HEXDIGEST.fullmatch(up_hash)
                or not isinstance(import_hash, str) or not HEXDIGEST.fullmatch(import_hash)):
            raise IntegrityError(f"invalid checksums: {source}")
        if source == "README.md" and destination != "UPSTREAM_README.md":
            raise IntegrityError("original upstream README attribution path changed")
        if source.startswith(".github/workflows/"):
            expected = ".github/upstream-workflows-disabled/" + source.split("/", 3)[-1]
            if destination != expected:
                raise IntegrityError("original release automation moved into active workflows")
        if import_hash != up_hash:
            changed += 1
        actual = digest(checked_file(root, destination))
        if actual != import_hash:
            raise IntegrityError(
                f"unexpected content drift: {destination}\n"
                "Review the change and explicitly refresh its recorded import checksum."
            )
    if len(sources) != 4597:
        raise IntegrityError("source count mismatch")
    return len(entries), changed


def refresh(root: Path, manifest: dict, approved_paths: list[str]) -> int:
    """Explicitly record reviewed changes in specific, already imported files."""
    inventory = {x["import_path"]: x for x in manifest["files"]}
    updated = 0
    for raw in approved_paths:
        path = safe_path(raw)
        if path not in inventory:
            raise IntegrityError(f"not an upstream-tracked import: {path}")
        if path in ("LICENSE", "UPSTREAM_README.md") or path.startswith(
            ".github/upstream-workflows-disabled/"
        ):
            raise IntegrityError(f"protected upstream attribution/automation: {path}")
        new_hash = digest(checked_file(root, path))
        inventory[path]["import_sha256"] = new_hash
        updated += 1
    return updated


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("verify", "refresh"))
    parser.add_argument("--path", action="append", default=[], help="reviewed repository path for refresh")
    args = parser.parse_args()
    try:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        if args.mode == "verify":
            if args.path:
                raise IntegrityError("--path is only valid with refresh")
            files, changed = verify(ROOT, manifest)
            print(f"PASS {files} upstream files match the reviewed import digests; {changed} differ from upstream by recorded GoreeCloud changes.")
        else:
            if not args.path:
                raise IntegrityError("refresh requires an explicit --path for each reviewed file")
            updated = refresh(ROOT, manifest, args.path)
            MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            print(f"Recorded {updated} explicitly reviewed source file digest(s). Review the manifest diff before committing.")
        return 0
    except (IntegrityError, OSError, ValueError, KeyError, TypeError) as e:
        print(f"FAIL source integrity: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
