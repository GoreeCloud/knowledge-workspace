# Static network host references – privacy review starting point

**Status:** Source text inventory for development. This is not a network firewall, DNS filter, actual egress measurement, malware audit, privacy certification, or assertion that named services are contacted.

## Verified scan scope

The dependency-free read-only tool searches HTTP(S) URL **literals** in Dart files under frontend/appflowy_flutter/lib and Rust files under frontend/rust-lib. It groups unique hostnames without saving full URL paths or query strings that may contain credentials. The inventory includes references in comments, tests and examples as well as runtime code; it cannot resolve dynamically assembled URLs, other schemes, SDK behavior or configuration obtained at runtime.

The November 12, 2026 imported-source baseline records **41 distinct hostname literals**, including AppFlowy-related names such as appflowy.com, beta.appflowy.cloud and test.appflowy.cloud. Source appearance alone does not establish a live request or default behavior. These references merit a separate configuration/network-traffic review before production deployment, particularly because GoreeCloud is intended to be self-hostable and privacy-first.

## Commands

Verify the currently reviewed static hostnames:

    python3 tools/network_reference_audit.py verify

Generate a read-only, path-only source-reference report (no outbound requests):

    python3 tools/network_reference_audit.py report

When a new hostname appears after a source change, the CI check fails until the change is independently reviewed for purpose, transport security, consent, minimization and offline/self-hosting behavior. After review, record the exact hostname explicitly:

    python3 tools/network_reference_audit.py approve --host api.example.org

The approval command records **source-literal review**, not permission to send user data, not runtime allowlisting, and not compliance signoff. The reviewed hostname list is maintained in .goreecloud/network-host-references.json and changes must pass code review. Removed hostnames are reported as stale but are not silently deleted from the audit history.

## Privacy/security follow-up

1. Trace actual request paths, triggers and auth flows in inherited client and Rust services.
2. Run network tests in a controlled, isolated development environment with explicit authorization, data-minimized dummy accounts and reliable instrumentation; distinguish first-run, offline, sign-in and collaborative operation.
3. Review telemetry and AI endpoints, DNS and certificate validation, redirects, proxies, user data transmission, consent, data retention and vendor-specific default configurations.
4. Implement GoreeShield privacy preference/consent enforcement and Wardveil security controls where authorized. Connect GoreeCloud Identity and GoreeCloud Mesh only after vetted contracts and acceptance tests.
5. Enforce actual outbound restrictions in runtime/network policy separately; this source scanner has no enforcement capability.

No user accounts, service tokens, external URLs or test payloads were sent by this static scan.
