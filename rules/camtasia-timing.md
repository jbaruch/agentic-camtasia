---
alwaysApply: true
description: Clock domains and container timing for Camtasia edits
---

# Camtasia Timing

## Clocks

- Apply these directives when changing Camtasia timing.
- Read project `editRate` and frame rate from the document; never assume the demo's values.
- Distinguish project ticks, source-stream ticks, clip-local ticks, and displayed seconds.
- Determine parameter clocks independently of their containers; source-owned data need not use the source stream's sample clock. See `skills/camtasia-project/references/captions.md` for the native transcription probe.
- Preserve parameter-specific units; a duration-named control need not use its effect's outer clock.
- Preserve rational scalars and time values without a float round trip.
- Quantize edited video clip cuts to the target frame grid; preserve native subframe effect timing and intentional subframe audio edits.

## Containers

- Traverse every scene and nested `Group`, `StitchedMedia`, and `UnifiedMedia` container.
- Resolve `trackNumber` against the source's streams, separately from the timeline lane.
- Preserve container-relative offsets; negative child starts can be valid.
- Treat still-image holds separately from playback of finite video or audio.
- Clone with fresh clip IDs and remap internal references, including transitions.

## Changes

- When splitting linked media, update wrapper and child timing in their respective domains.
- Keep presenter source offsets advancing across splits.
- Retain keyframe defaults, interpolation, and animation-track metadata.
- Check source bounds against the selected source stream's rate and range.
- Require continuity only on lanes the edit intends to keep continuous.
