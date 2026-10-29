# Native verification and schema compatibility

Target: Camtasia **2025.0.3 for Mac**, project format **9.0**.
The separate [Mac version guide](mac-versions.md) records the additional
2026.2.4 / format-10 profile, native conversion, Tiling, and recorded-cursor
smoothing evidence. Select the matching profile explicitly.
Verification session: 2026-10-23. Probe projects use generated color-bar video,
a sine-wave audio track, and synthetic text. The person-segmentation test uses
a short local camera extract; it is excluded from distribution. Original demo
projects stay intact.

## Schema baseline

The researched pycamtasia schema is pinned to commit
`443a41e37cddb460c0aa6e046c951cb17f241bf3`, SHA-256
`e8df2fab865f9a42b953985c01a47bfc898da3641b50dc7d0af80af53794f08a`.
The schema-audit helper fetches and checks these exact bytes. Its profile adds
only corrections supported by this target editor's saved documents:

| Upstream constraint | Observed native result | Profile correction |
| --- | --- | --- |
| Root requires `sourceBin` | A new empty project saves without that key. | Make that key optional; source references still require semantic validation. |
| Timeline rejects `metadata` | Existing format-9 projects carry recording-dimension metadata. | Admit an object-valued timeline metadata property. |
| Ordinary-effect enum omits `Border` | Native saves retain `Border`; export accepts the project. The full-canvas probe does not expose an outer outline. | Add the saved identifier to that enum; test visible border geometry separately. |
| Ordinary-effect enum omits `Colorize` | Native saves retain `Colorize`; an export renders the color change. | Add the identifier to that enum. |
| Media union omits `Caption` | Dedicated SRT import creates a standalone `Caption` node with `parameters.captionData`; saved output renders both cues. | Add a strict branch for the observed unstyled point-caption clip. |
| Callout-kind enum omits `TypeWinPixelate` and `TypeWinHighlighter` | Native annotation presets save and render pixelation and highlighting. | Add the two observed kind identifiers. |
| Ordinary-effect enum omits `CursorPath`, `CursorHilight`, `ChromaKey`, and `DeviceFrameEffect` | Native UI operations save these identifiers; inspected native exports show cursor motion/highlight, corrected keying, and a desktop device frame. | Add those identifiers without relaxing other effect constraints. |
| Added `Caption` branch initially admitted numeric scalars only | A trimmed, 2× native caption save retains scalar `"1/2"`; native SRT export confirms its time mapping. | Admit positive integer-ratio strings as well as positive numbers; reject zero denominators and nonpositive values. |
| Ordinary-effect enum omits `BlurRegion`, `Tonal`, `FreezeRegion`, `Pixelate`, `MediaPath`, `Sketch`, `Reflection`, and `Sepia` | Native preset application, save/reopen, and inspected exports establish region blur/freeze, tint, mosaic, motion path, outlines, reflection, and sepia. | Add those exact identifiers; preserve other effect constraints. See [effect contracts](advanced-features.md#region-color-and-movement-effects). |

The profile is restricted to the exact authoring-client identity and format.
It retains type checks, other enums, required fields, and unknown-property
rejections. It does not set `additionalProperties: true` across the schema.

Resolve this skill directory to absolute `camtasia_skill_root`, then run:

```bash
uv run --no-project --with jsonschema==4.26.0 python -B "{camtasia_skill_root}/scripts/schema_audit.py" fetch --out "<schema-cache.json>"
uv run --no-project --with jsonschema==4.26.0 python -B "{camtasia_skill_root}/scripts/schema_audit.py" check --schema "<schema-cache.json>" --profile mac-2025.0.3 "<project>"
```

Omit `--profile` to test strict upstream conformance. Output separates
`upstreamErrors`, corrected `errors`, and `nativeCompatibilityErrors`. Exit 0
means those checks pass; exit 1 reports failure and exit 2 is invalid CLI usage.
`fetch` never executes downloaded data and refuses an unexpected hash or a
different file already occupying the cache path.

## Findings that structural conformance misses

**Ordinary geometry points can collapse to static values.** The format-10 Mac
2026.2.4 `VMFile` translation0/1 controls accept zero-duration double keyframes
under the schema, then fold them into static or initial values in native saves.
An animation marker alone does not turn those points into timed movement.
The [point-limit investigation](animations.md#ordinary-geometry-point-limits)
has four controlled shapes, two decoded-identical exports, measured frame
bounds and stable reconstruction. Validation warns without changing the input;
the interval helper preserves ambiguous point-shaped curves through refusal.

**Duplicate sibling track indices can prevent native opening.** A format-10
Mac 2026.2.4 fixture copied `trackIndex: 2` into two additional scene lanes.
Schema and earlier structural checks passed, but native opening stalled while
handling a corrupt project. The retained sample includes a cloud-path lookup;
that stack does not establish a cloud-service fault. A copied fixture differing
only at those two index fields opened and saved normally. The helper now rejects
duplicate present integer indices within each scene or Group's sibling tracks.
It does not infer contiguous indices or compare different parent containers.
Evidence is `matte-owners-native-checks.json` and the retained opening diagnostic.

**A valid list of overlays can still collide on a native lane.** A format-10
Mac 2026.2.4 vertical candidate passed the community schema/profile and core
structural checks, then failed native opening with `Collision exception.`
Concurrent panels and labels had shared scene lanes. Separate lanes resolved
the failure; the corrected project has two fresh-process exports with identical
decoded video/audio. The helper now rejects the reproduced scene-lane collision
through its native hazard check; see [helper scope](helper.md). Existing 444
accepted native snapshots pass this guard. Caption color precedence and the
separate frozen-highlight export finding are in [captions](captions.md#longer-vertical-edits-and-export-checks).

**A behavior payload can crash the native parser while passing the schema.**
The original generated `pulsating` phase had a static double `scale` default
plus a redundant point keyframe at zero. The crash stack reached
`AnimationTrack::mutex` from `readBehaviorParameterList`. Removing that
redundant keyframe allowed the same corpus to save. The project helper rejects
the reproduced shape for this build before a write. The schema-audit helper
includes that semantic guard as a separate result.

**Saving a document does not establish rendering support.** A ten-preset
behavior probe saved through Camtasia, then produced its “contains unsupported
features” warning at export. The extra `flyOut`, `emphasize`, and `jiggle`
identifiers each produced that warning in independent native open probes and
remain outside the compatibility overlay. The schema-listed set
`reveal`, `sliding`, `fade`, `flyIn`, `popUp`, `pulsating`, and `shifting`
exported through the native renderer after the keyframe correction.

**Behavior acceptance is not correct phase timing.** Lengthening each generated
text clip to eight seconds left the community effect's duration at 0.8 seconds;
Reveal remained invisible and Sliding disappeared early. A native Reveal applied
through the editor's preset context menu → Add to Selected Media serialized
`start: 0`, duration equal to the eight-second clip, different in/out type values,
and an actual Reveal center phase. That native control rendered visible text.
A second seven-label comparison used the native Reveal phases and matched each
effect's start/duration to its clip-local interval. All seven labels were visible
in inspected middle frames, with samples near entry and exit also checked.
Clone native behavior phases and preserve their clock and duration relationship;
changing only a containing clip's length does not retime its behavior safely.

**A generic image clip is not a native freeze-frame constructor.** The tested
community freeze helper placed a held `IMFile` against a video source and
overlapped the original clip. Camtasia refused that project with OSStatus -19.
The replacement uses an extracted PNG, its image-source definition, and
non-overlapping left/hold/right intervals. That replacement saved and exported
through Camtasia. Preserve original video and audio offsets around the hold.

**Native saves can mirror visual effects on linked media.** Several probes
started with an effect on a `UnifiedMedia.video` child; the editor saved the
effect on both the wrapper and the child. Compare the native feature and its
rendered result; do not deduplicate those nodes by effect-name counts.

**Constructor defaults need output checks.** The tested community
`ColorAdjustment` constructor serialized contrast zero and exported a flat gray
frame, rather than the intended saturation-only change. Do not treat its
successful save/export as proof of neutral defaults. Obtain same-build native
parameters before synthesizing a color adjustment. A follow-up with contrast
1.0 and saturation 0.2 saved, reopened, and exported the expected desaturated
picture on this build; the original constructor's contrast 0.0 was not neutral.
Its keyframe convenience method also initialized animated scale and opacity to
zero, making the transform probe invisible before the later opacity keyframe.
Set defaults from the intended initial state rather than accepting that method's
generic numeric zero.
A corrected initial scale/opacity of 1.0 exported a visible start, zoom, pan,
and later fade; endpoint frames were inspected.

**Caption convenience methods may create ordinary text.** The tested
`timeline.add_caption` created `Callout` nodes without a caption modifier.
That probe establishes text overlays, not imported closed captions, native
transcription, or word-highlighting support.
A separate native Add Caption probe produced a `caption` parameter on the
linked `AMFile`. Two texts with a four-second boundary saved and exported as
native burned-in captions. The caption reference records the actual paths and
clock observation. A subsequent dedicated SRT import produced a standalone
`Caption` clip with `parameters.captionData`, rather than the audio-child path.
Its two cues saved and rendered the expected texts at two and six seconds.
A follow-up native web export also passed local CC-toggle and cue-text
checks; the caption reference records the export-mode constraint.

**An exported effect can be outside the visible canvas.** Full-canvas border
and shadow probes exported, but their inspected frames did not expose the outer
effect. Scale the subject inside a contrasting canvas before claiming visible
border/shadow behavior. The annotation probe also clipped part of its Unicode
string; a saved text value is not proof that the entire string is visible.
An inset subject subsequently exported with a visible red border and passed
two native save/close cycles. A black shadow against a black canvas remains an
inadequate visibility probe even when the subject is inset.
A white-background follow-up exported a visible soft shadow.

**Motion blur needs a moving control.** The initial stationary probe proved
renderer acceptance only. Adding the native `MotionBlur` effect at intensity
1.0 to the corrected transform probe produced visibly softer, smeared moving
edges at 1.4 seconds than the matching export without the effect. Preserve
the initial scale and opacity so an invisible subject cannot masquerade as blur.

**A matte needs actual alpha content.** Changing an empty text callout's shape
identifier to an ellipse without fill properties produced black output through
the alpha matte. The installed native ellipse preset specifies `fill-color` and
`fill-style`; the shape identifier alone does not establish an opaque fill.
Adding those native fill properties produced a circular matte in an inspected
native export.

**Rich-text ranges use a different unit from Python string length.** The
exercised `Unicode: café — 日本語` callout has 19 characters and 28 UTF-8 bytes.
The community constructor's range end of 19 omitted the Japanese suffix even
after changing to an installed CJK font. Changing only the rich-text range ends
to 28 rendered the complete string. See the caption reference for the exact
locations and the helper's advisory coverage check.

**Confirm the timeline before export.** One native session displayed the
candidate name while retaining a mismatched one-minute placeholder state. Its
movie was quarantined as failed evidence. Reopening the saved candidate through
the editor and checking the source, tracks, duration, and preview produced the
correct eight-second color-adjustment output. A title or scripting document URL
alone does not establish which visible content the renderer will use.

**The scripting dictionary includes unreliable hidden commands.** Reading
the advertised project width failed with an AppleEvent handler error; adding
media through an empty track's hidden scripting handler crashed in
`NSScriptCommand`. The shipped native adapter uses the exercised standard
document open/save/close operations and verifies the document URL before save.

## Serialized native work and stability

On macOS, a CUA app binding can leave the application in the background.
Window Raise alone did not restore Chrome's native exit control in the resume
probe. Use CUA Finder to open a new task-owned window, select the installed app
bundle through Go to Folder, and invoke its observed **Open Finder item** action.
Recheck the exact owned project/tab before continuing. Opening the installed
Chrome app restored the native button's action. Close the task-owned Finder
window after verification. This is an observed activation recovery, not a
reason to repeat successful feature edits through UI.

The Mac 2026.2.4 native accessibility `playheadSlider` uses project ticks,
not seconds. The observed four-second position is `2822400000` at edit rate
`705600000`; setting its value to `4` stays within the displayed first frame.
Confirm the editor's DurationLabel before a timing-sensitive native capture.
The exported browser player's progress slider uses seconds instead. Do not
transfer units between these surfaces.

Use one native verification project at a time. Before automation, run the
read-only preflight with the loaded skill root:

```bash
python3 -B "{camtasia_skill_root}/scripts/native_health.py"
```

It emits `ok`, `problems`, native process identities, and system privacy-service
status. Failure exits 1 and forbids scheduling the next native operation;
invalid CLI arguments exit 2. See the script's module contract for its health
criteria. It never launches/kills apps, resets permissions, or restarts services.
For a continuing automation session, pass the first successful result's privacy
PID with `--expected-tcc-pid` on subsequent checks. Re-observe health after the
native operation; a preflight cannot guarantee future operating-system health.

Process health does not establish editor responsiveness. If UI observation or
an AppleScript request times out, observe that same operation before sending
more input. Do not repeat an open, export, or write from an unknown state.
Retain a read-only process sample when available. A normal app restart must
include the recorded editor PID exiting and a new exact-bundle PID appearing;
closing a document or returning to Welcome does not establish a restart.

For sustained disposable tests, keep native groups short and quit normally
between groups after saving and closing the owned documents. On this build, a
long-running session separately stalled in tooltip/WebKit initialization and
system-power registration while opening a document, with a healthy privacy
service and no thumbnailers. Shorter sessions are an operational precaution,
not proof of the internal cause or a permanent fix. Verify the old process has
exited before starting the same exact app again; retain completed renders.

Media import can also stop responding before it reaches source decoding. A
Mac 2026.2.4 import of a local MP4 under `/private/tmp` blocked in
`SourceManager.autoProxyFilesIfNecessary` → `NSURL(CloudDrive).isOnOneDrive`
→ dictionary file read → filesystem `open`. Read-only document queries timed
out while the process/privacy preflight still passed. That preflight does not
certify editor responsiveness. The sample does not identify the blocked read's
path, establish that the imported source is cloud-hosted, or prove a corrupt
media file. Apply the timeout/recovery procedure above; preserve the selected
source path and sample rather than repeating the import or changing cloud
configuration from this stack alone.

The media Quick Property investigation encountered the same main-thread import
stack. Its saved project remained byte-identical, while `~project.tscproj` had
already recorded the new source. Native Activity Monitor selected only the exact
hung test PID for Force Quit. The helper refused an offline candidate with that
recovery data present. After preserving it, native Project Recovered → Open
retained the import; Save bundled the source, without another import or cloud
configuration change. The new exact-bundle process later completed native
reopen/export and normal Quit. Retain recovery bytes and inspect the native
prompt rather than deleting them to satisfy a closed-project check.

The direct-Library comparison repeated this recovery for three unique local
inputs: MP4, stereo WAV and PNG. Each ordinary import stalled in the same
OneDrive-classification/read stack after recording its source. Each saved and
recovery bundle was independently preserved before native Activity Monitor
quit only that hung PID; native recovery/save retained the input without a
second import. The finished three-source ordinary-import and Library recipients
both completed fresh-process save/reopen/render pairs with positive bundled AV
handles and matched output. No cloud setting or system service was changed.
This demonstrates recovery of these three imports, not a permanent import fix
or identification of the unknown blocked file path.

A separate Mac 2026.2.4 close operation stalled after its native export had
returned successfully. The main thread was destroying audio preview and
waiting through PortAudio stop, `AudioOutputUnitStop`, and CoreAudio
`StopIOProc` on a mutex. Read-only document queries timed out with healthy
privacy-service state and no thumbnailers. Retain the completed export proof;
closing the document is still incomplete. Preserve the sample and use the
same editor-recovery procedure above. This stack does not identify a failed
audio device or prove another desktop watchdog.

A missing computer-use window is not by itself an editor hang. If the OS reports
the desktop locked while a read-only document query responds, retain the active
document/export state and wait for desktop access. Do not restart the editor,
re-export, or certify completion solely from a movie's presence. Re-observe the
same owned window after unlocking and finish the pending operation's checks.

The save/reopen adapter performs these checks before native execution and after
it returns. Its result includes `nativeHealth.before` and `nativeHealth.after`.
A failed initial check leaves the candidate and backup directory untouched.
A failed post-save check names the retained original backup; the candidate may
already contain a native save. Stop further editor work and inspect that state.

The adapter also requires one running Camtasia editor. It resolves that
process's executable and app-bundle metadata, verifies the Mac authoring build,
and checks the format for the shipped exact-build profiles before backup or
native calls. `--editor-app "<absolute-Camtasia.app>"` optionally requires that
exact running bundle. The adapter does not choose an installation by display
name or launch a different build. Unknown author identities and conversions use
the explicit editor workflow in [Mac versions](mac-versions.md).

The selected bundle path is passed to the native invocation. AppleScript's
`using terms from` supplies compile-time vocabulary; its runtime `tell` target
is the verified app path. [Apple's terminology/target distinction](https://developer.apple.com/library/archive/documentation/AppleScript/Conceptual/AppleScriptLangGuide/reference/ASLR_control_statements.html)
The native layer requires no other documents before each open and verifies the
candidate URL before save. A changed editor process, authoring identity, or
project format fails verification and names the retained backup.

If the desktop hangs, the privacy service restarts, or native helpers persist,
stop native automation and continue independent file/schema work. Preserve
current projects and diagnostic reports. Do not retry a failed preview/batch
workflow, reset licensing/permissions, or restart system services as recovery.
Resume with a healthy preflight and a single disposable project after the
failure has been investigated. Use normal editor cancellation/quit to stop an
idle owned test session; do not discard another person's unsaved document.

On the observed 2026.2.4 installation, adding 25 projects to the native Batch
Export picker twice coincided with WindowServer watchdog failures. Each report
contains over 270 `CLThumbnailer` processes, and WindowServer's main thread was
waiting for the throttled system privacy service on its ListenEvent preflight
queue. This establishes the failure pattern, not Camtasia as its sole cause.
Avoid Batch Export and the multi-preview Export History workflow during
verification on an installation showing this pattern. Use individual local
exports and capture their completion dialogs and actual output streams.
If a completion dialog is not exposed, retain the exact native destination,
export options, and observed return to the expected editor document. Decode the
whole actual output and verify its duration, dimensions, video, and audio.
Record that evidence path explicitly; do not invent a completion dialog or
open Export History to fill the observation gap. Independently close/reopen the
saved project and repeat the export before accepting persistence.
Earlier completed batch comparisons remain scoped evidence; they do not certify
that a long automated batch session is stable.

The native Welcome window can cover an existing editor/export panel. A Welcome
observation alone does not prove the project closed or export stopped. Inspect
**Window**, select the exact expected project entry, and reobserve its document
or pending panel before continuing. Never repeat an export from a tool timeout
without checking the destination, output files, and current native state.

## Native adapter procedure

The only Platform-Bound Untestable Carve-Out artifact is
`scripts/native_roundtrip.applescript`. Its exempt interaction is execution
inside Camtasia: open the requested document, save/close it, reopen it, and
save/close it again. Its Python caller's parsing, ownership checks, backups,
response validation, and failure handling have ordinary unit tests.

1. Start the candidate's matching Camtasia Mac build and close its other
   documents. Use a disposable, closed candidate with valid source paths.
2. Run `python3 -B "{camtasia_skill_root}/scripts/native_roundtrip.py" "<candidate>"`.
3. Confirm it reports the candidate path, original-byte backup, before/after
   hashes, selected `editor.app`/`pid`/`version`, `saveReopen: true`, and a passing
   structural report. Wrong bundle/build/known format must refuse before backup
   and native execution. The same editor PID must remain across the operation.
4. Open the candidate in Camtasia. Confirm expected tracks, clips, source
   selections, and native effects. Check any repair or missing-media dialog.
5. Export a local movie. An unsupported-feature warning fails feature support
   even when the earlier save/reopen succeeded.
6. Inspect the rendered frames at changed boundaries and animation endpoints;
   listen to changed audio and verify the requested visible or audible effect.

A pass requires the relevant native observations, not merely successful
AppleScript execution. The adapter deliberately reports `renderVerified: false`;
the invoking workflow continues through export and inspection.

The exact-bundle revision passed this procedure on Mac 2026.2.4 / format 10
with both 2025 and 2026 bundles installed. Two native save/close cycles retained
the original-byte backup and project state apart from a source cache timestamp.
Independent editor reopen/rerender reproduced the control's fully decoded
video/audio. A separate test with another disposable document open refused
before saving or closing either project; both JSON files remained byte-identical.

## Probe coverage

Mac 2026.2.4 Lottie import and per-clip recoloring have two independent native
pairs with identical complete decoded streams and fifteen inspected native frames
beside background controls. A fresh-process baseline uses only bundled source
bytes with the original import path absent. The raw pinned schema and existing
exact-build profile both pass without changes. [Lottie](lottie.md) records the
source/clip clocks, native static-parameter collapse, per-instance reset metadata,
color-channel observations, and the boundary between shape closure and external
image/font dependencies. A third pair verifies automatic grouped color Quick
Properties, retaining child bindings and exact decoded parity with the ungrouped
output. Four more grouped frames are inspected beside ungrouped references.
The subsequent [color Quick Property lifecycle](quick-properties.md) has fifteen
native captures, a two-minute independent native pair with identical decoded
streams, and 45 inspected frames. Strict comparisons retain the explicit native
75-clip ID/reference map and duration-label update while preserving all other
payload, sources and audio. Both raw/profile schema checks pass unchanged.

Text/typography Quick Properties add 23 native captures and a 184-second
independent export pair with identical complete decoded video/audio. All 46
native visible/post-end frames are inspected beside repeated controls. Integer
child bindings, UTF-8 byte ranges, rich-run style codes, default-font preservation,
alignment, overall Callout opacity, text stroke and spacing/fitting are retained
under strict payload checks. Native saves permute the demonstrated unique eight
rich-property entries; comparison retains every entry field and refuses to
normalize unknown/mixed/duplicate sets. The size combo's uncommitted display
is retained as a separate negative diagnostic. Both schema checks pass unchanged.
Physical font-file identity and media replacement require separate cases;
see [the text contract](quick-properties.md#text-group-constructor).

A second 23-case text lifecycle establishes font-theme application and linking,
with another 184-second independent native pair and 46 inspected frames. It
captures the five-property rich-run form, both font resources and all five text
color resources, first-text/second-font precedence during linking, shared edits,
unlink, remove/re-add, independent remapping and the second appearance control.
Native payload comparison preserves all fields and remaps integer child bindings
with 138 storage-order clip nodes. Expected white-on-white and dark-on-dark
states are recorded beside later visible contrast states. Raw/profile schema
passes unchanged. Exact synthetic theme files are archived after normal Quit,
with preexisting user bytes unchanged; the [linked-text contract](quick-properties.md#two-text-constructor-and-font-themes)
retains dependency and physical-font limits.

The [media Quick Property contract](media-quick-properties.md) adds three initial
constructors and seven lifecycle captures, a 56-second independent native pair,
14 inspected frames and 28 audio windows. Both complete decoded streams match.
The native source switch includes both AV children, while clear creates a
transparent Callout and removes audio. Source restoration, property visibility,
re-add and unapplied Logo mapping retain their observed owners. Strict resave
permits only demonstrated static-descriptor collapse and cleared-box default
addition. Both bundled source hashes and all other payload remain checked;
raw/profile schema passes unchanged. Nine additional applied Logo/image states
have a 72-second pair and a third fresh-process render with the original theme
paths absent. All complete decoded outputs match; 18 frames and 36 audio windows
verify image fitting, clear/restore, visibility and image-to-AV replacement.
Temporary owned theme copies are archived with preexisting user bytes intact.
Fifteen two-AV link/unlink/independent-edit states add a two-minute native pair
with identical complete decoded streams, 30 inspected frames and 60 both-channel
audio windows. Integer bindings track native ID reallocation during clear/restore.
Picture references retain the earlier verified native source-color interpretation;
raw source pixel equality is not asserted. Fifteen mixed image/AV states add
another two-minute pair with matching complete decoded streams, 30 inspected
frames and 60 audio windows. Image fits remain square; AV fits the original wide
boxes. Relinking with an unmapped second entry removes the first mapping. Exact
incidental Group movement is retained in captures and explicitly reset in the
comparison sequence. Ten trimmed/styled states and eight direct controls add a 72-second pair,
36 inspected native frames and 72 audio windows. Source replacement resets the
old trim; clear/restore loses audio gain while retaining Colorize/opacity. The
format-10 profile adds the observed Colorize identifier missing upstream.
Ten short/portrait/wide states and three direct controls add a 52-second pair,
52 inspected native frames and 104 audio windows. Short AV clamps to two seconds
inside a retained four-second Group; late output is black and silent. Longer
replacement and clear restore the remembered four-second duration. Native aspect
fit and distinct track/audio sample clocks remain checked. Both imports recover
their saved autosave sources after the same sampled import stall; neither import
is repeated. Both original input paths are absent during exports after restart,
and all four bundled sources remain byte-identical. No new schema correction is needed.

An accessible project can have controls outside the visible desktop. In the
Lottie investigation, element actions returned `elementHasNoFrame`, coordinate
actions returned `windowNotFoundAtPosition` with negative coordinates, and some
clicks returned `noWindowsAvailable`, while macOS reported an unlocked desktop
and the editor remained healthy. The native **Window → Fill** menu restored
onscreen geometry and normal selection. Check window placement alongside desktop
and process health when diagnosing these errors; retain a fresh observation
after moving/resizing before using control coordinates.

The later native Window menu can place display destinations under Move To.
Its exposed child item returned `AXError.invalidUIElement`; keyboard selection
of the observed Move To entry, Right and the selected Built-in Retina Display
then Return moved the window successfully. Reobserve actual placement and use
Window → Fill before deriving new drag coordinates. A selected Media Bin source
and an unexpected deletion prompt are not replacement evidence; cancel the
unrequested prompt and compare the saved project before proceeding.
An incomplete annotation drag can also leave File commands disabled. Cancel
the drag and press Escape, then reobserve enabled Save/Close commands before
continuing. Asset selection alone does not establish insertion.

The session exercises native empty and imported-media saves; linked AV;
annotations with Unicode text; audio envelopes; visual transforms and opacity;
transitions; nested groups; placeholders; speed changes; and a
real-image freeze. Effect probes cover borders, rounding, color adjustment,
colorization, blend mode, shadow, glow, matte, motion blur, and spotlight.
Text-overlay captions are distinct from native imported closed captions and
source-level dynamic recognition. The feature map preserves that distinction.
Marker, timeline-metadata, and a disposable stitched-media clone subsequently
passed two native save/close cycles. The marker probe normalized wrapper-level
`parameters.toc` into the linked video child; the feature map records that path.
Twenty original feature documents have first-save results; that count
does not assert that every original variant rendered correctly. Corrected
representatives across those feature families subsequently reopened, including
the six-/ten-second speed/freeze cases and both caption structures. The initial pass produced thirty-six native
movie files. They include visible rounded corners, spotlight,
nested-group text, an inset border, visible shadow, corrected color/transform
defaults, a circular matte, full Unicode text, native caption text, moving-subject
blur, and the corrected behavior phases. The
original failing variants are retained alongside their corrected probes.

The broader pass adds functional placeholder replacement; native blur,
pixelation, and highlighting; chroma key with a measured correction; person
background removal; created cursor paths and cursor highlighting; device
frames; both trimmed/sped-up caption forms and SRT export; template archive
export/import/instantiation; and PQ/converted-SDR input rendering. Local Smart
Player playback exercises a six-second hotspot seek, all four native quiz
question types, and SCORM 1.2 initialization, interactions, score/status, commit,
and finish calls. See [additional native contracts](advanced-features.md) for
serialization and delivery details, and [captions](captions.md) for the measured
clock formula. Generated paths do not establish captured-cursor smoothing.
A local mock LMS does not establish a destination LMS's import or resume policy.

The session encountered an activation mismatch and startup failure. TechSmith's
bundled support tool's Licensing → Reset Cache, followed by native license
refresh, restored a normal launch and a real MP4 export. Preserve recovery
copies before a cache reset; this is an application recovery operation, not a
project JSON repair. An activation dialog is not an unsupported-feature result
or a successful export. Verify the actual output file even when UI automation
fails after a completed render.

The native verification record in the repository's `docs/verification.md`
records the observed outcomes and renderer evidence from this session. ACR
does not publish that repository-only report; this reference carries the
operational findings needed by installed consumers.
