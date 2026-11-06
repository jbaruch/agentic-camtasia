# Project helper contract

For Mac 2025.0.3 format 9, validation also warns about rich-text ranges that
end before the text's UTF-8 byte length. This advisory detects the reproduced
missing-suffix case; it does not rewrite text, choose fonts, or prove complete
styling coverage. See [native verification](native-verification.md).

`scripts/project.py` requires Python 3.11+. All output is JSON; errors also
produce stderr diagnostics. Success exits 0, operational/validation failure 1,
and argument errors 2. No command launches Camtasia, edits media, or exports video.

Run helpers and transformation scripts that import them with Python's `-B`
option, or set `PYTHONDONTWRITEBYTECODE=1`. ACR v1 includes every regular file
inside a declared skill directory; local installs do not use Git ignore patterns
to omit bytecode. Keep generated files outside the installed skill tree.

Transformation scripts can use `load(path)` to obtain the parsed document and
original bytes, then `encode_document(document)` to obtain candidate UTF-8
bytes. The encoder preserves the observed native loudness decimal that exceeds
binary64 range; its accepted location/build contract is owned by
`scripts/project.py` — `native_float` and `nonfinite_errors`. Ordinary JSON
constants such as NaN and Infinity remain errors. The native numeric
observation is described in [the format map](project-format.md).
Do not pass that loaded decimal through an ordinary float or replace it with
an infinity. Encoding does not validate media, apply a candidate, or save in
the editor. `apply` still validates and writes the supplied candidate bytes.

| Command | Inputs | Output / side effects |
| --- | --- | --- |
| `inspect PROJECT` | Bundle directory or UTF-8 JSON file | Hash, format/client identity, canvas, clocks, recursive clip/effect inventory, observed asset references, structural report. Read-only. |
| `source-manifest PROJECT [--media-root DIR]` | Bundle or JSON candidate, optional destination directory | Versioned project/source hashes, original references, resolved file paths, availability, bundle-relative containment, unresolved logical assets, and limits. Read-only; missing or unchecked sources exit 1. |
| `validate PROJECT [--media-root DIR] [--contiguous-track S:T]` | JSON candidate, optional destination directory | `ok`, `errors`, `warnings`, `limits`. Read-only. Media resolves from the project document's parent unless overridden. |
| `diff BEFORE AFTER [--limit N]` | Two bundles or JSON files | Change count, JSON pointers, bounded before/after previews, truncation flag. Read-only. Array changes are positional, not a semantic ID diff. |
| `apply TARGET CANDIDATE --expected-sha256 HASH [--preserve-track S:T] [--contiguous-track S:T]` | Existing target, staged full JSON candidate, inspection hash | Validates destination references; checks unchanged identity, selected preserved data, live ownership, and baseline; writes backup and atomic replacement. |

`S:T` means scene-array position and track-array position, both zero-based.
It does not mean clip `trackNumber` or the displayed lane label. Selectors repeat.
`--contiguous-track` checks a declared lane from time zero; intentional gaps or
layered overlaps must not use this option. It does not assert that other lanes
end at the same time.

`--preserve-track` compares the entire selected track, its corresponding
`timeline.trackAttributes` entry, every referenced source-bin entry, and the
project's audio output/normalization settings. Timeline gain and legacy mix
attenuation are protected too. Source comparison includes transcription and
opaque metadata. Use it for unchanged narration during visual
work; caption edits on that same source require a more specific task-level
comparison instead. The helper does not choose narration automatically.

The backup is a content-addressed `project.before-<sha256>.tscproj` beside the
target. An identical candidate is a no-op, even on a rerun with the original
hash. A different candidate with a stale hash is refused. Existing backups are
never overwritten with different data. Permissions on the replaced JSON are
retained. No bundle companion or media file is replaced.

Live ownership checks support macOS: nonempty recovery markers and Camtasia
file handles prevent a write. Inspection failures also prevent a write. An
empty marker alone is inconclusive. No filesystem transaction can lock
Camtasia's in-memory state: keep the project closed throughout the operation.
The editor can retain media handles after document closure. If that blocks a
closed candidate, save and close any other work, quit Camtasia normally, and
repeat the ownership check. Do not bypass it by deleting recovery markers.

