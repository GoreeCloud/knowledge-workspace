#!/usr/bin/env python3
"""Read-only, static HTTP(S) host literal inventory for imported Dart/Rust source.

This tool does not perform DNS, network access, code execution, proxy enforcement,
or detection of dynamically assembled URLs and SDK-supplied endpoints.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / ".goreecloud/network-host-references.json"
SOURCE_DIRS = (
    "frontend/appflowy_flutter/lib",
    "frontend/rust-lib",
)
SOURCE_SUFFIXES = {".dart", ".rs"}
URL_PATTERN = re.compile(r"https?://[A-Za-z0-9][A-Za-z0-9.:-]*", re.IGNORECASE)
HOST_PATTERN = re.compile(r"(?=.{1,253}\Z)[a-z0-9][a-z0-9.-]*[a-z0-9]\Z|[a-z0-9]\Z")


class AuditError(Exception):
    """A security-review decision is missing or the inventory is malformed."""


def extract_hosts(source: str) -> set[str]:
    hosts = set()
    for matched in URL_PATTERN.findall(source):
        candidate = matched.rstrip(".:-")
        try:
            parsed = urlsplit(candidate)
            hostname = (parsed.hostname or "").lower()
            if hostname and HOST_PATTERN.fullmatch(hostname):
                hosts.add(hostname)
        except ValueError:
            continue
    return hosts


def scan_references(root: Path) -> dict[str, list[str]]:
    references: dict[str, set[str]] = defaultdict(set)
    for relative in SOURCE_DIRS:
        directory = root / relative
        if not directory.is_dir():
            raise AuditError(f"source directory is missing: {relative}")
        for path in directory.rglob("*"):
            if not path.is_file() or path.is_symlink() or path.suffix not in SOURCE_SUFFIXES:
                continue
            # Extremely large generated sources are handled separately; do
            # not interpret binary data or allocate large unknown content.
            if path.stat().st_size > 4 * 1024 * 1024:
                continue
            content = path.read_text(encoding="utf-8", errors="replace")
            for hostname in extract_hosts(content):
                references[hostname].add(path.relative_to(root).as_posix())
    return {host: sorted(paths) for host, paths in sorted(references.items())}


def verify_baseline(references: dict[str, list[str]], baseline: dict) -> tuple[int, int]:
    if baseline.get("schema") != 1 or baseline.get("classification") != "static-strings-not-egress-allowlist":
        raise AuditError("invalid host-inventory semantics")
    if baseline.get("upstream_revision") != "8fcee27d9bd93aad4ee0191d5d8d915d6a9a4e93":
        raise AuditError("network reference baseline is not tied to the pinned upstream snapshot")
    approved = baseline.get("reviewed_hostnames")
    if not isinstance(approved, list) or approved != sorted(set(approved)):
        raise AuditError("host inventory must be unique and sorted")
    if not all(isinstance(host, str) and HOST_PATTERN.fullmatch(host) for host in approved):
        raise AuditError("invalid domain in approved static inventory")
    unknown = sorted(set(references) - set(approved))
    if unknown:
        raise AuditError(
            "new HTTP(S) literals require privacy/security review before recording: "
            + ", ".join(unknown)
        )
    return len(references), len(set(approved) - set(references))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["verify", "report", "approve"])
    parser.add_argument("--host", action="append", default=[], help="explicitly reviewed host for approve")
    args = parser.parse_args()
    try:
        current = scan_references(ROOT)
        if args.mode == "report":
            if args.host:
                raise AuditError("--host applies only to approve")
            print(json.dumps({
                "classification": "static host references, not observed outbound traffic",
                "hosts": current,
            }, indent=2))
            return 0
        baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
        if args.mode == "approve":
            if not args.host:
                raise AuditError("approve requires an explicit --host for each reviewed hostname")
            approved = set(baseline["reviewed_hostnames"])
            for raw in args.host:
                candidate = raw.lower()
                if candidate not in current:
                    raise AuditError(f"cannot approve absent or unobserved literal host: {candidate}")
                if candidate in approved:
                    raise AuditError(f"host already recorded: {candidate}")
                approved.add(candidate)
            baseline["reviewed_hostnames"] = sorted(approved)
            BASELINE.write_text(json.dumps(baseline, indent=2) + "\n", encoding="utf-8")
            print(f"Recorded {len(args.host)} reviewed host literal(s). Inspect this change in the PR.")
            return 0
        if args.host:
            raise AuditError("--host applies only to approve")
        seen, stale = verify_baseline(current, baseline)
        print(
            f"PASS {seen} distinct source-literal HTTP(S) hosts match the reviewed reference inventory; "
            f"{stale} historical hosts no longer occur in current source."
        )
        return 0
    except (AuditError, OSError, ValueError, KeyError) as exc:
        print(f"FAIL static HTTP(S) host inventory: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
