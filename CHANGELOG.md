# Changelog

## 0.52.0 — 2026-11-07

### Added

- Ordinary same-source audio-only stitched parents support closed-cue mapping,
  text/cue edits, recognized-word clocks and parent retiming, including Group
  ancestry. Internal audio/source IDs remain explicit, source skips retain joined
  holds, and audio cuts preserve exact subframe ticks independently of displays.
- The exact Mac 2026.2.4 profile admits native ordinary-audio closed points while
  retaining other parameter and recording-type checks. The shared stitch guard
  distinguishes homogeneous audio/AV children from mixed, recording or held forms.
- Fifteen native exports cover all 3,270 closed-cue and word-presence states;
  3,255 highlights match projected clocks, with fifteen observed one-frame delays
  at exact word boundaries retained as explicit native limits. Three independent
  reopen pairs reproduce complete decoded streams. Common-Group speed preserves
  uniform highlights; alternate native audio layouts can still differ in samples.

## 0.51.0 — 2026-11-07

### Added

- Ordinary same-source linked-AV stitched parents support closed-cue mapping,
  text/cue editing and parent retiming, including Group ancestry. Virtual stitch
  composition preserves word holds across source skips and retains child/source
  provenance without changing internal clips or recognition.
- Stitched mapping returns separate `words` and `displayWords`. Native parent
  speed applies an additional final-child highlight projection; the latter map
  reports observed display timing, including projected future onsets, while
  source words retain the nominal speech clock. A unit-speed stitch inside a
  sped common audio/display Group provides the verified uniform-clock alternative.
- The exact Mac 2026.2.4 schema profile admits native parent-owned caption points
  without relaxing other parameter checks. Captioned stitches require the shared
  ordinary-AV predicate; unverified layouts remain audit failures. Timeline cues
  must fit the selected clip's visible window, including trimmed root owners.
  Twenty-six native exports pass all
  4,758 frames for closed cues and highlights; six reopened/fresh-process pairs
  repeat complete decoded streams. Recording and other stitch forms remain tracked.

## 0.50.0 — 2026-11-06

### Added

- Default caption mapping includes recognized source words through Group clocks.
  A selected audio-source trim omits earlier onsets; parent cropping carries an
  already active word hold. Exact rational gaps, signed offsets and linked mirrors
  retain their own source and parent-clock roles. Closed-only mapping stays separate.
- Inspection exposes logical audio uses, physical IDs, source selection and
  container clocks even when recognized media has no closed-cue parameter.
- Group source retiming accepts actual transcription without closed cues.
  Dynamic display bounds accept explicit parent-clock start/duration, including
  signed placement, while retaining every ancestor and unrelated rich/style data.
- Nineteen native exports verify all fifteen spoken words, gap clearing, nested
  trims/speed, display bounds and independent source/display ownership. All 3,960
  mapped highlight/gap and bound-window frames pass; four reopened pairs have
  identical decoded streams. An assembled root display over grouped audio remains
  blank, establishing a measured binding limit rather than missing recognition.
- Signed audio placement reproduces the equivalent Group-trim picture but changes
  decoded samples around the opening. The measured boundary difference is documented;
  source/clock preservation does not imply identity between alternate audio layouts.

## 0.49.0 — 2026-11-06

### Added

- Closed-caption `map --closed-only` composes and crops Group clocks without
  including unverified Group source-word mappings. Plain cue authoring accepts
  source-media or visible global timeline seconds. Explicit parent-clock retiming
  changes the selected child and linked mirrors while retaining ancestor payloads.
- Twenty-six native exports verify trimmed/speed-adjusted Groups, three-level
  ancestry, signed container-relative starts, both closed-caption forms, authored
  cues and retiming. All 4,665 cue/clear frames pass; four reopened pairs reproduce complete decoded streams.
  Same-layout audio survives caption edits. Native grouping has separately
  documented audio-boundary differences from flat controls.

### Fixed

