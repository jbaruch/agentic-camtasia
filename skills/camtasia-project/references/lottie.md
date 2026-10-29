# Lottie animation sources

Use this contract for Mac 2026.2.4, project format `10.0`. TechSmith supports
[importing Lottie JSON through File → Import → Media](https://support.techsmith.com/hc/en-us/articles/360060035772-Add-Lottie-Animations-to-Camtasia-Editor).
Import a new animation through the editor to obtain its source tracks and
dynamic properties; a `.json` extension alone does not identify a Lottie file.

## Source and clip ownership

The native test imports a self-contained 640×360 animation with two shape
layers, two fill colors, 30 fps, `ip: 0`, and `op: 120`. Its source file has
`v: "5.7.4"`; this is animation metadata, separate from project format 10.
The editor bundles identical JSON under `./media/<native-directory>/`.
Preserve the bundle companions and the original animation bytes.

The source-bin entry has a 640×360 rectangle and one visual source track:
`type: 0`, `editRate: 1000`, `range: [0,4000]`, `sampleRate: 30`, and
`bitDepth: 32`. The timeline instance is a `VMFile`, selects that source ID
and `trackNumber: 0`, and consumes four seconds. In this project, `start`,
`duration`, `mediaStart`, and `mediaDuration` use 705,600,000 ticks per second;
the duration is 2,822,400,000 ticks. Neither source milliseconds nor animation
frame numbers can be copied directly into clip timing.

This animation uses ordered position keyframes with `h: 1`. Lottie's
[property specification](https://lottie.github.io/lottie-spec/latest/specs/properties/)
defines `t` in frames and held values. Preserve those animation-local keys
inside the source JSON; Camtasia's clip placement supplies a separate clock.
The import allocates/remaps IDs natively. Recover actual IDs from the saved
document rather than assuming the specimen's allocation applies elsewhere.

## Per-clip dynamic colors

The source entry's `effectDef` declares `sourceFileType` with default `Lottie`
and two `Color` definitions, `Color000` and `Color001`, with RGBA defaults
`[1,0,0,1]` and `[0,1,1,1]`. Discover each imported source's actual definitions;
color counts, ordering, and names are not universal.

Each clip owns a `sourceEffect` node with `effectName: "SourceEffect"`,
`bypassed: false`, and an empty category. Its `parameters` contain
`sourceFileType: "Lottie"` and the `red`, `green`, `blue`, and `alpha`
components for each color, named for example `Color000-green`.
Keep this node separate from the clip's ordinary `effects` array.

On first import, color components are static double descriptors with
`defaultValue` and `interp: "linr"`; four zero geometry-crop parameters have
`interp: "eioe"`. A subsequent native reopen/save collapses precisely these
unanimated descriptors to equal bare numbers. This observation does not permit
flattening animated parameters or discarding extra descriptor fields.

Native RGB controls changed Color 1 from red to `#FF8800` and Color 2 from cyan
to `#8833FF`. The saved clip changes three component values:

| Parameter | Native saved value |
| --- | --- |
| `Color000-green` | `0.533333333333333` |
| `Color001-red` | `0.533333333333333` |
| `Color001-green` | `0.2` |

The clip also gains reset metadata:
`default-SourceEffect-Color000: "(255,0,0,255)"` and
`default-SourceEffect-Color001: "(0,255,255,255)"`.
Preserve that metadata, other components, unknown fields, source defaults, and
the bundled JSON. These doubles are not the binary32 values observed in some
other effect families. Native edits do not replace the source's fill colors.

Two consecutive four-second clips sharing one source retain independent
red/cyan and orange/purple settings. The second starts at four seconds while
its `mediaStart` remains zero, so its animation restarts locally. Cloning an
instance requires a new global clip ID and preservation of its complete source
effect and reset metadata; changing source defaults would affect a different
owner than the demonstrated per-instance edit.

## Native verification and dependencies

Two projects each have an independent native save/reopen/export pair. All
eight-second movies retain the background AV, and each pair reproduces complete
decoded video and audio exactly. Fifteen native frames were inspected beside
fifteen background frames. They show held left/center/right/center motion,
transparent compositing, disappearance at the four-second boundary, and the
second clip's independent colors and restarted motion. The original import path
was unavailable during the fresh-process baseline render. Both projects pass
the pinned raw community schema and exact-build profile without corrections.

The color-picker RGB and encoded RGB are distinct observations: orange
`[255,136,0]` measured approximately `[255,124,0]`, and purple `[136,51,255]`
measured approximately `[125,44,255]` in decoded interior patches. Retain output
color metadata and compare native reference renders when channel accuracy
matters. These fixtures establish visible recoloring, not transfer mathematics.
Small compression differences from a separate background-only export are
recorded independently from exact equality within each native reopen pair.

## Automatic group Quick Properties

Selecting the native animation and choosing **Edit → Group** creates a `Group`
with one child track. In this constructor the wrapper takes the former clip's
ID 7, the child receives ID 8, and the source remains ID 2. Keep those namespaces
separate: property bindings refer to the child media ID, not the source ID.
The child retains its complete payload apart from the allocated ID, including
its `sourceEffect`, source timing, and unknown metadata. The wrapper retains
four-second bounds and 640×360 `widthAttr`/`heightAttr` geometry.

The group's `attributes.assetProperties` automatically contains two entries:

```json
{
  "type": 1,
  "name": "Color 1",
  "objects": [{"media": 8, "property": "Color000"}],
  "themeMappings": {"fill": "background-1"}
}
```

The second uses `name: "Color 2"` and `property: "Color001"`, with the same
child ID and default mapping. Preserve the array order, object bindings, labels,
and mapping data when cloning groups; remap child references with child IDs.
The saved default `background-1` mapping does not apply a theme: the native
panel still shows **Select Theme...**, and the red/cyan child colors remain.

This grouped project has an independent native reopen/export pair. Its complete
decoded video/audio matches both its own rerender and the accepted ungrouped
output exactly. Four actual grouped frames were inspected beside four ungrouped
frames, including clip-end disappearance. Both automatic color properties remain
in the native saved group. The existing raw/profile schema accepts the group.

The subsequent [Quick Property editing contract](quick-properties.md) verifies
labels, all five theme slots, linked edits, unlink, remove/re-add, reorder and
direct color editing through fifteen native captures and an independent native
sequence pair. It records mapping precedence, absent mappings, and native
clip-ID reallocation separately from automatic group creation.

The initial shape file has `assets: []` and no image or font references.
The separate dependency cases below cover original images and glyphs. A
source-file manifest does not inspect Lottie-internal images, fonts, external
URLs, expressions, plugins, or arbitrary render features. Inspect those
dependencies and exercise them natively before claiming closure for another animation.
Other Quick Property types and group layouts require their own native
constructors; the demonstrated color bindings do not establish those operations.

Repository evidence: `build/native-verification/lottie-render-comparison.json`,
`lottie-group-comparison.json`,
the native import/recolor captures, source-isolation record, and tested contracts
in `lottie_native_contract.py` and `lottie_frame_contract.py`. Synthetic and
native verification media are not part of the distributed plugin.

## Internal images, glyphs and project relocation

Twelve additional four-second animations use the accepted same-build source
and `VMFile` constructor. They are template-derived sources, rather than twelve
new UI-import constructors. All retain 640×360 geometry, `fr: 30`, frames
`[0,120)`, source milliseconds `[0,4000]`, and separate project-tick intervals.
The original image is a four-quadrant PNG. The original custom font maps `A`
to a filled triangle; it is generated locally and never installed. Direct
vector shapes and embedded character outlines supply independent controls.

The primary [image-asset specification](https://lottie.github.io/lottie-spec/latest/specs/assets/)
defines `id`, `w`, `h`, filename/data URL `p`, path `u`, and embedded flag `e`.
Image layers use `ty: 2` and `refId` to select the asset; those identifiers are
animation-local, distinct from Camtasia source/clip IDs. The
[text format documentation](https://lottiefiles.github.io/lottie-docs/text/)
describes `fonts.list`, font names/families/styles, `fPath` and `origin`, plus
embedded `chars[].data.shapes`. These describe the input format; they do not
establish Camtasia rendering support.

Observed Mac 2026.2.4 output:

| Input | Native result |
| --- | --- |
| PNG in `p` as `data:image/png;base64,...`, `e: 1`, empty `u` | Visible with companions present, withheld, restored, and after an actual bundle move. |
| Bare PNG filename, `e: 0`, empty `u` | Absent even with matching PNG beside the JSON. |
| PNG filename and relative `u: "images/"` | Absent even with the matching subdirectory/file. |
| PNG filename and absolute filesystem directory in `u` | Visible while the original location exists; absent when withheld or moved. Restoring the original companion restores identical decoded output. |
| PNG filename and `file:///` directory in `u` | Absent in these loads, including while the PNG exists. |
| Embedded `chars` triangle glyph, matching family/style and `AAA` text document | Three filled triangles match the direct vector control and survive isolation/relocation. |
| Custom uninstalled font via relative `fPath`, file-URI `fPath`, or base64 TTF data URL, each `origin: 3` | None renders the custom triangle glyph. All show the same thin `AAA` lettering as the unavailable-family control. |
| `Arial` family or unavailable custom family, no `chars`/`fPath` | Both show that same lettering. Equal output does not identify which native fallback font was selected or prove that Arial was used. |

All font-reference controls retain visible colored vector quadrants and dark
backgrounds; this is distinct from a missing or wholly blank animation.
The custom TTF's character map, original triangle outline, advance and fixed
header dates have independent parser tests. These are finite input cases,
not a universal claim about all fonts, image formats or Lottie players.

The staged sources initially retain only the native `sourceFileType` definition
and per-clip selector. On native save, Camtasia reads their fills and materializes
color definitions and corresponding per-clip RGBA component values. These
fixtures produce six colors for vector/text sources and two for image sources;
raster pixels do not become individually editable colors. The first extracted
color is yellow; source order and defaults are checked against the actual save.
Do not copy another animation's palette or assume every source has two colors.
All other document payload is compared strictly, apart from the previously
observed thumbnail, command-count and source-modification bookkeeping.

Four independent native save/reopen/export pairs cover present, withheld,
restored and physically relocated resources. Each pair repeats all decoded
video/audio exactly. Ninety-six actual frames in eight contacts and 192
both-channel silence windows cover two times per animation per phase. The
restored streams equal the initial streams; moved streams equal the withheld
streams. All twelve JSON hashes, three companion hashes, 25 global IDs and
both raw/profile schemas remain checked without a profile addition.

The moved bundle contains all fifteen files, but the old absolute image path
is absent during rendering. The entire original bundle is then restored from
a verified full backup, with the native moved specimen retained. After that
restoration, the moved specimen can resolve the old location again; its retained
movies specifically document the earlier origin-absent state.

For portable output, embed required raster bytes and intended glyph outlines,
then check an actual relocated native render. Keeping matching companion files
or passing the primary source manifest alone does not prove rendered closure.
HTTP resource loading, expressions, plugins and other render constructs retain
their own requested-case checks. This contract does not establish physical
font closure for native Camtasia Callouts.

Repository evidence: `lottie-dependencies-*-comparison.json`, resource-operation
receipts and `lottie-dependencies-native-checks.json` under
`build/native-verification`; fixture, palette, isolation/move and render contracts
have deterministic tests. Generated fonts, images and native media are excluded
from the plugin distribution.
