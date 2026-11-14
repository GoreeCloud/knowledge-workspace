import struct
import tomllib
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from check_linux_ffi_bundle import APP, elf_header, report


def elf(kind=3, arch=62):
    hdr = bytearray(64)
    hdr[:7] = b"\x7fELF\x02\x01\x01"
    struct.pack_into("<HH", hdr, 16, kind, arch)
    return bytes(hdr)


def fixture(root):
    (root / "linux/flutter/dart_ffi").mkdir(parents=True)
    (root / "linux/CMakeLists.txt").write_text('set(BINARY_NAME "AppFlowy")\ninstall(FILES "${DART_FFI_DLL}" DESTINATION lib)\n')
    (root / "linux/flutter/CMakeLists.txt").write_text('set(DART_FFI_DLL "dart_ffi/libdart_ffi.so" PARENT_SCOPE)\n')


class NativeBundlePreflight(unittest.TestCase):
    def test_rust_ffi_exports_static_and_shared_library_types(self):
        rust_crate = APP.parent / "rust-lib/dart-ffi/Cargo.toml"
        manifest = tomllib.loads(rust_crate.read_text(encoding="utf-8"))
        self.assertEqual(manifest["lib"]["name"], "dart_ffi")
        self.assertEqual(set(manifest["lib"]["crate-type"]), {"staticlib", "cdylib"})
        self.assertEqual(manifest["package"]["name"], "dart-ffi")

    def test_imported_source_not_mistaken_for_runnable(self):
        x = report(APP)
        self.assertEqual(x["status"], "incomplete")
        self.assertTrue(all(x["source_contract"].values()))
        self.assertFalse(x["ffi"]["present"])
        self.assertFalse(x["release_verified"])

    def test_elf_header_rejects_wrong_kind_arch_and_truncation(self):
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp) / "lib.so"
            for raw, valid in ((elf(), True), (elf(2), False), (elf(3,183), False),
                               (b"not ELF", False), (b"\x7fELF", False)):
                p.write_bytes(raw)
                self.assertEqual(elf_header(p, shared=True)[0], valid)

    def test_only_structural_presence_can_pass(self):
        with tempfile.TemporaryDirectory() as temp:
            app = Path(temp)
            fixture(app)
            self.assertEqual(report(app)["status"], "incomplete")
            (app / "linux/flutter/dart_ffi/libdart_ffi.so").write_bytes(elf())
            self.assertEqual(report(app)["status"], "prerequisites_present")

    def test_bundle_parts_required(self):
        with tempfile.TemporaryDirectory() as temp:
            app = Path(temp)
            fixture(app)
            (app / "linux/flutter/dart_ffi/libdart_ffi.so").write_bytes(elf())
            bundle = app / "build/linux/x64/debug/bundle"
            (bundle / "lib").mkdir(parents=True)
            (bundle / "data/flutter_assets").mkdir(parents=True)
            (bundle / "AppFlowy").write_bytes(elf(kind=2))
            (bundle / "lib/libflutter_linux_gtk.so").write_bytes(elf())
            (bundle / "lib/libdart_ffi.so").write_bytes(elf())
            self.assertEqual(report(app, bundle)["status"], "prerequisites_present")
            (bundle / "lib/libdart_ffi.so").unlink()
            self.assertEqual(report(app, bundle)["status"], "incomplete")

    def test_symlink_ffi_and_escape_bundle_refused(self):
        with tempfile.TemporaryDirectory() as temp:
            app = Path(temp) / "app"
            app.mkdir()
            fixture(app)
            real = app / "linux/flutter/dart_ffi/real.so"
            real.write_bytes(elf())
            (app / "linux/flutter/dart_ffi/libdart_ffi.so").symlink_to(real)
            self.assertEqual(report(app)["status"], "incomplete")
            with self.assertRaises(ValueError):
                report(app, app.parent)


if __name__ == "__main__":
    unittest.main()
