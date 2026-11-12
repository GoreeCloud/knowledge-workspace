"""Unit tests for offline host-literal privacy review metadata."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from network_reference_audit import (  # noqa: E402
    AuditError,
    extract_hosts,
    scan_references,
    verify_baseline,
)


class HostLiteralTests(unittest.TestCase):
    def test_parses_hostnames_only_not_secrets_or_paths(self):
        urls = "https://API.Example.COM:443/private?token=abc http://localhost:8080/admin"
        self.assertEqual(extract_hosts(urls), {"api.example.com", "localhost"})

    def test_ignores_incomplete_url_literal(self):
        self.assertEqual(extract_hosts("http:// https://"), set())

    def test_ignores_non_http_urls(self):
        self.assertEqual(extract_hosts("ftp://ftp.example.com file://secret/path"), set())

    def test_source_scan_keeps_only_source_file_paths(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "frontend/appflowy_flutter/lib").mkdir(parents=True)
            (root / "frontend/rust-lib").mkdir(parents=True)
            (root / "frontend/appflowy_flutter/lib/test.dart").write_text(
                "// Docs: https://docs.example.org/page?secret=redacted\n"
            )
            (root / "frontend/rust-lib/client.rs").write_text(
                'let url = "http://127.0.0.1:8111/health";'
            )
            actual = scan_references(root)
            self.assertEqual(set(actual), {"docs.example.org", "127.0.0.1"})
            self.assertEqual(
                actual["docs.example.org"],
                ["frontend/appflowy_flutter/lib/test.dart"],
            )

    def test_new_unreviewed_host_fails(self):
        observed = {"new.example.org": ["frontend/appflowy_flutter/lib/test.dart"]}
        baseline = {"schema": 1, "classification": "static-strings-not-egress-allowlist",
                    "upstream_revision": "8fcee27d9bd93aad4ee0191d5d8d915d6a9a4e93",
                    "reviewed_hostnames": ["old.example.org"]}
        with self.assertRaises(AuditError):
            verify_baseline(observed, baseline)

    def test_historical_host_becomes_stale_informationally(self):
        observed = {"present.example.org": ["frontend/rust-lib/code.rs"]}
        baseline = {"schema": 1, "classification": "static-strings-not-egress-allowlist",
                    "upstream_revision": "8fcee27d9bd93aad4ee0191d5d8d915d6a9a4e93",
                    "reviewed_hostnames": ["old.example.org", "present.example.org"]}
        self.assertEqual(verify_baseline(observed, baseline), (1, 1))

    def test_reject_unsorted_or_duplicate_baseline(self):
        for invalid in (["z.example.org", "a.example.org"], ["a.example.org", "a.example.org"]):
            with self.subTest(value=invalid), self.assertRaises(AuditError):
                verify_baseline({}, {"schema": 1, "classification": "static-strings-not-egress-allowlist",
                    "upstream_revision": "8fcee27d9bd93aad4ee0191d5d8d915d6a9a4e93",
                                     "reviewed_hostnames": invalid})


if __name__ == "__main__":
    unittest.main()
