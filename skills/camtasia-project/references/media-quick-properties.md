# Media Quick Properties

These contracts apply to Camtasia Mac 2026.2.4, format `10.0`, with a synthetic
640×360 linked AV source, a 64×64 synthetic theme logo, and the portrait/wide
AV inputs described below.
[Text/color controls](quick-properties.md) have separate binding and editing
contracts. Native cases verify AV/image replacement, clearing/restoration,
visibility controls, applied Logo mapping, AV/mixed-image linking and the
trimmed/styled lifecycle below. Shorter and differently sized AV replacements
have separate native fitting, duration and source-clock contracts below.

## Group and property identity

Grouping the eight-second `UnifiedMedia` creates a Group with one nested track,
visible bounds 640×360 and initially empty `attributes.assetProperties`.
The wrapper and both AV children retain their complete payload and local clocks
apart from their newly allocated IDs. The native Quick Property Editor lists
the source under Available Properties. Adding it creates:

```json
{"type": 2, "name": "source", "objects": [4]}
```

The integer identifies the **UnifiedMedia wrapper**, not its video child,
audio child or source-bin entry. Renaming it to Footage changes only the label.
Native source import subsequently allocates source ID 2, moves timeline ID 2
to 3, and maps Group/wrapper/video/audio IDs from 3/4/5/6 to 4/5/6/7.
The property binding becomes `[5]`. Keep an explicit complete native ID map;
discarding IDs during comparison would hide broken bindings.

## Native video replacement

Dragging the imported twelve-second synthetic movie onto the Footage thumbnail
replaces both video and audio source references with source ID 2. The wrapper,
stream children and Group keep their eight-second used intervals and source
start zero. No twelve-second timeline extension occurs. The video ident becomes
`replacement-12s`, and its four zero crop parameters become static double
descriptors with `defaultValue: 0`, `interp: "eioe"`.

Native replacement replaces the wrapper's metadata with five typed doubles:

| Metadata key | Native value in this fixture |
| --- | --- |
| `originalMediaWidth` | `640` |
| `originalMediaHeight` | `360` |
| `originalMediaQuickPropertyDuration` | `5644800000` |
| `previousReplacementWidth` | `640` |
| `previousReplacementHeight` | `360` |

Each entry is `{"type":"double","value":...}`. The duration is eight seconds
at 705600000 project ticks/second, not eight seconds represented as `8`.
The original wrapper's default-scale, effect-label, lock-aspect and other
metadata entries are absent after this native operation. Preserve the original
project when those values matter; dropping the old source back does not restore
the old metadata. Do not extend this observed owner replacement to unrelated
Group, source, stream or unknown payload. This fixture has no active effects;
arbitrary processing retention requires its own styled-media probe.

A computer-use drag landed on the canvas and added a separate twelve-second
clip instead of replacing the property. The retained negative capture was undone
and strict whole-document comparison confirmed restoration before the guarded
native drag. Verify the actual property, lane count and duration after a drop;
selection or a new canvas object is not replacement evidence. Coordinates must
come from the current window, after any display/window placement change.

## Clear, restore, remove and re-add

The thumbnail's X clears the media. It replaces the AV wrapper with a **Callout**
at the same bound child ID, not `PlaceholderMedia`. The native definition is a
Bold `shape-rectangle` with transparent black fill, zero stroke, dimensions
640×360 and static double descriptors using `interp: "linr"`. It retains the
eight-second bounds and replacement metadata. The video/audio children are gone;
the source-bin entries remain. The Group and its type-2 binding remain intact.
Rendering over the project's black canvas shows empty black output, with silence
in both sampled audio channels. The UI exposes Import File on the empty thumbnail.

Dropping the original source into that control creates linked AV again at the
bound wrapper ID and restores both source references to ID 1. It retains the
eight-second bounds, replacement metadata and static zero crop descriptors.
This restores the source content, not the complete pre-replacement wrapper state.

Removing the Quick Property in the Editor clears its visible entry without
clearing the child media. Re-adding the source restores `type: 2`, the native
default label `source` and the current child binding, with no `themeMappings`.
Picture, audio, timing and current metadata remain unchanged.

## Logo mapping, application and images

The native theme menu offers Logo. Assigning it saves the unusual literal
mapping `"themeMappings": {"logo-1":"logo-1"}`. With no theme applied, this
changes no source references or content and adds no applied Group theme ID.

