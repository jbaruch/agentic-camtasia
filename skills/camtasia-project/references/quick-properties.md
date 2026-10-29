# Group Quick Properties

These native contracts apply to Camtasia Mac 2026.2.4, format `10.0`, with a
grouped [Lottie source](lottie.md) and a native Basic text box. TechSmith describes
[Quick Property assets](https://support.techsmith.com/hc/en-us/articles/360032837791-Customize-the-Intros-Lower-thirds-and-Outros-in-Camtasia-Editor-Video)
as reusable assets with editable text, colors, fonts, and other controls. These
probes establish color, text/typography, font-theme application and linked text
controls below. [Media Quick Properties](media-quick-properties.md) have a separate
native AV replacement/clear contract and additional image/linking dependencies.

## Bindings and ownership

The group owns `attributes.assetProperties`, an ordered array. A native color
entry has `type: 1`, a display `name`, and an `objects` array of bindings:

```json
{
  "type": 1,
  "name": "Circle Fill",
  "objects": [{"media": 8, "property": "Color000"}],
  "themeMappings": {"fill": "accent-2"}
}
```

`media` identifies the child clip, while `property` identifies its dynamic color.
The actual color components remain in the child's
`sourceEffect.parameters.Color000-red/green/blue/alpha`. A source-bin ID and a
child clip ID are separate references. Discover the imported source's color
definitions and retain the complete child and group, including unknown data.
Other numeric property types and binding names are opaque until demonstrated;
the integer text bindings below are a separate native form.

Renaming the two entries to **Circle Fill** and **Panel Fill** changes their
names without changing bindings, geometry, source defaults, or child colors.
Reordering through the native handles reverses the `assetProperties` entries
without reordering clips or changing colors. When cloning groups, remap every
bound child ID along with the child; retain array order and local child clocks.

## Theme slots and application

The native editor exposes five fill mappings:

| Native choice | Saved `themeMappings.fill` |
| --- | --- |
| Foreground | `foreground-1` |
| Background 1 | `background-1` |
| Background 2 | `background-2` |
| Accent 1 | `accent-1` |
| Accent 2 | `accent-2` |

Setting a mapping before selecting a theme leaves concrete colors unchanged.
Applying the synthetic five-color theme adds `metadata.AppliedThemeId` to the
group and writes the mapped RGB values into the child's source-effect
parameters. It does not change the source JSON, source defaults, or the child's
theme metadata. Once that theme is active, saving a changed mapping also applies
its resource color. Preserve the actual native decimal values; this path writes
approximately fifteen significant digits, rather than binary32 quantization.

The tested theme provides white, dark blue, gray-blue, blue, and orange resources.
All five selections have native saved constructors and inspected output. The
second property stays on Background 1 during these individual-slot tests.
Theme selection is separate from merely storing a mapping: the automatic group
constructor's default `background-1` mappings initially retain red/cyan colors.

## Link, unlink, remove, and re-add

The native **Link with item above** operation merges the two color entries.
In this specimen it keeps the first label, appends the second binding to
`objects`, and adopts the **second entry's mapping**. With a theme active, both
child colors become that resource color. Selecting Accent 1 on the linked entry
then updates both colors through its two bindings.

Unlinking creates two entries with one binding each. Both inherit the linked
label and mapping; the original second label is not restored. The two concrete
colors remain equal at that point.

Removing the second entry hides that Quick Property and retains the child's
color. Re-adding **Color 2** from Available Properties creates an entry with the
default label and its original binding, with **no `themeMappings` field**. It
preserves the current color. An absent mapping does not mean Background 1.
Changing the first entry's mapping afterward updates only its mapped color;
the re-added unmapped color stays independent.

Available Properties also contains the media source. Select the actual color
entry when restoring a color control; adding the source creates another kind of
property. A cancelled source-property addition is not evidence of media
replacement support.

A direct native edit of the restored color to RGB `(200,40,200)` changes only
its three RGB source-effect components. The group keeps its selected theme ID,
property order, and mappings, and the other color remains orange. This observed
Quick Property edit adds no reset metadata. Preserve reset metadata already
present; the separate per-clip Dynamic Properties path can add native reset
strings and must not be normalized into this path.

## Native resave and output

Fifteen native constructor captures supply a 120-second sequence, with an
eight-second background slot and a four-second grouped animation per case.
Children remain at local time zero while their groups move on the scene clock.
The native editor renumbers clips into track-storage order and updates the
Quick Property child references. A strict comparison applies the observed
75-node ID map and the duration-label change from `00:08` to `02:00`; all
other payload, timing, colors, source defaults, and audio remain under comparison.
Retain an explicit ID map when the native editor reallocates IDs. Dropping all
IDs from a comparison would hide broken bindings.

Native save/close/reopen and independent exports reproduce complete decoded
video and audio exactly. Forty-five actual native frames were inspected beside
three repeated background frames. They verify both sampled held positions,
every color state, retained colors after unlink/remove/re-add/reorder, direct
editing, transparency, and disappearance after the group ends. Measured encoded
RGB remains separate from native parameter RGB; this is not color-transfer
calibration. Raw community schema and the existing exact-build profile both
pass without additions.

The test theme definition and logo have separately retained exact bytes. The
temporary user copies are archived after normal Quit, and preexisting theme
files remain byte-identical. Restore those dependencies before repeating the
theme tests. Media source hashes do not resolve theme, font, or library closure;
see [native theme dependencies](advanced-features.md#themes).

Repository evidence is `build/native-verification/lottie-quick-sequence-comparison.json`,
the fifteen native captures, source/theme receipts, and tested
`lottie_quick_contract.py`. Generated verification media and private native
automation helpers are excluded from the distributed plugin.

## Text group constructor

Grouping a native five-second Basic `text-rectangle` Callout creates a Group
with one child on its nested track. The observed group retains visible box
bounds `widthAttr: 376`, `heightAttr: 176`; these are not the 640×360 canvas
dimensions. The child stays at local time zero. The Group owns two ordered
`attributes.assetProperties` entries:

```json
[
  {"type": 0, "name": "Text", "objects": [7],
   "themeMappings": {"font-color": "foreground-1"}},
  {"type": 1, "name": "Callout", "objects": [7],
   "themeMappings": {"fill": "background-1", "outline": "accent-1"}}
]
```

These `objects` values are integer **child clip IDs**, not the Lottie
`{media, property}` objects. The text and appearance entries both refer to the
same Callout. Native grouping preserves its complete definition and parameters
apart from its allocated ID. Copy the demonstrated constructor and remap all
bindings with the child; do not invent a shared binding shape for all types.
Automatic mappings alone do not establish applied theme values.

## Text and rich font runs

Editing the Text Quick Property from `ABC` to `Build → Buy` changes the child's
`def.text` alone. Selecting Arial then materializes rich properties in
`def.textAttributes.keyframes[0].value`; the original `def.font` stays as the
Montserrat Regular 64-point default. The keyframe retains `time: 0`,
`duration: 0`, and `endTime: 0`. All eight entries initially cover
`rangeStart: 0`, `rangeEnd: 13`: the string has eleven Unicode codepoints but
**thirteen UTF-8 bytes**.

| Rich property `name` | `valueType` | Native initial value | Exercised edit |
| --- | --- | --- | --- |
| `fontName` | `string` | `Arial` | Native family selection |
| `fontWeight` | `int` | `400` | Bold Italic → `700` |
| `fontItalic` | `int` | `0` | Bold Italic → `2` |
| `fontSize` | `double` | `64` | Size slider → `48` |
| `underline` | `int` | `0` | Enabled → `1` |
| `strikethrough` | `int` | `0` | Enabled → `-1` |
| `fgColor` | `color` | `(46,59,68,255)` | Purple → `(60,20,180,255)` |
| `kerning` | `double` | `0` | Horizontal spacing → `2` |

Preserve the native signed codes, value types, and color tuple. Do not replace
italic/strike values with booleans, infer rich colors by rounding the default
font's channels, or rewrite `def.font` as a substitute for rich overrides.
Native saves can permute this known eight-property array. Comparison may sort
that unique demonstrated set by `name` while retaining every entry field;
unknown, duplicate, mixed or multi-keyframe data remains under strict comparison.
This is an observed comparison allowance, not permission to discard style runs.

A subsequent multiline edit to `Build →\nBuy now` extends all eight ranges to
seventeen UTF-8 bytes while preserving their styles. Recompute affected byte
ranges when changing text; this specimen establishes one uniform run per
property, not arbitrary overlapping/mixed styles. Rich `fgColor` can override
the defaults, as also observed in [dynamic captions](captions.md).

## Alignment, opacity, stroke and layout

Horizontal alignment writes `def["horizontal-alignment"]` as `left`, `right`
or `center`. Vertical alignment writes `def["vertical-alignment"]` as `top`,
`bottom` or `center`; the UI's middle choice saves `center`.

The text editing pane's opacity slider writes the **child Callout's overall**
`parameters.opacity`; 50% saves `0.5`. It fades the white box and outline along
with the text. Rich `fgColor` alpha remains 255 and the group opacity is unchanged.
Keep text-color alpha, text-stroke alpha and overall clip opacity separate.

Text stroke lives directly in `def`: `text-stroke-width: 2` and
`text-stroke-color-red/green/blue/alpha`. The tested green `(20,160,80)` saves
normalized channels approximately `0.0784313725490196`, `0.627450980392157`,
`0.313725490196078`; half stroke opacity saves alpha `0.5`.
Horizontal spacing uses the rich `kerning` entry, while vertical spacing uses
`def["line-spacing"]`. A slider request of 5 clamps to 3 in this build;
1.2 and 0 have separate saved/rendered cases.

The native size combo can display an uncommitted value: setting its text to 48
and tabbing away left the slider and saved rich size at 64. Setting the observed
size slider committed 48. Verify the saved payload after UI edits; the displayed
field alone is insufficient evidence.

Rendered layout also depends on the retained box and fit behavior. Arial 64
wraps the Unicode phrase to two lines, while the 48-point case fits one line.
Kerning 2 spreads characters and causes wrapping. Changing line spacing changes
fitting and wrapping, including shrinking at spacing 3. The explicit multiline
string renders with different fitting at spacing 1.2 and 0. A stored font size
does not promise a fixed rendered glyph size in a constrained text box.

## Typography verification

Twenty-three actual native constructor captures supply a 184-second sequence.
Each eight-second background slot contains a five-second group with its child
at local zero. Storage-order IDs and both integer bindings are assigned together.
Strict native resave comparison permits the demonstrated rich-property ordering
and the existing three bookkeeping fields; it preserves all other group/child
payload, source bytes, defaults, timing and audio.

Native save/close/reopen and independent exports reproduce complete decoded
video and audio exactly. All 46 actual native frames were inspected in eight
contacts beside two repeated background controls: one visible text frame and
one after the group ends for every case. They verify Unicode text, font/style
edits, all six alignment choices, color, whole-callout opacity, stroke, spacing,
multiline layout and disappearance. Raw community schema and the existing
exact-build profile pass without corrections. Nine fixed typography tests refuse
range, binding, default-font, audio and opaque-payload loss.

Repository evidence is `build/native-verification/quick-text-sequence-comparison.json`,
the hash-bound `quick-properties-*-native.json` and controls, and tested
`quick_text_contract.py`. Font names and native rendered behavior are established;
the physical font file selected by the renderer is a separate dependency check.
The separate two-text lifecycle below establishes font-theme application and
text linking. The [media contract](media-quick-properties.md) covers AV replacement.

## Two-text constructor and font themes

A second native fixture groups two Basic text boxes on separate nested tracks,
at local zero with vertical translations +88 and −88. Its visible bounds are
376×352. The native automatic property order is Text bound to child 7, Callout
bound to child 7, then Text bound to child 8. The second appearance is **not**
implicitly bound to the first appearance entry; it remains in Available Properties.

Renaming these text controls to Heading and Subheading and saving the Quick
Property Editor materializes five rich properties on both children:
`fontName`, `fontSize`, `fontWeight`, `kerning`, `fgColor`. The default names
remain Montserrat, with size 64, weight 400, tracking 0 and color
`(46,59,68,255)`. `First → Text` uses UTF-8 bytes 0–14 and
`Second → Text` uses bytes 0–15. This native path omits the three explicit
italic/underline/strike entries observed in the direct typography path. Do not
require eight entries everywhere or inject omitted properties into a saved run.
The unique five-property set has its own observed order-permutation allowance;
all entry fields and unfamiliar/duplicate/mixed sets remain under comparison.

The Text row has separate font-family and font-color theme controls:

| Native choice | Saved mapping | Synthetic resource |
| --- | --- | --- |
| Font 1 | `themeMappings["font-family"]: "font-1"` | Arial |
| Font 2 | `themeMappings["font-family"]: "font-2"` | Georgia |

Before theme application, adding these mappings preserves the concrete font
names and colors. Applying the synthetic theme stores its ID on the Group and
writes rich `fontName` and `fgColor` on each bound child. The original `def.font`
and child theme metadata remain unchanged. Text colors use the same five theme
resource names as the fill table above, under the **`font-color`** mapping key.
All five have native saved and rendered cases.

Application affects only exposed/mapped properties. Here both text entries
map to white Foreground, but only the first appearance maps to dark Background 1
and blue Accent 1 outline. The second box remains white: its white text has no
contrast until a later text-color or appearance mapping changes it. Check actual
mapping coverage and rendered contrast; a valid text payload can be invisible.

## Linked text edits and re-addition

The editor offers **Link with item above** for adjacent compatible Text entries.
Removing the intervening Callout appearance entry makes the two texts adjacent
and retains the child's concrete fill/outline. Linking produces one type-0 entry
named Heading with integer `objects: [7,8]`. In this native specimen:

- The first label and **first text value** win. Both children become `First → Text`.
- The second entry's font mapping wins. Both rich fonts become Georgia.
- The selected Group theme ID and the hidden appearance's concrete colors remain.

Retain the original separate strings when they must survive a later unlink.
Unlink does not restore them. A linked edit to `Together → Go` writes both
child strings and all five ranges to UTF-8 bytes 0–15. Switching the linked
font mapping to Font 1 changes both to Arial; changing `font-color` changes both
rich colors. Geometry, default fonts, source/audio and the hidden appearance
remain unchanged.

Unlink creates two one-child Text entries, both named Heading and inheriting
the current mappings. Both retain the shared text/font/color. Editing the first
to `Only First → Go` changes only that child and its range ends to 17.
Removing the second Quick Property retains its text and styling.

Re-adding it from Available Properties creates `type: 0`, `name: "Text"`,
`objects: [8]`, with **no `themeMappings` field**. The child retains its current
Arial/orange rich values. Remapping the first to Font 2 changes only the first
child to Georgia. Editing the re-added second to `Only Second → Go` changes
only its string and range ends to 18. A later Foreground mapping on the first
changes only its text to white; the unmapped second stays orange.

Adding the second Callout appearance from Available Properties creates a
separate type-1 Callout entry bound to child 8, also without mappings. Its
existing fill/outline remain. Assigning Background 2 to its fill and Accent 2
to its outline creates those mapping keys and updates only that child's concrete
definition colors. The first callout's appearance stays independent.

## Linked text verification and dependencies

Twenty-three native constructor captures supply another 184-second sequence.
Its native save/close/reopen and independent exports reproduce complete decoded
video/audio exactly. All 46 native visible/post-end frames are inspected beside
two repeated background controls. They show both font resources, linked and
independent text edits, five color states, retained styling through unlink/remove/
re-add, independent remapping, and the second appearance's fill/outline changes.
The expected white-on-white and matching dark-on-dark cases are recorded
explicitly; later contrasting cases show the retained text. All groups disappear
at the sampled 6.5-second point.

Strict checks preserve complete group/child payload, default fonts, timing,
source bytes and audio, and remap every integer binding with the 138 stored clip
nodes. The native unique five-property ordering is the only additional comparison
allowance. Raw community schema and the existing exact-build profile pass
without additions. Ten fixed tests cover these constructor/editing contracts;
four filesystem lifecycle tests protect isolated theme restoration and cleanup.

The synthetic theme definition and logo are hash-bound during application and
render verification, then recoverably archived after normal Quit. Preexisting
user theme files remain byte-identical. Restore those exact dependencies before
repeating the theme tests; source-bin hashes do not establish theme or physical
font-file closure. Repository evidence is
`build/native-verification/quick-text-pair-sequence-comparison.json`, its native
captures and controls, tested `quick_text_pair_contract.py`, and the separate
`quick-text-pair-theme-restoration.json` / cleanup receipts. The separate
[media contract](media-quick-properties.md) covers AV/image replacement, applied
Logo lifecycle, linked AV/mixed image/AV edits, unmapped-second relink mapping
loss, trimmed/styled replacement with source-offset and audio-gain changes,
short/portrait/wide fitting and duration restoration, and the type-2 wrapper/image binding.
