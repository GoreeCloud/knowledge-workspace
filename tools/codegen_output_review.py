#!/usr/bin/env python3
"""Offline code-generator source change detection and output path preflight.

This is not a sandbox. No imports of, or execution of, AppFlowy/Rust build scripts.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / ".goreecloud/rust-codegen-source-review.json"
CODEGEN = "frontend/rust-lib/build-tool/flowy-codegen/src/"
FILES = (
    "dart_event/dart_event.rs",
    "protobuf_file/mod.rs",
    "protobuf_file/proto_gen.rs",
    "protobuf_file/proto_info.rs",
    "util.rs",
)
SHA = re.compile(r"[0-9a-f]{64}\Z")
class CodegenReviewError(ValueError):
    pass

def inventory(root: Path) -> list[dict[str,str]]:
    result=[]
    for suffix in FILES:
        rel=CODEGEN+suffix
        path=root/rel
        if not path.is_file() or path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
            raise CodegenReviewError(f"unsafe/missing codegen source: {rel}")
        data=path.read_bytes()
        result.append({"path":rel,"sha256":hashlib.sha256(data).hexdigest()})
    return result

def verify(root:Path, baseline:dict) -> int:
    if (baseline.get("schema") != 1 or
        baseline.get("scope") != "five-first-party-code-generator-source-files" or
        baseline.get("upstream_revision") != "8fcee27d9bd93aad4ee0191d5d8d915d6a9a4e93"):
        raise CodegenReviewError("unrecognized code generator review baseline")
    approved=baseline.get("files")
    if not isinstance(approved,list) or approved!=inventory(root):
        raise CodegenReviewError("codegen source changed: inspect filesystem writes, subprocesses and env variables")
    if not all(SHA.fullmatch(x["sha256"]) for x in approved):
        raise CodegenReviewError("bad code generator source SHA")
    return len(approved)

def validate_environment(env: dict[str,str]) -> Path:
    """Check only declared output location; cannot constrain the build generator itself."""
    fields=("GOREECLOUD_BUILD_OUTPUT_ROOT","CARGO_MAKE_WORKING_DIRECTORY","FLUTTER_FLOWY_SDK_PATH")
    if any(not env.get(x) for x in fields):
        raise CodegenReviewError("explicit build root, working directory and SDK relative path required")
    base=Path(env[fields[0]])
    work=Path(env[fields[1]])
    relative=Path(env[fields[2]])
    if not base.is_absolute() or not work.is_absolute() or relative.is_absolute():
        raise CodegenReviewError("build root/working must be absolute and SDK path relative")
    if not base.is_dir() or not work.is_dir():
        raise CodegenReviewError("build root and working directory must already exist")
    if any(p in ("", ".", "..") for p in relative.parts):
        raise CodegenReviewError("invalid SDK path components")
    if any(p.is_symlink() for p in (base,work)):
        raise CodegenReviewError("symlinked build output base/working directory not accepted")
    output=(work/relative).resolve()
    root=base.resolve()
    if work.resolve()!=root and not work.resolve().is_relative_to(root):
        raise CodegenReviewError("working directory escapes approved build output root")
    if not output.is_relative_to(root):
        raise CodegenReviewError("generator Dart output would escape approved build root")
    # Existing path segments must not be symlinked (including link redirection back inside).
    here=work
    for part in relative.parts:
        here=here/part
        if here.is_symlink():
            raise CodegenReviewError("output path includes symlink")
    return output

def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode",choices=("verify","report","check-env"))
    args=parser.parse_args()
    try:
        if args.mode=="check-env":
            output=validate_environment(dict(os.environ))
            print(f"PASS intended code generator output is inside approved root: {output}")
            return 0
        records=inventory(ROOT)
        if args.mode=="report":
            print(json.dumps({"scope":"source digest inventory only; no code executed",
                              "files":records},indent=2))
        else:
            count=verify(ROOT,json.loads(BASELINE.read_text()))
            print(f"PASS {count} reviewed Rust codegen source files unchanged")
    except (OSError,CodegenReviewError,KeyError,TypeError) as exc:
        print(f"FAIL Rust codegen review: {exc}",file=sys.stderr)
        return 1
    return 0

if __name__=="__main__":
    raise SystemExit(main())
