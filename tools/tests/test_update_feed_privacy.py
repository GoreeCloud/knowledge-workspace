"""Read-only source contract for disabling inherited upstream release egress.

Does not execute Flutter, intercept network traffic, or establish privacy
conformance of all other imported components.
"""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "frontend/appflowy_flutter/lib"


def read_source(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


class UpdateFeedPrivacyTests(unittest.TestCase):
    def test_startup_update_feed_is_unconfigured(self):
        source = read_source("startup/tasks/auto_update_task.dart")
        self.assertIn("static const String? _feedUrl = null;", source)
        self.assertIn("if (UniversalPlatform.isMobile || _feedUrl == null)", source)
        self.assertIn("if (feedUrlTemplate == null)", source)
        self.assertLess(
            source.index("if (UniversalPlatform.isMobile || _feedUrl == null)"),
            source.index("unawaited(_setupAutoUpdater())"),
        )
        self.assertNotIn("AppFlowy-IO/AppFlowy/releases/latest", source)

    def test_manual_update_cannot_open_inherited_download_page(self):
        source = read_source("shared/version_checker/version_checker.dart")
        self.assertIn("bool get hasConfiguredUpdateFeed => _feedUrl != null;", source)
        self.assertIn("if (!hasConfiguredUpdateFeed)", source)
        self.assertLess(
            source.index("if (!hasConfiguredUpdateFeed)"),
            source.index("await autoUpdater.checkForUpdates()"),
        )
        self.assertIn("GoreeCloud Linux update destination is not configured", source)
        self.assertNotIn("appflowy.com/download", source)
        self.assertNotIn("afLaunchUrlString(", source)

    def test_about_shows_local_version_when_release_channel_unavailable(self):
        source = read_source("workspace/presentation/settings/pages/about/app_version.dart")
        self.assertIn("if (!versionChecker.hasConfiguredUpdateFeed)", source)
        self.assertIn("return _buildLocalVersion(context);", source)
        self.assertIn("ApplicationInfo.applicationVersion", source)
        self.assertIn("return Text(\n      ApplicationInfo.applicationVersion,", source)

    def test_sidebar_update_prompt_hidden_without_feed(self):
        source = read_source("workspace/presentation/home/menu/sidebar/sidebar.dart")
        self.assertIn("if (!versionChecker.hasConfiguredUpdateFeed)", source)
        self.assertIn("return const SizedBox.shrink();", source)

    def test_no_unreviewed_replacement_release_url(self):
        source = read_source("startup/tasks/auto_update_task.dart")
        self.assertNotIn("https://github.com/GoreeCloud/knowledge-workspace/releases", source)
        self.assertNotIn("https://github.com/AppFlowy-IO/", source)
        self.assertNotIn("https://appflowy.com/download", source)


if __name__ == "__main__":
    unittest.main()
