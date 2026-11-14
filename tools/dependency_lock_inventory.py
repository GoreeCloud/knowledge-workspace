#!/usr/bin/env python3
"""Offline checks of source identities in the imported Dart and Rust lockfiles.

Only parses lockfile metadata. No network, dependency acquisition or code execution.
"""
from __future__ import annotations
import argparse
import collections
import json
import re
import sys
import tomllib
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
DART = ROOT / "frontend/appflowy_flutter"
RUST = ROOT / "frontend/rust-lib"
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
SHA40 = re.compile(r"[0-9a-f]{40}\Z")
REF = re.compile(r"[0-9a-f]{7,40}\Z")
NAME = re.compile(r"[a-zA-Z_][a-zA-Z0-9_]*\Z")
DART_EXPECTED = {"hosted":294, "git":15, "path":8, "sdk":9}
RUST_EXPECTED = {"registry":768, "git":24, "path":31}
REVIEWED_RUST_GIT = {
    "https://github.com/AppFlowy-IO/AppFlowy-Cloud",
    "https://github.com/AppFlowy-IO/AppFlowy-Collab",
    "https://github.com/appflowy/langchain-rust",
    "https://github.com/rust-rocksdb/rust-rocksdb",
}

class LockError(ValueError):
    pass

def clean_value(s: str) -> str:
    value = s.strip().strip("'\"")
    if not value or "\n" in value:
        raise LockError("empty or invalid lockfile scalar")
    return value

def attribute(block: str, indent: int, name: str) -> str:
    hits = re.findall(r"(?m)^" + " " * indent + re.escape(name) +
                      r":\s*(.*?)\s*$", block)
    if len(hits) != 1:
        raise LockError(f"missing or duplicated {name} lockfile field")
    return clean_value(hits[0])

def parse_dart_packages(text: str) -> dict[str,str]:
    if text.count("\npackages:\n") != 1 or text.count("\nsdks:\n") != 1:
        raise LockError("unexpected Flutter lockfile package/sdk structure")
    raw = text.split("\npackages:\n",1)[1].split("\nsdks:\n",1)[0]
    chunks = re.split(r"(?m)(?=^  [A-Za-z_][A-Za-z0-9_]*:\s*$)",raw)
    result: dict[str,str] = {}
    for chunk in chunks:
        m = re.match(r"^  ([A-Za-z_][A-Za-z0-9_]*):\n", chunk)
        if not m:
            if chunk.strip(): raise LockError("unexpected Flutter package block")
            continue
        name = m.group(1)
        if name in result:
            raise LockError(f"duplicate Dart package: {name}")
        source = attribute(chunk,4,"source")
        if source not in DART_EXPECTED:
            raise LockError(f"unexpected Dart package source: {name}")
        attribute(chunk,4,"version")
        if source == "hosted":
            if attribute(chunk,6,"name") != name:
                raise LockError(f"hosted package identity changed: {name}")
            if attribute(chunk,6,"url") != "https://pub.dev":
                raise LockError(f"unexpected hosted repository: {name}")
            if not SHA256.fullmatch(attribute(chunk,6,"sha256")):
                raise LockError(f"hosted checksum missing or invalid: {name}")
        elif source == "git":
            url = urlsplit(attribute(chunk,6,"url"))
            if (url.scheme != "https" or url.hostname != "github.com" or
                    url.username or url.password or url.query or url.fragment or
                    not re.fullmatch(r"/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+",url.path)):
                raise LockError(f"Git origin requires review: {name}")
            if not SHA40.fullmatch(attribute(chunk,6,"resolved-ref")):
                raise LockError(f"Git resolved commit invalid: {name}")
            requested = attribute(chunk,6,"ref")
            if not REF.fullmatch(requested):
                raise LockError(f"Git ref is floating or malformed: {name}")
            if not attribute(chunk,6,"resolved-ref").startswith(requested):
                raise LockError(f"Git requested and locked commits disagree: {name}")
            subpath = attribute(chunk,6,"path")
            if not safe_subpath(subpath):
                raise LockError(f"Git package path unsafe: {name}")
        elif source == "path":
            if attribute(chunk,6,"relative") != "true":
                raise LockError(f"local Dart package must be relative: {name}")
            subpath = attribute(chunk,6,"path")
            if not safe_subpath(subpath):
                raise LockError(f"local Dart package path unsafe: {name}")
            package = DART / subpath
            if not package.is_dir() or package.is_symlink() or not (package/"pubspec.yaml").is_file():
                raise LockError(f"local Dart package missing: {name}")
        elif source == "sdk":
            if attribute(chunk,4,"description") not in {"dart","flutter"}:
                raise LockError(f"unexpected Dart SDK package: {name}")
        result[name] = source
    if dict(collections.Counter(result.values())) != DART_EXPECTED:
        raise LockError("Dart lockfile source counts changed; review required")
    return result

