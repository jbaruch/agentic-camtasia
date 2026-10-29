---
name: camtasia-feature
description: Research a Camtasia feature's serialized JSON, compare before/after projects, or extend support for transitions, behaviors, mattes, cursor effects, templates, markers, quizzes, and other unfamiliar project structures.
---

# Camtasia Feature

Process steps in order. Do not skip ahead.

Resolve the loaded `skills/camtasia-project/SKILL.md` directory to absolute
`camtasia_skill_root`. ACR rebases that package reference to the installed skill.

## Step 1 — Locate evidence

Read `skills/camtasia-project/references/features.md` and
`skills/camtasia-project/references/sources.md`. Match target editor build,
OS, and project format. Prefer official behavior docs plus a project saved by
that editor. Follow linked community source for serialization clues. Never
claim that a community schema is the full official format. Read
`skills/camtasia-project/references/native-verification.md` for the tested
profile, schema omissions, and native rejection cases. Proceed immediately
to Step 2.

## Step 2 — Isolate the feature

Use two copies of a small saved project: before the feature and after one
feature change. Keep both outside temporary recording storage. Existing sample
projects can supply this pair; when no sample exists, prepare the probe and ask
the user to make the specific editor change if UI access is unavailable.

```bash
python3 -B "{camtasia_skill_root}/scripts/project.py" diff "<before>" "<after>"
python3 -B "{camtasia_skill_root}/scripts/project.py" inspect "<after>"
```

Diff returns JSON pointer changes and bounded previews. Inspect returns the
feature inventory and validation findings. Separate incidental UI metadata from
changes to clips, effects, sources, tracks, and external assets. Proceed
immediately to Step 3.

## Step 3 — Describe the contract

Record the JSON location, required companions, ID references, clock domain,
parameter representation, effect ordering, and asset dependencies supported by
the probe. Include build, OS, format version, evidence URL or local sample,
confidence, and unknowns. Do not distribute private sample media or proprietary
asset definitions. Audit the before/after documents against the pinned community
schema using the commands in the native verification reference. Record raw
schema errors separately from the exact-build profile and native compatibility
errors. Resolve discrepancies through native evidence; retain restrictive checks
for unsupported identifiers. Proceed immediately to Step 4.

## Step 4 — Verify the feature

Apply the smallest demonstrated transformation to a separate candidate. Use
the project skill's helper contract for validation and writes. Open it in the
target Camtasia build, save and reopen it, then check behavior and export when
the feature affects rendering or interactivity. Record any editor repairs.
If editor access is unavailable, prepare the probe and request the missing
access while continuing independent checks. Do not close the investigation
with its required native verification outstanding. Finish here after the
observed result is recorded.
