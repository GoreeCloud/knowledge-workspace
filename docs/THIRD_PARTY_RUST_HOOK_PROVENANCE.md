# Third-party Rust executable hook provenance — offline development gate

**Status: partial cached-source provenance verification, not a security certification or release gate pass.**

The imported GoreeCloud Noteflow Rust Cargo.lock fixes registry packages by
package name, version, crates.io origin, and archive SHA-256. A compiled crate
may execute its build.rs, and a procedural macro may execute arbitrary code
during compilation. A sandboxed build alone is not a malware-free verdict.

## Reproduce read-only locked-source verification

From the repository root:

    python3 tools/third_party_rust_hook_audit.py --json

This no-cache mode reads **only the tracked lockfile** and reports
lock_only_source_not_inspected. It does not fetch any package or claim that
absent sources are safe.

For a separately acquired, disposable Cargo cache:

    python3 tools/third_party_rust_hook_audit.py \
      --source-root "/path/to/cargo/registry/src/index.crates.io-CACHE_ID" \
      --archive-root "/path/to/cargo/registry/cache/index.crates.io-CACHE_ID" \
      --json > /path/to/disposable/read-only-audit.json

The stdlib-only scanner does not load modules from dependencies, execute
Cargo, macros, build scripts or other subprocesses, or make network requests.
For each matching locked registry package it verifies the cached .crate archive
SHA-256 against Cargo.lock, then requires the cached Cargo.toml, build-script
source (where present), and each proc-macro entry file to match the archive's
bounded regular members byte-for-byte. It rejects checksum/source mismatches,
unsafe symlinks, path traversal, and oversized files. --strict rejects missing
source/archive coverage.

**Scope limits:** It does not compare every nested source module to the
archive. The archive checksum authenticates the complete archive bytes, but
extracted-source comparison is limited to manifests, hooks, and macro entries.
Cargo Git checkouts, local crates, Dart plugins, executable behavior, and
transitive downloaded build tools require separate review. Pattern indicators
are review hints, not confirmed vulnerabilities.

## November 14, 2026 observed development cache

A bounded read-only scan of previously acquired isolated development cache:

| Measure | Observed |
| --- | ---: |
| Registry package name/version records in Cargo.lock | 768 |
| Cached sources matched to locked archive checksum and inspected hook/entry source | 654 |
| Locked registry source packages absent in this cache | 114 |
| Archive missing for any of the 654 matched sources | 0 |
| First-party Rust build scripts (existing separate audit) | 11 |
| Third-party cached build scripts | 79 |
| Cached third-party procedural-macro crates | 57 |
| Process invocation text indicators in build scripts | 18 |
| Network/download-related text indicators | 27 |
| Filesystem-write text indicators | 24 |
| Native-toolchain text indicators | 9 |

Some absent source packages may be irrelevant to this Linux target, but
platform relevance has not been exhaustively determined. The reported hook
counts describe only the verified cached sources. Raw machine-readable
source-path-free evidence remains in disposable private development storage
and is not represented as a complete security or license audit.

A separate source check of cached Flutter Linux CMake plugins found optional
GoogleTest FetchContent archives in the test-only sections of
file_selector_linux, url_launcher_linux, and screen_retriever_linux. These
archive downloads were not activated in the verified normal debug build.
Enable plugin tests only after authorized source acquisition and checksum
pinning. Their URLs inside conditional code are not evidence of runtime egress.

## Open acceptance work

1. Classify and acquire any required portion of the 114 absent locked
   packages through authorized, separate, security-reviewed acquisition.
2. Review behavior of 79 build scripts, 57 procedural macros and Cargo Git
   checkout code beyond literal-pattern triage.
3. Complete comprehensive source licenses, SBOM, build-output provenance,
   optional CMake test hooks, Wardveil and GoreeShield acceptance.
4. Validate desktop data workflows, user control and accessible behavior,
   then authorize and sign any release independently.

CI runs lock-only inspection and scanner fixture tests, not a source-cache
audit, and must not claim full source review when it lacks acquired sources.
