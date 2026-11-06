# Independent theme duplication

This native workflow was exercised in the English UI of Camtasia Mac 2026.2.4,
project format `10.0`, with `.tsctheme` version `0.0.1`. It preserves the source
theme's identity and gives the copy an independent logo resource. It uses Theme
Manager; no theme-duplication CLI or complete official theme schema is asserted.
The [theme reference](advanced-features.md#themes) owns application, package,
missing-theme and preexisting-file normalization contracts.

## UUID and label behavior

In both the Default and an owned custom-theme probe, **Duplicate** produced a
new UUID with the source's previous English label. The UUID that existed before
duplication received the entered label. This occurred with both accessibility
value entry and typed text. Selecting a label alone can therefore target the
source UUID. Read the definition's `id` and UUID-named file after each operation.

The verified sequence uses a temporary label, then two native renames:

| Definition | Before Duplicate | After Duplicate | After both renames |
| --- | --- | --- | --- |
| Original UUID A | Source | Temporary | Source |
| New UUID B | Absent | Source | Copy |

The original theme's logo path stays on A. B receives a native copy in another
resource directory, retaining the filename and initial bytes. The observed
files have different inodes, not merely different path strings. The new
definition initially has an `en-US` name; a native save materializes the empty
locale entry. The source's locale labels survive the restoration sequence.
Other editor builds and UI locales need their own identity readback.

## Native procedure

1. Save and close affected projects. Retain the source definition's exact
   bytes, UUID, locale names and logo bytes/path. Record other installed theme
   files under `~/Library/Application Support/TechSmith/Camtasia/Themes` before
   opening Theme Manager; its Save can normalize preexisting files.
2. In **Camtasia → Manage Themes**, select the source and choose the gear menu's
   **Duplicate**. Enter a unique temporary label, distinct from the desired
   copy name, and confirm. Verify the actual saved UUID/label pairing against
   the table above before continuing.
3. Select the source's old label, now attached to new UUID B. Choose **Rename**
   and enter the desired copy name. Read back B's file and ID.
4. Select the temporary label, attached to original UUID A. **Rename** it back
   to its original name. Save the manager. Duplicate and Rename already produce
   filesystem writes before this Save; retain the protected source bytes until
   the whole operation is verified.
5. Compare the source's entire definition and logo against the protected
   originals. Check the copy's UUID, label, resource path, bytes and independent
   file identity. Investigate any source difference; use the existing theme
   reference's guarded restoration procedure for demonstrated normalization
   after normal Quit. Never overwrite an unrelated change.
6. Select B by its verified name/UUID and edit its colors, fonts or logo. Save
   and recheck A's definition and resource bytes. Font resources store names;
   they do not create independent physical font files.
7. Apply A and B to separate native controls using their explicit Quick Property
   mappings. Verify `metadata.AppliedThemeId`, concrete values and logo source
   references. Follow the [native verification procedure](native-verification.md#native-adapter-procedure)
   through save, close/reopen and independent exports. Keep project styling and
   dependencies under comparison, including after cleanup of disposable themes.

For binding shapes and theme coverage, use the
[text/color contracts](quick-properties.md) and
[media Logo contract](media-quick-properties.md#logo-mapping-application-and-images).
Do not infer ownership from a displayed name, the preview callout, or matching
logo basenames.

## Native verification

The owned source has four colors, one font and one synthetic PNG logo. After
the rename sequence, its bytes are identical to its pre-duplication native save.
The copy differs only at UUID, English label and logo path; all other definition
values, resource descriptors and tags remain equal. Two separate logo paths
and inodes initially contain identical bytes.

Native edits change only the copy's Accent 1 from `#FF739922` to `#FFE05020`
and Font 1 from Montserrat to Arial. The source definition stays byte-identical.
After normal Quit, a controlled change to the copy's PNG changes that resource
alone; the source PNG remains unchanged. This file-level logo edit is distinct
from the native color/font edits.

Two four-second Groups apply the source and edited copy in one eight-second
project. Each retains its own theme UUID. Native application writes the mapped
fill and rich font override, while the Callout's default font remains intact.
It imports each logo into a separate bundled source with matching bytes. The
copy's cyan logo and orange/Arial treatment remain distinct from the source's
quadrant logo and green/Montserrat treatment.

After normal Quit, both owned definitions and their installed logo resources
are removed and the preexisting user theme inventory/bytes are restored. A fresh
process reopens and saves the project with both theme files absent. Its complete
payload remains equal except the command counter; the selector shows
**Select Theme...** while retaining the saved UUIDs and concrete styling.

Two native MP4s have identical complete decoded video and audio. All four
sampled frames show the expected independent color, typography and logo states;
eight both-channel audio windows retain the background source tone. All three
bundled source hashes remain unchanged. Structural and exact-build schema checks
pass; the two raw Callout-metadata omissions remain separately reported under
the existing profile correction. Physical font-file identity, cross-host font
availability and deletion behavior for copied/shared resources remain outside
this probe. Completed disposable projects, movies, images and diagnostics are
deleted after these findings are incorporated.
