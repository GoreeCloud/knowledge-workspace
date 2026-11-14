#!/usr/bin/env python3
"""Read-only x86_64 Linux FFI/bundle prerequisites. NOT runtime or security certification."""
from __future__ import annotations

import argparse
import json
import struct
import sys
from pathlib import Path

APP = Path(__file__).resolve().parents[1] / "frontend/appflowy_flutter"
OUTPUTS = ("AppFlowy", "lib/libdart_ffi.so", "lib/libflutter_linux_gtk.so", "data/flutter_assets")


def safe_file(root: Path, path: Path) -> bool:
    return path.resolve().is_relative_to(root.resolve()) and path.is_file() and not path.is_symlink()


def elf_header(path: Path, shared: bool) -> tuple[bool, str]:
    try:
        with path.open("rb") as handle:
            hdr = handle.read(64)
    except OSError:
        return False, "unreadable"
    if len(hdr) < 64 or hdr[:4] != b"\x7fELF":
        return False, "not_elf"
    if hdr[4:7] != b"\x02\x01\x01":
        return False, "not_64_bit_little_endian"
    kind, arch = struct.unpack_from("<HH", hdr, 16)
    if arch != 62 or kind not in ((3,) if shared else (2, 3)):
        return False, "wrong_arch_or_kind"
    return True, "elf64_x86_64_shared" if shared else "elf64_x86_64_executable"


def report(app: Path, bundle: Path | None = None) -> dict:
    if not app.is_dir():
        raise ValueError("application root not found")
    cmake, flutter = (app / "linux/CMakeLists.txt"), (app / "linux/flutter/CMakeLists.txt")
    cmake_text = cmake.read_text() if safe_file(app, cmake) else ""
    flutter_text = flutter.read_text() if safe_file(app, flutter) else ""
    source = {
        "runner_declares_AppFlowy": 'set(BINARY_NAME "AppFlowy")' in cmake_text,
        "runner_installs_ffi": 'install(FILES "${DART_FFI_DLL}"' in cmake_text,
        "flutter_expects_shared_lib": "dart_ffi/libdart_ffi.so" in flutter_text,
    }
    ffi = app / "linux/flutter/dart_ffi/libdart_ffi.so"
    ffi_present = safe_file(app, ffi)
    ffi_valid, ffi_detail = elf_header(ffi, shared=True) if ffi_present else (False, "missing")
    result = {
        "scope": "read-only structural Linux native input inspection",
        "source_contract": source,
        "ffi": {"path": "linux/flutter/dart_ffi/libdart_ffi.so", "present": ffi_present,
                "elf_structural_check": ffi_valid, "detail": ffi_detail},
        "release_verified": False,
        "limitations": "ELF headers do not establish exported symbols, correct linkage, safety, runtime behavior, or licensing",
    }
    good = all(source.values()) and ffi_valid
    if bundle is not None:
        if bundle.is_symlink() or not bundle.resolve().is_relative_to(app.resolve()):
            raise ValueError("bundle path must remain inside the app root")
        outputs = {}
        for rel in OUTPUTS:
            file = bundle / rel
            if rel == "data/flutter_assets":
                ok = file.is_dir() and not file.is_symlink() and file.resolve().is_relative_to(app.resolve())
                outputs[rel] = {"present": ok}
            else:
                present = safe_file(app, file)
                valid, detail = elf_header(file, shared=rel != "AppFlowy") if present else (False, "missing")
                outputs[rel] = {"present": present, "elf_structural_check": valid, "detail": detail}
            good = good and outputs[rel]["present"] and outputs[rel].get("elf_structural_check", True)
        result["bundle"] = {"outputs": outputs}
    result["status"] = "prerequisites_present" if good else "incomplete"
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=APP)
    parser.add_argument("--bundle", type=Path)
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        data = report(args.root, args.bundle)
    except (ValueError, OSError) as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(data, indent=2) if args.json else f"Linux FFI/bundle: {data['status']} (no runtime validation)")
    return 1 if args.strict and data["status"] != "prerequisites_present" else 0


if __name__ == "__main__":
    raise SystemExit(main())
