# Rust Cargo Git dependencies — reviewed source pin alignment

At the AppFlowy source-import baseline, Cargo.toml included one branch-following Git source declaration: langchain-rust, branch af. Cargo.lock already resolved that dependency to a full immutable commit SHA: 9a319193352331fa4e5ff1dd4de43a0fbc5d0cbd. The commit was verified in the public appflowy/langchain-rust GitHub source repository on November 13, 2026.

This compatibility-preserving change replaces branch af with that exact existing resolved commit in Cargo.toml, and changes only the corresponding Cargo.lock source query parameter from branch=af to rev=the-same-existing-SHA. The resolved commit hash, package name, package version (4.6.0), dependency list and source repository do not change.

The offline verifier at tools/verify_rust_git_locks.py reads Cargo.toml and Cargo.lock with the Python standard library. It checks that all 13 reviewed direct Git declarations use a Git rev rather than floating branch/tag selectors; their lockfile source query matches; all 24 locked Git packages have a 40-hex resolved commit; and the four reviewed Git source repositories remain present. It cannot establish that any package is safe, uncompromised, license-compatible, or buildable.

Run:

    python3 tools/verify_rust_git_locks.py

For focused manifest inspection without network or executing third-party crates:

    CARGO_NET_OFFLINE=true RUSTUP_AUTO_INSTALL=0 cargo metadata --locked --no-deps --format-version 1

The metadata command checks workspace manifests only. Full dependency resolution, package scripts, proc-macros, native linking, generated data, egress, and runtime behavior remain outside this check. Do not run Cargo build or Cargo test on unreviewed dependency sources without separately staged source and build-script review and appropriate isolation.

Original source integrity hashes for exactly Cargo.toml and Cargo.lock were refreshed as part of the change. Retain the AppFlowy AGPL-3.0 notices and archived upstream publishing workflows.