def safe_subpath(value: str) -> bool:
    return bool(value and not value.startswith("/") and "\\" not in value and
                all(c not in {"..",""} for c in value.split("/")) and
                not any(ord(c) < 32 for c in value))

def parse_rust_packages(text: str) -> dict[str,int]:
    lock = tomllib.loads(text)
    if lock.get("version") != 4 or not isinstance(lock.get("package"),list):
        raise LockError("unsupported Rust Cargo.lock format")
    counts: collections.Counter[str] = collections.Counter()
    seen = set()
    for pkg in lock["package"]:
        name,version = pkg.get("name"),pkg.get("version")
        if not isinstance(name,str) or not name or not isinstance(version,str) or not version:
            raise LockError("unnamed or versionless Rust package")
        source = pkg.get("source")
        identity = (name,version,source)
        if identity in seen: raise LockError(f"duplicate Rust lock package: {name}")
        seen.add(identity)
        if source is None:
            counts["path"] += 1
        elif source == "registry+https://github.com/rust-lang/crates.io-index":
            counts["registry"] += 1
            if not SHA256.fullmatch(str(pkg.get("checksum",""))):
                raise LockError(f"missing registry checksum: {name}")
        elif isinstance(source,str) and source.startswith("git+"):
            counts["git"] += 1
            url = urlsplit(source[4:])
            canonical=f"{url.scheme}://{url.netloc}{url.path}"
            if canonical not in REVIEWED_RUST_GIT or url.username or url.password:
                raise LockError(f"unreviewed Rust Git source: {name}")
            if not SHA40.fullmatch(url.fragment):
                raise LockError(f"Rust Git commit invalid: {name}")
            if not re.fullmatch(r"(?:rev|branch)=[a-zA-Z0-9_.-]+",url.query):
                raise LockError(f"invalid Rust Git source query: {name}")
            if url.query.startswith("rev=") and not url.fragment.startswith(url.query[4:]):
                raise LockError(f"Rust Git request does not match locked commit: {name}")
        else:
            raise LockError(f"unreviewed Cargo lock package source: {name}")
    if dict(counts) != RUST_EXPECTED:
        raise LockError("Rust lockfile source counts changed; review required")
    return dict(counts)

def report(dart_text: str,rust_text: str) -> dict:
    dart = parse_dart_packages(dart_text)
    rust = parse_rust_packages(rust_text)
    return {"classification":"source metadata only—not a source-code audit or complete SBOM",
            "dart":{"total":len(dart),"source_counts":dict(sorted(collections.Counter(dart.values()).items()))},
            "rust":{"total":sum(rust.values()),"source_counts":dict(sorted(rust.items()))},
            "assurance":"lockfile identifiers and digests are present; archives, licenses, build scripts and runtime not verified"}

def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode",choices=("verify","report"))
    args=p.parse_args()
    try:
        x=report((DART/"pubspec.lock").read_text(),(RUST/"Cargo.lock").read_text())
        if args.mode=="report": print(json.dumps(x,indent=2))
        else: print(f"PASS {x['dart']['total']} Flutter and {x['rust']['total']} Rust source records checked offline (metadata only)")
    except (LockError,ValueError,OSError,tomllib.TOMLDecodeError) as exc:
        print(f"FAIL dependency lock inventory: {exc}",file=sys.stderr)
        return 1
    return 0
if __name__=="__main__":
    raise SystemExit(main())
