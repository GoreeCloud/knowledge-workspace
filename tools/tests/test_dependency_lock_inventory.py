"""Offline lockfile source identity tests; no dependency downloads or builds."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dependency_lock_inventory import (DART,RUST,LockError,parse_dart_packages,
                                       parse_rust_packages,report)

class LockSourceInventoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dart=(DART/"pubspec.lock").read_text()
        cls.rust=(RUST/"Cargo.lock").read_text()
    def test_current_lock_sources(self):
        data=report(self.dart,self.rust)
        self.assertEqual(data["dart"]["total"],326)
        self.assertEqual(data["rust"]["total"],823)
        self.assertEqual(data["dart"]["source_counts"],
                         {"hosted":294,"git":15,"path":8,"sdk":9})
        self.assertEqual(data["rust"]["source_counts"],
                         {"registry":768,"git":24,"path":31})
    def test_hosted_checksum_tampering_refused(self):
        data=self.dart.replace('sha256: "16e298750b6d0af7ce8a3ba7c18c69c3785d11b15ec83f6dcd0ad2a0009b3cab"',
                               'sha256: "bad"',1)
        with self.assertRaises(LockError):parse_dart_packages(data)
    def test_unreviewed_dart_host_refused(self):
        with self.assertRaises(LockError):
            parse_dart_packages(self.dart.replace("https://pub.dev","https://evil.example",1))
    def test_dart_git_floating_revision_refused(self):
        data=self.dart.replace('ref: e8317c0d1af8d23dc5707b02ea43864536b6de91','ref: HEAD',1)
        with self.assertRaises(LockError):parse_dart_packages(data)
    def test_dart_git_resolved_drift_refused(self):
        data=self.dart.replace('resolved-ref: e8317c0d1af8d23dc5707b02ea43864536b6de91',
                               'resolved-ref: aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',1)
        with self.assertRaises(LockError):parse_dart_packages(data)
    def test_dart_duplicate_package_refused(self):
        data=self.dart.replace('  analyzer:\n','  _fe_analyzer_shared:\n',1)
        with self.assertRaises(LockError):parse_dart_packages(data)
    def test_rust_registry_checksum_refused(self):
        data=self.rust.replace('registry+https://github.com/rust-lang/crates.io-index',
                               'registry+https://unreviewed.example/index',1)
        with self.assertRaises(LockError):parse_rust_packages(data)
    def test_rust_git_commit_refused(self):
        data=self.rust.replace('#9a319193352331fa4e5ff1dd4de43a0fbc5d0cbd',
                               '#0000000000000000000000000000000000000000',1)
        with self.assertRaises(LockError):parse_rust_packages(data)
    def test_rust_git_source_query_refused(self):
        data=self.rust.replace(
            '?rev=9a319193352331fa4e5ff1dd4de43a0fbc5d0cbd',
            '?rev=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',1)
        with self.assertRaises(LockError):parse_rust_packages(data)
    def test_license_claim_not_in_inventory(self):
        self.assertIn("not verified",report(self.dart,self.rust)["assurance"])
if __name__=="__main__":unittest.main()
