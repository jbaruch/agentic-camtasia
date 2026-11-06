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
Native application to a stitched parent leaves both children unchanged. Root
linked moving recordings have the additional mirror and audio controls below.
Ordinary linked AV retains its existing mirror contract.

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

## Linked moving recordings

Locally observed in Camtasia Mac 2026.2.4 (2026.132), project format 10. Native
Recorder creates a root `UnifiedMedia` with a `ScreenVMFile` video and same-source
stereo `AMFile` system audio. Native Media Matte application creates matching
wrapper/video effects with the same `effectIndex` token. Intensity, bypass and
removal change both mirrors; source definitions and the audio child survive.
The helper's `media_targets` and linked-recording constants own accepted owner
shapes and clock checks. Held, stitched and nested linked recording variants
retain separate contracts.

The native half-intensity edit adds the wrapper reset companion
`default-MediaMatte-intensity: "1"`. The helper preserves an existing companion
without inventing a missing reset value. The native effect otherwise uses the
ordinary matte payload, including its category and track-depth parameter.

A native Custom animation on a trimmed 2× recording confirms the existing
source-position clock on both mirrors. Its local zero–one-second interval saves
`time: 1411200000`, `endTime: 2822400000`, `duration: 1411200000`, and linear
interpolation at project rate 705600000 with a two-second source in-point.
The independent helper result matches both complete effect payloads. The audio
retains its own stream selection, stereo channel binding, processing and clocks.

A 36-second root sequence pairs helper construction, half intensity, bypass,
removal and linear curves with independently captured native controls. Clearing
the curve to half intensity matches the static half control. An independent
background-only cell distinguishes masking from the recorded picture. The
recording is inset, has a positive source in-point and plays at 2×. Forty-six
sampled frames show the opaque interior, black or partially visible exterior,
linear ramp and restored recording picture for bypass/removal. Twenty-one
matched-time comparisons differ by at most 1.055 mean RGB byte levels per
channel; these inter-cell encoding differences are separate from repeat-export
equality. The recorded picture contains a macOS permission notice; no permission
was granted to obtain these results.

Native save, close, reopen and a second export produce identical complete
decoded RGB and PCM streams: 36 seconds, 1080 frames, 640×360 H.264 and stereo
44.1 kHz AAC. These two exports use the same editor process. Twenty-four
both-channel one-second windows retain the 440 Hz background tone and, in
recording cells, the 660 Hz system-audio tone. RMS spans 0.09608–0.13481; the
background-only control has no recorded-audio contribution.

Whole-document first-save comparison accounts for 70 remapped IDs, fourteen
static intensity collapses, twelve omitted unity-opacity fields, one derived
visual interval, two source-metadata basename updates and UI caches. Every other
field remains equal, including all audio, recording source selection and matte
clocks. The second save is byte-identical. Bundled recording/background hashes
and the original baseline remain unchanged. Ten snapshots pass the existing
exact-build profile and native hazard checks; each raw-schema result reports
only its previously documented timeline-metadata omission. No new profile
correction is needed. Completed disposable comparison artifacts are removed
after incorporating these observations.
