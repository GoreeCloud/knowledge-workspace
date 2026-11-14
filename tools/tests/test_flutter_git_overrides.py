"""No-network tests for exact Git overrides and regression detection."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from verify_flutter_git_overrides import OverrideError, PACKAGE, verify

class OverrideContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pub = (PACKAGE / "pubspec.yaml").read_text()
        cls.lock = (PACKAGE / "pubspec.lock").read_text()
    def test_baseline_exact_revisions(self):
        pins = verify(self.pub, self.lock)
        self.assertEqual(pins["url_protocol"], "77a84201ed8ca50082f4248f3a373d053b1c0462")
        self.assertEqual(pins["flutter_cache_manager"], "fbab857b1b1d209240a146d32f496379b9f62276")
    def test_unsupported_commit_rejected(self):
        bad = self.pub.replace("ref: 77a84201ed8ca50082f4248f3a373d053b1c0462",
                               "commit: 77a84201ed8ca50082f4248f3a373d053b1c0462", 1)
        with self.assertRaises(OverrideError):
            verify(bad, self.lock)
    def test_floating_head_or_new_commit_rejected(self):
        for ref in ("HEAD", "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"):
            with self.subTest(ref=ref), self.assertRaises(OverrideError):
                verify(self.pub.replace(
                    "ref: 77a84201ed8ca50082f4248f3a373d053b1c0462",
                    "ref: " + ref, 1), self.lock)
    def test_lock_ref_drift_rejected(self):
        with self.assertRaises(OverrideError):
            verify(self.pub, self.lock.replace(
                "ref: fbab857b1b1d209240a146d32f496379b9f62276",
                "ref: HEAD", 1))
    def test_resolved_ref_drift_rejected(self):
        with self.assertRaises(OverrideError):
            verify(self.pub, self.lock.replace(
                "resolved-ref: fbab857b1b1d209240a146d32f496379b9f62276",
                "resolved-ref: aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", 1))
    def test_duplicate_override_refused(self):
        with self.assertRaises(OverrideError):
            verify(self.pub + "\ndependency_overrides:\n  url_protocol:\n    git:\n      ref: HEAD\n",
                   self.lock)
if __name__ == "__main__":
    unittest.main()
