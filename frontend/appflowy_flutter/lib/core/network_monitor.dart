import 'dart:async';

import 'package:appflowy_backend/dispatch/dispatch.dart';
import 'package:appflowy_backend/log.dart';
import 'package:appflowy_backend/protobuf/flowy-user/user_setting.pb.dart';
import 'package:connectivity_plus/connectivity_plus.dart';

import 'network_monitor_bus_stub.dart'
    if (dart.library.io) 'network_monitor_bus_io.dart' as system_bus;

class NetworkListener {
  NetworkListener() {
    // The Linux plugin starts a D-Bus signal stream immediately upon listen.
    // Without a system bus that internal asynchronous connect can fail outside
    // our stream onError handler. Preserve monitoring on supported desktops.
    if (!_systemMonitorAvailable) {
      return;
    }
    _connectivitySubscription = _connectivity.onConnectivityChanged.listen(
      (result) => unawaited(_updateConnectionStatusSafely(result)),
      // Linux can have no system D-Bus (for example a minimal sandbox).
      // An absent monitor is not a reason to abort application startup.
      onError: (Object error, StackTrace stackTrace) {
        Log.error('Connectivity stream unavailable: ${error.runtimeType}');
      },
    );
  }

  final Connectivity _connectivity = Connectivity();
  final bool _systemMonitorAvailable = system_bus.networkStatusMonitorSupported;
  StreamSubscription<ConnectivityResult>? _connectivitySubscription;

  Future<void> start() async {
    if (!_systemMonitorAvailable) {
      Log.info('Linux connectivity monitor unavailable; skipping D-Bus checks');
      return;
    }
    try {
      final result = await _connectivity.checkConnectivity();
      await _updateConnectionStatusSafely(result);
    } on Exception catch (error) {
      // Includes PlatformException and the missing D-Bus SocketException.
      // Log only its type rather than exposing connection details.
      Log.error('Connectivity check unavailable: ${error.runtimeType}');
    }
  }

  Future<void> stop() async {
    final subscription = _connectivitySubscription;
    if (subscription != null) {
      await subscription.cancel();
      _connectivitySubscription = null;
    }
  }

  Future<void> _updateConnectionStatusSafely(
    ConnectivityResult result,
  ) async {
    try {
      await _updateConnectionStatus(result);
    } on Exception catch (error) {
      // Stream callbacks must handle errors from asynchronous SDK dispatch.
      Log.error('Connectivity status update failed: ${error.runtimeType}');
    }
  }

  Future<void> _updateConnectionStatus(ConnectivityResult result) async {
    final networkType = () {
      switch (result) {
        case ConnectivityResult.wifi:
          return NetworkTypePB.Wifi;
        case ConnectivityResult.ethernet:
          return NetworkTypePB.Ethernet;
        case ConnectivityResult.mobile:
          return NetworkTypePB.Cell;
        case ConnectivityResult.bluetooth:
          return NetworkTypePB.Bluetooth;
        case ConnectivityResult.vpn:
          return NetworkTypePB.VPN;
        case ConnectivityResult.none:
        case ConnectivityResult.other:
          return NetworkTypePB.NetworkUnknown;
      }
    }();
    final state = NetworkStatePB.create()..ty = networkType;
    return UserEventUpdateNetworkState(state).send().then((result) {
      result.fold((l) {}, (e) => Log.error(e));
    });
  }
}
