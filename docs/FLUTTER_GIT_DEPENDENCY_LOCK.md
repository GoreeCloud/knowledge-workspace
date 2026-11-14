# Flutter Git override locking — compatibility review

The inherited AppFlowy Flutter pubspec used a nonstandard Git selector called commit in two dependency_overrides. Dart documents ref as the supported selector for a Git revision. The existing lockfile recorded ref HEAD for both dependencies, so the apparent commit selectors did not enforce the revisions.

The inherited url_protocol manifest contained the short value 737681d, while the lockfile had resolved 77a84201ed8ca50082f4248f3a373d053b1c0462. The old short value could not be verified through the public source GitHub commit API on November 13, 2026. Switching to that value would be an unreviewed package change.

**Compatibility-preserving fix:** Replace the unsupported selectors with the existing locked, public source-verified 40-character revisions. Set both lockfile ref entries to those same already resolved commits. Leave the lockfile's resolved-ref fields, versions, package list and source remotes unchanged.

- url_protocol: 77a84201ed8ca50082f4248f3a373d053b1c0462
- flutter_cache_manager: fbab857b1b1d209240a146d32f496379b9f62276

Run the pure-stdlib offline contract check:

    python3 tools/verify_flutter_git_overrides.py

The checker covers two reviewed overrides, ensures their manifest refs and lockfile resolved commits match and rejects new unsupported commit keys. It does not parse arbitrary YAML, audit third-party source code, resolve transitive dependencies or guarantee future Pub resolution.

Do not assume that dart pub get --offline prevents Git network access. In a separate isolated scratch experiment with a nonexistent Git remote, Pub still attempted a Git clone. External network controls must be applied independently before any imported-app dependency resolution. After reviewing package sources and build hooks, use enforced lockfile semantics in a controlled build environment. This change does not activate archived CI, run imported code, certify the application or deploy a release.
