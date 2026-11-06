# Visual-effect curves on recordings

Use the [effect-curve workflow](helper.md#visual-effect-curve-editing) for an
existing recording effect. The compiler contract owns admitted owners, clocks,
selection and refusals. This reference records native Camtasia Mac 2026.2.4,
format-10 evidence for Sepia intensity. It adds no recording, freeze, stitch or
effect constructor and does not establish arbitrary parameter combinations.

## Native ownership and clock captures

A direct moving `ScreenVMFile` receives a native Sepia effect without an
`effectIndex`. Setting intensity to zero, adding a Custom animation ending at
second two, then setting intensity to one creates an interval from seconds
one to two. The effect retains its typed double descriptor, UI hints and linear
frame interpolation, alongside the matching visual interval.

Native Extend Frame to Playhead creates a `StitchedMedia` parent with moving
and held children. The existing visual interval moves to the parent. Adding
Sepia there and changing its endpoint creates a parent-owned effect curve;
children retain their source selection and clocks. Native removal of stitches
produces standalone moving and frozen owners, retaining the appropriate effect
state on each segment.

On the standalone `ScreenIMFile`, the selected source frame is `5621280000`
and `mediaDuration` remains one tick. Its Custom animation over displayed local
seconds zero to one instead saves effect bounds zero to `705600000`. The held
source position does not offset this interval. All three complete native
curve documents replay exactly through the helper using their captured
parameter descriptors and visual intervals.

## Independent rendered controls

A forty-five-second sequence contains five three-second states per owner:
Spring curve, helper-cleared zero, bypassed curve, independent zero and
independent full-intensity control. All states share a linear horizontal
translation from −60 to +60 over local seconds 0.5–2.5. The generated linked AV
background repeats its original source clock and retains its audio.

All three foreground owners run at 2× speed. The moving recording has a
one-second source in-point. The stitched parent begins at source second four
and crosses into its held child at local second two. The frozen owner retains
its independently selected frame. Native readback at local 0.7 seconds reports
translation −48 and intensity 60% for each owner. After the stitched join, local
2.3 seconds reports translation +48 and full intensity.

Two fresh-process native exports repeat all 1,350 decoded RGB frames and complete
stereo PCM audio exactly. Three contact sheets contain ninety inspected frames.
Every measured foreground rectangle matches the independently calculated bounds
at the sampled phases. Color projection between the zero/full controls is
0.613–0.614 at local 0.7 seconds, 1.110 at 0.9 seconds and 0.984 at 1.5 seconds.
The overshoot remains visible while unrelated geometry keeps linear timing.

Cleared states differ from their zero controls by at most 0.039 mean absolute
RGB byte levels per channel. Sampled bypass states match those controls exactly.
All thirty measured audio-channel windows retain 440 Hz; RMS spans
0.096056–0.096093. The recording has a video-only source track, so this verifies
the preserved independent background audio rather than a linked recording-audio
constructor. Outputs are 640×360 H.264 at 30 fps, with stereo 44.1 kHz AAC.

## Native normalization and limits

The first save remaps seventy IDs, supplies five translation interpolation
defaults, collapses eighty-nine static descriptors, reconstructs fifteen constant
scale/cursor-size companions and refreshes two UI caches. The second save
reconstructs fifteen more frozen scale/cursor-size companions and six constant
zero-intensity curves over retained intervals. A third fresh-process save is
byte-identical. The Spring effect frames and independent linear translation
survive throughout.

Whole-document comparisons retain all other fields. Source-bin definitions,
three bundled source hashes, cursor points and image paths, source selection,
recording processing, child clocks and virtual hold durations survive. The
pinned exact-build schema profile passes the captures and sequence saves with
the existing Sepia identifier correction; no new schema exception is required.

Linked recording mirrors and new effect-specific parameter forms retain separate
native verification obligations. Check the actual consumer project after an edit.
Completed native projects, exports, screenshots and measurements are deleted
after these findings and deterministic tests are incorporated.
