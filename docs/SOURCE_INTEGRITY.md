# Imported source integrity and update contract

**Status:** Dependency-free, offline source-file integrity checks. This is a maintenance and change-review safeguard; **not** a malware guarantee, signed supply-chain attestation, SBOM, runtime security test, or release acceptance.

## Scope

The GoreeCloud Knowledge Workspace import was pinned to upstream AppFlowy:

- Repository: https://github.com/AppFlowy-IO/AppFlowy
- Branch: main
- Revision: 8fcee27d9bd93aad4ee0191d5d8d915d6a9a4e93
- Upstream-tracked files: 4,597
- Mapping: 1:1, including original README copied to UPSTREAM_README.md and 12 inherited release workflows moved into inert .github/upstream-workflows-disabled/.
- Modified source files: 13 (initial ten display/manifest changes plus three further user-visible names).

Per-file upstream and reviewed import SHA-256 digests are in .goreecloud/upstream-source-digests.json. Any unexpected content drift or missing recorded file causes failure. The inventory includes files in ignored directories such as locale data and upstream development configuration examples, so their source content cannot be silently omitted.

## Read-only verification

Run from the repository root:

    python3 tools/verify_import.py
    python3 tools/source_integrity.py verify
    PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tools/tests -p 'test_*.py' -v

The single active GitHub Actions workflow calls these checks with read-only contents permission and no persisted checkout credentials. No inherited release/publishing workflow is activated.

## When a source file changes intentionally

1. Inspect the proposed source diff, license and attribution, compatibility, privacy and security implications.
2. Explicitly record each reviewed upstream-tracked source path with:

       python3 tools/source_integrity.py refresh --path path/to/reviewed-file

3. Review the resulting JSON diff. The helper records only the new imported digest and never alters upstream reference hashes or the pinned upstream revision.
4. Run all relevant checks and platform builds/tests before reviewing and merging the PR.
5. Never automatically refresh protected files: LICENSE, UPSTREAM_README.md and archived upstream workflows require a separate explicit license/provenance/workflow review.
6. New GoreeCloud-owned files remain under ordinary review; they are not appended to this historical upstream snapshot manifest.

Updating the file manifest and validator in the same PR is possible, so repository controls and source review remain necessary. Hashes demonstrate equality to a recorded review baseline, not that the upstream code was trustworthy, nor that it is still current.

## Remaining security/release gates

Audit source code, scripts and dependencies; network endpoints and telemetry; secrets and signing; consent, collection/retention and privacy; platform package and data migrations; and deployment. GoreeShield governs privacy, Wardveil governs cybersecurity, GoreeCloud Mesh governs integration, and GoreeCloud UI governs design.
