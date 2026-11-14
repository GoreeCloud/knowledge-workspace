// Avoid importing dart:io into Flutter web, where Linux D-Bus is not used.
bool get networkStatusMonitorSupported => true;
