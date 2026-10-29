# Cursor effects and click editing

These contracts were exercised in Camtasia Mac 2026.2.4, format 10.0, on a
real `ScreenVMFile` with recorded pointer samples. A generated cursor path is
a separate input workflow; see [features](features.md). Retain the recording
stream selection and pointer metadata described in [media](media.md).

## Native identifiers and controls

All twelve presets below saved `categoryCursorEffects`, `bypassed: false`,
and bare parameter values. Preserve casing, hyphens, booleans, and companion
fields. Do not infer serialization from the palette label or another preset.
Values listed here are observed preset defaults, not bounds or universal units.

| Native label | Serialized `effectName` | Observed controls |
| --- | --- | --- |
| Cursor Color | `CursorColor` | `intensity: 1`, `desaturation: 0`; split `color-*`/`secondColor-*` RGBA fields, luma cutoffs, channel and shadow/highlight ramp endpoints. Default dark-tone replacement is yellow. |
| Cursor Glow | `CursorGlow` | `showCursor: true`, green split `color-*`, `intensity: 1`, `thickness: 1`, `pulse: false`, `speed: 0.5`. |
| Cursor Highlight | `CursorHilight` | Preserve the native `Hilight` spelling; `radius: 50`, yellow `color-*`, `color-alpha: 0.75`, `blur: 0.1`. |
| Cursor Magnify | `CursorMagnify` | `radius: 100`, `zoom-level: 150`, `softness: 0`, `border-width: 2`, black `border-color-*`. |
| Cursor Motion Blur | `CursorMotionBlur` | `intensity: 1`. Check moving frames; a stationary pointer is insufficient. |
| Cursor Shadow | `CursorShadow` | `angle: 3.92699081698724` for displayed 225°, `enabled: 1`, `offset: 7`, `blur: 10`, `opacity: 0.5`, black `color-*`. |
| Cursor Spotlight | `CursorSpotlight` | `radius: 100`, `blur: 0.35`, `blur-sigma: 0`, `background-saturation: 1`, `background-opacity: 0.3`, black `color-*` with alpha 0.3. |
| Kinetic Cursor | `CursorPhysics` | `intensity: 1.5`, `tilt: 2.5`. Check movement-dependent deformation, separately from smoothing. |
| Cursor Isolation | `Cursor Isolation` | Spaced identifier; `Opacity: 0`. The exercised MP4 shows the pointer against black after removing the screen image. The separately verified WebM alpha path is described in [delivery](delivery.md). |
| Gradient | `Gradient` | Split `Color0-*`/`Color1-*` RGBA fields; `Opacity: 0.5`, `Radius: 100`, `Feather: 1`, `Angle: 0`, `CircularGradient: false`. |
| Lens | `Lens` | `Radius: 150`, `Power: 2.5`, `Magnification: 1.5`. Distinct from Cursor Magnify. |
| Negative | `Negative` | `Radius: 100`, `Feather: 1`, `Red: true`, `Green: true`, `Blue: true`. |

Cursor Smoothing has a separate native movement/bypass comparison and parameter
contract in [Mac versions](mac-versions.md). Cursor Path Creator is covered by
the generated-path specimen in [features](features.md).

## Source scale, bounds, and persistence

The comparison uses an eight-second trim of a real screen recording at native
16.7% media scale, on a 640×360 project. Cursor scale is deliberately 500%. The retained microphone track is muted
in this fixture; matching audio verifies retained muting, not speech quality.
Source-space radii can occupy a small region after media scaling; a UI radius
of 100 is not proof of a 100-pixel circle in the output movie. Preserve media
transforms separately from cursor scale and effect controls.

The demonstrated defaults have zero UI ease-in/ease-out. Inspect the desired
entry/exit and any edited easing separately. Keep effects scoped to their
native owner; do not flatten recording cursor metadata into the source pixels.
Recorded click, keystroke, and active-window processing require their own event
data. Pointer movement alone does not establish those event families. Manual
click insertion has the separate contracts below.

All twelve native preset projects and the clean control were independently
loaded from saved bundles by native Batch Export. The thirteen fresh movies
are each decoded-identical in video and audio to their first native exports.
The Color specimen also independently reopened in the editor with its native
controls retained. Sampled stationary/movement frames show the intended color,
glow, highlight, local shader, isolation, spotlight, and motion behavior.
Keep independent rendering and UI inspection distinct in reports.

For native multi-project export, read [delivery](delivery.md).

## Recorded keystrokes and active windows

These effects use `categoryScreenRecordingEffects` on the recorded
`ScreenVMFile`. They require the corresponding recording metadata, separately
from pointer coordinates. A rasterized MP4 or reimported WebM does not recover
the original editable keyboard/window events.

