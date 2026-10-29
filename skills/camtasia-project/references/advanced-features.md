# Additional native feature contracts

Native serialization examples identify Camtasia Mac 2026.2.4/format 10.0 where
stated; earlier examples use Mac 2025.0.3/format 9.0. The companion-workflow section separately identifies vendor-documented
entry points and later versions; it does not claim native handoff verification.
Preserve extra fields and distinguish tested representations from other builds.

## Region, color, and movement effects

These presets were applied in the native editor to an eight-second generated
AV clip, saved, independently reopened, and exported. The inspected movies
establish the effects below. Names in the UI differ from serialized identifiers.
The exact-build profile admits the eight identifiers missing upstream; `Mask`
was already present. This does not supply constructors for arbitrary builds.

| UI preset | `effectName` | Observed contract / output |
| --- | --- | --- |
| Blur Region | `BlurRegion` | Rectangle uses `mask-shape: 1`, `sigma` default 15, 120×120 mask, white tint alpha 0.25. The export visibly blurs the center. |
| Color Tint | `Tonal` | Separate light `color-*` and dark `secondColor-*` channels, intensity/desaturation 0.5, plus channel/ramp controls. The export shows the two-tone color treatment. |
| Freeze Region | `FreezeRegion` | `freezeEndFrame: 0`, explicit effect `start` and `duration`, plus mask geometry. The native default lasts 2⅓ seconds, rather than the whole eight-second clip. Center pixels at 0.2/1.8 seconds are identical while the surrounding video changes. |
| Mask | `Mask` | Oval uses `mask-shape: 0`, `mask-invert: 0`, outside `mask-opacity` 0, 120×120 geometry. The native export exposes the center circle with black outside. |
| Mosaic | `Pixelate` | Typed double `intensity` default 0.25; visible full-clip pixelation. This differs from the `TypeWinPixelate` annotation. |
| Motion Path | `MediaPath` | Point parameter `mediaLocation`, with native points at one/two seconds: `[0,0,0]` and `[256,144,0]`; the latter carries a Bézier interpolation object. `mediaPathAutoOrient: 0`. Exported video moves visibly. |
| Outline Edges | `Sketch` | Intensity/desaturation defaults 1; inspected export contains monochrome outlines. This differs from Sketch Motion annotations. |
| Reflection | `Reflection` | Distance default 20, opacity 0.4. At 50% media scale the export visibly reflects the bottom edge into the surrounding canvas. |
| Sepia | `Sepia` | Typed double `intensity` default 1; inspected export shows the brown/yellow treatment. |

The native effects use `categoryVisualEffects`. Numeric animated parameters
remain typed objects with `defaultValue` and interpolation; mask shape/invert
and path orientation are scalar selectors. Preserve the complete native
parameter objects, timing, order, and wrapper/video-child mirrors when cloning.
Do not replace these with bare numbers based on the property panel's display.
For example, the panel's blur amount text and serialized `sigma` use different
display scaling. Preserve the observed negative mask feather value.

The installed editor also exposes Tiling. Its default `Tiling` effect saved
and reopened but rendered black on the generated MP4; that specimen is a failed
rendering test and is not an admitted profile extension. Keystroke and Window
Spotlight offered no **Add to Selected Media** action for that MP4. Test those
with a recording carrying the relevant events rather than manufacturing event
data or treating palette presence as successful feature support.

## Placeholder replacement

Converting ordinary media through the editor creates `PlaceholderMedia` with
`attributes.ident`, `width`, `height`, and `note`, plus timing, parameters,
effects, animation tracks, and metadata. The observed native metadata includes
`placeHolderSubTitle`. A community-generated placeholder lacking useful native
dimensions opened as “Unknown”; saving/exporting it did not prove replacement.

A native 640×360 placeholder at 70% scale was replaced with a twelve-second
video through canvas drag-and-drop and **Replace From Start**. The result was
an eight-second `UnifiedMedia` with new clip IDs and linked video/audio sources.
The video retained scale defaults near 0.7 and rendered at 448×252 inside the
640×360 canvas. Preserve the chosen replacement mode, source selection, crop,
effects, and animation; do not assume IDs or clip type remain unchanged.

## Blur, pixelation, and highlight

These native annotations use `Callout.def.kind`, rather than a rectangle that
imitates the effect. The installed presets and native outputs establish:

| Kind | Observed definition fields |
| --- | --- |
| `TypeWinBlur` | `width`, `height`, `intensity`, `blur-invert`, `shape`, `style` |
| `TypeWinPixelate` | `width`, `height`, `intensity`, `shape`, `style` |
| `TypeWinHighlighter` | `width`, `height`, `fill-invert`, `fillColorRed`, `fillColorGreen`, `fillColorBlue`, `fill-color-opacity`, `shape`, `style` |

The probes rendered a 400×200 region over generated video: visibly blurred
edges, pixel blocks, and a colored highlight, respectively. Verify the requested
region and strength in output; an annotation's existence does not establish
that sensitive details are sufficiently obscured. The exact-build profile adds
the two missing kind identifiers while retaining the remaining constraints.
Preset definitions and generated media are not distributed with the plugin.

All seven Mac 2026.2.4 Blur/Highlight constructors uniquely match installed
definitions. The three `TypeWinHighlighter` presets use green RGB `(0,1,0)` at
opacity 0.25, magenta `(1,0,1)` at 0.75, and yellow `(1,1,0)` at 0.5, with
`fill-invert: 0`. `TypeWinSpotlight` uses intensity 0.5 and darkens the exterior
of its central region. Both `TypeWinBlur` presets use intensity 0.8125:
`blur-invert: 1` softens the exterior, while 0 softens the central region.
`TypeWinPixelate` uses intensity 0.33 and visibly blocks the central region.
All retain native corner radius 6, geometry, and clip scale.

A 35-second native sequence and matched source-only control each independently
reopen and reproduce complete decoded video/audio. Fourteen processed frames
were inspected beside fourteen control frames and amplified differences; source
audio is unchanged by the annotations. Differences outside principal effect
regions can include compression. Definition width/height alone do not establish
rendered mask bounds: native spotlight also retains clip scale near 0.4444444444.
The format-10 profile adds the observed Highlighter, Spotlight and Pixelate kind
names; arbitrary masks, strengths and privacy sufficiency require output checks.

## Standalone keystroke callouts

All six Mac 2026.2.4 standalone presets use `Callout.def.kind: "MacKey"` and
literal `keys: "⌘ A"`; they do not derive from recording keyboard-event data.
Native definitions retain height 64, corner radius 6, `showKeyHint: 0`, and these
style/background/width combinations in observed palette order:

| `keyStyle` | `showKeyBackg` | Native width | Inspected appearance |
| --- | --- | --- | --- |
| 2 | 1 | 128 | Separate beveled light keys |
| 3 | 1 | 127.111111111111 | Separate outlined dark keys |
| 0 | 1 | 90.1111111111111 | Combined dark panel |
| 1 | 1 | 127.111111111111 | Separate flat light keys |
| 0 | 0 | 90.1111111111111 | Bare dark glyphs |
| 4 | 1 | 127.111111111111 | Separate filled dark keys |

Each constructor uniquely matches an installed definition. A 30-second neutral
sequence independently reopens and reproduces decoded video/audio; twelve
inspected early/late frames retain the command glyph, A and native styling.
The format-10 profile adds only the observed `MacKey` identifier. Preserve keys,
background flags and geometry together; arbitrary key text, hint controls and
cross-host glyph/font selection are separate checks.

## Themes

