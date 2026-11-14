"""Read-only generated source prerequisite contracts."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from generated_source_preflight import APP, classify_generated, generated_report, source_modules


class GeneratedSourceContracts(unittest.TestCase):
    def test_real_import_scan_is_future_compatible(self):
        result = generated_report(APP)
        self.assertGreater(result["scanned_dart_files"], 100)
        self.assertGreaterEqual(result["missing_count"], 0)
        # When generated files are later checked in, this test must not
        # obstruct a valid improvement by requiring that files stay missing.
        self.assertEqual(result["unsafe_path_references"], [])

    def test_classification(self):
        cases = {
            "generated/locale_keys.g.dart": "localization",
            "lib/generated/flowy_svgs.g.dart": "svg",
            "protobuf/flowy-folder/view.pb.dart": "rust_protobuf",
            "dart_event/flowy-folder/dart_event.dart": "rust_dispatch",
            "model.freezed.dart": "freezed",
            "model.g.dart": "dart_generated",
        }
        for uri, expected in cases.items():
            with self.subTest(uri=uri):
                self.assertEqual(classify_generated(uri, "part"), expected)

    def test_plain_imports_not_counted(self):
        self.assertIsNone(classify_generated("package:flutter/widgets.dart", "import"))
        self.assertIsNone(classify_generated("src/settings.dart", "import"))

    def test_synthetic_generated_sources(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            lib = root / "lib"
            lib.mkdir()
            (lib / "main.dart").write_text(
                "import 'package:appflowy/generated/locale_keys.g.dart';\n"
                "part 'model.freezed.dart';\n"
                "import 'package:appflowy_backend/protobuf/flowy-folder/view.pb.dart';\n"
            )
            backend = root / "packages/appflowy_backend"
            (backend / "lib").mkdir(parents=True)
            (backend / "pubspec.yaml").write_text("name: appflowy_backend\n")
            result = generated_report(root)
            self.assertEqual(result["missing_count"], 3)
            (lib / "generated").mkdir()
            (lib / "generated/locale_keys.g.dart").write_text("// generated\n")
            (lib / "model.freezed.dart").write_text("// generated\n")
            (backend / "lib/protobuf/flowy-folder").mkdir(parents=True)
            (backend / "lib/protobuf/flowy-folder/view.pb.dart").write_text("// generated\n")
            self.assertEqual(generated_report(root)["status"], "complete")

    def test_path_escape_refused(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "lib").mkdir()
            (root / "lib/test.dart").write_text("part '../../secret.freezed.dart';\n")
            self.assertEqual(len(generated_report(root)["unsafe_path_references"]), 1)

    def test_package_discovery(self):
        modules = source_modules(APP)
        self.assertIn("appflowy", modules)
        self.assertIn("appflowy_backend", modules)
        self.assertIn("flowy_svg", modules)


if __name__ == "__main__":
    unittest.main()