- The Mac 2026.2.4 auditor accepts omitted Caption metadata only under Group-only
  ancestry, as observed in native saves. Root metadata stays required, present
  values require objects and source documents remain unchanged.

## 0.48.0 — 2026-11-06

### Added

- Caption `rtf-text` decodes native text-only Cocoa RTF cues and `set-rtf-text`
  stages occurrence-specific substring replacement, insertion and deletion.
  Original Unicode code-point ranges retain existing formatting controls, groups,
  untouched text, point timings, global style and opaque project data.
- Explicit refusals keep embedded content, unsupported RTF representations and
  stale text outside the editor. Native rendering limits remain visible: the
  original native rich accent boundary adds a replacement glyph; the emoji
  renders as a missing glyph in both the native expected control and helper output.
- Nine eight-second native exports verify audio-owned and standalone captions,
  three byte-identical project reopens, complete cue clearing and cross-style
  edits. Three repeat pairs match complete decoded video/audio; edited outputs
  match independent native rich or previously verified plain-text controls.
- Deletions retain lexical separators between RTF tokens. A focused follow-up
  verifies the reported paragraph-token boundary, later chunks after retained
  style controls and complete clearing in both owner forms: five more native
  exports match an independent control, with two byte-identical reopens.

## 0.47.0 — 2026-11-06

### Added

- Caption `set-style` stages edits to existing global closed-caption font, size
  and foreground/background RGBA settings. Other global attributes, cue/RTF
  bodies, clocks, source words and dynamic displays survive. Inspection exposes
  the saved global settings. The native background-opacity control uses the
  background color's alpha byte; the legacy opacity scalar stays unchanged.
- Six native operation comparisons, four literal candidates and ten native
  exports verify both caption-owner forms, native styling parity, saved reloads,
  cue boundaries and audio preservation. Three independent repeat pairs and
  all native/helper combined-style outputs have identical decoded streams.
- The native foreground-alpha limit is explicit: zero removes glyph fill while
  leaving a readable black outline. RGBA inputs retain native saved units without
  promising linear blending or physical font/resource closure.
- Caption top-level and subcommand help now use the versioned JSON owner
  envelope with a help string. Help exits successfully without reading a project;
  syntax errors retain their JSON stderr and exit-code contract.

## 0.46.0 — 2026-11-06

### Added

- Timed rich-style authoring and effective-state clearing support remix text
  descendants with Group-only ancestors. Selected-child clocks retain trims and
  speed, complete UTF-8 rich states, independent geometry/outline intervals and
  every parent payload. Parent cropping does not expand the Group.
- Ten complete-state comparisons and two decoded-identical 160-second native
  exports verify three Group levels, native child trims/speed, parent clocks,
  cropped points and cleared states. All 568 sampled rich states and 320 tone
  windows match their controls. Three pre-endpoint continuous-geometry samples
  show the documented native phase variation; rich boundaries remain correct.

### Fixed

- Validation refuses the reproduced Mac 2026.2.4 positive-in-point 0.5× Group
  reload shrinkage. The existing 2× Group growth guard stays in force. Neither
  guard changes parent timing or infers behavior at unexercised speeds.

## 0.45.0 — 2026-11-06

### Added

- Animation schema 2 accepts existing remix fill/stroke RGB/opacity and shape
  stroke-width targets on root or Group-contained Callouts, including trimmed/
  speed-adjusted children and combined text/shape/glyph outlines. Coupled easing
  and removal retain initial scalars, other intervals, rich states, sizing flags,
  metadata and all ancestor payload. Fill/stroke opacity stays distinct from
  text-outline alpha; native values retain their supplied precision.
- Eleven whole-document native/helper comparisons and two decoded-identical
  168-second exports verify all five easings, palette changes, native removals,
  three Group levels and speech-bubble scale reconstruction. All 168 phase
  frames, ten full-size views, 152 paired samples and 168 audio-channel windows
  retain the exercised behavior. Seventeen profile/hazard checks pass with the
  existing raw-schema speech-bubble enum omission; no new correction is needed.

