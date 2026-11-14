#!/usr/bin/env python3
"""Offline narrow check of two AppFlowy-derived Flutter Git dependency overrides."""
from __future__ import annotations
import re
import sys
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1] / "frontend/appflowy_flutter"
SHA = re.compile(r"[0-9a-f]{40}\Z")
REVIEWED = {
    "url_protocol": "https://github.com/LucasXu0/flutter_url_protocol.git",
    "flutter_cache_manager": "https://github.com/LucasXu0/flutter_cache_manager.git",
}

class OverrideError(ValueError):
    pass

def block(lines: list[str], name: str, indent: int) -> list[str]:
    starts = [i for i, line in enumerate(lines) if line == " " * indent + name + ":"]
    if len(starts) != 1:
        raise OverrideError(f"expected exactly one block: {name} at {indent}")
    start = starts[0] + 1
    end = start
    for idx in range(start, len(lines)):
        line = lines[idx]
        if line.strip() and len(line) - len(line.lstrip(" ")) <= indent:
            break
        end = idx + 1
    return lines[start:end]

def field(lines: list[str], name: str, indent: int) -> str:
    pattern = re.compile("^" + " " * indent + re.escape(name) + r":\s*(.*?)\s*$")
    values = [m.group(1).strip("\"'") for line in lines if (m := pattern.fullmatch(line))]
    if len(values) != 1 or not values[0]:
        raise OverrideError(f"expected one nonempty {name} field at {indent}")
    return values[0]

def verify(pubspec: str, lockfile: str) -> dict[str, str]:
    if re.search(r"(?m)^ +commit\s*:", pubspec):
        raise OverrideError("unsupported Git commit selector: use ref")
    override = block(pubspec.splitlines(), "dependency_overrides", 0)
    packages = block(lockfile.splitlines(), "packages", 0)
    result = {}
    for name, expected_url in sorted(REVIEWED.items()):
        declared = block(override, name, 2)
        git = block(declared, "git", 4)
        fields = [re.match(r"^ {6}([a-zA-Z_-]+):", x) for x in git]
        if any(m and m.group(1) not in {"url", "ref", "path"} for m in fields):
            raise OverrideError(f"unsupported Git field for {name}")
        requested = field(git, "ref", 6)
        url = field(git, "url", 6)
        locked = block(packages, name, 2)
        details = block(locked, "description", 4)
        pinned = field(details, "resolved-ref", 6)
        lock_ref = field(details, "ref", 6)
        if field(locked, "source", 4) != "git":
            raise OverrideError(f"{name} is not a locked Git dependency")
        if url != expected_url or field(details, "url", 6) != expected_url:
            raise OverrideError(f"{name} remote changed; requires manual review")
        if not SHA.fullmatch(requested) or requested != lock_ref or requested != pinned:
            raise OverrideError(f"{name}: manifest and lockfile must select the same full Git commit")
        result[name] = requested
    return result

def main() -> int:
    try:
        approved = verify((PACKAGE / "pubspec.yaml").read_text(),
                          (PACKAGE / "pubspec.lock").read_text())
    except (OverrideError, OSError) as exc:
        print(f"FAIL Flutter Git overrides: {exc}", file=sys.stderr)
        return 1
    print(f"PASS {len(approved)} reviewed Flutter Git overrides match resolved locked commits")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
