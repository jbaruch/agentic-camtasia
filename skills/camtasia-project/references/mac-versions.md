# Mac build and project-format selection

Match the actual installed editor, the JSON format version, and the document's
authoring client separately. Read the app's Info.plist or About panel; an old
project's authoring metadata does not identify the running application.
Native observations in this plugin currently cover Mac 2025.0.3 (format 9)
and the additional 2026.2.4 observations below. Keep evidence scoped to its build.

Mac 2026.2.2 adds SVG Tiny 1.2 rendering according to the vendor's
[release history](https://support.techsmith.com/hc/en-us/articles/41263167862285-Camtasia-Mac-2026-Version-History).
The [native SVG observations](media.md#svg-inputs) establish direct import,
bundled still-source representation, transparency, scaled/offset viewBox,
independent rerenders, and one Gaussian-blur example in 2026.2.4. Keep those
specific findings separate from broader SVG conformance.

## Native conversion to format 10

Mac 2026.2.4 refused to open the format-9 probe directly and offered **Convert**.
It then requested **Save Converted Project As**, created a separate `.cmproj`,
and reported a successful upgrade. The new JSON used version `10.0`. Its
authoring client initially retained `2025.0.3`; an explicit native save updated
that field to `2026.2.4`. Never simulate conversion by changing those strings.
Keep the old project and inspect native repairs before editing the converted one.
The [standalone bundle check](media.md#standalone-bundle-verification) additionally
verifies a two-source conversion with both earlier locations withheld, a fresh
editor process, and matching decoded rerenders.

The same native Tiling preset that exported black in 2025.0.3 rendered repeated
tiles after conversion in 2026.2.4. Its parameters were the typed doubles
`positionU.x`, `positionU.y`, `positionV.x`, `positionV.y`, with native defaults
400, 0, 0, 400. The native 2026 export initially selected 3840×2160 HEVC while
the project remained 640×360. **Advanced Export Options → Dimensions → Current**
and **Compression type → H.264** produced the intended 640×360 comparison on
the subsequent recording probe. Check output streams rather than assuming
that project dimensions or an earlier build's export settings control the movie.

Do not apply the format-9 compatibility profile to format 10. The schema helper's
`--profile mac-2026.2.4` selects a separate exact-build profile. It currently
adds the demonstrated `Tiling`, `CursorSmoothing`, five gesture identifiers,
and native `WinCompression`/`Pitch` identifiers (see [audio](audio.md)). It also
admits `Vignette` and the spaced native names `CRT Monitor`, `Static Noise`, and `Torn Edge`,
the gesture category, and the boolean `sourceTrack.transcriptionSet` retained
by native recording and generated-transcription saves.
It also adds the standalone `Caption` branch observed in current VTT/SAMI
imports; see [captions](captions.md) for native entity, RTF, and timing results.
An independently saved/reopened native empty project also omits `sourceBin`;
the format-10 profile makes that root key optional. Semantic source-reference
checks still apply when media clips exist.
The profile also admits the natively rendered `TypeWinSVG` Sketch Motion Callout
and its single `DrawPercentageFade` drawing modifier. All twenty presets have
independent native rerenders over video and neutral gray, with inspected drawing
and Fade phases; see [Sketch Motion](advanced-features.md#sketch-motion-annotations).
All 41 native text-callout presets also have inspected independent rerenders.
The profile adds their five missing speech/thought-bubble and text-arrow shape
identifiers; see [text callouts](advanced-features.md#text-callout-presets).
All 32 current shape presets also have inspected independent native rerenders.
The profile adds `shape-star` and `shape-octagon`; see
[shape presets](advanced-features.md#shape-presets) for native fill opacity,
style-dependent geometry, and the misleading Abstract triangle filename.
Seven Blur/Highlight and six standalone keystroke presets have inspected native
rerenders and a matched source-only control. The profile adds the demonstrated
`TypeWinHighlighter`, `TypeWinSpotlight`, `TypeWinPixelate` and `MacKey` names;
see [processing annotations](advanced-features.md#blur-pixelation-and-highlight)
and [standalone keystrokes](advanced-features.md#standalone-keystroke-callouts).
Default/custom theme application, missing-theme-ID persistence, Arial font
replacement and fresh-process `.camtheme` import/export also have independent
native rerenders under this existing profile; see [themes](advanced-features.md#themes).
All 32 factory LUT filters also have inspected independent native sequence pairs
under this existing profile. Native `LutEffect` mirrors, filename dependencies,
static descriptor resaving and the measured control-audio difference are in
[color LUT filters](advanced-features.md#color-lut-filters).
Fresh native recordings also save `timeline.metadata` with source capture
dimensions such as `RecordingWidth: "3024"` and `RecordingHeight: "1898"`.
These are strings and remain separate from the resized project's numeric
`width`/`height`. The format-10 profile admits the native metadata object without
relaxing unrelated timeline fields.
These three visual presets use typed animated double parameters and native
`uiHints`; Torn Edge also uses bare booleans for its four edge switches.
Their eight-second native movies show scanlines/warping, visible grain, and
a transparent rough border respectively. Each saved project independently
reopened with its effect controls retained, and the three movies' decoded
audio hashes match. Preserve `metadata.effectIndex` and native wrapper/child
mirrors. The project effect name is distinct from the `.tsceffect` filename;
for example, `CRT Monitor` retains its space.

Native **Modify → Add Effects → Visual Effects → Vignette** is available even
when absent from the palette scan. The default saves bare numeric parameters
`Amount: -100.0`, `Size: 50.0`, `Roundness: 0.0`, and `Feather: 100.0` in
`categoryVisualEffects`, with wrapper/child mirrors and `effectIndex: "0"`.
Its native movie darkens the image perimeter while retaining the bright center.
Independent reopen retains all four controls; a fresh render reproduces the
decoded video and audio. Do not wrap these bare fields in animated doubles
merely because neighboring visual presets use that representation.

Native trimmed/styled media-property saves additionally retain `Colorize` on
wrapper/video mirrors, Callout and image owners. The format-10 profile adds this
exact effect identifier; the pinned upstream enum omits it. A 72-second native
pair and direct color controls verify output. See
[styled replacements](media-quick-properties.md#trimmed-and-styled-replacement).

The [short/portrait/wide replacement](media-quick-properties.md#short-and-differently-sized-av)
probe needs no profile correction. Its portrait source has a 96000 track clock
and 32000 Hz audio; preserve those distinct native rates. Aspect fit, short-source
clamping and remembered-duration restoration have native render evidence.

It does not inherit all format-9 corrections. Preserve unknown fields and
investigate actual schema errors with a same-build native specimen.

The matching profile also admits the native recorded-cursor identifiers absent
from the upstream enum; parameter and independent rerender contracts are in
[cursors](cursors.md). Upstream identifiers such as `CursorPhysics` remain
distinct from their UI labels.

## Recorded-cursor smoothing

The 2026.2.4 probe uses an actual `ScreenVMFile` and the original TREC's recorded
pointer data, rather than a generated path. Native **Cursor Smoothing** saves
`CursorSmoothing` in `categoryCursorEffects`. The preset supplied integer
`moveTime: 705600000`, `delayTime: 176400000`, and `lingerDuration: 564480000`,
plus typed double parameters `easeType`, `enableLingers`, and `lingerBounds`.
The property panel displayed one-second movement, 0.25-second delay, easing,
and pause detection. These times use the project's 705600000-tick clock.

A matched bypass comparison at 500% cursor scale exposes visibly different
cursor locations and pauses at 4.5, 5.5, 6.5, and 7.5 seconds. Both movies are
eight seconds, 640×360 H.264. The independently reopened smoothed project
retained 500% scale, one-second movement, 0.25-second delay, easing, and pause
detection. Preserve the effect's scalar tick values separately from its typed
animated controls. The result establishes actual recorded-cursor processing;
it does not establish every click sound, keyboard overlay, or cursor preset.

## Recorded keyboard and windows

Recorded Keystroke and Window Spotlight use the separate
`categoryScreenRecordingEffects`. Their native names, tick/position controls,
recording dependencies, and independent rerenders are documented in
[recorded cursors and events](cursors.md#recorded-keystrokes-and-active-windows).
The format-10 profile admits their observed identifiers for this exact build.

The same profile adds 23 native left/right click identifiers missing from the
pinned upstream enum. `LeftClickScaling` and `categoryClickEffects` already
exist upstream. All 24 presets have positive native output and independent
reload/rerender evidence. The native generated-path specimens also establish
`CursorPath` for this build. Recorded overrides and generated-path keyframes use
different click representations; read [click editing](cursors.md#inserting-and-removing-clicks).

## Current native behaviors

All thirteen palette behaviors have native application/save, inspected phase
frames, and independent saved-project batch rerenders. The matching profile
adds six behavior names and ten phase-specific identifiers missing upstream.
Read [behavior phases](behaviors.md) for the complete entry/center/exit map,
mixed tick/second/rational controls, wrapper/video mirrors, and measured audio
comparison limits. The earlier seven-preset Mac 2025 result remains scoped to
that build; do not infer newer preset availability from its enum.

## Current native animations and geometry

Twenty-five saved animation/geometry specimens independently reload and render
decoded-identical output. They cover all twelve native presets, five easing
choices, Auto Animate, crop/corner pin, and short/retimed boundaries. The
format-10 profile adds native `MediaPath`; its typed point/Bézier curves remain
distinct from ordinary visual animation intervals. Read
[native animations](animations.md) for ownership, source-position tick clocks,
SmartFocus dependencies, negative keyframe starts, and coupled geometry.

## Current native transitions

The [native transition contract](transitions.md) adds 24 rendered presets plus
a clean control, with 25 independent editor reopen/rerender comparisons. The
matching format-10 profile adds 23 missing transition identifiers while keeping
other name/type/property constraints and exact-build scoping.

## Native gesture effects

All five current gesture presets were applied to the same generated eight-second
AV clip, independently saved/reopened, and inspected across native exported
frames. Their decoded audio hashes match; the added gestures change the picture.
Native identifiers and the omitted `categoryGestureEffects` enum value are
admitted only in the demonstrated format-10 profile.

| UI preset | `effectName` | Inspected behavior |
| --- | --- | --- |
| Tap | `tapGestureEffect` | Central indicator changes appearance on press/release, then disappears. |
| Double Tap | `doubleTapGestureEffect` | Two presses with an additional `gesture_midDuration` phase. |
| Tap and Hold | `tapAndHoldGestureEffect` | Press/hold/release; the pressed indicator remains visible at 2.5 seconds and is gone at 3.8 seconds. |
| Pinch | `pinchGestureEffect` | Two indicators converge; native `secondXPosition`/`secondYPosition` defaults are 250/100. |
| Swipe | `swipeGestureEffect` | Indicator moves from the center to the right; the second-position defaults are 250/0. |

The initial preset uses typed double parameters for mask position, phase
durations, color, and radius, with scalar `invertEffect`. The observed radius
is 44 and alpha 0.8. Keep native left/right edge modifiers and their metadata.
The inner `gesture_*Duration.defaultValue` numbers are **seconds** (for example
0.5), while effect `start`/`duration` and edge-modifier durations are **project
ticks**. The Tap specimen has outer duration 852364800 and fade durations
141120000; these are distinct from the inner phase controls. Native bounds can
be subframe. Preserve them rather than deriving an outer length by summing
inner defaults or multiplying every field whose name contains “Duration.”

## Version-dependent feature discovery

TechSmith's [Mac 2025 history](https://support.techsmith.com/hc/en-us/articles/37778934597005-Camtasia-Mac-2025-Version-History)
and [Mac 2026 history](https://support.techsmith.com/hc/en-us/articles/41263167862285-Camtasia-Mac-2026-Version-History)
identify when later feature families appear. Use them to select an editor for
the requested operation; release notes do not specify serialized JSON.

| Minimum release | Features to investigate in that build |
| --- | --- |
| 2025.1 | CRT Monitor, Static Noise, Torn Edge; cursor isolation and additional shader-based cursor/click presets. |
| 2025.2 | Single-window recording and Rev media workflows; later fixes add WebM input support. |
| 2026.0 | Editable Rev components, Rev dynamic captions and SmartFocus, Audiate text editing workflows. |
| 2026.1 | Audio-based media alignment, VTT caption import/export, vertical Rev layouts; later behavior word-order controls. |
| 2026.2 | WebM export including transparency, curved Remix arrows, customizable Lottie assets, and Snagit Step Capture workflows. |

The current native 2026 palette visibly includes CRT Monitor and Cursor
Isolation. Presence of a bundled `.tsceffect`, model, or asset file alone does
not establish that the older editor exposes or renders it. Discover the feature
in the target UI, capture its actual saved representation, and exercise its
output. Cloud and companion-app features also need the named service/app;
do not infer an offline JSON equivalent from a release-note description.
