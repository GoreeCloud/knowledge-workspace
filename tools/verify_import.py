#!/usr/bin/env python3
"""Dependency-free, read-only integrity checks for GoreeCloud's AppFlowy source import."""
import hashlib
import json
import plistlib
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = json.loads((ROOT / ".goreecloud/import-manifest.json").read_text())
BRAND = "GoreeCloud Knowledge Workspace"

def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)
    print("PASS", message)

def text(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")

def main() -> None:
    require(re.fullmatch(r"[0-9a-f]{40}", MANIFEST["upstream_sha"]) is not None, "upstream commit pinned")
    require(MANIFEST["upstream_repository"] == "https://github.com/AppFlowy-IO/AppFlowy", "upstream provenance")
    require(MANIFEST["upstream_ref"] == "refs/heads/main", "upstream branch")
    for filename, expected in [("LICENSE", MANIFEST["upstream_license_sha256"]), ("UPSTREAM_README.md", MANIFEST["upstream_readme_sha256"])]:
        actual = hashlib.sha256((ROOT / filename).read_bytes()).hexdigest()
        require(actual == expected, f"{filename} matches upstream snapshot checksum")
    require("GNU AFFERO GENERAL PUBLIC LICENSE" in text("LICENSE"), "AGPL license present")
    require(MANIFEST["upstream_sha"] in text("UPSTREAM.md"), "upstream revision documented")
    require(BRAND in text("README.md"), "project identity documented")
    require('android:label="' + BRAND + '"' in text("frontend/appflowy_flutter/android/app/src/main/AndroidManifest.xml"), "Android display name")
    for os in ("ios", "macos"):
        with (ROOT / f"frontend/appflowy_flutter/{os}/Runner/Info.plist").open("rb") as handle:
            plist = plistlib.load(handle)
        require(plist.get("CFBundleDisplayName") == BRAND, f"{os} display name")
    with (ROOT / "frontend/appflowy_flutter/web/manifest.json").open(encoding="utf-8") as handle:
        web = json.load(handle)
    require(web["name"] == BRAND, "web manifest display name")
    require(f"<title>{BRAND}</title>" in text("frontend/appflowy_flutter/web/index.html"), "web document title")
    require(BRAND in text("frontend/appflowy_flutter/windows/runner/Runner.rc"), "Windows product display name")
    require(f'L"{BRAND}"' in text("frontend/appflowy_flutter/windows/runner/main.cpp"), "Windows initial window title")
    require(f"Name={BRAND}" in text("frontend/scripts/linux_distribution/deb/AppFlowy.desktop"), "Linux display name")
    require(f'gtk_window_set_title(window, "{BRAND}");' in text("frontend/appflowy_flutter/linux/my_application.cc"), "Linux initial window title")
    active = sorted(p.name for p in (ROOT / ".github/workflows").glob("*") if p.is_file())
    require(active == ["verify-import.yml"], "inherited automatic workflow execution disabled")
    archived = sorted(p for p in (ROOT / ".github/upstream-workflows-disabled").iterdir() if p.is_file())
    require(len(archived) == MANIFEST["upstream_workflows_archived"] == 12, "upstream workflows archived")
    print("PASS Import checks complete (static checks only; builds and runtime unverified)")

if __name__ == "__main__":
    main()
