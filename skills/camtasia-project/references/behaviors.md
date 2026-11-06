# Native behavior phases

These contracts cover Camtasia Mac 2026.2.4, format 10.0. All thirteen palette
presets below were applied natively to the same eight-second linked AV clip,
saved, rendered, and independently loaded/rerendered through native Batch Export.
All fourteen outputs, including the clean control, reproduce their own first
exports in decoded video and audio. Entry, middle, and exit frames show the
actual transformations. These whole-media specimens do not establish every
per-character text option; verify glyph layout separately for a text task.


The [behavior helper](helper.md#behavior-json-editing) now copies a selected
same-build saved instance and stages phase timing/static controls, bypass and
removal. It retains complete phase payloads and existing reset data. It requires
matching owner kinds, linked layout and complete clocks for construction; it
infers no outer interval retiming. Selected phase copying has the separate
contract below. Native references
below describe observations, while the helper module owns its accepted input
and refusal contract.

Direct moving/frozen recordings and stitched parents have separate
[native interval and lifecycle controls](behavior-recordings.md), including
source in-points, held frames and independent rendered phase comparisons.

## Identifiers and phase ownership

Behaviors use `_type: "GenericBehaviorEffect"`, separately from ordinary visual
effects. The outer `effectName` and each phase's `attributes.name` are distinct
identifiers. Preserve the complete `in`, `center`, and `out` payloads.

| Native preset | `effectName` | Entry name | Center name | Exit name |
| --- | --- | --- | --- | --- |
| Drifting | `drifting` | `drifting` | `drifting` | `drifting` |
| Explode | `explode` | `implode` | `none` | `explode` |
| Fade | `fade` | `fadeIn` | `none` | `fadeOut` |
| Fly In | `flyIn` | `flyIn` | `none` | `flyOut` |
| Jump & Fall | `jumpAndFall` | `bounceIn` | `jump` | `drop` |
| Pop Up | `popUp` | `hinge` | `popUp` | `hinge` |
| Pulsating | `pulsating` | `grow` | `pulsate` | `shrink` |
| Reveal | `reveal` | `reveal` | `reveal` | `reveal` |
| Scale | `scale` | `grow` | `none` | `shrink` |
| Shifting | `shifting` | `shifting` | `shifting` | `shifting` |
| Sliding | `sliding` | `sliding` | `fading` | `sliding` |
| Tremble | `tremble` | `none` | `tremble` | `none` |
| Wiggle | `wiggle` | `none` | `wiggle` | `none` |

The exact-build profile adds six outer names and ten phase-specific enum
entries absent from the pinned upstream schema. A valid phase name is not
automatically a valid outer behavior name. For example, `flyOut` is the native
exit phase of Fly In; the separate outer `flyOut` helper payload was rejected
in the earlier Mac 2025 test. See [native verification](native-verification.md).

On the exercised `UnifiedMedia`, the editor mirrors the behavior in the wrapper
and its video child, preserving `metadata.effectIndex: "0"`. The wrapper also
updates its applied-effect metadata. Keep these native owners aligned and leave
the audio child unchanged. Do not move behavior attributes into ordinary visual
parameters or remove a phase just because its name is `none`.

## Timing, values, and parameters

The demonstrated outer `start` is zero and `duration` is `5644800000`, matching
the eight-second clip on its 705600000-tick clock. Native entry/exit
`suggestedDurationPerCharacter`, `offsetBetweenCharacters`, and center
`delayBetweenLoops` use ticks. Center `secondsPerLoop` uses seconds, including
rational strings. For example, Jump & Fall saves loop seconds `1` and delay
`1176000000` ticks in the same center attributes object.

Preserve rational strings such as `overlapProportion: "-1/5"`, `"23/60"`, or
`secondsPerLoop: "4/5"`. Overlap is dimensionless; it is not another duration.
Native zero-duration `none` phases, `movement: -1`, and `numberOfLoops: -1` are
not evidence of malformed negative timing. Do not normalize enum-like fields
such as `characterOrder`, `type`, or `movement` from their names alone.

Wiggle's native center saves `secondsPerLoop: 100000` while its visible motion
is also controlled by typed `frequency`, `nuance`, `offsetX`, `offsetY`,
`rotation`, and `scale` parameters. Do not replace that observed value with a
guessed duration. Tremble uses typed `horizontal`, `rotation`, and `vertical`
parameters. Jump & Fall has a typed `jump` center parameter; Drifting has typed
center `movement` and entry/exit `direction` parameters. Preserve their
`valueBounds`, `uiHints`, types, and keyframes independently from phase
attributes with similar names.

When trimming or retiming, inspect the native effect's interval and all phase
clocks. Preserve text ranges and check multi-character ordering for callouts;
the whole-video result does not validate per-glyph spacing. Check entry,
middle-loop movement, and exit separately. A middle frame can legitimately
match control for presets whose center phase is `none`.

## Audio comparison limits

Each saved project's independent native rerender reproduces its own video and
audio streams exactly. All thirteen behavior specimens also share the same
decoded AAC audio, but that audio differs slightly from the clean control.
The measured comparison has zero sample lag and fitted gain approximately one.
Matching native stereo 44100 Hz, 16-bit Wave exports of control and Drifting
differ by one least-significant bit in 191 of 352800 sample frames; their saved
audio-child objects are identical. Do not claim bit-identical audio against a
no-behavior control or infer an audible audio effect from a hash mismatch alone.
Keep native rerender persistence, signal measurements, and perceptual checks
separate. See [audio](audio.md) for requested mix and delivery verification.

## Phase editing and reset companions

A current eight-second linked AV Fade probe saves entry/exit phase names
`fadeIn`/`fadeOut`, outer start zero and whole-clip project-tick duration. Native
entry Speed 50% saves `suggestedDurationPerCharacter: 2116800000` at edit rate
705600000, representing three seconds per character. Both effect mirrors
change together. The wrapper gains `metadata.default-Speed-fade: "705600000"`,
retaining the prior duration as its reset value; no matching video-owner field
is added. Other phase attributes and the complete audio child stay unchanged.
This single observation does not define a general speed-percentage formula.

The helper's template construction and explicit three-second entry edit produce
the same complete native clip owner, including reset metadata. Native bypass
roundtrip, save/close/reopen and export preserve that payload; the saved document
changes only its command counter. Its export and the separate UI-created timing
control match complete decoded video/audio. Raw and exact-build schema checks
pass without an overlay extension.

The active-center Jump & Fall constructor retains default-less typed integer
`direction` point frames in entry/exit. These are distinct from the redundant
static-double point shape that crashed the 2025 parser; preserve valid integer
points when editing another control. The center `jump` parameter is a typed
double with default 60 and bounds 0–500. Editing it to 120 retains those bounds,
reset value and UI hints. The helper's `secondsPerLoop: "3/2"`, quarter-second
delay and two-loop request appear natively as Loop time 1.50s, Delay 0.25s,
Loops 2 and Loop Forever off. Delay remains ticks in JSON while loop time remains
rational seconds. Do not convert all numerics in an attributes object as time.

A three-slot native sequence contains the center edit, a bypassed copy and a
copy with the behavior removed. Its independent 24-second exports repeat
complete decoded video/audio. Fifteen inspected frames show entry, center
movement, exit, bypass and removal beside matching source phases. The Fade
pair adds five inspected intro/hold/outro frames. Strict lifecycle payload
comparison allows only the observed copied-clip ID remap, duration label and
command-counter changes; the remaining behavior, audio and source data match.
All bundled source bytes remain identical. The existing exact-build profile
accepts the saved sequence; its eight raw-schema errors are the previously
recorded missing outer/phase names, not a new schema relaxation.

## Copying native phase styles

Use the [behavior helper](helper.md#behavior-json-editing) `copy-phase` operation
to replace one complete saved `in`, `center` or `out` phase. The template and
destination require the same outer behavior name, owner kinds, linked layout,
project rate, complete owner clocks and behavior outer interval. Existing owner
and mirror restrictions remain in force. No style-name constructor, timing
conversion or external-resource import is inferred. The source phase replaces
its selected counterpart, including timing, typed parameters, point frames and
opaque phase data. Other phases, effect identity/token, bypass, owner state,
reset companions, sources and audio remain unchanged.

To give an existing Fade a Grow entry, first save a native Fade with Grow
selected in its In tab. Select that saved Fade as the phase donor. The outer
name remains `fade`; `grow` is its entry style, not a replacement outer name.
Similarly, native During maps to `center`. A None template clears an active
phase without deleting the behavior. This copies the template's complete phase
settings; it does not combine donor style with the destination's old timing.

### Native changes and reset preservation

Camtasia Mac 2026.2.4 (2026.132), format 10, changes only the selected phase
payload when Fade's In style becomes Grow, During becomes Pulsate, or Out becomes
Shrink. Native Grow retains its Spring movement code, duration/offset hints and
rational overlap. Pulsate introduces a default-less typed integer `movement`
point at zero plus a bounded typed `scale` default of 1.08. Preserve that valid
integer point; the separately reproduced hazardous redundant static-double
point remains refused. Clearing Pulsate to None removes its active parameter
map and restores the complete native inactive phase.

A further native control first edits Fade entry Speed to 50%, creating
`default-Speed-fade: "705600000"`, then selects Grow. The reset companion
survives unchanged while the phase receives Grow's native defaults. Phase copying
retains the destination's reset history and imports no donor reset metadata.
Five whole-document helper/native comparisons match outside thumbnail and
command-count UI metadata. Targeted deterministic tests retain linked mirrors,
Group ancestors, direct recording clocks, independent tokens and atomic refusal.
These inherited owner contracts do not imply new per-glyph or resource closure.

### Rendered and persistence controls

A twelve-cell, 96-second sequence pairs the five native/helper states and adds
bare-media and dim-background-only controls. Two exports separated by saved
close/reopen match complete decoded RGB and PCM: 2880 frames, 640×360 H.264 at
30 fps and stereo 44.1 kHz AAC, using the same editor process. The analysis
samples 180 phase frames; two contact sheets contain 96 visually inspected
frames. Seventy-five matched-time pairs differ by at most 0.942 mean RGB byte
levels per channel. Grow entry, Pulsate motion, Shrink exit and cleared None
remain visibly distinct.

Grow-only widths at five middle samples are 355, 387, 391, 384 and 384 pixels;
Pulsate changes them to 359, 384, 380, 388 and 400. Clearing restores the matching
Grow-only progression, including its settling motion. Shrink's four late samples measure 355, 423, 279 and 114
pixels. These are observations of this specimen, not general interpolation or
phase-duration formulas.

All 110 foreground audio-channel windows retain the 440 Hz source tone, with
RMS 0.0955–0.0965; ten background-only windows are silent. Style changes affect
the picture without fading source audio. Strict whole-document comparison
accounts for 69 remapped clip IDs, duration text and thumbnail. Every remaining
field, source definition and bundled media byte remains unchanged. The second
native save is byte-identical. Fifteen native/candidate/save snapshots pass raw
schema, the existing exact-build profile and native hazard checks without a new
correction. Completed disposable projects, exports and measurements are deleted
after incorporation. Verify actual consumer text layout, requested clocks and
unfamiliar phase settings before delivery.
