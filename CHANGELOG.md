# Changelog

## 0.3.0 — 2026-11-05

### Added

- Visual-effect construction from a same-build saved project through
  `effects.py add`. Copies the complete selected native payload, preserves
  wrapper/video mirror differences and reset companions, appends without
  changing existing order, and allocates a fresh stable effect token across
  the destination's visual and audio instances.
- Construction retains resource selectors, keyframes, edge modifiers and opaque
  fields. Timed payloads require matching complete owner clocks; retiming,
  resource replacement and new animated-control authoring remain separate work.
  Conflicting reset defaults, mismatched builds/owners and ambiguous token
  bindings refuse without changing either input.
- Generated-fixture coverage for constructor preservation, linked audio,
  template selection, clocks, tokens and exclusive candidate staging.

## 0.2.0 — 2026-11-05

### Added

- Transition preset discovery and construction from the matching local Mac
  2026.2.4 installation. Reads all 148 installed definitions without distributing
  vendor metadata or evaluating shader code; supports double, boolean and RGB
  defaults and the observed metadata-only trailing decimal syntax.
- Same-build native transition template cloning for built-in presets and saved
  customized transitions. Preserves complete attributes and opaque payloads while
  remapping root clip endpoints and duration to the destination project clock.
- Generated-fixture coverage for parser boundaries, build matching, omitted
  controls, resource/payload preservation, linked AV identities and exclusive
  candidate staging. Existing Fade and edit/remove commands remain available.

## 0.1.0 — 2026-10-29

### Added

- ACR package for Claude Code, Codex and Cursor, with four Camtasia rules, two
  skills and a read-only session context hook.
- Project inspection, partial structural validation, native hazard checks,
  source-file manifests, preservation checks and guarded candidate application
  with backups and stale-baseline protection.
- Native Mac 2025.0.3/format-9 and 2026.2.4/format-10 compatibility profiles,
  with raw community-schema discrepancies reported separately.
- Animation interval authoring, easing, empty markers and removal; explicit
  Motion Path geometry, orientation and lifecycle editing on the verified owners.
- Static editing of existing visual effects; supported media/track matte
  construction, intensity curves, bypass and removal.
- Root-track Fade construction, displayed-duration conversion, existing
  transition control editing and removal.
- Supported hotspot and quiz/survey authoring, feedback, retiming and owner
  transfer, with preserved native identities and clock mappings.
- A backed-up native save/reopen adapter and read-only process health preflight.
- Native format and output references covering annotations, behaviors, audio,
  captions, recorded cursors/clicks, Quick Properties, themes, Library packages,
  Lottie/SVG resources, video formats and Smart Player/SCORM delivery.
- Deterministic generated-fixture tests and package checks. The initial code
  gate passes 360 tests and validates 41 clean ACR distribution files.

### Scope

- Feature contracts retain their exercised build, owner and resource boundaries.
  Save acceptance, schema validity and rendered behavior are separate results.
- No vendor assets, community source code, private production media or historical
  test archives are distributed.
- Known feature gaps are tracked in GitHub issues #1–#14 and do not block the
  initial package. New capabilities follow actual project needs.
