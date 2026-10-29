# Native feature map

Read only the requested feature's row and linked evidence. This expands beyond
`port-demo`; a feature listed here is not a promise that the helper constructs
or validates it. Serialized details are observations, not official guarantees.
See [native verification](native-verification.md) for the exercised target,
schema corrections, supported behavior set, and rejected payloads.
See [additional native contracts](advanced-features.md) for the exercised
placeholder replacement, redaction, keying, background removal, cursor paths,
hotspots, quizzes, SCORM 1.2 calls, and device-frame dependencies.
That reference also records native region blur/freeze, masking, tint, mosaic,
motion paths, outlines, reflection, and sepia, including their UI/JSON name
differences and the failed Tiling default.

| Feature | Serialized evidence / dependencies | Verification |
| --- | --- | --- |
| Video, audio, stills | Source entry and selected source stream; see [format map](project-format.md). | Open each new asset; check finite source ranges separately from still holds. |
| Screen recordings and cursor | Screen clip/source parameters and recording metadata; see [media](media.md). | Twelve recorded-cursor presets, all 24 left/right click presets, recorded Keystroke styles and Window Spotlight have independent native rerenders in [cursors](cursors.md). That reference also covers recorded and generated click insertion/removal, their distinct owners/clocks, and the initial generated-keyframe limitation. Smoothing has a matched bypass comparison in [Mac versions](mac-versions.md). |
| Linked AV | `UnifiedMedia.video` and `.audio` have separate timing and processing. | Split/trim a probe; verify both children and wrapper stay aligned. |
| Groups | Child `tracks`, wrapper transforms, audio controls, and version-specific metadata. | Nested playback, mute/solo, bounds, and save/reopen without repairs. |
| Group color Quick Properties | Ordered `attributes.assetProperties`, child media/property bindings, optional fill mappings and group theme ID; [native editing contract](quick-properties.md). | Fifteen cases verify rename, all five theme slots, linked edits, unlink, remove/re-add, reorder and direct color editing, with an independent two-minute native pair and 45 inspected frames. |
| Group text / typography Quick Properties | Native type-0 Text and type-1 Callout entries use integer child IDs; rich UTF-8 byte ranges, default fonts and child opacity have distinct owners; [text contract](quick-properties.md#text-group-constructor). | Twenty-three native captures, a 184-second independent export pair and 46 inspected frames verify Unicode editing, font/style/size, six alignments, color, opacity, stroke, spacing and multiline fitting. Font-theme/linking cases are below; media replacement and physical font-file closure remain separate. |
| Font themes / linked text Quick Properties | Separate `font-family` and `font-color` mappings, five-property rich runs, linked integer child lists and unmapped re-addition; [native lifecycle](quick-properties.md#two-text-constructor-and-font-themes). | Another 23 native captures, 184-second independent pair and 46 inspected frames verify both font resources, five color slots, linking, shared edits, unlink, remove/re-add, independent changes and the second Callout appearance. Linking uses first text/label but second font mapping. User themes are preserved through recoverable synthetic-resource cleanup. |
| Media Quick Properties | Native type-2 properties bind the linked AV wrapper or image child; replacement metadata, transparent Callout clearing, remove/re-add and applied `logo-1` mapping have distinct owners; [media contract](media-quick-properties.md). | Three initial constructors/seven AV lifecycle captures have a 56-second native pair, 14 inspected frames and 28 audio windows. Nine applied Logo/image states add a 72-second pair and matching fresh-process closure render. Fifteen two-AV link/unlink/independent-edit states add a two-minute pair, 30 inspected frames and 60 audio windows. Fifteen mixed image/AV states add another two-minute pair, 30 inspected frames and 60 audio windows, including mapping loss on unmapped-second relink. Ten trimmed/styled states and eight direct controls add a 72-second pair, 36 inspected frames and 72 audio windows. Replacement resets source trim; clear/restore resets audio gain while retaining Colorize/opacity. Ten short/portrait/wide states and three direct controls add a 52-second pair, 52 inspected frames and 104 audio windows, verifying aspect fit, short-source clamping/late silence, remembered-duration restoration and bundled-source closure. |
| Stitched segments / freezes | `StitchedMedia.medias`, internal trims and offsets; still variants may consume one source tick. | Every join and freeze; do not reject negative internal starts automatically. |
| Placeholders / templates | Native `PlaceholderMedia` and replacement `UnifiedMedia`; [observed replacement](advanced-features.md#placeholder-replacement). | Replace a placeholder in the target editor; preserve intended duration and inherited styling. |
| Transitions | Track-level `transitions` link clip IDs; one-sided transitions omit the unused endpoint. See [native transitions](transitions.md). | All 179 native presets have inspected output and independent rerenders. Separate Fade fixtures verify short clips, source skips, gaps, a retimed boundary, and independent preroll flags. Verify requested audio and handle behavior. |
| Zoom, pan, rotation, opacity | Parameter curves and visual intervals; see [native animations](animations.md). | All twelve presets, five easing choices, Auto Animate, crop, corner pin, SmartFocus, short clips, and source-position retiming have saved native output and independent rerenders. Nested transforms still need parent geometry. |
| Annotations, titles, arrows | `Callout.def`, shape/text/font properties, rich-text ranges, effects; [41 native text presets](advanced-features.md#text-callout-presets), [28 native arrow/line presets](advanced-features.md#arrow-and-line-presets). | Font availability, Unicode text ranges, line breaks, text bounds, safe margins; retain typed arrow endpoints and inspect contrast. Saved font names do not resolve physical font files. |
| Shape presets | Native `remix` definitions, shape/style, geometry, fill/stroke channels and opacity; [32 verified presets](advanced-features.md#shape-presets). | Preserve transparent-center outlines and style-dependent geometry; resource filenames may misidentify shapes. |
| Blur, pixelate, highlight, spotlight | All seven native presets, `Callout.def.kind` and inversion/color/strength fields; [native contracts](advanced-features.md#blur-pixelation-and-highlight). | Independent rerenders and a source-only control; verify the requested region and obscuration strength. |
| Standalone keystroke callouts | Six native `MacKey` presets, literal keys and style/background fields; [native contracts](advanced-features.md#standalone-keystroke-callouts). | Preserve glyphs and native geometry; distinguish annotations from recorded keyboard events. |
| Themes | Native Default/custom application, font replacement, missing-ID parity, fresh-process `.camtheme` export/import with logo closure, and [rename/delete](advanced-features.md#theme-rename-and-delete). | Rename retains UUID/resources; confirmed Delete removes the exercised definition/logo. Both write before Manager Save and persist through Manager Cancel. Four native exports match complete decoded streams across renamed/deleted states, retaining existing project payload/styling. Keep external dependencies and preexisting user bytes; font names do not bundle fonts. Successful duplication/shared-resource deletion retain separate cases. |
| SVG sources / internal resources | Native `IMFile` stills retain source clock 600/range `[0,1]` and separate project holds; [native SVG/dependency cases](media.md#svg-inputs). | Nine image/font/path controls have four native pairs across present/withheld/restored/moved environments. Embedded PNG and outlines survive; absolute links depend on the original location. The tested relative PNG and four text/font variants are absent. Source-only manifest success does not establish internal dependency or rendering closure. |
| Sketch Motion | Native `Callout.def.kind: TypeWinSVG`, embedded SVG, clip-local draw modifier, and separate ending Fade; [twenty native presets](advanced-features.md#sketch-motion-annotations). | Inspect drawing/full/fade phases and contrast; retain native geometry, scale, and transition ID references. |
| Behaviors | `GenericBehaviorEffect` carries phase data; [native behavior contracts](behaviors.md). | All thirteen current presets have native phase-frame and independent rerender evidence. Preserve phase names, mixed clocks, rational values, and wrapper/video mirrors; verify text layout and requested retiming separately. |
| Visual effects | Clip `effects`, optional source effects, effect-specific parameters and metadata. | Preserve category identifiers and order; check platform support. |
| Color LUT filters | Native `LutEffect` AV mirrors, all 32 factory filters, custom CUBE import, intensity/easing/bypass, thirteen range choices and missing-resource fallback have native pairs; [filter contract](advanced-features.md#color-lut-filters). | Hash CUBE dependencies outside `sourceBin`; preserve unknown parameters/reset metadata and report measured control-audio differences. |
| Lottie animations | Native JSON import, source tracks, separate frame/millisecond/project clocks, per-clip `sourceEffect` colors and automatic group color bindings; [native Lottie contract](lottie.md). | Three initial pairs verify shape motion, transparency, clip end, shared-source colors/local restart and grouped-output parity. Twelve image/font/glyph controls add four native pairs over present/withheld/restored/actually moved resources. Embedded PNG and glyph outlines survive; absolute image links depend on the old path, tested relative/file-URI images are absent, and font references show matching fallback text. Source-only manifests do not establish internal closure. |
| Current CRT, noise, and torn edges | Spaced native names and typed controls; [current Mac contracts](mac-versions.md#native-conversion-to-format-10). | All three save/reopen and render visibly; preserve native `uiHints`, edge booleans, and wrapper/child mirrors. |
| Gesture effects | Native `categoryGestureEffects`, typed phase/position/color parameters, outer tick bounds and fades; [current Mac contracts](mac-versions.md#native-gesture-effects). | Tap, Double Tap, Tap and Hold, Pinch, and Swipe have native save/reopen and sampled animation exports. Preserve inner seconds separately from outer ticks. |
| Track mattes and masks | [JSON matte editing](helper.md#matte-json-editing), root/Group track attributes and Callout/video/linked AV/image/Group effects; [native modes and controls](advanced-features.md#media-and-track-mattes). | Four native sequence pairs verify modes, intensity, easing, bypass, removal, linked mirrors/stable tokens, linear intensity curves and explicit clearing. Retimed keyframes use source positions; edge easing uses timeline seconds. Five retained depth values have equivalent immediate-layer scope in the tested stack. Nonlinear/point curves, recording owners and interacting mattes retain separate cases. |
| Green screen / background removal | Native `ChromaKey` and `BackgroundRemoval`; [parameters and inspected outputs](advanced-features.md#chroma-key). | Target editor acceptance, edge quality, GPU/runtime availability, export parity. |
| Color adjustment / HDR | Effects plus media color metadata; these are separate mechanisms. | Compare native rendering and output tags; see [media](media.md). |
| Narration and music | `AMFile`, gain/volume automation, source processing, project normalization; [native audio contracts](audio.md). | Measured native AI cleanup survives reopening with identical output; native pitch changes frequency without changing length. Check doubling, clipping, fades, channel routing, and preserved cleanup. |
| Dynamic captions | Source transcription plus modifier-bearing `Callout`; [native generation/edit/style contracts](captions.md#native-generation-source-edits-and-styling). | Native block/word-highlight exports, source edits with unchanged word times, independent reopen, and identical word-highlight rerender. Identify parameter clocks separately from audio sample rates. |
| Standard/closed captions | Native Add Caption uses `AMFile.parameters.captions`; SRT import creates a standalone `Caption` clip with `parameters.captionData`. Global settings use `timeline.captionAttributes`; see [captions](captions.md). | Both forms saved, reopened, and rendered expected texts. Native SRT export confirms retiming; a web export exposes working CC toggling and both cue texts. |
| Markers / chapter navigation | Timeline or media `parameters.toc.keyframes` in community implementation. | Timeline markers stay on the timeline; media markers follow their clip. Check retiming. |
| Hotspots | Native `video.attributes.hotspot`; [six-second Smart Player seek](advanced-features.md#interactive-hotspots). | Probe URL, time, marker, pause/continue in the intended Smart Player output. |
| Quizzes / SCORM | [Direct timeline/media quiz editing and pin/unpin](helper.md#quiz-json-editing), all four question kinds, feedback/actions, [all four survey kinds with optional grading inputs](advanced-features.md#survey-grading-inputs), eight owner/global clocks, SCORM 1.2, SCORM 2004 export/runtime pairs and [fourth-edition session resume](advanced-features.md#suspending-and-resuming-a-quiz-session). | Test unobserved destination/container clocks, other-edition resume, restart/failure paths and target LMS policy. Do not assume a plain MP4 preserves interactions. |
| Library assets / `.libzip` archives | Native `.assetproj`, actual companions, copied sources, archive headers, insertion ID/Quick Property remapping; [Library contract](library.md). | Native controls cover AV/text reuse and ungroup's grouped-audio endpoint remedy; canvas/visible sizes; blank, Default, vendor and mixed Libraries; asset/folder/Library naming; copy/move and populated folders; preview, search, Name/date/type sorting and reversal; direct PNG/WAV/MP4 clocks and insertion; whole-Library archives and reuse with donor Libraries absent. Occupied-name refusals and allowed equal folder/asset labels have distinct contracts. Fifteen archive-import states expose merged projects, both-project exports, incorrect Last Used metadata and row coalescence after restart. Unique native intake avoids that demonstrated merge; eight native AV/text pairs match independent controls installed and with donor Libraries absent. Within-Library populated-folder nesting and child/sibling asset drags retain bytes/identities through restart and two further native reuse pairs. An unexpected descendant-drop Delete prompt is cancelled; safe descendant rejection and root/ancestor return remain separate. Shared-resource hard links, actual companions, bundled-source handles and source-free raw-schema discrepancies remain explicit. Permanent Library deletion, other resources and physical font closure remain separate. |
| Device frames / installation assets | Asset IDs and installed resources; [native DeviceFrameEffect dependency](advanced-features.md#device-frames-and-installation-assets) and [installed preset discovery](advanced-features.md#installed-preset-discovery). | Copy the demonstrated dependency closure; verify target installation can load it. |
| Rev / Audiate / companion imports | Additional metadata, source processing, or proprietary runtime state; [handoff/dependency contracts](advanced-features.md#companion-apps-and-connected-imports). | Verify actual app/service handoff, selected sync scope, source closure, and independent native rendering before synthesizing JSON. |

## Transitions

The upstream transition implementation stores `name`, `duration`, `attributes`,
and one or both of `leftMedia`/`rightMedia`. Endpoints refer to clips in that
track, not source-bin IDs. A one-sided transition can introduce or end a clip;
an absent side can be omitted. Preserve the editor's representation of nulls.
Cloning or deleting clips requires endpoint remapping.

The project validator checks endpoint references and positive duration. The
[transition editor](helper.md#transition-json-editing) stages Fade construction,
duration/control changes and removal using root clip endpoints. It does not prove
available media handles, adjacency, rendering, or a transition's allowed name.
Use a same-version native sample rather than inventing attributes.
The [current native contract](transitions.md) records saved identifiers,
boundary duration, bare controls, color precision, and installed metadata syntax.
[Implementation evidence](https://github.com/grandmasteri/pycamtasia/blob/443a41e37cddb460c0aa6e046c951cb17f241bf3/src/camtasia/timeline/transitions.py).

## Markers on linked media

The Mac 2025.0.3 native save/reopen probe retained timeline markers at
`timeline.parameters.toc`. It normalized a marker placed on the `UnifiedMedia`
wrapper into `UnifiedMedia.video.parameters.toc`. Use that native child location
for this build. The community schema rejects wrapper-level `parameters`; no
compatibility correction is needed after native normalization. Retiming and
chapter-player behavior still require their own output checks.

## Effects and behaviors

Effects can have defaults, animated values, edge modifiers, opaque state, and
version-specific category strings. A UI name is not an effect identifier.
Behaviors use a different phase structure from ordinary visual effects. The
native verification reference records a schema-conforming parser crash and
identifiers the editor saves but rejects for rendering.
The longer probes also exposed clip/effect duration mismatches and incorrect
Reveal phases. Obtain a same-build native preset and keep its clip-local timing
consistent when trimming or extending a clip; the corrected seven-behavior
comparison has visible native output, rather than renderer acceptance alone.
The current build's complete thirteen-preset phase map and independent
rerenders are in [behaviors](behaviors.md), including the measured audio
comparison limit. Keep those newer identifiers scoped to their actual build.
The local demo verifies `RoundCorners` followed by an alpha-aware `Border` on
a square presenter source, and `VSTEffect-DFN3NoiseRemoval` on narration; it
does not establish defaults for every effect.

For exact identifiers and parameter spelling, inspect the relevant upstream
[visual](https://github.com/grandmasteri/pycamtasia/blob/443a41e37cddb460c0aa6e046c951cb17f241bf3/src/camtasia/effects/visual.py),
[audio](https://github.com/grandmasteri/pycamtasia/blob/443a41e37cddb460c0aa6e046c951cb17f241bf3/src/camtasia/effects/audio.py),
[cursor](https://github.com/grandmasteri/pycamtasia/blob/443a41e37cddb460c0aa6e046c951cb17f241bf3/src/camtasia/effects/cursor.py),
or [behavior](https://github.com/grandmasteri/pycamtasia/blob/443a41e37cddb460c0aa6e046c951cb17f241bf3/src/camtasia/effects/behaviors.py)
implementation, then confirm with native saves. No external library code or
proprietary asset definition is vendored by this plugin.

For filled shapes, the installed Mac 2025.0.3 ellipse preset at
`Camtasia.app/Contents/Resources/AnnotationsBin/Shape/31-basic-ellipse.json`
uses `fill-color` and `fill-style`. Replacing a text callout's `shape` identifier
alone did not create useful alpha content in the matte probe. Preserve a native
shape's fill/stroke contract when constructing a matte.

## Interaction caveat

TechSmith's Results Service and online quiz editor have retired. Quizzes can
still be included in projects and appropriate output, and SCORM can target an
LMS; do not promise the former hosted scoring/reporting service.
[Current TechSmith notice](https://support.techsmith.com/hc/en-us/articles/14539861012237-Changes-to-Quizzing-in-TechSmith-Apps).