## 0.44.0 — 2026-11-06

### Added

- Animation schema 2 authors continuous text-outline width/RGBA targets on
  existing remix text Callouts, independently or with geometry. Root and
  Group-only descendants retain source clocks through trims and speed changes.
  Initial values, rich points, metadata and all ancestor payload survive.
- Easing and removal now handle coupled outline definition curves alongside
  geometry. This fixes orphaned outline animation left by marker removal.
  Unknown nested definition coupling and absent-marker orphans refuse edits;
  inspection exposes direct definition curves, including discrete rich states.
- Seven native operation comparisons and two decoded-identical 120-second
  exports verify creation, compound edits, all five easings, return intervals,
  native removals and trimmed 2× text through three Group levels. All 120 phase
  frames, five full-size views, 95 paired samples and 120 audio-channel windows
  retain the exercised behavior. Fourteen raw/profile/hazard checks pass.

## 0.43.0 — 2026-11-06

### Added

- Existing remix text definitions accept native wrapping flags and center/inside/
  outside outline placement on root or Group-contained Callouts. Static typed
  descriptors, complete text/rich states, fonts, geometry, bindings and all
  ancestor payload survive. Unknown containers, missing fields, boolean flags
  and animated/default-less parameter flattening remain refused. Wrapping off
  preserves hard newlines and can clip long fixed-box lines; thick center/inside
  outlines can consume glyph fill.
- Sixteen independently prepared candidates and two decoded-identical 136-second
  native exports verify all placements, wrapped/clipped lines, explicit newlines,
  Groups and retained timed rich font changes. All 136 phase frames, 56 paired
  root/Group samples, twelve full-size views and 272 audio-channel windows retain
  the exercised behavior. Independent glyph masks establish outline placement;
  wrapped size 44→32 text reflows from three lines to two. Thirty-eight raw/
  profile/hazard checks pass without a correction.

## 0.42.0 — 2026-11-06

### Added

- Sketch Motion drawing-time and stroke edits support trimmed/speed-adjusted
  Callouts beneath Group-only ancestor chains or on root lanes. Missing drawing
  companions can be recreated using the observed native shape; stroke-only
  edits preserve their absence. Drawing time follows the selected clip's local
  timeline while source clocks, all ancestor payload, SVG and Fade remain intact.
- Six whole-document comparisons and two independent 264-second native exports
  verify trimmed 2× and slowed nested children, typed stroke fields, color
  bindings and preserved parent cropping. Complete decoded RGB/PCM repeat
  identically; 308 inspected phase frames, 105 paired native/helper/root samples,
  twelve full-size views and 616 audio-channel windows retain the exercised
  behavior. Native UI time rounding, static-descriptor serialization and Group
  duration limits are documented. Twenty-two profile/hazard checks pass with
  the two known raw-schema omissions.

## 0.41.0 — 2026-11-06

### Added

- Existing standalone Sketch Motion annotations accept rational drawing time and
  native stroke thickness/RGB edits. Timing changes the drawing modifier while
  retaining the definition's DrawTime value, SVG, geometry, reset metadata and
  ending Fade. Inspection exposes the actual drawing modifier. Unverified owner
  clocks and unfamiliar modifier shapes remain refused.
- Seven whole-document native comparisons and two independent 120-second exports
  verify slower/instant/full-duration drawing, yellow/orange strokes, thickness
  and zero thickness. Complete decoded video/audio repeat exactly; 180 sampled
  and inspected phase frames, 84 native/helper pairs, eight full-size views and
  360 channel-specific audio windows retain the exercised behavior. Sixteen
  schema/profile/hazard checks pass with the two known raw-schema omissions.
  A full-duration draw still overlaps its independent ending Fade.

## 0.40.0 — 2026-11-06

### Added

- Static keystroke definition edits now accept existing children beneath
  Group-only ancestor chains. Child fields change while Group bounds, transforms,
  clocks, tracks, effects and metadata remain intact. Other containers remain
  refused. Native Resize Group → To Canvas Size is verified independently:
  parent bounds can crop a wider chord even when its child width is correct.
