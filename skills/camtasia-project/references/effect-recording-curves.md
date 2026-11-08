# Visual-effect curves on recordings

Use the [effect-curve workflow](helper.md#visual-effect-curve-editing) for an
existing recording effect. The compiler contract owns admitted owners, clocks,
selection and refusals. This reference records native Camtasia Mac 2026.2.4,
format-10 evidence for Sepia intensity. It adds no recording, freeze, stitch or
effect constructor and does not establish arbitrary parameter combinations.
[Native-template construction and lifecycle](effect-recording-constructors.md)
have separate evidence.

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

Root linked moving recordings have the additional controls below. Other linked
variants and new effect-specific parameter forms retain separate native
verification obligations. Check the actual consumer project after an edit.
Completed native projects, exports, screenshots and measurements are deleted
after these findings and deterministic tests are incorporated.

## Linked moving recordings

Locally observed in Camtasia Mac 2026.2.4 (2026.132), project format 10. Existing
typed-double Sepia intensity on a root `UnifiedMedia` / `ScreenVMFile` pair uses
matching wrapper/video effect payloads and a stable shared token. The source
also supplies a stereo `AMFile` system-audio child. The compiler's `selected`
and `effects.constructor_owners` own the admitted linked form, complete clocks,
source/audio bindings and token checks. Group-contained moving recordings have
the additional evidence below. Linked held, stitched and other containing owners
retain separate contracts. This edits existing effects and descriptors; it adds
no effect or recording constructor.

The native linear control has a two-second source in-point and 2× speed.
Its local zero–one-second interval saves source bounds `1411200000`–`2822400000`
with duration `1411200000` at project rate 705600000. The complete native document
replays through the schema-2 helper without changes. A native Spring menu edit
changes both effect frames to `sprg` and also changes the shared visual interval.
The helper matches both effect payloads while retaining the existing shared
interval's linear easing. Thumbnail and command-count caches remain separate
from this explicit interval-easing distinction.

Independent native position edits create a linear −60 to +60 translation over
that interval. Applying Spring only to intensity preserves the complete native
geometry parameters, visual interval, cursor settings, reset data, audio and
source definitions. Native readback at local 0.1 seconds shows position −48 and
intensity 60%; at 0.2 seconds it shows position −36 and intensity 112%. Those
values distinguish the retained linear geometry from the nonlinear effect.

A 27-second comparison contains native/helper Spring controls, independent
native linear geometry, Spring with retained linear geometry, cleared zero,
native/helper bypass, full intensity and background-only references. Seventy-two
inspected phase frames cover the initial value, ramp, overshoot and hold. All
48 measured foreground bounds agree with the independent geometry within two
pixels.

Twenty-four matched-time comparisons differ by at most 1.258 mean RGB byte
levels per channel, separately from repeat-export equality. Foreground color
projection against zero/full controls is approximately 0.599 at local 0.1
seconds, 1.107 at 0.2 seconds and 0.980 at 0.5 seconds. Clearing matches the native
bypass picture while its geometry keeps moving. The recorded source contains
a macOS permission notice; no permission was granted for verification.

Native save/close/reopen and two exports in the same editor process repeat all
810 decoded RGB frames and complete PCM audio exactly. Output is 27-second
640×360 H.264 at 30 fps with stereo 44.1 kHz AAC. Eighteen both-channel one-second
windows retain the 440 Hz background tone and, in recording cells, the 660 Hz
system-audio tone. The background-only reference has no recorded tone; RMS
spans 0.09606–0.13480.

The first save remaps 51 clip IDs, updates the duration label and collapses both
cleared intensity descriptors to zero scalars. Reopening regenerates two
constant-zero frames from the retained visual interval and refreshes the
thumbnail; the third save is byte-identical. Whole-document comparisons account
for those changes and preserve every other field. Original baseline/source and
bundled AV hashes remain unchanged. Eight snapshots pass the existing build
profile and native hazard checks. Their 44 raw errors are the known timeline
metadata and wrapper Sepia-enum omissions; no new correction is needed.
Completed comparison artifacts are removed after incorporation.

The [linked frame-extension workflow](effect-recording-extensions.md) adds
cross-join native parent curves, complete template copying and clearing on
Mac 2026.2.5. Its linked moving child and silent hold remain separate descendants.

## Group-contained linked moving recordings

The effect-curve helper now opts into existing Group-contained linked moving
recordings, including nested Groups. Its descriptor, interval, mirror and token
rules remain in the helper contract. Inputs stay relative to the recording's
visible timeline, independently of Group placement. Parent geometry/clocks,
recorded audio, reset data and source processing survive authoring and clearing.
No Group retiming or owner constructor is supplied.

Controls reconstruct the native linear interval recorded in 0.30.0 and the
Spring/linear-position fields recorded in 0.28.0, on a newly saved native Group
baseline from the same Mac 2026.2.4/format-10 build. These are reused template
controls. The recording retains a two-second source in-point, inverse speed
`"1/2"` and four-second visible duration. The outer Group begins at timeline
second one; a second enclosing Group preserves the child's clock. Local
zero–one-second effect intervals retain source bounds `1411200000`–`2822400000`
and duration `1411200000` in both mirrors.

Native property readback on the authored Spring effect with independent linear
translation shows X −48 and intensity 60% at local second 0.1, then X −36 and
intensity 112% at 0.2. The effect preserves the existing linear visual interval
and geometry frame while storing its own `sprg` frame. Clear removes only the
selected effect curve and retains those position fields. The Group's existing
frame clips the translating child; the helper preserves that frame. Measured
bare-control bounds move from X 138–441 through 139–501 to 199–501, with Y
62–297 throughout. Native readback distinguishes stored linear position from
the clipped visible rectangle.

Thirteen six-second cells compare reused linear/Spring templates, helper
authoring, independent linear geometry, clearing, bare/full controls and nested
Group variants. Two exports from the same editor process, separated by native
close/reopen/saves, repeat all 2,340 decoded RGB frames and complete stereo PCM
exactly. Inspected contact sheets contain 117 phase frames. Forty-five paired
samples have maximum mean absolute RGB difference 0.937 byte levels per channel;
separate encoded cells are not a bitwise-equivalence claim. Spring color
projection against matching bare/full geometry controls measures approximately
0.597, 1.107 and 0.979 at local seconds 0.1, 0.2 and 0.5; clearing restores the
bare-control color while retaining movement and clipping.

One hundred thirty channel windows retain the independent 440 Hz background
tone; the 72 recording-active windows retain 660 Hz within 0.2% of the bare
geometry control. Outside Group intervals and in the background-only cell,
measured 660 Hz amplitude stays below 0.00007 on normalized PCM. Output is
78-second 640×360 H.264 at 30 fps, stereo 44.1 kHz AAC.

The first save remaps 89 IDs, closes twelve Group-open UI flags, adds seven
default parameter-level translation interpolations, collapses four cleared
intensity descriptors and refreshes duration/thumbnail UI metadata. Their
linear geometry frames remain unchanged. The second save reconstructs four
constant-zero effect frames from retained visual intervals and refreshes the
thumbnail. The third save is byte-identical. Whole-document comparisons
preserve every other field. Original baseline/source and bundled AV hashes
remain unchanged. Thirteen snapshots pass the existing exact-build profile and
native hazard checks; 62 raw errors are the known timeline-metadata and wrapper
Sepia-enum omissions. No new schema correction is needed. Completed disposable
artifacts are removed after incorporation.
