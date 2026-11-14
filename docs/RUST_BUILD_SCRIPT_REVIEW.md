# First-party Rust build script review — initial gate

Scope: eleven inherited first-party files named build.rs under frontend/rust-lib. This inventory does not cover the 823 locked Rust packages, transitive crates' build scripts, proc-macros, dynamic linking, or executable generator functions.

At this November 13, 2026 review, the eleven directly inspected scripts invoke only two inherited project code-generation entry points:
- flowy_codegen::protobuf_file::dart_gen
- flowy_codegen::dart_event::r#gen

The second call is gated on the Dart feature in affected scripts. The invoked generator implementation is NOT inert. Its source under frontend/rust-lib/build-tool/flowy-codegen uses filesystem operations to create directories and write generated files. It reads environment variables CARGO_MAKE_WORKING_DIRECTORY and FLUTTER_FLOWY_SDK_PATH to locate generated outputs. Source inspection found a std::process::Command import and commented invocation in protobuf_file/mod.rs. This is NOT approval to execute that generator with uncontrolled paths or trust the complete dependency tree.

The accompanying reviewed JSON baseline records the 11 first-party source paths, exact file SHA256 digests and direct codegen call names. A no-execution verifier rejects added/missing/changed direct scripts and a narrow set of dangerous direct call patterns. It is intentionally a tripwire and documentation aid, NOT a comprehensive Rust parser, sandbox, threat detector, transitive dependency scanner, or production security gate.

Run locally without Cargo or Rust execution:

    python3 tools/rust_build_script_audit.py verify
    python3 tools/rust_build_script_audit.py report

For an intentional source change: inspect actual source, full invoked generators and output paths, update the original imported-source integrity ledger using its path-scoped refresh, review the inventory delta in a separate PR, verify third-party build script sources and licenses, then test build under restricted filesystem/network privileges.

Do not use this inventory to justify running any unreviewed build script, enabling inherited publishing workflows, accepting third-party SDK licenses, or declaring dependency safety.
