"""Tests of declared toolchain pins without downloading SDKs or executing builds."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from check_development_toolchains import PreflightError, anchored_value, project_pins, semver  # noqa: E402


class DevelopmentToolchainContracts(unittest.TestCase):
    def test_pins_match_imported_ci_and_pubspec(self):
        pins = project_pins()
        self.assertEqual(pins["ci_flutter"], "3.27.4")
        self.assertEqual(pins["ci_rust"], "1.85.0")
        self.assertEqual(pins["repo_rust_channel"], "1.85")
        self.assertEqual(pins["min_flutter"], "3.27.4")
        self.assertEqual(pins["min_dart"], "3.3.0")

    def test_semver_rejects_invalid_or_truncated_versions(self):
        self.assertEqual(semver("3.27.4"), (3, 27, 4))
        for bad in ("", "3.27", "3.27.4-beta", "3.27.4;echo", "-1.2.3"):
            with self.subTest(bad=bad), self.assertRaises(PreflightError):
                semver(bad)

    def test_duplicate_ci_pins_rejected(self):
        with self.assertRaises(PreflightError):
            anchored_value('FLUTTER_VERSION: "3.27.4"\nFLUTTER_VERSION: "9.9.9"',
                           "FLUTTER_VERSION")

    def test_conflicting_rust_channels_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for dirname in (".github/upstream-workflows-disabled", "frontend/rust-lib",
                            "frontend/appflowy_flutter"):
                (root / dirname).mkdir(parents=True)
            (root / ".github/upstream-workflows-disabled/flutter_ci.yaml").write_text(
                'FLUTTER_VERSION: "3.27.4"\nRUST_TOOLCHAIN: "1.85.0"\n'
            )
            (root / "frontend/rust-toolchain.toml").write_text(
                '[toolchain]\nchannel = "1.85"\n'
            )
            (root / "frontend/rust-lib/rust-toolchain.toml").write_text(
                '[toolchain]\nchannel = "1.84"\n'
            )
            (root / "frontend/appflowy_flutter/pubspec.yaml").write_text(
                'environment:\n  flutter: ">=3.27.4"\n  sdk: ">=3.3.0 <4.0.0"\n'
            )
            with self.assertRaises(PreflightError):
                project_pins(root)

    def test_developer_guide_present(self):
        guide = Path(__file__).resolve().parents[2] / "docs/DEVELOPMENT_TOOLCHAINS.md"
        text = guide.read_text()
        for key in ("Flutter 3.27.4", "Rust 1.85.0", "flutter doctor"):
            self.assertIn(key, text)


if __name__ == "__main__":
    unittest.main()
