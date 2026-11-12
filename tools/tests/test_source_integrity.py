"""Safety tests for the offline source-snapshot integrity validator."""
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from source_integrity import IntegrityError, checked_file, digest, refresh, safe_path  # noqa: E402


class SourceIntegrityTests(unittest.TestCase):
    def test_rejects_parent_directory(self):
        for path in ("../private", "/etc/passwd", "foo//bar", "foo/./bar", "C:/Windows",
                     "foo\\bar", "foo/../bar", ""):
            with self.subTest(path=path):
                with self.assertRaises(IntegrityError):
                    safe_path(path)

    def test_accepts_hidden_repository_file(self):
        self.assertEqual(safe_path(".goreecloud/upstream-source-digests.json"),
                         ".goreecloud/upstream-source-digests.json")

    def test_rejects_missing_and_symlink(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with self.assertRaises(IntegrityError):
                checked_file(root, "missing.txt")
            (root / "actual.txt").write_text("example")
            (root / "alias.txt").symlink_to(root / "actual.txt")
            with self.assertRaises(IntegrityError):
                checked_file(root, "alias.txt")

    def test_detects_unapproved_content_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "demo.txt"
            path.write_bytes(b"before")
            expected = hashlib.sha256(b"before").hexdigest()
            self.assertEqual(digest(checked_file(root, "demo.txt")), expected)
            path.write_bytes(b"after")
            self.assertNotEqual(digest(checked_file(root, "demo.txt")), expected)

    def test_explicit_refresh_only_updates_selected_entry(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "alpha.txt").write_bytes(b"new alpha")
            (root / "beta.txt").write_bytes(b"new beta")
            manifest = {"files": [
                {"import_path": "alpha.txt", "import_sha256": "a" * 64},
                {"import_path": "beta.txt", "import_sha256": "b" * 64},
            ]}
            self.assertEqual(refresh(root, manifest, ["alpha.txt"]), 1)
            self.assertEqual(manifest["files"][0]["import_sha256"],
                             hashlib.sha256(b"new alpha").hexdigest())
            self.assertEqual(manifest["files"][1]["import_sha256"], "b" * 64)

    def test_protected_attribution_never_automatically_rebaselined(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "LICENSE").write_bytes(b"example")
            manifest = {"files": [{"import_path": "LICENSE", "import_sha256": "a" * 64}]}
            with self.assertRaises(IntegrityError):
                refresh(root, manifest, ["LICENSE"])

    def test_unlisted_new_file_requires_own_source_process(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "new-file.txt").write_bytes(b"hello")
            with self.assertRaises(IntegrityError):
                refresh(root, {"files": []}, ["new-file.txt"])


if __name__ == "__main__":
    unittest.main()
