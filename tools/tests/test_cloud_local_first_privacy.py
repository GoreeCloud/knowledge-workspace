"""Static GoreeShield cloud-default policy gate for imported Flutter sources.

Requires separate runtime tests to verify persistence, sync, network behavior,
and real configured self-hosted/remote accounts.
"""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "frontend/appflowy_flutter/lib"


def read(relative):
    return (ROOT / relative).read_text(encoding="utf-8")


class CloudLocalFirstTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cloud = read("env/cloud_env.dart")
        cls.deps = read("startup/deps_resolver.dart")
        cls.function = cls.cloud.split(
            "Future<AuthenticatorType> getAuthenticatorType() async {", 1
        )[1].split("\n}\n", 1)[0]

    def test_missing_setting_defaults_local_without_cloud_selection(self):
        fn = self.function
        null_case = fn.split("if (value == null) {", 1)[1].split("\n  }\n", 1)[0]
        self.assertIn("await useLocalServer();", null_case)
        self.assertIn("return AuthenticatorType.local;", null_case)
        self.assertNotIn("useAppFlowyBetaCloudWithURL", null_case)
        self.assertIn("!integrationMode().isUnitTest", null_case)

    def test_explicit_configured_build_cloud_respected_without_unapproved_beta(self):
        fn = self.function
        null_case = fn.split("if (value == null) {", 1)[1].split("\n  }\n", 1)[0]
        self.assertIn("Env.afCloudUrl.isNotEmpty", null_case)
        self.assertIn("configuredType.isAppFlowyCloudEnabled", null_case)
        self.assertIn("return configuredType;", null_case)
        self.assertLess(null_case.index("return configuredType;"), null_case.index("await useLocalServer();"))
        url_fn = self.cloud.split("Future<String> getAppFlowyCloudUrl() async {", 1)[1].split("\n}\n", 1)[0]
        self.assertIn("result ?? (Env.afCloudUrl.isNotEmpty ? Env.afCloudUrl : kAppflowyCloudUrl)", url_fn)

    def test_explicit_cloud_modes_remain_supported(self):
        fn = self.function
        for kind, name in (("0", "local"), ("2", "appflowyCloud"),
                           ("3", "appflowyCloudSelfHost"), ("4", "appflowyCloudDevelop")):
            self.assertRegex(
                fn, r'case "' + kind + r'":\s+return AuthenticatorType\.' + name + r';'
            )

    def test_invalid_persisted_mode_fails_local_not_upstream(self):
        fn = self.function
        default = fn.split("    default:", 1)[1]
        self.assertIn("await useLocalServer();", default)
        self.assertIn("return AuthenticatorType.local;", default)
        self.assertNotIn("useAppFlowyBetaCloudWithURL", default)

    def test_cloud_selector_still_explicitly_selectable(self):
        source = self.cloud
        self.assertIn("Future<void> useAppFlowyBetaCloudWithURL(", source)
        self.assertIn("Future<void> useSelfHostedAppFlowyCloud(", source)
        self.assertIn("Future<void> useLocalServer()", source)
        self.assertIn("await _setAuthenticatorType(AuthenticatorType.local);", source)

    def test_startup_logging_does_not_dump_cloud_configuration(self):
        self.assertIn("cloud mode:", self.deps)
        self.assertNotIn('Log.info("cloud setting: $env")', self.deps)
        to_string = self.cloud.split(
            "  @override\n  String toString() {", 1
        )[1].split("\n  }\n", 1)[0]
        self.assertNotIn("appflowyCloudConfig.toJson()", to_string)
        self.assertIn("authenticator:", to_string)


if __name__ == "__main__":
    unittest.main()
