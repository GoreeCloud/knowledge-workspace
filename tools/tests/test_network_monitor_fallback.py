"""Static guard for tolerant Linux network-monitor startup.

Code-level safeguards only; runtime D-Bus and online/offline behavior require
isolated Linux integration testing.
"""
import unittest
from pathlib import Path

SOURCE = (
    Path(__file__).resolve().parents[2]
    / "frontend/appflowy_flutter/lib/core/network_monitor.dart"
)


class NetworkMonitorFallbackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SOURCE.read_text(encoding="utf-8")

    def test_linux_without_system_bus_skips_monitor_and_start_check(self):
        s = self.source
        io_source = SOURCE.with_name("network_monitor_bus_io.dart").read_text()
        self.assertIn("File('/var/run/dbus/system_bus_socket').existsSync()", io_source)
        self.assertIn("Platform.environment['DBUS_SYSTEM_BUS_ADDRESS']", io_source)
        self.assertIn("if (!_systemMonitorAvailable)", s)
        self.assertLess(s.index("if (!_systemMonitorAvailable)"), s.index("_connectivity.onConnectivityChanged.listen("))
        self.assertIn("Linux connectivity monitor unavailable; skipping D-Bus checks", s)

    def test_conditional_import_preserves_web_build_compatibility(self):
        s = self.source
        stub = SOURCE.with_name("network_monitor_bus_stub.dart").read_text()
        self.assertIn("if (dart.library.io) 'network_monitor_bus_io.dart'", s)
        self.assertNotIn("import 'dart:io'", s)
        self.assertIn("networkStatusMonitorSupported => true;", stub)

    def test_no_subscription_can_be_stopped_safely(self):
        s = self.source
        self.assertIn("StreamSubscription<ConnectivityResult>? _connectivitySubscription;", s)
        self.assertIn("if (subscription != null)", s)
        self.assertIn("await subscription.cancel();", s)

    def test_async_stream_has_error_callback(self):
        s = self.source
        self.assertIn("_connectivity.onConnectivityChanged.listen(", s)
        self.assertIn("onError: (Object error, StackTrace stackTrace)", s)
        self.assertIn("Connectivity stream unavailable:", s)

    def test_network_check_handles_socket_and_platform_exceptions(self):
        s = self.source
        self.assertIn("final result = await _connectivity.checkConnectivity();", s)
        self.assertIn("on Exception catch (error)", s)
        self.assertNotIn("on PlatformException catch", s)

    def test_async_sdk_dispatch_does_not_leak_future_exception(self):
        s = self.source
        self.assertIn("unawaited(_updateConnectionStatusSafely(result))", s)
        self.assertIn("await _updateConnectionStatus(result);", s)
        self.assertIn("Connectivity status update failed:", s)

    def test_error_log_avoids_full_socket_detail(self):
        s = self.source
        self.assertIn("${error.runtimeType}", s)
        self.assertNotIn("Log.error(error.toString())", s)


if __name__ == "__main__":
    unittest.main()
