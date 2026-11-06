# SVG image inspection and embedding

Use this workflow for image references inside an SVG source. Read
[the native SVG contract](media.md#svg-image-and-font-dependencies) for the
exercised Mac 2026.2.4 forms. Source-bin file availability does not establish
internal raster, font or stylesheet closure.

## Helper contract

`skills/camtasia-project/scripts/svg_images.py` owns parsing, selection,
byte preservation and refusal behavior in its module docstring, `Document`,
`eligible`, `embed_png` and `stage` contracts. It reads a standalone SVG,
not a Camtasia project. It never follows stored references, fetches remote
resources, executes SVG content or copies fonts/installation resources.

```bash
python3 -B "{camtasia_skill_root}/scripts/svg_images.py" inspect "<source.svg>"
python3 -B "{camtasia_skill_root}/scripts/svg_images.py" embed "<source.svg>" --expected-sha256 "<source-hash>" --image-id "<id-from-inspection>" --image "<selected.png>" --output "<candidate.svg>"
python3 -B "{camtasia_skill_root}/scripts/svg_images.py" embed "<source.svg>" --expected-sha256 "<source-hash>" --image-index N --image "<selected.png>" --output "<candidate.svg>"
python3 -B "{camtasia_skill_root}/scripts/svg_images.py" inspect "<candidate.svg>" --require-embedded
```

Select by one existing image ID or by the zero-based SVG image index from
inspection. These are animation/source identities, separate from Camtasia
source and clip IDs. The input hash must match the inspected bytes. A changed
source requires a new inspection. The explicitly selected PNG is the intended
replacement content; the helper does not prove that an external image has
equal pixels or equal bytes.

Only the selected image's existing reference value bytes change. The surrounding
SVG bytes remain intact, including namespaces, prefixes, attribute order and
quoting, comments, styles, numeric text, geometry, other elements and references.
Equivalent `href`/`xlink:href` pairs change together. Conflicting references,
missing references, ambiguous ownership and unverified dynamic/active forms
refuse. Viewport size and aspect fitting remain separate from the PNG's physical
pixel dimensions. Original source and PNG files remain unchanged.

Active-content refusals include SVG scripts and handlers, unqualified `on*`
attributes, XML Events listeners and attributes in the XML Events namespace.
Namespace aliases do not change this guard; unrelated namespace metadata remains
opaque.

Parsing uses Expat's namespace and ordered-attribute information to locate
values in UTF-8 source bytes; it does not reserialize an XML tree. XML DTDs,
custom entities and unsupported encodings require a separate reviewed source
conversion. This parser is not a complete SVG validator. Unknown render features
remain subject to native verification.

Stdout uses schema 1, owner `camtasia-svg-images`, `sourceSha256`, `images`,
`duplicateIds`, active/dynamic element indices, `otherReferences`, raw font/style
declarations and `nativeVerified: false`. Image rows report document-order
`imageIndex`, `elementIndex`, `id`/`xmlId`, inspected reference attributes/kinds,
embedding status and available PNG dimensions/hash/size. Unavailable PNG fields
are null; rejected images include a reason. Data URL payloads are omitted from
the returned reference value. Embed adds selected index, PNG/candidate hashes,
`changed`, `written` and `output`. This helper owns the snapshot; readers recheck
source and candidate hashes before use. No continuity state is read or migrated.

`imageAssetsEmbedded` covers static SVG image references only. Zero SVG images
is a vacuous image-only result. Other resource references, stylesheet content,
physical fonts and glyph coverage remain unresolved. A positive image gate
never certifies full SVG/project portability, native support or rendering.
PNG checks use the existing container-only contract without pixel decoding.

Candidate creation is exclusive. An identical rerun is a no-op; source aliases,
output symlinks and different occupied files refuse. Inputs must be stable
regular files. Exit 0 means successful inspection/staging, 1 means refusal or
an unmet image gate, and 2 means argument syntax. Failures emit JSON diagnostics
and action guidance on stderr. An unmet gate retains its stdout inventory.
Staging may succeed while other images remain external; inspect the report.

## Project workflow

1. Preserve the source SVG, intended PNG and original project. Inspect and hash
   each selected image reference, then stage a separate SVG candidate.
2. Create a new project bundle with its required companions. Import the candidate
   through the matching editor to obtain its native source/clip constructor.
   A verified same-build template-derived replacement retains the source track,
   still hold, source identity and opaque metadata through the ordinary
   [candidate and guarded apply workflow](helper.md). Recheck all source hashes.
3. Save and reopen in a fresh process, export, and inspect the affected image
   beside an independent native control. Retain audio and unrelated source data.
4. Close the editor and physically move the owned test bundle. Make its old path
   and original image location unavailable, then reopen/export in a fresh process.
   Compare actual picture/audio and restore withheld inputs afterward.

The primary source manifest remains a separate check. Fonts, CSS, nonimage
references, geometry/animation semantics and general bundle packing keep their
own verification obligations. A file-copy receipt or successful save is not
rendered closure.

## Native helper acceptance

A synthetic 64×64 quadrant PNG supplies a sixteen-second control sequence:
linked SVG, helper-produced embedded XLink SVG, helper-produced plain `href`
SVG, and a direct native PNG at matching 256×256 geometry. All SVGs retain the
same 640×360 viewport. A real native SVG import supplies the source and `IMFile`
constructor; the embedded sources reuse it with their separately bundled bytes.
Native source edit rate 600/range `[0,1]` remains distinct from four-second project
holds and `mediaDuration: 1`.

Independent native save/reopen/export pairs cover resources present and the
physically moved bundle with the original PNG withheld. The linked image is
visible initially and absent after the move. Both embedded reference forms and
the direct PNG remain visible. Two interior frames per cell per phase are
inspected. Pairwise complete decoded video/audio, native save identity and source
hashes are checked separately from cross-constructor pixel differences.

Both pairs repeat complete decoded video/audio exactly and retain byte-identical
native saves. Embedded XLink/plain-href frames are identical at both interior
samples; embedded/direct-PNG frames remain identical before/after relocation.
SVG versus direct-PNG output has mean absolute RGB difference 0.203 and maximum
64 over the whole sampled frame, concentrated on scaled boundaries. This is
visible agreement, not identical interpolation. Audio matches across all four
exports. All six source-file hashes and both raw/profile schema checks survive.

This evidence covers these Mac 2026.2.4/format-10 PNG forms, not all SVG features,
encodings, fonts or renderer builds. Deterministic fixtures and preservation,
selection, namespace, resource and refusal cases live in `tests/test_svg_images.py`.
Disposable native media are excluded and removed after incorporation.
