# Staged source bundles

Use the [bundle helper contract](helper.md#source-bundle-staging) to inspect a
saved `.cmproj` and stage an independent source bundle. Review every source ID
and its content hash before selecting files for copying. Keep the original
closed throughout staging. The helper copies the complete bundle, including
opaque companion files and empty directories, and changes external source paths
to relative paths in the new bundle. It preserves project identity, source IDs,
streams, timing, effects, captions, reset data and unknown project values.

The result establishes source-bin file containment. Physical fonts and
application resources require separate licensed delivery; logical installation
selectors are retained unresolved. SVG/Lottie internal references retain their
[image](svg-images.md) and [animation](lottie-images.md) contracts. Bookmarks,
font resolution, installation assets and native rendering require target-editor
checks. A successful source report alone does not establish complete portability.

## Native relocation verification

The local check uses Mac 2026.2.5 (2026.136) with a format-10 project originally
saved by 2026.2.4. An eight-second native Group combines a moving screen recording
with its microphone audio, a second WAV source, closed captions and a shared
dynamic-caption display. The staging input references an external TREC through
a symlink and an external hard-linked WAV. It also contains ordinary original
media companions, opaque preferences/bookmarks, an added binary companion and
an empty companion directory.

Native Camtasia opens that externally linked input but refuses to save its
symlinked TREC. The input project remains byte-identical. A separate control
using the existing ordinary relative source files saves and renders; only its
native authoring version changes to 2026.2.5. This is an observed save refusal,
not a claim that every source link fails or a general Camtasia recovery fix.

The staging command copies both selected source files into independent regular
files and preserves every companion's bytes. An identical rerun is a no-op.
After quitting the control editor and confirming its exit, the test withholds
the disposable input, control and external-media paths and moves the staged
bundle. A fresh exact-build editor opens and saves that relocated bundle without
missing-media or repair prompts. Positive native file handles point to both
selected media files inside the relocated bundle. Their hashes match the inputs;
no staged file is a symlink or shares a hard link.

Three eight-second 1432×1080, 30-fps exports cover the ordinary-file control,
relocated bundle and its save/close/reopen output. All 720 decoded frames and
complete decoded audio streams match; both audio halves contain speech. Six
inspected frames retain the moving recording, both source sections, closed
captions and dynamic word highlighting. The native first save updates authoring
version, source modification timestamps and source-metadata filename prefixes;
all other project values remain. The next reopen's project bytes are identical.
Companion bytes and the empty directory remain unchanged. The two saved controls
each have eight raw upstream schema errors, zero corrected errors and zero native
compatibility errors under the exact-build profile. Earlier disposable paths
are restored and hash-checked before cleanup; canonical inputs remain unchanged.

Repeat this isolation procedure for the actual requested bundle and target
installation. This specimen establishes source-copy closure on one host; it does
not establish cross-host fonts, vendor-asset redistribution, archive transport,
extended attributes or resource-fork closure.