Native **Keystroke** saves `effectName: "Keystroke"` and bare parameters:
`keystroke-style: "clear"`, `keystroke-duration: 705600000`,
`keystroke-drawBackground: 1`, `keystroke-showKeyHint: 0`,
`keystroke-preClick: 0`, `mask-height: 64`, `mask-positionX: 0`,
`mask-positionY: -140`, and white split `text-color-*` channels.
The duration is in project ticks; the demonstrated UI value is one second.
The total visible interval also includes native fades. Do not equate the
duration control with the first/last visible output pixel.

The recorded Command-Tab combination visibly renders in the exercised trim.
The second specimen uses `keystroke-style: "traditional"`, duration two
seconds, `keystroke-preClick: 1`, `keystroke-drawBackground: 0`,
`keystroke-showKeyHint: 1`, and black text channels. It visibly starts earlier
and displays named modifier keycaps. Preserve the selected style's companion
values. Gray, Outline, and Black also have native saved/rendered/reopened
specimens. They save `"gray"`, `"outline"`, and `"black"` respectively, with
one-second duration, background on, before-keypress off, and modifier names
off. Gray selects black text channels; Outline and Black select white. The
inspected output shows gray keycaps, white outlined keycaps, and black keycaps.
This event effect is separate from the
MacKey annotation assets. TechSmith's [Mac Keystroke documentation](https://www.techsmith.com/blog/wp-content/uploads/2025/02/Camtasia-2024-Help-EN.pdf)
describes recorded modifier combinations, not unrestricted typed-text capture.

Native **Window Spotlight** saves `effectName: "FrontMostWindowHighlight"`,
with `zoomUp: 1`, `blur: 0`, `feather: 0`, and `opacity: 0.2`. The tested
controls display 100% zoom, zero blur, and 20% background visibility. Its
region follows the recorded foreground window geometry. A window partly
outside the recorded screen can yield only a strip of highlight; do not
replace those recorded coordinates with the current desktop window bounds.

All five Keystroke styles and Window Spotlight independently reopen with their
controls retained. All six fresh native rerenders match their first exports
in decoded video and audio. The tested recording has a muted microphone track.

The attempted Left Click Rings interval saved its native effect but rendered
identically to the clean control. That interval supplies no positive click
processing evidence. Do not infer click events from pointer movement, keyboard
events, or successful effect serialization.

A separate single-window capture of a local synthetic browser page recorded
visible counters for two left and two right clicks made through computer use.
Native Rings at radius 200 still rendered identically to its clean control.
Check actual native click processing before accepting an automation-generated
recording as a click fixture. This result does not establish that Camtasia
cannot record physical clicks or that a different input method will behave alike.

## Native left and right click presets

A subsequent capture made with the authorized guarded native mouse helper
supplies positive recorded clicks. Its matched sixteen-second control and all
24 native left/right presets were saved and rendered. Independent native Batch
Export reloads those projects, three recorded-click edit variants, and a laptop
sound variant: all 29 decoded video/audio pairs match their first exports.
The original TREC remains unchanged. This positive result does not retroactively
turn the earlier computer-use capture into click-bearing input.

All presets save `categoryClickEffects` and `bypassed: false`. Identifiers are
`LeftClick` or `RightClick` followed by the suffix below. Preserve bare values,
case-sensitive fields, split color channels, and any native metadata.

| Suffix | Native parameter specimen |
| --- | --- |
| `Rings` | `clickDuration: 1.25`, `postClickPercent: 100`, `radius: 50`, `scale: 0.5`, split lowercase `color-*` RGBA. The positive left specimen edits radius to 200; the right specimen retains 50. |
| `Ripple` | `clickDuration: 1.25`, `postClickPercent: 100`, `radius: 100`, `scale: 0.5`. |
| `Scaling` | `scale: 3.5`, `speed: 7.5`; no duration field in this specimen. |
| `Scope` | `clickDuration: 1.25`, `postClickPercent: 100`, `radius: 75`, `scale: 0.5`, split lowercase `color-*`. |
| `Target` | `clickDuration: 1.25`, `postClickPercent: 100`, `radius: 10`, `scale: 3`, split lowercase `color-*`. |
| `Warp` | `clickDuration: 1.25`, `postClickPercent: 100`, `radius: 75`, `scale: 0.5`. |
| `Burst1` | `clickDuration: 1.25`, `postClickPercent: 100`, `Scale: 1`, `Count: 6`, `Thickness: 3`, split uppercase `Color-*`. |
| `Burst2` | `clickDuration: 0.5`, `postClickPercent: 100`, `Scale: 2`, `Length: 5`, `Count: 6`, `Thickness: 3`, split `Color-*`. |
| `Burst3` | `clickDuration: 0.6`, `postClickPercent: 100`, `Scale: 2`, `Count: 6`, `Thickness: 3`, split `Color-*`. |
| `Burst4` | `clickDuration: 0.6`, `postClickPercent: 100`, `InnerRadius: 10`, `OuterRadius: 120`, `Count: 12`, `Thickness: 0.5`, split `Color-*`. |
| `Zoom` | `clickDuration: 0.6`, `postClickPercent: 100`, `Scale: 1`, `Radius: 200`, `Thickness: 2`, black split `Color-*`. |
| `Sound` | `filename: "mouse_click_single.wav"`, `volume: 1`. Native Laptop Click selects `"laptop_click_single.wav"`; committed 50% volume saves `0.5`. |

