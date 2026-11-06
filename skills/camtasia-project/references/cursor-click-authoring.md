# Explicit cursor click authoring

Use the [click helper](helper.md#cursor-click-json-editing) to replace explicit
authored left/right click lists on an existing native video cursor path or a
standalone moving recording. The helper owns selectors, specifications, clocks,
anchor handling, preservation and refusals. These observations target Camtasia
Mac 2026.2.4 (2026.132), format 10, using generated AV and a synthetic browser
recording. The earlier [click investigation](cursors.md#inserting-and-removing-clicks)
records the native insertion/removal controls and distinct source owners.

## Generated path events

The existing `CursorPath` effect stores `parameters.cursorAction` as an `int`
descriptor with `uiHints` and zero-duration keyframes. Native creator controls
retain a source-zero frame with `time: 0`, `endTime: 0`, `duration: 0`, `value: 0`.
Linked AV saves matching effect objects on its wrapper and video child.

The exercised three-second clip begins at source second one and uses scalar
`"1/2"` for 2× playback. Native insertion at timeline second one adds source
tick 2116800000, value `1`. A right click at timeline second two adds tick
3528000000, value `4`, at project rate 705600000. Adding a left click at that
same timestamp replaces its value with `1`; it does not combine buttons.
Native removal deletes that point frame. Removing the final authored event
retains the original zero-valued anchor. Insertion at the visible trim start
instead adds tick 705600000 while keeping the distinct source-zero anchor.

An explicit source-zero click can replace the anchor's value. An empty helper
list restores its native zero-valued control form. The earlier native time-zero
Remove UI action left a click value unchanged; do not equate that UI quirk with
the helper's explicit desired-list replacement. Path points, handles, images,
scale, opacity, smoothing, linked tokens and unrelated effects remain separate.

## Recording edits and captured clicks

An authored recording click uses `ScreenVMFile.parameters.cursorAction.edits`,
with source-clock `time` and `value`; it has no typed descriptor or keyframe
duration/end fields. The recording starts at project second three, source
second one, and plays at 2×. Native insertion at project seconds four and five
saves the same source ticks 2116800000 and 3528000000. Clip placement is not
part of those edit timestamps. A click at project second three saves tick
705600000, the visible source in-point.

Adding, replacing and removing authored events changes only this edit list.
For this specimen, removing the last authored event removes `cursorAction`.
An earlier captured-click specimen instead retained empty edits and a native
`deletions` array. Preserve existing deletion entries without inferring their
meaning or changing TREC data. The helper replaces authored edits only; it does
not decode, erase or restore captured clicks. An empty list retains existing
deletions and opaque companion fields, or removes an edits-only override.

Twelve complete helper replays match native insertion, right-click addition,
same-time replacement, second-event removal, clearing and visible trim-start
insertion across both owners, excluding only project thumbnail and command
counter metadata. The recording's original captured click remains visible at
the beginning of the control and cleared cells; authored events add independent
later targets. Generated fixtures retain the independent native event values
and verify complete preservation, including recorded path overrides.

## Rendering, persistence and limits

The 78-second sequence contains 26 three-second cells: twelve helper/native
pairs and separate generated/recorded controls. Native Left Click Target and
Right Click Target effects provide green/yellow event graphics. The generated
video retains its 20% media opacity; the targets inherit that attenuation.
The recording retains its original source scale and captured click tail.

All 156 inspected phase frames and 24 enlarged target crops show matching
authored events, replacement colors, removal, clearing and trim-start timing.
Compare against the matching control; pointer motion, original captured clicks
and codec noise alone do not establish a newly authored event. Separate-cell
helper/native mean absolute RGB differences remain below 0.248 byte levels per
channel. Cleared controls retain their original picture, including the captured
click tail, with separate-cell differences below 0.731.

Two fresh-process exports repeat all 2,340 decoded RGB frames and complete
stereo PCM audio exactly. All 52 audio-channel windows retain 440 Hz, with RMS
0.095725–0.096534. Output is 640×360 H.264 at 30 fps with stereo 44.1 kHz AAC.
The first sequence save remaps 91 IDs, collapses 624 static double descriptors
to their matching bare defaults, and updates thumbnail/duration caches. Event
frames/edits and all other data remain unchanged. The fresh-process save is
byte-identical. Twenty snapshots pass the existing exact-build profile with
zero compatibility errors. Raw errors remain confined to its known missing
`CursorPath`, `LeftClickTarget` and `RightClickTarget` enum entries; no new
schema correction is added. Source bins, three source hashes and the original
baseline remain unchanged. Both render processes quit normally.

Nested, linked recording, frozen and stitched click owners require separate
contracts. Other buttons, interpolation, raw captured-sample deletion editing,
effect construction and click sound/resource authoring are outside this writer.
Verify native effects, target resources and visible event fitting in the consumer
project. Completed disposable projects, exports, images and audits are deleted
after incorporating these findings into the plugin and generated-fixture tests.
