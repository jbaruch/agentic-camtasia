# Physical fonts and licensed handoffs

Use the [font helper contract](helper.md#font-resource-handoff) to inspect actual
font files and prepare a separate handoff. A stored family or PostScript name
does not identify the file Camtasia resolves. Default/reset names can remain in
a project alongside effective rich-text names. RTF, SVG, Lottie and installation
resources can carry additional font dependencies. Keep their existing contracts;
this handoff does not establish complete font closure or glyph coverage.

Select the intended physical versions and styles from their inspected metadata.
Preserve complete font files, their original basenames and the applicable
copyright/license notices. Confirm redistribution rights for every face in a
collection, including unselected faces. Font embedding flags are metadata, not
a standalone license. The handoff is separate from the `.cmproj`; merely placing
it beside a project does not install its fonts.

An installed consumer can run the helper with `uv run --with` and the pinned
requirement named by the helper contract, followed by `python -B`, the installed
helper path and its command arguments. This keeps optional parser packages out of
the installed skill tree. Use the repository's `fonts` extra when working from
its source checkout.

## Target-editor verification

Record the exact editor build, project hash and selected physical font hashes.
Use disposable project copies with visible text and distinct intended styles.
Inventory the target's fonts before adding anything; preserve existing user fonts.
Request the required authorization before installation or activation changes.

First open, save and render a font-absent control. Record fallback appearance,
native warnings and any stored declaration changes. Quit normally and confirm the
editor process exits before changing the test font state. A native family label
or a generic font matcher's result alone does not prove the resolved physical face.

After authorized installation, verify the installed file identities and open the
unchanged intended input in a fresh editor. Check Regular/Bold or other selected
styles, save, close/reopen and export. Inspect the text, word highlighting and
line bounds; compare decoded video/audio with appropriate native controls.

Move the staged handoff and disposable project to a new location. Withhold their
earlier disposable source paths while keeping protected originals untouched.
Verify the relocated handoff before authorized activation from those files.
Use fresh native processes for the absent/present checks; compare the relocated
and reopened outputs with the established font-present controls. Restore earlier
paths and the initial font state, verify their identities, then remove completed
disposable inputs and outputs under the working-storage policy.

## Current native observation

On Mac Camtasia 2026.2.5 (2026.136), a four-second format-10 dynamic-caption
project requesting Averia Libre opens and saves while that family is absent from
the system font catalog. The save retains the requested font declarations and
changes only the project thumbnail. Native MP4 output contains the expected
caption words and active-word highlighting without installing the selected files, with 120
1432×1080 frames at 30 fps and four seconds of audio. No missing-font repair
dialog appears in this specimen. Retained declarations and successful rendering
do not establish that the intended physical font was used.

The helper stages the unmodified Averia Libre Regular and Bold files with their
OFL notice; repeated staging is a no-op and independent verification matches
both physical face identities. Relocating the handoff with its earlier output
and original font paths absent still passes physical metadata/hash verification.
Restoring those paths retains every input hash. Direct and nested filesystem
case aliases refuse without changing the input tree.
Font Book's read-only validation passes both
files. Installation, relocated activation and font-present native comparison
remain pending; this observation does not complete native font portability.
