# Changelog

## 0.16.0 — 2026-11-06

### Added

- Lottie image inventory and explicit PNG embedding into a separate candidate.
  Image identities, physical dimensions and byte hashes remain distinct from
  Camtasia source IDs and clocks. Stored resource paths are never followed;
  original inputs, geometry, layers, colors, fonts and unfamiliar data survive.
- Native present/relocated save-and-render pairs compare the helper-produced
  image with an absolute-path image and direct PNG. Embedded images survive
  with the original location absent; linked images disappear. Font/glyph
  coverage, other render resources and general project packing remain outside
  this image-only feature.

## 0.15.0 — 2026-11-05

### Added

- Quiz authoring, editing, exact-XML pin/unpin, retiming and removal on existing
  standalone frozen recordings and stitched parents. Frozen points use a
  local-zero clock independently of source-frame selection; stitched points
  retain source positions, trims and inverse speed. Hidden stitched children
  and linked variants remain refused.
- Independent native pin/unpin captures and a six-quiz runtime sequence for
  authored, unpinned and explicitly retimed points. Fresh native saves retain
  exact XML and repeat byte-for-byte; removed points remain absent from export.

## 0.14.0 — 2026-11-05

### Added

- Hotspot construction, action edits and removal on existing standalone frozen
  recordings and stitched parents. Held markers use a local-zero clock while
  retaining source-frame selection; stitched markers retain trim/source timing
  and inverse speed. Hidden stitched children and linked variants are refused.
- Independent native constructor and marker captures, plus repeatable web-player
  controls for Continue, Time, URL and Marker on both new owner forms. Fresh
  reopening preserves the accepted marker identities and complete decoded AV.
  A failed synthetic forward-reference roundtrip is documented separately;
  cached seek success alone does not prove retained Marker ownership.

## 0.13.0 — 2026-11-05

### Added

- Version-2 typed-double visual-effect curves with per-segment exponential,
  bounce and spring easing. Version-1 linear inputs retain their contract.
  Explicit effect-frame easing preserves matching known visual intervals and
  unrelated geometry, linked effect tokens/mirrors, audio and source clocks.
- Native Sepia easing captures and independent rendered controls for trimmed
  2× linked AV, a 2× Group, mixed curves, clearing, bypass, geometry and audio.
  Spring overshoot and constant-frame reconstruction remain explicit.

## 0.12.0 — 2026-11-05

### Added

- Atomic composition staging for explicit media and root/Group track matte edits.
  Linked aliases and duplicate physical targets are refused; any failed edit
  leaves the source and candidate path untouched. Existing intensity curves,
  linked visual identities, audio and unrelated payload keep their contracts.
- Native comparison controls for media-only, track-only, combined alpha, mixed
  inversion, bypass, half intensity and clearing, with independent blue/background
  references and a separate root-scope case.

## 0.11.0 — 2026-11-05

### Added

- Media matte construction, controls, intensity curves and lifecycle edits on
  existing moving/frozen screen recordings and stitched parents. Frozen
  intensity uses its local-zero animation clock while preserving source-frame
  selection; moving/stitched owners retain source-position timing.
- Native constructor captures and independent render controls for trim/speed,
  cursor/child preservation, curve clearing, bypass and removal. Linked recording
  wrappers remain refused until their native mirrors are established.

## 0.10.0 — 2026-11-05

### Added

- Version-2 matte intensity curves with per-segment exponential, bounce and
  spring easing. Linear version-1 inputs retain their contract. Exact source
  clocks, linked visual mirrors, audio and unrelated animation payload survive.
- A native guard for the reproduced positive-time linear matte point form that
  passes the community schema but fails Mac 2026.2.4 project opening.
- Native save/reopen/render evidence for nonlinear curves, trimmed 2× linked AV
  and a 2× Group retaining an independent linear geometry curve.

## 0.9.1 — 2026-11-05

### Fixed

- Native theme duplication guidance now preserves the source UUID and label.
  The observed Duplicate operation gives the entered name to the original UUID;
  a temporary name and two native renames retain the intended source/copy roles.
- Independent copied-logo ownership and duplicate-only color/font edits now have
  native filesystem, applied-project and render evidence. Source theme/resource
  bytes remain unchanged; concrete project styling and bundled logos survive
  fresh-process reopening after the disposable themes are removed.

## 0.9.0 — 2026-11-05

### Added

- Group Quick Property inspection, guarded binding labels/order/visibility,
  native text/color values and link/unlink operations. Unknown entry descriptors
  and uniform rich-text styles survive; text ranges follow UTF-8 bytes.
- Native-template AV/image replacement and transparent clearing. Source starts
  reset, finite AV use clamps to both selected streams, fitting retains the
  original box, and longer replacement restores remembered duration. AV gain
  survives AV replacement; restoring audio after image/clear creates unity gain.
- Stable bound root IDs, fresh children across the full ID namespace on type
  changes, source-bin preservation and refusal of unsupported coupled processing.
  Theme application remains a native operation; changing mappings under an
  active theme requires its resource contract.

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
