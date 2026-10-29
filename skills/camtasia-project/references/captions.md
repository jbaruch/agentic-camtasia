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
1.000–2.000 and 2.000–4.000, matching trim, speed, and offset. Nested groups
and stitched captions still need their container mappings; this probe does not
establish their internal clock contracts.

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