Applying the synthetic theme imports its 64×64 PNG into a new bundled source.
The native source has one still track: `type: 1`, `editRate: 600`, `range: [0,1]`,
64×64 `rect`/`trackRect`, sample rate/channels zero. The bound AV wrapper becomes
an `IMFile` with the same eight-second used duration, source start zero and
`mediaDuration: 1`. Its audio/video children disappear. Image `scale0` and `scale1`
are both `5.625`, producing a centered 360×360 picture in the retained 640×360
Group. Do not stretch the square to fill the Group. Replacement metadata retains
original dimensions 640×360/duration eight seconds; previous replacement size
becomes 360×360. The Group gains `metadata.AppliedThemeId`.

The native import renumbers timeline/Group/bound child from 3/4/5 to 4/5/6,
and the property binding becomes `[6]`. Reapplying after clear imports a second
PNG source even though its bytes match the first. Reapplying after direct video
replacement imports a third. Each gets its own native source ID, bundle path and
time-added metadata; earlier entries remain. Preserve these entries and explicit
ID/binding remaps instead of deduplicating them during JSON comparison.

Clearing this image creates a transparent Bold rectangle Callout at its bound ID.
Its intrinsic definition is 64×64 and retains scale `5.625`, rather than adopting
the earlier AV clear's 640×360 definition. The Group, mapping and applied theme ID
remain. The control displays Select Theme even though that ID remains saved.
Output over black is empty and silent. Reapplying the theme restores the image.

Removing the image property retains its concrete picture and saved theme ID.
Re-adding uses the default label `theme-fixture-logo`, `type: 2`, the integer image
child ID and no theme mapping. Assigning Logo restores the mapping without
importing another source or changing the image. Removing/re-adding does not
recover the old custom label/mapping automatically.

Dropping the twelve-second AV source onto the mapped image property creates
linked `UnifiedMedia` again. It uses eight seconds from source start zero, with
new video/audio children at the following IDs, scalar one and the demonstrated
static crop descriptors. The image scale is absent; the 640×360 video fills the
original bounds, both streams reference source ID 2, and previous replacement
dimensions become 640×360. The saved Logo mapping and applied theme ID survive,
while the UI displays Select Theme. Applying the theme again replaces AV with
the logo and removes its audio. UI theme text alone is not a saved-state check.

## Linked AV properties and independent edits

A separate native Group contains two eight-second AV wrappers on distinct
nested lanes: IDs 5 and 8, each with video/audio children. Both videos are
scaled to 320×180 and translated to X −160/+160 in the retained 640×360 Group.
Adding each Available Property creates separate type-2 entries with integer
wrapper IDs. Native default labels follow the current media's ident; renaming
them First Footage and Second Footage changes no media payload.

Assigning Logo to the second entry without applying a theme adds only its
mapping. Linking the second entry to the first produces:

```json
{"type":2,"name":"First Footage","objects":[5,8],"themeMappings":{"logo-1":"logo-1"}}
```

The **first label and source win; the second mapping wins** in this exercised
case. Both video/audio pairs now reference source 1, with native video ident
`source`. Separate translations/scales and eight-second local clocks remain.
Linking materializes seven static double/eioe descriptors per video: translation
X, both scales and four crops. It extends each wrapper's existing metadata with
the five replacement fields, using visible size 320×180 and eight-second ticks.
It does not discard the old wrapper metadata during this linking operation.

Dropping source 2 onto the linked control replaces both AV pairs. This actual
thumbnail replacement retains only the five replacement metadata fields,
with the same visible dimensions. Both sound contributions switch too. Clear
creates two transparent 640×360 Bold Callouts, each retaining scale 0.5 and its
own translation, with no AV children. The second bound ID changes from 8 to 6;
the linked property becomes `[5,6]`. Restoring source 1 recreates the wrappers
and their video/audio children, expanding the second bound ID back to 8.
Update all affected bindings when a native type change reallocates later IDs.

Unlink duplicates the shared First Footage label and Logo mapping into separate
`objects: [5]` / `[8]` properties. It retains the current picture/audio, rather
than recovering the second clip's pre-link source, label or mapping. Replacing
the first then changes only the first AV pair. Removing the second property's
visible entry retains its media; re-add uses default label `source`, its current
wrapper ID and no mapping. Independent clear/restore and replacement of the
second control preserve the other clip. Clearing only the first also renumbers
the untouched second wrapper and its property binding until restoration.

