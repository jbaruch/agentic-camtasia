# Native-template effects on recordings

Use the [visual-effect workflow](helper.md#visual-effect-json-editing) to copy a
saved native effect or edit its lifecycle. The helper contract owns admitted
owners, build checks, template selection, timing and refusals. This reference
records Camtasia Mac 2026.2.4/format-10 Sepia controls on moving recordings,
standalone freeze frames and stitched parents. It supplies no recording, freeze
or stitch constructor and does not establish every effect-specific combination.

## Native payloads and reset data

Native Sepia application creates a direct `categoryVisualEffects` instance on
each exercised owner without a linked `effectIndex`. Static saves can collapse
its intensity to a bare numeric scalar. Native intensity changes retain the
same effect placement; bypass changes its flag. Deletion retains owner reset
metadata and leaves recorded cursors, source selection and stitched children
intact.

Ten native add/edit/bypass/removal comparisons match the helper outside UI
thumbnail/command counters and one reset-companion addition: the first moving-
recording intensity edit adds `default-Sepia-intensity: "1"`. The helper retains
existing reset data and copies recorded companions from the selected template;
it does not infer absent reset defaults. Select a native template containing
the intended reset companions when those controls matter. The rendered
constructor comparison uses the captured half-intensity template with that
companion present.

A separate frozen native Custom interval saves a typed intensity default zero,
then reaches one over local seconds zero to one. Its held source frame remains
`5621280000`, independently of the local effect bounds. Copying this complete
effect preserves the descriptor, hints and keyframes. The recipient initially
has no visual interval; native loading reconstructs it from the copied effect.
The helper does not copy the template owner's geometry or cursor tracks.

## Independent rendered controls

A fifty-eight-second sequence has six three-second states for each owner:
constructed half intensity, helper-edited full intensity, bypass, removal,
independent bare media and the native half-intensity control. Foreground media
has matching 423.4×265.7 geometry over generated linked background AV. Moving
recordings use a one-second source in-point at 2× speed; the stitched parent
begins at source second four at 2× and crosses into its held section at local
second two. Static template copies retain those recipient clocks. Frozen
controls keep their selected source frame.

Two additional two-second cells compare the copied complete frozen interval
with the original native animated owner. Construction uses matching clocks;
subsequent timeline placement leaves its local effect interval intact.

Two fresh-process exports repeat all 1,740 decoded RGB frames and complete
stereo PCM audio exactly. Four contact sheets contain 98 inspected phase
frames. All ninety static-control rectangles match the independently expected
pixel bounds. Constructed/native half-intensity comparisons have maximum mean
absolute RGB differences of 0.557 byte levels per channel for moving recordings
and 0.012 for frozen/stitched owners. The moving helper/control owner payloads
are identical apart from clip identity, timeline placement and display name;
these separate-cell rendered comparisons are not bitwise-equivalence claims.

Removal matches the bare control at every sampled phase. Bypass differs by at
most 0.021 mean RGB byte levels per channel. Full intensity differs from bare
media by approximately 30.599 levels, visibly retaining the intended Sepia
state. The copied/native animated cells agree within 0.077 levels over all sixty
frames, with initial, ramped and final color states inspected separately.

All forty measured audio-channel windows retain 440 Hz, with RMS
0.096056–0.096181. The recording supplies video only; this verifies preservation
of independent background audio rather than a new recording-audio mirror
contract. Outputs are 640×360 H.264 at 30 fps with stereo 44.1 kHz AAC.

## Persistence and preservation

The first native save remaps ninety-two IDs, collapses 114 static descriptors,
reconstructs the copied effect's visual interval and refreshes two UI caches.
The second reconstructs six constant scale/cursor-size companions across the
two animated frozen cells. A third fresh-process save is byte-identical.
Whole-document comparisons preserve every other field, including all effect
payloads, source-bin definitions, cursor points and image paths, child clocks,
virtual holds and source processing. All three bundled source hashes survive.
Eighteen capture/candidate/save snapshots pass the existing exact-build schema
profile; no new correction is required.

Motion Path lifecycle operations retain their dedicated rotation contract.
Root linked moving recordings have the additional contract below. Other linked
variants, resource closure and unfamiliar effect-specific companions require
separate evidence. Verify each consumer project's native
output. Completed projects, movies, screenshots and measurements are deleted
after their findings and deterministic tests are incorporated.

## Root linked moving recordings

Locally observed in Camtasia Mac 2026.2.4 (2026.132), project format 10. A root
`UnifiedMedia` contains `ScreenVMFile` video and same-source stereo `AMFile`
system audio. Native Sepia creates matching `categoryVisualEffects` instances
on wrapper and video, with shared `effectIndex: "0"`. Static intensity saves as
a numeric scalar. The native half-intensity edit adds the wrapper reset value
`default-Sepia-intensity: "1"`; bypass changes both flags, and removal retains
the reset value. Audio, source definitions and all owner clocks remain equal
through these native edits.

The helper's linked-recording constants and `constructor_owners` own accepted
owners, source/audio bindings, complete clock checks and unique-token refusals.
Generic visual-effect construction and lifecycle use this opt-in. Behavior and
[effect-curve authoring](effect-recording-curves.md#linked-moving-recordings)
retain their separate owner contracts.
Group-contained moving recordings have the additional evidence below. Further
linked held, stitched and other containing forms need their own evidence.

Five complete helper/native comparisons cover full and half construction,
half-intensity editing, bypass and removal. Only thumbnail/command caches and
the native first-edit reset addition are excluded. Construction from the native
half template copies that reset companion; editing preserves existing companions
without inferring an absent default. Existing unrelated effects and audio tokens
participate in fresh-token allocation, without reordering or renumbering them.

A native Custom interval also supplies a complete animated Sepia template.
On the trimmed 2× owner, local zero–one second becomes source positions
`1411200000`–`2822400000` with duration `1411200000`, project rate 705600000 and
a two-second source in-point. Both effect mirrors contain the same linear
intensity frame and native descriptor. The constructor copies those complete
payloads only with matching owner clocks; it copies no geometry or visual
animation track and performs no retiming. Native loading derives the missing
visual interval from the copied effect. The separate effect-curve contract
linked above records authoring and clearing on this linked form.

A 42-second sequence compares those helpers with independent native full,
half, bypass, removal and animated controls, plus bare recording and background
references. The recording remains inset and plays from its positive source
in-point at 2×. Fifty-two inspected phase frames include the copied interval's
start, ramp and endpoint. Thirty matched-time comparisons differ by at most
0.941 mean RGB byte levels per channel. Separate cells retain these encoding
differences; full intensity visibly changes the foreground, and bypass/removal
restore its original color. The recorded picture includes a macOS permission
notice; no permission was granted for this verification.

Native save/close/reopen and two exports in the same editor process produce
identical complete decoded RGB and PCM streams: 1260 frames, 42 seconds,
640×360 H.264 and stereo 44.1 kHz AAC. Twenty-eight both-channel one-second
windows retain the 440 Hz background tone and the 660 Hz recorded-system-audio
tone in recording cells. The background-only cell has no recorded tone. RMS
spans 0.09607–0.13480.

Whole-document first-save comparison accounts for 81 remapped clip IDs, one
derived visual interval, the duration label and thumbnail. Every other field
remains equal. The second save is byte-identical; original baseline/source and
bundled AV hashes remain unchanged. Nine snapshots pass the existing exact-build
profile and native hazard checks. The 43 raw errors are the known timeline
metadata and wrapper Sepia-enum omissions; no new correction is needed.
Completed comparison projects, media, exports and measurements are disposable.

## Group-contained linked moving recordings

The same Mac 2026.2.4 build saves an existing linked moving recording inside a
native Group, including a second enclosing Group. Sepia still belongs to the
recording wrapper/video pair, with the same token, scalar intensity, reset
companion and bypass/removal payloads as the root form. The containing Groups
remain independent owners. The helper's `constructor_owners` opt-in owns this
extension; behavior, matte and effect-curve authoring retain separate scopes.
No Group, recording or freeze constructor is supplied.

The native outer Group starts at timeline second one, lasts four seconds and
uses local media bounds zero–four seconds with scalar one. The recording inside
starts at Group-local zero and retains source in-point `1411200000`, duration
`5644800000` and inverse speed `"1/2"`. Native second-level grouping adds another
Group without changing the recording's clock. A native Custom Sepia interval
saves source bounds `1411200000`–`2822400000`, duration `1411200000`, on both
effect mirrors. Its one-second visible ramp starts at the Group's visible
beginning. Copying the complete template retains these child-source ticks;
ancestor placement is preserved, with no Group retiming or curve authoring.

Five full helper/native lifecycle comparisons cover construction, editing with
the captured reset companion, half-template copying, bypass and removal. As on
the root owner, a first native intensity edit adds the reset value; the helper
preserves or copies it without inventing an absent default. Whole-document
comparisons exclude thumbnail/command caches and the native Group-open and
track-height/lock UI initialization. Audio and source-bin payloads match.

Fourteen six-second cells compare native/helper half intensity, full editing,
bypass, removal and complete timed-template copies in one and two Groups, plus
independent bare-Group and background-only controls. Two exports in the same
editor process, separated by close/reopen/save, repeat all 2,520 decoded RGB
frames and complete stereo PCM exactly. Inspected contact sheets contain 126
phase frames; 81 paired samples differ by at most 0.846 mean RGB byte levels per
channel. Separate encoded cells are not a bitwise-equivalence claim.

Color projection against independent full/bare controls measures approximately
0.51 for half intensity and at the timed ramp's midpoint. Bypass/removal restore
the original color. One hundred forty channel windows preserve the 440 Hz
background tone; the 78 recording-active windows retain 660 Hz within 0.2% of
the bare-Group amplitude. Outside the Group interval and in background-only
controls, measured 660 Hz amplitude stays below 0.00007 on normalized PCM.
The 84-second output is 640×360 H.264 at 30 fps, stereo 44.1 kHz AAC.

The first save remaps 96 IDs, closes eight Group-open UI flags, reconstructs two
missing visual intervals from copied effects and refreshes the duration label.
Every other field matches, including ancestor geometry/clocks, recording/audio
payloads and source processing. The second save is byte-identical. Original
baseline/source and bundled AV hashes remain unchanged. Eleven snapshots pass
the existing exact-build profile and native hazard checks; 47 raw errors are
the known timeline-metadata and wrapper Sepia-enum omissions. No new schema
correction is needed. Completed disposable artifacts are removed after these
findings and tests are incorporated.
