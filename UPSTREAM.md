# Upstream provenance and maintenance

This repository is a **rebranded, attributed source snapshot** of [AppFlowy](https://github.com/AppFlowy-IO/AppFlowy), not a first-party implementation of its inherited functionality and not an official upstream distribution.

| Property | Verified value |
| --- | --- |
| Source repository | https://github.com/AppFlowy-IO/AppFlowy |
| Source branch | main |
| Source commit | 8fcee27d9bd93aad4ee0191d5d8d915d6a9a4e93 |
| Upstream commit date | 2026-10-28 |
| Import snapshot date | 2026-11-12 |
| Inherited tracked file count | 4,597 |
| Primary upstream source license | AGPL-3.0 (LICENSE) |
| Original source README | UPSTREAM_README.md, retained verbatim |
| Workflow safety | 12 inherited workflows relocated to .github/upstream-workflows-disabled/ |

The original upstream license file and existing additional component licenses and notices are retained. Copyright on inherited work stays with its respective holders. GoreeCloud-authored modifications are identified by Git history. Do not remove vendor credits, assume rights over AppFlowy trademarks, or change license obligations through bulk replacement.

## Changes in the initial snapshot

- Added GoreeCloud README, provenance manifest and static validation.
- Applied **display names only** in selected Android, iOS, macOS, Windows, Linux and web entry points.
- Archived inherited CI/CD workflows (including upstream publishing and secret-backed integrations) as inert historical material.
- Preserved internal identifiers, signing settings, deep links, package names, database keys and compatibility-sensitive source semantics.

**Known limitations:** Many strings, logos, illustrations, app identifiers and service references still use upstream names or endpoints; no full rebranding or privacy audit has been completed. Source presence does not prove successful builds, feature equivalence, integration, functional security, or stable deployment.

## Future update procedure

1. Review the current source branch and exact commit; inspect source changes, licenses, third-party dependencies, secrets and CI/CD definitions.
2. Fetch upstream into a separate review branch (git fetch upstream main). **Never** blindly mirror upstream to the production branch or activate imported workflows.
3. Compare the reviewed source revision against this pinned baseline; apply controlled changes while preserving GoreeCloud-specific display naming and notices.
4. Re-run python3 tools/verify_import.py, dependency and vulnerability checks, and platform builds/tests when toolchains and test environments are available.
5. Review source-code attribution and AGPL-3.0 network-service source availability obligations before deployment.
6. Record the revised upstream SHA and verification evidence, and advance to release only after independent acceptance gates pass.

## GoreeCloud ecosystem design intent

GoreeCloud UI owns design language; GoreeCloud Mesh owns interoperability; GoreeCloud Identity owns authentication; GoreeShield owns privacy and consent; Wardveil owns cybersecurity and incident response. These are *planned integration boundaries*, not claims of implemented connectivity.

## Imported source integrity gate

The machine-readable file registry at .goreecloud/upstream-source-digests.json records SHA-256 digests for all 4,597 upstream files, with mapped paths and reviewed rebranding changes. Run python3 tools/source_integrity.py verify to check file presence and reviewed import digests. The validator is offline and read-only; it does not certify the absence of malicious code. Consult docs/SOURCE_INTEGRITY.md before revising any imported file checksum.