Mac 2026.2.4's native **Default** theme has ID
`e59eeb42-ccf0-4a36-bdf9-e630fdab686d`. The installed resource and initial user
copy were byte-identical `.tsctheme` JSON, version `0.0.1`. This is the theme
definition version, separate from project format 10.0.

The observed definition has `colorSettings`, `fontSettings` and `mediaSettings`,
each with `resources` and `tags`. Color resource names are `accent-1`,
`background-1`, `background-2`, and `foreground-1`. The
`annotationBackgroundColor` tag associates with `accent-1`; that resource holds
`#FF739922`. `font-1` holds `{fontName: "Montserrat"}`. Font tags and media
resources/tags are empty in this particular theme. Preserve names, bindings,
unknown fields and file version; this example is not a complete theme schema.

Applying Default through the selected annotation's property panel changes its
concrete definition values and `metadata.AppliedThemeId`. In the tested text
arrow, fill RGB becomes `(0.450980392156863, 0.6, 0.133333333333333)` and font
RGB becomes `(0.847058823529412, 0.870588235294118, 0.890196078431372)`.
These match the accent and `#FFD8DEE3` foreground resources. Its font name was
already Montserrat and remains unchanged. The custom-theme test below separately
establishes font replacement.
For the tested filled rectangle, only fill RGB and theme ID change; native
stroke fields remain. No theme file enters either media source bin.

Independent native export pairs cover a 70-second callout sequence and a
40-second shape sequence. All 44 edited early/late frames were inspected beside
their baseline frames. The selected annotations change color; the other
thirteen callouts and seven shapes retain their payload and appearance. Both
pairs reproduce complete decoded video/audio, and audio matches the unthemed
controls. Geometry, text, existing font names, timing and source bytes remain.

A separate copy replaces only the selected callout's `AppliedThemeId` with an
unused UUID absent from both theme directories. Native save/reopen preserves
the unknown ID; the property selector shows **Select Theme...**. Both native
70-second exports reproduce the accepted themed project's complete decoded
video and audio. All 28 early/late frames match their themed baseline. Retain
the concrete definition when its theme is unavailable; this result does not
recover the missing theme asset or establish portable font dependencies.

The native Theme Manager exposes Foreground, Background 1/2, Accent 1/2,
Annotation Background selection, two font slots, Logo Browse, and
rename/delete/duplicate/import/export actions. Read-only inspection found
Montserrat in Font 1, an empty Font 2, and no logo; Cancel preserved theme bytes.
An independently created synthetic theme saves five color resources, including
`accent-2`, and binds `annotationBackgroundColor` to that second accent. Its
`font-1` and `font-2` resources hold Arial and Georgia font names. `logo-1` holds
an absolute path to a native-copied image below the user's Themes directory;
the copied image bytes equal the original fixture.

