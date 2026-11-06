# Recorded cursor path overrides

Use the [recorded-path helper](helper.md#recorded-cursor-path-json-editing) to
create or replace a complete override on an existing standalone moving recording,
or restore its original captured path. The helper owns selectors, clocks, point
specifications, preservation and refusals. These observations use Camtasia Mac
2026.2.4 (2026.132), format 10, with a synthetic browser recording. The earlier
[recorded cursor investigation](cursors.md#editing-and-restoring-recorded-pointer-paths)
establishes the distinct native workflow and source ownership.

## Native override and restoration

Cursor Properties → Edit Cursor Path → Create New Path saves directly under
`ScreenVMFile.parameters.cursorLocation`. It contains `ignoreSource: true` and
a nonempty `edits` list. Each edit has source-clock integer `time`, a planar
three-component `value` and optional native `interp`. It has no typed `point`
descriptor, `keyframes`, `endTime` or `duration`. The `CursorPath` effect used
on ordinary video is a separate representation.

The exercised three-second recording starts at source second one and uses native
scalar `"1/2"` for 2× playback. Creating points at timeline seconds one and two
saves source seconds three and five: ticks 2116800000 and 3528000000 at project
rate 705600000. Their values are `[604.8,589.75,0]` and `[2419.2,1440.25,0]`.
The second point's Bézier object contains handles `[1512,589.75,0]` and
`[1512,1440.25,0]`, followed by `"eioe"`.

Restore Original Path removes only this override and returns to captured TREC
samples. After excluding the project thumbnail and command counter, the complete
native restored document equals the saved baseline. Captured `cursorAction`
click edits/deletions, cursor scale/opacity/smoothing, geometry, effects, source
processing and independent audio retain their original ownership. No TREC is
rewritten or generated.

## Explicit movement, insertion, deletion and hold

Moving the first point to `[793.016,685.949,0]` also moves its outgoing handle
to `[1700.22,685.949,0]`; the incoming handle at the endpoint stays unchanged.
Native insertion at timeline 1.5 seconds creates a source-second-four edit at
tick 2822400000, value `[1606.11,1063.1,0]`. It splits the handles and records
`esIn` and `esOt` timing tokens on the two resulting segments.

Deleting the middle point retains two endpoints with new handles
`[1246.62,685.949,0]` and `[1965.6,1440.25,0]`, using `esOt`. It does not
restore the original curve. Deleting the final endpoint leaves one edit at
source second three, producing a static hold throughout the exercised visible
clip, including before that timestamp. The helper requires the full desired
points and handles explicitly; it does not infer native handle adjustments.

Six complete helper replays match the native creation, movement, insertion,
middle deletion, endpoint deletion and restoration documents after accounting
only for thumbnail and command-counter metadata. Generated fixtures retain
these independent native values and verify unrelated project preservation.

## Rendered persistence and limits

The 42-second sequence has fourteen three-second cells: an original recording,
six helper/native pairs and an invisible-cursor control. Seventy inspected phase
frames and twenty enlarged endpoint crops show matching pointer positions,
curved movement and the one-point hold. Restoration returns the recorded pointer;
the invisible control retains the same background without it. Separate-cell
mean absolute RGB differences remain below 0.353 byte levels per channel,
including ordinary compression variation.

Two fresh-process exports repeat all 1,260 decoded RGB frames and complete
stereo PCM audio exactly. All 28 audio-channel windows retain 440 Hz, with RMS
0.096090–0.096136. Output is 640×360 H.264 at 30 fps with stereo 44.1 kHz AAC.
The first sequence save remaps 56 media IDs and updates the duration UI cache;
all other fields survive unchanged. Its fresh-process save is byte-identical.
Eleven snapshots pass both the raw community schema and the existing exact-build
profile with zero compatibility errors; no schema correction is added. Three
source hashes and the original baseline remain unchanged. Both rendering
processes quit normally and the privacy service remains healthy.

The verified writer covers complete overrides on standalone moving recordings.
Partial source edits/deletions, linked/nested/frozen/stitched recordings and
recording owners carrying a created `CursorPath` effect need separate contracts.
Coordinate values refer to the recording's source geometry; verify fitting and
cursor resources in the actual consumer project. Native Simplify Existing Path,
automatic handle generation and click authoring are separate operations.
Completed disposable projects, exports, images and audits are deleted after
incorporating these findings into the plugin and generated-fixture tests.
