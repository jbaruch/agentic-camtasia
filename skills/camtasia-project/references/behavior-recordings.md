# Native-template behaviors on recordings

Use the [behavior workflow](helper.md#behavior-json-editing) to copy a saved
native behavior or edit its phase controls, bypass or removal. The helper owns
admitted owners, build checks, matching clocks, selection and refusals. These
Camtasia Mac 2026.2.4/format-10 Fade controls exercise direct moving recordings,
standalone freeze frames and stitched parents. They establish neither new
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
interval or phase retiming. Linked recording mirrors require separate evidence.

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

Verify requested presets, text layout, unfamiliar phase controls and linked
recording layouts in their consumer project. Completed projects, movies,
screenshots and measurements are deleted after incorporation into the plugin
and deterministic tests.
