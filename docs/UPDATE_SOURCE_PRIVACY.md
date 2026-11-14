# Update source, privacy and release readiness

**Status: disabled by default. No verified GoreeCloud update feed or signed release.**

The imported desktop code originally scheduled a request to AppFlowy's
GitHub appcast feed during startup. The Linux manual update path opened the
upstream AppFlowy website. That is inappropriate for a GoreeCloud-branded
development import and can disclose launch activity to unrelated services.

Until a maintained and approved GoreeCloud release channel exists, the imported
update feed is deliberately unset. The startup task does not request appcast
metadata or initialize native updater listeners; the Linux manual update path
no longer opens the upstream site. The About page shows the locally installed
version without asserting that an unverified release is current or offering a
nonfunctional update button. The sidebar upgrade prompt is also suppressed
until an approved update feed exists. No alternative update URL has been invented.

Before enabling an update channel, independently review provenance, release
signatures, appcast ownership, least-privilege installer access, rollback,
operating-system targets, user control and consent. Preserve appropriate
GoreeShield privacy requirements and Wardveil update-chain security controls.

**Evidence limits:** These are static source and guardrail changes only; they
do not prove runtime network isolation, consent enforcement in other modules,
absence of third-party telemetry, a verified release process, or a production
deployment. Imported AppFlowy code remains AGPL-3.0 with preserved attribution.
