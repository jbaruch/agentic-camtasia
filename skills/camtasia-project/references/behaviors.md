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
infers no outer interval retiming or phase-style replacement. Native references
below describe observations, while the helper module owns its accepted input
and refusal contract.

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
