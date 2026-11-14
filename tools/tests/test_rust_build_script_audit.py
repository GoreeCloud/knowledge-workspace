"""No-execution tests for imported first-party Rust build-script inventory."""
import sys
import unittest
from pathlib import Path
import json

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rust_build_script_audit import (ROOT, BASE, BuildScriptError,
                                     actual, examine_source, verify)

class FirstPartyBuildScriptTests(unittest.TestCase):
    def test_current_inventory(self):
        verify(actual(ROOT), json.loads(BASE.read_text()))
    def test_process_spawn_refused(self):
        with self.assertRaises(BuildScriptError):
            examine_source('fn main(){ std::process::Command::new("curl"); flowy_codegen::protobuf_file::dart_gen(env!("CARGO_PKG_NAME")); }')
    def test_network_access_refused(self):
        with self.assertRaises(BuildScriptError):
            examine_source('fn main(){ reqwest::get("https:example"); flowy_codegen::protobuf_file::dart_gen(env!("CARGO_PKG_NAME")); }')
    def test_unreviewed_generator_refused(self):
        with self.assertRaises(BuildScriptError):
            examine_source('fn main(){ flowy_codegen::network::fetch(env!("CARGO_PKG_NAME")); }')
    def test_new_script_refused(self):
        records=actual(ROOT)
        more=records+[{"path":"frontend/rust-lib/evil/build.rs","sha256":"a"*64,"calls":[]}]
        with self.assertRaises(BuildScriptError):
            verify(more,json.loads(BASE.read_text()))
    def test_changed_script_refused(self):
        records=actual(ROOT)
        records[0]["sha256"]="a"*64
        with self.assertRaises(BuildScriptError):
            verify(records,json.loads(BASE.read_text()))
    def test_build_script_review_documented(self):
        s=(ROOT/"docs/RUST_BUILD_SCRIPT_REVIEW.md").read_text()
        self.assertIn("flowy_codegen",s)
        self.assertIn("transitive",s)
if __name__=="__main__":
    unittest.main()