- Five definition comparisons plus a measured resize-workflow comparison and
  two independent 128-second exports verify single/two-level Groups, translated
  placement, style, modifier names and background visibility. Complete decoded
  video/audio repeat exactly; 192 sampled phase frames, 84 paired comparisons,
  96 inspected contact-sheet frames, ten full-size views and 192 audio-channel
  windows retain native/helper and independent-root parity. Twenty profile/hazard
  checks retain only the known raw-schema MacKey omission. The key-capture save
  stall and verified recovery are documented without treating the failure as a
  format rejection or a permanent editor fix.

## 0.39.0 — 2026-11-06

### Added

- Existing standalone MacKey annotations accept literal native key strings,
  style and background/modifier-name flags through definition edits. Explicit
  geometry can accompany key/style changes; omitted width, display labels,
  metadata, source and audio remain unchanged. Raw strings do not synthesize
  recorded keyboard events or infer native chord parsing and layout.
- Four whole-document comparisons and two independent 96-second native exports
  verify complete chords, Traditional keycaps, modifier names and background
  removal. Both complete decoded video/audio repeat exactly; 144 sampled phase
  frames, 48 paired samples, 72 inspected contact-sheet frames, eight full-size
  views and 144 audio-channel windows retain the exercised behavior. Two stale-
  width diagnostics omit the final key after save/reopen, documenting the need
  for matching native geometry. Fourteen profile/hazard checks retain only the
  known raw-schema MacKey omission, without a new correction.

## 0.38.0 — 2026-11-06

### Added

- Annotation definition edits expose existing static Blur/Pixelate/Spotlight
  strength, Blur inversion and Highlighter inversion/legacy RGB fields. Values
  use saved native units; existing spelling, static typed descriptors, geometry,
  reset metadata and audio survive. Missing fields, cross-kind controls and
  animated/default-less parameter flattening remain refused.
- Seven whole-document native comparisons and a 152-second save/reopen sequence
  verify strength, color, opacity and inversion against independent controls.
  Across 228 sampled phase frames, 84 paired samples, 133 inspected contact-sheet
  frames, seven full-size views and 228 audio-channel windows, the controls retain
  native/helper parity. Repeat PCM matches; repeat RGB differs on 279 frames with
  maximum frame mean difference 0.908 byte levels. Twenty profile/hazard checks
  pass with only the three known missing raw-schema kind identifiers. Native UI
  floating aliases are documented without quantizing helper inputs or claiming
  sufficient obscuration for arbitrary content.

## 0.37.0 — 2026-11-06

### Added

- Annotation definition edits accept native `resize-behavior` choices and the
  numeric `enable-ligatures` flag while preserving rich styles, including timed
  states, geometry and reset metadata. Native fitted font size remains distinct
  from its saved rich value; fixed sizing can clip text to retained bounds.
- Six whole-document native comparisons and a 128-second save/reopen sequence
  verify native/helper parity and retained timed styles/movement. Across 192
  measured phase frames, 84 paired samples, 128 inspected contact-sheet frames
  and 192 audio-channel windows, controls retain their expected states. Repeat
  PCM matches; repeat RGB has measured differences up to 0.848 mean byte levels.
  The Georgia controls establish ligature flag parity without demonstrating a
  visible glyph substitution. Twenty-three schema/profile/hazard checks pass
  without a new correction.

## 0.36.0 — 2026-11-06

### Added

- Annotation `set-rich-steps` authors cumulative discrete rich-style changes
  with whole-property or Unicode range edits on root remix text. Exact source
  clocks preserve trim/speed. `clear-rich-steps` keeps the complete style active
  at a chosen visible time while retaining text, geometry, intervals and fonts.
  Existing static text-edit commands continue to refuse timed rich payloads.
