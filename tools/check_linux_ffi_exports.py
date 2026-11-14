#!/usr/bin/env python3
"""Read-only cross-check of generated Dart FFI symbol references vs an ELF shared library.

Inspecting ELF using nm does not execute its code, but does not certify safety,
ABI type compatibility, plugin behavior, dependency provenance or release quality.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

from check_linux_ffi_bundle import APP, elf_header

SOURCE = APP / "packages/appflowy_backend/lib/ffi.dart"
LITERAL_LOOKUP = re.compile(r"lookupFunction<[^;]*?>\(\s*'([^']+)'\s*\)", re.S)
KNOWN = frozenset({
    "async_event", "sync_event", "init_sdk", "set_stream_port",
    "set_log_stream_port", "link_me_please",
    "store_dart_post_cobject", "rust_log", "set_env",
})


def required_exports(source: Path) -> list[str]:
    if source.is_symlink() or not source.is_file():
        raise ValueError("Dart FFI source is missing or a symlink")
    text = source.read_text(encoding="utf-8")
    found = sorted(set(LITERAL_LOOKUP.findall(text)))
    if not found or len(found) != len(LITERAL_LOOKUP.findall(text)):
        raise ValueError("unexpected duplicate or absent Dart FFI symbol references")
    return found


def parse_dynamic_exports(nm_output: str) -> set[str]:
    exports = set()
    for line in nm_output.splitlines():
        fields = line.split()
        if len(fields) < 2:
            continue
        # Be defensive even if nm's --defined-only option is unsupported.
        if fields[-2].upper() == "U":
            continue
        symbol = fields[-1].split("@", 1)[0]
        if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", symbol):
            exports.add(symbol)
    return exports


def verify(library: Path, required: list[str]) -> dict:
    if library.is_symlink() or not library.is_file() or library.stat().st_size > 500_000_000:
        raise ValueError("library must be a regular, bounded ELF file, not a symlink")
    good, detail = elf_header(library, shared=True)
    if not good:
        raise ValueError(f"invalid x86_64 shared library: {detail}")
    nm = shutil.which("nm")
    if not nm:
        raise RuntimeError("nm must be installed for dynamic-symbol inspection")
    try:
        process = subprocess.run(
            [nm, "--dynamic", "--defined-only", "--", str(library.resolve())],
            capture_output=True, text=True, timeout=15, check=False,
            env={"PATH": "/usr/bin:/bin", "LC_ALL": "C"},
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("native symbol read timed out") from exc
    if process.returncode:
        raise RuntimeError("nm could not inspect the shared library")
    defined = parse_dynamic_exports(process.stdout)
    missing = sorted(set(required) - defined)
    return {
        "status": "required_exports_present" if not missing else "missing_exports",
        "required_count": len(required),
        "missing": missing,
        "release_verified": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=SOURCE)
    parser.add_argument("--library", type=Path, help="optional built ELF64 x86_64 shared library")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        required = required_exports(args.source)
        if set(required) != KNOWN:
            raise ValueError("Dart FFI ABI changed; review the expected dynamic exports")
        report = {"scope": "read-only Dart-to-Linux C FFI export inspection",
                  "required": required, "release_verified": False}
        if args.library is not None:
            report["library"] = verify(args.library, required)
            ok = report["library"]["status"] == "required_exports_present"
        else:
            report["library"] = {"status": "not_checked"}
            ok = True
    except (ValueError, RuntimeError, OSError) as exc:
        print(f"FFI export inspection failed: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2) if args.json else f"FFI exports: {report['library']['status']} ({len(required)} required)")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
