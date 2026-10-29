# Native Library assets and archives

Target: Camtasia Mac 2026.2.4, format-10 projects. TechSmith's
[Mac Library overview](https://support.techsmith.com/hc/en-us/articles/229859268-Using-Camtasia-Editor-Media-Assets-on-Mac)
describes the user-facing Library. The serialization below is locally observed
through native creation, export, isolated import, insertion and ungrouping.
It is not an official complete asset schema or a Windows compatibility claim.

## Create and export an editable asset

Select the intended timeline clips and use **Edit → Add Selection To Library**.
Record the asset name, destination Library and **Use Canvas Size** versus
**Use Visible Size** choice. The tested canvas-size asset includes an eight-second
linked video/audio clip and a separate five-second styled text group on a
640×360 canvas. Its original source video, audio, Unicode text, rich properties,
effects, timing and unknown media payload remain intact.

The observed installed directory is:

`~/Library/Application Support/TechSmith/Camtasia/Library/User Libraries/<library>/<name>.asset/`

The created asset has four files:

| File | Owner and role |
| --- | --- |
| `<name>.assetproj` | Editable Library document with sources and timeline. |
| `<name>.info.json` | Library metadata, asset UUID and displayed duration/dimensions. |
| `<name>.thumb.png` | Native thumbnail, separate from project/media data. |
| `source.mp4` | Exact copied source bytes in this one-source asset. |

Do not infer every asset's companions from this inventory. Preserve its actual
files, resolve its actual references and verify reuse with the originals absent.
One `.asset/` directory can contain multiple internal projects after an import
collision. Enumerate every actual `.assetproj` and its matching internal-stem
metadata/thumbnail; see [archive-import collisions](#archive-import-collisions-and-isolated-intake).
Source media is copied beside this asset document and referenced as
`./source.mp4`; it is not linked to the original project's media directory.

Right-click the owned Library item and choose **Export Asset**. The resulting
`.libzip` is a ZIP containing that complete `.asset/` directory and a root
`Packages.json`. The native header has `LibraryVersion: "4.0"`, `Platform: "Mac"`,
and `CamtasiaVersion: "2026.2.4"`. Library version, editor version and asset/project
format version are separate identities. All four exported files match their
installed bytes, including the source MP4. No font files are included.

## Asset JSON differs from a project document

This `.assetproj` has precisely these observed root fields: `width`, `height`,
`ident`, `version`, `clientName`, `editRate`, `sourceBin`, `timeline`, `duration`.
It uses `clientName: "Camtasia"`, rather than the project document's
`authoringClientName` object. Do not pass it to a full-project helper or apply
the full `.tscproj` schema as if the two document types were interchangeable.
Obtain native asset constructors; preserve unfamiliar asset data.

The selected media/source payload is preserved. Native asset creation drops the
empty third scene lane and the per-lane UI metadata, copies the source to the
new relative location, and initializes an unused caption background alpha from
204 to 191. This specimen has no captions; the change is recorded separately
from the preserved media. These finite differences do not authorize discarding
other tracks, metadata or caption styling from arbitrary assets.

The root `duration` is zero even though the asset lasts eight seconds. Its
`.info.json` supplies `Asset Duration: "5644800000"` and
`Asset Edit Rate: "705600000/1"`; project ticks, source-stream sample ticks and
displayed seconds remain distinct. Width/height, type, project version and size
are also string-valued metadata here. `Asset Type: "6"` identifies this native
group specimen, not a complete type enum. Its stored size counts the asset
project plus the source bytes, excluding metadata and thumbnail in this case.
Preserve the asset UUID separately from numeric project source/clip IDs.

## Import and insert with original paths absent

Use **File → Library → Import Zipped Library**. The tested **Create New Library**
choice creates a Library named from the archive basename. All four imported
asset files and the asset UUID remain identical to the exported originals.
The original installed item and author project are recoverably moved away;
the destination project starts empty with no copied author media in its bundle.
Importing the archive changes the Library, not that empty project's timeline.

Right-click the imported item and choose **Add to Timeline at Playhead**.
The native operation creates an outer `Group`, copies source bytes into the
destination bundle's actual `./media/<native-directory>/source.mp4`, and remaps
the shared numeric namespace. Recover that path from the native save instead of
synthesizing its directory name. Preserve source tracks and clocks; this source
has video and audio streams with edit rate 48,000 and bounds `[0,384000]`.

In the empty-recipient specimen, IDs are source 1, timeline 2, outer group 3,
linked AV/video/audio 4/5/6, nested text group 7, and Callout 8. The outer group
and the nested text group both expose Text/Callout Quick Properties bound to
Callout 8. The wrapper has 640×360 bounds and eight-second duration, while the
nested text group retains its five-second duration and original geometry.
Child tracks combine the selected asset lanes with their native lane attributes.
Use actual IDs and remap both nested bindings; the specimen's allocation is
not universal. The asset's Last Used Date changes after use; its other metadata,
asset project, thumbnail and media bytes remain unchanged.

Initial insertion materializes 42 static double descriptors: twelve crop
parameters, Callout opacity, and the demonstrated definition/font controls.
A later native save collapses that complete cohort back to equal scalars.
The exact path/default/interpolation checks preserve all other payload and the
eight rich-text entries. This observation does not permit flattening animated,
mixed, unknown or extended descriptors.

## Rendering, audio endpoints and ungrouping

Four independent eight-second native MP4 pairs cover the author, imported group,
fresh-process reuse after removing the installed asset, and a separately
ungrouped copy. Each pair repeats complete decoded video/audio exactly. Thirty
actual native frames were inspected beside thirty author references, including
the text's five-second endpoint. All video streams equal the author's output.
The imported and Library-absent grouped outputs equal each other in both streams.
This establishes the copied project's independence from the installed item on
this host; it does not identify the physical font file used by Camtasia.

**Check the audio end after importing a group.** Grouped output differs from the
author at the very end. Independent native stereo 44.1-kHz/16-bit WAV pairs
localize it to the final 127 sample frames, about 2.9 ms. The exported AAC's
decoded difference begins about 60 ms before the end. Four additional WAV
controls with **Enable smoothing** off reproduce the same endpoint difference;
that option has no effect on these measured outputs. Do not attribute the
result to the smoothing checkbox or infer the renderer's internal cause.

Selecting the imported outer group and using **Edit → Ungroup** restores the
original AV and nested text layout. In this constructor the native IDs return
to AV/video/audio 3/4/5, text group 6 and Callout 7; both retained bindings follow
the Callout ID. All original media/typography/other payload is preserved,
apart from the verified source-copy path/addition time and bookkeeping.
The ungrouped native MP4 pair matches the original author's complete decoded
video and audio. Its independent WAV pair also matches every original PCM
sample exactly. When this endpoint difference matters, ungroup the outer asset
wrapper in a separate copy and verify the result before delivery. Retiming,
other group layouts and other sources need their own endpoint checks.

The completed test retains eight MP4s, ten WAVs, the exact archive and recoverable
asset copies. All 1,584 preexisting Library files remain byte-identical and the
original author bundle is restored in full. The original smoothing setting and
Library selection are restored. Native inserted/ungrouped projects pass both
the pinned raw schema and exact-build profile without a new correction.

Evidence: `build/native-verification/library-*-comparison.json`, native operation
captures, isolation/restoration receipts and tested asset/insertion/resource/
ungroup contracts. Generated/private fixtures and vendor Library backups are
excluded from distribution. Library management operations, other media/resource
types and physical font-file closure remain separate feature cases.

## Text-only assets and canvas versus visible size

Saving only the original five-second styled text Group creates three files:
`.assetproj`, `.info.json` and `.thumb.png`. Its `sourceBin` is empty; the
unselected AV source is omitted rather than copied. This native metadata uses
`Asset Type: "5"`, rather than the multi-selection specimen's `"6"`. These are
observed constructors, not a complete type enum.

**Use Canvas Size** saves root dimensions 640×360. **Use Visible Size** saves
376×176, the selected Group's bounds. Apart from `ident` and those root
dimensions, both asset documents are identical. Both retain the same original
child coordinates, five-second clocks, rich typography and concrete styling.
The asset namespace becomes timeline 1, Group 2 and Callout 3; both Quick
Property entries bind Callout 3. Each asset has its own UUID.

Insertion into an empty 640×360 project uses that existing Group directly;
it does not add the multi-selection asset's extra outer wrapper. Its name comes
from the Library display name and its width/height come from the asset root.
The native save expands 38 static crop/opacity/definition/font descriptors.
The later fresh-process save collapses that entire same cohort to equal
literals, with no other document changes in either size control. Mixed cohorts,
changed defaults and animated forms are not covered by that normalization.
Both inserted text variants keep the original child payload and render with
the same centered placement, typography and complete decoded output as an
independent text-only control. Asset bounds do not imply automatic enlargement
of the text to fill a receiving canvas.

Native source-free saves omit `sourceBin` from the full project. The pinned raw
schema reports its required-property error; the existing exact-build Mac
profile accepts this known omission. Keep that raw discrepancy visible instead
of adding a fictional source or silently rewriting the saved document.

## Native Library management

The exercised Mac operations use synthetic user assets and a blank test Library:

| Operation | Observed result |
| --- | --- |
| Library selector → Create New Library, Start from Blank | Creates a named empty user Library directory. |
| Right-click → New Folder | Creates an empty directory inside the current user Library. |
| Folder Rename / Move To | Renames that directory or moves it to the selected Library. The exercised folder is empty; populated-folder drag/drop is separate. |
| Asset Rename | Renames only the outer `.asset` directory. Original internal filenames, asset `ident`, metadata UUID and every file byte remain unchanged. Resolve the actual internal document instead of deriving its basename from the displayed asset name. |
| Asset Copy To | Adds a complete byte-identical asset directory to the selected Library and retains the source, including the same UUID. Do not assume copying allocates a new identity. |
| Asset Move To | Transfers the complete asset directory, removes its old location and retains all file bytes/UUID. |
| Preview | Opens a separate native playback window with five-second duration. The text is visible at the start and absent at the end in this specimen. Preview does not replace a project export check. |
| Sort By → Reverse Order | Reverses all three displayed entries, including the folder; toggling again restores the prior order. Other sort-key distinctions need suitable native controls. |
| Search Library | `Renamed` finds the renamed asset; its old internal `Text Canvas` ident produces no result. Clearing the query restores all entries. Search uses the display name in this case. |

The copied renamed canvas-size asset and moved visible-size asset both insert
and render correctly in a fresh editor process. Their internal source-free
documents remain editable. Insertion changes only the installed metadata's
**Asset Last Used Date**; native preview, sort and search preserve all asset
bytes in these controls. Nine operation snapshots retain the exact file and
empty-directory states. The original Library selection, forward order and empty
search are restored, and the synthetic resources are recoverably archived.

Five independent native export pairs cover the text-only control, both inserted
variants and both variants after all synthetic installed Library paths are
absent. Every pair and each variant's complete decoded video/audio match the
independent control. Sixteen native frames and sixteen control frames are
inspected in four contacts, with 32 both-channel silence windows. All 1,584
preexisting Library files and the original full author bundle remain unchanged.
These are same-host font observations, not physical font packaging proof.

Evidence: `build/native-verification/library-sizes-*-comparison.json`,
`library-management-*.json`, immutable text asset/insertion captures and
`library-sizes-cleanup.json`.

## Mixed Libraries, populated folders and shared files

**Create New Library → Start from** an existing mixed user Library copies its
populated and empty folders. The observed Library has one four-file AV/text
asset and one three-file text-only asset. All seven bytes and UUIDs remain
identical. **Manage Library → Rename Library** changes only its outer directory.
Asset Rename still changes only the outer `.asset` directory, leaving internal
filenames and the asset's JSON ident intact.

**Do not overwrite installed Library asset files in place.** In both whole-Library
duplication and populated-folder **Copy To**, five resource files share device
and inode with their originals: both asset JSON documents, both thumbnails and
the source MP4. The two `.info.json` files have independent identities. Native
copies can share underlying resource files even when their directories differ.
Close the editor, retain a full backup and stage independent files outside the
installed Library. Use the isolated archive-intake workflow below to install
the staged result and verify the recipient; no direct installed-asset writer
is provided by this plugin.

Populated-folder **Rename** and **Move To** retain all seven file bytes and
filesystem identities. Move removes the old folder location; the exercised
destination already has a separate copied folder. No name collision or merge
is exercised. Insertion from the moved folder uses the renamed asset's display
name on the new outer Group and preserves the established eight-ID AV constructor.
Only the selected independent metadata file's **Asset Last Used Date** changes;
the source and other copied asset metadata stay unchanged.

## Whole-Library archives and isolated re-import

Native **Manage Library → Export Library** writes all seven files under their
populated-folder paths plus `Packages.json`. The header is Library `4.0`, Mac,
Camtasia `2026.2.4`. This eight-member ZIP has no directory entries: the empty
folder is omitted. **Import Zipped Library → Create New Library** names the new
Library from the archive basename, recreates the populated folder and both
assets, and does not recreate the empty folder. All seven bytes and UUIDs match;
all seven imported filesystem identities differ from the archived originals.
Import leaves the empty receiving project's timeline unchanged until insertion.

Three eight-second native save/reopen/export pairs cover moved-folder reuse,
isolated whole-Library re-import with all original test Libraries absent, and
a fresh renderer after every test Library is recoverably archived. All complete
decoded video/audio streams equal the accepted grouped AV control, including
its separately measured endpoint behavior. Thirty native frames and thirty
control frames are inspected in six contacts; sixty both-channel tone windows
are checked. This is same-host reuse, not physical font-file closure.

Twenty-eight synthetic installed files are retained in two recovery archives.
All 1,584 preexisting Library files, the original full author bundle and user
themes remain unchanged. Evidence: `build/native-verification/library-lifecycle-*.json`,
immutable operation copies, exact `.libzip`, native controls and accepted render
reports. The following sections extend the collision, sorting and direct-media
cases; Library deletion, folder drag/drop, other
asset/resource types and physical/cross-host font closure remain separate.

## Name collisions and date-based sorting

Native **Copy To** an existing destination name creates a new suffixed entry.
The tested asset becomes `Agentic Library Contract 64(1).asset`; an empty folder
becomes `Agentic Empty 67(1)`, and a populated folder becomes
`Agentic Bundle 67(1)`. The existing entries remain unchanged. **Move To** a
Library already holding the populated folder and its `(1)` copy chooses
`Agentic Bundle 67(2)` and removes the old source-folder location. These finite
copy/move collisions do not merge or replace existing contents. Keep the actual
native chosen name; do not predict it from a single attempt or reuse a stale path.

Both operations switch the Library browser to the destination. Reobserve the
selected Library and its actual rows before the next operation. The suffixed
asset retains its original internal filenames, document ident, metadata UUID
and all four file bytes. Its three resource files share original device/inode;
its metadata file is independent. The seven-file populated copy shares five
resource identities and independently copies two metadata files. Native Move
preserves all seven identities. Preserve the shared-file safeguards above.

Distinct native name/date controls verify these sort keys within an expanded
populated folder:

| Choice | Observed order |
| --- | --- |
| Name | Alphabetical display names, including the renamed outer asset. |
| Date Added | Newest `Asset Created Date` first in these copied native assets. |
| Date Used | Newest `Asset Last Used Date` first; inserting the older AV asset updates only its metadata and moves it ahead of the text asset immediately. |
| Reverse Order | Reverses sibling folders and the populated folder's child order while retaining hierarchy. |

The AX menu's `selected` label can represent focus; verify the resulting rows
against distinct names and metadata dates. Do not infer the active sort key
from that label alone. Name/forward ordering is restored after these cases.
The direct-media controls below distinguish Media Type ordering. Date ties
still need separate discriminating controls.

The native **Manage Library → Delete Library** confirmation identifies the
Library and warns that deletion permanently removes its contained folders and
assets. Verify the exact selected Library, preserve complete independent copies
and check receiving-project dependencies before committing it. The current
collision test retains 29 owned files and every empty folder before that action;
its native deletion and post-deletion render check are pending. No deletion
or recovery behavior is asserted by the completed collision/sort evidence.

Evidence: `build/native-verification/library-collisions-operation-checks.json`,
eight immutable native states and five distinct name/date row controls.
Eleven fixed tests protect collision bytes/identities, metadata changes and
hierarchical ordering. All 1,584 original Library files, their backup, original
author bundle and user themes remain unchanged during the completed operations.

The installed collision recipient also has an accepted native save/reopen/export
pair. Both complete decoded streams equal the accepted grouped AV control;
ten native/control frame pairs and twenty both-channel tone windows match.
The saved project is byte-identical to its original native insertion. This
closes installed-recipient rendering, while native deletion and post-deletion
closure remain pending. Evidence: `library-collisions-installed-native-checks.json`
under `build/native-verification/`.

## Direct PNG, WAV and MP4 Library assets

Use **File → Library → Import Media to Library**, then choose the destination in
**Add To Library**. Native direct-media constructors have the same nine root
fields described above, with root `duration: -1` rather than the grouped
specimen's zero. Each tested asset has four files: its original filename/media,
`.assetproj`, `.info.json` and `.thumb.png`. The copied source bytes are exact.
Its string-valued `Asset Size` counts asset-project plus source bytes, excluding
metadata and thumbnail. Preserve all actual companions and each distinct UUID.

| Native input | Asset metadata and bounds | Timeline constructor |
| --- | --- | --- |
| Eight-second 640×360 MP4, video plus mono audio | `Asset Type: "1"`, 640×360 | One `UnifiedMedia`, linked `VMFile` and `AMFile`; source tracks 0 and 1. |
| Eight-second 48-kHz, stereo 16-bit WAV | `Asset Type: "2"`, default 1920×1080 asset canvas | One `AMFile`, source track 0, `channelNumber: "0,1"`; source rectangle remains 0×0. |
| 128×64 PNG | `Asset Type: "3"`, 128×64 | One `IMFile`, source track 0; five-second hold and `mediaDuration: 1`. |

These are finite observed codes alongside group `6` and text-only `5`, not a
complete asset enum. Audio's default asset canvas does not resize the existing
640×360 recipient. The still's one-unit media duration is not one project tick
of display time. All asset timelines use project edit rate 705,600,000; the
MP4's two source tracks use 48,000 with range `[0,384000]`, including its 30-fps
video stream. The WAV source uses 48,000, range `[0,384000]`, two channels and
bit depth 16. The PNG source uses edit rate 600 and range `[0,1]`. Keep these
source clocks distinct from project timing, video frame rate and audio rate.

Native direct assets initially retain `integratedLUFS: 100` and `peakLevel: -1`
as unmeasured source-track cache values. Inserting/importing into a full native
project fills measured audio values. Do not treat the sentinels as actual signal
measurements or overwrite measured caches from a different source.

**Add to Timeline at Playhead** inserts these direct clips without an outer
asset `Group`. In the tested three-source recipient, sources are IDs 1–3,
timeline 4, linked movie/video/audio 5/6/7, separate stereo audio 8 and image 9.
All start at zero on separate scene lanes; movie/audio last eight seconds and
the picture lasts five. Each source is copied into the recipient's actual
native `./media/<directory>/<original-filename>` path. Remap actual IDs and
recover actual paths instead of reusing this specimen's allocation.

An independently constructed ordinary **Import Media** recipient retains the
same source/clip payload, audio cache, geometry and timing after the observed
native addition-path/time differences. Ordinary import alone adds the string
metadata `default-scale: "1"` to movie and picture clips. This is retained native
metadata, not an instruction to rescale the picture. Each clip also receives
native standard clip metadata. Native fresh saves collapse a complete cohort
of four zero crop descriptors per video/image to equal scalars. Preserve mixed,
animated, extended or changed-value crop data; this observation does not
authorize general descriptor flattening.

The three direct Library assets retain every byte except their individual
**Asset Last Used Date** advances after insertion. **Sort By → Media Type**
orders video, image, audio here; Reverse gives audio, image, video. The metadata
codes are respectively `1,3,2`, so numeric code sorting would be wrong. Distinct
display names independently verify Name sorting and restoration. Other asset
classes and date ties require their own controls.

Two fresh-process eight-second native save/reopen/export pairs cover Library
reuse and the ordinary-import control. All four movies have identical complete
decoded video and audio. During those renders all original Library/input paths
and their renamed loose recovery paths are absent: twelve native asset files
and three inputs are retained in a verified fifteen-member recovery ZIP. Both
recipients independently bundle all three original sources. Positive editor
file handles resolve MP4 and WAV inside each recipient before and after reopen;
PNG is separately checked in decoded frames after its file handle closes.
A renamed directory alone is weaker isolation when macOS can follow bookmarks.

Ten native/reference frame pairs in two inspected contacts establish layering
and the five-second picture endpoint. Additional independent checks cover the
original PNG's four colors/cross in 24 frames, its absence against an older
bare-movie native control in sixteen frames, and both sources' distinct stereo
tones in twelve windows. The older separately encoded control has small pixel
differences; its content comparison is bounded lossy agreement, while all four
current movies are decoded-identical. These checks establish these fixed source
fixtures, not arbitrary image/color management or perceptual audio quality.

The ordinary-import route encountered three native import hangs, one per unique
source, before decoding. Whole saved/recovery bundles were preserved; native
Activity Monitor quit only each exact hung PID. **Project Recovered → Open →
Save** retained and bundled each import without repeating it. See the
[native import recovery procedure](native-verification.md) before responding to
this observed stack; it does not establish cloud-hosted or corrupt sources.

Evidence: `build/native-verification/library-direct-native-checks.json`, immutable
created/inserted file copies, original recovery bundles, fifteen-member recovery
ZIP, four positive handle observations and native comparison/content reports.
Twenty-nine fixed Python tests cover constructors, clocks, channel metadata,
insertion, strict resaves, archive isolation and positive picture/stereo checks.
All original Library files, the pending collision Library and independent backup,
the full original author and user themes remain unchanged. No schema correction,
vendor asset or generated native fixture is distributed with the plugin.

## Occupied names and equal folder/asset labels

Native **Rename** to another existing asset name is rejected with **Cannot
rename asset**. A populated-folder rename to another existing folder name
receives the same message. Both original entries, all contained bytes and
paths remain unchanged; neither operation creates a Copy To style `(1)` suffix
or merges contents. The dialog also lists unsupported filename characters;
the completed controls establish the occupied-name case, not every invalid
character or normalization rule.

**Rename Library** and **Create New Library** show **This library name already
exists** and disable their submission button for an existing Library name.
Cancel retains both Libraries. The observed initial Rename field suggests the
current Library name with `(1)` appended; inspect and set the intended name
instead of accepting that suggestion implicitly. A valid new Library name
changes only the outer directory, retaining all contained bytes and file IDs.

**Equal display labels can still be valid.** Renaming a text asset to an existing
folder's visible name succeeds: `Agentic Folder 69.asset/` and `Agentic Folder
69/` coexist. Conversely, a populated folder can take the visible name of an
existing AV asset: `Agentic Library Contract 64/` and `Agentic Library Contract
64.asset/` coexist. All children, internal filenames, JSON idents, UUIDs and
physical file identities are retained through these outer renames. Display-name
uniqueness is not a safe selection rule.

Before an action, establish the selected Library, parent path and item type from
the actual rows. A collapsed folder and a `Group Icon` asset with the same label
expose different context commands. In the native control, selecting the root
AV asset's typed row exposes **Add to Timeline at Playhead** and inserts the
eight-second AV/text group; selecting its same-named folder would be a different
operation. Reobserve after rename, Library selection or expansion. Do not use
the first matching label or let a multiline match span unrelated rows.

## Start from Default, vendor and mixed Libraries

**Create New Library → Start from** lists Blank, installed vendor Libraries and
current user Libraries on this host. Selecting the existing, empty **Default**
Library creates a new empty named user Library and selects it. It does not add
media to the receiving timeline. This result describes the observed empty
Default; preserve actual Default contents on another host.

Starting from the installed **Camtasia 2025** vendor Library creates a user
Library containing all 401 assets and fourteen category folders. Its 1,583 files
are byte-identical to the vendor originals, including all UUID metadata. The
root `CamtasiaVersion` marker is omitted, so it is not a raw full-directory copy.
All 415 nested directories are retained. Native duplication shares 1,182 resource
file identities and independently copies 401 `.info.json` files. The shared
resources include native asset documents, thumbnails, JSON, shader-video, PDF
and MP3 files in this specimen. Apply the shared-resource safeguards above;
these additional file types do not become safe to overwrite in place.

Starting from the renamed mixed user Library also preserves both same-label
folder/asset pairs. All 21 files and nested folders survive; fifteen resource
files share original identities and six metadata files are independent. Native
insertion changes only the selected copied asset's Last Used Date. The donor
metadata and all other files remain unchanged. The receiving project has the
established eight-ID AV/text constructor and its exact source copied into its
own bundle, independently of the equal-label folders.

Two native save/reopen/export pairs cover insertion from this mixed duplicate
and fresh-process reuse after all five synthetic Libraries are absent. All four
complete decoded video/audio streams equal the accepted grouped AV control;
the previously measured grouped-audio endpoint remains part of that control.
Twenty native/reference frame pairs are inspected in four contacts, including
the five-second text endpoint, with forty both-channel tone comparisons. Two
positive main-editor file-handle observations resolve the source inside the
recipient before/after isolated reopening. The fresh save collapses only the
complete 42-field static descriptor cohort, apart from standard bookkeeping.

All 1,625 test files and 436 directories are retained in a verified recovery ZIP
before the five exact owned Library roots are removed. No native Delete command
is used for this reversible isolation. All 1,584 original vendor files and
physical identities, the full original author, user themes and the separate
29-file pending collision Library/backup remain unchanged. Native processes
quit normally between render groups and at completion.

Evidence: `build/native-verification/library-names-native-checks.json`, eleven
immutable operation states, original vendor identity capture, the recovery ZIP,
two positive source-handle reports and four inspected native contacts. Twelve
fixed tests protect refusal, outer rename, copy/metadata ownership and exact-root
isolation. Vendor-copy bytes do not prove rendering of all 401 vendor assets or
arbitrary resource/font portability. Populated-folder
drag/drop, other sort classes/date ties and native permanent deletion remain
separate feature cases.

## Archive-import collisions and isolated intake

**Import Zipped Library → Create New Library** suffixes an occupied Library
basename: two completed imports create `Agentic Archive 70(1)` and `(2)` and
select each newly created Library. **Add To Library → existing Library** leaves
the browser on its previous Library in these controls. Reobserve the actual
destination; import success does not establish the browser selection.

Importing the same four-file AV asset into an occupied destination creates
`Agentic Library Contract 64(1).asset/`. A populated-folder import similarly
creates `Agentic Nested 66(1)/`, retaining its seven files. Original paths,
bytes and identities remain unchanged. Native imports can hard-link identical
thumbnails and source media to older installed resources; the incoming project
and metadata files have independent identities in these controls. Apply the
shared-file safeguards above even after importing an archive.

**An occupied outer asset name does not always produce a separate asset.** A
native text asset packaged under the AV asset's outer `.asset/` name has three
different internal filenames. Import into the occupied destination adds those
three files to the existing AV container. The result has seven files: two
`.assetproj`, two `.info.json`, two `.thumb.png` and `source.mp4`. All original
AV files remain unchanged. A native isolated re-export of the incoming text
package matches every prepared member byte, verifying this as a native package
case. A later completed import of that same package creates a separate `(2)`
container after the internal filenames are also occupied.

The shared container initially exposes two assets with the same display label,
parent and Group Icon type. Native previews distinguish eight-second AV from
five-second text. Exporting either item includes **both projects and every
shared-container companion** in an eight-member ZIP, including `Packages.json`.
After a full editor restart, only the text item is exposed at that root label;
all seven files remain on disk. Inserting the transient AV item updates the
text companion's **Asset Last Used Date**, leaving the AV metadata unchanged.
Inserting the remaining text item also updates that text metadata. Exact byte
preservation alone does not prove correct Library identity or persistent UI
access to every internal project.

Before a Library mutation or insertion:

- Enumerate all internal project stems and companions in the actual container.
- Establish the selected item using native preview/content as well as Library,
  parent and type. Those three selectors can still identify two same-label rows.
- Do not treat a single row after restart as proof of a single internal project.
- Retain all files before any repair. Renaming a shared container does not split
  its projects, and Export Asset does not isolate the selected project here.

For an incoming asset whose destination names might collide, use this tested
native intake workflow:

1. Import into a separate new Library and inspect its actual container. Confirm
   the intended asset has one internal project and its complete companions.
2. Rename that isolated asset to an unused destination display name through
   Camtasia. Rename changes its outer directory; internal filenames, ident,
   UUID and all bytes remain intact.
3. Export the renamed isolated asset. Inspect the archive's unique outer path
   and complete internal project/metadata/thumbnail/source inventory.
4. Import that native export into the destination Library. Confirm the separate
   actual container, preview it, restart the editor and confirm it stays visible.
5. Insert into a disposable empty project, save/reopen/export, verify source
   content and confirm only the intended asset's metadata advances. Verify reuse
   again with the donor test Libraries absent before relying on portability.

The independently named AV and text assets both import into separate containers,
remain separately visible after restart and update only their own metadata.
The AV recipient retains the strict eight-ID constructor and bundled source;
the text recipient retains the three-ID source-free constructor. These controls
prevent the demonstrated collision during intake; they do not provide an
in-place repair tool for an already merged Library.

Eight native export/reopen pairs cover shared-container and unique-name AV/text
recipients, each installed and again in a fresh renderer with all five test
Libraries absent. All sixteen movies match the respective independent control
in complete decoded video/audio. Sixty-four native/control frame pairs are
inspected in sixteen contacts, with eighty both-channel tone windows and
forty-eight silence windows. Four positive AV source-handle observations point
inside the recipient bundles before/after isolated reopen. Fresh native saves
collapse only the established 42-field AV or 38-field text descriptor cohort,
apart from standard bookkeeping and native rich-property ordering.

Fifteen immutable operation states, fifty resource files and twenty directories
are retained; a verified seventy-member recovery ZIP precedes removal of the
five exact test Library roots. All original vendor bytes/identities, the whole
author bundle, themes and the pending 29-file collision Library/backup remain
unchanged. No native Delete is used. Source-free text retains the raw schema's
known `sourceBin` requirement discrepancy and passes the existing build profile;
no new profile correction is added. Seventeen fixed tests protect import deltas,
resource sharing, companions, metadata ownership, constructors and isolation.

Evidence: `build/native-verification/library-import-collisions-native-checks.json`,
the operation audit, native packages, immutable captures, recovery ZIP and
accepted render comparison. These are finite same-host AV/text cases, not a
complete import-collision algorithm, arbitrary resource or cross-host font proof.

## Within-Library folder and asset drags

Drag a populated folder onto an unused receiving folder to nest it within the
same Library. The tested mixed folder moves all seven files, both asset
directories and its empty child directory; every byte and physical file identity
is retained, and the old outer folder path disappears. A text asset can similarly
move into that empty child folder, then into a separate sibling branch, retaining
all three companion bytes and identities. These operations move existing items;
they do not duplicate metadata UUIDs or add media to the receiving timeline.
The resulting locations remain visible after a full editor restart.

Treat each drop's result separately. The tested occupied same-name folder target
leaves every path, byte and identity unchanged; it does not create a `(1)` entry
like the earlier cross-Library Move To case. Drops onto background space and
back onto an ancestor also leave these resources unchanged. An attempted parent
folder drop toward its own child instead opens **Confirm Delete**. That alert
was cancelled; the entire Library and empty timeline remain unchanged. This
diagnostic does not establish a safe descendant rejection or its internal cause.

- Use unused destination paths and observe the resulting hierarchy after a drop.
- Verify full contents and empty folders before treating a move as successful.
- Cancel an unexpected deletion confirmation and inspect the selected items.
  A drag is not authorization to delete assets.
- Do not infer a root-un-nesting gesture, modifier-copy behavior, multi-selection
  semantics or universal collision policy from these finite attempts.

Insertion from the persisted moved folder creates the established eight-ID AV
constructor and bundles the exact source in the recipient. Only that moved AV
asset's Last Used metadata advances; the independent occupied branch and moved
text metadata remain unchanged. Two native save/reopen/export pairs cover this
recipient installed and again in a fresh renderer with the entire test Library
absent. All four complete decoded AV streams match the independent grouped
control. Twenty native/control frame pairs are inspected in four contacts, with
forty both-channel tone windows and two positive bundled-source handle captures.

Eleven immutable operation captures and eleven fixed tests protect moves,
unchanged attempts, metadata ownership and isolation. A verified twenty-five-
member recovery ZIP retains fourteen files and eleven directories before removal
of the sole owned test Library. All original vendor bytes/identities, the whole
author bundle, themes and pending 29-file collision Library/backup remain
unchanged. No native Delete or new schema correction is introduced.

Evidence: `build/native-verification/library-drag-native-checks.json`, immutable
operation/control captures, cancelled dialog, recovery ZIP and accepted native
comparison. Root/ancestor return and the unexpected descendant-delete diagnostic
remain distinct from the completed valid nesting and asset-move cases.
