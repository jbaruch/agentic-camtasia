# Created cursor point paths

Use the [cursor-path helper](helper.md#created-cursor-path-json-editing) to replace
the explicit point list in an existing native `CursorPath`. The helper owns
selectors, clocks, interpolation parsing, preservation and refusals. These
observations use Camtasia Mac 2026.2.4 (2026.132), format 10, on ordinary MP4
video. TechSmith's [Cursor Path Creator history](https://support.techsmith.com/hc/en-us/articles/38103527405581-Camtasia-Mac-2022-Version-History)
describes the user-facing workflow; it does not define these serialized fields.

## Native points and mirrored ownership

Cursor Path Creator on linked AV saves `categoryVisualEffects`, `effectName:
"CursorPath"` and matching wrapper/video `effectIndex` tokens. Its
`parameters.cursorLocation` is a typed `point` with zero-duration keyframes:
equal integer `time`/`endTime`, `duration: 0` and a three-component position.
The tested points are `[128,90,0]` at 705600000 ticks and `[512,270,0]` at
1411200000 ticks. The project edit rate is 705600000.

Moving the first point to `[95.2476,71.8534,0]` also moves its outgoing Bézier
handle to `[287.248,71.8534,0]`; the other handle remains `[320,270,0]`. Native
point easing edits can change the selected point's token and the next segment's
token together. Converting the outgoing segment to angle removes the Bézier
object and retains its `esOt` timing string. The helper requires the complete
desired points and handles explicitly; it does not infer these UI operations.

The effect also retains cursor image, opacity, scale, track elevation, click
events and smoothing. Native Separate Video and Audio retains the same point
descriptor on the resulting `VMFile`; its `AMFile` remains separate. Moving the
separated endpoint to `[447.38,243.444,0]` moves its incoming handle to
`[332.18,243.444,0]` and leaves the audio owner unchanged.

## Trimmed clocks, insertion and deletion

A three-second clip with source in-point one second and native scalar `"1/2"`
plays at 2× speed. Moving its path interval to timeline seconds 1–1.5 saves points
at source seconds 3–4. Inserting at timeline 1.2 seconds saves at source 3.4
seconds, tick 2399040000. Both linked mirrors agree.

Native insertion creates `[265.921,133.5,0]` and splits the Bézier handles with
`esIn`/`esOt` timing. Deleting that point retains two endpoints with handles
`[204.8,90,0]` and `[396.8,270,0]`; it does not restore the original handles.
Deleting the second point from the zero-trim control instead leaves one point
at source second one. That one-point path renders a static cursor hold throughout
the tested clip, including before the point's timestamp.

Eight complete native edit replays match the helper after accounting only for
project thumbnail and command-counter metadata. Seven paired controls cover
movement, explicit easing/angle forms, trimmed retiming, insertion/deletion and
separated video; an eighth pair covers the one-point hold. Coordinates refer to
the source image plane. Media transforms and recording cursor overrides remain
separate from these point values.

## Rendered persistence and limits

The final 54-second sequence contains eighteen three-second cells: eight
helper/native pairs and two invisible-cursor controls, with separate zero-trim
and trimmed 2× source clocks. Ninety inspected phase frames and 32 enlarged
endpoint crops show matching positions, curved/angular movement and static holds.
The invisible-cursor controls retain their backgrounds without a pointer.
Separate-cell mean absolute RGB differences stay below 0.695 byte levels per
channel, including ordinary encoding variation between cells.

Two fresh-process exports repeat all 1,620 decoded RGB frames and complete stereo
PCM audio exactly. All 36 audio-channel windows retain 440 Hz, with RMS
0.096095–0.096239. Output is 640×360 H.264 at 30 fps with stereo 44.1 kHz AAC.

The initial comparison save remaps 49 clip IDs, relocates fifteen wrapper labels
to video children, removes seventeen default opacity fields, collapses 54 cursor
static descriptors and eight crop descriptors, and updates two UI caches.
Cursor point values, handles and times survive unchanged. The final sequence
save changes five IDs and the duration UI cache; its fresh-process save is
byte-identical. Seventeen snapshots pass the existing exact-build profile. Raw
schema errors remain limited to its known missing `CursorPath` enum entry; no
new correction is added. Three source hashes and the original baseline remain
unchanged.

The native **Extend Cursor Path to Playhead** action on the trimmed 2× probe
exited with `SIGABRT` while leaving the saved document unchanged and an empty
recovery file. That observation does not identify the internal cause. This
helper supplies explicit full point lists; it does not synthesize that native
extension action or its generated points. Nested, recording, image and Group
owners, resource changes and click authoring need separate contracts. Verify
cursor resources, transformed geometry and visible fitting in the consumer
project. Completed disposable projects, movies, images and audits are removed
after incorporation into the plugin and generated-fixture tests.
