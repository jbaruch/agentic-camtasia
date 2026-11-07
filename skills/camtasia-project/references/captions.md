# Captions and transcripts

These structures were observed in the local Mac workflow and are corroborated
by the speaker-toolkit reference linked in [sources](sources.md). They are not
a universal caption schema for all Camtasia releases.

## Source recognition versus display

The dynamic-caption workflow stores words in
`sourceBin[].sourceTracks[].parameters.transcription.keyframes` on an audio
stream. Storage ownership does not determine the parameter's clock. The native
2026.2.4 WAV probe has a source-track `editRate` of 48000 and range 0–384000,
but its transcription point times use the **705600000-tick clock**: the first
word at 14112000 is 0.02 seconds, and the last observed word starts at
4710144600, or 6.675375 seconds. Dividing these values by the audio sample
rate would put the words far outside the eight-second source. Measure word
onsets and native display before choosing a clock for another representation.
Some recorded workflows use `%GAP` pause markers; preserve them when present,
without requiring the current native recognizer to emit them.
The display is a separate `Callout` with `def.modifier == "dynamicCaption"`.
Correcting display text alone may leave the source transcript unchanged.

Keep each recording's transcript separate. Map word times through source
selection, clip trims, speed, containers, and scene placement before using
them as timeline cut points or chapters. Never divide every timestamp by the
project edit rate or source sample rate solely because of the containing object.

## Corrections

- Keep reliable native word onsets when correcting names and punctuation.
- Treat recognition, word timing, and editorial wording as separate tasks.
- Preserve pause markers deliberately; check gaps at sentence boundaries.
- When collapsing a false start, align the retained words with the actual
  delivery rather than the discarded lead-in.
- Make manual onset overrides occurrence-specific for repeated words.
- Review interpolated words against speech; interpolation is not measured timing.
- Keep corrected captions faithful to the meaning actually spoken.

The local workflow creates sentence blocks from punctuation using
`dynamic-caption-new-paragraph-for-each-sentence`. Caption styling can involve
both `def.font.size` and rich-text `fontSize` attributes. Preserve rich-text
range semantics. On the exercised Mac 2025.0.3 format-9 text callout,
`def.textAttributes.keyframes[].value[].rangeStart` and `rangeEnd` use UTF-8
byte offsets. The string `Unicode: café — 日本語` has 19 Python characters and
28 UTF-8 bytes. A whole-string `rangeEnd` of 19 omitted the Japanese suffix;
28 rendered the complete string. A CJK-capable font alone did not repair the
incorrect ranges. The helper warns when a rich-text frame's maximum range end
falls short of the UTF-8 byte length for this exact editor identity. It does
not repair styling ranges or prove font coverage. Other versions and text
representations require their own indexing probe.

## Native generation, source edits, and styling

