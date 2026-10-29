# Research and provenance

Research dates: 2026-10-23–27. Refresh links and recheck product behavior when
supporting a different Camtasia release. Upstream commit links preserve the
research baseline; they are evidence, not runtime dependencies.

## Official behavior documentation

| Source | Establishes | Does not establish |
| --- | --- | --- |
| [TSCPROJ and TREC](https://support.techsmith.com/hc/en-us/articles/203730028-Working-with-Camtasia-Editor-TSCPROJ-and-TREC-Files) | Project versus recording roles and source dependencies. | Complete JSON field schema. |
| [Saved recordings](https://support.techsmith.com/hc/en-us/articles/203727488-Location-of-Saved-Recordings) | Durable/standalone project handling. | All binary TREC layouts. |
| [Project recovery](https://support.techsmith.com/hc/en-us/articles/203727268-Error-Cannot-Open-Project) | Project and recovery documents inside Mac bundles. | A recovery file as a reliable process lock. |
| [Legacy project conversion](https://support.techsmith.com/hc/en-us/articles/360048452272-Opening-Camproj-and-Camrec-Files-in-Camtasia-2020-and-Later) | Legacy formats require conversion through older editors. | Compatibility by changing a version string. |
| [Animations](https://www.techsmith.com/learn/tutorials/camtasia/animations-in-depth/) | User-visible animation behavior. | Exact serialized keyframe enums. |
| [TechSmith 2023 help, Media Matte](https://www.techsmith.com/blog/wp-content/uploads/2024/05/Camtasia-2023-Help-EN-1.pdf) | Four media/track matte modes and the track-eye menu workflow. | Current Mac JSON enums, intensity/bypass equivalence or a depth formula; use the independent [native matte contract](advanced-features.md#media-and-track-mattes). |
| [Transitions](https://www.techsmith.com/camtasia/features/video-transitions/) | Native transitions exist. | Allowed JSON names and attributes for a given build. |
| [Interactive hotspots](https://support.techsmith.com/hc/en-us/articles/360029430091-Add-a-Clickable-Link-to-Your-Video-Using-Interactive-Hotspots-Video) | URL and navigation interactions. | Full hotspot serialization. |
| [Quizzing changes](https://support.techsmith.com/hc/en-us/articles/14539861012237-Changes-to-Quizzing-in-TechSmith-Apps) | Current Results Service retirement and supported quiz delivery routes. | A current hosted quiz analytics service. |
| [TechSmith 2020 help, Working with Quizzes](https://www.techsmith.com/learn/wp-content/uploads/2022/01/Camtasia-Help-2020.0.8.pdf) | Historical select/hover/click pin/unpin gesture, then independently exercised in current Mac native captures. | Current hosted quiz reporting or an inferred current JSON clock contract. |
| [ADL SCORM 2004 API interface](https://github.com/adlnet/SCORM-2004-4ed-Test-Suite/blob/050f1b4282c914154ab80254e4767ce8c58d0d36/software_development/src/org/adl/api/ecmascript/SCORM13APIInterface.java) and [lifecycle error codes](https://github.com/adlnet/SCORM-2004-4ed-Test-Suite/blob/050f1b4282c914154ab80254e4767ce8c58d0d36/software_development/src/org/adl/api/ecmascript/APIErrorCodes.java) | Eight standard API signatures, string returns and lifecycle error identities used by the local observation adapter. | A complete LMS, certification or Camtasia JSON serialization. |
| [ADL runtime data model](https://github.com/adlnet/SCORM-2004-4ed-Test-Suite/blob/050f1b4282c914154ab80254e4767ce8c58d0d36/software_development/src/org/adl/datamodels/ieee/SCORM_2004_DM.java) and [TechSmith Smart Player session-exit guidance](https://support.techsmith.com/hc/en-us/articles/360016509591-Update-the-Version-of-the-TechSmith-Smart-Player) | Entry vocabulary, suspend/resume session-flag resets, native exit/confirmation route and documented resumption behavior. | The Camtasia project's JSON schema, a full production LMS or untested restart/error paths. |
| [Mac 2026 history](https://support.techsmith.com/hc/en-us/articles/41263167862285-Camtasia-Mac-2026-Version-History) | Version introduction of VTT, audio alignment, WebM export, and other current features. | Serialized field contracts or successful execution on a particular project. |
| [Audiate integration](https://support.techsmith.com/hc/en-us/articles/39967435209485-Using-Camtasia-Audiate-with-Camtasia-Editor) and [included-capability installation](https://support.techsmith.com/hc/en-us/articles/41334438405773-How-to-access-the-included-Audiate-features-with-Camtasia-Editor) | Separate application, supported handoff, timeline/media sync scopes. | Observed native synchronization or JSON constructors. |
| [Zoom recording import](https://www.techsmith.com/learn/tutorials/camtasia/edit-zoom-recording/) | Host-recording restriction, connected import, Rev and ordinary media choices. | An authorized service connection or successful import in this session. |
| [Mac Snagit 2026 history](https://support.techsmith.com/hc/en-us/articles/41975263481613-Snagit-Mac-2026-Version-History) | Step Capture handoff version requirements. | The resulting native project shape or dependency closure. |
| [Caption troubleshooting](https://support.techsmith.com/hc/en-us/articles/43374924720397-Captions-Troubleshooting-for-Camtasia-Editor) | Vendor procedure for SRT/VTT import or display failures using a UTF-8 BOM copy. | A requirement inferred from the successful native SRT probe. |
| [SAMI synchronization](https://learn.microsoft.com/en-us/previous-versions/windows/desktop/dnacc/understanding-sami-1.0) | Millisecond start times and explicit blank paragraphs in SAMI. | TechSmith's imported JSON or preservation of the final caption end. |

No official complete `.tscproj` JSON schema was located in this research.
Do not interpret that search result as proof that none exists privately.

## Community implementation

[pycamtasia](https://github.com/grandmasteri/pycamtasia) is a primary source for
its own reverse-engineered implementation, not for TechSmith guarantees.
Reviewed commit: `443a41e37cddb460c0aa6e046c951cb17f241bf3`.

- [Schema](https://github.com/grandmasteri/pycamtasia/blob/443a41e37cddb460c0aa6e046c951cb17f241bf3/src/camtasia/resources/camtasia-project-schema.json): structural vocabulary for another format baseline.
- [Field reference](https://github.com/grandmasteri/pycamtasia/blob/443a41e37cddb460c0aa6e046c951cb17f241bf3/docs/camtasia-format-reference.md): lookup material for exact paths and version differences.
- Feature-specific source files are linked from the feature and caption references.

The upstream describes validation against TechSmith samples. That claim is not
independent proof of all versions/features. No library code, schema, sample
media, or proprietary presets are vendored here. Fetch and review only the
relevant source when a new feature needs investigation.

Three upstream fixtures labeled as TechSmith samples were inspected from a
temporary download: formats `5.0`, `6.0`, and `8.0`, including nested groups,
callouts, linked AV, and stitched media. The helper reported no structural
errors in those documents beyond missing media files absent from the download.
This was a parsing check, not independent provenance or native acceptance proof.

## Local evidence

- Six `port-demo` project bundles, original and versions 2–5: format `9.0`; ordinary and unified
  media, stitched frame holds, native zoom keyframes, round presenter effects,
  and preserved AI noise removal. Original files remain untouched. All six
  were checked against the pinned schema and partial semantic validator.
  Five pass media resolution; version 2 retains two missing temporary recordings.
- `port-demo` editorial/review notes: source-frame proof, missing original
  recordings, HDR conversion, cached replacements, duplicated narration risk,
  and the distinction between source previews and final native export.
- Claude project memory: identified the later speaker-toolkit extraction.
  Available Codex project memory/session index was checked; no additional
  Camtasia format contract was found there.
- [speaker-toolkit format notes](https://github.com/jbaruch/speaker-toolkit/blob/main/skills/screencast-editor/references/camtasia-format.md)
  and [production lessons](https://github.com/jbaruch/speaker-toolkit/blob/main/skills/screencast-editor/references/production-lessons.md):
  recorded workflow observations, not a required dependency of this plugin.
- Installed Camtasia 2025.0.3 for Mac: native annotation JSON files and
  `ThemeEditorDemo.tscproj` exist in app resources. That demo identifies itself
  as an older format/client; an app installation can contain legacy examples.
- Disposable native probes: generated AV, real-image holds, synthetic text,
  and isolated community feature constructors. Twenty feature documents saved
  through the editor in the initial pass; thirty movie files were exported
  after activation recovery and follow-up probes. The shipped adapter completed
  two save/close cycles on a candidate with spaces, markers, timeline metadata,
  a stitched-media clone, inset effects, and the color-adjustment correction.
  Later UI-created caption parameters and UTF-8 range corrections have saved
  project and rendered-frame evidence too.
  See [native verification](native-verification.md) for schema corrections,
  parser crashes, rejected features, and the limits of those observations.

## Extending evidence

Library sources: TechSmith's [Mac Library overview](https://support.techsmith.com/hc/en-us/articles/229859268-Using-Camtasia-Editor-Media-Assets-on-Mac)
describes the asset workflow. Its [fall-2026 default-asset notice](https://support.techsmith.com/hc/en-us/articles/41310557595917-Where-are-the-Camtasia-Library-Assets)
distinguishes downloadable legacy assets from custom user Libraries. Inspect the
actual installation; the tested host retains a Camtasia 2025 vendor Library.
The [native Library contract](library.md) establishes current Mac asset/archive
serialization, isolated source copies, insertion/remapping, installed-resource
closure and the measured grouped-audio endpoint with a verified ungroup remedy.
Its separate text-only controls establish canvas/visible bounds, omitted unused
sources, exact-byte rename/copy/move behavior, preview/sort/search and native
rendering before and after installed asset removal.
Mixed-Library controls establish duplication, Library/folder rename, populated
folder copy/move, shared resource files, whole-Library archive contents and
isolated re-import. These use exact native filesystem captures and three
independent render pairs, including an installed-Library-absent renderer.
Direct PNG/WAV/MP4 controls add typed native constructors, source clocks,
video/image/audio Media Type ordering and ordinary-import comparison. Two more
native pairs repeat complete decoded AV with all loose originals packed away;
independent picture/stereo-tone checks and positive bundled AV handles establish
source presence separately from matching output. Installed collision-recipient
rendering is also accepted; permanent Library deletion remains separate.
Native naming controls distinguish occupied-name refusals from allowed equal
folder/asset labels. Default/vendor Start from copies and mixed duplication with
equal labels retain actual files and resource identities; two more native pairs
verify AV insertion and fresh-process reuse after all owned Libraries are packed
away. Vendor-copy coverage establishes copying, not rendering every vendor asset.
Fifteen archive-import states expose a two-project shared container, misleading
Last Used metadata, both-project native exports and row coalescence after restart.
Native unique-name intake avoids the demonstrated merge. Eight more native pairs
match independent AV/text controls installed and with every donor test Library
absent, with positive AV bundle handles and inspected native/control frames.
Within-Library drag controls add populated-folder nesting, asset moves into a
child and sibling, unchanged drop attempts and a cancelled unexpected deletion
prompt. Two more native pairs match the grouped control with donor resources
installed and absent. These native observations remain separate from generic
Library organization guidance or inferred drag-operation codes.
These locally observed fields are not an official complete asset schema.

Lottie sources: TechSmith's [native JSON import procedure](https://support.techsmith.com/hc/en-us/articles/360060035772-Add-Lottie-Animations-to-Camtasia-Editor),
the primary [property/keyframe specification](https://lottie.github.io/lottie-spec/latest/specs/properties/),
the [shape specification](https://lottie.github.io/lottie-spec/latest/specs/shapes/),
the [image-asset specification](https://lottie.github.io/lottie-spec/latest/specs/assets/),
and LottieFiles' [font and embedded-character documentation](https://lottiefiles.github.io/lottie-docs/text/).
The [local native contract](lottie.md) separates those animation definitions from
observed Camtasia serialization and independent native render evidence, including
twelve internal image/font/glyph cases across withholding, restoration and an
actual bundle move. Player format documentation is not a Camtasia support guarantee.
TechSmith's [Quick Property asset overview](https://support.techsmith.com/hc/en-us/articles/360032837791-Customize-the-Intros-Lower-thirds-and-Outros-in-Camtasia-Editor-Video)
describes the customization surface; [native color and text editing](quick-properties.md)
records the exercised Mac serialization, integer versus media/property bindings,
UTF-8 typography ranges, font-theme and linked-text operations, and rendering evidence.
The separate [media property contract](media-quick-properties.md) records native
AV/image replacement, applied Logo fitting and source allocation, transparent
clearing, metadata changes, bundled-image closure and recovery evidence.
Its two-AV linking cases distinguish native source-render controls from raw
decoded source colors and verify both audio contributions separately. Mixed
image/AV linking additionally verifies square fit, type/ID changes, independent
replacement and removal of the first mapping by an unmapped second entry.
Trimmed/styled cases compare direct controls for source-start reset, retained
Colorize/opacity and audio-gain loss after clear/restore.
Short/portrait/wide cases verify native source clocks separately from audio
sample rates, short-source clamping, remembered-duration restoration and fresh
exports with both original import paths absent.

TechSmith's [2022 help guide](https://www.techsmith.com/blog/wp-content/uploads/2023/12/Camtasia-Help-2022-EN.pdf)
describes the Theme Manager and rename surface. The current-build
[rename/delete contract](advanced-features.md#theme-rename-and-delete) instead
uses native file changes, canceled/confirmed operations, preserved UUID/resources
and independent renders to establish immediate persistence and existing-project behavior.

Record feature name, editor build, OS, format version, exact JSON pointers,
before/after hashes, external dependencies, clock domain, and save/reopen,
playback, and export results. Mark untested fields explicitly. Keep private
media and bundled proprietary assets out of published fixtures.

WebM alpha delivery additionally uses [Chrome’s primary alpha documentation](https://developer.chrome.com/blog/alpha-transparency-in-chrome-video).
Codec capability is kept separate from the native Mac output’s measured alpha;
TechSmith’s general background-removal marketing does not specify every export path.

SVG internal dependency fixtures use the primary [Tiny 1.2 image rules](https://www.w3.org/TR/SVGTiny12/struct.html#ImageElement)
and [embedded/external font rules](https://www.w3.org/TR/SVGTiny12/fonts.html).
Original synthetic glyph paths and PNG bytes avoid vendor/font redistribution.
The [native dependency contract](media.md#svg-image-and-font-dependencies) verifies
which controls render, their loss/restoration with external files, and an actual
bundle move. Standards conformance is not inferred from native JSON acceptance.
