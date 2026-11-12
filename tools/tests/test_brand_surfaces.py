"""Source-level checks for the intentionally scoped GoreeCloud display identity."""

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
FLUTTER = ROOT / "frontend/appflowy_flutter"
DISPLAY = "GoreeCloud Knowledge Workspace"


class ProductIdentityTests(unittest.TestCase):
    def test_one_canonical_display_name(self):
        source = (FLUTTER / "lib/goreecloud/workspace_identity.dart").read_text()
        self.assertIn("const String goreeCloudWorkspaceDisplayName = '" + DISPLAY + "';", source)
        self.assertIn("compatibility/migration plan", source)

    def test_mobile_header_uses_shared_identity_and_ellipsis(self):
        source = (FLUTTER / "lib/mobile/presentation/home/mobile_home_page_header.dart").read_text()
        self.assertIn("goreeCloudWorkspaceDisplayName,", source)
        self.assertIn("overflow: TextOverflow.ellipsis", source)
        self.assertNotIn("FlowyText.medium('AppFlowy'", source)

    def test_window_title_is_display_only(self):
        source = (FLUTTER / "lib/startup/tasks/windows.dart").read_text()
        self.assertIn("this.title = goreeCloudWorkspaceDisplayName", source)
        self.assertNotIn("this.title = 'AppFlowy'", source)

    def test_locale_app_name_without_translation_data_rewrite(self):
        locale = FLUTTER / "assets/translations/mr-IN.json"
        self.assertEqual(json.loads(locale.read_text())["appName"], DISPLAY)

    def test_flutter_test_declares_public_identity(self):
        test = (FLUTTER / "test/goreecloud/workspace_identity_test.dart").read_text()
        self.assertIn("goreeCloudWorkspaceDisplayName", test)
        self.assertIn(DISPLAY, test)


if __name__ == "__main__":
    unittest.main()
