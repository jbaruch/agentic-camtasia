# Media, recording, and rendering

## Source retention

Copy required recordings out of temporary Camtasia storage into a durable
project before relying on them. Prefer standalone bundles for portable edits.
Preserve originals; a low-resolution MP4 export cannot restore native source
detail or all recording metadata. TechSmith documents the recording location
and standalone save behavior in its
[recording guidance](https://support.techsmith.com/hc/en-us/articles/203727488-Location-of-Saved-Recordings).

Relinking needs the source-bin entry, selected stream, dimensions, duration,
rate, and any dependent effects. Keep paths relative to the destination bundle
when creating a portable project. A source missing on the current machine is
a relinking problem, not evidence that its timeline clip should be deleted.

Use the read-only `source-manifest` command in [the helper contract](helper.md)
to record source identity and content hashes before packaging. Recompute it on
the destination and compare each retained reference/hash. An available absolute
source is still external to a portable bundle. Source-file containment does not
resolve installation assets or certify archive/symlink transport. Native standalone
save, close/reopen, and rendering must establish the delivered project's behavior.

## Standalone bundle verification

A copied two-source native format-9 bundle was converted by Mac 2026.2.4 using
**Save Converted Project As**. Both source files kept their relative references
and content hashes inside the new bundle. An explicit native save updated the
authoring version, as described in [Mac versions](mac-versions.md). The only JSON
changes were format 9.0→10.0, authoring version 2025.0.3→2026.2.4, and four
added zero-valued source-track `tag` fields; every other field was preserved.

The editor can retain a previous bundle's media handles during conversion.
Source existence and the first export do not establish independent resolution.
The test quit the editor normally, confirmed its process exited, temporarily
withheld both earlier disposable bundle locations, and reopened the converted
bundle in a fresh editor process. A positive selected-source handle pointed
inside that bundle. Its native rerender matched the first export's decoded
video/audio, and inspected frames showed the expected replacement source.
Both earlier bundles and their source hashes were restored unchanged afterward.

For a disposable relocation probe, preserve the original bytes and source
manifest, close the editor before withholding earlier locations, and verify
the new bundle through an independent native reopen/export. Restore originals
and compare their hashes before finishing. Use the [ownership procedure](helper.md)
for retained media handles. This exercised source-bin closure does not establish
font, model, installation-asset, archive, or cross-host portability.

## Recording streams and cursor

The observed Mac `.trec` files can be probed with ffprobe and contain screen,
camera, and microphone streams. Do not assume every TREC version or platform
uses the same codecs, stream order, or container internals. Enumerate streams.

In the local take, pointer motion is stored separately from screen pixels.
Extracting a screen frame does not reveal the native rendered cursor. The
speaker-toolkit research documents a `TSCM` atom containing pointer and capture
rectangle records; treat its byte layout as an observed implementation, not a
universal binary contract. Preserve the original recording for cursor effects.
Check native playback when zooming around a pointer target.

The combined September 28 take distinguishes the screen stream's `ScreenVMFile`
from the camera stream's ordinary `VMFile`; its microphone is source track 2.
An eight-second disposable probe retained all three source-track descriptions,
selected screen track 0, and used a separate muted `AMFile` for track 2. At
3840×2160 source resolution on a 640×360 canvas, native 16.7% scale fits the
screen. Keeping only a video-stream number on an ordinary `VMFile` did not
expose Cursor Properties; preserving the native screen type did. Carry its
cursor parameters and recording metadata as well as the original TREC.

## SVG inputs

TechSmith added SVG rendering in Mac 2026.2.2, limited to SVG Tiny 1.2.
Check the actual build and asset entry point before treating an SVG as accepted
media. The vendor statement does not establish arbitrary SVG 1.1/2 filters,
scripts, fonts, or external-resource support, nor a project JSON representation.
Use a small self-contained Tiny 1.2 specimen, inspect its native saved source
and clip, then reopen and render it over a contrasting background to verify
geometry and transparency. A source-file hash does not close resources that
an SVG itself references. [Mac 2026 release history](https://support.techsmith.com/hc/en-us/articles/41263167862285-Camtasia-Mac-2026-Version-History),
[SVG Tiny 1.2 document structure](https://www.w3.org/TR/SVGTiny12/struct.html)

In Mac 2026.2.4, native **File → Import → Media**, followed by the Media Bin's
**Add to Timeline at Playhead**, accepts the self-contained Tiny 1.2 specimen.
Native save copies the original SVG bytes into the standalone bundle and uses
an `IMFile` clip referencing its source-bin ID/track 0. The source retains a
640×360 rect, source-track `editRate: 600`, and range `[0, 1]`. The five-second
still clip saves `duration: 3528000000` at project `editRate: 705600000`, but
`mediaDuration: 1`, `mediaStart: 0`, and scalar 1. Preserve this still-source
representation rather than deriving its hold length from the source range.

The test's rectangle, circle, path triangle, and half-opacity magenta square
render at the declared 640×360 viewport. Separate black/white native project
backgrounds establish transparent regions and visible alpha blending. Exported
patches for the half-opacity square are RGB `(118, 0, 118)` over black and
`(255, 114, 254)` over white; do not promise arithmetic 50/50 RGB output from
`fill-opacity="0.5"`. The same shapes remapped into `viewBox="100 200 320 180"`
reproduce the original `0 0 640 360` video's decoded pixels exactly. All four
SVG projects independently reopen and reproduce their own video/audio streams.

A separate SVG 1.1 specimen with `feGaussianBlur`, standard deviation 8, also
imports, saves, and visibly blurs the rectangle; its independent rerender
matches. This positive example does not expand the vendor's documented support
to all SVG 1.1/2 features. The Tiny specimen additionally reopens in a fresh
editor process with its original import file unavailable and produces identical
decoded streams from the bundled source. The original file is restored unchanged.
The dependency cases below separately check raster references and SVG text/fonts.

One import selected the intended SVG but recorded a transient `.tmp.driveupload`
path, produced a blank asset, and could not save. A stable local fixture copy,
fresh native import, and source-path/hash checks resolved that disposable test.
Inspect the actual saved source rather than trusting the selected filename or
thumbnail. After an external-change warning, compare on-disk bytes with the
retained baseline before choosing whether to save; never overwrite unknown work.

### SVG image and font dependencies

Mac 2026.2.4 / format 10 additionally renders nine controlled SVG variants
through the known native `IMFile`/still-source constructor. Each five-second
use retains source range `[0,1]`, source edit rate 600 and `mediaDuration: 1`.
Source IDs 1–9, timeline ID 10 and clip IDs 11–19 remain distinct. The probe
stages existing native serialization; it does not assert a new native import API.

| SVG content | Observed native output in these controls |
| --- | --- |
| Vector paths and color rectangles | Visible through every resource and relocation phase. |
| PNG embedded as `data:image/png;base64,...` | Visible with original input paths absent and after moving the bundle. |
| Relative PNG `xlink:href` beside its SVG | Absent even with the matching PNG present beside the bundled SVG. |
| PNG through `file:///...` or an absolute filesystem path | Visible while that exact original path exists; absent when withheld or after moving the bundle. Restoring the same bytes at that path restores output. |
| Embedded SVG font, external SVG-font URI, Arial text, generic sans-serif text | All four text panels are absent. Their matching path-outline control remains visible. |

The image and font syntax follows [SVG Tiny images](https://www.w3.org/TR/SVGTiny12/struct.html#ImageElement)
and [font references](https://www.w3.org/TR/SVGTiny12/fonts.html#FontFaceURIElement).
Those standards describe the input, not Camtasia's implementation. These finite
controls do not establish every URI, font or SVG text configuration.

For portable raster content, inline the PNG and preserve its geometry. An
absolute reference remains dependent on that location even when a byte-identical
PNG is copied into the moved bundle. Check SVG text visibly; for critical
typography use outlines generated from the intended font or editable native
[Callout text](quick-properties.md#text-group-constructor). Do not assume that
installing a named font repairs a missing SVG text panel.

The source manifest reports all nine SVG files bundled even with both internal
companions withheld. It audits source-bin files; it does not traverse SVG image
or font references. Inspect the SVG dependencies separately and render after an
actual move with the original paths unavailable. A project/SVG hash alone does
not establish the same picture under a different resource environment.

Four 45-second native save/reopen/export pairs cover resources present, withheld,
restored and a physically moved bundle. Each pair repeats complete decoded
video/audio. Restored output equals the original present output; moved output
equals the withheld control despite both companion files existing in the moved
bundle. All 72 sampled frames in eight contacts are inspected, with 144
both-channel silence windows and fixed visible/absent panel checks. Nine SVG
hashes, both companion hashes and all 19 IDs remain strict. Original inputs and
a full pre-move bundle backup are retained; the original bundle is restored
byte-for-byte after the test. Raw/profile schemas need no correction.
Repository evidence is `svg-dependencies-native-checks.json`, four phase comparison
reports, the isolation/relocation receipts and tested `svg_dependency_*` contracts.

## Replacement assets

Probe resolution, duration, frame/sample rates, channels, and color metadata
before replacement. Keep original detail when a close-up needs it. A
higher-resolution source also needs adjusted scale defaults and keyframes to
preserve framing. Use a new filename for a replacement asset when Camtasia's
media cache continues showing an older version.

The local demo mixed HDR and SDR media. Its corrected asset was converted to
SDR BT.709, inherited HDR tags removed, then output primaries/transfer/matrix
verified. Do not relabel HDR pixels as SDR without a real color transform.
Native codec acceptance still requires opening the asset in Camtasia; one
hardware-encoded intermediate failed while a software-encoded version worked.

## Final evidence

For a visual pass, compare narration and processing state with the baseline.
Avoid duplicate sound from camera cutaways or screen sources. Export from
Camtasia when AI cleanup, native compositing, captions, cursor effects, or
other editor processing must be included. An ffmpeg preview is useful evidence
of source pixels and timing, but cannot certify those native features.

## Measured HDR/SDR input probe

The broader Mac 2025.0.3 probe used a generated HEVC `yuv420p10le` input tagged
BT.2020 primaries, SMPTE ST 2084 transfer, and BT.2020 nonconstant matrix. A
separate conversion linearized PQ, converted primaries, applied Hable tone
mapping, encoded BT.709 limited-range pixels, and deleted inherited side data.
The FFmpeg build needed `zscale`; merely setting output color tags was not the
conversion. See the [FFmpeg filter documentation](https://www.ffmpeg.org/ffmpeg-filters.html#tonemap).

Both inputs opened and rendered through Camtasia. The tested MP4 export encoded
H.264 `yuv420p` with BT.709 primaries/transfer/matrix for both. The converted SDR
input versus its native export had mean absolute RGB error 0.354 at two seconds.
Native PQ interpretation and the chosen Hable conversion differed in brightness;
that difference must not be hidden by matching output tags. Choose the intended
appearance with representative highlights, shadows, and color controls. These
probes establish input acceptance and SDR output for the exercised files, not
HDR mastering, every HDR profile, or HDR-preserving export.
