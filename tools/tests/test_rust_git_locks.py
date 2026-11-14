"""Offline Git source pin regression tests for the imported Cargo workspace."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from verify_rust_git_locks import ROOT, CargoGitError, verify

class CargoGitLockTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = (ROOT / "Cargo.toml").read_text()
        cls.lock = (ROOT / "Cargo.lock").read_text()
    def test_expected_git_revisions_are_locked(self):
        self.assertEqual(verify(self.manifest,self.lock),
                         {"manifest_git_dependencies":13,"locked_git_packages":24,"git_repositories":4})
    def test_floating_branch_refused(self):
        changed=self.manifest.replace(
            'rev = "9a319193352331fa4e5ff1dd4de43a0fbc5d0cbd"',
            'branch = "af"',1)
        with self.assertRaises(CargoGitError):
            verify(changed,self.lock)
    def test_sha_mismatch_refused(self):
        changed=self.lock.replace(
            "#9a319193352331fa4e5ff1dd4de43a0fbc5d0cbd",
            "#aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",1)
        with self.assertRaises(CargoGitError):
            verify(self.manifest,changed)
    def test_changed_source_query_refused(self):
        changed=self.lock.replace(
            "?rev=9a319193352331fa4e5ff1dd4de43a0fbc5d0cbd#",
            "?branch=af#",1)
        with self.assertRaises(CargoGitError):
            verify(self.manifest,changed)
    def test_unreviewed_origin_refused(self):
        changed=self.manifest.replace(
            "https://github.com/appflowy/langchain-rust",
            "https://untrusted.example/appflowy/langchain-rust",1)
        with self.assertRaises(CargoGitError):
            verify(changed,self.lock)
    def test_lockfile_package_count_drift_refused(self):
        changed=self.lock.replace(
            'source = "git+https://github.com/appflowy/langchain-rust?rev=',
            'source = "registry+https://github.com/appflowy/langchain-rust?rev=',1)
        with self.assertRaises(CargoGitError):
            verify(self.manifest,changed)

if __name__ == "__main__":
    unittest.main()
