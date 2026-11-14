# Isolated Linux build acceptance — imported Knowledge Workspace

**Status: controlled build investigation, not production release acceptance.** This AppFlowy-derived source lacks generated Dart parts and Rust-backed bindings by default. Rootless dependency acquisition and network-disabled compilation have been tested, but no complete Knowledge Workspace desktop executable has been verified.

## Inspect generated source requirements

Use the zero-dependency, read-only inventory:

    python3 tools/generated_source_preflight.py --json

After running reviewed source generators in a disposable workspace, optionally use the strict gate:

    python3 tools/generated_source_preflight.py --strict --json

The scanner reads direct Dart import, export and part statements. It does not generate code, check runtime behavior, compile binaries, scan dependencies or verify the contents of generated files. The import currently lacks 244 directly referenced generated files among 1,673 scanned Dart files: 143 Freezed parts, 10 other Dart-generated parts, 81 Rust protobuf files, eight Rust event-dispatch parts, one SVG constants file and one locale-key file. These figures are a source snapshot, not the full runtime dependency graph.

The inherited generator scripts in frontend/scripts/code_generation cover localization, SVGs and build_runner. First-party Rust flowy_codegen builds protobuf messages and event dispatch. Do not invoke upstream scripts blindly: some scripts delete directories, change permissions, fetch dependencies, and invoke many generators. Review actual source and constrain every writable path to a disposable scratch tree before execution.

## Two-phase rootless isolation

1. Verify Flutter/Dart and Rust pin consistency with the existing development toolchain preflight. Prepare user-owned disposable source and cache directories; do not mount authentication credentials, SSH keys, a user's entire home directory or production state.
2. Acquire public dependencies in a separate rootless Podman container with network access only during the fetch step. Mount source read-only. Limit CPU, memory and process count; drop Linux capabilities, set no-new-privileges and use read-only container root filesystems. Only a dedicated disposable cache/workspace is writable.
3. Verify staged crate archive checksums against Cargo.lock, inspect tar members for traversal, links and devices, and inspect executable build.rs scripts. Verify Pub cache origin metadata and exact Git checkout commits. Pub cache hash records are metadata, not independent archived-byte verification if tarballs are not retained.
4. Build only in a different rootless container with no network: network none, read-only root, cap-drop=all, no-new-privileges, user namespace, and resource limits. Mount imported source read-only; use disposable source copies solely when generator output must be written. Do not mount the user's full home directory. Test the absence of routes and the failure of outbound connections before invoking an imported build.
5. Require offline locked dependency resolution in this isolated environment. Source integrity reviews, directory access scopes, native development libraries and nested Git submodules are independent checks. Do not assume Dart Pub offline mode by itself blocks Git cloning.
6. Run only reviewed generation steps, then recheck generated source requirements before attempting a complete desktop build. Verify runtime linkage, local UI and default windowed behavior, accessibility, privacy, identity and security functionality, and packaging/signing before release.

## Verified checkpoint — November 13, 2026

A tested rootless network-none Podman container had no default IPv4 route, rejected outbound connections, could not view the host user's home directory and resolved Cargo's 31-package workspace metadata. Separately, a bounded acquisition container fetched the Linux-target Cargo lockfile sources. **654 of 768** registry crate archives required for this target were retained and independently SHA-256 and structure verified; 114 unacquired registry records are not claimed to be reviewed. The acquired sources included 75 crate-root Rust build scripts and four first-party-external locked Git package build scripts requiring execution-aware review.

An isolated Dart acquisition completed with the original lockfile. All **294** hosted package cache hash records matched their lockfile values, and all **15** Git packages matched their recorded commits. Linux CMake required additional keybinder-3.0 and libnotify headers; six Ubuntu package payloads were checked against package-index SHA-256 values and extracted into disposable storage, without running package-manager install scripts or changing system packages.

The full application build progressed through the Linux native plugin configuration and Dart compiler, but failed on missing generated sources. The SVG and localization generators generated three Dart files in scratch, and the official Protobuf plugin version **21.1.2**, specified by the inherited build script, passed a network-isolated protoc smoke test. Rust 1.85.0 successfully compiled an isolated flowy-ast target and a narrowly scoped first-party flowy-error protobuf generator; the latter wrote nine backend Dart files in scratch. A bounded all-package Freezed generator attempt processed thousands of actions but did not finish or commit output files before timeout.

**No complete application binary has been built, launched, signed or deployed.** None of these checks proves that third-party source is free of malware, license-compatible, or that GoreeCloud privacy and security policies have been enforced in the imported application.

## Linux native-library acceptance before launch

The Linux CMake source requires linux/flutter/dart_ffi/libdart_ffi.so
and bundles that file alongside Flutter's libflutter_linux_gtk.so. The imported
frontend/rust-lib/dart-ffi/Cargo.toml now declares both staticlib and cdylib
so the existing static-library consumers remain supported while Linux can obtain
a compatible libdart_ffi.so. This source declaration alone does not compile,
validate, stage, package, or sign the native library.

Inspect the source contract and the required native file without executing ELF:

    python3 tools/check_linux_ffi_bundle.py --json

After generating the native library in disposable storage, use --strict to
reject missing native files or invalid ELF64 x86_64 headers. Pass --bundle
with an assembled debug-bundle path under the application root to check
that the executable, native FFI and Flutter GTK libraries, and Flutter asset
directory are structurally present. This is not an exported-symbol, ABI,
dynamic-dependency, security, network, privacy or license attestation.
Use an isolated native-library audit and runtime validation before release.


To produce the Linux-native FFI artifact safely, use the reviewed Rust toolchain
and pinned Cargo.lock in an isolated network-disabled, disposable workspace.
Build the dart-ffi library target, inspect its ELF dynamic symbols and loader
requirements, then stage only the verified library in the disposable app at
linux/flutter/dart_ffi/libdart_ffi.so before invoking the inherited Linux
CMake install. The original imported CMake still controls installation of the
shared library into the bundle; do not edit live system library directories.
This documented path remains a development flow, not a release certification.

The read-only ABI cross-check identifies the nine C function exports referenced
by the imported Dart bindings. In CI, validate just the source-level contract:

    python3 tools/check_linux_ffi_exports.py --json

After building a disposable Linux shared library, inspect its dynamic symbols
without executing it:

    python3 tools/check_linux_ffi_exports.py --library /path/to/libdart_ffi.so --json

A passing dynamic-symbol scan does not verify function type compatibility or
safe runtime behavior; those remain separate tests.