- Native save/readback and an 88-second reopen/export pair verify size, color,
  bold range, underline, clearing and independent movement. Complete decoded
  video/audio repeats exactly; 187 sampled frames, 68 paired samples, 88 inspected
  contact-sheet frames and 132 audio-channel windows retain the contract.
  Thirteen raw-schema/profile/hazard checks pass without a correction. Native
  Auto Animate text-size edits remain static; accepted timed rich frames switch
  discretely at their endpoint rather than interpolating font size.

## 0.35.0 — 2026-11-06

### Added

- Verified native linked-recording frame extensions and unstitching: a stitched
  parent contains the moving video/audio pair and a silent standalone hold.
  Existing matte commands edit one parent effect, preserve descendants and audio,
  and support cross-boundary intensity curves and unstitched held-root edits.
  Ten fixed regression tests retain the native shape, clocks and preservation.
- Five whole-document native comparisons and a 144-second save/reopen sequence
  verify lifecycle and curve readback, with 234 sampled frames, 91 paired samples,
  126 inspected contact-sheet frames and 252 audio-channel windows. Repeat PCM
  matches; repeat RGB has small measured differences (maximum mean 0.722 byte
  levels), explicitly documented alongside the native trimmed-frame picture
  limitation. Seventeen schema/profile/hazard checks need no new correction.

## 0.34.0 — 2026-11-06

### Added

- `behaviors.py copy-phase` replaces a selected entry, middle or exit phase
  from a matching saved native behavior, including activating or clearing a
  None phase. Style, timing, parameters and native integer point frames copy
  together. Other phases, effect identity/bypass, owner clocks, reset companions
  and unrelated payload remain unchanged; no style defaults or retiming are
  inferred.
- Five whole-document native comparisons and a 96-second save/reopen sequence
  verify Grow, Pulsate, Shrink, None and reset preservation. Repeat exports match
  complete decoded video/audio, with 180 sampled phase frames, 75 paired samples,
  96 visually inspected frames and 120 audio-channel windows. All fifteen raw
  schema/profile/hazard checks pass; the second native save is byte-identical.

## 0.33.0 — 2026-11-06

### Added

- Native-template behavior construction, phase timing/static edits, bypass and
  removal on linked moving recordings inside Groups, including nested Groups.
  Matching wrapper/video mirrors preserve source/timeline reset distinctions,
  recorded audio, child clocks, ancestor geometry and unrelated payload.
- Five whole-document native comparisons and a 72-second save/reopen sequence
  verify the extension. Complete repeat exports match decoded video/audio,
  with 132 measured phase frames, 55 paired samples and 120 audio-channel windows.
  The independent native save is byte-identical.

## 0.32.0 — 2026-11-06

### Added

- Media Matte construction, static edits, intensity intervals, clearing, bypass
  and removal on linked moving recordings inside Groups, including nested
  Groups. Matching wrapper/video mirrors preserve recorded audio, child clocks,
  parent geometry and unrelated animations. Atomic media/Group-track edits keep
  their controls independent.
- Native lifecycle controls and reused native curve templates pass a 144-second
  save/reopen comparison with identical decoded repeat exports, 216 measured
  phase frames, 99 paired comparisons and 240 audio-channel windows. Save
  normalization stabilizes after regenerating constant intensity companions.

## 0.31.0 — 2026-11-06

### Added

- Typed-double effect interval authoring and clearing on linked moving
  recordings inside Groups, including nested Groups. Wrapper/video mirrors keep
  the child's source clock, stable identities, recorded audio and reset data.
  Nonlinear effect easing preserves independent geometry, parent timing and
  existing Group clipping; clearing retains the unrelated movement.
- Reused native template controls, direct native property readback and a
  78-second save/reopen comparison verify the extension. Complete repeat exports
  match decoded video/audio, with 117 inspected phase frames, 45 paired samples
  and 130 audio-channel windows. Native constant-frame reconstruction stabilizes
  on the third save.

## 0.30.0 — 2026-11-06

### Added

- Native-template visual-effect construction, static editing, bypass and removal
  on linked moving recordings inside Groups, including nested Groups. Matching
  wrapper/video mirrors retain complete child-source clocks, stable identities,
  reset metadata and recorded audio; ancestor geometry and timing stay intact.
  Complete timed templates copy without retiming or importing parent state.