One restore drag only selected a Media Bin source; another attempt produced a
native media-deletion confirmation. Cancel preserved the complete saved project
apart from allowed bookkeeping. Both observations remain negative evidence.
After normal Quit/restart and native window placement, the restore succeeds.
Verify actual source/type/binding changes after a drop; neither selection nor
an attempted operation establishes success. The later export pair includes the
successful native restore. No deletion or repeated source import was accepted.

Fifteen saved cases form a 120-second native sequence. Independent exports
before/after reopen match complete decoded video/audio. All thirty frames in
eight contacts are inspected. References use the earlier independently accepted
native source renders, resized into the two fixed slots; they retain Camtasia's
source-color interpretation. Raw decoded source colors differ and are not a
native compositing reference. The fixed picture checks retain their original
bounds; they are not an arbitrary color-calibration or source-pixel-equality claim.
Sixty audio windows check both channels for distinct-source mixtures, two
in-phase copies of either source, one remaining clip, and complete silence.
Source/native tone amplitudes remain distinct from PCM identity.

Evidence is `quick-media-pair-sequence-comparison.json`, its fifteen native
captures and `media_link_contract.py`. Four staging, ten lifecycle, four picture
and four audio-mixture tests protect these contracts. Both source hashes and
raw/profile schemas pass unchanged. The mixed image/AV probe below extends this
evidence; styled/trimmed/shorter-source replacement behavior retains separate cases.

## Mixed image/AV linking and mapping loss

Mac 2026.2.4 / format 10 also saves fifteen mixed-media states. The original
Group uses two 320×180 replacement boxes, with a 64×64 image fitted to 180×180
on the left and 640×360 AV scaled to 320×180 on the right. Image scale is 2.8125;
video scale is 0.5; translations remain −160/+160. The image's source hold is
`mediaDuration: 1`, while its used duration remains eight seconds. AV wrapper,
video and audio retain their separate eight-second local clocks.

Native Add creates two type-2 integer bindings, default names
`theme-fixture-logo` and `replacement-12s`. Renaming them First Image and
Second Footage changes only labels. Assigning Logo to the second adds its
mapping without importing a source. Linking replaces the second AV with the
first image, removes its audio, and saves one First Image entry with
`objects: [8,9]` and `themeMappings: {"logo-1":"logo-1"}`. Both images fit their
own original boxes; neither stretches to 320×180. Seven static double/eioe
geometry descriptors materialize per image. Previous replacement width is 180,
while original width remains 320; height remains 180 in both metadata fields.

Dropping AV onto the linked control creates two wrappers and both stream pairs.
Bindings expand to `[8,11]`; video/audio IDs are 9/10 and 12/13. Both source IDs
switch to 1, scales become 0.5, and previous replacement width becomes 320.
The shared label/mapping, original boxes, translations and used duration remain.
Clearing creates transparent 640×360 Bold rectangle Callouts, with scale 0.5
and bindings `[8,9]`. Restoring the bundled image creates two 64×64 IMFiles
with scalar 2.8125 geometry, image holds and previous width 180. No AV children
remain. No new source entry or theme application is needed for these bin drops.

Unlink duplicates the shared label and mapping into two entries while retaining
both current images. Independent first-image replacement changes only its slot
to AV source 2 and renumbers the untouched second image/binding to 11. Removing
the second visible property retains that image; re-add restores its default
name and current integer binding with **no mapping**. Replacing the second image
with AV source 1 then replacing the first AV with the image leaves separate
image/video slots and remaps the second binding back to 9.

Linking these entries again retains the first image/label, but **removes the
first Logo mapping when the second entry has no mapping**. The native result is
`{"type":2,"name":"First Image","objects":[8,9]}`. Do not preserve the first
mapping by assuming an absent second mapping means no change. The exercised
mapped-second and unmapped-second cases both establish second-entry precedence;
they do not establish arbitrary multi-entry merge behavior.

The retained native captures include an incidental Group translation X=1/Y=2
from window-placement keystrokes before the linked-video case. The comparison
sequence explicitly removes only those two known values, retaining source
captures and all child geometry. Never normalize arbitrary Group movement or
unknown geometry out of project comparisons.

