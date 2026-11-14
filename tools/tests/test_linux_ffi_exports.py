import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from check_linux_ffi_exports import KNOWN, parse_dynamic_exports, required_exports, verify
from check_linux_ffi_bundle import APP


class LinuxFfiExports(unittest.TestCase):
    def test_imported_dart_bindings_require_nine_stable_names(self):
        names = required_exports(APP / "packages/appflowy_backend/lib/ffi.dart")
        self.assertEqual(set(names), KNOWN)

    def test_parse_defined_dynamic_symbols_not_headers(self):
        nm = '''                 U not_exported
00000000000182e0 T async_event
00000000000011e0 T sync_event@@VERSION_1
0000000000001fb0 W rust_log
'''
        self.assertEqual(parse_dynamic_exports(nm), {"async_event", "sync_event", "rust_log"})

    def test_deny_symlink_and_non_elf_library(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            fake = root / "libdart_ffi.so"
            fake.write_bytes(b"not an ELF")
            with self.assertRaises(ValueError):
                verify(fake, list(KNOWN))
            link = root / "link.so"
            link.symlink_to(fake)
            with self.assertRaises(ValueError):
                verify(link, list(KNOWN))

    def test_deny_absent_or_duplicate_bindings(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "ffi.dart"
            source.write_text("const name = 'unrelated';")
            with self.assertRaises(ValueError):
                required_exports(source)
            source.write_text("lookupFunction<X, Y>('abc');lookupFunction<X, Y>('abc');")
            with self.assertRaises(ValueError):
                required_exports(source)


if __name__ == "__main__":
    unittest.main()