These are observed values, not parameter bounds. Duration controls above display
seconds, separately from the tick clocks of click events. Rings/Scope default
to red on the left and yellow on the right; Target uses green/yellow; Burst
presets use red/blue. Ripple and Warp visibly distort nearby pixels; Scaling
changes the pointer size. Inspect moving event frames, not a late stationary
sample. Source radii are reduced by media scaling.

For the exercised Right Click Target, native **Show effect before click** saves
`postClickPercent: 25`, retaining duration 1.25. Independent editor reopen
retains the checked control and reproduces identical decoded video/audio.
The measured changed-frame interval moves from approximately 10.97–12.17 seconds
to 10.07–11.23 seconds in that 30 fps specimen. These pixel observations include
sampling/visibility thresholds; do not equate them with exact duration bounds or
assume the checkbox saves zero post-click time.

The sound specimens keep the clean control's silent source and add audio only
at the corresponding recorded left/right event. Laptop Click at committed 50%
has half the RMS amplitude of its 100% baseline, before rounding from AAC.
The sound names are native logical resources, not evidence of missing files
beside the project. An accessibility text-field value can differ from saved
state; commit the native edit and verify JSON plus rendered audio.

## Inserting and removing clicks

Use the intended click-effect panel's **Add cursor click at playhead** control.
Multiple panels expose identically named controls. Select the effect explicitly
before adding a left or right event. **View next cursor click** navigates actual
events; it does not establish an event's meaning from pointer coordinates.

On `ScreenVMFile`, native insertion saves `parameters.cursorAction.edits` entries
with `time` and `value`. The exercised values are `1` for left and `4` for right;
do not infer other enum values or operating-system button mappings. A trim at
source 128 seconds saves `time: 90316800000` when insertion occurs at timeline
zero on the 705600000-tick clock. These event times use the recording's source
clock. Preserve existing edits/deletions when changing another event.

Removing the exercised inserted left click saves `edits: []` and
`deletions: [0]`. Its native movie reproduces the pre-insertion video exactly.
Native Undo restores the original parameter/effect objects. This is an override
of recorded metadata; do not rewrite the original TREC.

On ordinary linked video, apply **Cursor Path Creator** first. Native cursor
effects/click menus were disabled before that step. The generated `CursorPath`
effect owns `parameters.cursorAction`, a typed `int` with `uiHints` and
`keyframes`; it is not the recording's `edits` object. The initial keyframe has
`time: 0`, `endTime: 0`, `duration: 0`, `value: 0`. A click at timeline one second
adds a zero-duration keyframe at `705600000`, value `1` or `4`. The exercised
generated clip begins at source zero with scalar one; retimed clips need their
own clock mapping before editing this parameter.

Native Remove deletes the generated click at one second and retains the initial
zero-valued keyframe. For the time-zero click, the exercised Remove control leaves
value `1` unchanged; native Undo restores `0`. Do not report that initial click
removed without inspecting the saved value and output. Preserve the path's
location keyframes, image resource, smoothing, opacity, and scale separately.

The generated control, time-zero left click, one-second left/right clicks,
one-second removal, and source-128 recorded insertion independently reload and
rerender through native Batch Export. All six decoded video/audio pairs match
their originals. The generated one-second removal restores control video
exactly; inspected native frames show green/yellow Targets for the inserted
events. Targets remain at the click location as the cursor continues moving.

## Editing and restoring recorded pointer paths

For an actual recording, use Cursor Properties → Edit Cursor Path. The native
dialog offers Simplify Existing Path and Create New Path. Cursor Path Creator
in the effect menu is disabled for the exercised `ScreenVMFile`; use the
recording's path editor instead of forcing the generated-path effect onto it.

Create New Path saved a `parameters.cursorLocation` override with
`ignoreSource: true` and an `edits` array. Each edit has a source-clock `time`
and a three-component `value`. The demonstrated second edit also carries
`interp.bezier`, containing two three-component control points and the native
`"eioe"` token. Preserve that payload rather than translating it into ordinary
position keyframes. The recording trim begins at source 128 seconds; the new
points occur at source 129/130 seconds, displayed at timeline 1/2 seconds.
Their coordinates belong to the source geometry, separately from the media's
16.7% canvas scale.

The new path visibly changes pointer positions and independently reopens with
a decoded-identical native rerender. Restore Original Path exits editing and
removes the `cursorLocation` override. The restored export reproduces the clean
control's decoded video exactly; decoded audio matches across all specimens.
The original TREC stays unchanged. Native point selection exposes curve/angle
controls and easing; the tested point context menu exposes deletion. That menu
does not supply evidence for creating mouse-click events.
