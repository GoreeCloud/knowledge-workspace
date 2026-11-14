# Linux connectivity monitoring without system D-Bus

**Scope:** Flutter desktop network status monitoring; not network egress policy.

The inherited NetworkListener on Linux uses connectivity_plus to observe
NetworkManager via system D-Bus. A minimal sandbox or recovery environment
may deliberately omit /var/run/dbus/system_bus_socket. In a headless smoke
test, the unguarded stream and synchronous check each emitted an unhandled
SocketException after the branded window appeared.

The updated listener first skips NetworkManager subscription and status
checks on Linux if the conventional system D-Bus socket is absent and no
explicit system D-Bus address is configured. A conditional Dart import keeps
the Linux-only socket check out of Flutter web builds. This avoids initiating a plugin
connection whose asynchronous exception can escape its error callback.
As a secondary safeguard it catches stream errors, failed platform
connectivity checks and asynchronous SDK event dispatch failures. These conditions log an error
category rather than a raw socket path or user system detail. When the
platform API succeeds, the existing NetworkTypePB mapping and update
dispatch are preserved. No service is installed or network permission expanded.

**Verification:** review source-level Python regression tests and an isolated
flutter build linux --debug --no-pub followed by a network-denied Xvfb
launch with an empty home and no system D-Bus. Verify that the D-Bus exceptions
are handled without aborting startup and that a GoreeCloud window appears.
Results must be recorded separately from test intentions.

**Limits:** A successful headless test does not establish reliable online
network state, permission to send telemetry, production UI acceptance, or
GoreeCloud Mesh, GoreeShield, Identity, and Wardveil integration.


## Verified bounded offline acceptance — November 14, 2026

An earlier isolated runtime produced two unhandled Dart SocketExceptions
while initializing the Linux NetworkManager plugin without a system D-Bus
socket. Adding only asynchronous error handlers did not resolve those
exceptions, because the connection attempt originated inside the dependency.

The reviewed conditional Linux socket-availability precheck was then built
into the real imported Flutter/Linux debug application. In a fresh rootless
Podman container with no network, no host system D-Bus, an empty disposable
home and a private Xvfb display, the resulting application:

- logged the intentional connectivity-monitor unavailable fallback once;
- opened a top-level GoreeCloud Knowledge Workspace window;
- remained alive for the bounded smoke test; and
- recorded **zero** unhandled Dart exceptions and **zero** SocketExceptions.

The full Python regression suite passed **90** tests and the changed source
was included in a successful native Flutter debug build. All 4,597 recorded
upstream-source digest entries matched their reviewed baseline.

A real Linux desktop with an available NetworkManager D-Bus service has not
yet been independently acceptance-tested. Other imported network clients,
internet connectivity, service availability, telemetry, permissions and
GoreeCloud Mesh/GoreeShield/Wardveil controls remain separate concerns.
