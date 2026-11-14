#!/usr/bin/env python3
"""No-network Cargo manifest/lockfile Git source consistency gate."""
from __future__ import annotations
import re
import sys
import tomllib
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parents[1] / "frontend/rust-lib"
REV = re.compile(r"[0-9a-f]{7,40}\Z")
FULL_REV = re.compile(r"[0-9a-f]{40}\Z")

class CargoGitError(ValueError):
    pass

def declarations(manifest: dict) -> dict[str, str]:
    result: dict[str, str] = {}
    n = 0
    def walk(data: object) -> None:
        nonlocal n
        if isinstance(data, dict):
            if "git" in data:
                url, rev = data.get("git"), data.get("rev")
                if not isinstance(url, str) or not isinstance(rev, str) or not REV.fullmatch(rev):
                    raise CargoGitError("Git dependencies must use a reviewed 7-40 hex rev")
                if "branch" in data or "tag" in data:
                    raise CargoGitError("floating Git branch/tag declaration detected")
                uri = urlsplit(url)
                if uri.scheme != "https" or uri.hostname != "github.com" or uri.username or uri.password:
                    raise CargoGitError("unreviewed Git dependency origin")
                if url in result and result[url] != rev:
                    raise CargoGitError("conflicting Git revisions for a single repository")
                result[url] = rev
                n += 1
            for value in data.values():
                walk(value)
        elif isinstance(data, list):
            for value in data:
                walk(value)
    walk(manifest)
    if n != 13 or len(result) != 4:
        raise CargoGitError("unexpected number of reviewed direct Git dependencies or source repositories")
    return result

def verify(cargo_toml: str, cargo_lock: str) -> dict[str, int]:
    manifest = tomllib.loads(cargo_toml)
    locked = tomllib.loads(cargo_lock)
    refs = declarations(manifest)
    seen: set[str] = set()
    git_packages = 0
    for package in locked.get("package", []):
        source = package.get("source", "")
        if not isinstance(source, str) or not source.startswith("git+"):
            continue
        parsed = urlsplit(source[4:])
        url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        query = parse_qs(parsed.query)
        if url not in refs or set(query) != {"rev"} or query["rev"] != [refs[url]]:
            raise CargoGitError(f"unreviewed Git lock source in {package.get('name', '?')}")
        if not FULL_REV.fullmatch(parsed.fragment) or not parsed.fragment.startswith(refs[url]):
            raise CargoGitError(f"Git lock commit differs from manifest rev for {package.get('name', '?')}")
        seen.add(url)
        git_packages += 1
    if git_packages != 24 or seen != set(refs):
        raise CargoGitError("missing or additional Git-locked Rust package source")
    return {"manifest_git_dependencies": 13,
            "locked_git_packages": git_packages,
            "git_repositories": len(seen)}

def main() -> int:
    try:
        results = verify((ROOT / "Cargo.toml").read_text(),
                         (ROOT / "Cargo.lock").read_text())
    except (OSError, ValueError, CargoGitError, tomllib.TOMLDecodeError) as exc:
        print(f"FAIL Rust Git lock consistency: {exc}", file=sys.stderr)
        return 1
    print("PASS Rust Cargo Git lock consistency: "
          f"{results['manifest_git_dependencies']} direct refs, "
          f"{results['locked_git_packages']} locked packages, "
          f"{results['git_repositories']} source repositories")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
