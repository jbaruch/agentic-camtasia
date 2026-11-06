# Mixed-style annotation text edits

Use the [annotation workflow](helper.md#annotation-json-editing) for explicit
substring replacement, insertion and deletion. The helper owns schema version 3,
original code-point coordinates, expected-text guards, style anchors and refusals.
These observations use Camtasia Mac 2026.2.4 (2026.132), format 10, on the Basic
text Callout described in [mixed rich ranges](annotation-rich-ranges.md).

## Native editing controls

The initial text is `Alpha café — omega\nBeta 42`, with independent weight,
italic, size, underline and color partitions. Replacing `café` with `résumé`
inherits the original `c` properties: bold covers UTF-8 bytes 6–14, italic
`omega` moves to 19–24, and the smaller second line begins at byte 25.

Inserting ` très` immediately after `résumé` inherits the original character to
the left of the caret. The helper requests that character explicitly with
`style_from: 11`; it does not infer caret state. Bold then covers bytes 6–20,
italic covers 25–30, and the second-line boundary moves to 31.

Replacing `Alpha résumé très` with `Résumé`, anchored at original character 0,
removes bold while preserving the italic `omega`, size and underline partitions.
Orange covers bytes 0–8 and cyan covers 8–26. Deleting ` — omega` produces
`Résumé\nBeta 42`: orange ends at byte 8, while size and underline change at
byte 9. Other property payloads and the default font remain intact.

Deleting all remaining text saves one static `textAttributeList` frame with
`value: null`. After a fresh-process reopen, native insertion of `Reborn café`
creates seven full-string properties over bytes 0–12: Helvetica size 12, weight
400, italic/underline/strikethrough 0 and white `(255,255,255,255)`. Kerning is
absent. The native default font object still says Montserrat size 96; it cannot
supply the new typing style. The native paragraph alignment also changes from
center to left. A complete helper replay supplies the seven explicit
`text_style` properties and separately requests left alignment in `definition`.

A compound edit changes `café` to `tea` and `Beta 42` to `Go`. Both selections
use coordinates from the original text. The native control performs the edits
right-to-left; the helper applies one original-coordinate request. The result
is `Alpha tea — omega\nGo`, with bold bytes 6–9, italic 14–19 and the size/
underline boundary at byte 20.

Seven complete native edit replays match after accounting only for project
thumbnail/command-counter metadata and rich-list permutation. The seven complete
helper-produced Callouts also match their independent native controls before
fresh identity and timeline placement.

## Rendering and persistence

An 80-second sequence contains sixteen five-second cells: the mixed baseline,
seven helper/native pairs and a background-only control. All use the same native
400×250 text box over repeated generated background AV; no recording-audio mirror
is involved. Forty-eight inspected phase frames and enlarged reinsertion crops
show matching accented text, line breaks, wrapping, emphasis, colors and placement.
The empty cells show only the background. Bright-text bounds match in every
paired phase and remain within the canvas.

Separate-cell mean absolute RGB differences range from 0 to 0.201 byte levels
per channel. Empty/background comparisons stay below 0.158. These compressed
cell comparisons are distinct from the two fresh-process exports, whose complete
2,400-frame decoded RGB streams and stereo PCM audio are identical. All 32
audio-channel windows retain 440 Hz, with RMS 0.096082–0.096118. Outputs are
640×360 H.264 at 30 fps with stereo 44.1 kHz AAC.

The first native save remaps 63 clip IDs and updates the project thumbnail and
duration UI cache. Every other field matches, including text/ranges, paragraph
controls, default fonts, sources and audio. The fresh-process save is
byte-identical. Thirteen capture/candidate/save snapshots pass both the raw schema
and existing exact-build profile without a new correction. All three bundled
source hashes and the original baseline remain unchanged.

These controls establish static substring edits. Animated attributes, RTF,
grapheme-aware selection, physical font closure and automatic caret-style
inference retain separate contracts. Completed disposable projects, media,
exports, images and audits are deleted after incorporation into the plugin and
generated-fixture tests.
