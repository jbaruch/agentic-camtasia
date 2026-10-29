# Native transitions

These observations target Camtasia Mac 2026.2.4, project format 10.0. All
179 presets in this installation's native palette and a clean control have
actual native exports
and independently reopened rerenders with identical decoded video and audio.
Five hundred forty inspected boundary frames show the effects. The fixture uses two
four-second text Callouts above continuous video/audio; it does not establish
every transition's behavior on trimmed AV or short clips.

## JSON editing

The [transition helper](helper.md#transition-json-editing) provides direct JSON
Fade construction, existing scalar controls, duration changes and removal.
Eight whole-native controls reproduce Fade creation at a linked AV edge/join,
bypass, reverse, coupled preroll, re-enable, two-second duration and both
removals. Removing the last transition omits the track array. Eleven fixed core
tests protect clocks, preservation, selectors, fit/refusal and separate staging.

A sixteen-block, 128-second native/helper sequence independently reopens with
byte-identical JSON and repeats complete decoded RGB/audio streams across two
native exports. First save changes only the thumbnail. Eighty inspected pictures
match the controls; the edge fade and enabled shared fade have measured visible
differences from their controls. Thirty-two stereo tone windows preserve audio,
all copied source hashes stay unchanged and the native MP4 handle resolves
inside the test bundle. Raw and existing-profile schemas pass without correction.
Each installed Codex, Claude Code and Cursor copy executes all eight controls.

This helper's constructor is Fade. Existing other-preset scalar edits preserve
the saved preset payload; a new combination needs its own native render check.
Nested track clocks, null endpoints and source-handle synthesis are separate
contracts. The earlier preset catalogue and boundary measurements below retain
their original scope.

## Ownership and boundary clock

Native transitions belong to a track's `transitions` array. `leftMedia` and
`rightMedia` identify its media endpoints, separate from source-bin IDs. Keep
the original endpoint representation when remapping clips. The native samples
link two Callout IDs on the same track; transitions are not ordinary clip
effects or animation markers.

At the exercised four-second join, native saves use `duration: 352800000` with
project `editRate: 705600000`. The editor's transition overlay spans the half
second on either side of that join. That saved duration is not the full
one-second displayed interval. Preserve this boundary relationship instead of
changing clip durations or interpreting the field as a total overlap.
Additional native Fade controls establish the one-sided cases. Fade-in stores
only `rightMedia: 6` and `duration: 705600000`; inspected output fades the first
Callout in from zero to one second. Fade-out stores only `leftMedia: 7` with
that same duration and fades the final Callout over seconds seven through
eight. The unused side remains omitted after reopening. Preserve omission
rather than inserting an unexercised null endpoint. A shared Fade boundary
retains the half-second duration and visibly crossfades from 3.5 to 4.5 seconds.
All three independent rerenders match decoded video/audio, with unchanged
clip/source payloads and continuous audio. These Fade controls supplement
the table's presets. The linked-AV and edited-boundary cases below separately
exercise source handles, gaps, and retiming.

TechSmith documents placement at a clip's beginning, end, or shared boundary,
with duration adjusted on the timeline. Its instructions describe editor
behavior rather than a project-file schema. [Official transition workflow](https://support.techsmith.com/hc/en-us/articles/41262572834829-How-do-I-Make-a-Video-With-Camtasia-Editor)

## Short clips

The short control has two adjacent six-frame Callouts at 30 fps. Each retains
`duration` and `mediaDuration` of `141120000`, with scalar 1; their timeline
intervals are 0–0.2 and 0.2–0.4 seconds. Continuous background video/audio lasts
eight seconds. The default Fade palette drop added no transition in two native
attempts, including an enlarged timeline; those attempts are retained separately.

A separate backed-up candidate copies the observed native Fade and sets its
boundary extent to `141120000`. Native save preserves that value and both clip
intervals. Inspected frames show a shared crossfade over 0–0.4 seconds, followed
by the unchanged background; it does not extend the Callouts. The clean short
control and fitted Fade each independently reopen and produce identical decoded
video/audio to their first exports. Audio equals the continuous control.

Fit a requested short transition through a staged same-build, same-clock native
candidate and verify its saved representation and output. Do not claim that a
failed default drop establishes that short transitions are unsupported, or that
this Fade example establishes another preset's minimum duration.

## Linked AV and trimmed content

A native scalar-one split at four seconds creates `UnifiedMedia` endpoints
3 and 6 with separate video/audio children. The shared Fade belongs to their
track and references those wrapper IDs, not the video-child IDs. It saves
`duration: 352800000` with the same `705600000` project clock. Native
**Use trimmed content** controls both flags together:

| Native checkbox | `useVisualPreRoll` | `useAudioPreRoll` |
| --- | --- | --- |
| On | `true` | `true` |
| Off | `false` | `false` |

Toggling the checkbox changes neither clip's source interval, duration, scalar,
nor processing. Preserve those fields; switching the flags does not untrim the
clips. All four fixtures—uncut, split without a transition, Fade on, Fade off—
independently reopen and produce identical video/audio to their own first
exports. Their actual bundled source-file identities and bytes match.

With the checkbox on, this continuous-source Fade's video equals the uncut
control. Turning it off produces ghosted moving edges around the join; inspected
3.6–4.4-second frames expose the change. The visible movement looks restored at
4.6 seconds, but decoded differences remain; sampled appearance does not prove
exact first/last changed frames. Both Fade settings' audio equals the split
control in AAC and lossless PCM. The split itself changes native PCM from the
join onward; read [split audio controls](audio.md#splits-and-transition-audio).
This continuous-source specimen does not establish other boundary geometries;
the following fixtures measure them separately. Null endpoints remain unexercised.

## Edited AV boundaries and independent preroll flags

Eight additional same-build Fade candidates retain the complete saved clip,
source, global, and opaque payloads of the changing-tone controls in the
[clock map](project-format.md#clock-domains). Every candidate has native save,
independent reopen, and identical first/reopened decoded MP4 and lossless Wave
outputs. All eight pass the existing exact-build schema and semantic checks.

The six-second source-skip edit plays source 0–3 followed by 5–8. Its shared
Fade retains wrapper endpoints 3/6 and `duration: 352800000`. Four separately
staged combinations establish native persistence of each boolean independently.
TT/TF/FT/FF below name **audio first, visual second**; the editor checkbox still
toggles both flags together.

| Saved combination | `useAudioPreRoll` | `useVisualPreRoll` | Complete video result |
| --- | --- | --- | --- |
| TT | `true` | `true` | Same as FT; differs from TF/FF and control |
| TF | `true` | `false` | Same as FF; differs from TT/FT and control |
| FT | `false` | `true` | Same as TT |
| FF | `false` | `false` | Same as TF |

The sampled 2.6–3.4-second frames show blended moving diagonals with different
trajectories for the two visual groups. Visual preroll changes the rendered
result for this source skip; audio preroll changes neither decoded AAC nor native
lossless PCM. All four audio outputs equal their source-skip control exactly.
Do not infer independent audio-fade behavior merely from the persisted flag.

The six-second retimed edit plays source 4–8 over timeline 4–6 at 2.00x. Shared
Fade TT and FF retain that clip timing and half-second boundary extent. Both
complete videos differ from each other and the retimed control; inspected
3.6–4.4-second frames show mixed diagonal trajectories and gray-shape sizes.
Both audio outputs equal the retimed control in decoded AAC and lossless PCM.
Only coupled on/off settings were exercised on this retimed boundary.

The ten-second gap edit has clips at 0–4 and 6–10. It uses separate one-second
outgoing/incoming Fades: outgoing stores only `leftMedia: 3`, incoming only
`rightMedia: 6`, each with `duration: 705600000`. Preserve the omitted unused
endpoints; do not synthesize a shared transition across the gap. TT and FF
produce identical complete video streams, fading out over 3–4 and in over
6–7. Inspected middle-gap frames remain black. Both settings equal the gap
control in decoded AAC and lossless PCM, retaining its silent gap.

These measurements cover this Fade, source, normalization-off mix, and Mac
2026.2.4 build. Preserve the requested flags and verify other presets, rates,
processing, and handle availability in their own native fixtures. Seventy-seven
inspected frames establish sampled appearance, not exact decoded effect endpoints.

## Parameters and identifiers

The exercised transitions store bare values in `attributes`, including numeric
controls, booleans, and named RGB components. Color metadata expands to keys
such as `Color-red`, `Color-green`, and `Color-blue`, with normalized components.
Numbered colors retain their full names, such as `Color0-red`. A subsequent
native save can round numeric attributes to binary32 precision, including color
components and directional angles; preserve the saved values rather than
reconstructing them from a rounded display.

All exercised defaults retain `bypass: false`, `reverse: false`, `trivial: false`,
`useAudioPreRoll: true`, and `useVisualPreRoll: true`. Preserve those flags and
each preset's additional attributes. This fixture's unchanged continuous audio
does not establish the behavior of attached audio or trimmed media handles.
Whole-project comparisons also preserve global settings and opaque fields;
the only other differences are native `/metadata/ProjectThumbnail`,
`/metadata/commandCount/value`, and source `lastMod` updates. Record this
native bookkeeping separately from edits.

| Native UI label | Saved `name` |
| --- | --- |
| Accordion | `Accordion` |
| Action Wipe | `ActionWipe` |
| Angled Line Wipe | `AngledLineWipe` |
| Angled Sliders | `AngledSliders` |
| Animated Mosaic | `AnimatedMosaic` |
| Arrow Slice | `ArrowSlice` |
| Arrows | `Arrows` |
| Arrows Solid | `ArrowsSolid` |
| Bar Wipe | `BarWipe` |
| Barn Door | `BarnDoor` |
| Bars | `Bars` |
| Blinds | `Blinds` |
| Blob | `Blob` |
| Blob 2 | `Blob2` |
| Blur Zoom | `BlurZoom` |
| Bounce | `Bounce` |
| Box Iris | `BoxIris` |
| Bubbles | `Bubbles` |
| Bubbles 2 | `Bubbles2` |
| Burn | `Burn` |
| Burn Through Fade | `BurnThroughFade` |
| Bursting Heart | `BurstingHeart` |
| Card Flip | `CardFlip` |
| Card Flip Swap | `CardFlipSwap` |
| Card Slide | `CardSlide` |
| Card Swap | `CardSwap` |
| Cascading Squares | `CascadingSquares` |
| Cell Zoom | `CellZoom` |
| Center Slice | `CenterSlice` |
| Checker Board | `CheckerBoard` |
| Chevrons | `Chevrons` |
| Circle Bloom | `CircleBloom` |
| Circle Crop | `CircleCrop` |
| Circle Offset | `CircleOffset` |
| Circle Reveal | `CircleReveal` |
| Circle Slice | `CircleSlice2` |
| Circle Stretch | `CircleStretch` |
| Circles | `Circles` |
| Color Burn | `ColorBurn` |
| Color Distance | `ColorDistance` |
| Color Spin Door | `ColorSpinDoor` |
| Color Wipe | `ColorWipe` |
| Concentric Rings | `ConcentricRings` |
| Cross Zoom | `CrossZoom` |
| Cube | `Cube` |
| Cube Rotate | `CubeRotate` |
| Diagonal Move | `DiagonalMove` |
| Diagonal Slice | `DiagonalSlice` |
| Dial Wipe | `DialWipe` |
| Diamonds | `Diamonds` |
| Digital | `Digital` |
| Dissolve | `Dissolve` |
| Distorted Fall | `DistortedFall` |
| Doorway | `Doorway` |
| Drawbridge | `Drawbridge` |
| Drop | `Drop` |
| Drops | `Drops` |
| Expanding Squares | `ExpandingSquares` |
| Fade | `Fade` |
| Fade Through Black | `FadeThroughBlack` |
| Fall | `Fall` |
| Falling Hearts | `FallingHearts` |
| Fan | `Fan` |
| Flare | `Flare` |
| Flare 2 | `Flare2` |
| Flashback | `Flashback` |
| Flip | `Flip` |
| Fold | `Fold` |
| Fold Shut | `FoldShut` |
| Four Color Iris | `FourColorIris` |
| Four Color Wipe | `FourColorWipe` |
| Four Squares | `FourSquares` |
| Geometric Slice | `GeometricSlice1` |
| Glass Triangles | `BlurSlide` |
| Glitch | `Glitch` |
| Glitch 2 | `Glitch2` |
| Glitch 3 | `Glitch3` |
| Glow | `Glow` |
| Gradient Door | `GradientDoor` |
| Gradient Wipe | `GradientWipe` |
| Grid Flip | `GridFlip` |
| Growing Squares | `GrowingSquares` |
| Heart Flips | `HeartFlips` |
| Heart Offset | `HeartOffset` |
| Heart Pops | `HeartPops` |
| Hex Magnify | `HexMagnify` |
| Hex Spin Cascade | `HexSpinCascade` |
| Hexagonalize | `Hexagonalize` |
| Hexagons | `Hexagons` |
| Hitch Push | `HitchPush` |
| Horizontal Stretch 1 | `BlurStretch` |
| Horizontal Stretch 2 | `BlurStretch2` |
| Imploding Hexagons | `ImplodingHexagons` |
| Imploding Squares | `ImplodingSquares` |
| Inset | `Inset` |
| Interference | `Interference` |
| Inverted Page Curl | `InvertedPageCurl` |
| Inward Slice | `InwardSlice` |
| Iris | `Iris` |
| Jagged Wipe | `JaggedWipe` |
| Likes and Loves | `LikesNLoves` |
| Line Wipe | `LineWipe` |
| Linear Blur | `LinearBlur` |
| Luminance Fade In | `LuminanceFadeIn` |
| Luminance Fade Out | `LuminanceFadeOut` |
| Morph | `Morph` |
| Multiply Blend | `MultiplyBlend` |
| Noise | `Noise` |
| Opacity Squares | `OpacitySquares` |
| Page Roll | `PageRoll` |
| Page Turn | `PageTurn` |
| Paint Arcs | `PaintArcs` |
| Paint Drip | `PaintDrip` |
| Paint Strokes | `PaintStrokes` |
| Paint Swipe | `PaintSwipe` |
| Perlin Blobs | `PerlinBlobs` |
| Pixelate | `Pixelate` |
| Portal | `Portal` |
| Prism Wipe | `PrismWipe` |
| Purple Triangles | `PurpleTriangles` |
| Push | `Push` |
| Puzzle | `Puzzle` |
| Quarter Split | `QuarterSplit` |
| Radial Blur | `RadialBlur` |
| Radial Wipe | `RadialWipe` |
| Random Bars | `RandomBars` |
| Random Dissolve | `RandomDissolve` |
| Random Squares | `RandomSquares` |
| Rhombus Dots | `RhombusDots` |
| Ripple | `Ripple` |
| Rolling Squares | `RollingSquares` |
| Rounded Squares | `RoundedSquares` |
| Shatter | `Shatter` |
| Shifting Hearts | `ShiftingHearts` |
| Shockwave | `Shockwave` |
| Shuffle Slice | `ShuffleSlice` |
| Shutter Snap | `ShutterSnap` |
| Shutters | `Shutters` |
| Simple Zoom | `SimpleZoom` |
| Slam Shut | `SlamShut` |
| Slant Shutters | `SlantShutters` |
| Slide Left | `SlideLeft` |
| Slide Right | `SlideRight` |
| Sliding Bars | `SlidingBars` |
| Sliding Triangles | `SlidingTriangles` |
| Smileys | `Smileys` |
| Smooth Slide | `SmoothSlide` |
| Snapshot | `SnapShot` |
| Spin | `Spin` |
| Spin Flip | `SpinFlip` |
| Spin Views | `SpinView` |
| Spin Views 2 | `SpinView2` |
| Spin Zoom | `BlurSpin` |
| Spinning Blinds | `SpinningBlinds` |
| Spinning Color Wipe | `SpinningColorWipe` |
| Spiral | `Spiral` |
| Square Drops | `SquareDrops` |
| Square Pops | `SquarePops` |
| Squares Rotate Away | `SquaresRotateAway` |
| Static | `Static` |
| Stretch | `Stretch` |
| Strips | `Strips` |
| Swap | `Swap` |
| Swing | `Swing` |
| Swirl Spin | `SwirlSpin` |
| Tile | `Tile` |
| Transmission | `Transmission` |
| Unfold | `Unfold` |
| Vertical Offset | `BlurOffset` |
| Vortex | `Vortex` |
| Walking Wipe | `WalkingWipe` |
| Waves | `Waves` |
| Waves 2 | `Waves2` |
| Wheel | `Wheel` |
| Whip Spin | `SphericalSpin` |
| Zig Zag | `ZigZag` |
| Zoom Blur | `ZoomBlur` |
| Zoom Fade | `ZoomFade` |
| Zoom In | `ZoomIn` |

Card Slide retains bare `Depth: 1`, `Opacity: 1`, white `Color-*`, and black
`Background-*`. Inspected output shows rounded cards over black, with LEFT and
RIGHT stacked at the midpoint. Its decoded audio matches the continuous control;
its independent native reopen/rerender matches both first-export streams.

Card Swap uses the common flags without additional attributes in the observed
save. Inspected midpoint frames show displaced LEFT/RIGHT panels and thin
rectangular outlines. Its independent reopen/rerender and continuous-control
audio comparisons pass.

The native **Change the type of transition** control replaced the preset on
an existing shared boundary for Cascading Squares through Zoom In. It retained
the endpoints and duration while supplying the new preset's attributes. Clone
the resulting complete transition; changing only `name` does not supply those
native controls. The native menu label can differ from the identifier, as
Circle Slice's `CircleSlice2` demonstrates.

Observed defaults include `Number: 7` and `FlipX: false` for Cascading Squares;
`Number: 8` and `Random: 0` for Cell Zoom; `Columns: 12` and `Rows: 10` for
Checker Board; four numbered RGB colors and `FlipY: false` for Chevrons; yellow
`Color0-*` and black `Color1-*` for Circle Bloom; `Radius: 0.5` for Circle Slice;
and `Number: 3` for Circles. Other members of this group retain only the common
flags in the observed save. Inspected Circle Crop output closes to black at
the midpoint and then reopens onto the right clip.

Color Spin Door's Angle control displays `90.0º` while its initial native save
stores `1.5707963267949`. Its installed attribute metadata declares
`userInterfaceType: directional` and `unitType: radians`. A later native save
stores `1.57079637050629`, matching binary32 rounding of π/2. The independently
reopened native export is decoded-identical. Preserve the serialized radians
and their native precision; the displayed degrees are not the stored number.

Color Burn uses one RGB `Color-*`. Color Spin Door uses three numbered RGB
colors plus `Angle`; Color Wipe uses two numbered colors, `Angle`, `Feather: 0`,
and `Width: 1`. Dial Wipe retains `Clockwise: false`, `Number: 12`, and
`Random: 0`; Diamonds retains `Aspect: 0.5`, `Number: 5`, and `Random: 0`.
Diagonal Move additionally retains `FlipX: false`. The other presets in this
group retain the common flags without additional attributes in the saved sample.

Dissolve saves a two-component offset as bare `Offset.x: 0` and `Offset.y: 0`.
Digital adds `Random: 0`; Distorted Fall adds `Random: 0` and `FlipX: false`.
Drops retains `Number: 8` and `Random: 0`; Expanding Squares retains `Number: 5`
and both `FlipX: false` and `FlipY: false`. Fall uses `Number: 7` and `Random: 0`.
Falling Hearts uses red `Color0-*`, white `Color1-*`, `Number: 8`, and `Random: 0`.
Fade Through Black uses black `Color-*`. Doorway, Drawbridge, Drop, and Fade
retain the common flags without additional saved attributes.

Fan retains `Number: 6` and both flip flags false. Flare uses red `Color-*`;
Flare 2 uses a different RGB triplet. Four Color Iris saves four numbered RGB
colors and `Width: 40`; Four Color Wipe saves four colors, `Angle: 0`, and
`Width: 400`. Four Squares saves four colors, `Size: 0.25`, and an initial
`Angle: 1.5707963267949`. Its UI displays `90.0º`; native resaving stores
`1.57079637050629`, and its independent rendered streams match. Its installed
metadata marks Angle as directional without declaring `unitType`. Preserve
the observed native radians; do not infer every directional control's unit
from that UI classification alone.

Geometric Slice's native identifier is `GeometricSlice1`. Glass Triangles
saves as `BlurSlide` with `FlipY: false`. Installed English labels independently
match both mappings. Flashback, Flip, Fold, Fold Shut, and Geometric Slice retain
the common flags without additional saved attributes in these specimens.

Flare and Flare 2 cover the full canvas with a bright flash on this text-Callout
fixture. Flare is white at the join; Flare 2 is still white at 4.4 seconds. Extra
inspected frames at 4.6 seconds show RIGHT and the normal continuous background
for both. Account for that scene-wide appearance when choosing a transition;
the text clip's alpha bounds do not confine these observed flashes.

Glitch and Glitch 2 retain `Random: 0`; Glitch 3 retains one normalized RGB
`Color-*` triplet. Glow adds no controls beyond the common flags. Gradient Door
saves `Angle: 0`, lavender `Color0-*`, and dark-blue `Color1-*`. Gradient Wipe
saves `Angle: 0` and `Width: 0.2`; its native Width field displays `0.20` without
a percent sign. Grid Flip saves `Number: 4` and `Random: 0`. Growing Squares
retains four numbered gray RGB triplets.

Heart Flips saves black `Background-*`, magenta `Color0-*`, white `Color1-*`,
`Depth: 1.5`, `Number: 4`, and `Random: 0`. Heart Offset saves `Size: 0.7` and
`Vertical: true`; its native Size field displays `0.70` without a percent sign.
Heart Pops saves red `Color0-*`, white `Color1-*`, and `Number: 3`. Hex Magnify
saves `Number: 5`. Preserve each preset's saved units and color components;
similarly named controls need not share units across presets.

Inspected join frames show Glitch's horizontal fragments, full-canvas gray
static for Glitch 2, and black for Glitch 3. Gradient Door covers the join with
a blue/lavender gradient; Grid Flip adds a black grid; Growing Squares adds
bright overlapping panels. Heart Flips covers the join with purple hearts
over black; Heart Offset displaces letters vertically, Heart Pops adds red
hearts, and Hex Magnify divides letters through hexagonal regions. Scene-wide
coverage is part of these observed outputs even when endpoints are Callouts.

Hexagonalize saves `Number: 20`; Hexagons saves `Number: 3` and `Random: 0`.
Interference and Inverted Page Curl each save `FlipX: false`. The other presets
from Hex Spin Cascade through Inward Slice add no controls beyond the common
flags in the observed defaults. Horizontal Stretch 1 and 2 save `BlurStretch`
and `BlurStretch2`; installed English labels independently confirm both mappings.
Preserve those native identifiers rather than deriving names from UI text.

Inspected frames show Hex Spin Cascade's rotated letter fragments,
Hexagonalize's hexagonal cells, Hitch Push's labels moving to opposite edges,
and distinct imploding hexagonal/square fragments. Horizontal Stretch 1 clears
the visible text at the midpoint; Horizontal Stretch 2 stretches it into thin
horizontal streaks. Inset overlays differently sized labels. These observations
apply to the exercised Callout boundary and its default parameters.

Interference overlays the labels at the join; Inward Slice concentrates and
duplicates letter fragments. Inverted Page Curl curls the scene over black,
and its 4.4-second sample still shows RIGHT against black instead of the
continuous background. Separate inspected frames at 4.6, 5, 6, and 7.5 seconds
show the normal background again. Account for that scene-wide coverage rather
than assuming the Callout alpha bounds confine the curl. The tail's decoded
pixels need not equal the clean control even when the scene looks restored.

Jagged Wipe saves `Number: 12` and `Random: 0`. Likes and Loves saves as
`LikesNLoves` with four numbered RGB colors, `Number: 8`, and `Random: 0`.
Line Wipe saves black `Color-*`, `Angle: 0`, and `Width: 20`. Linear Blur saves
bare `Intensity: 2`; Morph saves `Intensity: 1`. Noise retains white `Color-*`
and `Random: 0`. Iris, both Luminance Fades, Multiply Blend, Opacity Squares,
and Page Roll add no controls beyond the common flags in these native defaults.
Installed English metadata independently confirms Likes and Loves' `LikesNLoves`
mapping. The four numbered colors remain separate; do not collapse them into
one generic color control.

Inspected samples show Iris exposing incoming-label fragments before the join,
Jagged Wipe revealing RIGHT at the join, and Likes and Loves covering the whole
scene with blue thumbs/red hearts. Line Wipe's default adds a vertical black
dividing line. Linear Blur softens the letters; Morph overlays warped/offset
labels. The two Luminance Fades and Multiply Blend leave distinct mixed or
fragmented labels. Noise adds white streaks across the scene, densest at the
join. Opacity Squares mixes the label regions, and Page Roll moves label
fragments across the boundary. These three-time samples do not establish the
complete shader algorithm or exact first/last changed frames.

Paint Arcs retains both `FlipX: false` and `FlipY: false`, plus `Random: 0`.
Paint Strokes retains `FlipX: false` and `Random: 0`; Paint Swipe adds both flip
flags, `Number: 10`, and `Random: 0`. Perlin Blobs saves `Number: 10` and
`Random: 0`. Pixelate's bare `Size: 50` is distinct from Heart Offset's `0.7`.
Prism Wipe saves `Number: 6`; Purple Triangles retains its RGB `Color-*` values.
Puzzle saves `Aspect: 1.2`, `Number: 18`, and `Random: 0`. Page Turn, Paint Drip,
Portal, and Push add only the common flags in these defaults.

Inspected frames show the paint/Perlin presets revealing different letter
fragments, and Pixelate reducing the midpoint label to large blocks. Portal
adds a bright irregular ring that expands across the scene. Prism Wipe and
Push move label regions toward opposite canvas edges; Purple Triangles overlays
large colored triangular regions. Puzzle adds piece outlines across the scene
and fragments the label. Its 4.4-second sample still has outlines; the three
samples do not establish the exact end of that coverage.

Random Bars and Random Dissolve retain `Random: 0`. Random Squares adds
`Number: 10`; Rhombus Dots saves `Number: 2`; Rounded Squares saves `Number: 5`.
Shatter saves `Number: 8` and `Random: 0`. Rolling Squares retains one RGB
`Color-*` triplet. Shifting Hearts retains separate `Background-*`, `Color0-*`,
and `Color1-*` triplets, `FlipX: false`, and `Random: 0`. Quarter Split, Radial
Blur, Radial Wipe, and Ripple add only the common flags in these native defaults.

Inspected samples show Quarter Split scattering label fragments toward the
corners, Radial Blur softening the text, Radial Wipe revealing different letter
regions, Random Bars adding horizontal breaks, and Random Dissolve adding fine
speckled fragments. Rhombus Dots overlays white dots across the scene. Ripple
warps the letters; Rolling Squares covers the midpoint with blue/purple panels;
Rounded Squares mixes rotated label regions, and Shatter displaces fragments.

Shifting Hearts replaces the scene with heart-shaped label windows over pink
and translucent circles. Separate tail samples at 4.6, 5, 6, and 7.5 seconds
show RIGHT over the normal moving background again. Decoded differences against
the control remain, including maximum 105 channel units at 7.5 seconds; visible
restoration does not establish exact effect-end timing or pixel equality.

Shockwave retains both flip flags as false. Shuffle Slice saves `Number: 4`
and `Random: 0`. Shutters saves `Number: 7`/`FlipY: false`; Slant Shutters saves
the same count with `FlipX: false`. Slam Shut and Slide Right each save `Angle: 0`.
Sliding Bars retains `Number: 6` and initial `Angle: 0.6`; Sliding Triangles
retains two numbered RGB colors and `FlipY: false`. Smileys saves three separate
numbered RGB triplets, `Number: 6`, and `Random: 0`. Shutter Snap, Simple Zoom,
and Slide Left add only the common flags in these native defaults.

Sliding Bars' native panel displays `34.4º` for the 0.6-radian default; its
installed directional metadata explicitly declares radians. A subsequent native
save retains `0.600000023841858`, matching binary32 rounding of 0.6. Preserve
that stored value rather than converting the rounded 34.4-degree display back
to radians: the unrounded equivalent is about 34.3774677 degrees. Its independent
native rerender matches both decoded streams.

Inspected samples show Shockwave's curved bright bands and warped letters,
Shuffle Slice's displaced fragments, and Shutter Snap reducing the scene to a
small hexagonal opening against white at the join. Shutters and Slant Shutters
reveal different label regions. Simple Zoom enlarges LEFT beyond the canvas;
Slam Shut and the two Slides displace or mix the labels. Sliding Bars cuts
diagonal fragments, while Sliding Triangles adds large pale triangular panels.
Smileys fills the join with yellow faces across the scene.

Separate Shutter Snap and Smileys tail samples at 4.6, 5, 6, and 7.5 seconds
show the normal moving background again. Shutter Snap's samples at 5, 6, and
7.5 equal the control's decoded pixels; its 4.6 sample still differs. Smileys
retains decoded differences at every sampled time. These samples establish
visible restoration without assigning an exact final transition frame.

Snapshot saves `SnapShot`, `Depth: 2`, `Angle: 0.1`, and `FlipX: false`.
Spin Views and Spin Views 2 save `SpinView` and `SpinView2`, each with both flip
flags false; Spin Zoom saves `BlurSpin`. Installed English labels independently
confirm all four mappings. Spin Flip retains `Blur: 4` and `FlipY: false`;
Spinning Color Wipe retains two numbered RGB colors and `Angle: 0`. Square Drops
saves `Number: 8` and `Random: 0`. Smooth Slide, Spin, Spinning Blinds, Spiral,
and Square Pops add only the common flags in these defaults.

Snapshot's native display is `5.7º`; its initial 0.1 angle resaves as
`0.100000001490116`, matching binary32 radians. The unrounded degree equivalent
is about 5.72957795, so converting the rounded display back does not preserve
the stored value. Its installed metadata marks the control directional but omits
`unitType`, and lists min/max 0 despite default/native 0.1. Do not turn those
metadata entries into a zero-only JSON range or clamp a native value to zero.
The actual native save/reopen/render and display support this observed angle.

Inspected samples show Smooth Slide's horizontal streaks, Snapshot's framing
corners and tilted white border, Spin's rotated/blurred letters, and Spin Flip's
tilted labels. Spin Views overlaps the labels; Spin Views 2 places smaller
rotated labels at different positions. Spin Zoom enlarges and smears the text
through a circular blur. Spinning Blinds fragments letters into bands; Spinning
Color Wipe covers the join with purple and blue panels. Spiral retains mixed
letter regions late in the sampled boundary; Square Drops and Square Pops
produce distinct broken label regions.

Separate Snapshot, Spinning Color Wipe, and Spiral tail samples at 4.6, 5, 6,
and 7.5 seconds show RIGHT over the normal background. Pixel differences against
the control remain in several samples. Use those observed results without
claiming exact final effect frames or continuous pixel equality.

Squares Rotate Away saves `Number: 5` and `Random: 0`; Strips retains bare
`Size: 6.5` and `FlipX: false`. Swing saves `Number: 4` and `FlipY: false`.
Tile saves `Number: 12`, `Random: 0`, and both flip flags false. This transition
is distinct from the ordinary visual effect `Tiling`. Transmission retains
`Random: 0`. Vertical Offset saves `BlurOffset`, independently confirmed by its
installed English label; Whip Spin saves `SphericalSpin` without a matching
definition file. Preserve these exact names rather than deriving them from labels.

Walking Wipe retains one RGB `Color-*` and `FlipX: false`. Waves retains two
separate numbered RGB triplets and both flip flags false; keep both colors even
when their defaults match. Waves 2 retains two numbered colors and initial
`Angle: 0.4`. Wheel saves `Number: 4`; Zig Zag saves `Rows: 5`; Zoom Fade saves
`Zoom: 2`. Static, Stretch, Swap, Swirl Spin, Unfold, Vortex, Whip Spin, Zoom Blur,
and Zoom In add only the common flags in these native defaults.

Waves 2 displays `22.9º` for its 0.4-radian default and natively resaves
`0.400000005960464`, matching binary32 rounding. Its installed directional
metadata explicitly declares radians. The exact mathematical degree equivalent
is about 22.9183118; do not replace the native value with a conversion of the
rounded display. Its independent native rerender and decimal-angle audit pass.

Inspected final-preset samples show rotating square fragments, scene-wide gray
noise for Static, narrowed letters for Stretch, and mixed strips for Strips.
Swap presents reflected scene panels against black; Swing moves the labels;
Swirl Spin adds circular warped streaks. Tile breaks letter regions; Transmission
warps and displaces them. Unfold folds the scene into planes against black.
Vertical Offset streaks the text vertically, while Vortex mixes warped letters.
Walking Wipe adds dark colored coverage; Waves overlays large pale waves, and
Waves 2 covers the midpoint with blue and a bright wavy line. Wheel and Zig Zag
break/reveal different letter regions. Whip Spin stretches them horizontally;
Zoom Blur smears them, Zoom Fade reaches a white midpoint, and Zoom In enlarges
outgoing letters across the scene while the incoming label is initially small.

Separate inspected tail samples for Static, Swap, Unfold, Walking Wipe, both
Waves, Zoom Fade, and Zoom In show the normal moving background and RIGHT at
4.6, 5, 6, and 7.5 seconds. Decoded differences remain in many samples, including
Static after its noise coverage. These observations do not establish the
internal cause of those differences or exact shader-end timing.

On this fixture, **Add to Selected Media** for the left Callout creates both
a one-sided start transition and the shared transition. A replayed native
Undo Add Transition removes both additions together. Inspect the actual array
after applying or undoing a preset; do not assume that one menu command adds one transition. The verified
Card Swap specimen retains only the shared transition after native removal of
the extra start transition.

The exact format-10 profile adds the 169 demonstrated identifiers absent from
the pinned community enum; `CardFlip`, `Fade`, `FadeThroughBlack`, `Glitch3`, `LinearBlur`, `PaintArcs`, `SlideLeft`, `SlideRight`, `Stretch`, and `SphericalSpin`
were already present. Other names,
property/type checks, and the exact editor-build match remain enforced.

## Installed metadata and verification

This installation exposes 179 UI presets and 148 files under
`<target-app>/Contents/Resources/Transitions/*.tsceffect`. These are different
inventories. The metadata's internal `name`, localized label, and attribute
declarations provide discovery clues; they do not establish that another
build can render the effect.

All 148 transition definitions are readable as data. Four use JSON5-compatible
trailing-point numbers such as `8.` and `0.`. The private verification used
JSON5 0.12.1, without evaluating shader strings or editing vendor files. The
three observed attribute types are `double`, `bool`, and `Color`. Native defaults
match every one of the 148 installed definitions. Barn Door,
Blinds, Checker Board, Circle Reveal, Circle Stretch, Cube Rotate, Dissolve,
Fade, Fade Through Black, Flip, Fold, Glow, Gradient Wipe, Inset, Iris, Page Roll,
Page Turn, Pixelate, Radial Blur, Radial Wipe, Random Bars, Random Dissolve,
Ripple, Slide Left, Slide Right, Spiral, Stretch, Strips, Wheel, Whip Spin,
and Zig Zag have native evidence
without corresponding installed definition files in this inventory.
Keep project JSON parsing strict. Metadata syntax does not authorize JSON5,
NaN, or infinities in a `.tscproj`. [JSON5 number syntax](https://spec.json5.org/#numbers)

Use a matching native sample and verify the requested parameters through
save/reopen, actual export, boundary frames, and audio. Follow the
[serialized native stability procedure](native-verification.md#serialized-native-work-and-stability).
The current evidence uses individual exports and retained native panels/outputs;
it does not reopen the affected Batch Export or Export History workflow.
Generated samples and vendor definitions remain outside the distributed plugin.