- Native lifecycle comparisons, an 84-second independent control with identical
  decoded repeat exports, 126 inspected phase frames and 140 audio-channel
  windows verify the Group extension. Other feature helpers retain their
  separate Group ownership contracts.

## 0.29.0 — 2026-11-06

### Added

- Native-template behavior construction, phase timing/static editing, bypass and
  removal on root linked moving recordings. Matching wrapper/video mirrors
  preserve stable identities, recorded audio, source processing and complete
  trim/speed clocks. First phase-duration edits keep native source durations
  distinct from timeline reset ticks; existing reset companions survive.
- Five native lifecycle comparisons and an eleven-cell, 44-second save/reopen
  control verify construction and editing against native Fade. Repeat exports
  match complete decoded video/audio, with 99 inspected phase frames and measured
  background/recorded-audio tones. Behavior CLI help now emits versioned JSON.

## 0.28.0 — 2026-11-06

### Added

- Typed-double visual-effect interval authoring and clearing on root linked
  moving recordings. Wrapper/video mirrors retain exact trim/speed clocks,
  stable identities, recorded stereo audio, source processing, reset data and
  unrelated geometry. Nonlinear effect easing preserves matching shared visual
  intervals; further linked variants and point forms retain separate contracts.
- Native Spring and independent linear-position controls, a 27-second comparison
  with identical complete decoded repeat exports, measured geometry, phase-frame
  inspection and preserved background/system-audio tones. Effect-curve CLI help
  now emits versioned JSON.

## 0.27.0 — 2026-11-06

### Added

- Native-template visual-effect construction, static editing, bypass and removal
  on root linked moving recordings. Matching wrapper/video mirrors retain stable
  identities, recorded stereo audio, cursor/geometry state, source processing and
  reset metadata. Complete animated templates copy with matching owner clocks;
  behavior and effect-curve authoring keep their separate ownership contracts.
- Five native lifecycle replays and a 42-second save/reopen comparison verify
  static and timed template copies against native controls. Repeat exports match
  complete decoded picture/audio, with inspected phase frames and measured
  background/system-audio tones. Effect CLI help now emits versioned JSON.

## 0.26.0 — 2026-11-06

### Added

- Media Matte construction, static edits, intensity curves, clearing, bypass
  and removal on root linked moving recordings. Native wrapper/video mirrors
  share stable tokens and exact trim/speed clocks; recorded stereo audio,
  source data, cursor settings and unrelated visual state survive. Ambiguous
  clocks or audio bindings refuse; further linked owner forms remain separate.
- Native linked animation and lifecycle controls, a 36-second save/reopen
  comparison with identical complete decoded repeat exports, inspected masks
  and independently measured background/system-audio tones. The matte CLI's
  help now emits structured JSON with its existing owner and schema version.

## 0.25.0 — 2026-11-06

### Added

- A dedicated cursor click helper authors complete explicit left/right lists on
  existing video cursor paths and replaces authored recording click edits.
  Exact trim/speed clocks, linked mirrors, same-time metadata, captured deletion
  entries, cursor geometry, source data and audio survive. Empty lists clear the
  selected authored events; captured TREC clicks retain their separate ownership.
- Twelve complete native replays cover insertion, button replacement, removal,
  clearing and visible trim-start events on trimmed 2× video and recordings.
  Two fresh-process 78-second exports repeat all decoded picture/audio; independent
  controls retain original captured clicks and show authored green/yellow targets.

## 0.24.0 — 2026-11-06

### Added

- Explicit recorded-cursor path creation, replacement and restoration on standalone
  moving recordings. Native source-clock edits preserve captured clicks, cursor
  styling, smoothing, media geometry, sources and independent audio; restoring
  removes only the complete override and returns to the original TREC path.
