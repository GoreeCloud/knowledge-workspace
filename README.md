# GoreeCloud Noteflow

**Development baseline · Rebranded Import · Not production-ready**

**Canonical repository:** https://github.com/GoreeCloud/noteflow. Formerly GoreeCloud Knowledge Workspace in the same GitHub repository; its GitHub ID and history are preserved.
The founder's November 14, 2026 rename changed the public product name,
not the inherited application's package, database, protocol or executable
identifiers. See [Noteflow rename and migration contract](docs/PRODUCT_RENAME_NOTEFLOW.md).

GoreeCloud Noteflow is an **AppFlowy-derived** open-source knowledge, document, wiki and project workspace maintained under the GoreeCloud name. This repository contains a source snapshot of the latest verified AppFlowy upstream main as of November 12, 2026, with initial user-facing display-name changes and explicit upstream attribution.

> **Status:** Source imported for development. A controlled Linux debug build and isolated virtual-display launch have been verified (November 13, 2026), but production UI, icons, account flows, security and privacy, non-Linux builds, migrations and deployment have not. Do not use this snapshot as evidence of a production-ready GoreeCloud service.

## Source and license

- **Upstream:** [AppFlowy-IO/AppFlowy](https://github.com/AppFlowy-IO/AppFlowy)
- **Pinned upstream main commit:** [8fcee27](https://github.com/AppFlowy-IO/AppFlowy/commit/8fcee27d9bd93aad4ee0191d5d8d915d6a9a4e93), dated October 28, 2026.
- **Import date:** November 12, 2026.
- **License:** GNU Affero General Public License v3.0 (AGPL-3.0), with retained upstream [LICENSE](LICENSE) and applicable nested licenses. These modifications do not relicense third-party contributions.
- **Attribution:** Original documentation is retained intact in [UPSTREAM_README.md](UPSTREAM_README.md). See [UPSTREAM.md](UPSTREAM.md) and the [machine-readable import manifest](.goreecloud/import-manifest.json).
- This is a **source import, not an official AppFlowy release**; GoreeCloud does not imply affiliation with or endorsement by AppFlowy.

## Included baseline

The inherited source includes Flutter client code and Rust components for a multi-platform workspace. Initial **GoreeCloud Noteflow** display naming is applied to select Android, iOS, macOS, Windows, Linux desktop-entry/window title and web manifest/title surfaces. Internal package IDs, database formats, deep links, binary names and third-party integrations remain at their inherited values pending compatibility review. The upstream graphics and localized application strings may still say AppFlowy.

**First-use privacy default:** When no cloud mode is saved, Noteflow selects local mode rather than the inherited AppFlowy beta cloud, unless an explicit build-time cloud endpoint was configured. Existing saved cloud selections remain supported. See [local-first cloud policy](docs/LOCAL_FIRST_CLOUD_PRIVACY.md). This is not a complete network-privacy audit.

**Privacy and release notice:** The imported AppFlowy startup update feed and manual Linux download redirect are disabled by default. No verified GoreeCloud release feed or signed update channel is configured; the About panel displays only the locally installed version without claiming it is up to date. Other imported network clients remain unaudited. See [Update source and privacy](docs/UPDATE_SOURCE_PRIVACY.md).

No integrations with GoreeCloud Identity, Mesh, GoreeShield or Wardveil have been implemented or validated by this import. GoreeCloud UI design-token adoption remains future work.

## Development starting points

- Flutter client: [frontend/appflowy_flutter/](frontend/appflowy_flutter/)
- Rust components: [frontend/rust-lib/](frontend/rust-lib/)
- Original upstream build guidance: [Flutter README](frontend/appflowy_flutter/README.md) and [UPSTREAM_README.md](UPSTREAM_README.md)
- Import details and update procedure: [UPSTREAM.md](UPSTREAM.md)
- Static import validator: run python3 tools/verify_import.py
- Whole-import file integrity check: run python3 tools/source_integrity.py verify; see [Source integrity guide](docs/SOURCE_INTEGRITY.md).
- Static network-reference review: run python3 tools/network_reference_audit.py verify (or report); see [Network reference audit](docs/NETWORK_REFERENCE_AUDIT.md). This does not enforce egress restrictions.
- Developer toolchain preflight: run python3 tools/check_development_toolchains.py --json (add --local on a configured Linux workstation); see [development toolchains](docs/DEVELOPMENT_TOOLCHAINS.md).

**Security:** Inherited upstream GitHub Actions are archived under .github/upstream-workflows-disabled/ so release, publishing, messaging and credential-dependent automations do not run in this repository without independent review. The only active workflow is the minimal, read-only import validator.

## Next acceptance gates

1. Review inherited dependencies, workflows, network endpoints and authentication flows; remove or constrain unnecessary services.
2. Complete GoreeCloud UI rebranding without changing legal notices or compatibility-critical package IDs blindly.
3. Build and test supported targets; review privacy and accessibility; add signed and reproducible release processes.
4. Integrate GoreeCloud Identity, GoreeCloud Mesh, GoreeShield privacy controls and Wardveil cybersecurity controls where appropriate and verified.
5. Define deployment, backup, recovery, upstream-update and maintenance procedures before release.

Contributions must retain applicable copyright and attribution, and comply with the AGPL-3.0 and any additional per-component terms.

## Isolated Linux development build readiness

The imported application requires generated Dart and Rust-backed files not committed in this repository. Run python3 tools/generated_source_preflight.py --json for a read-only inventory, and add --strict only after reviewed generators have completed in a disposable environment. A separately recorded, rootless, network-disabled Linux debug build and an isolated headless window startup passed on November 13, 2026. See docs/ISOLATED_LINUX_BUILD.md for the exact limits. Import-metadata CI does not run that full native build or certify security, features, or deployment.
