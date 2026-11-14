# Development toolchain preflight — Linux

**Scope:** Developer workstation setup for the AppFlowy-derived GoreeCloud Knowledge Workspace. Passing these checks does not establish that the full application builds, runs or is ready for release.

## Verified source constraints

The inherited archived .github/upstream-workflows-disabled/flutter_ci.yaml pins **Flutter 3.27.4** and **Rust 1.85.0**. Flutter 3.27.4 includes Dart 3.6.2. The application pubspec.yaml requires Flutter >=3.27.4 and Dart >=3.3.0, <4.0.0. Both inherited Rust rust-toolchain.toml files request the broader **1.85** channel, which currently selects Rust 1.85.1, not necessarily the exact CI pin.

Linux desktop builds additionally require Clang/clang++, CMake, Ninja, pkg-config, GTK3 development headers, and a C++ toolchain. Flutter doctor checks these requirements. Android requires compatible Java and Android SDK/build tools plus explicit review and acceptance of any outstanding SDK licenses. Chrome is needed for web browser tests, but not for Linux desktop tests.

## Commands

Run the dependency-free read-only source-pin check in the repository root:

    python3 tools/check_development_toolchains.py --json

To opt in to local Linux compiler version checks:

    python3 tools/check_development_toolchains.py --local --json
    flutter doctor -v

The optional local check does not install SDKs, fetch application dependencies, accept licenses, execute imported build scripts or activate archived workflows. It disables Flutter/Dart analytics for the version commands and disables Rustup auto-install of a missing compiler during inspection.

## Ordered validation

1. Install official checked Flutter/Dart and Rust toolchains at the verified project versions, preferring isolated user-owned directories unless privileged system installation is explicitly authorized.
2. Install/test Clang, CMake, Ninja, pkg-config and GTK3 build headers before attempting Linux desktop builds; check flutter doctor.
3. Create and build a disposable app from the verified Flutter SDK template before attempting the imported AppFlowy application. Record temporary smoke evidence separately from product acceptance.
4. Independently review third-party dependencies, executable build scripts, native library and ABI compatibility, telemetry, network endpoints and licensing before fetching and executing application dependencies.
5. Perform actual Flutter/Rust application tests, user interface checks, privacy/security controls and release validation in separately scoped work.

Product responsibilities remain distinct: GoreeCloud UI provides design authority, GoreeShield governs privacy, Wardveil governs cybersecurity, GoreeCloud Mesh governs integration and GoreeCloud Identity governs authentication/authorization.