Applying this custom theme to the first Basic text-arrow changes its fill to
Accent 2's `#E05020`: saved RGB is `(0.87843137254902, 0.313725490196078,
0.125490196078431)`. It replaces `font.name` from Montserrat to Arial and sets
`metadata.AppliedThemeId`; white font color, text, size, geometry, other
definition fields, thirteen other callouts and media sources remain unchanged.
The two 70-second exports reproduce complete decoded video/audio after an
independent native save/close/reopen. All 28 early/late frames were inspected
beside the original Basic sequence; the orange fill and changed text face render.

Native theme export creates a `.camtheme` ZIP. This specimen has two members:
the UUID-named `.tsctheme` definition and `COMk/theme-fixture-logo.png`. The sole
definition change is rebasing `logo-1` from its absolute user path to that
package-relative path; all other JSON values and the logo bytes are preserved.
The archive contains font names, with no font files. Preserve referenced assets
and the definition together rather than treating the ZIP as a project JSON file.

A fresh editor imports that package after the original custom definition and
logo have been archived out of the user directory. Import recreates both files
byte-for-byte, restores an absolute logo path under the user's Themes directory,
and leaves preexisting Default bytes unchanged. Native Font controls show Arial
and Georgia; the Logo tab displays the original fixture. Applying the imported
theme to another unthemed Basic sequence and independently reopening/exporting
it reproduces the original custom-theme pair's complete decoded video/audio.
Another 28 early/late frames were inspected. The theme logo is a theme resource;
applying it to this text arrow does not insert an image into the timeline or
`sourceBin`. Physical font-file selection and cross-host font availability remain
separate from this same-host font replacement and package closure.

Theme Manager's imported preview callout is red in the observed screenshot,
while the selected annotation-background resource is orange. Check the applied
timeline definition and exported result when validating that binding.

Native Theme Manager **Save** also rewrites preexisting theme files in the
observed case: Default receives an empty `name[""]` language entry and new JSON
formatting, with all other definition values preserved. Record existing bytes
before lifecycle tests. Restore test-induced normalization only after closing
the editor and checking the exact current and retained hashes; preserve any
other user changes. Archive only identified synthetic assets created by the
test. After native Quit, the verification archives the owned theme/logo and
restores the preexisting Default file byte-for-byte. An unchanged preview does
not prove unchanged theme-file bytes. Rename/delete have the separate native
checks below; duplication requires its own identity/resource evidence.

### Theme rename and delete

Mac 2026.2.4 / format 10 exercises the native gear menu on a backed-up synthetic
theme with five colors, two fonts and one copied PNG logo. Rename changes only
`name["en-US"]`. The UUID, UUID-named `.tsctheme` path, empty-locale name entry,
resource definitions, tags, logo path and version `0.0.1` remain unchanged.
The existing project's selector displays the new name through its retained
`metadata.AppliedThemeId`; its complete saved payload is unchanged.

Rename writes the theme file **before Theme Manager Save**. Closing the manager
with Cancel and opening it again retains the new name; a fresh editor process
also sees it. Do not treat Manager Cancel as rollback for a completed rename.
Keep the original theme bytes when testing lifecycle operations.

Native Delete first prompts with the selected theme's name. Canceling that
confirmation preserves every theme/logo file. Confirming Delete immediately
removes the UUID-named definition **and its single owned logo file** from the
user Themes directory; unrelated Default bytes remain identical. The manager
switches to Default. Manager Cancel afterward leaves those files deleted.
This single-logo fixture does not establish deletion behavior for shared or
duplicated resources; identify dependencies before deleting another theme.

The already themed project retains its complete payload, including the absent
theme's saved ID, both concrete font definitions, colors and Quick Property
bindings. Its selector displays Select Theme. Native save/reopen does not remove
that saved ID or substitute Default styling. Applying the theme again still
requires its definition/resources; the saved ID cannot reconstruct them.

Two independent eight-second native export pairs cover renamed and deleted
states. The deletion pair runs after a full process exit/restart with the theme
and installed logo absent. All four complete decoded video/audio outputs match.
Eight native frames are inspected beside eight independently accepted earlier
theme-application frames; sixteen both-channel audio windows retain the source
tone. Three pictures per state show the upper text/callout; the second callout
is white-on-white in this retained fixture and does not visually prove its font
or text. The late picture shows source video after the five-second Group ends.
Saved typography remains strict separately; physical font-file closure is not asserted.

Raw/community and exact-build schemas pass without additions. Six fixed
definition/inventory tests reject identity, resource, locale and unrelated-file
damage; four archive-plan tests protect recoverable owned assets and preexisting
user files. The renamed theme/logo backup remains outside the user Themes
directory. Final native Quit leaves the original user inventory byte-identical.
Repository evidence is `theme-manager-rename-checks.json`,
`theme-manager-delete-checks.json`, both `theme-manager-*-comparison.json`
reports, native controls/disk captures and `theme_manager_contract.py`.

The native Duplicate dialog initially reuses the selected name, reports that
it already exists and disables OK. This is name-collision evidence only.
Successful duplication, its UUID/logo allocation and later independent edits
remain required cases; do not synthesize those contracts from Rename/Delete.

## Text callout presets

All 41 Mac 2026.2.4 text callouts were individually created through the native
palette: nine Abstract, fourteen Basic, nine Bold, and nine Industrial. Each
constructor uniquely matches an installed definition after the observed default
normalization. Industrial's serialized/resource style is `urban`; retain that
literal rather than substituting the UI label. Palette order does not establish
resource filename order.

The native `Callout.def.kind` is `remix`. Its shape, font, text formatting,
geometry, fill, stroke, and tails form one preset contract. The format-10 profile
adds the demonstrated `speech-bubble`, `speech-bubble2`, `thought-bubble`,
`thought-bubble2`, and `text-arrow` shape identifiers. Preserve other native
definition fields; changing only a shape name does not reconstruct the preset.

Installed six-digit fill/stroke RGB and nested `font.color` become separate
native unit color components. Resource `defaultValue` descriptors become their
native defaults, and booleans may serialize as numeric 0/1. These observations
describe constructor matching, not permission to normalize arbitrary project
objects or discard extra defaults.

Four neutral-gray sequences retain all native callout payload and source audio.
Each independently reopens and reproduces its complete decoded video/audio;
82 inspected frames cover each preset early and late. ABC text, native font
names/formatting, fills, outlines, and tails remain visible. Industrial decorative
bands reach the small canvas edge: preserve geometry and verify fitting for the
requested canvas. Matching saved font names and inspected output on this host
does not identify the physical font file or establish cross-host font closure.

## Arrow and line presets

All 28 Mac 2026.2.4 arrow/line presets were individually created through the
native palette: seven each in Abstract, Basic, Bold, and Industrial. Each saved
constructor uniquely matches its installed definition. Industrial serializes as
`urban`; palette order does not identify the resource filename.

These are `Callout` clips with `def.kind: "remix"` and `def.shape: "arrow"`.
Preserve the native `shape-anchor`, `shape-tail`, `stroke-style`, `stroke-width`,
stroke RGB/opacity components, and geometry together. A plain line intentionally
has different endpoint styles from a single or double arrow. Dotted and dashed
strokes are separate native styles.

Unlike the observed text-callout constructors' bare tail defaults, arrows retain
`tail-x` and `tail-y` as animated objects with `type: "double"`, `defaultValue`,
and `interp: "eioe"`. The installed descriptor supplies the default and
interpolation; the native constructor adds the type. Do not flatten these
objects to the numbers displayed in the property panel or discard interpolation
when matching presets.

Four 35-second sequences retain all native arrow payload and source audio. Each
independently reopens and reproduces its complete decoded video/audio. All 56
early/late frames were inspected, including endpoint shapes and stroke patterns.
Native arrows are small at their default size on the test canvas; Industrial's
muted purple line/shaft has low contrast against gray. Verify scale and contrast
for the intended background. Default-preset acceptance does not establish every
endpoint edit, Bézier option, or theme combination. Existing exact-build schema
and semantic checks pass without another profile extension.

Two additional Mac 2026.2.4 native control cases have independent 35-second
export pairs and 28 inspected edited frames beside their baseline frames.
Only the first red double-ended dotted arrow changes; six later presets retain
their payload and appearance, and source audio remains decoded-identical.

Enabling **Bezier Curve** adds `numCtrlPts: 2.0`, `ctrlPt0-x: 25.0`,
`ctrlPt0-y: 20.0`, `ctrlPt1-x: 75.0`, and `ctrlPt1-y: -20.0` to this arrow's
definition. Native output becomes an S curve with tangent-oriented endpoints.
Its existing typed `tail-x`/`tail-y`, stroke, clip transform and timing remain.
No new boolean flag appears. These observed coordinates do not establish a
universal coordinate conversion for other arrow geometry or edited handles.

The separate endpoint case changes left **circle**/right **diamond** to
`shape-anchor: "circle"`/`shape-tail: "diamond"`, line **solid** to
`stroke-style: "solid"`, thickness 12 to `stroke-width: 12.0`, and opacity 60%
to `stroke-color-opacity: 0.600000023841858`. Keep that saved numeric precision.
Native metadata retains original preset defaults as strings:
`default-callout-shape-anchor: "arrow"`, `default-callout-shape-tail: "arrow"`,
`default-callout-stroke-style: "dot"`, `default-callout-stroke-width: "8"`,
and `default-callout-stroke-color-opacity: "1"`. Preserve these fields alongside
the edited definition; property-panel values alone omit them.

Two further native pairs verify edited Bézier handles and full annotation-panel
Reset, with 28 inspected edited frames beside baseline frames. Native handle
drags change `ctrlPt0-y` to `70.1960784313726`, `ctrlPt1-x` to
`108.464052287582`, and `ctrlPt1-y` to `-53.4640522875817` in the observed
curve; do not clamp control points to 0–100. Endpoint locations, existing tail
descriptors and unrelated project data remain. The changed curve renders with
larger asymmetric bends and changed endpoint tangents after native reopen.

Handle edits add six metadata defaults as `{type: "double", value: ...}`
objects: `default-ctrlPt0-x/y` retain 25/20, `default-ctrlPt1-x/y` retain 75/-20,
and `default-width`/`default-height` retain 125/34. These typed values differ
from the endpoint/stroke reset strings above. The source arrow definition has
no width/height fields; those metadata values do not authorize inserting them.

Full annotation-panel Reset on the edited endpoint specimen restores
arrow/arrow, dotted stroke, thickness 8 and opacity 1. It retains all five
original-preset metadata strings and adds `lockAspectRatio` as
`{type: "bool", value: true}`. Its complete decoded video/audio reproduces the
accepted original Basic sequence, and independently reopened output matches.
These cases establish the observed controls; they do not define arbitrary
transformed-handle coordinate math or all theme/reset combinations.

## Shape presets

All 32 Mac 2026.2.4 shape presets were individually created through the native
palette: eight each in Abstract, Basic, Bold, and Industrial. Each saved
constructor uniquely matches an installed definition. Four 40-second sequences
independently reopen and reproduce their complete decoded video/audio. All 64
early/late frames were inspected, including filled shapes and transparent-center
outlines. Source bytes, native definitions, geometry, styles and unrelated
payload survive native saving with the observed media-ID bijection.

These use `Callout.def.kind: "remix"` with `shape-rectangle`, `shape-ellipse`,
`shape-triangle`, `shape-star`, and `shape-octagon`. The format-10 profile adds
the demonstrated star/octagon identifiers while retaining exact enum and type
constraints. Preserve `style`, dimensions, `corner-radius`, `fill-style`,
`stroke-style`, stroke width, and separate color/opacity components. The native
Bold star differs visibly from other styles; its equal-dimension ellipse renders
as a circle. A shape identifier alone does not reconstruct the preset.

The observed installed fill literal `00000000` becomes native black RGB with
`fill-color-opacity: 0`; six-digit black becomes opaque. Transparent-center
outlines retain `fill-style: "solid"` with zero fill opacity. Do not replace
them with black-filled rectangles or infer a general eight-digit color byte
order from this all-zero value. Preserve independently specified stroke opacity.

Read resource definitions rather than inferring semantics from filenames:
`AnnotationsBin/Shape/18-abstract-octagon.json` defines `shape-triangle`, and its
native output is a triangle. Industrial serializes as `urban`. Additional
geometry, fill/stroke edits, shape replacement and theme combinations require
their own native checks. Vendor preset definitions remain outside the plugin.

## Sketch Motion annotations

All twenty presets in the Mac 2026.2.4 Sketch Motion palette were individually
created through the editor and checked in two separate 100-second sequences:
one over source video, one over neutral gray. Both independently reopen and
reproduce their first export's complete decoded video and audio. One hundred
sixty inspected frames cover early/late drawing, the complete shape, and ending
Fade. The neutral variant retains the pattern sequence's decoded audio.

These are `Callout` clips with `def.kind: "TypeWinSVG"` and embedded
`def.xmlContent`. They are separate from an imported SVG `IMFile` source and
from the ordinary `Sketch` visual effect. The native definitions include width,
height, `DrawTime: 1.0`, `borderWidth: 3.0`, and separate `borderColorRed/Green/Blue`
components. The demonstrated yellow strokes retain red/green 1 and blue 0.
Keep each native SVG and its geometry/scale together; do not substitute a generic
shape identifier or round its fractional dimensions.

The drawing companion is clip-local `leftEdgeMods`, containing one object:
`group: "DrawPercentageFade"`, a project-tick `duration: 705600000`, and
`parameters: [{"name": "DrawTime", "func": "FadeInFunc"}]`. It is not a visual
animation-track interval. Each native five-second specimen also has a separate
one-sided ending Fade in its track, referencing that Callout's ID. Preserve both
the draw modifier and the ending transition; a clip that exists for five seconds
does not by itself establish drawing or fade timing.

The exact-build format-10 profile adds only this SVG kind and the demonstrated
single drawing-modifier shape. Unknown modifier groups/functions, extra fields,
multiple entries, and invalid duration types remain rejected. The native SVGs in
these twenty specimens contain no text/image/script/style elements, hrefs, or
CSS `url()` references. This bounded inspection does not establish dependency
closure for arbitrary SVG. No vendor SVG or font assets are distributed.

Native saves of the staged sequence renumber media IDs in source-lane-first
order and update the ending Fade references consistently. The strict comparison
checks that bijection and retains all other payload, with observed duration-label
and track-height bookkeeping recorded separately. Do not strip IDs or metadata
wholesale to make a preservation check pass.

## Chroma key

The native Remove a Color effect serializes as `ChromaKey`. Observed parameters
include `enabled`, `tolerance`, `softness`, `clrCompensation`, `defringe`,
`color-red`, `color-green`, `color-blue`, `color-alpha`, and `invertEffect`.
Preserve the native spelling and numeric representations.

The generated green/blue fixture remained green at the native default tolerance
0.1. A native change to 0.5 removed green while retaining the blue subject over
a white canvas. This establishes a tested correction for that fixture, not a
universal tolerance. Sample the actual input and inspect keying, edge spill,
foreground loss, and contrasting-background output before choosing settings.

## Person background removal

The native `BackgroundRemoval` effect retained `alphaMaskQualityLevel`,
`backgroundOpacity`, `blurBackgroundSigma`, `featherMaskSigma`, and
`aiModelSourceName`. This installation saved model name `modnet`, quality level
1, and typed double defaults for the three mask/background controls. Keep these
runtime-dependent fields opaque unless a same-build native change proves their
meaning. Native saves can mirror the effect onto the linked-media wrapper.

An uncropped local camera sample saved and rendered with its room background
removed. A small background fragment near the subject illustrates the need to
inspect segmentation edges; effect acceptance is not a guarantee of a clean
mask on every frame. TechSmith documents this feature for person camera footage
and cautions about cropped recordings and screenshares.
[Official input limitations](https://support.techsmith.com/hc/en-us/articles/46053810228109-How-can-I-remove-the-background-from-a-cropped-recording-or-a-screenshare-with-a-plain-background).

## Created cursor paths and highlight

Native Cursor Path Creator applied to an ordinary MP4 produced `CursorPath` in
the linked video and wrapper effects. `parameters.cursorLocation` has type
`point`; its point values are three-element coordinates. The native probe used
`[128, 90, 0]` at 705600000 ticks and `[512, 270, 0]` at 1411200000 ticks, with
project rate 705600000. Inspected one-/two-second frames place the pointer at
the corresponding image positions. The second keyframe's `interp.bezier`
contains two control-point vectors and easing identifier `eioe`.

Other native parameters include `cursorImagePath` (`Mac/pointer` here),
`cursorOpacity`, `cursorScale`, `cursorTrackLevel`, `cursorAction`, and
`smoothCursorAcrossEditDuration`. Built-in cursor lookup is a dependency on
the target installation; preserve it instead of distributing native assets.
These timings were observed on a zero-trim, speed-1 clip; retiming needs its
own mapping evidence.

The native highlight effect is spelled **`CursorHilight`**. Its typed doubles
include `radius`, four `color-*` components, and `blur`. Radius 50, yellow with
alpha 0.75, and cursor scale 2.0 rendered a visible highlight and larger pointer.
The native UI did not offer Add to Selected Media for Cursor Smoothing on this
generated-path MP4. That observation does not establish smoothing behavior on
a recording with captured cursor data; preserve that distinction.

## Interactive hotspots

Native Interactive Hotspot stores its state in
`UnifiedMedia.video.attributes.hotspot`, not in an ordinary effect node.
Mac 2026.2.4 format-10 native captures establish the default constructor and
Continue, Time, URL and Marker actions, including end pausing and URL window
selection. Use the [hotspot helper contract](helper.md#hotspot-json-editing) for
the executable mapping and candidate workflow. Inactive destination fields
survive native action changes; preserve them during unrelated edits.

Timeline markers target the timeline's ID, with matching local/global point
times. A linked clip's media markers are stored under
`UnifiedMedia.video.parameters.toc`, but the native hotspot's
`markerParametricId` identifies the enclosing **UnifiedMedia** ID. It does not
identify the video child or marker ordinal. Native selections of two timeline
points and one media point establish this distinction. Retain `markerTime` and
`lastMarkerGlobalTime` separately; the latter is not a substitute for the
point's own clock. Seven independent native captures match helper-generated
hotspot objects without copying those expected objects into the transformation.

Native **Export as Web Page** produced local Smart Player HTML, JavaScript,
CSS, MP4, and XMP configuration. Its XMP converts the destination to
`tscHS:jumpTime="6000"` with a millisecond track rate. Browser playback confirmed
that clicking the hotspot near the beginning seeks to six seconds. Serve the
package through HTTP with byte-range support: the first test server without
ranges could play but could not seek correctly. Keep the complete package;
a plain MP4 does not carry the clickable player interaction.

A JSON-authored format-10 sequence adds current-build runtime proof: six visual
clips exercise end pause/Continue, time seek, both URL window choices, timeline
marker and media-marker targets. After normal Quit, a fresh editor process
reopens, saves and exports the project again. Both 48-second native movies have
identical complete decoded video/audio; their XMP preserves all six actions.
Actual Smart Player clicks in both packages pass fourteen observed outcomes,
including a media-marker jump from the clip at 40 seconds to its point at 42
seconds. Native save remaps the six clip IDs and the linked marker reference
together. Continue pauses shortly before its clip boundary and clicking resumes
playback; do not require a browser pause event at the exact serialized end tick.

Native application to an image, callout, Group and screen recording retains the
same hotspot constructor. A Group owns its hotspot independently of its children.
Four before/after saves establish those owners; the helper preserves their
geometry, still hold, text, Quick Property bindings and recording processing.
Eleven further native marker selections verify source and global clocks for
image/callout holds, grouped text, recording in-points, trimmed video, 2× video,
Group trims, a Group-owned point, sped-up Group content, nested Groups and linked
AV. The helper calculates these observed single-scene mappings automatically;
other clock structures retain an explicit native-global-time input path.

A 96-second JSON-authored timeline exercises those four visual targets and all
eleven marker cases. Thirty actual Smart Player clicks, with observed click and
seeked times, repeat across independent native exports. Their native project
bytes and complete decoded video/audio are identical after fresh reopening.
Twenty inspected frames retain the image/callout/Group/recording pictures and
source timecodes at the retimed destinations. The
[Group reopen finding](project-format.md#clock-domains) records the unstable
positive-in-point constructor and verified rebasing used for the accepted pair.
Legacy still-screen, stitched and placeholder constructors remain distinct cases;
this evidence does not promote them into the helper's observed target set.

## Quizzes and SCORM

Native timeline quizzes use `timeline.parameters.quiz`: a `type: "string"`
parameter with point keyframes whose values contain XML. The four observed
question elements are `MultipleChoice`, `Logical`, `FillBlank`, and
`ShortAnswer`, under `Quiz/Questions`. Preserve XML escaping, question/answer
IDs, correctness flags, feedback actions, and the quiz's timing domain.
`metadata.QuizCount` is a typed integer. Do not replace this with invented JSON
question objects.

The editor refused insertion on a 640×360 canvas and offered to enlarge it;
the native adjustment preserved the aspect ratio at 853.333×480. Quizzes require
at least 640×480 according to that native dialog. Verify dimensions after the
editor's adjustment rather than assuming a fixed replacement size.

The native local web export paused at the quiz and presented all four question
types. Correct answers scored **3 correct, 100%**; the short-answer response
was recorded with a neutral result and excluded from grading. A local mock LMS
received SCORM 1.2 `LMSInitialize`, question interactions, `cmi.core.score.raw`
100, `cmi.core.lesson_status` passed, `LMSCommit`, and `LMSFinish`. The exported
ZIP passed integrity checking and contained `imsmanifest.xml` and local player
resources. This proves the tested package's local API behavior; verify import,
resume, completion policy, and reporting in the destination LMS before delivery.

The current Mac 2026.2.4/format-10 contract also has a standalone
[JSON quiz editor](helper.md#quiz-json-editing). A three-quiz, six-question
candidate generated by that helper opens and saves without quiz normalization.
A fresh-process reopen preserves all question XML, source/timeline data and
quiz timing. Showing the quiz tray changes three track-height metadata values
from `"78"` to `"63"`; this layout-only change is retained explicitly. The
native survey panel displays Score Quiz and Viewer can see their results off
for the helper's disabled root options. This panel check is distinct from
proving scored-choice survey behavior.

A separate forty-second JSON-authored native pair exercises per-question
feedback for both correct and incorrect answers. The helper's schema-2 input
supports response text and Continue, URL, Time and Marker actions; schema-1
inputs remain readable. Native feedback uses question attributes rather than
the root viewer-results option. Native action strings and input fields are
owned by `scripts/quizzes.py`'s feedback contract. Preserve inactive URL/time/
marker destinations when switching actions or disabling response feedback.
Marker selection adds `metadata.markerIdentifier` to the existing marker
keyframe. Feedback stores that identity and its global millisecond time;
the helper requires an existing unique identity instead of inventing a target.

Twenty actual responses across first/reopened exports verify Unicode/XML
feedback, both branches of each action and disabled response feedback.
Continue presents results. URL opens the requested local destination in a new
tab while retaining the original quiz results. Time and Marker resume playback
at their destinations, bypassing the results screen. The ungraded multiple-choice
survey exports `correctAnswer` as `0`, records the stored incorrect choice as
`neutral`, and contributes no answer key or denominator to runtime grading.
The deliberate five-correct/four-incorrect graded controls score 55.55555555555556,
scaled 0.5555555555555556, `failed` and `completed`; the survey is excluded.
Both sessions commit and terminate. Saved JSON repeats byte-for-byte after a
fresh process; only the initial duration label changes. Full decoded AV repeats,
with twenty inspected frames and native ZIP/XSD/resource closure checks.
This proves the exercised forward timeline-marker destinations. Feedback
destinations on other containers and destination-LMS resume remain separate cases.

### Survey grading inputs

Schema-3 authoring supports ungraded multiple-choice, true/false, fill-in and
short-answer questions without requiring grading answers from the caller.
The helper reproduces the complete native candidate, saves and reopens with
zero parsed JSON differences, and preserves existing inactive keys on omission.
An explicit empty fill-in answer list clears its stored accepted answers.

Mac 2026.2.4 requires a stored multiple-choice key even when scoring is off.
Two isolated zero-key probes save successfully but export a movie and ZIP
without the required `_config.xml`; their player HTML still references it.
Opening native survey properties assigns the first choice as the inactive key.
The helper follows that behavior for new keyless choice inputs and retains a
single surviving inactive key when updating. A true/false question retains a
native boolean, while an empty fill-in key list exports successfully. These
are distinct serialization requirements; save/reopen alone does not prove
the interactive export is usable.

Both independent native fourth-edition packages retain all five questions and
pass ZIP/member/resource and manifest XSD checks. Their complete decoded AV
matches. Ten actual responses record one correct control and four neutral
survey interactions per session. The choice and true/false responses oppose
their inactive keys; the fill-in accepts arbitrary Unicode text with no key.
All four survey interactions omit runtime correct-response keys. Each session
finishes raw 100/scaled 1, passed/completed, committed and terminated through
53 successful calls. A native screenshot shows ungraded results without a
score. Evidence is `quiz-surveys-native-checks.json`; schema 1/2 remain readable.

### Suspending and resuming a quiz session

Resume state belongs to the exported player/LMS attempt, outside the project
JSON. Preserve the native `cmi.suspend_data` string without rewriting its quiz
model. The observed Smart Player payload uses `tscsp2` with viewing progress,
view history, a runtime-seconds bookmark and question snapshots. These fields
are native player internals, not the JSON quiz editor's authoring spec.

1. Open the native SCORM output in the intended LMS/runtime.
2. Hide an open pending quiz, select **Complete video later**, and confirm
   **Exit video**. Verify successful suspend-data/location writes, commit,
   `cmi.exit: suspend` and termination.
3. Start a new session with the retained attempt state. The LMS supplies
   `cmi.entry: resume` and resets session flags; it owns total-time accounting.
4. Verify the actual native playback position and retained answers before
   finishing the remaining questions. Check final score/status and termination.

Two unchanged, independently produced SCORM 2004 fourth-edition packages have
completed this sequence. Each initial session saves two correct answers, a
third viewed/unanswered question and bookmark `14`, then commits and terminates
after 36 API calls. A newly opened session reads the exact prior suspend string,
starts at native player second 14 and writes only interactions 2–7. All eight
answers finish correct, raw 100/scaled 1, passed/completed, with 66 API calls in
each resumed session. Completion clears the suspend string and exit flag.
The pre-suspend progress slider reads approximately 13.5 seconds while the
native bookmark stores 14; use the native saved state and observed reopening
instead of inferring the bookmark from that slider alone. One captured native
screen independently shows the resumed 0:14/0:36 position and pending quiz.

The local observer carries attempt state and records native calls; it does not
implement a production LMS's full data model, time accounting or certification.
Other SCORM editions, cancellation/restart and rejected suspend writes retain
separate test cases. [TechSmith's session-exit guidance](https://support.techsmith.com/hc/en-us/articles/360016509591-Update-the-Version-of-the-TechSmith-Smart-Player)
describes the exit control and resume route. The
[ADL runtime model](https://github.com/adlnet/SCORM-2004-4ed-Test-Suite/blob/050f1b4282c914154ab80254e4767ce8c58d0d36/software_development/src/org/adl/datamodels/ieee/SCORM_2004_DM.java)
defines the entry and session-flag reset behavior used by the observation adapter.

SCORM 2004 **2nd, 3rd and 4th editions** each have independent native first/
reopened web exports and actual player interaction. All six packages report
six responses, raw score 100, scaled score 1, success `passed`, completion
`completed`, Commit and Terminate through `API_1484_11`. The tested types map
to `choice`, `choice`, `fill-in`, `long-fill-in`, `choice`, `long-fill-in`.
True/false with a false key scores correctly. The alternative fill-in answer
`four` scores correctly and both `4`/`four` reach correct-response patterns.
Both short responses remain neutral and excluded from scoring. Unicode,
quotes, ampersands and angle brackets survive native XML, exported XMP and
the visible player. All six complete decoded video/audio streams match.

Each ZIP passes CRC/member-byte checks and contains every manifest resource.
The manifest validates offline using all namespace schemas named by its
`schemaLocation`; validating against only the content-package XSD omits other
namespaces. Second edition exports native `schemaversion: CAM 1.3`; third and
fourth name their editions explicitly. Do not relabel native output to hide
that distinction. The local adapter uses ADL's standard API signatures and
lifecycle codes, records actual SetValue calls and retains six completed
sessions. This proves these exports' local behavior, not LMS certification,
resume support or destination-specific policy.

A deliberate multiple-correct-answer diagnostic saves but exports only its
last marked answer. The player presents radio buttons and scores the earlier
marked answer incorrect, producing 75%/failed. The helper now refuses such
authoring input. Multiple accepted fill-in answers remain supported.

Media-owned quiz editing is verified separately in Mac 2026.2.4. Native
pinning of a quiz at timeline second 4 onto linked AV starting at second 2
with source in-point 1 moves its unchanged XML to the **video child's** quiz
parameter at source second 3. Unpinning restores the timeline point at 4;
both operations preserve quiz/question/answer IDs. The wrapper's clock applies
once; the mirrored video timing is not another transform.

A JSON-authored 36-second sequence has eight quiz points across linked AV,
retimed video, an image hold, a callout, a Group, a recording with an in-point,
a 2× Group and a nested video child. Exported XMP and actual player triggers
agree at **4.5, 10, 14, 19, 24, 29, 33 and 34.5 seconds**. The image retains
`mediaDuration: 1`; its quiz uses the visible held interval. Source trim,
inverse speed and Group ancestry remain distinct clock operations. Native
normalization remaps three sources, the timeline, fourteen clip IDs and the
two child Quick Property bindings, adds the standalone video's standard
metadata, updates duration/thumbnail, and retains Group content-clock values
with native numeric types. Quiz XML, point times, effects and other fields
remain under strict comparison.

The complete project is byte-identical after a fresh-process save/reopen.
Both SCORM 2004 fourth-edition packages have eight actual correct responses,
100%/passed/completed, commits and termination. Two deliberately added-then-
removed points are absent from native JSON and exported XMP. Complete decoded
AV repeats; sixteen inspected frames retain the image, annotations, recording,
source-video regions and native Group bounds/crops. This adds owner-aware
editing/removal and exact-XML `move`, including automatic inverse clock
conversion that preserves global position. Inspect and select the new native
IDs after saving; candidate IDs are not stable across a native normalization.

Additional feedback destination clocks, other-edition/restart/failure resume,
standalone audio, screen-still/stitched/placeholder quiz owners and multiple-scene clocks require further native
cases. Preserve those existing representations; the tested owner mapping does
not authorize guessing another container's clock.

## Media and track mattes

Mac 2026.2.4 format 10 has two distinct mechanisms. Root track selection changes
`timeline.trackAttributes[index].matte`; a Group's track uses its own `matte`
field. Native UI captures establish None `0`, Alpha `1`, Alpha Invert `2`,
Luminosity `3` and Luminosity Invert `4`. Media Matte is a separate
`categoryVisualEffects` effect named `MediaMatte`. Fresh native application uses
bare `matteMode`/`trackDepth` and a typed static double for `intensity`; the parser
serializes that intensity as a bare number after reopening. Both forms are valid.
The observed constructor uses mode 1, intensity 1 and depth 10002. Preserve
existing depth. The helper's supported input contract is in
[matte JSON editing](helper.md#matte-json-editing).

Twelve native changes replay through the helper. Changing the media mode or
intensity preserves the preset label and adds the corresponding native reset
metadata. Easing stores `leftEdgeMods` / `rightEdgeMods` with group `Video`,
project-tick duration, and intensity `FadeInFunc` / `FadeOutFunc`. Native one-
and half-second captures give 705600000 and 352800000 ticks. Clearing the known
fade removes its modifier; native saving removes empty modifier arrays. Bypass
sets the effect's boolean `bypassed`. Root track changes leave the media effect
and source content intact. Unknown modifiers, controls and reset data survive
unrelated helper edits; shared modifier timing requires separate native evidence.

A JSON-authored 67-second project isolates 22 cells using native Group/AV and
filled-ellipse constructors. Both media effects and Group track modes are
tested with white and black shapes. Alpha ignores those RGB differences;
Luminosity on black hides the underlying video, while Luminosity Invert on
black reveals it. Inverted white mattes hide the ellipse's interior and retain
the outside. The independent native control distinguishes a valid hidden
region from absent source video.

In the tested Alpha effect, half intensity leaves the interior intact and
partially reveals the outside. Zero intensity reveals the entire lower video;
bypass instead draws the opaque white shape normally. One-second easing starts
with the lower video visible, reaches the full matte and restores the outside
at the end. Five within-cell samples distinguish that progression from a static
mask; cleared easing retains the full matte.

The first native save changes only thumbnail/duration caches, 44 Group clock
number types and the two empty cleared-edge arrays. IDs, sources, audio,
matte modes, timing and other payload remain strict. A fresh process preserves
byte-identical JSON and repeats complete decoded video/audio. All 54 native
frames are inspected; independent inner/outer regions verify 16 mode/color
cases per phase, and 44 stereo windows retain the control's RMS/frequencies.
Evidence is `matte-native-checks.json`.

Seventeen additional native helper replays extend creation and controls to
standalone video, linked AV, still images and Groups, including fresh Callout
construction. Linked AV stores matching effects on the wrapper and video child;
audio remains unchanged. `metadata.effectIndex` is a stable token, not an array
position. After deleting matte token `0`, Border token `1` moves to position zero
without changing its token. Native reapplication appends matte token `2`.
Do not renumber other effects or remove one linked visual mirror alone.

A JSON-authored 72-second, eighteen-cell native pair verifies these owners,
typed half intensity, image bypass, linked/Group removal, three retimed ease
owners and depth values `0`, `1`, `2`, `3`, `10002`. Each depth remains in saved
JSON; all five render the same blue ellipse over the unchanged lower video in
this three-track stack. They mask the immediate blue layer and leave the lower
video visible outside. This does not establish a depth-to-track-count formula.
Use Group composition for a verified coverage boundary.

At 2× speed with positive source in-points on video/linked clips and a zero
in-point on a Group, one-second/half-second easing still follows timeline seconds.
Do not multiply its edge duration by inverse speed. Sixty inspected frames and
36 stereo windows distinguish masks, restored visual content and the linked
source mix. Retimed linked audio matches an independent no-matte clock control;
ordinary linked layers add their synchronized audio rather than silently muting it.
Reopened bytes and complete decoded AV repeat. The native parser changes only
thumbnail/duration caches, 42 Group number types and sixteen static intensities.
Evidence is `matte-owners-native-checks.json`.

Linear intensity curves have native output on Callout, standalone video, linked
AV, images and Groups. A JSON-authored discovery sequence distinguishes source
positions from timeline positions on trimmed 2× video and zero-in-point 2× Groups.
The typed double retains its initial `defaultValue` and interval keyframes with
`time`, `endTime`, `duration`, `value` and `interp: "linr"`. Unlike edge easing,
these curve bounds use source positions in project ticks. The helper accepts
clip-relative timeline seconds and converts them through the visual owner's
source in-point and inverse speed. Linked wrapper/video clocks must agree.
The still-image curve spans the visible hold even with `mediaDuration: 1`;
do not clamp its animation to that one-unit source duration.

The native parser removes redundant parameter-level linear interpolation and
derives missing visual intervals from the curve. In the discovery fixture it
also creates constant `scale0`/`scale1` companions on video and still owners.
Those retain the original scale values and do not introduce a visible scale
animation. Explicit preexisting visual intervals survive; a separate native
case with explicit intervals renders the same matte progression.

A second sequence authored through the shipped commands clears intensity on
all five owner types, retaining every unrelated visual interval and scale curve.
The six physical cleared mirrors first save as bare constants. Reopening derives
six constant intensity curves from the retained visual intervals, including their
optional interpolation fields; other payload stays unchanged. Clearing to zero
restores the full lower video throughout the sampled window. The discovery pair
reopens byte-identically; the clear pair has only those six known companions.
Both 44-second native pairs repeat complete decoded AV. Four contact sheets contain
204 inspected samples; 44 stereo windows
verify unchanged source audio, including the linked clip's second contribution.
Evidence is `matte-curves-native-checks.json`. Nonlinear/point intensity curves,
recording owners and interacting media/track mattes retain separate cases.

## Companion apps and connected imports

These workflows have vendor-documented entry points; their linked project state
requires native before/after evidence. Do not manufacture a successful handoff
by adding an app name, source transcription, or an ordinary Group to project JSON.

| Workflow | Entry point and dependency | Verification |
| --- | --- | --- |
| Rev | Import Media Bin footage into Camtasia Rev; retain the recording's screen, camera, and cursor streams for relevant layouts. Current Rev media supports component editing, SmartFocus, and dynamic captions. | Save a same-build native specimen, modify a layout, reopen and render it. Preserve opaque component state until its ownership and clocks are established. |
| Audiate | Select timeline audio → Edit in Audiate, or Edit as Text. Audiate is a separate installation; included capabilities and account requirements are documented by TechSmith. | Save the editor project first. Choose the intended sync scope, send one synthetic edit back, then compare both affected and preserved tracks and independently reopen/render. |
| Edit in Snagit | Use the image's native Edit in Snagit command with a compatible Snagit installation. Mac's timeline command was added in 2026.0.4. | Change a disposable image, send changes back, and check actual image pixels, framing, scale, duration, and reopen/render persistence. Preserve editable SNAGX content when required. |
| Snagit Step Capture | Snagit 2026.3.0+ sends step captures to Camtasia Editor 2026.2.0+. | Use a synthetic step sequence, verify step ordering and timing on the resulting timeline, save/reopen, and inspect transitions/animations in the native export. |
| Zoom cloud import | File → Import → Zoom connects to hosted recordings for which the signed-in user was meeting host. Native choices include Open in Rev and Import Media. | Use an authorized test recording; check downloaded streams, duration, selected layout, saved source paths, and independent rendering. An ordinary MP4 import does not verify this connected flow. |

Audiate's **Edit Camtasia Timeline** scope synchronizes edits across tracks over
the linked interval; **Edit Media Only** limits synchronization to the linked
media. Record the chosen scope before accepting timeline changes. Its caption
options and unlink operation are separate state changes. See
[Audiate integration](https://support.techsmith.com/hc/en-us/articles/39967435209485-Using-Camtasia-Audiate-with-Camtasia-Editor)
and [installation/included capabilities](https://support.techsmith.com/hc/en-us/articles/41334438405773-How-to-access-the-included-Audiate-features-with-Camtasia-Editor).

Rev and Zoom's visible workflow is documented in
[Edit Zoom Recordings](https://www.techsmith.com/learn/tutorials/camtasia/edit-zoom-recording/).
Unpacking Rev media changes its editing workflow; retain a saved copy before
testing it. For introduction versions, use the
[Mac editor history](https://support.techsmith.com/hc/en-us/articles/41263167862285-Camtasia-Mac-2026-Version-History)
and [Mac Snagit history](https://support.techsmith.com/hc/en-us/articles/41975263481613-Snagit-Mac-2026-Version-History).

An absent companion app, deployment-disabled command, missing service account,
or unavailable recording is a named dependency, not a JSON-validation failure.
Complete local staging and checks first. Account connections, remote content,
and publishing retain their own authorization requirements.

## Device frames and installation assets

Native Device Frame saved `DeviceFrameEffect`, category
`categoryVisualEffects`, with `parameters.deviceFrameSource: "Desktop_1.mp4"`.
The editor mirrored it onto the linked wrapper and video child. The asset is
resolved from the Camtasia installation's Resources directory, outside
`sourceBin`; a complete source-bin path audit alone cannot certify portability.
The observed export placed generated video inside a desktop monitor with its
bundled surrounding scene. Verify both installation assets and source files
on the target build. Do not redistribute proprietary bundled media as plugin
fixtures. The exact-build profile adds the missing effect identifier.

## Installed preset discovery

The inspected 2026.2.4 installation has separate resource families under
`Camtasia.app/Contents/Resources`: annotation presets in `AnnotationsBin`,
`.cube` files in `Color LUTs`, shader definitions in `CursorEffects`,
`ClickEffects`, `VisualEffects`, and `Transitions`, and sample projects in
`DynamicCaptions`. These are different dependency types. An installation's
resource count is not its UI preset count: this build has 148 transition
shader files while its observed palette lists 179 transitions.

The resource inventory found 114 annotation JSON presets, 32 LUTs, and seven
dynamic-caption sample projects. Annotation preset `kind` values include
`remix` and `MacKey`; treat them as preset metadata until a native applied
project establishes the corresponding `Callout.def` contract. An example
project bundled by the current app can still identify an older author/format.
Inspect that identity before using it as a serialization reference.

The 32 installed LUT files contain complete finite 3D tables: 31 use
`LUT_3D_SIZE 25` with 15,625 RGB rows, and `Enhance Contrast (Default).cube` uses
size 64 with 262,144 rows. Its internal title is **Enhance Contrast**, distinct
from the filename. Retain the original table bytes and resolve the actual file;
do not reconstruct a LUT from its title or assume every preset has one grid
size. Structural table checks do not establish Camtasia's interpolation, project
serialization, imported dependency closure, or rendered output. TechSmith's
[Mac LUT workflow](https://support.techsmith.com/hc/en-us/articles/360060036192-Using-LUT-Visual-Effect-in-Camtasia-Editor-on-macOS)
describes loading a CUBE file through the effect's properties. The native
factory-filter contract below supplies observed project parameters; custom
imports need their own saved dependency and output checks.

Do not feed a `.tsceffect` file to the project schema or copy its shader
definition into a clip's `effects` array. Several files contain raw newlines
inside quoted shader code; six current definitions still fail JSON parsing
even with relaxed control-character handling. Obtain their project parameters
by applying the preset through the target editor and diffing saved projects.
Keep native shader code and bundled LUT/media assets in their installation;
record dependency selectors and verify the result on the destination build.
Presence on disk establishes discovery evidence, not successful application,
persistence, or rendering.

## Color LUT filters

Mac 2026.2.4 natively applies **Basic Black & White** as `LutEffect`, category
`categoryVisualEffects`, `bypassed: false`. A linked AV clip mirrors the effect
on its wrapper and video child; its audio child remains unchanged. The wrapper's
last-applied `metadata.effectApplied` becomes `LutEffect`. Preserve effect order
and metadata, including `effectIndex: "0"` and the native `presetName`.

The observed full-intensity/full-range parameters are:

| Parameter | Native value |
| --- | --- |
| `lutSource` | `Basic Black & White.cube` filename string |
| `lut_intensity` | 1.0 |
| `channel` | 0 integer |
| `shadowRampStart`, `shadowRampEnd` | 0.0, 0.0 |
| `highlightRampStart`, `highlightRampEnd` | 1.0, 1.0 |

Initial application wraps each of these five double values in
`{"type":"double","defaultValue":1.0,"interp":"linr","uiHints":{"userInterfaceType":0,"unitType":0}}`,
with the corresponding default substituted. A later native reopen/save converts
these unanimated default descriptors to literal doubles in both effect arrays.
Retain either observed representation. Do not flatten keyframes or generalize
this conversion to other effects or parameter values.

Four 64-second native sequences exercise all 32 factory definitions at these
defaults, using full eight-second source clips, distinct media IDs, and unchanged
source bytes. All four independent reopen/export pairs reproduce their complete
decoded video and audio. Two inspected source phases per filter show its output
against the unfiltered control: 64 native/control frame pairs. The initial Basic
Black & White case also has native palette application, its own independent
export pair, and four inspected frame pairs. The other sequences use actual
native factory definitions and the observed static serialization; this does not
establish 32 individually clicked constructors or every parameter combination.
Both existing community and exact-build schema checks accept these saved files.

Resolve and hash the selected CUBE file separately from `sourceBin`. Native
factory recovery creates user `Color LUTs` copies with installation-identical
bytes and `VisualEffects/LUT <name>` preset directories containing `effect.json`,
`preview.png`, and `preview.mp4`. An empty Filters palette can coexist with intact
installed CUBE files. In the observed case, the gallery's **Restore Default
Effects** populated all 32 filters and retained all 45 preexisting preset files
byte-for-byte. Back up existing user presets before recovery; follow TechSmith's
[missing-effects instructions](https://support.techsmith.com/hc/en-us/articles/360062098032-Effects-Missing-in-Camtasia-Editor-on-macOS).
Do not distribute vendor LUTs or treat a media-source manifest as filter closure.

Keep native rerender equality separate from unfiltered-control audio equality.
The Basic Black & White and clean control each reproduce their own complete
decoded audio after reopening. Their native stereo 44.1-kHz, 16-bit Wave exports
differ in 191 of 352,800 sample frames, with a maximum difference of one 16-bit
step and zero measured lag. Their AAC exports also differ. Report the direct
difference; do not align, normalize, or erase it with a tolerance. These results
do not identify Camtasia's internal cause.

Native **Open CUBE file** imported a synthetic size-2 inversion table whose
internal `TITLE` differed from its filename. The saved `lutSource` uses the
filename, and the editor copies identical CUBE bytes into its user `Color LUTs`
directory. The original import file was then unavailable during a fresh-process
save/reopen/export pair; both decoded streams match and four inspected frames
show the inversion. The effect retains its original preset metadata rather
than adopting the CUBE title. Its native Reset selector returns to the original
factory filename. Preserve those metadata/reset companions when changing the
resource selector. No new visual-preset files appeared in this import case.

Four further native control states verify intensity 0.5, Grey Shadows, one-second
ease-in with 1.5-second ease-out, and bypass. The native halves use bare numeric
`lut_intensity: 0.5`. Easing uses `leftEdgeMods`/`rightEdgeMods`, `group: "Video"`,
project-tick durations, and a parameter entry naming `lut_intensity` with
`FadeInFunc`/`FadeOutFunc`. Zero-duration edge arrays survive native disabling
of easing; retain them. Wrapper/video effects remain equal, audio stays intact,
and `default-LutEffect-*`/`default-easeIn`/`default-easeOut` metadata records the
native reset values. The four-state native pair repeats complete decoded streams;
12 inspected native frames beside 24 reference frames show partial processing,
edge easing, and bypass. The half-inversion control is intentionally neutral
gray, so that case alone cannot establish visible geometry.

All thirteen native Range choices have saved constructors and two independent
sequence pairs. `channel` is 0 for Grey, 1 for Red, 2 for Green and 3 for Blue.
The four ramp parameters serialize as follows; Shadows/Midtones/Highlights each
offer all four channels, while Grey All is the sole All entry.

| Range | `shadowRampStart` | `shadowRampEnd` | `highlightRampStart` | `highlightRampEnd` |
| --- | --- | --- | --- | --- |
| All | 0.0 | 0.0 | 1.0 | 1.0 |
| Shadows | 0.0 | 0.0 | 0.25 | 0.5 |
| Midtones | 0.25 | 0.4 | 0.6 | 0.75 |
| Highlights | 0.5 | 0.75 | 1.0 | 1.0 |

The two sequences retain full eight-second source slots, effect mirrors and
unrelated payload. Both pairs reproduce complete decoded video/audio. All 26
native frames were inspected beside 52 unfiltered/full-filter references.
These controls select input ranges; a Red mask does not mean only the red
output component changes. Do not derive exact blending/color-transfer math
from the labels or this saturated-color fixture. Custom ramp-handle positions,
animated intensity and additional effect combinations need their own cases.

With both original/imported custom CUBE locations absent in a fresh process,
the editor retained the filename and effect payload and displayed **Color LUT
file not found. Please select another.** Its two native exports repeated
decoded video/audio; complete video equaled the unfiltered control, while
decoded audio did not equal that separate control. Four inspected frame pairs
show unchanged source color/time/geometry. This is observed missing-resource
fallback, not successful grading. Structural/schema/media-source checks passed
without resolving the CUBE dependency. Restore or replace the exact resource
and inspect new output before delivering a graded project.

## Template package roundtrip

Native **File → Export → Template** produced a ZIP-format `.camtemplate` with
`templateInfo.json`, a GUID-named `.tsctemplate` JSON document, a preview PNG,
and both referenced MP4 source files. `templateInfo.json` included `Id`, `Name`,
`Version`, and `DateUsed`. Treat package identity separately from an ordinary
project clone. Do not change internal GUIDs or timestamps to imitate a native
export without a measured requirement.

**File → Import → Template** added the uniquely named disposable template;
**New Project from Template** instantiated its eight-second timeline. Saving
as a standalone `.cmproj` copied sources to relative `./media/...` paths. The
new project retained its 70% video framing and rendered successfully. Check
archive integrity, referenced media hashes, native instantiation, standalone
save, and final render when delivering a template. A JSON document renamed
`.camtemplate` does not establish this package contract. The probe used local
generated inputs; no native template package or bundled asset is distributed.
