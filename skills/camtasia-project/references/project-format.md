# Project format map

This is a working map, not TechSmith's specification. Evidence and upstream
links are in [sources](sources.md). Match the format and authoring-client build
before reusing any structure.

## Native numeric precision

A native Mac 2026.2.4 WebM import writes
`sourceBin[].sourceTracks[].integratedLUFS: -1.79769313486232e+308` for its
silent audio track. This is a finite JSON decimal beyond binary64's negative
range; an ordinary floating-point JSON parser turns it into negative infinity.
The same decimal also occurs in a native 2025.0.3 stitched-media save.
The files do not contain a literal `-Infinity` token. Preserve the original
decimal as opaque loudness metadata. It is not a time, zero loudness, or a
reason to permit arbitrary infinities. The shipped reader and candidate encoder
handle the observed value; see [the helper contract](helper.md).

## Containers and identity

Imported Lottie JSON is a media source inside a project, separate from the
project document. Native `VMFile` instances retain source-level color definitions
and per-clip dynamic color overrides; see [Lottie clocks and ownership](lottie.md).
Group [Quick Properties](quick-properties.md) bind child clip IDs through
`attributes.assetProperties[].objects`; native ID reallocation must update those
references along with the clips. Lottie colors use `{media, property}` bindings;
native Text/Callout properties use integer child IDs. Type-2 [media properties](media-quick-properties.md)
bind the AV wrapper or image child, and clearing creates a transparent Callout
at that bound ID. Styled replacement retains the exercised Colorize/opacity but
resets source offsets; clear/restore recreates audio with unity gain. Applied Logo replacement imports a bundled still source;
native source/clip ID reallocation also updates the integer property binding.
Linked image/AV properties can bind either current child type; relinking with
an unmapped second entry removes the first mapping. Two linked AV properties
use one integer list containing both wrapper IDs;
clear/restore can renumber later wrappers and their bindings as AV children
disappear/reappear. Linking and actual replacement have distinct metadata owners
in the media contract. Short AV replacement can clamp wrapper/stream durations
while retaining the Group duration; longer replacement restores the remembered
original use. Preserve the separate source edit rate and audio sample rate;
the native portrait example uses 96000 and 32000 respectively.
Rich text ranges use UTF-8
byte offsets and may override the retained default font definition. The native
Quick Property Editor and direct typography path produce different demonstrated
five- and eight-property rich sets; preserve the actual set and its unknown data.

A Mac `.cmproj` bundle contains `project.tscproj`; saved working bundles also
have `bookmarks.plist`, `docPrefs`, and media/recording directories. Preserve
these companions. Windows and exported interchange projects may expose a
standalone `.tscproj`. Legacy `.camproj` is a separate historical format; open
and migrate it through the editor rather than treating it as current JSON.

Root fields observed locally include `width`, `height`, `version`, `editRate`,
`videoFormatFrameRate`, `audioFormatSampleRate`, `authoringClientName`,
`sourceBin`, `timeline`, and `metadata`. The file's `version` is not the product
year: `port-demo` saves format `9.0` from Camtasia 2025. The researched community
library targets another format, `10.0`; its constraints must not be imposed
unchanged on the demo. The installed app's theme demonstration is older still.
A fresh native empty project omits `sourceBin`; absence is not itself corruption.
The tested corrections and audit commands are in
[native verification](native-verification.md).

## Sources and lanes

- Source-bin entries identify underlying assets. Clip `src` points to an entry's
  integer `id`; the entry's `src` is a file path.
- Source `rect` and `sourceTracks[].trackRect` describe dimensions. Each stream
  has its own `editRate`, `range`, `type`, `sampleRate`, and metadata.
- Clip `trackNumber` selects a source stream. Timeline `trackIndex` selects a
  lane; these are separate indices.
- Traverse `timeline.sceneTrack.scenes[].csml.tracks[].medias` and nested
  containers. Keep track display/mute/visibility attributes in sync when
  changing lane structure.
- Generated/shader assets may carry source-level definitions and extra files;
  a file path alone does not describe their dependency graph.

