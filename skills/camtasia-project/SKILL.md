---
name: camtasia-project
description: Inspect, create, edit, package, or validate Camtasia .cmproj and .tscproj projects. Use for timeline cuts, source relinking, portable bundles, source-file manifests, zooms, effects, annotations, captions, audio, groups, hotspots, quizzes, or project JSON repairs.
---

# Camtasia Project

Process steps in order. Do not skip ahead.

Resolve this loaded skill's directory to absolute `camtasia_skill_root`.
Use that root for every helper command; project paths belong to the consumer.
Python 3.11+ is required. The helper uses only the standard library.
Use `python3 -B` for helpers and task scripts that import their modules.

## Step 1 — Inspect the project

```bash
python3 -B "{camtasia_skill_root}/scripts/project.py" inspect "<project.cmproj-or-file.tscproj>"
```

Stdout includes `sha256`, `formatVersion`, `authoringClient`, `tracks`,
`clipTypes`, `effects`, `assetReferences`, and a `validation` report. Keep the
hash as the edit baseline. Read [the format map](references/project-format.md) and only the
relevant sections of [the feature map](references/features.md).
For captions or source transcription, also read [captions](references/captions.md).
For recording streams, color conversion, or portable/source-file closure checks, read [media](references/media.md).
For recorded cursors, keystrokes, or window highlighting, read [cursors](references/cursors.md).
For local video formats, transparency, or batch export, read [delivery](references/delivery.md).
For cleanup, pitch, dynamics, or audio-only delivery, read [audio](references/audio.md).
For schema compatibility, read [native verification](references/native-verification.md).
For another Mac build or a conversion prompt, read [Mac versions](references/mac-versions.md).
Proceed immediately to Step 2.

## Step 2 — Define the change

- Identify clips and sources by ID and semantic role, not fixed lane numbers.
- Record requested behavior, affected time windows, and tracks to preserve.
- Read [the helper contract](references/helper.md) before using preservation or continuity selectors.
- For an unfamiliar serialized feature, invoke `Skill(skill: "camtasia-feature")` and return here with its findings.
- For a new project, copy a suitable saved template and its required bundle companions to a new output bundle; keep its format identity.

Proceed immediately to Step 3.

## Step 3 — Stage the candidate

Use an existing candidate helper from [the helper contract](references/helper.md)
when its verified scope covers the change. Otherwise write a task-specific
transformation script. Stage a separate candidate JSON document. Preserve
unrelated data and the original project. Resolve media relative
to the destination document, not the staging file. Use rational arithmetic for
timing; native trims, keyframes, and effects keep the project editable.

```bash
python3 -B "{camtasia_skill_root}/scripts/project.py" validate "<candidate.json>" --media-root "<destination-project-directory>"
python3 -B "{camtasia_skill_root}/scripts/project.py" diff "<original-project>" "<candidate.json>"
```

Validation emits `ok`, `errors`, `warnings`, and `limits`; diff emits changed
JSON pointers with bounded previews. Fix errors; investigate warnings relevant
to the change. Proceed immediately to Step 4.

## Step 4 — Apply the candidate

Establish that the target is saved and closed in Camtasia. If closure requires
the user, keep the candidate ready and request only that missing action.
The helper's live process check supports macOS; other platforms can inspect,
validate, and stage candidates but must use the editor to save final changes.

```bash
python3 -B "{camtasia_skill_root}/scripts/project.py" apply "<target-project>" "<candidate.json>" --expected-sha256 "<baseline-hash>" --preserve-track "<scene-index>:<track-index>"
```

Repeat `--preserve-track` for each unchanged lane; omit it when no whole lane
can remain unchanged. Stdout reports `changed`, `sha256`, `backup`, and
`validation`. Apply validates before writing, preserves the original bytes,
and replaces only the project JSON. A no-op creates no backup.
Proceed immediately to Step 5.

## Step 5 — Verify the result

Re-run inspection. Follow the loaded Camtasia Validation rule's editor checks.
On macOS, start the matching authoring build and close its other documents.
Run the backed-up native save/reopen adapter:

```bash
python3 -B "{camtasia_skill_root}/scripts/native_roundtrip.py" "<candidate-project>"
```

It returns backup/hash evidence and separate `saveReopen` and `renderVerified`
fields. Continue through native export and pixel/audio inspection; save success
does not establish rendering support. Check unsupported-feature dialogs.
Use app-scoped UI tools or the verified macOS automation procedure in the
native verification reference. If access is missing, prepare the candidate and
request the required access while continuing independent checks. Do not treat
an outstanding verification item as a completed edit. Include project/backup
paths, changes, schema results, native checks, and rendered evidence. Finish here.

All commands emit JSON on stdout. Operational or validation failures exit 1;
invalid CLI usage exits 2. Diagnostics go to stderr. The full contract and
validation boundaries are in `references/helper.md`.
