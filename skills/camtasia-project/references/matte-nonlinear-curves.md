# Nonlinear matte intensity curves

The `set-intensity-curve` command in `skills/camtasia-project/scripts/mattes.py` accepts curve input
schema 2 with per-segment `easing`. Schema 1 retains its linear-only shape.
Both replace only the selected Media Matte intensity default/keyframes.
The [helper contract](helper.md#matte-json-editing) owns command invocation;
the script owns accepted fields, exact source-clock conversion and refusals.

```json
{
  "schema_version": 2,
  "defaultValue": 0,
  "segments": [
    {"start": 1, "end": 3, "value": 1, "easing": "exponential"},
    {"start": 4, "end": 5, "value": 0, "easing": "bounce"}
  ]
}
```

The compiler contract linked above owns easing defaults, accepted choices and
saved codes. Defaults and target intensities must lie in [0,1]. Spring interpolation can
overshoot those endpoints in native output; the helper does not clamp the
renderer or approximate it with extra linear frames.

Segments have positive duration and ordered, nonoverlapping clip-relative
rational timeline bounds. Trimmed and sped-up owners convert those bounds to
source positions in project ticks. Linked wrapper/video mirrors share that
clock and the effect's stable token. Audio children, source definitions, other
effects, edge easing, descendants and unrelated parameter curves survive.
The existing [owner contract](advanced-features.md#media-and-track-mattes)
remains in effect; this update adds no recording-owner constructor.

Existing visual animation intervals retain their own interpolation and opaque
fields. The helper does not change global animation easing to edit one effect.
The native parser can derive missing visual intervals from intensity frames.
A Group can retain linear scale keyframes on an interval whose intensity uses
Bounce. Inspect both owners after a native save; a global UI easing edit can
change every coupled parameter instead.

## Native verification

Locally observed in Camtasia Mac 2026.2.4, project format 10. Native animation
menu edits from Exponential In/Out to Bounce to Spring change only the command
counter and the selected visual interval/intensity-frame interpolation codes.
The second linear intensity interval remains unchanged.
TechSmith's [animation help](https://www.techsmith.com/blog/wp-content/uploads/2024/05/Camtasia-2023-Help-EN-1.pdf)
describes these easing choices; the serialized codes come from these native saves.

A helper-authored 36-second sequence contains linear, exponential, bounce and
spring Callouts, a trimmed 2× linked AV owner, and a 2× Group with an independent
linear scale curve and an ellipse descendant. Both native exports retain the
intended mask regions and distinct temporal profiles. Seventy-eight inspected
frames sample the initial state, ramps, full mask and return. The measured
outside region distinguishes every nonlinear choice from linear; the Spring
return briefly exceeds the initial outside brightness. The Group's ellipse
shrinks independently of its Bounce intensity.

Native saving preserves every intensity target, frame code and source-clock
bound, both linked effect mirrors, the Group scale curve and its child. It
remaps clip IDs, uses absolute root starts on linked children, adds missing
visual intervals and flat linked scale companions, omits unity opacity, fills
native Group defaults and refreshes thumbnail/duration metadata. A fresh-process
reopen/save produces byte-identical project JSON. Both complete decoded video
and audio streams match across that restart. The source definition and bundled
AV bytes remain unchanged.

Thirty-six both-channel audio windows retain the 440 Hz source tone. Baseline
RMS remains about 0.096; the intentional linked 40% contribution raises it to
about 0.134 only during that clip's three-second visible interval. These checks
retain the native audio clock and mix; matte intensity does not mute the linked
audio. Both exports are 36-second 640×360 H.264 with stereo 44.1 kHz AAC.
Completed disposable inputs, movies and measurements are removed after these
findings are incorporated; no historical verification archive is required.

## Rejected point-shaped form

Positive-time intensity frames with `time == endTime`, `duration: 0` and
`interp: "linr"` pass the pinned community schema, then fail native opening
with `Invalid KeyFrame operation ... on parameter intensity`. The interval-only
candidate opens and renders. The project validator rejects this reproduced
shape for the exact build above without changing it. A zero-time descriptor,
another parameter and another editor build are outside that guard's evidence.
The curve helper continues to require positive-duration segments. This result
does not establish a working point-intensity authoring format.