Mac 2026.2.4 rejected simultaneous Callout panels/titles on one scene lane
with `Collision exception.` Separating concurrent layers onto different tracks
allowed the same vertical edit to open, save, reopen and render. Adjacent clips
may share an endpoint, and lanes may contain gaps. Do not flatten linked AV
children into scene lanes: their matching wrapper/child intervals are intentional.
The helper's exact-build parser guard checks known scene-lane clips; nested
container and unfamiliar-build semantics remain separate.

## Clip families

| JSON `_type` | Role and edit consequence |
| --- | --- |
| `VMFile`, `AMFile` | Video/audio referencing source streams. Preserve stream selection. |
| `IMFile` | Still image or held frame; timeline duration can exceed a one-tick source hold. |
| `ScreenVMFile`, `ScreenIMFile` | Moving/frozen screen-recording variants; retain cursor and recording metadata. Frozen `mediaStart` selects the held source frame independently of its local animation clock. |
| `UnifiedMedia` | Linked `video` and `audio` objects with independent parameters/effects and wrapper timing. |
| `StitchedMedia` | Child `medias` plus wrapper timing/effects; retain internal offset and trim fields. |

Native recording holds may have `mediaDuration: 1`, a long virtual child duration
clipped by their StitchedMedia parent's visible duration, and negative cursor
point times. Preserve those values; see [frozen animation owners](animations.md#frozen-and-stitched-owners).
| `Group` | Nested `tracks`; children can layer and inherit group transformations. |
| `Callout` | Annotation definition in `def`, including rich text and shapes. |
| `Caption` | Native imported closed captions with `parameters.captionData`; independent of audio-child captions. Current VTT/SAMI and earlier SRT forms are in [captions](captions.md). |
| `PlaceholderMedia` | Template placeholder; replacing it requires the target clip type and its dependencies. |

These families are corroborated by local projects or the upstream
[clip ontology](https://github.com/grandmasteri/pycamtasia/blob/443a41e37cddb460c0aa6e046c951cb17f241bf3/docs/concepts/clip-ontology.md).
Unknown types remain opaque data until probed.

## Clock domains

`start` and `duration` place a clip on its parent timeline. `mediaStart` and
`mediaDuration` describe the used source interval in the clip representation.
Convert to an actual source stream using that stream's own rate. Preserve
rational strings where present. Never use the source stream's numeric range
as project ticks without conversion.
Parameter keyframes need their own clock identification: source ownership
does not automatically make a transcription parameter sample-timed. See the
native word-clock measurement in [captions](captions.md).

The community timing implementation represents `scalar` as the inverse of
playback speed: a two-times-speed clip uses `1/2`. Validate this against a
same-version speed-change save before generating a new variant. The native
speed-change probe in this session retained that inverse representation. Still holds,
stitched offsets, linked children, and subframe audio need separate handling.
Do not enforce `mediaDuration == duration` or nonnegative starts on every child.
See upstream [timing observations](https://github.com/grandmasteri/pycamtasia/blob/443a41e37cddb460c0aa6e046c951cb17f241bf3/docs/concepts/timing.md).

A native Mac 2026.2.4 split of an eight-second, scalar-one `UnifiedMedia` at
four seconds mirrors timing on its wrapper, `VMFile`, and `AMFile`. With
`editRate: 705600000`, all three left nodes have `start: 0`, `mediaStart: 0`,
`duration: 2822400000`, and `mediaDuration: 2822400000`. All three right nodes
have `start: 2822400000`, `mediaStart: 2822400000`, and the same four-second
durations. Wrapper and child IDs are distinct, and the right pair retains the
original source ID and processing. Do not add these mirrored wrapper/child
positions together or divide them directly by the source's 48000 Hz clock.
This observation applies to the exercised scalar-one split, not every nested
container or retimed clip.

Uncut and split projects each reproduce their own native video/audio after
reopening. The split's video equals the uncut control, while native lossless
audio differs from the join onward. Do not promise sample-identical audio
from unchanged processing objects alone. Read the measured
[split audio controls](audio.md#splits-and-transition-audio) and
[linked-AV transition flags](transitions.md#linked-av-and-trimmed-content).

Native changing-tone controls on Mac 2026.2.4 independently verify the following
incoming-clip intervals. Times are seconds obtained from the `705600000`
project clock. Wrapper/video/audio retain matching time fields and `scalar`.

| Control | `start` | `mediaStart` | `duration` | `mediaDuration` | `scalar` |
| --- | --- | --- | --- | --- | --- |
| Four-second native split | 4 | 4 | 4 | 4 | 1 |
| Native trim leaving a gap | 5 | 5 | 3 | 3 | 1 |
| Adjacent non-contiguous source | 3 | 5 | 3 | 3 | 1 |
| Timeline gap, contiguous source halves | 6 | 4 | 4 | 4 | 1 |
| Two-times-speed right half | 4 | 4 | 2 | 4 | `"1/2"` |

The trimmed native clips use source 0–3 and 5–8. Moving only the incoming
timeline start from five to three produces a six-second edit that skips source
seconds 3–5. Moving the untrimmed incoming start from four to six produces a
ten-second edit with a two-second black/silent gap. Retiming keeps source 4–8
but plays it over timeline 4–6. Native `metadata.clipSpeedAttribute` is a typed
true boolean on the wrapper and both children; the editor displays 2.00x.
All seven exercised source/split/trim/gap/rate controls independently reopen
and reproduce their own decoded streams. Rendered source timecodes and
changing-tone windows establish the source positions. Separate native Fade
fixtures now verify these edited boundaries and independently saved preroll
flags; see [edited AV transitions](transitions.md#edited-av-boundaries-and-independent-preroll-flags).

A format-10 2× Group with a positive in-point exposes a native reopen failure.
The synthetic Group starts at 38 seconds, trims one internal second, contains
video at internal 1–5 seconds and initially requests two timeline seconds.
Fresh native loading/saving grows it to 2.5 seconds, then three seconds on the
next fresh load, without moving its marker destination. Repeated saves in the
same process do not expose the growth. A scalar-one trimmed control remains
four seconds. In the observed Group selection, the Clip Speed palette menu
omits Add to Selected Media; no alternate native speed constructor is inferred.

For this unanimated one-video Group, rebasing its internal clock to in-point
zero and shifting the child's timeline start from one second to zero preserves
the source interval, Group speed and every marker destination. The corrected
Group lasts two seconds; its fresh native saves are byte-identical and the
96-second independent native exports reproduce complete decoded video/audio.
This finite construction is not an automatic animation/Quick Property rewriter.
The [helper's native guards](helper.md) reject the reproduced drift before
applying a candidate. Preserve complex Group animation and derive a stable
constructor for it rather than dropping its timing metadata.

## Geometry and animation

Locally, `translation0`/`translation1` position content in canvas pixels about
the center, positive Y upward. Parameters can be scalars or typed objects with
`defaultValue`, `interp`, and `keyframes`. Preserve the existing representation.
Keyframes may have `time`, `endTime`, `duration`, and `value`; visual animation
metadata may also live in `animationTracks.visual`.
Fresh native imports can store zero crops as typed double descriptors with
`defaultValue: 0.0` and `interp: "eioe"`. Native split/trim saves in the
exercised AV controls normalize four `geometryCrop0`–`geometryCrop3` defaults
to bare `0.0` on a clip. Record those exact changes in preservation audits;
this observation does not permit flattening other typed parameters or keyframes.
For current native presets, easing owners, source-position animation clocks,
negative short-clip intervals, SmartFocus, crop, and corner pin, read
[native animations](animations.md).

Scale semantics must be checked on the actual source/template pair. The demo
contains both high-resolution sources and baked intermediate assets; its
absolute scale values are not general presets. When replacing a source, update
dimensions and adjust every affected default/keyframe to retain framing.

Test endpoint frames for exposed canvas, menu bars, clipped text, and overlay
collisions. A source-frame crop cannot reproduce native cursor/effect rendering.
