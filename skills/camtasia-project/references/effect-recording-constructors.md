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
Linked recording mirrors, other resource closure and unfamiliar effect-specific
companions require separate evidence. Verify each consumer project's native
output. Completed projects, movies, screenshots and measurements are deleted
after their findings and deterministic tests are incorporated.
