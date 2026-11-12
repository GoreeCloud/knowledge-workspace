# GoreeCloud UI integration – verified scope and next steps

This project is an AppFlowy-derived Flutter/Rust source import. The founder's GoreeCloud UI design authority is maintained separately at https://github.com/GoreeCloud/gc-ui. Its verified alpha design-language reference was reviewed on 2026-11-12.

## Implemented in this change

- One Dart compile-time constant drives the mobile personal-workspace header and desktop window title.
- The header uses a one-line ellipsis treatment for the deliberately long name.
- The Marathi locale appName field is updated without rewriting neighboring translations.
- Existing package imports, internal identifiers, storage paths, URL schemes and executable filenames remain unchanged.

## Adoption requirements (not yet implemented)

GC UI defines Cloud Canvas, Cloud Surface and Cloud Lens; semantic color roles; 4px spacing increments; 44px control minimums; reduced-motion and increased-contrast requirements; and both light and dark appearances. There is **no mandatory GoreeCloud color or global hue**. Iris, Lagoon, Ember and Moss are optional curated presets. Values in gc-ui are alpha candidates, not a universal required theme or a published native Flutter SDK.

Implementing a GC UI Flutter adapter requires separately reviewing AppFlowy's inherited theme and accessibility code, preserving user-controlled appearance, and testing actual platform navigation and contrast. This change intentionally does not impose new colors or copy upstream brand graphics. Any replacement imagery must use verified GoreeCloud brand assets and retain legal notices.

## Important limitations

The original AppFlowy package identifiers, deep links, executable names, some icons, notifications, onboarding materials and other strings remain. Changing them without migrations risks existing user data, external links, background integrations and build compatibility. All GoreeCloud Mesh, GoreeShield, Wardveil and Identity integrations remain unverified.

Run the lightweight brand-contract tests with:

    python3 -m unittest discover -s tools/tests -p test_brand_surfaces.py -v

Run the Flutter test when a verified Flutter SDK and dependencies are available:

    cd frontend/appflowy_flutter
    flutter test test/goreecloud/workspace_identity_test.dart
