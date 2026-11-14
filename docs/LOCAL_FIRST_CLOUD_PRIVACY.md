# GoreeShield local-first cloud selection

**Scope:** First-use account/cloud selection in imported Knowledge Workspace.

The AppFlowy-derived source originally selected https://beta.appflowy.cloud
for a new profile with no stored cloud type. It also selected that external
service after encountering an unknown stored cloud value. In a clean isolated
Linux runtime, startup logging confirmed the effective remote beta-cloud
mode before the change.

GoreeCloud's default for an **unset** or **invalid** stored cloud selection
is now local mode. The local value is stored for ordinary new profiles and
returned for unit tests without writing storage. Existing explicit saved
cloud values are retained: 0 local, 2 AppFlowy Cloud, 3 self-hosted,
4 developer cloud. Changing one of these valid saved values without
consent is not authorized. A deliberately configured build-time cloud
endpoint is also respected when no user selection has been saved; the
inherited default AUTHENTICATOR_TYPE=2 without an endpoint is not treated
as consent. Saved cloud URLs take precedence over an explicit build endpoint. Manually selected cloud and self-hosted options
remain available; this patch does not claim they are GoreeCloud Identity
or Mesh integrations.

Startup logs only the selected authentication mode, not the entire cloud
configuration with potentially sensitive server addresses. Shared-env string
conversion is also restricted to the mode so subsequent logging cannot
accidentally print those endpoints.

**Verified bounded Linux acceptance — November 14, 2026:** The actual
Flutter 3.27.4 / Dart 3.6.2 Linux debug application rebuilt successfully in
rootless Podman with network disabled and the reviewed Rust FFI shared library.
Strict native-bundle and nine-symbol ABI checks passed. A fresh disposable
home, isolated Xvfb display, no host D-Bus and no network access yielded a live
GoreeCloud Knowledge Workspace window and startup log mode
AuthenticatorType.local. No AppFlowy beta-cloud mode or full cloud
configuration was logged. The app stayed alive, the known Linux D-Bus
fallback logged, and there were **zero** unhandled Dart or SocketExceptions.
The previous unmodified fresh-profile test had selected AppFlowy Cloud.

Static tests enforce default/invalid/explicit saved choice and build-endpoint
selection and bounded cloud logging. They are not a real-service acceptance
test. Existing explicit user-selected and deployment-configured cloud modes
remain supported in source, but those remote flows and persisted-account
migration require separate positive-path and privacy acceptance.

**Important limitations:** Source changes do not prove absence of all network
traffic or remove inherited third-party URLs from other modules. GoreeShield
consent controls, Wardveil review, GoreeCloud Identity/Mesh integration,
offline document persistence, accessibility and release acceptance remain open.
No production user data or settings should be migrated by this change.
