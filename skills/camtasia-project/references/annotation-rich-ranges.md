# Mixed annotation rich-text ranges

Use the [annotation workflow](helper.md#annotation-json-editing) for explicit
range styling. The helper owns input versions, offsets, supported properties,
partition validation, merging and refusals. These observations use Camtasia Mac
2026.2.4 (2026.132), format 10, on a native Basic text Callout. They establish
static rich text. Timed rich-style steps have the separate verification below;
RTF conversion and physical font closure remain separate.

## Independent property partitions

The native text `Alpha café — omega\nBeta 42` occupies 29 UTF-8 bytes. Bold
`café` is a `fontWeight` run over bytes 6–11, surrounded by weight 400. Italic
`omega` is a separate `fontItalic` partition over bytes 16–21, with native value
2. The other properties need not share either partition.

Native size changes create size 36 over bytes 0–22 and size 28 over bytes
22–29. Underline value 1 covers the first line and newline; value 0 covers the
second line. Color initially has orange `(255,128,64,255)` over bytes 0–5 and
cyan `(32,192,240,255)` over bytes 5–29. The default font object remains
unchanged while rich properties control the displayed text.

Resetting only `fé` to regular weight leaves `ca` bold over bytes 6–8 and
coalesces regular weight over bytes 8–29. Changing `pha café` to green
`(128,224,64,255)` crosses the existing color boundary and creates bytes
0–2 orange, 2–11 green and 11–29 cyan. Other property partitions survive.
Native saves can permute the rich property list; that order is distinct from
the text positions carried by each run.

Seven complete native edit replays match the helper after accounting for
thumbnail/command-counter metadata and rich-list permutation. Both complete
helper-produced annotation owners also match their independently captured
native mixed and edited controls before identity/timeline placement.

## Rendered and persistence controls

A 25-second sequence contains five separate five-second cells: helper mixed,
native mixed, helper edited, native edited and a helper whole-property weight
reset. The reset removes the remaining bold span while retaining italic, size,
underline and color partitions. All cells use the same native 400×250 text box
over repeated generated background AV. No recording-audio mirror is involved.

Two fresh-process exports repeat all 750 decoded RGB frames and complete
stereo PCM audio exactly. Fifteen inspected phase frames and five enlarged
text crops show the full accented text, em dash, line break, emphasis, colors
and smaller un-underlined second line. Helper/native mixed comparisons have
maximum mean absolute RGB difference 0.379 byte levels per channel; edited
comparisons stay below 0.083. These separate-cell comparisons are not bitwise
equivalence claims. The observed bright text remains within canvas bounds.

All ten measured audio-channel windows retain 440 Hz, with RMS
0.096099–0.096116. Outputs are 640×360 H.264 at 30 fps with stereo 44.1 kHz AAC.

The first native save remaps twenty clip IDs and updates two UI caches.
Every other field matches, including rich values and ranges, default fonts,
geometry, source definitions and audio. The fresh-process save is byte-identical.
All three bundled source hashes and the original baseline remain unchanged.
Twelve capture/candidate/save snapshots pass both the raw schema and existing
exact-build profile without a new correction.

Verify requested font files, glyph coverage, ligatures and fitting in the
consumer project. Code-point selection does not promise grapheme-aware editing.
Completed native projects, exports, screenshots and measurements are deleted
after incorporation into the plugin and generated-fixture tests.

## Timed rich-style steps

Locally observed in Camtasia Mac 2026.2.4 (2026.132), format 10. The annotation
helper's `set-rich-steps` and `clear-rich-steps` commands add discrete timed
styles to root remix text annotations. The module docstring and
`rich_step_frames`, `rich_source_time`, `set_rich_steps` and `clear_rich_steps`
own the input, clock, replacement and preservation contracts. General `set`
continues to require static rich text; clear timed styles explicitly before
changing text content. Nested clocks, RTF conversion and physical font closure
remain separate work.

Native Auto Animate followed by a font-size edit saves one static rich frame.
Adding an explicit Custom animation first still edits that static frame. These
UI operations do not establish a font-size ramp. A separate JSON-authored
candidate retains the native initial rich-state list and adds a second complete
list as either an interval or a point. Native save accepts both forms, removes
their redundant interpolation fields and playback switches at endTime. At the
interval midpoint the size remains 32; after its endpoint it is 64. The helper
therefore authors discrete points rather than promising continuous interpolation.
These timed states are JSON-authored and natively saved/rendered, not captured
as a native UI authoring operation.

The first state remains at native time zero. Subsequent complete lists contain
independent per-property UTF-8 partitions, preserving native property types and
opaque run fields. They do not replace the annotation's text or default font.
A trimmed 2× control starts at timeline second one, has source in-point one
second and a rich point at source second two. Native size readback is 32 at
global 1.25 seconds and 64 at 1.75 seconds. This establishes source-position
clock conversion independently of timeline placement. With no visual interval
in the candidate, native saving reconstructs the observed interval preceding
the point; rich playback remains discrete. Existing independent geometry and
visual intervals are retained by the helper.

An 88-second sequence compares complete literal reference states with helper
output and three independent static controls for clearing. The text is `A café`.
A positive source in-point and 2× speed place the three requested local style
changes at source seconds four, six and eight. Initial 32-point white becomes
64-point orange, then café alone becomes bold cyan, then the whole annotation
becomes 24-point green and underlined while café stays bold. Native property
readback confirms size/color/underline states. Independent translation continues
through every style step and after clearing at local 1.5, 2.5 and 3.5 seconds.
Separate controls retain the accepted interval-shaped step, the UI-authored
static size and an empty background. References reuse native static rich payloads
and the accepted point representation; no missing UI animation capture is inferred.

Two same-process exports separated by saved close/reopen match all 2640 decoded
RGB frames and complete stereo PCM: 88-second 640×360 H.264 at 30 fps with stereo
44.1 kHz AAC. Three inspected contact sheets contain 88 unique phase frames;
four full-resolution views verify accents, range color/bold and underline.
Across 187 sampled frames, 68 matched reference/helper comparisons differ by at
most 0.849 mean RGB byte levels per channel. Frame-boundary measurements retain
white before the first switch, orange afterward, cyan only from the second
switch and green from the third. The interval control stays small until its
endpoint, and the UI-created size remains static. All 132 audio-channel windows
retain the 440 Hz background tone with RMS amplitude 0.09559–0.09654.

Strict whole-document comparison of the sequence permits only 43 remapped IDs,
duration text and thumbnail. Every other value remains equal, including all
rich frames/partitions, text/font data, geometry, source definitions and audio.
Reopened saves change only the thumbnail. Original baseline and bundled AV
hashes remain unchanged. Thirteen snapshots pass raw schema, exact-build profile
and native hazard checks without a correction. Completed disposable projects,
movies, screenshots and measurements are deleted after incorporation.

## Text layout switches

Locally observed in Camtasia Mac 2026.2.4 (2026.132), format 10. Annotation
`set` definition edits support the native automatic-sizing choice and ligature
flag. Layout-only edits can retain timed rich states; they do not run the static text-replacement
path. Other text content edits retain their existing static-state requirement.

Native **Auto-resize text** stores `resize-behavior: "resizeText"` when enabled
and `"resizeCallout"` when disabled. Native **Font Ligatures** stores numeric
`enable-ligatures: 1.0` or `0.0`. Use the native numeric flag in definition specs,
not a JSON boolean. First native edits add owner reset companions
`default-callout-resize-behavior: "resizeText"` and
`default-callout-enable-ligatures: "1"`. The helper preserves existing reset
metadata without inventing missing defaults.

A 320×90 Georgia text box contains `office ffi fi fl waffle`, with rich fontSize
64. Automatic sizing displays 39 in the native property panel while the saved
rich value remains 64. Disabling automatic sizing displays 64 and clips text to
the retained box; it does not guarantee that the complete text fits. Restoring
automatic sizing returns the smaller fitted text. Native character-spacing
controls retain their own rich values; layout switches change neither those
values nor text/range partitions, default fonts or geometry.

Six whole-document native/helper comparisons cover disabling/restoring sizing,
ligatures off/on and a combined edit. Only thumbnail/command caches and the two
observed first-edit reset additions are normalized. A 128-second sequence pairs
those controls and adds a seventh pair retaining discrete size/color states and
independent translation. Timed helper readback shows orange size 32; the two
static helper readbacks show size 64 with both switches off, then fitted size 39
with both on. The timed-rich property panel does not expose the automatic-sizing
checkbox in this capture; its saved choice and output remain under comparison.

Four inspected contact sheets contain 128 unique phase frames; six full-size
views verify clipping, fitted text, spacing and timed colors. Across 192 sampled
frames, 84 native/reference-helper comparisons differ by at most 1.034 mean RGB
byte levels per channel. The fixed unspaced control occupies a 283×90 bright-pixel bounding box;
the automatic control occupies 205×74. Native and helper bounds agree. The
Georgia ligature variants retain the same visible layout in these controls;
this establishes native flag parity, not a visible glyph-substitution result
for arbitrary fonts. Verify the requested font, text and fitting on its host.

Two same-process exports separated by saved close/reopen are 128-second
640×360 H.264 at 30 fps with stereo 44.1 kHz AAC. Complete decoded PCM is
identical. RGB is not bitwise-identical: 3830 of 3840 frames have nonzero pixel
differences, with maximum per-frame mean difference 0.848 byte levels. All
192 audio-channel windows retain the 440 Hz background tone with RMS amplitude
0.09559–0.09654. The paired layout states and independent movement remain visible
across this measured repeat-video variation.

Strict whole-document sequence comparison permits only 63 remapped clip IDs,
duration text and thumbnail. Rich frames/partitions, all definition fields,
geometry, intervals, reset metadata, sources and audio otherwise remain equal.
Reopened saves change only the thumbnail. Source and original baseline hashes
remain unchanged. Twenty-three snapshots pass raw schema, exact-build profile
and native hazard checks without a correction. Completed disposable projects,
movies, screenshots and measurements are deleted after incorporation.
