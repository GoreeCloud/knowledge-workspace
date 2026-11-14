import 'dart:io';

// NetworkManager's Linux plugin requires a working system D-Bus connection.
// It starts an asynchronous signal stream that can fail before onError runs.
// Do not initiate that stream when the conventional socket is absent.
bool get networkStatusMonitorSupported {
  if (!Platform.isLinux) {
    return true;
  }
  final alternateAddress = Platform.environment['DBUS_SYSTEM_BUS_ADDRESS'];
  if (alternateAddress != null && alternateAddress.isNotEmpty) {
    return true;
  }
  return File('/var/run/dbus/system_bus_socket').existsSync();
}
