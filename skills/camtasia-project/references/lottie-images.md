# Lottie image inspection and embedding

Use this workflow when a Lottie source contains image assets. Read
[the native Lottie contract](lottie.md#internal-images-glyphs-and-project-relocation)
for the exercised Mac 2026.2.4 forms. An intact source-bin JSON file does not
establish that its internal image or font dependencies are portable.

## Helper contract

`skills/camtasia-project/scripts/lottie_images.py` owns image recognition, PNG
checks and preservation in its module docstring and `inventory`, `embed_png`
and `read_file` contracts.
It reads a standalone Lottie JSON source, never a Camtasia project. Select an
animation-local image asset ID from inspection and provide the intended PNG
explicitly. Stored filenames, directories, URLs and font declarations are
reported without opening them. No network fetch or installation-resource copy
occurs.

```bash
python3 -B "{camtasia_skill_root}/scripts/lottie_images.py" inspect "<animation.json>"
python3 -B "{camtasia_skill_root}/scripts/lottie_images.py" embed "<animation.json>" --asset-id "<image-id>" --image "<selected.png>" --output "<embedded-candidate.json>"
python3 -B "{camtasia_skill_root}/scripts/lottie_images.py" inspect "<embedded-candidate.json>" --require-embedded
```

Stdout uses schema 1, owner `camtasia-lottie-images`, and includes
`sourceSha256`, `images`, unresolved/malformed image references, raw
`fontDeclarations`, `embeddedGlyphCount`, `imageAssetsEmbedded`, and
`nativeVerified: false`. Each image reports its animation-local identity,
reference kind, dimensions, embedding status and available PNG byte hash.
Dimensions and reference fields are null when their input is absent or
unusable; unsupported forms retain the valid values that can be inspected.
`missingImageAssetIds` names absent asset IDs, independently of whether an
existing asset is an eligible image. Present unsupported assets remain
unhandled and cannot satisfy an image layer reference or the image gate.
Embedded data URLs are omitted from the filename field. Embed also returns
`assetId`, `pngSha256`, `candidateSha256`, `changed`, `written` and `output`.
The helper owns this snapshot; readers must recheck input hashes before use.
No continuity state is read or migrated.

`unhandledAssetIds` also lists other file assets outside image processing,
including sound and data references. Those entries do not make the image-only
gate fail. They remain unresolved resources; the gate never claims their
portability. The [Lottie schema](https://lottiefiles.github.io/lottie-docs/schema/)
distinguishes image dimensions/slots from general file-asset path fields.
Image sequences, slotted images and other typed image forms remain unhandled, fail the
image-only gate, and refuse single-PNG replacement.

The candidate preserves animation geometry, clocks, layers, colors, fonts,
glyphs, unfamiliar payload and other assets. Only the selected image's native
embedding fields change. PNG physical dimensions must match the asset.
Original source and image bytes remain unchanged. The output is exclusive;
an identical rerun is a no-op, while a different occupied output, source alias
or output symlink refuses. Hard links to the source also refuse. JSON decimal
clocks and unfamiliar numeric values retain their exact values without a binary
float conversion. Exit codes are 0 for inspection/staging, 1 for a
refusal or unmet `--require-embedded`, and 2 for argument syntax. Errors are JSON
on stderr. A successful embed can still report other unresolved images.
File/parser errors include operation-specific `action` guidance. Source and
PNG inputs must be stable regular files; special files and changed snapshots
refuse before staging.

`imageAssetsEmbedded` covers the inspected image asset/reference table only.
PNG checks cover the container without decoding pixels or certifying every PNG
feature. Font declarations do not identify the physical font selected by the
renderer; glyph counts do not prove text coverage. Expressions, plugins,
slots, other render resources and full project closure remain separate checks.

## Stage a portable project

1. Preserve the original animation, selected PNG and project bundle. Inspect
   each relevant source and stage explicit embeddings to separate files.
2. Create a new output bundle with the existing required companions. Import the
   candidate through the matching native editor to obtain its source and clip
   payload. For a verified template-derived replacement, retain the same-build
   source/clip constructor, clocks and opaque metadata; use the ordinary
   [candidate and guarded apply workflow](helper.md). Recheck source hashes.
3. Run the project source manifest separately. Inspect image assets in every
   relevant bundled Lottie JSON; the primary manifest does not inspect them.
4. Save, close, reopen in a fresh matching process and export. Inspect actual
   pixels/audio beside an independent native control. Preserve source hashes.
5. Close the editor and physically move the owned test bundle to a new path.
   Make the original image location and old bundle path unavailable without
   deleting consumer data. Reopen/export in a fresh process and repeat the
   inspection. Restore withheld inputs after the test.

Do not claim portable rendering from an embedded flag, file-copy receipt,
source manifest or successful save alone. General project packing, automatic
font/glyph conversion and arbitrary dependency resolution are outside this
helper.

## Native helper acceptance

A synthetic 64×64 quadrant PNG supplies a linked four-second Lottie, the
helper-produced embedded candidate and a direct native PNG control at matching
256×256 geometry. The Lottie source retains 640×360 composition dimensions,
30 fps and frames `[0,120)`; only the selected asset's embedding fields change.
The native source and `VMFile` constructor come from a real editor import;
the embedded instance uses that constructor with its separately bundled JSON.
The three controls occupy a twelve-second sequence over repeated native AV.

Independent native save/reopen/export pairs cover resources present and the
physically moved bundle with its original image directory withheld. Each pair
repeats complete decoded video/audio exactly and retains byte-identical native
project saves. The linked image disappears after relocation; the embedded
image and direct PNG remain visible. Actual exported frames are inspected at
both interior times per cell. Source-bin JSON and media hashes remain intact.
The pinned raw community schema and exact-build profile are checked separately.

At one and three seconds inside each cell, the embedded and direct-PNG frames
remain byte-identical before/after relocation. Embedded versus direct-PNG
frames differ by mean absolute RGB 0.203 and maximum 64 over the whole frame;
visible differences concentrate on scaled boundaries. They are independent
native controls, not a claim of identical raster interpolation. Audio remains
identical across all four exports. All five source-file hashes survive.

These observations exercise the helper's PNG output on Mac 2026.2.4/format 10.
They do not establish all PNG encodings, Lottie render features or other builds.
Deterministic fixtures and preservation/refusal cases live in
`tests/test_lottie_images.py`; disposable native media are excluded and removed
after incorporation.
