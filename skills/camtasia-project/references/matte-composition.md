# Media and track matte composition

Use [matte JSON editing](helper.md#matte-json-editing) to stage explicit media
and root/Group track changes together. The compiler owns the input schema and
preservation/refusal contract. Existing layer arrangement and native fill/alpha
content determine the result; this operation does not arrange a composition.

For example, after inspecting IDs and storage track indices:

```json
{
  "schema_version": 1,
  "media": [{"clipId": 114, "mode": "alpha-invert"}],
  "tracks": [{"track": 1, "groupId": 115, "mode": "alpha"}]
}
```

Pass that file to `set-composition --spec`. Inspect the complete candidate diff,
validate it and use the ordinary guarded apply workflow on the closed project.
One invalid later edit refuses the complete operation before an output write.
Choose an unoccupied candidate path or repeat an identical staging operation.
Reinspect IDs after native saving; the editor can remap them.

## Independent native controls

Observed in Camtasia Mac 2026.2.4, project format 10. A forty-second sequence
has eight separate four-second Groups, followed by independent blue-content
and background-only controls. Each Group contains the same blue rectangle on
its lower track and filled white ellipse above it. Generated color-bar video
and a sine-wave audio track run beneath the Groups, outside their scope.
Every background cell repeats the same source clock.

| Media effect on ellipse | Upper Group track mode | Native result |
| --- | --- | --- |
| None | None | White ellipse over blue rectangle. |
| Alpha | None | Blue inside ellipse; background outside. |
| None | Alpha | Same visible mask as media-only Alpha. |
| Alpha | Alpha | Same visible mask as the two independent Alpha controls. |
| Alpha Invert | Alpha | Blue rectangle outside ellipse; background inside. |
| Alpha Invert, bypassed | Alpha | Blue inside ellipse; the track mask remains active. |
| Alpha Invert, half intensity | Alpha | Blue remains outside; the interior partially reveals background. |
| Both previously active controls cleared | None | Same visible picture as the original unmasked pair. |

The combined Alpha result alone does not establish two successive mask
multiplications. The mixed inversion, bypass and half-intensity controls
separately establish observable interactions in this arrangement. Preserve both
selected controls; do not infer a universal ordering or simplify them algebraically.
Clearing a media effect alone does not clear its track's matte mode.

Ten inspected full-resolution exported frames cover every cell and both
independent references. Media-only Alpha differs from the track-only and
combined controls by less than 0.059 mean absolute RGB byte levels per channel.
Bypass with track Alpha is decoded-identical to track-only Alpha at the sampled
source time. Clearing both differs from the raw pair by less than 0.057.
Inner and outer regions independently distinguish opaque blue, white fill,
background and partial transparency.

## Root scope and empty upper lanes

A separate eight-second root timeline has background AV, the blue rectangle
and the same white ellipse on three lanes. Media Alpha Invert plus root-track
Alpha matches the Group mixed-control picture within 0.094 mean absolute RGB
byte levels per channel at the sampled source time. Background remains visible
outside the rectangle and through its ellipse-shaped hole.

In the second half both upper lanes contain no media. The stored root-track
Alpha mode remains; the background-only picture differs from its independent
control by less than 0.054. This case establishes empty-lane behavior for the
tested stack, not a rule for every combination of overlapping mattes. Track
mode belongs to the lane for its whole scope. Use separate Groups for different
track modes across sequential cells rather than inventing per-clip track modes.

## Save, reopen and preservation

Both sequences have two fresh-process native exports with identical complete
decoded RGB and PCM audio within each pair. Output is 640×360 H.264 at 30 fps
with stereo 44.1 kHz AAC. All 48 one-second windows per channel retain the 440 Hz
tone; RMS stays between 0.0959 and 0.0964, with the fundamental more than 100×
the 880 Hz control. The test verifies preservation of the independent linked
background audio, not a new recorded-audio owner contract.

Whole-document comparisons find only native ID remapping, shape color/default
normalization, Group bounds/audio defaults, static intensity collapse and UI
caches on the first saves. Native matte modes, bypass, half intensity, timing,
source definitions and audio controls remain unchanged. Both second saves are
byte-identical. Source media retains its original SHA-256. Candidates pass the
raw pinned schema; native saves pass the existing exact-build profile with its
previously documented omitted-Callout-metadata correction. No new correction is
needed. Completed probes, exports and measurement files are disposable.

Root linked moving recordings have a separate [mirror/audio contract](matte-recording-owners.md#linked-moving-recordings).
Further linked variants and a working point-intensity representation retain
separate investigation. Verify the actual consumer project's native output
before delivery; this bounded arrangement does not cover every matte stack.