For Lottie sources, `allSourcesBundled` covers the JSON itself. The
[native Lottie dependency cases](lottie.md#internal-images-glyphs-and-project-relocation)
retain twelve valid primary sources while linked image content is absent or
font references render fallback text. Inspect and verify internal dependencies.

For SVG sources, `allSourcesBundled` covers the SVG file itself. The
[native dependency probe](media.md#svg-image-and-font-dependencies) passes that
source-only check while linked PNG content is absent. Inspect internal image/font
references and verify the rendered result with original locations unavailable.
Other platforms can stage and validate JSON, then save through their editor.

Validation is deliberately partial. It checks core shape, positive dimensions
and clocks, parseable rational timing, IDs, local source existence, and
track-local transition references. Its native guards include the Mac 2026.2.4
scene-lane collision and reproduced Group reopen-drift checks; see
`scripts/project.py` — `native_hazards`, `native_lane_collisions` and
`native_group_reopen_hazards` for their supported scope.
It preserves unfamiliar fields and warns
on unknown clip types. Nonlocal/foreign-platform paths are reported as
unchecked. It does not certify source-stream bounds, local clock mapping,
keyframes, codecs, fonts, opaque effects, rendering, or interactive output.
No official complete schema is bundled or claimed.

Inspection's `assetReferences` exposes the logical selectors recognized by
`scripts/project.py` — `ASSET_PARAMETERS`. Each entry has its JSON pointer,
effect name, parameter name, unchanged reference value, and resolution status.
Wrapper/child mirrors remain separate. These selectors can name installation
assets rather than files beneath the project. The helper does not resolve them
as source-bin media or certify fonts, models, asset availability, or complete
dependency closure; verify their resolution in the destination editor.

`source-manifest` writes no files and never retrieves remote media. Its stdout
schema is owned by `scripts/project.py` — `source_manifest`. A caller may retain
that JSON as a snapshot, with its `schema_version`, owner, and project/source
hashes. Recompute it before delivery; a prior manifest authorizes no edit.
`--media-root` resolves candidate media against the intended destination, as in
validation. Absolute references can be available without being bundle-relative.
The report separates source-bin file closure from unresolved native dependencies;
it does not certify an archive, symlink transport, fonts, models, bookmarks,
installation assets, or native playback. Compare destination hashes and perform
the native package reopen/render checks described in [media](media.md).

An editable Library `.assetproj` is a different document type from a full
`.tscproj`; do not apply the full-project helper/schema to it. The
[native Library contract](library.md) records its observed root fields, archive
companions, source-copy and insertion behavior. A successful source manifest
does not certify font packaging or identical audio at grouped asset endpoints.
Native Library/folder copies can hard-link asset JSON, thumbnails and media.
Matching hashes and separate directories do not establish independent files;
follow the Library contract before editing installed resources.

For full upstream-schema checks and the tested compatibility profile, use
`scripts/schema_audit.py` per [native verification](native-verification.md).
For backed-up editor save/reopen checks, use `scripts/native_roundtrip.py`.
Its structured result separates native save acceptance from rendered support.
The result identifies the selected editor and includes before/after native health.
Start the matching editor build and close its other documents before invocation;
the [native verification procedure](native-verification.md#serialized-native-work-and-stability)
defines editor selection, optional app-path input, preflight use, and recovery.

## Transition JSON editing

Use `scripts/transitions.py` to inspect root-track transitions, discover local
presets, construct transitions, patch an existing transition or remove it. Its module docstring and
`scripts/transition_presets.py` own the input/output contract, native defaults, duration
conversion and fit checks. Select endpoints by root clip ID, using wrapper IDs
for linked AV. Read [native transition evidence](transitions.md) for boundary
clocks, preroll behavior and rendering limits.

```bash
python3 -B "{camtasia_skill_root}/scripts/transitions.py" inspect "<project>"
python3 -B "{camtasia_skill_root}/scripts/transitions.py" presets "<project>" --app "<matching-Camtasia.app>"
python3 -B "{camtasia_skill_root}/scripts/transitions.py" add "<project>" --app "<matching-Camtasia.app>" --name SnapShot --left-id 5 --right-id 8 --duration 1 --output "<candidate.json>"
python3 -B "{camtasia_skill_root}/scripts/transitions.py" add "<project>" --template-project "<same-build-project>" --template-index 0 --right-id 5 --duration 1 --output "<candidate.json>"
python3 -B "{camtasia_skill_root}/scripts/transitions.py" add-fade "<project>" --left-id 5 --right-id 8 --duration 1 --output "<candidate.json>"
python3 -B "{camtasia_skill_root}/scripts/transitions.py" set "<project>" --left-id 5 --right-id 8 --spec "<transition-spec.json>" --output "<candidate.json>"
python3 -B "{camtasia_skill_root}/scripts/transitions.py" remove "<project>" --left-id 5 --right-id 8 --output "<candidate.json>"
```

Omit one endpoint flag for an edge transition. A schema-version-one spec supplies
`duration` in displayed timeline seconds and/or `attributes` with existing scalar
controls in raw native units. For example,
`{"schema_version":1,"duration":2,"attributes":{"useVisualPreRoll":false}}`.
Inspection returns physical paths and native payloads. Edits return candidate
hashes, `changed`, `written` and `nativeVerified: false`; they stage a separate
file and preserve the original. Follow the ordinary diff/validate/apply and
native save/reopen/export workflow. Unknown combinations still require rendered
verification, including source-handle availability and audio behavior.

`presets` is read-only and returns internal names, English labels, definition
paths and complete scalar defaults; choose `--name` from that output. Installation
resources are read locally and shader code is neither executed nor copied. For
built-in presets without definition files, `inspect` a saved same-build project
and choose its zero-based transition inventory index with `--template-index`.
That route preserves the complete saved transition, including opaque fields and
custom attributes, while replacing endpoints and duration for the destination.
Neither route copies external resources. Keep any template resource dependencies
available and verify the candidate in the matching native editor.

## Caption JSON editing

Use `skills/camtasia-project/scripts/captions.py` for plain closed cues, existing
caption text, recognized source-word corrections, root clock mapping/retiming and
existing dynamic display controls. Its module docstring, `RATE`, `root_clock`,
`point_frames`, `correction_edits`, `capacity`, `mapped_holds` and `set_display`
own the clock, source, value, preservation and refusal contracts. Read
[captions](captions.md) before selecting an owner or parameter clock.

```bash
python3 -B "{camtasia_skill_root}/scripts/captions.py" inspect "<project>"
python3 -B "{camtasia_skill_root}/scripts/captions.py" map "<project>" --clip-id 3
python3 -B "{camtasia_skill_root}/scripts/captions.py" set-cues "<project>" --clip-id 3 --spec "<cues.json>" --output "<candidate.json>"
python3 -B "{camtasia_skill_root}/scripts/captions.py" set-text "<project>" --clip-id 3 --spec "<corrections.json>" --output "<candidate.json>"
python3 -B "{camtasia_skill_root}/scripts/captions.py" correct-words "<project>" --source-id 1 --source-track 1 --spec "<word-corrections.json>" --output "<candidate.json>"
python3 -B "{camtasia_skill_root}/scripts/captions.py" retime "<project>" --clip-id 3 --spec "<clock.json>" --output "<candidate.json>"
python3 -B "{camtasia_skill_root}/scripts/captions.py" set-display "<project>" --clip-id 6 --spec "<display.json>" --output "<candidate.json>"
```

Inspection keeps audio-owned `captions`, imported `Caption.captionData`, source
transcription and modifier-bearing displays separate. Select IDs from that
inventory. A linked wrapper or its audio child selects the same closed parameter.
Native Add Caption/import must first create that parameter; this route does not
substitute an ordinary text overlay for captions. Plain closed editing covers
Mac 2025.0.3/format 9 and 2026.2.4/format 10. Dynamic operations require the latter.
The verified caption clock is 705600000 ticks/sec, independently of stream
sample/edit rates. Other clock contracts require a native capture.

Every edit spec has `schema_version: 1`. Closed cue authoring supplies
`clock: "media"` or `"timeline"` and ordered, nonoverlapping
`cues: [{"start":0,"end":4,"text":"First café"}]`, in rational seconds.
The helper compiles held text, gap clearing and an explicit final clear. An empty
cue array explicitly clears the parameter. Global caption styling survives;
its existing `enabled` flag becomes true. Replacement refuses styled/RTF values
and opaque point/value fields; text correction retains those opaque fields.

Both text-correction commands take
`{"schema_version":1,"edits":[{"index":7,"expected":"useful","text":"HELPFUL"}]}`.
Indices identify existing point occurrences. A stale expected value refuses;
an already-applied replacement is a no-op. Closed corrections retain every
point field and edit `value.text` only. Word corrections edit one existing
recognized token at a time and keep every onset, endTime, duration, pause marker,
confidence field and display unchanged. A source edit affects all uses of that
source. Generate actual recognition/transcription and save it first. No word
point insertion, inferred onsets, recognition or `%GAP` synthesis occurs here.
RTF closed values require native or RTF-aware editing; inspect them as raw data.

Clock edits require all of
`{"schema_version":1,"start":1,"duration":3,"media_start":2,"scalar":"1/2"}`.
Start/duration/trim inputs are seconds; scalar is inverse speed. Complete root
Caption/audio/linked AV clocks change together. Cue/word points stay in the
source/media clock. Stream ranges bound consumption using the stream edit rate;
the word/caption clock remains separate. Mapping returns source point indices,
exact timeline ticks and rational seconds, without frame quantization. Closed
cues carry into trims; dynamic words with pre-trim onsets are omitted.
Nested/stitched/multiscene clocks, nonzero audio `sourceFileOffset`, and retiming
effected/animated owners require separate native contracts. Existing transitions
must still fit; destination lane collisions refuse the edit.

Dynamic displays have independent bounds. A display spec may supply start and/or
duration seconds, `definition` with existing supported numeric controls, and
`rich` with existing fontName/fontSize/fgColor properties. For example:
`{"schema_version":1,"start":1,"duration":3,"definition":{"dynamic-caption-new-paragraph-for-each-sentence":1},"rich":{"fgColor":"(255,255,255,255)"}}`.
Bound edits require a clean untrimmed scalar-one root display. Its native
placeholder stays unchanged; source transcription supplies the words. Targeted
rich font/color entries must cover the placeholder; other native partial runs,
default fonts, style IDs and unknown controls survive. Verify physical fonts,
fitting and actual word highlighting on the rendering host.

Staging returns hashes, inventory, `changed`, `written` and
`nativeVerified: false`. Follow project validate/diff/apply and native
save/reopen/export checks. Inspect the actual cue boundaries, clearing and
highlighted words. MP4 uses burned-in text; Smart Player CC delivery requires
its own web package and toggle/playback checks.

## Annotation JSON editing

Use `skills/camtasia-project/scripts/annotations.py` for construction from a standalone native Callout,
uniform Unicode text/rich properties, and existing static shape/text fields.
Its module docstring, `KINDS`, `NUMBERS`, `ENUMS`, `RICH_TYPES`, `uniform_runs`
and `add_annotation` own the build, selector, value and preservation contracts.
Read [annotation definitions](advanced-features.md#text-callout-presets) and
[rich typography](quick-properties.md#text-and-rich-font-runs) before editing.

```bash
python3 -B "{camtasia_skill_root}/scripts/annotations.py" inspect "<template-project>"
python3 -B "{camtasia_skill_root}/scripts/annotations.py" add "<project>" --track 0:2 --new-clip-id 40 --template-project "<native-template>" --template-clip-id 7 --output "<candidate.json>"
python3 -B "{camtasia_skill_root}/scripts/annotations.py" set "<project>" --clip-id 40 --spec "<annotation-spec.json>" --output "<candidate.json>"
```

Construction uses an existing empty root lane in a single-scene destination.
Match the template's build, canvas and edit rate. Capture the Callout alone on
a root lane without lane parameters, effects, source references, hotspots, markers or
quizzes. The complete clip keeps its existing clock and modifiers; standalone
one-sided Fade companions remap to the requested fresh ID. Destination lane
parameters and visibility remain unchanged. No retiming or external resources
are copied. Add supported effects afterward with their dedicated helpers.

A schema-version-one edit spec supplies `text`, `rich` and/or `definition`:

```json
{"schema_version":1,"text":"Build → Buy","rich":{"fontSize":48,"fgColor":"(60,20,180,255)"},"definition":{"width":400,"horizontal-alignment":"left"}}
```

Name only existing fields and rich properties. Text changes without rich data
retain default fonts. Existing rich data must consist of one static frame of
unique full-string properties; replacement updates every end to the new UTF-8
byte length. Empty text has zero-byte ranges. Mixed, partial, unknown or animated
runs require a separate native contract. Native signed codes, value types,
opaque style IDs and default fonts survive. Shape/style identifiers are not
editable substitutes for full preset definitions. Numeric definition edits
retain static typed descriptors and refuse animated parameters.

Inspection reports declared fonts with `fontFilesVerified: false`. Resolve actual
fonts and glyph coverage on the rendering host. Staging reports hashes,
`changed`, `written` and `nativeVerified: false`. Follow ordinary project
validate/diff/apply, native save/reopen and output checks; inspect text fitting,
contrast, drawing/Fade phases and audio. A stored size can render smaller with
native auto-resize. Neither installed font names nor a valid candidate proves
cross-host dependency closure.

## Behavior JSON editing

Use `skills/camtasia-project/scripts/behaviors.py` to construct a behavior from a
saved native template, edit existing phase timing/static parameters, bypass it,
or remove it. Its module docstring, `NAMES`, `PHASE_NAMES`, `PHASE_ATTRIBUTES`,
`TICK_ATTRIBUTES`, `targets`, `reset_companions` and `attribute_value` own the
build, names, mixed-clock, selector and reset contracts. Read the
[native behavior evidence](behaviors.md) before selecting a template.

```bash
python3 -B "{camtasia_skill_root}/scripts/behaviors.py" inspect "<template-project>"
python3 -B "{camtasia_skill_root}/scripts/behaviors.py" add "<project>" --clip-id 10 --behavior fade --template-project "<same-build-template>" --template-clip-id 40 --template-effect-token 7 --output "<candidate.json>"
python3 -B "{camtasia_skill_root}/scripts/behaviors.py" set "<project>" --clip-id 10 --behavior fade --effect-token 7 --spec "<behavior-spec.json>" --output "<candidate.json>"
python3 -B "{camtasia_skill_root}/scripts/behaviors.py" remove "<project>" --clip-id 10 --behavior fade --effect-token 7 --output "<candidate.json>"
```

The schema-version-one spec supplies `phases` and/or boolean `bypassed`.
Phase entries supply existing `attributes` and/or static scalar `parameters`.
For example:
`{"schema_version":1,"phases":{"in":{"attributes":{"suggestedDurationPerCharacter":3}}},"bypassed":false}`.
Timing inputs use rational seconds; the helper retains each field's native
clock. Parameter inputs use raw native units. It does not interpret UI speed
percentages, replace phase styles or infer total per-character phase duration.

Inspection returns physical owners, payloads and optional stable `effectToken`
values; repeated names require a token. Construction preserves complete saved
phases and requires matching native owner kinds, linked layout and full clocks.
New linked copies receive fresh tokens. No external resource bytes are copied.

Edits return a separate candidate, hashes, inventory, `changed`, `written` and
`nativeVerified: false`. Follow ordinary diff/validate/apply and native
save/reopen/export checks. Verify requested entry, center and exit behavior;
text glyph ordering and new parameter combinations retain their own checks.

## Visual-effect JSON editing

Use `scripts/effects.py` for construction from a saved native template, existing
static scalar edits, bypass and removal. Its module docstring, `CLIENT_FORMATS`,
`CONSTRUCTOR_TYPES`, `add_effect`, `owner_defaults` and `patch_parameter` own the
build, owner, parameter, reset and preservation contracts. Read the relevant
[native effect contract](advanced-features.md) before selecting a template.

```bash
python3 -B "{camtasia_skill_root}/scripts/effects.py" inspect "<template-project>"
python3 -B "{camtasia_skill_root}/scripts/effects.py" add "<project>" --clip-id 10 --effect Sepia --template-project "<same-build-template>" --template-clip-id 40 --template-effect-token 7 --output "<candidate.json>"
python3 -B "{camtasia_skill_root}/scripts/effects.py" set "<project>" --clip-id 10 --effect Sepia --effect-token 1 --spec "<effect-spec.json>" --output "<candidate.json>"
python3 -B "{camtasia_skill_root}/scripts/effects.py" remove "<project>" --clip-id 10 --effect Sepia --effect-token 1 --output "<candidate.json>"
```

Inspection returns physical owners, array positions and stable `effectToken`
values. Select a template by its native clip ID and effect name; use its token
for repeated names. Construction appends a fresh instance. Linked instances
receive a fresh stable token; direct instances preserve their native metadata
and may have no token. Preserve resource availability at the destination; the helper copies
references, not their files. Retimed effects need their feature-specific clock
contract. Construction preserves complete curves without changing their times.
Use `scripts/motion_paths.py` for Motion Path construction and its coupled clip
rotation; the generic constructor refuses `MediaPath`.

`set` accepts a schema-version-one spec, for example
`{"schema_version":1,"parameters":{"intensity":"1/2"},"bypassed":false}`.
Existing structured or animated controls are not flattened by scalar patches.
Edits stage a separate candidate and report hashes, `changed`, `written` and
`nativeVerified: false`. Follow diff/validate/apply and native verification for
the edited project. Existing preset rendering evidence does not establish a
new owner's geometry, resource closure or a new parameter combination.

## Visual-effect curve editing

Use `skills/camtasia-project/scripts/effect_curves.py` to inspect effects, replace
an existing typed double parameter's linear interval curve, or clear it to a
constant. Its module docstring, `OWNERS`, `selected`, `parameter_of` and
`edit_curve` own the build, descriptor, clock and interval contracts. Read the
[native effect-curve evidence](advanced-features.md#visual-effect-parameter-curves).

```bash
python3 -B "{camtasia_skill_root}/scripts/effect_curves.py" inspect "<project>"
python3 -B "{camtasia_skill_root}/scripts/effect_curves.py" set "<project>" --clip-id 10 --effect Sepia --effect-token 7 --parameter intensity --spec "<curve-spec.json>" --output "<candidate.json>"
python3 -B "{camtasia_skill_root}/scripts/effect_curves.py" clear "<project>" --clip-id 10 --effect Sepia --effect-token 7 --parameter intensity --value "1/2" --output "<candidate.json>"
```

The schema-version-one spec supplies `defaultValue` and `segments`. Each segment
has `start`, `end` and target `value` in raw native units. Example:
`{"schema_version":1,"defaultValue":0,"segments":[{"start":1,"end":2,"value":1},{"start":3,"end":4,"value":"1/4"}]}`.
Times are rational clip-relative timeline seconds. The request replaces the
selected parameter's complete curve, including its initial value; other curves
and visual intervals survive. Clearing preserves intervals and descriptor data.
Native reopening may collapse the constant descriptor to a scalar; curve
commands require a typed native descriptor rather than inferring its kind.

Edits stage a separate candidate and report hashes, inventory, `changed`,
`written` and `nativeVerified: false`. Follow ordinary diff/validate/apply and
native save/reopen/export checks. Resource closure and a new parameter's units,
companions and rendered behavior remain separate verification obligations.
Use the dedicated Motion Path helper for its coupled position/rotation data.

## Color LUT JSON editing

Use `skills/camtasia-project/scripts/luts.py` for the existing `LutEffect` resource selector, intensity,
native ranges, bypass and edge easing. Its module docstring, `RANGE_CHOICES`,
`lookup_roots`, `resolve_resource`, `patch_double` and `patch_edge` own the
lookup, parameter and preservation contracts. Read [the LUT native evidence](advanced-features.md#color-lut-filters).

```bash
python3 -B "{camtasia_skill_root}/scripts/luts.py" resources --app "<matching-Camtasia.app>"
python3 -B "{camtasia_skill_root}/scripts/luts.py" inspect "<project>"
python3 -B "{camtasia_skill_root}/scripts/luts.py" set "<project>" --clip-id 10 --effect-token 7 --spec "<lut-spec.json>" --app "<matching-Camtasia.app>" --output "<candidate.json>"
```

The schema-version-one spec accepts `source`, `intensity`, `range`, `easeIn`,
`easeOut` and `bypassed`; provide at least one. Example:
`{"schema_version":1,"source":"Basic Black & White.cube","intensity":"1/2","range":"grey-shadows","easeIn":1,"easeOut":"3/2"}`.
Use an exact filename from `resources`; `--app` is required when changing it.
Discovery reads the selected installation and the observed native user Color
LUTs directory. Import new CUBE files in Camtasia first. No file is copied,
installed or modified. Same-name/case aliases with different hashes refuse.

Edits return a separate candidate, hashes, inventory, `changed`, `written` and
`nativeVerified: false`. A resource change also returns its filename, locations,
hash, finite-table audit and `closure: "selected-file-only"`; `resource: null`
means no resource audit was requested. The CUBE title does not replace the native
filename or original preset metadata. Audits do not establish native lookup,
resource portability or rendered processing. Follow the ordinary validation,
apply and native save/reopen/export workflow.

Existing curves survive resource/bypass/easing edits. Scalar intensity or range
patches refuse animated controls. Ease disabling retains existing native
zero-duration records; unrelated edge parameters and reset values stay intact.
Use the feature workflow for new keyframe shapes or effect-specific retiming.

## Animation JSON editing

Use `scripts/animations.py` to inspect curves or stage a coupled visual interval.
Its module docstring, `OWNERS`, `PROPERTIES`, `EASINGS`, `source_bounds`,
`edit_interval`, `remove_interval`, `interval_properties` and `REMOVAL_DEFAULTS` own the build,
geometry fields, easing/removal owners, timing and preservation contract.
The [native animation reference](animations.md) records
the tested constructors, visual owners and source-position clocks.

| Command | Required inputs | Output and side effects |
| --- | --- | --- |
| `inspect PROJECT` | Bundle or project JSON | Read-only physical owners, visual intervals and parameter curves, including unfamiliar owners. |
| `set-interval PROJECT --clip-id ID --spec SPEC --output CANDIDATE` | Verified visual-owner ID and schema-1 interval input | Separate candidate; adds or updates the interval and requested geometry targets. Missing parameters require explicit initial values. Linked IDs resolve to video; audio, wrapper, Group children and sources survive. |
| `ease-interval PROJECT --clip-id ID --start SECONDS --end SECONDS --easing CHOICE --output CANDIDATE` | Existing interval and easing choice | Separate candidate; updates the interval and matching geometry frames together. Other intervals and parameter-level interpolation survive. Unknown/effect-owned coupled curves require native investigation. |
| `remove-interval PROJECT --clip-id ID --start SECONDS --end SECONDS --output CANDIDATE` | Exact clip-relative bounds of the selected interval | Separate candidate; removes the interval and its coupled geometry frames, retaining initial geometry, other intervals, audio and sources. An already absent interval is a no-op without orphaned coupled frames. |

Example interval input:

```json
{
  "schema_version": 1,
  "start": 3,
  "end": 4,
  "values": {"scale0": 1.25, "scale1": 1.25},
  "initial": {"scale0": 1, "scale1": 1},
  "easing": "exponential"
}
```

Times use clip-relative timeline seconds. Existing initial values are preserved;
an input cannot implicitly replace them. Optional `parameterEasing` addresses
parameter-level interpolation separately from interval/frame easing. Subject
analysis and preset framing are not performed. The
[native axis contract](animations.md#additional-rotation-and-depth) records the
verified rotation/depth units and output. Other owner types, unobserved controls
and point-curve mutation remain outside this helper's verified scope. The
[ordinary point limits](animations.md#ordinary-geometry-point-limits) distinguish
native static-value folding from timed movement. Removal retains
parameter-level metadata and refuses unfamiliar or effect-owned coupling.

Stdout uses schema 1, owner `camtasia-animations`, hashes and the physical
animation inventory. Staging reports `changed`, `written` and
`nativeVerified: false`. Errors are JSON on stderr; exit codes are 0 success,
1 input/I/O refusal and 2 CLI syntax. Use the ordinary diff, validation and guarded
apply workflow. The helper never opens Camtasia or writes the original project.

An empty `values` object in `set-interval` creates a native Custom marker without
target geometry. Optional easing is explicit; omission retains an existing
marker's setting or uses the new marker's native default representation.
`ease-interval` still requires an existing marker. Native reopening can rebuild
constant image-scale curves; see the [empty-marker evidence](animations.md#empty-custom-intervals).
Frozen recording and stitched owners use the same commands. Their distinct
clocks, native constant cursor-size companions and two-save reconstruction are
documented in [frozen and stitched owners](animations.md#frozen-and-stitched-owners).

## Motion Path JSON editing

Use `scripts/motion_paths.py` for explicit point geometry. Its module docstring,
`TIMINGS`, `OWNERS`, `visual_targets`, `set_path`, `point_frames`, `set_bypass`
and `remove_path` own the native build, owner, constructor, interpolation,
clock, companion and preservation contracts. The
[Motion Path evidence](animations.md#motion-path-json-editing) records native
constructor, curve editing, retimed and orientation checks.

| Command | Inputs | Output and side effects |
| --- | --- | --- |
| `inspect PROJECT` | Bundle or project JSON | Read-only physical path owners and saved effects. |
| `set-path PROJECT --clip-id ID --spec SPEC --output CANDIDATE` | Verified visual-owner ID and schema-1 points | Separate candidate; creates or replaces explicit points, optional handles/interpolation and Auto Orient. Linked mirrors change together; audio, sources, Group children, recorded cursor data, other effects and same-time opaque frame data survive. |
| `set-bypass PROJECT --clip-id ID --bypass\|--no-bypass --output CANDIDATE` | Existing path owner and requested switch | Separate candidate; changes the selected path's bypass and its verified orientation companion, including linked mirrors where present. Missing paths refuse. |
| `remove-path PROJECT --clip-id ID --output CANDIDATE` | Verified visual-owner ID | Separate candidate; removes the selected path and its known Auto Orient companion. Retains reset metadata, unrelated effects/tokens, geometry, audio and descendants. An absent path is a no-op. |

The spec requires `schema_version: 1` and a nonempty `points` array. Each entry
has rational clip-relative timeline `time`, three-coordinate `position`, and
optional `interpolation` in the module's supported native representation.
Optional `autoOrient` is boolean. Omitted orientation preserves the existing
control. Point-array replacement supports explicit insertion, deletion,
extension and handle changes; it does not calculate a spline split or infer
geometry from a menu/preset name. Supply every retained point and its intended
interpolation. Same-time opaque frame data and parameter metadata remain.
The [frozen/stitched path contract](animations.md#frozen-and-stitched-motion-paths)
records held-frame clock separation and orientation edits while bypassed.

Stdout uses schema 1, owner `camtasia-motion-paths`, hashes and path inventory.
Staging adds `changed`, `written` and `nativeVerified: false`. JSON diagnostics
use stderr; exit codes are 0 success, 1 input/I/O refusal and 2 CLI syntax.
Use the ordinary staged diff, validation and guarded apply workflow. Original
documents/media and the editor are not changed by these commands.

## Matte JSON editing

Use `scripts/mattes.py` to inspect and stage media or track mattes. Its module
docstring, `MODES`, `DEFAULT_EFFECT`, `patch_ease`, `edit_media`, `curve_parameter`,
`edit_intensity_curve`, `clear_intensity_curve` and `track_target`
own the build, constructors, control units, edge preservation and ownership
contract. The [native matte evidence](advanced-features.md#media-and-track-mattes)
records the difference between intensity, bypass and track-level masking.

| Command | Required inputs | Output and side effects |
| --- | --- | --- |
| `inspect PROJECT` | Bundle or JSON document | Read-only physical effect paths, clip IDs and track-matte paths/codes. |
| `set-media PROJECT --clip-id ID --output CANDIDATE` | Verified visual-owner ID and at least one control: `--mode`, `--intensity`, `--ease-in`, `--ease-out`, `--bypass` or `--no-bypass` | Separate full candidate; creates or updates a native Media Matte. `--mode none` removes that effect. Linked wrapper/video mirrors change together; audio, unrelated effects, visual content and opaque state survive. |
| `set-track PROJECT --track INDEX --mode MODE --output CANDIDATE [--group-id ID]` | Storage track index and mode, optional existing Group ID | Separate candidate; edits the selected root or Group track attribute without changing its media. |
| `set-intensity-curve PROJECT --clip-id ID --curve SPEC --output CANDIDATE` | Verified visual-owner ID and schema-1 curve input | Separate candidate; creates/replaces the intensity curve with source-clock conversion. Linked visual mirrors change together; audio and other animations survive. |
| `clear-intensity-curve PROJECT --clip-id ID --intensity VALUE --output CANDIDATE` | Existing matte owner and requested static intensity | Separate candidate; clears only intensity keyframes. Other parameter curves and visual animation intervals remain. |

Curve input example:

```json
{
  "schema_version": 1,
  "defaultValue": 0,
  "segments": [
    {"start": "1/2", "end": "3/2", "value": 1},
    {"start": 2, "end": "11/4", "value": 0}
  ]
}
```

The input uses clip-relative timeline seconds. The helper owns source-position
conversion and accepted segment constraints. `set-media --intensity` refuses an
animated parameter; use the explicit clear command to replace it with a constant.
Native reopening can regenerate constant intensity companions for retained visual
intervals. That preserves static output and the other animations; see the linked
native evidence for the exact resave distinction.

Stdout uses schema 1, owner `camtasia-mattes`, source/candidate hashes and
inventory. Staging reports `changed`, `written` and `nativeVerified: false`.
Errors are JSON on stderr; exit codes are 0 success, 1 input/I/O refusal and
2 argument syntax. Outputs are exclusive or identical no-ops. Run the ordinary
project diff, validation and guarded apply workflow, then verify native output.

## Hotspot JSON editing

Use `scripts/hotspots.py` to inspect existing hotspots/marker identities and stage
full JSON candidates. The observed build, constructors, action mapping, supported
clip targets and timing constraints are owned by that script's module docstring,
`DEFAULT_HOTSPOT`, `ACTIONS`, `visual_target` and `edit_hotspot`. The
[native hotspot evidence](advanced-features.md#interactive-hotspots) distinguishes
serialized acceptance from Smart Player behavior.

| Command | Required inputs | Output and side effects |
| --- | --- | --- |
| `inspect PROJECT` | Bundle or project JSON | Read-only JSON with `projectSha256`, `hotspots` and `markers`. Marker entries retain logical owner ID, physical parameter owner ID, point time in ticks, label and JSON pointer. |
| `set PROJECT --clip-id ID --action ACTION --output CANDIDATE` | Unique clip ID and action-specific options | Separate full JSON candidate; report includes hashes, visual target pointer, resulting hotspot, `changed`, `written` and `nativeVerified: false`. Preserves unrelated content and inactive settings. |
| `remove PROJECT --clip-id ID --output CANDIDATE` | Unique clip ID | Separate full candidate with only the selected visual hotspot removed; removal is idempotent. |

Time targets take `--time SECONDS`; URL targets take `--url URL` and optionally
`--new-window` / `--no-new-window`. `--pause` / `--no-pause` controls end pausing.
Marker targets take `--marker-owner ID --marker-time SECONDS`. Use the logical
`ownerId` from inspection, not the label, list position or `parameterOwnerId`.
The script's `marker_global_ticks` resolves observed single-scene media and Group
clocks automatically. Other structures require `--marker-global-time SECONDS`
from native evidence. An explicit value must agree with an available verified
mapping. The [Group reopen finding](project-format.md#clock-domains) records a
native duration instability and the exercised content-preserving construction.

Stdout is JSON with `schema_version: 1` and owner `camtasia-hotspots`; errors are
JSON on stderr. Exit codes are 0 for success, 1 for input/I/O refusal and 2 for
argument syntax. The helper owns this report shape; readers must recheck the
input hash before applying a retained candidate. It never changes the source,
reads media, opens the editor or exports. An existing identical candidate is a
no-op; a different candidate or symlink at that path is refused.

Run the ordinary `project.py diff`, validation and guarded `apply` workflow on
the staged candidate. Staging does not establish native acceptance, valid nested
clock mapping, portable dependencies or working exported interactions.

## Quiz JSON editing

Use `scripts/quizzes.py` for quiz inspection, authoring, retiming, owner transfer
and removal. Its module docstring, `validate_spec`, `QUESTION_TAGS`, `build_xml`,
`resolve_owner`, `move`, `point_from_global`, `validate_feedback` and `apply_feedback`
own the supported build, authoring fields, answer-key limits and preservation
contract. Quiz data remains native XML inside the staged project JSON.

| Command | Required inputs | Output and side effects |
| --- | --- | --- |
| `inspect PROJECT` | Bundle or project JSON | Read-only hash and quiz inventory, including owner path/ID, point ticks, names and question identities. |
| `upsert PROJECT --spec SPEC.json --time SECONDS --output CANDIDATE [--owner-id ID]` | Complete versioned quiz spec, exact owner-clock seconds, optional destination owner | Separate full candidate; adds the quiz or replaces its known question/answer lists and retimes it. Existing quizzes keep their owner by default; new quizzes default to the timeline. |
| `move PROJECT --quiz-id ID --owner-id ID --output CANDIDATE [--time SECONDS \| --global-time SECONDS]` | Existing quiz and destination owner | Preserves global position and the exact XML string by default; optional time chooses a different owner/global point. Requires no reconstructed question spec. |
| `remove PROJECT --quiz-id ID --output CANDIDATE` | Quiz identity from inspection | Separate candidate with the selected quiz removed; absent identity is a no-op. |

Authoring specs accept `schema_version: 1`, `2` or `3`, owner `camtasia-quiz-spec`, a positive
integer quiz `id`, `name` and `questions`. See the script's validation contract
for each question's fields. This is the helper's input format, not a replacement
Camtasia project schema. Known list entries omitted from the spec are removed;
reused identities retain unfamiliar native XML attributes/children. Choose new
question identities when changing kinds. Omitted root options preserve existing
values. Schema 2 adds per-question feedback patches; schema 1 remains readable
without that field. Omitted response fields and inactive destinations survive.
The module docstring owns the feedback input contract. Root feedback controls
viewer results; per-question feedback controls response text/actions. Marker
actions require a unique existing native `markerIdentifier` and resolve its
global clock without creating or moving the marker. Native quiz-count metadata
follows additions, transfers and removals.

Schema 3 adds optional survey grading inputs under explicit `graded: false`.
The module docstring owns missing-field defaults, inactive-key preservation,
explicit clearing and the Mac exporter's required stored choice key. Older
specs retain their validation contract. Enabling grading requires explicit keys.

Inspection's `ownerId` remains the physical parameter-owner ID. It is accepted
by `--owner-id`; a UnifiedMedia wrapper ID also selects its video child. Use
the timeline ID for unpinning. The plain `--time` value always uses the chosen
owner's parameter clock. `move` computes the inverse clock mapping for global
time and verifies it through the shared forward mapper. The script's
`VISUAL_TYPES` and mapping functions own supported constructors and exact-clock
limits. Unknown containers, multiple scene clocks, out-of-view points and
fractional owner ticks require a new native case; no clock fields are flattened.

Stdout uses schema 1, owner `camtasia-quizzes`, hashes and the resulting quiz
inventory. Staging adds `changed`, `written` and `nativeVerified: false`; errors
are JSON on stderr. Exit codes are 0 success, 1 input/I/O refusal and 2 argument
syntax. Output is exclusive or an identical rerun. Source files/media are never
modified by this helper. Review the candidate with the ordinary diff/validation
and guarded apply workflow, then verify the native interactive output using
[the quiz evidence](advanced-features.md#quizzes-and-scorm).
