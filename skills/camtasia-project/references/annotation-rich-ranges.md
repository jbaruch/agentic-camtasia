# Mixed annotation rich-text ranges

Use the [annotation workflow](helper.md#annotation-json-editing) for explicit
range styling. The helper owns input versions, offsets, supported properties,
partition validation, merging and refusals. These observations use Camtasia Mac
2026.2.4 (2026.132), format 10, on a native Basic text Callout. They establish
static rich text, not animated attributes, RTF conversion or physical font closure.

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
