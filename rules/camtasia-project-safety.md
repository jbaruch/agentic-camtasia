---
alwaysApply: true
description: Ownership and preservation when working with Camtasia projects
---

# Camtasia Project Safety

## Scope

- Apply these directives to Camtasia project work only.
- Treat `.cmproj` as a bundle and `.tscproj` as the project document.
- Preserve the project format version and authoring-client identity.

## Ownership

- Before Library operations, read `skills/camtasia-project/references/library.md`.
- Read an open project for inspection; require a saved, closed project before disk mutation.
- A nonempty `~project.tscproj` indicates a possible live edit or recovery state; never delete it to unlock writes.
- An empty recovery file does not establish that a project is closed.
- Use `skills/camtasia-project/scripts/project.py apply` for existing-project JSON replacement.
- Keep the original bytes in a backup and reject a changed baseline.

## Preservation

- Change only the requested feature and its dependent references.
- Preserve unknown keys, effect ordering, opaque effect metadata, bundle companions, and original recordings.
- Protect narration and its source entries during visual passes.
- Keep a new project in a separate bundle built from a working template of the target editor version.
- Do not copy private recordings or absolute personal paths into reusable plugin examples.
