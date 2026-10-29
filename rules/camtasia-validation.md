---
alwaysApply: true
description: Structural checks and editor playback evidence for Camtasia work
---

# Camtasia Validation

## Static Checks

- Apply these directives when delivering Camtasia edits.
- Run the project helper before and after a change; report inherited defects separately.
- Check source references, IDs, timing, transition endpoints, and preserved tracks.
- Read the helper's warnings and validation limits; a passing report is a partial structural check.

## Editor Checks

- Follow the serialized native preflight and failure-recovery procedure in `skills/camtasia-project/references/native-verification.md` before editor automation.
- Reopen the candidate in the target editor and check for repairs or missing-media dialogs.
- Confirm visible sources, tracks, duration, and preview match the candidate before export.
- Inspect changed cuts, animation endpoints, text bounds, matte behavior, and captions in playback.
- Listen to changed audio and verify that visual edits preserve narration effects.
- A source-frame preview does not prove Camtasia compositing, cursor rendering, or audio processing.
- Test hotspots and quizzes in the intended player or LMS output.

## Handoff

- Export through Camtasia when native effects must appear in the deliverable.
- Identify the edited project, backup, changed seek points, and checks performed.
- State editor playback or export as pending when it has not been observed.
- Never describe JSON validation as proof of full format compatibility.

## Native Adapter Coverage

- The Platform-Bound Untestable Carve-Out covers only Camtasia's execution of `skills/camtasia-project/scripts/native_roundtrip.applescript`.
- Its Python editor selection, ownership, backup, response, and error handling remain unit-tested.
- Preconditions and native validation procedures are in `skills/camtasia-project/references/native-verification.md`.
