# Frozen and stitched hotspot owners

Use the [hotspot helper contract](helper.md#hotspot-json-editing) for candidate
staging, supported owners, actions and marker clocks. The helper edits existing
owners; constructing their source recordings and frozen/stitched arrangements
retains the [native ownership contract](animations.md#frozen-and-stitched-owners).

## Native ownership and marker clocks

Camtasia Mac 2026.2.4 / format 10 stores an Interactive Hotspot on a standalone
held recording or stitched parent using the ordinary hotspot payload. Native
application to the stitched parent leaves its moving and held children unchanged.
Four independent before/after captures establish the two default constructors
and their Marker actions. Helper replay matches these payloads while retaining
cursor points, source definitions, child timing and unrelated attributes.

Extending the eight-second recording to ten seconds creates a stitched parent.
Its media marker at source position nine seconds belongs to the parent. Native
removal of all stitches removes the parent hotspot and moves that marker to the
standalone held owner's local one-second point. The held owner retains source
frame `5621280000` and `mediaDuration: 1`; its marker origin is independent of
that selected source frame. Native marker creation requires the editor's minimum
interactive canvas dimensions; the disposable control accepts its resize prompt.

The native Marker selection caches nine seconds globally for that held point.
Changing the held owner's inverse-speed scalar to `"1/2"` produces 8.5 seconds
without changing its source frame. A separate stitched parent at ten seconds,
source in-point two seconds and scalar `"1/2"` maps its nine-second source point
to 13.5 seconds. The native save refreshes both caches to the helper's exact
tick values. Hidden stitched children are not independent hotspot owners.
Linked variants require separate ownership and clock evidence.

## Persistent native and runtime controls

A helper-authored 66-second sequence contains four actions on each new owner
and two destination controls. The held copies retain their source frame at 2×
speed. Stitched copies retain a positive in-point, 2× speed and moving-to-held
boundary. An independent linked AV background continues through every cell.

Both independent native web exports pass eight actual Smart Player activations:
Continue resumes after the observed end pause; Time jumps to 61 seconds; the held
URL opens a new tab and the stitched URL replaces the current tab; Marker jumps
to the held control at 0.5 seconds and stitched control at 9.5 seconds. Their XMP
retains all eight action spans, bounds, pause/window settings and destinations.
Serve the complete package over HTTP with tested byte-range support.

The second fresh-process native save is byte-identical to the first, including
both Marker action codes, owner IDs, point times and caches. Whole-document
comparison of the first save permits clip/reference ID remapping, collapse of
static held parameter descriptors and the thumbnail addition. Source-bin
definitions, bundled source hashes, cursor payload and all other content survive.
The candidate and both saves pass the pinned raw schema and exact-build profile.

The two 66-second 852×480 exports have identical complete decoded video and
stereo 44.1 kHz audio. Twelve inspected frames retain the synthetic page and
recorded pointer across held, stitched and destination controls. The recording
has no audio stream; audio preservation covers the independent background.

## Forward-reference failure

An earlier synthetic sequence places destination owners after their referring
hotspots. Its first native save produces incorrect marker owner IDs while
retaining the expected global caches. The next fresh save converts both Marker
actions into Time actions at those caches. Both movies can still seek correctly.
Reordering only the JSON media array does not repair that specimen; the editor
sorts the owners by timeline position. Placing the destination controls earlier
in the timeline yields the persistent accepted pair described above.

Check the saved action and marker identity after fresh reopening, separately
from playback and global-clock arithmetic. Do not accept a cached seek as proof
of a working forward Marker binding or silently convert a requested Marker to
Time. The staging helper reports `nativeVerified: false`; these observations
do not establish arbitrary forward references, linked recording wrappers,
placeholder targets or multiple-scene marker clocks. Completed probes, movies,
screenshots and logs are disposable after incorporating these findings.
