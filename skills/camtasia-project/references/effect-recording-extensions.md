# Effects across linked recording frame extensions

Use the existing [effect construction/lifecycle](helper.md#visual-effect-json-editing)
and [typed curve](helper.md#visual-effect-curve-editing) routes. This workflow
records native Sepia controls in Mac Camtasia 2026.2.5 (2026.136), format 10.
Select the inspected stitched parent for its own effect. A saved parent effect
can have no token; omit the optional token selector in that case. A static scalar
is not a typed animation descriptor. Capture a native animated effect before
authoring its curve, or copy that complete native effect with matching clocks.

## Native owners and clocks

Native **Edit → Playhead → Extend Frame to Playhead** creates one `StitchedMedia`
parent with a linked moving `UnifiedMedia` child and a separate silent
`ScreenIMFile` hold. **Modify → Remove → All Stitches** restores the moving pair
and standalone hold. These are native owner constructors, separate from the
effect helpers. See the [frame-extension ownership evidence](matte-recording-owners.md#frame-extensions-of-linked-recordings).

The exercised recording starts at timeline second one, selects source seconds
two–ten and plays at 2×. Its two-second visible extension ends at timeline second
seven. Parent `mediaStart`, `mediaDuration`, `scalar` and `duration` are
1411200000, 8467200000, `"1/2"` and 4233600000 at edit rate 705600000. The moving
wrapper/video/audio children retain start/mediaStart zero, duration/mediaDuration
7056000000 and scalar one. The hold starts at 7056000000, retains virtual duration
5081731200000, selected source frame 7008960000 and `mediaDuration: 1`.
Preserve its negative cursor times and let the parent bound the visible hold.

Native Sepia application, intensity, bypass and removal affect one parent
instance without adding effects to the moving wrapper, video, audio or hold.
The unstitched hold receives its own direct effect and has no audio child.
Six whole-document helper/native lifecycle comparisons differ only in UI command
counters and the first native intensity edit's reset addition. Construction from
the half-intensity template includes that reset companion; scalar editing retains
existing history without inventing a missing reset value.

## Cross-join animation and clearing

A native Custom interval animates parent Sepia from zero to one across the
moving/held join. The captured interval uses Spring easing. Clip-relative seconds
3.5–4.5 map to source ticks 6350400000–7761600000, duration 1411200000. Native
readback shows intensity 60% and 112% at timeline seconds 4.6 and 4.7; the latter
is the Spring overshoot. The parent continues that effect through the silent hold.

Schema-2 curve authoring reproduces the complete captured document. Complete
timed-template copying retains the effect's descriptor, frame easing and source
ticks without copying owner geometry or visual intervals. Its complete matching-
clock requirement remains in force. Clearing to half intensity preserves the
visual interval, reset data, child clocks, recorded cursor payload and sources.
Native reopening can regenerate constant frames from that retained interval;
clearing does not promise that later native saves omit every constant frame.

## Rendered and preservation controls

A sixteen-cell sequence compares native/helper full and half intensity, bypass,
removal, held-only construction, authored/copied curves and cleared half intensity,
with bare unstitched and independent background controls. Two exports separated
by a verified editor-process exit and fresh native reopen have identical complete
RGB/PCM streams, covering 7680 decoded frames in total. Each movie is 128 seconds, 640×360
H.264 at 30 fps, with stereo 44.1 kHz AAC. Positive source handles in both editor
processes point to the matching MP4 and TREC inside the disposable test bundle.

Three contact sheets contain 62 visually inspected frames. Across 128 sampled
frames, 56 paired native/helper samples differ by at most 0.874 mean RGB byte
levels per channel. Authored/copied curve pairs differ by at most 0.087 levels.
These separate encoded cells retain small differences; the exact equality above
compares the two complete exports. Color projection against full/bare controls
measures about 0.508 for half and cleared half, 0.604/1.101 during the Spring
ramp/overshoot and zero for bypass/removal. Held-only Sepia changes the held
section while preserving the earlier moving picture.

All 128 measured audio-channel windows retain the 440 Hz background tone at
amplitude 0.1358–0.1364. Recording-active windows retain 660 Hz at 0.13276–0.13288;
its maximum amplitude during holds, outside the recording and in the background-
only cell is below 0.000029. Parent effects and unstitching do not extend recorded
audio. The recorded permission notice is picture content; this test grants no
OS permission. The saved selected-frame field retains the earlier
[native-picture limitation](matte-recording-owners.md#frame-extensions-of-linked-recordings);
this workflow does not repair or infer the proprietary recording's frame mapping.

Strict first-save comparison accounts for 120 remapped clip IDs, 90 collapsed
held descriptors, twelve flat parent companions, one derived copied visual
interval and one collapsed cleared-intensity descriptor. The copied interval
omits easing while the effect's own Spring frame remains. The second save adds
one constant intensity frame and refreshes the thumbnail; the third save is
byte-identical. Every other project value remains unchanged. Both source hashes
and canonical inputs survive. Thirteen snapshots pass the existing exact-build
profile and compatibility checks; raw errors are only the existing Sepia enum
omission. No schema correction is added. Completed disposable verification files
are removed after incorporating these results and fixed regressions.

These controls establish this parent/hold workflow. Other wrapper/container
forms, effect-specific point/resource controls and new combinations retain their
own native verification obligations.
