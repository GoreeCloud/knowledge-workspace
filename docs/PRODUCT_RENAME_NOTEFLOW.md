# Product rename — GoreeCloud Noteflow

**Canonical display name:** GoreeCloud Noteflow.
**Canonical public source:** https://github.com/GoreeCloud/noteflow.
**Former product name:** GoreeCloud Knowledge Workspace (the founder also
referred to GoreeCloud Knowledge Space). This is a rename of the **same**
GitHub repository, not a second import, clone, or competing application.

## Current source changes

All product-owned, already-reviewed visible identity surfaces are updated
to GoreeCloud Noteflow: Android launcher label, iOS and macOS display names,
Flutter mobile header and desktop window title, Linux GTK initial window
title and desktop-entry labels, Windows executable metadata and window
title, web document/PWA labels, Flutter package description, Marathi
appName translation, active source validation and source documentation.
The generic first-party identity helper was renamed to noteflow_identity,
and its dependent Flutter test and imports were changed consistently.

The pre-existing Windows runner FindWindowA call lacked a closing
parenthesis and is now syntactically corrected. The runner captures the
mutex error immediately before its other Win32 calls, and verifies a non-null
window handle before interacting with it. A compatibility-preserved mutex may
outlive or precede a visible window. Actual Windows compilation and runtime
are separate acceptance gates.

## Critical compatibility constraints

The imported application is still based on AppFlowy, licensed under
AGPL-3.0, with pinned upstream history and attribution. **Do not silently
replace** the original executable binary name AppFlowy, desktop package
and application ID io.appflowy.appflowy, Android/iOS bundle identifiers,
Windows single-instance mutex, appflowy-flutter URL scheme, local
database directories, authentication or native Rust/Dart binding names.
Existing profiles, protocol links, plugin paths and update compatibility
depend on these names. A data-preserving migration must separately verify
backup, rollback, storage paths, upgrade/downgrade and cross-platform
permissions before changing compatibility-critical IDs.

Existing AppFlowy graphics and icon assets are inherited and not claimed
as original GoreeCloud branding. Verified GoreeCloud UI design tokens and
assets must be adopted through a separately tested design-system migration;
no palette or replacement logo is invented by this rename.

## Verification and limits

Run Python import, checksum and brand-contract tests against tracked source,
then execute the actual Flutter identity test and desktop Linux build using
an authorized, isolated dependency cache. For Linux, require a window titled
GoreeCloud Noteflow in an isolated GUI test and preserve no-network and
fresh-profile local-first guarantees.

The controlled Linux debug build and Xvfb launch from **before** the
rename proved a window with the then-current former title. Its historical
evidence is not falsified. A renamed source tree is not proof of a newly
built or signed application. Linux display acceptance, other platform
builds, current GoreeCloud UI integration, data migration, full privacy
and Wardveil acceptance, signed release and actual user installation
remain separate gates unless explicitly verified.

No new upstream release feed, cloud endpoint, user account, signing key,
device installation or deployment is authorized by a product rename.

## Verified Linux development acceptance — November 14, 2026

The actual imported Flutter Linux debug application rebuilt from the
reviewed Noteflow Dart helper, Linux native window title and unchanged
compatibility IDs in a rootless, egress-denied Podman toolchain.
Flutter reported a successful native CMake/Ninja debug bundle and
the inherited AppFlowy executable name was retained intentionally.
Strict native bundle and nine-symbol Dart FFI checks passed.
The actual isolated Flutter identity test for
test/goreecloud/noteflow_identity_test.dart passed as well.

A separate fresh-profile, network-denied Xvfb launch created a
1280x960 window titled GoreeCloud Noteflow. The process remained
alive for the bounded smoke window. Its X11 class and a secondary
internal helper window still expose inherited AppFlowy identifiers;
those are not considered new branding. Local document editing, data
migration, Windows/macOS/mobile builds, brand artwork and signed
distribution have not been verified by this test.