`quick-media-mixed-sequence-comparison.json` binds all fifteen native captures,
a two-minute save/reopen/export pair with identical complete decoded video/audio,
30 inspected pictures beside independent native image/AV controls, and 60
both-channel audio windows. Square fitting, wide-video slots, silence, one AV
contribution and two distinct/identical AV contributions remain separate checks.
Five bundled source hashes remain unchanged. Fresh native save collapses 84
known static geometry descriptors and 14 clear-definition descriptors, and adds
two zero corner radii. Unknown/keyframed payload stays strict. Four staging,
eight lifecycle and three mixed-picture fixed tests protect the added contracts.
Raw/profile schemas pass unchanged. This evidence covers the demonstrated
mixed-media boxes; styled, trimmed, shorter and differently sized source
replacements require their own probes.

## Trimmed and styled replacement

Mac 2026.2.4 / format 10 has ten additional native states for a four-second AV
use originally starting two seconds into its source. The Group starts at zero;
wrapper/video/audio `mediaStart` is 1411200000 and used duration/mediaDuration
is 2822400000 at this project's tick rate. Child video scale is 0.75 with
translation X=32/Y=−16 and opacity 0.75, producing a 480×270 inset. Audio-child
`attributes.gain` is 0.25. The type-2 Styled Footage property binds wrapper 8.

Native Colorize application adds matching effects to wrapper and video child.
Both use `effectName: "Colorize"`, `category: "categoryVisualEffects"`, green
RGBA (0,1,0,1), `amount` 0.5, mode/channel 0 and the native ramp controls.
Typed static double/linr values carry the native UI hints. The wrapper gains
`default-Colorize-amount: "1"` and its effect label; Group lock-aspect and
opened-lane metadata additions remain distinct from effect payload.

Replacing the property with AV source 2 preserves four-second use, both effect
mirrors, opacity, scale, translation and audio gain 0.25. It **resets source
start to zero** on wrapper, video and audio. Returning source 1 also starts at
zero; it does not recover the original two-second trim. Wrapper metadata is
replaced with the five typed replacement fields, original/previous dimensions
480×270 and original used duration 2822400000. Geometry becomes eight static
double/eioe descriptors; opacity becomes a static double/linr descriptor.
Do not retain an old source offset merely from the unchanged used duration.

Clear creates a transparent 640×360 Bold Callout, retaining the Colorize effect,
scalar 0.75 geometry/opacity, translation, four-second use and replacement fields.
AV children disappear. Restoring source 1 recreates both streams with the
retained visual treatment, but **audio gain becomes 1.0**. The former gain 0.25
belongs to the removed audio child; clear/restore does not recover it. Recheck
sound level after restoring media even when the picture looks unchanged.

Replacing AV with the bundled square image preserves Colorize, opacity and
translation. Scale 4.21875 fits 64×64 to 270×270 inside the original 480×270 box;
`mediaDuration` becomes the still hold 1 and there is no audio. Returning AV
source 2 restores 480×270 video and audio gain 1.0, retaining the visual effect.
Removing/re-adding the visible property changes no processing or media, and
re-add uses default label `replacement-12s` with the same binding and no mapping.

A separate 72-second native sequence includes these ten captures and eight
controls built by direct edits of the original AV/image constructors, without
Quick Property replacement. The controls distinguish source offsets zero/two,
plain/green treatment, quarter/unity gain and square image fit. Both exports
before/after native reopen have identical complete decoded video/audio. All
36 sampled native frames and 20 case/reference comparisons are inspected in
seven contacts. Six measured plain/green comparisons verify visible color change;
72 audio windows verify both channels, source identity, quarter/unity gain and
image/clear silence. Picture checks retain complete control comparisons and
allow the observed H.264 ringing footprint around otherwise black inset edges.
These are bounded synthetic checks, not general perceptual or audio calibration.

Fresh native save collapses 54 demonstrated geometry/opacity descriptors,
225 static Colorize descriptors across the retained mirrors, and seven cleared
rectangle descriptors; it adds one zero corner radius. Unfamiliar/keyframed
payload stays strict. All five source hashes and 66 storage-order clip nodes
remain checked. The pinned upstream schema omits Colorize; the exact format-10
profile adds only that identifier. Other effect identifiers, field types,
unknown properties and editor identities retain their restrictions.

