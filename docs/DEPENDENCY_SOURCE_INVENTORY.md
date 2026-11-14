# Imported dependency lockfile source inventory

This is an offline, metadata-only integrity and origin assessment, not a Software Bill of Materials, license decision, malware scan, artifact verification, or approval to execute third-party code.

On the reviewed AppFlowy source snapshot, the Flutter lockfile contains 326 packages: 294 hosted pub.dev packages with SHA-256 digest fields, 15 Git packages pinned to 40-character resolved commits, eight local path packages and nine SDK packages. The Rust lockfile contains 823 records: 768 registry records with SHA-256 fields, 24 Git packages pinned to full revisions in four previously reviewed Git repositories, and 31 local path packages.

The source inventory check rejects unexpected source type/origin, missing or malformed hosted/registry digest fields, floating or mismatched Git revisions, unexpected local path source declarations, and changes to the reviewed source-type counts. It never downloads or reads third-party dependency bodies, invokes Git, Pub, Cargo, Flutter, network clients or build scripts.

Run from the project root:

    python3 tools/dependency_lock_inventory.py verify
    python3 tools/dependency_lock_inventory.py report

For each future lockfile change, review source origins, exact commit/revision, new packages and their license/security evidence before updating counts or policies. Keep reviewed per-file source SHA256 digests in the upstream source integrity ledger aligned with any intentional import-file edits.

The application does NOT yet have a verified complete third-party artifact inventory, dependency-license compatibility, executable build script review, offline build under enforced OS network restrictions, signed artifact, or runtime privacy acceptance. The existence of a lockfile checksum only expresses the expected artifact checksum and must never be treated as proof that the artifact was independently acquired and verified.

Special note: Dart Pub offline mode was observed to attempt a Git clone when Git dependency cache was missing. A network namespace self-test of a stricter workstation sandbox was blocked by the workstation's execution safeguards; no verified complete network isolation is claimed. Do not use this audit alone as a sandbox.
