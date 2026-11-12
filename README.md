# GoreeCloud Knowledge Workspace

**Development baseline · Rebranded Import · Not production-ready**

GoreeCloud Knowledge Workspace is an **AppFlowy-derived** open-source knowledge, document, wiki and project workspace maintained under the GoreeCloud name. This repository contains a source snapshot of the latest verified AppFlowy upstream main as of November 12, 2026, with initial user-facing display-name changes and explicit upstream attribution.

> **Status:** Source imported for development. The complete user interface, icons, online services, account flows, builds, migrations, security posture and deployment have not been verified or fully rebranded. Do not use this snapshot as evidence of a production-ready GoreeCloud service.

## Source and license

- **Upstream:** [AppFlowy-IO/AppFlowy](https://github.com/AppFlowy-IO/AppFlowy)
- **Pinned upstream main commit:** [8fcee27](https://github.com/AppFlowy-IO/AppFlowy/commit/8fcee27d9bd93aad4ee0191d5d8d915d6a9a4e93), dated October 28, 2026.
- **Import date:** November 12, 2026.
- **License:** GNU Affero General Public License v3.0 (AGPL-3.0), with retained upstream [LICENSE](LICENSE) and applicable nested licenses. These modifications do not relicense third-party contributions.
- **Attribution:** Original documentation is retained intact in [UPSTREAM_README.md](UPSTREAM_README.md). See [UPSTREAM.md](UPSTREAM.md) and the [machine-readable import manifest](.goreecloud/import-manifest.json).
- This is a **source import, not an official AppFlowy release**; GoreeCloud does not imply affiliation with or endorsement by AppFlowy.

## Included baseline

The inherited source includes Flutter client code and Rust components for a multi-platform workspace. Initial **GoreeCloud Knowledge Workspace** display naming is applied to select Android, iOS, macOS, Windows, Linux desktop-entry and web manifest/title surfaces. Internal package IDs, database formats, deep links, binary names and third-party integrations remain at their inherited values pending compatibility review. The upstream graphics and localized application strings may still say AppFlowy.

No integrations with GoreeCloud Identity, Mesh, GoreeShield or Wardveil have been implemented or validated by this import. GoreeCloud UI design-token adoption remains future work.

## Development starting points

- Flutter client: [frontend/appflowy_flutter/](frontend/appflowy_flutter/)
- Rust components: [frontend/rust-lib/](frontend/rust-lib/)
- Original upstream build guidance: [Flutter README](frontend/appflowy_flutter/README.md) and [UPSTREAM_README.md](UPSTREAM_README.md)
- Import details and update procedure: [UPSTREAM.md](UPSTREAM.md)
- Static import validator: run python3 tools/verify_import.py

**Security:** Inherited upstream GitHub Actions are archived under .github/upstream-workflows-disabled/ so release, publishing, messaging and credential-dependent automations do not run in this repository without independent review. The only active workflow is the minimal, read-only import validator.

## Next acceptance gates

1. Review inherited dependencies, workflows, network endpoints and authentication flows; remove or constrain unnecessary services.
2. Complete GoreeCloud UI rebranding without changing legal notices or compatibility-critical package IDs blindly.
3. Build and test supported targets; review privacy and accessibility; add signed and reproducible release processes.
4. Integrate GoreeCloud Identity, GoreeCloud Mesh, GoreeShield privacy controls and Wardveil cybersecurity controls where appropriate and verified.
5. Define deployment, backup, recovery, upstream-update and maintenance procedures before release.

Contributions must retain applicable copyright and attribution, and comply with the AGPL-3.0 and any additional per-component terms.
