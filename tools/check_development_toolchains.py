#!/usr/bin/env python3
"""Read-only committed toolchain pin check; optional installed Linux tool checks."""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class PreflightError(Exception):
    """A project version requirement or local toolchain check failed."""


def semver(raw: str) -> tuple[int, int, int]:
    if not re.fullmatch(r"\d+\.\d+\.\d+", raw):
        raise PreflightError(f"not an explicit three-part version: {raw!r}")
    return tuple(map(int, raw.split(".")))


def anchored_value(source: str, key: str) -> str:
    hits = re.findall(rf"(?m)^\s*{re.escape(key)}:\s*[\"']?([0-9.]+)", source)
    if len(hits) != 1:
        raise PreflightError(f"expected exactly one {key} value, found {len(hits)}")
    semver(hits[0])
    return hits[0]


def project_pins(root: Path = ROOT) -> dict[str, str]:
    ci = (root / ".github/upstream-workflows-disabled/flutter_ci.yaml").read_text()
    flutter = anchored_value(ci, "FLUTTER_VERSION")
    rust_ci = anchored_value(ci, "RUST_TOOLCHAIN")
    def rust_channel(path: str) -> str:
        return tomllib.loads((root / path).read_text())["toolchain"]["channel"]
    rust1 = rust_channel("frontend/rust-toolchain.toml")
    rust2 = rust_channel("frontend/rust-lib/rust-toolchain.toml")
    pub = (root / "frontend/appflowy_flutter/pubspec.yaml").read_text()
    flutter_floor = re.search(r"(?m)^\s*flutter:\s*['\"]>=([0-9.]+)['\"]", pub)
    dart_floor = re.search(r"(?m)^\s*sdk:\s*['\"]>=([0-9.]+)\s+<4\.0\.0['\"]", pub)
    if not flutter_floor or not dart_floor:
        raise PreflightError("missing Flutter/Dart minimum constraints")
    min_flutter = flutter_floor.group(1)
    min_dart = dart_floor.group(1)
    if semver(flutter) < semver(min_flutter) or semver(min_dart)[0] != 3:
        raise PreflightError("upstream CI and pubspec SDK constraints conflict")
    if rust1 != rust2 or not re.fullmatch(r"\d+\.\d+", rust1):
        raise PreflightError("Rust toolchain channels disagree")
    if semver(rust_ci)[:2] != tuple(map(int, rust1.split("."))):
        raise PreflightError("CI Rust patch and repository Rust channel disagree")
    return dict(ci_flutter=flutter, ci_rust=rust_ci, repo_rust_channel=rust1,
                min_flutter=min_flutter, min_dart=min_dart)


def capture_version(command: list[str], env: dict[str, str]) -> str:
    if not shutil.which(command[0]):
        raise PreflightError(f"missing executable: {command[0]}")
    try:
        proc = subprocess.run(command, cwd=ROOT, env=env, text=True,
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                              timeout=45, check=False)
    except subprocess.TimeoutExpired as exc:
        raise PreflightError(f"version command timed out: {command[0]}") from exc
    if proc.returncode:
        raise PreflightError(f"version command failed: {command[0]} ({proc.returncode})")
    return proc.stdout


def check_local(pins: dict[str, str]) -> dict[str, str]:
    if sys.platform != "linux":
        raise PreflightError("--local currently checks Linux workstations only")
    env = dict(os.environ, FLUTTER_SUPPRESS_ANALYTICS="true",
               DART_SUPPRESS_ANALYTICS="true", RUSTUP_AUTO_INSTALL="0")
    checks = {
        "flutter": (["flutter", "--version"], r"Flutter\s+(\d+\.\d+\.\d+)"),
        "dart": (["dart", "--version"], r"Dart SDK version:\s+(\d+\.\d+\.\d+)"),
        "rust_ci": (["rustc", f"+{pins['ci_rust']}", "--version"], r"rustc\s+(\d+\.\d+\.\d+)"),
        "rust_repo": (["rustup", "run", pins["repo_rust_channel"], "rustc", "--version"], r"rustc\s+(\d+\.\d+\.\d+)"),
        "clang": (["clang++", "--version"], r"clang version\s+(\d+\.\d+\.\d+)"),
        "cmake": (["cmake", "--version"], r"cmake version\s+(\d+\.\d+\.\d+)"),
        "ninja": (["ninja", "--version"], r"^(\d+\.\d+\.\d+)"),
        "pkg_config": (["pkg-config", "--version"], r"^(\d+\.\d+\.\d+)"),
    }
    versions = {}
    for name, (command, pattern) in checks.items():
        match = re.search(pattern, capture_version(command, env), re.MULTILINE)
        if not match:
            raise PreflightError(f"unrecognized version output from {command[0]}")
        versions[name] = match.group(1)
    if versions["flutter"] != pins["ci_flutter"] or versions["rust_ci"] != pins["ci_rust"]:
        raise PreflightError("installed Flutter or CI Rust version does not match source pin")
    if tuple(map(int, versions["rust_repo"].split(".")[:2])) != tuple(
        map(int, pins["repo_rust_channel"].split("."))
    ):
        raise PreflightError("repository Rust channel version differs from source pin")
    if not (semver(pins["min_dart"]) <= semver(versions["dart"]) < (4, 0, 0)):
        raise PreflightError("installed Dart violates pubspec constraint")
    return versions


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--local", action="store_true",
                        help="opt in to read-only installed compiler checks (Linux)")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        pins = project_pins()
        local = check_local(pins) if args.local else None
        result = dict(status="pass", scope="local-versions" if args.local else "repo-pins",
                      project_pins=pins, installed_versions=local,
                      disclaimer="No application build, supply-chain scan, or release acceptance")
        print(json.dumps(result, indent=2) if args.json else
              f"PASS {result['scope']}: Flutter {pins['ci_flutter']}, CI Rust {pins['ci_rust']}")
        return 0
    except (PreflightError, OSError, KeyError, ValueError, tomllib.TOMLDecodeError) as exc:
        if args.json:
            print(json.dumps(dict(status="fail", error=str(exc))))
        else:
            print(f"FAIL development toolchains: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
