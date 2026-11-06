# Recording, frozen and stitched mattes

Use the [matte helper contract](helper.md#matte-json-editing) for existing
recording-owner media mattes, intensity curves, clearing, bypass and removal.
That contract names the compiler's owner scope and clock rules. Native source
recordings and frozen/stitched owner construction remain separate dependencies;
the matte helper edits an existing owner and preserves its other payload.

## Native ownership

Locally observed in Camtasia Mac 2026.2.4, project format 10. A native Media Matte
on a direct `ScreenVMFile`, standalone `ScreenIMFile` or `StitchedMedia` parent
uses the ordinary Media Matte payload. It has no linked `effectIndex` token.
Native application to a stitched parent leaves both children unchanged. A linked
recording wrapper's mirror contract has not been established; the helper refuses
that form. Ordinary linked AV retains its existing mirror contract.

Native **Edit → Playhead → Extend Frame to Playhead** turns the eight-second
recording into a ten-second stitched owner with moving and frozen children.
A disposable annotation extends the timeline past the recording end before the
command is enabled. Native removal of all stitches creates a standalone held
owner. These operations reproduce the [frozen/stitched ownership contract](animations.md#frozen-and-stitched-owners)
without synthesizing a freeze-frame constructor in the matte helper.

The held owner selects source frame `5621280000` and retains `mediaDuration: 1`.
Its native intensity animation instead has `time: 0`, `endTime: 705600000`,
`duration: 705600000`, with the captured Spring frame code. The whole native
capture matches helper output plus the explicitly added Custom interval and two
UI command counts. Its 494 cursor-location points and cursor-image path survive.
The stitched child's much larger virtual hold duration remains unchanged;
the parent clips it to the visible endpoint. Do not replace that duration or
trim its negative cursor times during a matte edit.

## Rendered clock and lifecycle controls

A helper-authored 104-second sequence contains curve, cleared, bypassed and
removed states for all three owner forms plus an independent background-only
control. The moving recording has a positive source in-point and 2× speed.
The frozen owner has 2× speed, retains its selected source frame and carries
an independent linear translation curve. The stitched parent has a positive
source in-point and crosses its moving-to-held boundary during playback.
The underlying generated AV repeats its original eight-second source clock.

Native intensity readback and mask progression establish source-position bounds
on the moving recording and stitched parent, and a local-zero origin on the
frozen owner. The existing inverse-speed conversion applies independently of
source-frame selection. Clearing preserves the frozen translation and cursor
data. Bypass and removal restore the native recorded pictures and cursor rather
than behaving like a zero-intensity matte.

Two fresh-process native exports have identical complete decoded video and
audio. Three contact sheets contain 143 unique sampled frames; additional
full-resolution views verify the synthetic page and recorded pointer. Across
the samples, clearing differs from the background-only control by at most 0.161
mean absolute byte levels per RGB channel; bypass and removal differ by less
than 0.069. These small encoding differences remain separate from the measured
outer-mask regions that distinguish initial, ramped, full and cleared states.
The frozen geometry moves independently, and the stitched source passes into
its held section without changing its descendants' saved clocks.

All 104 both-channel audio windows retain the 440 Hz background tone with RMS
between 0.0957 and 0.0967. The test recording has only a video source track;
this verifies preservation of the independent linked background audio, not a
new microphone/system-audio recording-wrapper constructor. The native outputs
are 104-second 640×360 H.264 with stereo 44.1 kHz AAC.

## Native normalization and preservation

The first native save remaps clip IDs, uses absolute starts on linked background
children, refreshes UI caches, collapses static held descriptors, derives missing
visual intervals and adds flat scale/cursor-size companions on marked stitched
parents. The second save adds twelve flat scale/cursor-size companions and one
constant-zero intensity companion on the held owners. Those companions use the
retained visual intervals; the unrelated translation curve survives. A third
fresh-process save is byte-identical to the second.

Whole-document comparisons permit only those demonstrated changes. Source-bin
definitions and all three bundled source hashes remain unchanged. Cursor paths,
all cursor points, recording processing, child timing, source selection and other
payload remain under comparison. The candidate and native saves pass the pinned
raw schema and exact-build profile without a new correction. Completed
projects, movies, screenshots and measurements are removed after incorporating
these findings; no historical verification archive is required.

[Media/track composition controls](matte-composition.md) have separate native
evidence. Any working point-intensity form retains separate investigation.
Verify a consumer project's actual native output;
these cases do not establish every recording stream or composition arrangement.