Evidence is `quick-media-styled-sequence-comparison.json`, its ten native
captures, independent control construction and tested `media_styled_contract.py` /
`media_styled_render_contract.py`. Four staging, eight lifecycle, seven render
and one exact-profile tests protect the addition. This probe covers Colorize,
static opacity/gain and a trim; it does not establish arbitrary effects, animated
processing. The following probe separately covers short and differently sized AV.

## Short and differently sized AV

Mac 2026.2.4 / format 10 saves ten states for a four-second Group and a type-2
Size Footage property bound to wrapper 7. Original 640×360 video uses scale 0.75,
translation X=32/Y=−16 and visible bounds 480×270. Source starts are zero;
this probe has no active effects. Both imported sources have native constructors:

| Input | Source dimensions | Length | Source-track edit rate / range | Audio sample rate |
| --- | --- | --- | --- | --- |
| Portrait | 320×480 | 2 seconds | 96000 / `[0,192000]` on both streams | 32000 |
| Wide | 960×320 | 6 seconds | 22050 / `[0,132300]` on both streams | 22050 |

The portrait source's track clock differs from its audio sample rate. Preserve
each native `editRate`, `range` and `sampleRate`; do not substitute one clock
for another or infer a universal clock formula from this example.
Native imports append source IDs 3 and 4, increment timeline/Group/clip IDs,
and update the property binding after each import. Source-bin IDs share the
project ID namespace; include them when checking unique IDs and remapping.

Replacing with the portrait keeps wrapper/video/audio IDs 7/8/9 and changes both
stream source IDs to 3. It fits to **180×270**, scale 0.5625, at the retained
translation. Wrapper and both children clamp `duration` and `mediaDuration` to
1411200000, two project seconds. The Group remains four seconds. The output
shows picture/audio before two seconds, then black picture and silence at the
sampled 2.5/3.5-second positions. It does not hold, stretch or loop this source.

Replacement metadata retains original dimensions 480×270 and
`originalMediaQuickPropertyDuration: 2822400000`, four project seconds;
previous replacement dimensions become 180×270. All five entries are typed
doubles. Replacing the portrait with the six-second wide source restores
**four seconds** on wrapper and both children, using the remembered original
duration. Scale 0.5 fits it to 480×160. Translation and original box remain;
previous replacement dimensions become 480×160. Only four source seconds are
used. Returning the original source restores scale 0.75 and 480×270.

Clearing the short portrait creates a transparent Bold rectangle Callout with
intrinsic definition 320×480, scale 0.5625 and the retained translation and
replacement metadata. Its duration/mediaDuration returns to **four seconds**,
rather than retaining the short AV's two seconds. AV children disappear.
Restoring portrait clamps back to two seconds; restoring wide returns to four.
Removing/re-adding the visible property retains media, timing and fit; re-add
uses default name `source`, binding `[7]` and no theme mapping.

Three directly edited controls and ten native states form a 52-second sequence.
Two fresh native exports, separated by save/reopen, have identical complete
decoded video/audio. All 52 native frames, 40 case/reference comparisons and
four raw-source previews are inspected in twelve contacts. Both channels have
104 measured tone/silence windows distinguishing 440/880/1100 Hz sources and
the short source's late silence. Raw previews verify source content; direct
native controls supply the picture comparison. Bounds, fit and complete frame
comparison remain separate from raw-source color interpretation.

Both imports stalled after writing their new source to autosave. Each exact
hung editor PID was sampled, its recovery bytes preserved, and native recovery
retained the import without repeating it or changing cloud configuration.
Both samples show the documented OneDrive-check/file-read stack, without
identifying the blocked path. After Save bundled the sources and normal Quit,
the two owned originals were recoverably archived. The editor was restarted
before the export pair, with original import paths absent. All four bundled
source hashes remain unchanged. This proves dependency closure for these files.

Native resave collapses 64 exact static geometry descriptors and seven cleared
definition descriptors, adding one zero corner radius. All 50 clip nodes,
bindings, clocks and unfamiliar payload remain strict. Raw/profile schemas pass
without new corrections. Evidence is `quick-media-size-sequence-comparison.json`,
its native import/recovery captures and tested `media_size_contract.py`,
`media_size_closure.py` and `media_size_render_contract.py`. Four staging, eight
lifecycle, two archive-guard and four rendering tests protect these additions.
These two finite inputs establish the demonstrated short/portrait/wide behavior;
other codecs, aspect ratios and animated processing need their requested checks.

