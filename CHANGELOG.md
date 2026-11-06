# Changelog

## 0.8.0 — 2026-11-05

### Added

- Closed and source-backed dynamic caption editing through
  `skills/camtasia-project/scripts/captions.py`. Native audio-owned captions,
  imported `Caption` clips, recognized source words and modifier-bearing displays
  retain their separate ownership and payloads.
- Plain cue authoring with explicit media/timeline clocks, gaps and a final clear;
  occurrence-specific text corrections preserve native point timing and opaque
  fields. Recognized word edits retain source onsets and `%GAP` pause markers.
- Exact root trim/inverse-speed/offset mapping and retiming, with mirrored AV
  clocks and source-stream bounds. Closed cues carry into a trim; dynamic words
  whose onsets were trimmed away are omitted, matching native output.
- Existing dynamic display bounds, numeric controls and rich font/color edits
  preserve its placeholder, native style identity and partial rich ranges.
  Recognition remains an actual native/external transcription step; RTF values,
  nested clocks and nonzero audio source-file offsets require separate contracts.

## 0.7.0 — 2026-11-05

### Added

- Annotation construction from caller-owned standalone native templates via
  `annotations.py`, retaining complete definitions, native style identifiers,
  clocks, animations and drawing modifiers. One-sided Fade references receive
  the new clip ID; destination lane state stays intact.
- Existing static shape/text controls and uniform rich-text edits with UTF-8
  byte-range updates, native signed style codes, default-font preservation and
  declared-font inventory. Mixed/partial/animated runs refuse unsupported edits.
- Exclusive candidate staging and explicit build, canvas, clock, ID, clean-template
  and dependency checks. Vendor presets, SVG definitions and fonts remain local.

## 0.6.0 — 2026-11-05

### Added

- Native-template behavior construction and existing phase editing through
  `behaviors.py`. Explicit phase timing keeps project ticks distinct from loop
  seconds, while preserving the outer interval, names, dimensionless values,
  descriptors, reset metadata, linked mirrors, stable tokens and unchanged audio.
- Behavior bypass/removal with exclusive, idempotent candidate staging. Constructor
  clock/layout checks, separate outer/phase name restrictions and the reproduced
  static-double zero-point hazard guard prevent unsupported synthesis.
- Native entry-duration reset companions and preservation of valid default-less
  integer direction points. Animated/structured parameter patches and inactive
  phase replacement remain outside the scalar phase-edit contract.

## 0.5.0 — 2026-11-05

### Added

- Linear interval curves on existing native visual-effect double parameters via
  `effect_curves.py`, with explicit initial values, rational clip-relative times,
  exact trimmed/retimed source positions and gap holds. Linked wrapper/video
  mirrors change together; descriptors, bounds, reset metadata, stable tokens,
  other curves, audio and resources remain intact.
- Explicit curve clearing retains visual intervals and other parameters. Native
  saves may collapse a cleared constant to a scalar; subsequent curve authoring
  requires a native typed descriptor. Unknown/point parameter representations,
  conflicting owner clocks and shared interval easing are refused.

- Exact-build format-10 schema correction admits the natively observed Sepia
  identifier, retaining all other effect constraints.

## 0.4.0 — 2026-11-05

### Added

- Color LUT editing through `luts.py`: select existing installed/imported CUBE
  filenames, set intensity, all 13 observed channel/range choices, bypass and
  project-clock ease-in/out. Linked visual mirrors change together; audio,
  tokens, original preset/reset metadata and unrelated controls survive.
- Read-only resource discovery and selected-file SHA-256/CUBE audits. Conflicting
  filename/case aliases refuse instead of guessing native lookup precedence.
  Resource files remain in their native lookup locations and are never copied
  into the plugin or project by this helper.
- Typed/bare native double handling without flattening keyframes, preservation
  of zero-duration ease records, and refusal of ambiguous shared edge timing.
  Native output evidence is reused from the established LUT controls; new
  combinations and destinations still require project-specific verification.

## 0.3.0 — 2026-11-05

### Added

- Visual-effect construction from a same-build saved project through
  `effects.py add`. Copies the complete selected native payload, preserves
  wrapper/video mirror differences and reset companions, appends without
  changing existing order. Linked construction allocates a fresh stable effect
  token across the destination's visual and audio instances; direct owners
  preserve native metadata without allocating linked identities.
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
