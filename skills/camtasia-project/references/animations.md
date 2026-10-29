# Native animations and canvas geometry

These observations cover Camtasia Mac 2026.2.4, format 10.0. All twelve native
animation presets, five easing choices, Auto Animate, crop, corner pin, a short
clip, and a trimmed/retimed clip have saved native specimens. Twenty-five
independent saved-project reloads/rerenders reproduce their own first exports
in decoded video and, where present, audio. One hundred sampled frames cover
movement, opacity, geometry, and boundary behavior. Preset values below describe
the exercised source/canvas pair; they are not universal framing constants.

## JSON interval authoring

The [animation helper contract](helper.md#animation-json-editing) supplies
inspection, interval authoring, coupled easing and interval removal commands. It targets native
visual geometry, resolving linked media to the video child. Explicit
initial values supply missing parameters; existing defaults remain intact.
Interval/frame easing and parameter-level interpolation have separate inputs.

Nineteen saved native projects replay through this helper, including Custom,
Restore, opacity, tilts, zooms, all five easing choices, Auto Animate's saved
result, clipped negative bounds, source-position retiming and supplied SmartFocus
curves. Whole-project comparisons allow only fixed UI command counts/thumbnail
caches and the short clip's duration label. Audio, wrapper effects, source data
and all other fields stay under comparison. The existing nineteen native render
pairs have freshly reverified complete decoded video/audio; Camtasia is not
opened or asked to render again. Evidence is `animation-json-native-checks.json`.

This helper does not run recorded-subject analysis or infer framing from a preset
name. Additional owner forms and unobserved controls retain separate
implementation work. Ordinary point-frame limits are recorded below.
Unknown coupled/effect-owned curves are
preserved through refusal rather than flattened by a global easing change.

## Frozen and stitched owners

On Mac 2026.2.4/format 10, Option-dragging the end of a screen recording creates
a `StitchedMedia` parent with moving `ScreenVMFile` and frozen `ScreenIMFile`
children. The exercised parent lasts ten seconds: eight moving and two held.
The frozen child has `mediaDuration: 1`, source-frame `mediaStart: 5621280000`
(7.9667 seconds at edit rate 705600000), and virtual duration `2540183520000`.
The parent clips that virtual hold to its visible end. Child cursor-location
points include negative times. Preserve these clocks, cursor paths and large
durations instead of trimming them to the parent's length. Removing all stitches
produces separate moving and frozen root clips; the held root has a two-second
visible duration but retains the same source-frame selection.

Both owners store geometry and visual intervals directly. Stitched parent
intervals use the usual source-position clock. A `ScreenIMFile`
instead stores animation bounds from local zero: its zero–one-second interval
uses `time: 0`, `endTime: 705600000`, independently of the selected source frame.
The interval helper preserves all children and recording data. Its
`source_bounds` owns the inverse-speed conversion. Hotspot and matte owner scopes
remain separate; the independently verified Motion Path extension is recorded below.

Fresh native saves normalize recording parameters in two stages. First, static
typed frozen crop, cursor and scale values become bare doubles; animated scales
lose parameter-level `eioe`. Marked stitched parents rebuild missing constant
scale and `cursorScale` curves. The second save builds those constant companions
on marked frozen owners. A third fresh-process save is byte-identical. Constant
`cursorScale` interval frames must retain the initial value and match the marker
bounds. The helper includes this observed companion in easing/removal while
refusing dynamic or point-shaped cursor coupling. It does not accept cursor
scale as authored geometry input.

Six native creation/scale/easing operations and two pre-animation removal
controls match whole-document helper results outside fixed UI counters and
thumbnail caches. The accessibility Remove Animation attempt deleted a clip
and was immediately undone; it is not counted as a native removal replay.
Removal is verified against the native pre-animation controls and rendered
output. Four additional replays against the normalized saved project verify
companion easing/removal. A 160-second, sixteen-block native/helper sequence
exports independently twice: all 4,800 decoded video frames and stereo audio
match. Eighty inspected samples show moving/held continuity, scale, Spring,
Bounce and restored geometry; sixteen tone and sixteen silent hold windows
verify audio. The existing schema/profile needs no correction. Deterministic
tests retain the contract after completed disposable media/records are deleted.

### Retimed frozen recordings

Native Clip Speed accepts frozen screen recordings. A hold selecting source
four seconds keeps `mediaStart: 2822400000` and `mediaDuration: 1` at both 2×
speed (`scalar: "1/2"`, four-second visible duration) and 0.5× speed (`scalar: 2`,
sixteen-second duration). Its animation clock still starts at local zero.
A native one–two-second Custom marker at 2× saves bounds
`1411200000`–`2822400000`; at 0.5× it saves `352800000`–`705600000`.
Native scale edits use exactly the same bounds, without adding the source-frame
selection. The helper now accepts these retimed owners for authoring, easing
and removal using the existing commands.

Retiming an existing 2× animation to 0.5× leaves its keyframe integers intact:
the visible animation moves from one–two seconds to four–eight seconds. It does
not change which source frame is held. The runtime comparison includes this
case alongside native empty/scale captures and pre-animation removal controls
at both speeds. Fresh loading reconstructs constant scale/cursor-size companions
around markers; the resulting project reopens byte-identically. Recorded cursor
points and source data remain under whole-document comparison.
In the held-source-four-second fixture, native loading supplies cursor points
both before and after local zero. The pointer moves along that retained curve
even while the recorded picture is held; do not flatten cursor points as an
incidental part of geometry editing.

Seven whole-project native/control comparisons and two normalized-project
removals verify the extension. Fourteen paired blocks export twice from fresh
native processes, each 176 seconds/5,280 frames. Every decoded RGB frame and
stereo PCM sample matches; seventy inspected pictures distinguish one–two-second
motion, four–eight-second retimed motion, removed geometry and the fast hold's
four-second end. Fourteen 440 Hz windows and eight silent windows retain the
separate source-audio behavior. All source hashes and both native MP4/TREC
handles pass; raw schema/profile checks need no correction.

## Removing a visual interval

Nine native Remove Animation captures verify deleting the sole, first and last
intervals, a trimmed/retimed selection, negative short-clip bounds, nondefault
initial scale, all supported geometry fields with default/nondefault initial
values, and the first SmartFocus interval on a recorded `ScreenVMFile`.
The helper reproduces each complete native document outside its one UI command
increment and thumbnail cache. Source data and linked audio stay unchanged.

Removing an interval removes its matching geometry targets. Other interval
markers and keyframes remain at their original source positions. A later return
animation can therefore remain present but constant after an earlier zoom is
removed. When the final frame of a plain parameter is removed, native saves
retain the initial value as static geometry. Ordinary default values are omitted;
zero crop values remain explicit. The command retains extra parameter metadata
instead of flattening it with the removed frames.

An eighteen-block, 187-second native sequence compares each original with its
JSON-authored removal. Independent fresh-process exports reproduce all decoded
video/audio, and the saved project is byte-identical after reopening. Fifty-four
native frames show the removed zooms, preserved earlier/later animation, initial
geometry and recorded cursor. Eighteen stereo audio windows retain measured
level/frequency, and positive native file handles identify both copied bundle
sources. Evidence is `animation-removal-native-checks.json` in the repository's
excluded verification tree. A missing interval with orphaned frames, ambiguous
timing, geometry point frames or unknown/effect-owned coupling requires another
native case; it is not silently cleared.

## Ordinary geometry point limits

Mac 2026.2.4 format-10 standalone `VMFile` translation controls distinguish
zero-duration double keyframes from Motion Path's `type: "point"` parameter.
Four native controls establish these ordinary `translation0/1` results:

| Supplied curve | Native saved result and output |
| --- | --- |
| One zero-duration point at one second, values 128/72 | Bare static translations 128/72 throughout the clip, including before one second. |
| Points at one and three seconds, ending at −128/−72 | Bare static translations −128/−72 throughout; the point times do not create timed jumps. |
| The same two points plus a one–three-second visual interval | The same static translations. Native loading additionally rebuilds constant scale curves; reopening rebuilds constant translation curves over the marker. |
| A point at one second followed by a positive two–three-second interval | The point becomes the initial 128/72 value; only the positive interval remains, targeting −128/−72. Its motion occurs at two–three seconds. |

The four-block native sequence has two independent 32-second exports with
identical decoded video/audio. Sixteen inspected frames verify static bounds
before/after point times and the mixed interval's actual midpoint. Four stereo
windows retain 440 Hz. Whole-document comparisons model only those observed
curve repairs and thumbnail cache. A third fresh-process save is byte-identical
to the reconstructed second save. The existing schema/profile accepts both
supplied and saved shapes, so conformance does not establish timed movement.

The project validator reports these observed translation-point shapes as
warnings; see `project.py` — `native_geometry_warnings`. It does not rewrite or
reject the document. Interval mutation continues to refuse point-shaped geometry
instead of guessing a timed-step or spline conversion. Use positive-duration
intervals for timed geometry. Other properties, clip owners, point positions,
interpolations and curve arrangements require separate native cases; this does
not limit recorded cursor points or `MediaPath` points.

## Empty Custom intervals

`set-interval` also accepts an empty `values` object. Four native Custom captures
verify interval-only authoring on an image, Callout, Group and retimed Group.
Parameters and source data remain unchanged in those immediate native saves.
No scale, position or opacity target is inferred. Explicit easing selects the
intended saved value; `ease-interval` continues to refuse an absent marker.

Loading the image's empty marker in a fresh editor process reconstructs constant
`scale0`/`scale1` curves from its static 3.125 scale. Their defaults and targets
remain 3.125, and the marker supplies their bounds/easing. The native saved
document is then byte-stable on the independent reopen. Rendered samples retain
the same image size. This specific reconstruction is recorded separately from
the helper's faithful immediate-Custom result. Orphaned coupled frames require
repair before adding an empty marker.

## Parameter and interval ownership

Twelve additional native operations establish adding, changing easing and
removing scale intervals on `IMFile`, `Callout`, `Group` and a Group at 2× speed.
These owners store `parameters` and `animationTracks.visual` directly. Group
children, source-bin data and the separate background audio remain unchanged.
The image retains `mediaDuration: 1` independently of its eight-second hold;
animation frames still use the project tick clock. Its initial scale 3.125
returns after removing the interval instead of being replaced by unit scale.

The retimed Group starts at timeline one second with `scalar: "1/2"` and zero
source in-point. A timeline three–four-second interval uses source bounds
`2822400000`–`4233600000`. Descendant clocks are unchanged. These observations
cover the exercised Group parent transform; arbitrary nested transforms and
nonzero-in-point Group stability retain their own verification requirements.

The helper reproduces each complete native operation outside fixed UI command
increments and thumbnail caches. Native Custom inherits the editor's last
selected easing in these captures. Supply the intended easing explicitly when
authoring; an earlier menu choice is not evidence of a new interval's value.

A 24-block, 192-second native sequence compares each native result with its
JSON-authored result. Independent fresh-process exports match complete decoded
video/audio, and reopening preserves the saved JSON bytes. The first save
renumbers all object IDs in traversal order; strict comparison accounts for
that exact allocation and the thumbnail. Seventy-two inspected frames show
initial, moving and final geometry, with measured paired picture differences
bounded separately from codec noise. Twenty-four stereo windows retain the
synthetic 440 Hz tone. Source hashes, a positive bundled AV handle in each
export session and the visible image establish the exercised dependencies.
Evidence is `animation-owners-native-checks.json`; installed consumers execute
all twelve operations in each agent layout. No vendor assets are distributed.

For linked `UnifiedMedia`, these native saves store geometry in `video.parameters`
and intervals in `video.animationTracks.visual`. The wrapper has neither object.
Do not invent wrapper copies or assume every clip exposes `parameters` directly.
The recorded SmartFocus specimens instead use a direct `ScreenVMFile` owner.
Keep the audio child, source bindings, and native container representation.

An ordinary one-second animation ending at four seconds saves an interval with
`endTime: 2822400000` and `duration: 705600000`. Affected typed parameters carry
their initial `defaultValue` and keyframes with `time`, `endTime`, `duration`,
and target `value`. Keep the interval marker and all coupled parameter curves.

| Preset | Demonstrated native change |
| --- | --- |
| Custom | Native Custom plus a scale edit creates `scale0`/`scale1` curves from 1 to 1.5. |
| Restore | A prior Scale Up remains at one–two seconds; Restore adds a three–four-second return from 1.25 to 1. |
| No Opacity | `opacity` goes from 1 to 0. The final picture is black on this opaque black canvas. |
| Full Opacity | With initial native opacity zero, `opacity` goes from 0 to 1. |
| Tilt Left | `translation0` targets −160, `rotation1` targets +0.523598775598299 radians, and both scales target 0.5 on the 640×360 fixture. |
| Tilt Right | Opposite translation/rotation signs with the same half scale. |
| Scale Up | Both scales go from 1 to 1.25. |
| Scale Down | Both scales go from 1 to 0.75. |
| Scale To Fit | Native initial scale 2 returns to 1 for this matching 640×360 source/canvas. |
| Motion Path | A separate `MediaPath` effect, described below. |
| SmartFocus | Recorded-data analysis creates coupled automatic zoom intervals, described below. |
| SmartFocus at Time | Creates the selected-time recorded-data zoom interval. |

Rotation parameters are radians. `rotation1` corresponds to the displayed Y
rotation in these Tilt specimens; do not replace it with Z rotation. Inspect
intermediate frames as well as endpoints. A valid final opacity or scale can
still hide an incorrect initial state or motion curve.

## Additional rotation and depth

Native Visual Properties maps X rotation to `rotation0`, Y to `rotation1`, Z to
`rotation2`, and Z position to `translation2`. Rotation targets are radians;
depth retains the entered canvas-space value. A native one–two-second Custom
interval followed by X=40°, Z=30° and depth=200 edits saves ordinary typed
double curves with zero defaults, source-position bounds, and respective targets
`0.698131700797732`, `0.523598775598299` and `200.0`. The interval marker is
shared. Existing constant half-scale curves retain their own defaults/targets.

Native None easing adds `linr` to the marker and all five matching geometry
frames, including the constant scales. Remove Animation removes the three
zero-default axes, collapses scales to bare 0.5 and removes the marker. Nonzero
initial axes, extra parameter metadata and other intervals follow the helper's
existing preservation contract; they are covered by fixed core tests.

Five whole-native replays verify the three edits, easing and removal. A ten-block,
80-second sequence pairs each native result with its JSON-authored equivalent.
Both independent fresh-process exports match every decoded video/audio sample.
Thirty inspected frames show X tilt, combined Z rotation, positive depth,
linear motion and restored initial geometry. Paired mean channel error is at
most 0.568, including codec noise. Ten stereo windows retain 440 Hz; the bundled
source hash remains unchanged. Reopening preserves every field except the PNG
thumbnail cache; it is not a byte-identical document claim. First-save comparison
additionally models sequential object IDs. Existing schema/profile checks pass
without changes. Each installed agent layout executes all five operations.

## Easing and Auto Animate

The animation arrow's native context menu exposes these choices:

| Native choice | Saved `interp` |
| --- | --- |
| None | `"linr"` |
| Exponential In/Out | `"eioe"` |
| Bounce | `"bnce"` |
| Spring | `"sprg"` |
| Auto | Omitted in this Scale Up interval and its keyframes. |

Explicit easing appears on both `animationTracks.visual` intervals and the
affected scale keyframes in these specimens. SmartFocus uses parameter-level
`interp` instead. Preserve the observed owner; a single global easing field
does not represent every native operation. Auto's decoded output matches the
unedited default Scale Up. Mid-interval sampled frames distinguish the other
choices; endpoint equality alone does not verify easing.

With Auto Animate enabled at four seconds, typing scale 150% creates the same
three–four-second curves and decoded video/audio as Custom followed by the
equivalent edit. Auto Animate is an editor interaction mode; the saved result
uses ordinary parameter curves. Restore Edit mode after the operation to avoid
adding animations during subsequent canvas edits.

## Source-position clocks and short clips

Animation keyframes and interval markers can use source positions expressed in
the **project tick rate**, independently of the source stream's sample rate.
The retimed native fixture starts at timeline one second, uses source one–seven
seconds, lasts four timeline seconds, and saves `scalar: "2/3"` for 150% speed.
Its animation at timeline three–four seconds saves source-position bounds
`2822400000`–`3880800000` and duration `1058400000` on the 705600000-tick clock.
The linked source stream has rate 48000; those animation integers are not audio
samples. Preserve all three domains: timeline placement, source position, and
the units used to express that position. See [clock domains](project-format.md#clock-domains).

The half-second, fifteen-frame specimen receives Scale Up ending at frame seven.
Native Camtasia retains a full one-second animation: `time: -540960000`,
`endTime: 164640000`, `duration: 705600000`. Its visible first frame is already
partway through the zoom. Independent reopening reproduces all fifteen frames.
Do not clamp negative keyframe starts or force animation duration within the
visible clip. These are native animation bounds, separate from parent placement.

## Motion Path

Motion Path saves `effectName: "MediaPath"`, `categoryVisualEffects`, and
`metadata.effectIndex: "0"`, mirrored in the linked wrapper and video child.
The exact-build profile admits this identifier. `parameters.mediaLocation` is
a typed point curve; the demonstrated points are `[0,0,0]` at one second and
`[256,144,0]` at two seconds. Its zero-duration point keyframes retain a nested
`interp.bezier` array containing two control points and `"eioe"`. Preserve this
structure separately from ordinary scale animation easing. The native default
`mediaPathAutoOrient` is the bare integer zero. The specimen has no visual
animation marker.

Sixteen additional exact-build feature cases have independent first/reopened
exports, strict whole-project/source preservation checks, and inspected frames:
four interpolation codes, auto-orient, four endpoint line controls, insertion,
four middle-point line controls, deletion, and extension. Four earlier popup
selection attempts also have native pairs, retained as menu diagnostics.

The second point's nested Bézier array accepts the demonstrated timing codes
`"eioe"`, `"esIn"`, `"esOt"`, and `"linr"`. Preserve capitalization, including
`esOt`. All four produce different complete decoded videos with identical audio
on the same curved path. Early intermediate frames distinguish slower `esIn`
movement from farther-advanced `esOt`; `eioe` differs from `linr` before and after
the midpoint. Endpoints alone do not establish timing behavior or an exact
mathematical easing formula. The exercised popup selections sometimes disagree
with displayed labels and saved codes; verify the actual saved payload and output
instead of treating a menu click as proof of the requested timing.

Auto Orient saves `mediaPathAutoOrient: 1` in both effect copies, wrapper metadata
`"default-MediaPath-mediaPathAutoOrient": "0"`, and bare
`video.parameters.rotation2: 0.0`. Its output visibly rotates with the curved
path and returns axis-aligned at the horizontal ending tangent. Keep these native
companions; do not invent a rotation keyframe curve or visual animation marker.

The four line-type buttons are unlabeled in accessibility output. Their actual
effects depend on the selected point. At the original two-point path's endpoint,
buttons 1 and 2 replace the nested Bézier object with the string `"eioe"` and
render identically. Button 3 retains the original curve; button 4 changes the
incoming handle. Straight spatial segments can therefore retain eased timing.

At the inserted middle point, the native results are:

| Button, left to right | Incoming segment | Outgoing segment |
| --- | --- | --- |
| 1 | String `"linr"` | String `"linr"` |
| 2 | String `"linr"` | Original Bézier object |
| 3 | Original Bézier object | String `"linr"` |
| 4 | Bézier with adjusted adjacent handle and explicit `"linr"` | Bézier with adjusted adjacent handle and explicit `"linr"` |

Segment interpolation belongs to the destination point. Editing a middle point
can therefore change both its keyframe and the next keyframe. Preserve the other
handles, clocks, values, and both wrapper/video copies; there is no demonstrated
standalone line-type enum in the JSON.

Native **Add Motion Path Point** from the curve's context menu splits a segment
and rewrites its controls. This insertion saves three zero-duration points,
including a subframe middle time `1059996337` on the project tick clock, with
fractional coordinates. Both resulting `interp.bezier` arrays have two control
points and omit the third timing-code element. Preserve this optional shape;
do not insert a guessed default code or round the new point to a video frame.
The inserted specimen's movement differs from the original eased segment.

**Delete Motion Path Point** removes the middle point and joins the retained
outer handles. It does not restore the original curve or its explicit easing.
**Extend Motion Path to Here** appears with the playhead after the final point.
At three seconds in this specimen, it preserves the existing points and appends
two more: a hold at the old position one frame after the previous endpoint, then
the selected destination at three seconds with a new Bézier segment and `"eioe"`.
The saved result remains one mirrored `MediaPath` effect. Use native specimens
for new path geometry rather than deriving a general spline constructor from
these fixture coordinates. See TechSmith's [Mac motion-path introduction](https://support.techsmith.com/hc/en-us/articles/37778948514829-Camtasia-Mac-2023-Version-History)
for the editor feature; the JSON contracts above come from exact-build native tests.

## Motion Path JSON editing

The [point-curve helper](helper.md#motion-path-json-editing) creates and edits
the verified visual owner's Motion Path through explicit points and interpolation.
Nineteen complete native replays cover construction, all literal timing forms,
endpoint/middle handles, native insertion/deletion/extension results, Auto Orient
on/off and a trimmed/retimed constructor. The array defines every retained
point; omitted points are removed. It does not derive a spline split from an
insertion index or a native button number.

Native Mac 2026.2.4 format-10 captures also establish direct `VMFile`, `IMFile`,
`Callout`, `Group` and `ScreenVMFile` constructors. A direct owner stores one
effect without linked `effectIndex` metadata. A linked `UnifiedMedia`/`VMFile`
stores matching wrapper/video effects with the same stable token. Group children
and recording cursor curves remain unchanged. A Group at 2× speed converts
clip-relative one–two-second points to source positions two–four seconds;
its child clocks, four-second duration and Clip Speed effect stay intact.

The earlier non-oriented bypass/re-enable controls change only the selected
effect's `bypassed` flag; oriented frozen/stitched coupling is recorded below.
Delete Effect removes `MediaPath` and its Auto Orient rotation companion while
retaining `effectApplied` and reset metadata. Other effects retain their order
and tokens; deletion does not renumber them. With multiple effects visible,
select the menu attached to the Motion Path header; the first generic Effect
menu may belong to Clip Speed.

The 150%-speed native control starts at timeline one second, uses source one–seven
seconds and `scalar: "2/3"`. Adding Motion Path at timeline four seconds creates
source-position points at `3880800000` and `4939200000` project ticks. These are
clip-relative timeline three–four seconds and source positions 5.5–7 seconds.
The final point lies at the clip's ending boundary. This native capture verifies
the conversion independently of ordinary animation intervals.

Auto Orient on adds the previously recorded wrapper reset metadata and bare
zero `video.parameters.rotation2`. Native off removes that zero parameter while
retaining the reset metadata. The helper preserves other transforms and refuses
an unfamiliar nonzero/animated rotation instead of clearing it implicitly.
For a direct `ScreenVMFile`, the native zero companion is instead
`{"type":"double","defaultValue":0.0,"interp":"eioe"}`. The recorded cursor
parameters retain their independent typed representations.

A one-point path is valid and holds its supplied position before and after its
point time. The linked half-size video control at `[128,72,0]` has foreground
bounds `[288,18,608,198]` on a 640×360 canvas at 0.5, 1.5 and 2.5 seconds.
Its first native save adds bare zero `translation0/1` to video parameters;
this observed initialization does not alter the path point.

Thirty-five native creation/bypass/enable/orient/removal captures plus the
single-point save replay against the helper. Their 36-block, 288-second sequence
has two independent fresh-process exports with matching complete decoded AV and
byte-identical reopened JSON. First-save comparison admits only sequential IDs,
thumbnail cache and the singleton's two zero translations. All 108 samples show
the expected motion, rotation and static bypass/removal results; 36 stereo tone
windows and all three source hashes remain intact. The installed Codex, Claude
Code and Cursor copies execute each of the 36 cases. Completed working movies,
projects and audit records are discarded after incorporating these findings.

A 23-block, 184-second native sequence includes these nineteen point cases and
the four empty Custom markers. Both independent fresh-process exports reproduce
complete decoded video/audio, and the first saved JSON reopens byte-identically.
Strict first-save comparison admits only sequential object IDs, the observed
constant image-scale companions and thumbnail cache. The native schema/profile
passes without an added correction; raw community errors remain separate.
The render audit checks independent native reference pictures, static marker
geometry, visible retimed motion and retained source audio. The installed
consumer check executed every case from each of the three agent layouts.

## Frozen and stitched Motion Paths

Mac 2026.2.4/format 10 stores a direct `MediaPath` effect on frozen `ScreenIMFile`
and `StitchedMedia` parents without a linked token. Five native owner/speed cases
cover ordinary, 2× and 0.5× frozen recordings plus ordinary and 2× stitched
parents. Stitched children, their cursor fields, source selection and virtual
hold duration remain unchanged.

Frozen point times start at local zero independently of `mediaStart`, using the
inverse-speed conversion owned by `point_frames`. With a held source frame at
four seconds and the native playhead at local two seconds, Motion Path creates
two–three-second points: `1411200000`/`2116800000` at normal speed,
`2822400000`/`4233600000` at 2×, and `705600000`/`1058400000` at 0.5×.
Stitched parents retain the source-position clock; the tested zero-origin
normal/fast parents use the corresponding normal/fast point integers. These
path points begin at the playhead, unlike the tested Custom interval that ends
at the playhead. Supply intended point times explicitly.

Auto Orient on these owners adds bare `rotation2: 0.0` and reset metadata.
Bypassing an oriented path removes that zero companion; re-enabling restores
it. Turning orientation off removes it, including when already bypassed.
Turning orientation on while bypassed keeps it absent until the effect is
enabled. Native fresh loading also retains that absence. The corresponding
[other-owner checks](#oriented-path-bypass) establish the same lifecycle for
the remaining verified visual families. Unfamiliar rotation state still refuses mutation.
Delete Effect removes the path/companion and keeps reset metadata.

Thirty-five native lifecycle captures and ten orientation edits made while
bypassed match complete helper candidates outside exact one-command increments
and thumbnail caches. All forty-five native/helper pairs render in a ninety-block,
774-second composition. Independent fresh-process exports repeat all 23,220
decoded RGB frames and stereo PCM audio; reopening is byte-identical. The first
save changes only the thumbnail. All 450 inspected pictures show the expected
motion, rotation, static bypass/removal and preserved moving-to-held joins.
Equivalent native lifecycle controls also match within measured codec noise.
Ninety stereo windows retain 440 Hz and all three bundled source hashes survive.
The raw community schema omits the eighty `MediaPath` identifiers in each runtime
document; the existing exact-build profile accepts them without a new correction.

## Oriented-path bypass

Native controls on linked video, standalone video, images, Groups, Callouts
and moving screen recordings confirm the companion lifecycle across the
remaining verified owners. Bypass removes the selected visual's zero-rotation
companion while retaining Auto Orient on the effect. Re-enable restores a bare
zero, except `ScreenVMFile`, which restores the typed `RECORDING_ROTATION`
representation owned by the helper. Linked wrapper/video effect flags change
together; rotation belongs only to the video child. Audio, effect tokens,
other transforms and Group children remain unchanged.

Turning orientation off or back on while bypassed keeps the zero companion
absent. Enabling the effect restores it. The earlier helper changed only the
bypass flag for these families; both `set_bypass` and `set_path` now match this
native coupling. Unknown orientation or nonzero/animated rotation still requires
native investigation and refuses mutation.

Thirty-six complete native operation comparisons cover bypass, enable, repeated
bypass, orientation edits while bypassed and final enable. The two first bypass
saves on Group/Callout also add `metadata.lockAspectRatio` as a typed true bool.
Those exact observed additions are admitted separately from command count and
thumbnail; no general metadata-ignore rule is used. Selecting their panels and
saving without an edit did not persist that flag. The helper retains unrelated
metadata rather than synthesizing this incidental default.

The native/helper comparison renders 72 eight-second blocks. Both independent
576-second exports have identical complete decoded picture and audio streams;
360 inspected samples match each operation and show visible motion only when
enabled. All 72 stereo tone windows retain source audio. First save changes only
the thumbnail and fresh-process reopening is byte-stable. The existing build
profile accepts the documents; raw upstream validation still reports its known
`MediaPath` enum omission. Each of the three installed agent layouts also
executes all 36 operations against these native controls.

## SmartFocus

SmartFocus is enabled for the demonstrated recorded `ScreenVMFile`, disabled
for the ordinary MP4. A forty-second real TREC segment with cursor/click data
produces two automatic zoom intervals. Translation, scale, and four
`geometryCrop*` parameters have typed curves with parameter-level `"eioe"`.
Automatic interval ends include subframe integers `7729024785` and
`22179712785`; do not snap them to frames. The zoomed view visibly follows the
synthetic click targets. The final native crop retains two-pixel top/bottom
values, so returning scale/position does not prove pixel equality to control.

SmartFocus at Time at four seconds creates one three–four-second translation
and scale interval in the same recording, without added crop curves in that
specimen. Do not synthesize its result from the automatic-analysis payload or
claim source-independent subject detection. Recorded source metadata remains
part of the feature's dependency closure; see [recorded media](media.md).

## Crop and corner pin

Dragging the native crop handles saves bare `geometryCrop0: 100.392156862745`
and `geometryCrop1: 50.1960784313725` for left and top crops on this fixture.
Scale and translation stay unchanged. The rendered picture retains black canvas
in the removed strips; the source is not rescaled to fill them. Do not round
fractional source crop values to screenshot coordinates or confuse a canvas
crop with cutting pixels out of the source file.

Moving the top-left native corner inward saves a coupled geometric transform:
`translation0/1`, `rotation0/1/2`, `shear0/1/2`, and unequal `scale0/1`.
It does not add a four-point effect or animation interval. The native output
shows perspective with the other three corners retained. Preserve the complete
transform, including tiny shear components; changing only the displayed skew
or scale cannot reproduce the native corner-pin result. Restore Edit mode and
check all corners in the exported picture.
