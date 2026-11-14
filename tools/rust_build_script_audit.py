#!/usr/bin/env python3
"""Offline, read-only first-party Rust build.rs review gate.

This narrow inventory does not inspect transitive crates or the functions
called by build scripts, and never executes Cargo, Rust or build scripts.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / ".goreecloud/rust-build-script-inventory.json"
CRATES = ROOT / "frontend/rust-lib"
REQUIRED = {
    "dart-ffi", "flowy-ai", "flowy-database2", "flowy-date", "flowy-document",
    "flowy-error", "flowy-folder", "flowy-notification", "flowy-search",
    "flowy-storage", "flowy-user",
}
ALLOWED_CALLS = {
    "flowy_codegen::protobuf_file::dart_gen",
    "flowy_codegen::dart_event::r#gen",
}
CALL_PATTERN = re.compile(r"flowy_codegen::[a-z_]+::(?:r#)?[a-z_]+")
DANGEROUS = re.compile(
    r"std\s*::\s*(?:process|net|fs)|Command\s*::|include\s*!|"
    r"\bunsafe\b|(?:reqwest|ureq|TcpStream|UdpSocket|curl|wget)\b|"
    r"env\s*::\s*var|std\s*::\s*env"
)

class BuildScriptError(ValueError):
    pass

def examine_source(source: str) -> list[str]:
    # Strip single-line comments for the limited inherited-script grammar.
    lines = [line.split("//", 1)[0] for line in source.splitlines()]
    code = "\n".join(lines)
    if code.count("fn main()") != 1:
        raise BuildScriptError("build script must retain one reviewed main entrypoint")
    if DANGEROUS.search(code) or "/*" in code or "*/" in code:
        raise BuildScriptError("build script now contains unreviewed executable/sensitive syntax")
    calls = CALL_PATTERN.findall(code)
    if not calls or set(calls) - ALLOWED_CALLS:
        raise BuildScriptError("build script invokes an unreviewed code generator")
    if re.search(r"\b(?:mod|extern|use|macro_rules|include_str)\b", code):
        raise BuildScriptError("build script imports external/unreviewed code")
    return calls

def actual(root: Path) -> list[dict]:
    scripts = sorted((root / "frontend/rust-lib").rglob("build.rs"))
    records = []
    for path in scripts:
        if not path.is_file() or path.is_symlink():
            raise BuildScriptError(f"invalid Rust build script: {path}")
        rel = path.relative_to(root).as_posix()
        data = path.read_bytes()
        text = data.decode("utf-8")
        calls = examine_source(text)
        records.append({
            "path": rel,
            "sha256": hashlib.sha256(data).hexdigest(),
            "calls": calls,
        })
    return records

def verify(records: list[dict], baseline: dict) -> None:
    if baseline.get("schema") != 1 or baseline.get("scope") != "first-party-rust-build-rs-only":
        raise BuildScriptError("unexpected Rust script baseline schema")
    expected = baseline.get("scripts")
    if not isinstance(expected, list) or len(expected) != 11:
        raise BuildScriptError("incomplete reviewed Rust script baseline")
    expected_paths = sorted(
        f"frontend/rust-lib/{name}/build.rs" for name in REQUIRED
    )
    baseline_paths = [r.get("path") for r in expected if isinstance(r, dict)]
    if baseline_paths != expected_paths:
        raise BuildScriptError("unreviewed or missing baseline build scripts")
    if records != expected:
        raise BuildScriptError("Rust build script added, removed or changed; review and rebaseline")
    for item in records:
        if not re.fullmatch(r"[0-9a-f]{64}", item["sha256"]):
            raise BuildScriptError("malformed script digest")

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("verify", "report"))
    args = parser.parse_args()
    try:
        records = actual(ROOT)
        if args.mode == "report":
            print(json.dumps({"scope": "first-party-only; no code executed",
                              "scripts": records}, indent=2))
        else:
            verify(records, json.loads(BASE.read_text(encoding="utf-8")))
            print(f"PASS {len(records)} reviewed first-party Rust build.rs files unchanged")
    except (BuildScriptError, OSError, UnicodeError, ValueError) as exc:
        print(f"FAIL Rust build script audit: {exc}", file=sys.stderr)
        return 1
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
