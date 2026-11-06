# Native-template behaviors on recordings

Use the [behavior workflow](helper.md#behavior-json-editing) to copy a saved
native behavior or edit its phase controls, bypass or removal. The helper owns
admitted owners, build checks, matching clocks, selection and refusals. These
Camtasia Mac 2026.2.4/format-10 Fade controls exercise direct moving recordings,
standalone freeze frames, stitched parents and root or Group-contained linked
moving recordings.
They establish neither new
recording constructors nor every preset-specific recording combination.

## Native intervals and reset data

Native Fade adds one direct `GenericBehaviorEffect` without an `effectIndex`.
The four-second moving owner starts at source second one; its behavior outer
start is `705600000` and duration `2822400000`. The eight-second stitched
parent has the same source in-point and behavior start, with duration
`5644800000`. The standalone frozen owner begins at timeline second four and
holds source frame `3504480000` with media duration one; its behavior starts at
local zero and lasts `2822400000`. These different origins survive copying.

Native entry Speed 50% changes the entry duration from one to three seconds,
or `2116800000` ticks, and records `default-Speed-fade: "705600000"`. It leaves
the outer interval and exit duration unchanged. The helper accepts explicit
phase seconds; this observation supplies no general UI percentage formula.
Bypass changes the native flag. Removal retains reset metadata, recorded cursor
data, source selection, child clocks and the stitched virtual hold.

Twelve complete native add/edit/bypass/removal comparisons match helper output
outside thumbnail and command-counter metadata. Complete template clocks are
matched before subsequent timeline placement; the helper performs no outer
interval or phase retiming.

## Independent rendered controls

A 108-second sequence contains six states for each recording family: default
one-second entry, helper-edited three-second entry, bypass, removal, independent
bare media and the native three-second entry. Moving and frozen cells last four
seconds; stitched cells last eight. The stitched parent crosses from moving
content into its held section at local second four. Foreground geometry remains
423.4×265.7 over independent background AV; two additional cells isolate that
background. Frozen controls retain their selected source frame.

Two fresh-process exports repeat all 3,240 decoded RGB frames and complete
stereo PCM audio exactly. Three inspected contact sheets contain 96 phase
frames, including initial fade, ramp, hold, exit and the stitched held section.
Helper-edited/native-edited comparisons have maximum mean absolute RGB
differences of 0.674 byte levels per channel. Separate timeline cells are not a
bitwise-equivalence claim. Bypass agrees with bare media within 0.320 levels;
removal agrees within 0.005. The default entry reaches its hold earlier than
the edited entry, with sampled differences up to 50.999 levels.

All forty measured audio-channel windows retain 440 Hz, with RMS
0.096083–0.096116. The recording supplies video only; these measurements verify
independent background audio preservation. Outputs are 640×360 H.264 at 30 fps
with stereo 44.1 kHz AAC.

## Persistence and preservation

The first native save remaps ninety IDs, collapses ninety-six static parameter
descriptors and refreshes two UI caches. Every other field matches, including
behavior phases, reset data, cursor payloads, child clocks, source processing
and virtual holds. The fresh-process save is byte-identical. All three bundled
source hashes and the original baseline survive unchanged. Eighteen native
capture/candidate/save snapshots pass both raw schema and the existing exact-
build profile without a new correction.

## Root linked moving recordings

The same Mac build saves Fade on both the root `UnifiedMedia` wrapper and its
`ScreenVMFile` child with matching `effectIndex` tokens. The same-source
`AMFile`, recorded cursor data and source processing survive construction,
phase editing, bypass and removal. The helper owns the supported layout and
refusals; Group containment is covered below. Linked held/stitched owners, other
containers and additional scenes retain separate contracts.

The four-second control has source in-point `1411200000`, source duration
`5644800000` and inverse speed `"1/2"`. Its complete behavior outer interval
retains those source ticks. Native entry Speed 50% stores
`suggestedDurationPerCharacter: 4233600000` in both mirrors and
`default-Speed-fade: "352800000"` on the wrapper. The entry is six stored source
seconds, rendered over three timeline seconds at 2× speed. The reset is the
prior one-source-second duration converted to half a timeline second. The
unchanged exit remains one source second. This observation supplies no general
UI percentage formula or automatic retiming contract.

Five complete native comparisons match helper construction, entry editing,
edited-template copying, bypass and removal outside thumbnail and command
counter metadata. An eleven-cell, 44-second comparison includes independent
bare-recording and background-only controls. Two exports from the same running
editor, separated by reopen/save, repeat all 1,320 decoded RGB frames and
complete stereo PCM exactly. Inspected contact sheets contain 99 phase frames;
63 paired samples have maximum mean absolute RGB difference 1.675 byte levels
per channel. Separate encoded cells are not a bitwise-equivalence claim.

Foreground projection against the independent controls measures approximately
0.50 at local second 1.5 for the edited entry, against 1.00 for the default
entry. Bypass and removal retain the full foreground. Sixty-six measured
channel windows preserve the independent 440 Hz background tone; the sixty
recording windows retain 660 Hz within 0.4% of the bare-recording amplitude.
The output is 640×360 H.264, 30 fps, stereo 44.1 kHz AAC.

The first save remaps 63 clip IDs and refreshes duration/thumbnail UI metadata;
every other field matches. The second save is byte-identical. Original baseline
and bundled source hashes remain unchanged. Eight snapshots each report the
known raw-schema timeline-metadata omission, with zero exact-build profile or
native compatibility errors and no new schema correction.

Verify requested presets, text layout, unfamiliar phase controls and further
recording layouts in their consumer project. Completed projects, movies,
screenshots and measurements are deleted after incorporation into the plugin
and deterministic tests.

## Group-contained linked moving recordings

Mac 2026.2.4 (2026.132), format 10, retains the linked Fade mirrors inside a
native Group. The recording has a two-second source in-point, four visible
seconds and inverse speed `"1/2"`; the containing Group starts at timeline
second one and retains its own four-second clock and bounds. Selecting either
the wrapper or video edits the same physical behavior pair. Parent Group
clocks, geometry, effects and layer placement are preserved.

Native entry Speed 50% saves six source seconds, or `4233600000` ticks, in
both mirrors. The wrapper's `default-Speed-fade: "352800000"` retains half a
timeline second, independently of the Group start. Five whole-document
comparisons verify helper construction, phase editing, edited-template copying,
bypass and removal against native controls. Differences are confined to the
thumbnail, command count, Group-open flag and default lane UI metadata.
Complete native templates copy between root and Group-contained owners with
matching child clocks; no parent timing is imported or phase retiming inferred.

A twelve-cell, 72-second sequence pairs default, edited, bypassed, removed and
nested edited-template states with native controls, plus bare-Group and
background-only controls. Two exports separated by saved close/reopen have
identical complete decoded RGB and PCM: 2160 frames, 640×360 H.264 at 30 fps
and stereo 44.1 kHz AAC, using the same running editor. The analysis samples
132 phase frames; two contact sheets show 96 of them. Fifty-five paired samples
differ by at most 1.147 mean RGB byte levels per channel. At local second 1.5,
foreground projection is approximately 0.508 for the edited entry and 1.000 for
the default, bypassed and removed controls. Nested edited-template copying
retains that ramp. The recorded picture includes a macOS permission notice;
no permission was granted during verification.

All 120 measured audio-channel windows retain the independent 440 Hz background.
The 66 active recording windows additionally retain the 660 Hz recorded tone,
with measured amplitude 0.1334–0.1339 and combined RMS 0.1344–0.1352. Outside
the Group's visible interval, and in the background-only cell, the recording
tone is absent. Behavior opacity changes do not fade the recorded audio.

The first native save remaps 82 clip IDs and updates duration/thumbnail UI
metadata; every other field remains equal, including behavior phases, reset
companions, ancestor and child clocks, cursor payload, sources and all audio.
The reopened save is byte-identical. Both bundled source hashes and the original
geometry baseline remain unchanged. Thirteen native/candidate/save snapshots
pass the existing exact-build profile and native hazard checks; each raw result
contains only the known timeline-metadata omission. No schema correction is
added. Completed disposable inputs, renders and measurements are deleted after
incorporating the findings. Further presets, phase-style changes and linked
owner forms retain their separate contracts.
