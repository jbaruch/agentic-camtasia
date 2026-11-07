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
stitched captions retain their separate clock investigation.

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
RTF editing and Group closed clocks have separate contracts below.
Group source-word and stitched/multiscene mapping, nonzero audio source-file offsets,
physical font closure and other requested delivery settings retain their own
checks. Native definitions, recognition models, fonts and media remain outside
the package. Completed disposable projects, exports, screenshots and diagnostics
are deleted after incorporating the findings and generated-fixture tests.

## Group-contained closed-caption clocks

Version 0.49.0 adds closed-cue mapping, plain cue authoring and selected-child
retiming through Group-only ancestry. The
[caption helper contract](helper.md#caption-json-editing) owns selectors, clocks,
cropping, exact rational output and refusal rules. Source-word mapping through
Groups remains pending; closed holds and recognized word onsets have different
trim behavior. Stitched, multiscene and dynamic-display Group clocks remain separate.

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

Twenty-two native exports total 127.5 seconds at 640×360/30 fps with stereo
44.1-kHz AAC. All 3,825 rendered frames pass cue/clear gates. Independent flat
controls match complete decoded pictures for trims, speeds, nested holds and
linked-child retiming. Four saved projects reopen byte-identically, and three
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
profile permits that omission while retaining object validation when present;
raw community errors remain separate. Thirty-nine input/saved schema checks
pass the profile and native guards. Known positive-in-point accelerated/slowed
Group reload drift remains refused. Other unexercised container forms and native
speed combinations require their own evidence. Completed disposable data is removed.

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