The current native probe imported an eight-second synthetic-speech WAV, added
it to the timeline, and used a native dynamic-caption style. Camtasia generated
20 source word points with `type: "string"` and retained
`sourceTrack.transcriptionSet: true`. TechSmith documents
[on-device transcription and source binding](https://support.techsmith.com/hc/en-us/articles/26713588518413-Dynamic-Captions-Best-Practices).
The inspected installation includes its speech model under
`Resources/models/speechToText`. Trimming a timeline clip does not shorten the
underlying source that the recognizer processes; do not infer recognition cost
or scope from the visible clip duration alone.

The generated display is a `Callout` with `def.modifier: "dynamicCaption"`.
Its native `def.text` remains the preset's `ABC` placeholder while actual words
come from the source transcription. Replacing that placeholder with a transcript
does not reproduce the measured native workflow. The palette/menu add action
created a 60-second display despite the eight-second audio. **Modify → Duration**
bounded it to eight seconds before export. Check both source and display bounds.

Selecting the audio in the Dynamic Captions tool exposes individual editable
word fields. Changing one occurrence of `synthetic` to `SYNTHETIC` changed only
that source point's value; all 20 `time`, `endTime`, and `duration` values stayed
unchanged. Deleting the display and adding a different native style preserved
the edited source transcription. A separate project copy retained its original
lowercase word, confirming that the intended project's source data was edited.
Preserve measured subframe onsets; do not quantize these points to video frames.

The Arial two-line style rendered complete text blocks. The Bebas three-line
word-red style rendered the current word in red at the source word boundaries.
Its native **Split captions by sentence** checkbox saves
`dynamic-caption-new-paragraph-for-each-sentence: 1.0`. Word styling also uses
`dynamic-caption-current-word-enabled` and its color/stroke/scale companions;
preserve the native font, layout, easing, and past/future-word controls instead
of reconstructing a style from one flag. Both specimens independently reopened.
The edited transcript and sentence setting survived, and a fresh word-red export
after reopening has identical decoded video and audio to the first export.

## Longer vertical edits and export checks

A Mac 2026.2.4 format-10 vertical edit verifies 195 corrected words over
80.866667 seconds, sentence blocks, a three-line Bebas display, and a lavender
current-word highlight. Recognition mistakes and speaker-authorized grammar
repairs were applied to the source points; the original recording remained
byte-identical. Matched native onsets were retained. Merged wording used the
first retained onset, and additional words used measured local recognition
onsets. Preserve `%GAP` markers and extend the display's bounds to the actual
timeline duration; the native constructor initially lasted only 60 seconds.

The preset's `def.font` was white while its rich-text `fgColor` value was
`"(0,0,0,255)"`. The noncurrent words rendered black against a dark panel.
Setting the applicable rich-text color to `"(255,255,255,255)"` produced white
noncurrent words while preserving the separate lavender highlight. Inspect
both representations when changing caption color; font color alone did not
override the native rich-text value. Preserve the preset's `ABC` placeholder
and attribute ranges rather than replacing it with the spoken transcript.

The first export after layout/preview edits contained frozen word highlights
inside some longer blocks, despite correct source times and a correct editor
preview. Restarting the saved project in a fresh editor process produced two
exports with identical complete decoded video/audio and correctly advancing
highlights in inspected passages. The internal cause is not established.
Inspect exported frames across longer blocks, not only the first highlighted
word or editor playback. If this symptom appears, save the owned project,
restart normally, and repeat the export/output checks. Keep the failed movie
separate from accepted delivery evidence.

## Other caption forms

The Mac 2025.0.3 native Add Caption command produced
`UnifiedMedia.audio.parameters.captions` on the `AMFile` child, with
`type: "caption"`. Its point keyframes have equal `time` and `endTime`, zero
`duration`, and `value: {"text": "...", "textAttributes": null}`. A text value
holds until the next point; an empty value clears it. The native probe changed
from caption one at zero to caption two at four seconds and cleared at eight.
Native save and export retained this structure, and inspected frames at two
and six seconds show the corresponding captions.

The dedicated **File → Import → Captions** SRT importer produced a different
native form on the same build: a standalone media node with `_type: "Caption"`
and `parameters.captionData`, using the same point-value structure. Two SRT
cues at zero/four seconds produced two points; the clip's eight-second duration
bounded the final cue without an extra empty point. The clip also carried
`allowTrimOut: false`, `maxMediaDuration`, ordinary clip timing, `scalar`,
`effects`, `metadata`, and `animationTracks`; it had no source-bin reference.
The imported clip saved, reopened, and rendered both expected texts. The
exact-build schema profile adds this observed unstyled form with strict fields;
styled per-cue values and other variants require their own samples. Global
caption styling uses the separately observed `timeline.captionAttributes`. Use the
dedicated caption importer rather than treating an SRT as generic media.

In this zero-trim, speed-1 probe, four seconds serialized as 2822400000 ticks
with project `editRate` 705600000, while the source-track clock was 48000.
Identify parameter clocks independently of the source sample range. A follow-up native test trimmed
two source seconds, used `scalar: "1/2"` for 2× speed, and placed each clip at
one timeline second. Both audio-child captions and standalone `Caption` clips
retained point times 0/4 seconds in their media clock. Native exports changed
caption at timeline second 2, following
`timelineStart + (captionTime - mediaStart) * scalar`. Frames at 1.9667 and
2.0333 seconds confirmed the boundary. Native SRT export produced cues
1.000–2.000 and 2.000–4.000, matching trim, speed, and offset. This probe
establishes root clocks. The Group contract below adds closed-cue mapping;
The ordinary-AV stitched-parent contract below adds its separate virtual clock;
recording and other stitched forms retain their own investigation.

`timeline.captionAttributes` enabled captions and supplied font, colors,
language, alignment, and background settings. These observed companions do
not establish that every field is required in all versions. The native export
used burned-in caption style. A follow-up web export selected **Closed
captions** after enabling **Export as Web Page**; the closed-caption choice
was disabled for plain MP4 export. Local Smart Player playback exposed the CC
toggle, displayed the retimed first cue, hid that text when CC was disabled,
and presented the second cue. Keep the full web package and inspect both
caption visibility and player timing for the requested delivery. An SRT export contains timed text and does not carry every
native word-highlighting or styling feature. Inspect the actual project and
requested player/output instead of converting between these forms blindly.
[Upstream caption configuration](https://github.com/grandmasteri/pycamtasia/blob/443a41e37cddb460c0aa6e046c951cb17f241bf3/src/camtasia/timeline/captions.py).

The tested community `timeline.add_caption` convenience method produced ordinary
text `Callout` overlays without a caption modifier. Its method name does not
establish native closed-caption or dynamic-caption serialization.

## Current interchange support

TechSmith's [Mac 2026 version history](https://support.techsmith.com/hc/en-us/articles/41263167862285-Camtasia-Mac-2026-Version-History)
introduces basic VTT import/export in 2026.1. This is vendor-documented support;
the native SRT probes above target 2025.0.3. A separate 2026.2.4 probe now
exercises VTT import, native save/reopen, export, reimport, and burned-in output.
It also creates standalone `Caption`/`captionData` point values. The format-10
profile admits this observed branch independently of the format-9 corrections.
Accents and quotation marks survive; native VTT escapes `&` as `&amp;`, and
native reimport restores identical cue texts and times. Do not double-escape
project text or assume every VTT style survives interchange.

The zero-trim probe changes cues at four seconds in the native movie. A
current-build follow-up retains the two-second trim, `scalar: "1/2"`, and
one-second timeline offset; both the native VTT export and inspected frames
confirm cues at 1–2 and 2–4 seconds. Exporting captions resets the format menu
to SRT in this installation. Select VTT explicitly and inspect file contents;
typing `.vtt` alone produced a `.vtt.srt` containing SRT.

When caption
import fails or text displays incorrectly, TechSmith's
[caption troubleshooting procedure](https://support.techsmith.com/hc/en-us/articles/43374924720397-Captions-Troubleshooting-for-Camtasia-Editor)
recommends saving a separate SRT/VTT copy as UTF-8 with BOM and importing that
copy. Keep the original, use the dedicated caption importer, and check cue text
and timings after import and export.

## SAMI and native RTF strings

The current editor also exports and imports SAMI. Its native `.smi` export uses
millisecond `SYNC Start` values and HTML entities. Reimport stores caption text
as **RTF strings** inside `value.text`, while `textAttributes` remains null.
Native rendering interprets those strings correctly, including the accented
text and quotes. A string-valued caption field is therefore not necessarily
plain text. Preserve the RTF payload and use an RTF-aware editing route or the
native caption editor; do not apply plain-text replacements or byte-range
assumptions from the separate `Callout` representation.

The native SAMI export of the retimed probe omitted a final clearing entry.
Reimport extended the final cue from its intended end at second 4 to second 6.
This is a demonstrated interchange loss even though the imported text renders
correctly. Preserve exact end times in the source project or another measured
interchange format. For required SAMI delivery, an explicit empty paragraph
at the known end time can clear it; Microsoft's
[SAMI synchronization contract](https://learn.microsoft.com/en-us/previous-versions/windows/desktop/dnacc/understanding-sami-1.0)
uses a non-breaking-space entity to blank a paragraph. A separate copy with
`SYNC Start=4000` and `<P Class=enCC>&nbsp;</P>` imported and rendered with
the correct four-second clearing boundary. Its fresh native export after
independent project reopen has identical decoded video and audio to the first
corrected export. Take the end time and language class from the actual source;
do not hardcode this probe's values into another SAMI file.

Before editing recognition data, establish that Camtasia has generated it and
saved the project. Missing transcription requires an editor transcription or
an explicitly chosen external workflow; inventing keyframes from text is not
equivalent to measuring the recording. Validate the staged project and inspect
caption blocks and highlighting in Camtasia playback.

## Reusable caption helper verification

The [caption helper](helper.md#caption-json-editing) was verified on Mac 2026.2.4
(2026.132), format 10, using a generated 640×360, 30-fps, eight-second AV source
with actual synthetic speech. Native **Add Dynamic Caption Style → Bebas 3 Line
Word Red** generated nineteen recognized word points and one `%GAP` point.
Both source streams use edit rate 384000, audio sample rate is 48000, and word
times still use the 705600000 project-tick clock. Native **Add Captions** on the
linked clip creates `audio.parameters.captions` with empty points at zero and
four seconds and enables the existing global caption attributes. This confirms
that audio-owned form independently on the current build.

Three separate helper candidates share a two-second source trim, inverse speed
`1/2`, and one-second timeline placement. The consumed six source seconds become
a three-second visible clip at timeline seconds 1–4. Complete wrapper/video/audio
clocks agree; all source word points remain unchanged except the requested
occurrence correction below. Each candidate saves, closes, independently reopens
and exports two matching four-second MP4s. All three pairs reproduce complete
decoded video/audio, and decoded audio matches across caption forms.

The audio-owned case authors `First café & timing` at source seconds 0–4 and
`Second caption → end` at 4–8, with a final clearing point. Native output is
blank before timeline second 1, shows the first held cue at 1, and switches at
2. Eight inspected frames include both sides of that boundary. Native save
changes only the project thumbnail, command count and duration label.

The standalone `Caption.captionData` case uses the same first cue, ends its
second cue at source second 7, and explicitly clears there. Eight inspected
frames confirm cue starts at timeline seconds 1 and 2 and clearing at second 3.5
while video continues to 4. Its native initialization removes the probe's empty
`attributes` object, adds the four observed clip metadata defaults
(`audiateLinkedSession`, `clipSpeedAttribute`, `colorAttribute`, `effectApplied`),
and allocates ID 10→6. Cue points, complete clocks, maxMediaDuration, source data
and audio survive. These initialization differences are separate from the
helper's field-preserving transformation and the three bookkeeping fields.

The dynamic case corrects source point 7 from `useful` to `HELPFUL` while retaining
all twenty `time`, `endTime` and `duration` values and the `%GAP` marker. It bounds
the independent display to timeline seconds 1–4, enables sentence splitting and
changes only its rich `fgColor` to white. The native `ABC` placeholder, default
font, style/preset identifiers and partial underline/strikethrough byte ranges
stay intact. Native save changes only the same three bookkeeping fields.

Fourteen inspected dynamic frames verify the trimmed opening, corrected text,
advancing red highlights, later words and pause clearing. The source `We` onset
precedes the two-second trim and is omitted; the first visible word is `build`.
Unlike a closed cue, a partly trimmed dynamic word does not carry into this
native display. `HELPFUL` starts at source second 2.42475 and maps to timeline
1.212375; `tools` starts at 2.87475 and maps to 1.437375. Frames at 1.2/1.2333
and 1.4333/1.4667 seconds bracket those changes. The odd-tick `%GAP` point retains
its exact rational mapped tick rather than being quantized to a video frame.

All candidates pass structural validation and the existing exact-build schema
profile with no compatibility errors. Raw community errors for `Caption` and
`transcriptionSet` remain separate. No new profile relaxation was needed.
The attempted dedicated VTT import in this batch hung inside the host's native
OneDrive-location check before importing; it was recovered without changing
cloud configuration. The separate current-build interchange evidence above
remains the import contract. This helper verification uses the known unstyled
Caption form, actual native audio-caption/recognition captures and saved output.

These checks cover the exercised plain values, root clocks and display controls.
RTF editing, Group closed clocks and Group source-word/display clocks have separate
contracts below. Other stitched/multiscene mapping, nonzero audio source-file offsets,
physical font closure and other requested delivery settings retain their own
checks. Native definitions, recognition models, fonts and media remain outside
the package. Completed disposable projects, exports, screenshots and diagnostics
are deleted after incorporating the findings and generated-fixture tests.

## Group-contained closed-caption clocks

Version 0.49.0 adds closed-cue mapping, plain cue authoring and selected-child
retiming through Group-only ancestry. The
[caption helper contract](helper.md#caption-json-editing) owns selectors, clocks,
cropping, exact rational output and refusal rules. Version 0.50.0 adds the
source-word and display-bound contract below. Closed holds and recognized word
onsets retain their distinct source-trim behavior. Stitched and multiscene clocks
remain separate.

Locally observed on Mac 2026.2.4 (2026.132), format 10. Native **Edit → Group**
keeps the closed parameter on its linked audio child and leaves cue points in
the source clock. Native-template JSON assemblies then exercise a trimmed 1×
Group, zero-in-point 2× and 0.5× Groups, and three nested Groups around a trimmed,
2× child. Both audio-owned cues and standalone `Caption.captionData` render
the same closed holds. Parent cropping carries the cue already active at the
visible opening. The three-level case shows source cue TWO at global seconds
1–1.5, THREE at 1.5–2.5, FOUR at 2.5–3 and blank output at 3–3.5.

Helper-authored media and global timeline cues match independently written
source-point expectations in both forms. Timeline ALPHA at 1.25–1.75 and BETA
at 2.25–2.75 survive native save and render with the intervening blanks.
Retiming the linked child or standalone Caption in its immediate parent clock
retains every ancestor. Shortening an eight-second child to six seconds leaves
its Group eight seconds long; the last two seconds render blank, and decoded
audio after second 6.1 is silent.
The helper does not resize parents to the edited child's extent.

Signed child and nested-Group starts retain their container-relative meaning;
root placement stays nonnegative. A regression combines inner-Group and child
starts of −1 second beneath a root Group starting at 1. Both caption forms show
TWO at 1–3, THREE at 3–5, FOUR at 5–6 and blank output at 6–7, matching an
independent root clip trimmed to source second 2. Negative parent-clock retiming
retains complete linked mirrors and all ancestors.

Twenty-six native exports total 155.5 seconds at 640×360/30 fps with stereo
44.1-kHz AAC. All 4,665 rendered frames pass cue/clear gates. Independent flat
controls match complete decoded pictures for trims, speeds, nested holds and
linked-child retiming. Five saved projects reopen byte-identically, and four
reopened export pairs reproduce complete decoded video/audio. Cue authoring
and standalone Caption retiming preserve the unchanged Group's decoded audio.

Grouping is not an assertion of whole-stream audio equality with a flattened
layout. The initial native grouping comparison changes samples only in the last
0.0594 seconds; its interior seconds 1–7 are identical. The fast/nested layouts
also differ from their flat audio controls while pictures match. The cause is
unestablished. Compare caption edits against the same Group/audio layout.

Native saves retain complete clocks and source/cue payloads, renumber the new
nested IDs, serialize Group in-points/durations as floats and initialize lane
flags. They omit empty Group-contained Caption metadata. The exact-build
auditor permits that omission only with Group-only ancestry. Root metadata stays
required and present values retain object validation; raw community errors remain
separate. Forty-five input/saved schema checks
pass the profile and native guards. Known positive-in-point accelerated/slowed
Group reload drift remains refused. Other unexercised container forms and native
speed combinations require their own evidence. Completed disposable data is removed.

## Group source-word and dynamic-display clocks

Version 0.50.0 extends default `map` to recognized words through Group-only
ancestry. `--closed-only` retains the independent closed-cue route. The
[caption helper contract](helper.md#caption-json-editing) owns source eligibility,
parent cropping, exact ticks and display-bound inputs. Group source retiming now
accepts actual transcription without a closed parameter. Parent-clock display
bounds change only the selected clean display; every ancestor survives.

Locally observed on Mac 2026.2.4 (2026.132), format 10. A native-template
eight-second AV clip contains generated speech; native **Bebas 3 Line Word Red**
generates fifteen words and one `%GAP` point. The source-track edit rate remains
48000 while transcription uses 705600000 ticks/sec. Native **Edit → Group**
places audio and display inside the same Group, adds its text Quick Property and
retains all source points. Ungrouped/grouped controls have identical decoded
pictures and audio.

The source word `useful` starts at 0.47 seconds, and `tools` starts at 0.88.
A Group trim of 0.7 seconds, placed at global second 1, carries the active
`useful` hold at the opening and switches to `tools` at 1.18. A source trim on
the audio child instead omits earlier word onsets and starts with `tools` at
1.18; its output matches the independent root-audio trim control. A negative
audio-child placement carries the opening hold through the parent crop.

A zero-in-point 2× Group retains exact word/gap times. A three-level case has a
negative inner-Group start and two parent crops; it matches an independent
single-Group source window. Its opening `tools` hold is visible at 1–1.02, followed
by `with`. The native gap starts at source tick 4656078001; its mapped odd tick
and rational seconds remain unrounded. At 30 fps, a short mapped word can fall
between rendered frames without losing its source onset from the map.

Positive display bounds inside a Group match a separate root display control.
A display at parent seconds −1–5 matches the visible 0–5 control while its Group
and audio remain eight seconds long. These edits preserve the placeholder,
partial rich ranges, native style, geometry, Quick Property bindings and source
transcription. They gate the independent display, without moving audio or
expanding its parent.

An assembled root-display/Group-audio control retains all transcription but
renders no words: all 180 active-window frames are uniform gray. Keep audio and
display inside the exercised common Group, or verify another native binding
before relying on it. A source-word clock map alone does not establish display
association, arbitrary caption presets or cross-container source discovery.

Nineteen native exports total 139 seconds. All 3,960 mapped highlight/gap and
display-window frames pass, with the separate 210-frame binding diagnostic above.
Seven independent comparisons match complete decoded pictures; six also match
audio. Four reopened pairs reproduce complete decoded video/audio and four saved
projects reopen byte-identically. Thirteen whole-payload comparisons preserve
all sixteen source points and bundled source bytes, allowing only observed
thumbnail/duration bookkeeping, Group numeric serialization and explicit nested
ID/Quick Property remapping. All 34 input/saved profile checks pass unchanged;
the existing raw `transcriptionSet` discrepancy remains separate.

The negative audio-placement and equivalent Group-trim movies differ in audio
only around global seconds 0.996–1.368. Their seconds 2–7 are sample-identical;
the cause of the opening difference is unestablished. Read-only word mapping
does not promise audio identity across alternate native clock layouts. Source
offsets, other stitched/recording variants, multiple scenes and remaining dynamic
controls retain separate work. Completed disposable data is removed.

## Ordinary-AV stitched caption clocks

Version 0.51.0 maps and edits the native stitched parent's closed cues and maps
its recognized word sequence. Select the parent ID from closed inspection or
the `StitchedMedia` container in `audioUses`. Internal child IDs identify source
occurrences; they are not interchangeable parent selectors. The
[caption helper contract](helper.md#caption-json-editing) owns the supported
shape, source validation, returned provenance and refusal rules.

Locally observed on Mac 2026.2.4 (2026.132), format 10. Native **Edit → Split**
at four seconds duplicates the complete audio-cue parameter onto each linked
half. Native **Stitch Selected Media** creates one `StitchedMedia`, moves the
closed parameter to that parent's `parameters.captions` and removes it from
both audio children. Source transcription remains on the source stream. The
parent's closed clock is the virtual stitch, not either child's source trim.

A second native stitch joins source seconds 0–3 and 5–8. Its closed points
become `ONE` at 0, `TWO` at 2, `THREE` at 3, `FOUR` at 4 and empty at 5.
Its word sequence retains only onsets inside the selected source windows.
`Every` at 2.979375 holds across the join until `Blue` at 3.39875; the removed
`word follows the speaker.` points do not appear in the rendered block.
Forming independent per-child word holds would incorrectly clear that join.
All sixteen original source word/gap points remain unchanged.

A parent trim of 0.7 seconds, placed at global second 1, omits earlier virtual
word onsets and starts highlighting `tools` at 1.18. The active closed cue
still carries into the trim. Cropping the same stitched parent through an outer
Group instead carries `useful` at second 1, then switches to `tools` at 1.18.
The native Group contains the stitched parent and its independent display.

Parent retiming preserves all internal children. A 2× parent and an independent
flat control render an authored `STITCHED EDIT` cue at 1.5–2.5 seconds while
source words retain their own onsets. Display bounds are edited separately.
The exact-build schema profile admits the parent's strict caption-point form
while retaining the upstream checks for every other parameter. Raw community
errors remain visible; input documents stay unchanged.

Default stitched mapping separates `words`, the nominal source-word clock, from
`displayWords`, the measured visible-highlight clock. At unit parent speed they
agree. At 2× parent speed, the first child follows the normal source clock, but
onsets in the final child are projected earlier again. With a final child starting
at virtual second 4 and placement at global second 1, `Blue` at source 5.39875
has nominal time 3.699375 and visible highlight time 3.3496875. A three-child
control with the same final boundary reproduces this behavior; moving that
boundary to second 5 moves the projection. Slowing the parent produces the
corresponding delayed final-window highlights. Removing closed cues leaves the
highlight behavior unchanged. The helper implementation owns the projection;
its internal cause in Camtasia is unestablished.

Trimming into the final child rebases the measured display projection at that
trim. Upper eligibility also follows projected display time: a parent consuming
source seconds 0–5 at 2× highlights `Blue` and `Rivers`, whose original onsets
are beyond second 5. `words` correctly omits those future source-word onsets;
`displayWords` reports their actual visible holds while retaining original source
provenance. Never use native highlight timing as an audio-cut clock.

A separate native Group containing the unit-speed stitched parent and its display
accepts 2× Group speed with uniform source/highlight timing. Keep the stitched
parent at unit speed and apply speed to that common Group for this measured
alternative. A slowed stitched parent inside an accelerated Group retains the
owner-local display projection even when the nominal speeds cancel.

Twenty-six native exports total 158.6 seconds and 4,758 frames. All frames pass
both closed-cue and visible-highlight/gap checks using the corresponding map.
Six independent reopen/fresh-process pairs reproduce complete decoded RGB and
PCM. Three helper project reopens are byte-identical. Twenty-one whole-payload
comparisons preserve source transcription, bundled media and all unrelated
payload after only observed thumbnail/duration bookkeeping, crop-default
normalization and Group serialization changes. All 52 input/saved schema checks
pass the profile and native guards; raw upstream diagnostics remain separate.

The continuous unit-speed stitched picture matches the independent flat control. Decoded
audio differs between these native layouts; preserved source bytes do not
establish sample identity after stitching. Compare edits against the same
stitched layout and verify its own independent reopen/export. Recording holds,
multiple-source stitches, nonzero source-file offsets and multiple scenes remain
separate work. Audio-only additions follow below. Completed disposable data is removed.

## Audio-only stitched caption clocks

Version 0.52.0 adds ordinary same-source audio-only stitched parents to the
[caption helper contract](helper.md#caption-json-editing). The native parent
owns closed cues; its children are plain `AMFile` nodes. Source and physical
audio IDs coincide for these children. Parent text/cue edits and retiming retain
every child, its parameters and source transcription. AV/audio mixtures,
recording holds, other sources and multiscene clocks remain separate forms.

Locally observed on Mac 2026.2.4 (2026.132), format 10. An eight-second mono
48-kHz WAV contains synthetic speech. Native Bebas word-red generation saves
fifteen words and one gap in the project tick clock. Native Split at four
seconds duplicates closed points on both audio halves. Stitch Selected Media
moves those points to one parent, removes the child parameters and keeps all
source points unchanged. The exact-build schema profile also admits the strict
caption-point form on ordinary `AMFile`, without changing the generic parameter
map or recording-specific types.

A native stitch of source 0–3 and 5–8 seconds produces parent closed points at
0/2/3/4/5. Its `Every` onset at 2.961 holds across the join until `blue` at
virtual 3.442. The unstitched control instead clears words at second 3 until
`blue`. All original source points remain available to other uses.

A parent trim at 0.7, placed at global second 1, omits earlier word onsets and
begins with `tools` at 1.23. An outer Group crop instead carries `useful`, whose
source onset is 0.5. The native Group retains the display's text Quick Property
and its global geometry through an observed local-position rebase.

Audio-only parent retiming accepts exact subframe cuts. A 0.01-second trim and
placement, with 7.99-second duration, saves and reopens without video-frame
quantization. A helper-authored `AUDIO EDIT` cue renders at global seconds 2–4,
while internal children and source points remain unchanged. The independent
display stays on its own video frame bounds.

Parent 2× and slowed controls reproduce the final-child display projection
observed for AV stitches. Keep using `words` for nominal source-word timing and
`displayWords` for the measured display projection. A unit-speed audio stitch
and display inside a 2× common Group match the independent sped flat control's
complete picture. Existing source/Group crop distinctions remain intact.

Exact mapped onsets do not guarantee a native pixel change on that same frame.
The source word `clear` starts at 1.6 seconds. At 30 fps, both unit-speed flat
and stitched movies retain `with` on frame 48 and switch to `clear` on frame 49.
Their 2× controls likewise switch one frame after the exact mapped boundary.
Some slowed, subframe and Group layouts show the same one-frame delay at
`useful` or `clear`. The source points and exact map ticks are preserved; no
general offset or rounding repair is inferred. Inspect exports when a specific
video frame matters. The internal cause is unestablished.

Fifteen exports total 109 seconds and 3,270 frames. All closed-cue states and
word-presence/gap states match. Exactly 3,255 highlights match the projected
holds; the remaining fifteen frames are the explicit one-frame boundary
observations above, each followed by the expected word. Five inspected reference
sheets cover every word in the full, trimmed, slowed and joined/separate layouts.
Three independent reopen pairs reproduce complete decoded RGB and PCM, and the
three saved projects reopen byte-identically. Thirteen whole-payload comparisons
allow only observed thumbnail/duration caches, Group numeric serialization,
track defaults, ID/Quick Property remapping and display-position rebasing. All
sixteen source points and thirteen bundled WAV copies remain unchanged. All 37
input/saved checks pass the exact-build profile and native guards, with raw
upstream discrepancies retained separately.

The unit-speed, trimmed and common-Group-speed pictures match their independent
flat controls. Decoded audio also matches for the trim control, but differs for
the unit-speed and Group-speed layouts. Use the same layout's independently
reopened output as its audio control; source preservation does not promise
sample identity across native layouts.

One source-skip opening crashed with a background memory-corruption trap while
the main thread initialized the tool palette. The old process exited; a fresh
matching process opened, saved and exported the same candidate normally. This
does not establish a project-parser rejection. Original saved bytes stayed
unchanged and the original editor window was restored. Completed disposable
projects, media, exports, screenshots and audit records are removed after shipping.

## Global closed-caption styling

Version 0.47.0 adds `set-style` for existing `timeline.captionAttributes`.
The [caption helper contract](helper.md#caption-json-editing) owns the spec,
supported fields/fonts and refusal rules. This edits global closed-caption
appearance independently of cue content, timing and dynamic-caption Callouts.
RTF bodies are preserved; the separate text editor below handles supported RTF
content. Resolving local rich-style overrides and physical font closure are unchanged.

Locally observed in Camtasia Mac 2026.2.4 (2026.132), format 10. The native
caption-options menu opens **Caption Settings**, with font, size, text color,
background color and background opacity. Native size 32→48 changes only
`fontSize`; `defaultFontSize` remains true. The font picker shows Arial,
Trebuchet MS and Verdana. A native Trebuchet/48/orange/blue control retains all
cue points and the existing global flags, language and legacy opacity value.

The native background-opacity slider changes the alpha byte of
`backgroundColor`. Moving its saved value from 204 to 128 leaves the separate
legacy `opacity: 0.5` unchanged. Setting it to zero removes the panel. Changing
background RGB through the color picker preserves that opacity when the dialog
is applied. Foreground-alpha controls are JSON-authored and natively saved,
reopened and rendered; no native foreground-opacity slider is inferred.

An orange Verdana/40 control with transparent background has three foreground
alpha states. Full and intermediate alpha produce different visible fills.
At zero, the native black glyph outline remains readable: changing foreground
alpha does not hide the complete caption. All saved alpha bytes survive native
reopening. Rendered video pixels do not establish a general color/linear-alpha
calibration. The blue panel stores RGBA 32/48/96/128 and an exercised interior
pixel renders RGB 79/86/109 over gray video; native and helper controls agree.

Six whole-document native/helper comparisons cover size, font, foreground RGB,
background RGB, background alpha and a combined Verdana/size/clear-panel edit.
The first save also normalizes the copied source's filename/channel metadata,
IDs, unit-opacity default and track heights. Later comparisons differ only in
thumbnail/command caches and requested style values. Four additional literal
candidates verify complete style replacement, intermediate/zero foreground
alpha and the standalone imported-caption owner. No native definition or font
file is distributed.

Seven eight-second variants use `First café & timing`, then
`Second caption → end` at four seconds, with clearing at seven. Native Add
Caption's audio-owned form and the standalone `Caption.captionData` form render
the same global style. Six first-save comparisons preserve every other payload
after thumbnail normalization and the standalone clip's four known initial
metadata defaults. Four independent reopened saves are byte-identical.

Ten native exports are 640×360 H.264 at 30 fps with stereo 44.1-kHz AAC.
All three repeat pairs reproduce their complete 240 RGB frames and PCM.
Both audio-owned helper exports and both standalone-caption exports reproduce
the native combined-style control's decoded RGB exactly. All ten outputs have
identical decoded audio. Three contact sheets contain 126 inspected phase
frames; fourteen full-size views verify the accent, arrow, font/size, panel,
fill and persistent outline. All 180 sampled cue/clear frames and 160 tone
windows retain their expected behavior; RMS is 0.06786–0.06817 with 440-Hz tone
power above 0.9996.

Twenty-three snapshots pass the exact-build schema/profile and native hazard
checks. Raw errors on the three standalone-Caption snapshots retain the pinned
upstream schema's existing missing-branch diagnosis; no profile correction is
added. Original and reusable baseline bytes remain unchanged; all seven bundled
media hashes agree. Completed disposable projects, exports, screenshots and audit
files are deleted after incorporation.

## Native RTF text editing

Version 0.48.0 adds RTF inspection and substring edits through the
[caption helper contract](helper.md#caption-json-editing). Use the decoded text
and occurrence index to prepare a guarded edit spec. The helper retains cue
clocks and global style; it does not flatten RTF into plain text or reconstruct
local style runs. Supported parsing and style inheritance belong to that helper.
[Microsoft's RTF specification](https://officeprotocoldoc.z19.web.core.windows.net/files/Archive_References/%5BMSFT-RTF%5D.pdf)
and [Apple's RTF extensions](https://developer.apple.com/library/archive/documentation/Cocoa/Conceptual/AttributedStrings/Tasks/RTFAndAttrStrings.html)
describe grouped controls and Unicode text encoding. Complex document content
and other RTF representations retain a separate editing contract.

The Mac 2026.2.4 (2026.132), format-10 native caption editor accepts formatted
paste into its Caption Text field and saves Cocoa RTF with null `textAttributes`.
This provides a current-build RTF capture without relying on the dedicated SAMI
importer. The attempted import in this batch stalled in the documented
OneDrive-classification/file-read path before saving captions. The exact hung
editor process was sampled and stopped through Activity Monitor after preserving
saved/recovery bytes; the replacement process completed editing and exports.
No cloud settings changed. The unrelated original project retained its hash.

Native captures include separate bold and italic font runs, an ANSI-escaped
accent, Unicode arrow/omega, escaped braces and backslash, and a backslash plus
literal newline. A native emoji paste uses an additional font-table entry and
unsigned UTF-16 surrogate controls. The editor's Unicode spelling can differ
from the helper's signed controls without changing the decoded text.

A linked audio-owned candidate replaces bold `café` with `COFFEE`, appends an
italic `s`, changes another bold word, inserts Unicode before a line boundary,
replaces text inside literal braces and appends punctuation. A separate native
caption-editor control authors the expected result. A standalone Caption uses
the same saved RTF and edits. Both candidates independently save, close, reopen
and export twice. Their four complete decoded RGB streams match the native
expected control, including formatting and line layout. Their audio matches too.

A third candidate clears every character from the first RTF cue and replaces
text spanning a normal/bold boundary in the second. The cleared RTF retains its
header and controls but renders no caption panel. Two exports separated by an
independent reopen match a separate plain-text control authored with the
previously verified cue representation. Remaining literal braces, backslash,
accent and arrow render correctly. This control is JSON-authored; the separate
rich expected-result control above is authored through the native text editor.

Nine eight-second H.264/AAC movies retain 640×360, 30 fps and stereo 44100-Hz
audio. All three repeat pairs match complete decoded video/audio; all nine
movies have identical decoded audio. All 2160 frames pass cue/clear-state checks,
including the original three-second gap boundary and seven-second final clear.
Three edited project reopens are byte-identical. First saves of audio-owned
edits change only the thumbnail; standalone initialization adds only the four
previously observed Caption metadata defaults. Fourteen document/profile checks
pass without compatibility errors. Four standalone snapshots retain the known
93 raw upstream Caption diagnostics; no profile correction was added.

Native glyph limits remain visible. The original native bold `café` capture
renders an extra replacement glyph at its following style boundary. Replacing
that word with ASCII removes it in both independently authored expected output
and helper output. The emoji renders as a missing-glyph box in both edited
outputs, including the native control with its saved emoji font entry. Successful
RTF decoding does not prove native glyph coverage, repair an existing native
boundary defect or provide physical font closure. Inspect actual output before
delivery. Nested timing, other RTF forms and remaining dynamic controls are
still tracked in the feature-completion plan.

The policy review exposed a deletion boundary that the initial native batch
did not exercise: deleting an encoded paragraph token after an undelimited
style control can join that control to remaining text. The editor now leaves
zero-width lexical separators at removed chunks. Fixed library and CLI tests
cover the original reproducer and multiple removed chunks separated by retained
style controls.

A focused native follow-up uses JSON-authored RTF from the captured text-only
form, including explicit paragraph controls. It replaces a bold word, appends
italic text, deletes two paragraph/text chunks across a retained italic switch,
and clears a complete later cue. Audio-owned and standalone variants each
save/reopen and export twice. All four movies match a separately authored
literal RTF/plain-clear control in complete decoded video/audio. Both project
reopens are byte-identical; all 1200 frames pass cue/clear checks. Nine additional
profile/hazard checks pass with the same known raw Caption-branch diagnostics.
The five follow-up movies retain the first batch's identical audio. Existing
global style, clocks, source data and unrelated payload survive.