- Six complete native edit replays cover creation, movement, insertion, deletion,
  one-point hold and restoration on a trimmed 2× recording. Two fresh-process
  42-second exports verify persistence and decoded picture/audio repeatability.
- Cursor helper reports now use schema version 2, retaining the version-one
  fields and adding the physical recording override inventory. Input point
  specifications remain version 1; created-path commands retain their contract.

## 0.23.0 — 2026-11-06

### Added

- A dedicated created-cursor path editor replaces explicit native video point
  lists, preserving linked mirrors, tokens, images, click events, smoothing,
  media transforms, source selection and audio. Point timing uses exact source
  ticks with trim and inverse-speed mapping; Bézier handles remain explicit.
- Native movement, easing/angle, trimmed 2× timing, insertion/deletion, separated
  video and one-point hold controls match complete helper replays. Two independent
  54-second exports repeat complete decoded picture/audio. Recorded overrides
  and other owners retain separate contracts.

## 0.22.0 — 2026-11-06

### Added

- Annotation schema version 3 supports mixed-style substring replacement,
  insertion and deletion with original code-point coordinates, exact expected
  text and explicit style anchors. Independent native property partitions and
  opaque payloads survive UTF-8 offset changes and adjacent-run merging.
- Complete deletion preserves the native null frame. Reinsertion into that
  saved empty frame requires explicit style properties; default font objects
  and cached caret styles are not inferred. Existing versions retain their contracts.
- Native edit replays and two fresh-process exports cover seven helper/native
  pairs, including compound edits, cross-style replacement and empty/reinserted text.

## 0.21.0 — 2026-11-06

### Added

- Annotation styling with schema version 2 over Unicode code-point ranges, compiled
  to native UTF-8 byte boundaries. Independent mixed property partitions retain
  opaque style data, default fonts, other annotation fields, sources and audio.
- Cross-boundary color edits, partial emphasis resets and whole-property edits
  preserve unrelated styles. Version one retains its uniform-text contract;
  changed mixed-style text and animated attribute maps remain refused.
- Native range replays and independent rendered controls cover accented text,
  emphasis, colors, underline boundaries and different sizes across a line break.

## 0.20.0 — 2026-11-06

### Added

- Native-template behavior construction, phase timing/static edits, bypass and
  removal on direct moving recordings, freeze frames and stitched parents.
  Complete native intervals preserve source in-points, held frames, cursor data,
  child clocks and captured reset companions without inferred retiming.
- Native Fade lifecycle comparisons and independent phase/render controls cover
  one- versus three-second entry timing and persistence across the stitched hold.
  Linked recording mirrors retain their separate verification requirement.

## 0.19.0 — 2026-11-06

### Added

- Native-template visual-effect construction, static edits, bypass and removal
  on direct moving recordings, freeze frames and stitched parents. Complete
  payloads and captured reset companions preserve recipient cursors, child
  clocks, source selection and audio; timed templates require matching clocks.
- Native lifecycle and rendering controls include complete frozen-interval
  copying and native interval reconstruction. General Motion Path edits/removal
  now route to its dedicated rotation-preserving helper.

## 0.18.0 — 2026-11-06

### Added

- Animated typed visual-effect parameters on existing moving recordings, freeze
  frames and stitched parents. Native source-position and frozen local clocks
  retain selected frames, cursor data, child timing and virtual holds.
- Exact native curve replays and independent retimed Sepia controls verify
  Spring easing, clearing and geometry preservation across the moving/held join.
  Linked recording mirrors and new constructors keep separate contracts.

## 0.17.0 — 2026-11-06

### Added

- SVG image-reference inspection and explicit PNG embedding into a separate
  candidate. Selected reference value bytes change while surrounding XML,
  namespace prefixes, formatting, numeric text and geometry remain intact.
  Hash-bound image selection, alias/collision protection and dynamic/active
  reference refusals preserve original inputs.
- Native XLink and plain `href` controls compare embedded and linked SVGs with
  a direct PNG before and after actual bundle relocation. Image gating remains
  distinct from fonts, stylesheets, other references and full render closure.

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
