#!/usr/bin/env python3
"""Read-only missing generated Dart and Rust-backend source preflight.

This intentionally does not generate, download, execute, or modify anything.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "frontend/appflowy_flutter"
DIRECTIVE = re.compile(r"(?m)^[ \t]*(import|export|part)[ \t]+['\"]([^'\"]+)['\"]")
GEN_SUFFIXES = (".g.dart", ".freezed.dart", ".pb.dart", ".pbenum.dart", ".pbjson.dart", ".pbserver.dart")
OTHER_GEN_PATHS = ("/dart_event/", "/protobuf/", "/generated/")


def source_modules(root: Path) -> dict[str, Path]:
    result = {"appflowy": root / "lib"}
    packages = root / "packages"
    if packages.is_dir() and not packages.is_symlink():
        for package in packages.iterdir():
            if (package.is_dir() and not package.is_symlink()
                    and (package / "pubspec.yaml").is_file()
                    and (package / "lib").is_dir()):
                result[package.name] = package / "lib"
    return result


def classify_generated(uri: str, directive: str) -> str | None:
    if not uri.endswith(".dart") or not (
        uri.endswith(GEN_SUFFIXES) or
        "/dart_event/" in f"/{uri}" or
        "/generated/" in f"/{uri}" or
        "/protobuf/" in f"/{uri}"
    ):
        return None
    if "locale_keys.g.dart" in uri or "codegen_loader.g.dart" in uri:
        return "localization"
    if "flowy_svgs.g.dart" in uri:
        return "svg"
    if "protobuf/" in uri or uri.endswith((".pb.dart", ".pbenum.dart", ".pbjson.dart", ".pbserver.dart")):
        return "rust_protobuf"
    if "dart_event/" in uri:
        return "rust_dispatch"
    if uri.endswith(".freezed.dart"):
        return "freezed"
    if directive == "part" or uri.endswith(".g.dart"):
        return "dart_generated"
    return "other_generated"


def generated_report(root: Path) -> dict:
    modules = source_modules(root)
    file_count = 0
    missing: dict[str, set[str]] = {}
    unsafe: set[str] = set()
    root_resolved = root.resolve()
    for package_root in modules.values():
        if not package_root.is_dir() or package_root.is_symlink():
            continue
        for source in package_root.rglob("*.dart"):
            if not source.is_file() or source.is_symlink():
                continue
            file_count += 1
            for directive, uri in DIRECTIVE.findall(source.read_text(encoding="utf-8", errors="replace")):
                category = classify_generated(uri, directive)
                if not category:
                    continue
                if uri.startswith("package:"):
                    rest = uri.removeprefix("package:")
                    package, separator, rel = rest.partition("/")
                    if not separator or package not in modules:
                        continue
                    target = modules[package] / rel
                elif ":" in uri or uri.startswith("/"):
                    continue
                else:
                    target = source.parent / uri
                absolute = target.resolve()
                if not absolute.is_relative_to(root_resolved):
                    unsafe.add(source.relative_to(root).as_posix() + " → " + uri)
                    continue
                if not absolute.is_file():
                    missing.setdefault(category, set()).add(absolute.relative_to(root_resolved).as_posix())
    summary = {
        "status": "incomplete" if missing or unsafe else "complete",
        "scope": "static Dart generated-file references; no build or third-party source execution",
        "scanned_dart_files": file_count,
        "missing_count": sum(len(x) for x in missing.values()),
        "missing_by_category": {
            category: {"count": len(items), "examples": sorted(items)[:5]}
            for category, items in sorted(missing.items())
        },
        "unsafe_path_references": sorted(unsafe)[:20],
        "note": "Passing only proves these referenced paths exist, not that generated content is correct, safe or buildable.",
    }
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=APP, help="Flutter application root")
    parser.add_argument("--strict", action="store_true", help="fail when any reviewed generated references are missing")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if not args.root.is_dir():
        print("FAIL application directory missing", file=sys.stderr)
        return 2
    report = generated_report(args.root)
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"{report['status'].upper()}: {report['missing_count']} generated sources absent "
              f"across {report['scanned_dart_files']} Dart files; "
              "see --json for category examples")
    return 1 if args.strict and report["status"] != "complete" else 0


if __name__ == "__main__":
    raise SystemExit(main())
