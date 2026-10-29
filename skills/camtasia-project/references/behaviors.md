# Native behavior phases

These contracts cover Camtasia Mac 2026.2.4, format 10.0. All thirteen palette
presets below were applied natively to the same eight-second linked AV clip,
saved, rendered, and independently loaded/rerendered through native Batch Export.
All fourteen outputs, including the clean control, reproduce their own first
exports in decoded video and audio. Entry, middle, and exit frames show the
actual transformations. These whole-media specimens do not establish every
per-character text option; verify glyph layout separately for a text task.

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