## Native resave and bundled image closure

Fresh native reopen collapses the demonstrated static zero crop descriptors to
scalar zeros. The cleared Callout's seven static definition descriptors collapse
to their numeric defaults, and the editor adds `corner-radius: 0`. The sequence
comparison permits only these demonstrated changes plus the existing three
bookkeeping fields. Keyframed or unfamiliar descriptors retain strict comparison.
All source files, other payload, bindings and clocks remain under comparison.
The image clear has its own exact 64×64 static-definition collapse; its scale
and replacement metadata remain unchanged. Unknown/keyframed definitions are
not covered by these demonstrated static changes.

The two-AV sequence additionally collapses its demonstrated static translation
X and scale descriptors to scalars. Only the exact known values and complete
descriptor shapes qualify. Its fresh native save collapses 126 geometry
descriptors, 21 cleared-definition descriptors and adds three zero corner radii.
Keyframes, unfamiliar descriptor fields and all other payload stay strict.

Nine native Logo states supply a separate 72-second sequence with all five
source entries and 22 clip nodes. Independent pre/post-reopen exports reproduce
complete decoded video/audio exactly. Eighteen frames in five contacts are
inspected; measured color quadrants, black center and sidebars verify the fixed
square fit. Thirty-six audio windows check both channels: original/replacement
tones in the two AV states and silence in all image/cleared states.

After normal Quit, the two owned synthetic theme files are recoverably archived
and preexisting user theme bytes remain unchanged. A fresh editor process opens
the project and renders a third movie with the original theme and logo import
paths absent. Its complete decoded video/audio matches the earlier exports.
All three bundled PNG copies retain the original hash. This proves saved-image
closure for the exercised fixture; applying a theme again still requires its
theme resources. Mixed linking is covered above; arbitrary image/effect sizing
remains separate.

## Import recovery and verification

The native File → Import Media operation stalled in
`SourceManager.autoProxyFilesIfNecessary` → `NSURL(CloudDrive).isOnOneDrive` →
dictionary-file read → filesystem `open`. The sample does not identify the read's
path or establish that the movie is cloud-hosted/corrupt. Process/privacy health
remained normal while UI observations timed out. The saved project stayed intact.

The disposable hung process was selected by exact PID in native Activity Monitor
and force-quit. The project helper then refused an offline candidate after finding
nonempty `~project.tscproj`. That recovery snapshot contained the native import.
Its bytes were retained; native Project Recovered → Open reopened the unsaved
changes, and Save bundled the imported source. No import was repeated and no
cloud configuration changed. A new exact-build PID and later normal Quit were
verified. Preserve recovery data and use the [native recovery procedure](native-verification.md);
never erase a live/recovery file to bypass the closed-project guard.

Three initial native constructors verify Group/add/rename ownership. Seven
later lifecycle captures supply a 56-second sequence. Native save/close/reopen
and independent exports reproduce complete decoded video/audio exactly. All
fourteen native frames are inspected beside original/replacement/empty controls.
Twenty-eight audio windows check both output channels: original 440 Hz,
replacement 660 Hz, and cleared silence. These are bounded source/silence checks,
not original-source PCM equality or perceptual-quality calibration.

The recovered source's full constructor is checked against the accepted import
baseline, with its observed path/time/ID allocation and the exact fresh analysis
peak retained separately from the older converted source's peak. Both bundled
source hashes remain intact. Raw community schema and the existing exact-build
profile pass without corrections. Five constructor/source-staging tests, nine
replacement/resave tests and three audio-window tests protect these contracts.

Repository evidence is `build/native-verification/quick-media-sequence-comparison.json`,
the native captures, recovery/negative-drop observations, tested
`quick_media_contract.py` / `quick_media_replacement_contract.py`, and
`quick-media-import-recovery.json`. Generated media, native UI helpers and app
binaries remain outside the distributed plugin.

Applied Logo evidence is `quick-media-logo-sequence-comparison.json`, the nine
`quick-media-logo-*-native.json` captures, `quick_media_logo_contract.py` and
`media_logo_frame_contract.py`. Ten constructor/resave tests and four image/clear
frame tests protect the added contracts. Both raw/profile schema checks pass
without corrections. Five closure-guard tests reject changed output, stale
processes, invalid export observations and remaining original theme resources.
