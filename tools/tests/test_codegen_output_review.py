"""Offline code-generator source and output path validation tests."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from codegen_output_review import (ROOT,BASELINE,CodegenReviewError,
                                   inventory,verify,validate_environment)
class CodegenOutputTests(unittest.TestCase):
    def test_reviewed_source_digest_inventory(self):
        self.assertEqual(verify(ROOT,json.loads(BASELINE.read_text())),5)
    def test_changed_source_hash_fails(self):
        data=json.loads(BASELINE.read_text())
        data["files"][0]["sha256"]="a"*64
        with self.assertRaises(CodegenReviewError):verify(ROOT,data)
    def test_missing_inventory_entry_fails(self):
        data=json.loads(BASELINE.read_text())
        data["files"].pop()
        with self.assertRaises(CodegenReviewError):verify(ROOT,data)
    def test_missing_env_fails(self):
        with self.assertRaises(CodegenReviewError):validate_environment({})
    def test_expected_nested_output_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)
            env={"GOREECLOUD_BUILD_OUTPUT_ROOT":tmp,
                 "CARGO_MAKE_WORKING_DIRECTORY":tmp,
                 "FLUTTER_FLOWY_SDK_PATH":"sdk"}
            self.assertEqual(validate_environment(env),p/"sdk")
    def test_absolute_sdk_path_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            env={"GOREECLOUD_BUILD_OUTPUT_ROOT":tmp,
                 "CARGO_MAKE_WORKING_DIRECTORY":tmp,
                 "FLUTTER_FLOWY_SDK_PATH":"/home/private"}
            with self.assertRaises(CodegenReviewError):validate_environment(env)
    def test_parent_escape_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            env={"GOREECLOUD_BUILD_OUTPUT_ROOT":tmp,
                 "CARGO_MAKE_WORKING_DIRECTORY":tmp,
                 "FLUTTER_FLOWY_SDK_PATH":"../../outside"}
            with self.assertRaises(CodegenReviewError):validate_environment(env)
    def test_symlink_escape_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)
            (p/"outside").symlink_to("/tmp")
            env={"GOREECLOUD_BUILD_OUTPUT_ROOT":tmp,
                 "CARGO_MAKE_WORKING_DIRECTORY":tmp,
                 "FLUTTER_FLOWY_SDK_PATH":"outside"}
            with self.assertRaises(CodegenReviewError):validate_environment(env)
if __name__=="__main__":unittest.main()
