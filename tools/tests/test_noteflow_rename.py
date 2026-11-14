"""Cross-platform, display-only Noteflow product rename contract.

Review and protect user-facing names without migrating inherited storage IDs,
protocol schemes, app packages, upstream copyright or imported binaries.
"""
import json
import plistlib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / "frontend/appflowy_flutter"
NAME = "GoreeCloud Noteflow"
OLD = "GoreeCloud Knowledge Workspace"


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


class NoteflowIdentityTests(unittest.TestCase):
    def test_canonical_metadata_preserves_upstream_provenance(self):
        manifest = json.loads(read(".goreecloud/import-manifest.json"))
        self.assertEqual(manifest["project"], NAME)
        self.assertEqual(manifest["previous_project_name"], OLD)
        self.assertEqual(manifest["upstream_repository"], "https://github.com/AppFlowy-IO/AppFlowy")
        self.assertEqual(manifest["upstream_license"], "AGPL-3.0")
        self.assertIn("https://github.com/GoreeCloud/noteflow", read("README.md"))

    def test_main_platform_surfaces_share_new_name(self):
        for file in (
            "frontend/appflowy_flutter/android/app/src/main/AndroidManifest.xml",
            "frontend/appflowy_flutter/linux/my_application.cc",
            "frontend/appflowy_flutter/windows/runner/main.cpp",
            "frontend/appflowy_flutter/windows/runner/Runner.rc",
            "frontend/appflowy_flutter/web/index.html",
            "frontend/appflowy_flutter/pubspec.yaml",
            "frontend/scripts/linux_distribution/deb/AppFlowy.desktop",
            "frontend/scripts/linux_distribution/packaging/io.appflowy.AppFlowy.launcher.desktop",
        ):
            with self.subTest(file=file):
                content = read(file)
                self.assertIn(NAME, content)
                self.assertNotIn(OLD, content)

    def test_macos_ios_launch_labels(self):
        for os in ("ios", "macos"):
            with self.subTest(os=os):
                with (APP / os / "Runner/Info.plist").open("rb") as handle:
                    plist = plistlib.load(handle)
                self.assertEqual(plist["CFBundleDisplayName"], NAME)

    def test_web_manifest_labels_and_nonplaceholder_description(self):
        manifest = json.loads((APP / "web/manifest.json").read_text())
        self.assertEqual(manifest["name"], NAME)
        self.assertEqual(manifest["short_name"], "Noteflow")
        self.assertNotEqual(manifest["description"], "A new Flutter project.")

    def test_shared_dart_imports_and_identity_test(self):
        for file in (
            "frontend/appflowy_flutter/lib/goreecloud/noteflow_identity.dart",
            "frontend/appflowy_flutter/lib/mobile/presentation/home/mobile_home_page_header.dart",
            "frontend/appflowy_flutter/lib/startup/tasks/windows.dart",
            "frontend/appflowy_flutter/test/goreecloud/noteflow_identity_test.dart",
        ):
            with self.subTest(file=file):
                self.assertIn("goreeCloudNoteflowDisplayName", read(file))
        for file in (
            "frontend/appflowy_flutter/lib/startup/tasks/windows.dart",
            "frontend/appflowy_flutter/lib/mobile/presentation/home/mobile_home_page_header.dart",
        ):
            self.assertIn("goreecloud/noteflow_identity.dart", read(file))
        self.assertFalse((APP / "lib/goreecloud/workspace_identity.dart").exists())

    def test_windows_runner_compiles_lookup_and_guards_missing_window(self):
        source = read("frontend/appflowy_flutter/windows/runner/main.cpp")
        self.assertIn('FindWindowA(NULL, "GoreeCloud Noteflow");', source)
        self.assertIn("if (handle != nullptr)", source)
        self.assertLess(source.index("if (handle != nullptr)"),
                        source.index("GetWindowPlacement(handle, &place);"))
        self.assertIn('CreateMutex(NULL, TRUE, L"AppFlowyMutex")', source)
        self.assertIn("const DWORD mutex_status = GetLastError();", source)
        self.assertIn("mutex_status == ERROR_ALREADY_EXISTS", source)
        self.assertLess(source.index("const DWORD mutex_status = GetLastError();"),
                        source.index("FindWindowA(NULL,"))


    def test_do_not_silently_change_native_app_identity(self):
        cmake = read("frontend/appflowy_flutter/linux/CMakeLists.txt")
        self.assertIn('set(BINARY_NAME "AppFlowy")', cmake)
        self.assertIn('set(APPLICATION_ID "io.appflowy.appflowy")', cmake)
        android = read("frontend/appflowy_flutter/android/app/src/main/AndroidManifest.xml")
        self.assertIn('android:scheme="appflowy-flutter"', android)

    def test_marathi_app_name_is_canonical(self):
        value = json.loads(read("frontend/appflowy_flutter/assets/translations/mr-IN.json"))
        self.assertEqual(value["appName"], NAME)


if __name__ == "__main__":
    unittest.main()
