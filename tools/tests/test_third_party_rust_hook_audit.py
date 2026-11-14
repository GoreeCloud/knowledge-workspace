"""Fixtures for read-only Cargo registry hook provenance verification."""
import hashlib
import io
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from third_party_rust_hook_audit import (
    AuditError, REGISTRY_SOURCE, audit, locked_registry_packages,
    safe_hook_path,
)


class ThirdPartyHooksTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.src = self.root / "src"
        self.archives = self.root / "cache"
        self.src.mkdir()
        self.archives.mkdir()
        self.lock = self.root / "Cargo.lock"

    def package(self, name="demo", version="1.0.0", build_name="build.rs",
                proc_macro=True, include_source=True, include_archive=True):
        label = f"{name}-{version}"
        manifest = (f'[package]\nname = "{name}"\nversion = "{version}"\n'
                    + (f'build = "{build_name}"\n' if build_name is not None else '')
                    + ('[lib]\nproc-macro = true\n' if proc_macro else ''))
        contents = {"Cargo.toml": manifest.encode(),
                    "build.rs": b'fn main(){let _ = std::process::Command::new("true");}\n'}
        if proc_macro:
            contents["src/lib.rs"] = b"pub fn entry() {}\n"
        with io.BytesIO() as output:
            with tarfile.open(fileobj=output, mode="w:gz") as tar:
                for filename, body in contents.items():
                    info = tarfile.TarInfo(name=f"{label}/{filename}")
                    info.size = len(body)
                    info.mode = 0o644
                    tar.addfile(info, io.BytesIO(body))
            archive = output.getvalue()
        if include_archive:
            (self.archives / (label + ".crate")).write_bytes(archive)
        if include_source:
            pkg = self.src / label
            pkg.mkdir()
            for filename, body in contents.items():
                destination = pkg / filename
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(body)
        return name, version, hashlib.sha256(archive).hexdigest()

    def set_lock(self, *items):
        packages = ''.join(
            '\n[[package]]\n'
            + f'name = "{n}"\nversion = "{v}"\nsource = "{REGISTRY_SOURCE}"\n'
            + f'checksum = "{checksum}"\n'
            for n, v, checksum in items
        )
        self.lock.write_text('version = 3\n' + packages)

    def test_lock_only_never_suggests_full_cache_coverage(self):
        a = self.package()
        self.set_lock(a)
        report = audit(self.lock, None, None)
        self.assertEqual(report["status"], "lock_only_source_not_inspected")
        self.assertFalse(report["cache_inspected"])
        self.assertFalse(report["full_security_review_complete"])
        self.assertEqual(report["build_scripts"], 0)

    def test_locked_archive_and_build_script_provenance(self):
        a = self.package()
        self.set_lock(a)
        report = audit(self.lock, self.src, self.archives, strict=True)
        self.assertEqual(report["source_verified_against_locked_archive"], 1)
        self.assertEqual(report["build_scripts"], 1)
        self.assertEqual(report["proc_macro_crates"], 1)
        self.assertEqual(report["status"], "complete_cache_provenance_verified")
        hook = report["entries"][0]["build_hook"]
        self.assertIn("process_invocation", hook["indicators"])

    def test_archive_checksum_must_match_cargo_lock(self):
        a = self.package()
        self.set_lock((a[0], a[1], "0" * 64))
        with self.assertRaisesRegex(AuditError, "archive SHA-256 mismatch"):
            audit(self.lock, self.src, self.archives)

    def test_cached_hook_must_match_verified_archive(self):
        a = self.package()
        self.set_lock(a)
        (self.src / "demo-1.0.0" / "build.rs").write_text("fn main() { panic!(); }")
        with self.assertRaisesRegex(AuditError, "hook differs"):
            audit(self.lock, self.src, self.archives)

    def test_source_manifest_must_match_verified_archive(self):
        a = self.package()
        self.set_lock(a)
        (self.src / "demo-1.0.0" / "Cargo.toml").write_text('[package]\nname = "other"\nversion = "1.0.0"\n')
        with self.assertRaisesRegex(AuditError, "identity mismatch"):
            audit(self.lock, self.src, self.archives)

    def test_missing_build_script_detected_against_archive(self):
        a = self.package()
        self.set_lock(a)
        (self.src / "demo-1.0.0" / "build.rs").unlink()
        with self.assertRaisesRegex(AuditError, "declared build hook absent"):
            audit(self.lock, self.src, self.archives)

    def test_tampered_proc_macro_entry_detected(self):
        a = self.package()
        self.set_lock(a)
        (self.src / "demo-1.0.0" / "src/lib.rs").write_text("malicious or accidental modification")
        with self.assertRaisesRegex(AuditError, "proc-macro entry source differs"):
            audit(self.lock, self.src, self.archives)

    def test_refuse_symlinked_source_hook(self):
        a = self.package()
        self.set_lock(a)
        path = self.src / "demo-1.0.0" / "build.rs"
        path.unlink()
        path.symlink_to("/etc/passwd")
        with self.assertRaisesRegex(AuditError, "source path includes symlink"):
            audit(self.lock, self.src, self.archives)

    def test_missing_package_marked_partial_and_strict_fails(self):
        a = self.package(include_source=False)
        self.set_lock(a)
        report = audit(self.lock, self.src, self.archives)
        self.assertEqual(report["sources_absent"], 1)
        self.assertEqual(report["status"], "partial_cache_provenance_verified")
        with self.assertRaisesRegex(AuditError, "strict audit requires complete"):
            audit(self.lock, self.src, self.archives, strict=True)

    def test_missing_archive_never_counted_as_verified(self):
        a = self.package(include_archive=False)
        self.set_lock(a)
        report = audit(self.lock, self.src, self.archives)
        self.assertEqual(report["archives_absent"], 1)
        self.assertEqual(report["source_verified_against_locked_archive"], 0)

    def test_allow_normalized_relative_hook_without_traversal(self):
        self.assertEqual(safe_hook_path("./build.rs"), "build.rs")
        self.assertEqual(safe_hook_path("build/setup.rs"), "build/setup.rs")
        self.assertIsNone(safe_hook_path(False))
        for bad in ("../outside.rs", "./../outside.rs", "/tmp/o.rs", "build//script.rs", r"build\file.rs"):
            with self.subTest(bad=bad), self.assertRaises(AuditError):
                safe_hook_path(bad)

    def test_reject_malicious_crate_name_and_version_paths(self):
        bad_names = ("../escape", "/tmp/secret", "demo/../../", "demo\\evil")
        for name in bad_names:
            with self.subTest(name=name):
                self.lock.write_text(
                    'version = 3\n[[package]]\nname = "' + name.replace("\\", "\\\\")
                    + '"\nversion = "1.0.0"\nsource = "' + REGISTRY_SOURCE
                    + '"\nchecksum = "' + "0" * 64 + '"\n'
                )
                with self.assertRaises(AuditError):
                    locked_registry_packages(self.lock)
        for version in ("../../escape", "1.0.0/../", "1..0", "1\\evil"):
            with self.subTest(version=version):
                self.lock.write_text(
                    'version = 3\n[[package]]\nname = "demo"\nversion = "'
                    + version.replace("\\", "\\\\") + '"\nsource = "'
                    + REGISTRY_SOURCE + '"\nchecksum = "' + "0" * 64 + '"\n'
                )
                with self.assertRaises(AuditError):
                    locked_registry_packages(self.lock)

    def test_duplicate_lock_registry_package_rejected(self):
        a = self.package()
        self.set_lock(a, a)
        with self.assertRaisesRegex(AuditError, "duplicate registry package"):
            locked_registry_packages(self.lock)


if __name__ == "__main__":
    unittest.main()
