# Nonlinear visual-effect intervals

Use the [effect-curve helper](helper.md#visual-effect-curve-editing) for existing
typed native double parameters. Its compiler owns input versions, easing choices,
clock conversion, interval preservation and refusal rules. This reference records
native Mac 2026.2.4 / format-10 evidence, using Sepia intensity as a visible control.
It does not supply new effect or parameter constructors.

## Native captures and independent easing

Native application of Sepia to linked AV creates matching wrapper/video effects
with the same stable token. Starting at intensity zero, **Modify → Add Animation
→ Custom** at second two makes a one-second interval beginning at second one.
Changing intensity to one at its endpoint creates the typed double descriptor
and interval frame on both visual mirrors. The audio child remains unchanged.

The native animation-arrow context menu changes **Animation Easing** between
Spring, Exponential In/Out, Bounce and None. Each saved change patches only the
matching effect frame on both mirrors, the visual interval's interpolation and
the UI command counter. The version-2 compiler reproduces all four complete
native documents from the captured descriptor, apart from thumbnails and UI
command counts. Native None corresponds to the helper's linear choice.

A separate probe preserves the native Spring effect frames while setting its
shared visual interval and translation frame to linear. Geometry moves from
−60 to +60 between seconds one and two. Native readback at 1.1 seconds gives
translation −48 and intensity 60%; at the displayed 1:07 frame it gives
translation −32 and intensity 116%. At 1.5 seconds geometry is zero while the
effect is 97%. Native saving changes only the thumbnail. Per-effect frame easing
can differ from the shared geometry interval; a global easing edit would change
that unrelated animation.

## Retimed rendered controls

A helper-authored 39-second sequence contains thirteen three-second cells.
Linked foreground AV has a positive one-second source in-point and 2× speed.
Its four easing cells, mixed exponential/bounce return, cleared curve, bypassed
curve and independent zero/one controls all retain the same linear translation.
The single-ramp interval spans timeline seconds 0.5–2.5 and source seconds 2–6.
The mixed cell has two matching intervals with independent linear geometry.

A 2× Group contains ordinary visual media and uses a zero Group source in-point.
Its Spring, cleared, zero and one cells retain the same linear movement; its
parent interval instead maps to source seconds 1–5. The child supplies its own
positive source in-point. The Group effect does not rewrite child clocks or
source selection. Generated background AV repeats its three-second source clock
outside both foreground scopes.

Two fresh-process exports have identical complete decoded RGB and PCM audio.
Three contact sheets contain 65 inspected phase frames, with 130 sampled frames
measured in total. Foreground rectangle bounds stay within two pixels of the
independent linear position/size calculation throughout every state. Sepia's
color progression differs while that geometry remains the same.

Projection between the independent zero/one color controls at 10% of the ramp
is approximately 0.100 for linear, 0.017 for exponential, 0.067 for bounce and
0.607 for Spring. Spring later exceeds the full-intensity control, matching its
native overshoot rather than a clamped target. The mixed curve reaches its first
target and returns to the original colors without changing geometry timing.
Cleared and bypassed states differ from zero controls by at most 0.744 mean
absolute RGB byte levels per channel across the samples; their projected effect
amount stays within 0.0013 of zero. These comparisons include encoding variation
between distinct cells; the two complete native renders themselves match exactly.

Linked cells retain both foreground audio and the independent background tone.
Their stereo RMS is 0.19169–0.19177, compared with 0.09614–0.09617 for the Group
cells' background-only audio. Every selected two-second audio window retains the
440 Hz tone; RMS differs from its corresponding zero-effect control by less
than 0.000041. This is a preserved native mix, not an assertion that visual
layers are silent. Outputs are 640×360 H.264 at 30 fps with stereo 44.1 kHz AAC.

## Normalization and representation limits

The first sequence save has 197 differences: native ID remapping, thumbnail and
track-height caches, Group defaults/number types, eighteen constant scale
companions and collapse of static intensity descriptors. Nonlinear effect frames,
linear geometry, stable tokens, source definitions and audio controls survive.
The second save reconstructs six constant-zero intensity companions from retained
visual intervals. The third fresh-process save is byte-identical to the second.
Clearing changes intensity alone; native reconstruction does not remove the
other animation or turn the constant effect back into the original ramp.

The exact-build schema profile passes with the existing Sepia enum correction.
No new correction is needed. Source media retains its original SHA-256. A
preliminary sequence using numeric `0.5` speed fields entered native corrupt-
project handling and then the previously observed cloud-path diagnostic stall.
Changing only those fields to the native saved `"1/2"` form allows opening.
That negative comparison does not establish every owner's numeric-scalar parser;
retain the project's native clock representation. The stalled test process
exits through normal Quit; privacy-service health remains unchanged.

Completed captures, projects, exports, process samples and measurements are
removed after incorporating these findings. Existing owner/type/resource limits
remain in the compiler contract. Point frames, new recording clocks and arbitrary
effect-specific parameter combinations still require their own native evidence.
