# First-party Rust code generation — output-path review

The eleven imported first-party build.rs scripts invoke inherited flowy_codegen helpers. This review covers five source files containing their direct file/output helper implementations. The code generator can create directories, write or truncate generated Rust/Dart files, inspect local templates and files, and invoke a vendored Protobuf compiler. Some output paths depend on CARGO_MAKE_WORKING_DIRECTORY and FLUTTER_FLOWY_SDK_PATH environment variables; they are not confined by Cargo itself. This source inspection does not establish complete trust, and transitive crates, proc-macros, compiler/linker executable behavior and native binary provenance remain unreviewed.

A no-execution SHA256 source snapshot is committed in .goreecloud/rust-codegen-source-review.json; the verification tool rejects any changed or missing reviewed source file. The optional environment preflight rejects missing paths, out-of-root destinations and simple symlink redirections for declared Dart SDK output destinations, but it DOES NOT constrain where the Rust generator can actually write or guarantee protection against races.

Run these read-only checks before reviewing an application build:

    python3 tools/codegen_output_review.py verify
    python3 tools/codegen_output_review.py report

For opt-in declared output-path analysis, first create a separate user-owned scratch directory (not production data). Set GOREECLOUD_BUILD_OUTPUT_ROOT to its absolute path, CARGO_MAKE_WORKING_DIRECTORY to a directory within it, and FLUTTER_FLOWY_SDK_PATH to a relative subdirectory, then run:

    python3 tools/codegen_output_review.py check-env

This check does not run, modify or sandbox Cargo. It is only a preflight for the intended path. Do not execute third-party build scripts or code generators without a separately validated operating-system-level confinement policy and reviewed source dependencies. No network-isolation acceptance is claimed.
