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

## Linked recording frame extensions

Camtasia Mac 2026.2.5 (2026.136), format 10, extends a trimmed 2× linked
recording with a direct `StitchedMedia` parent. Its moving child remains
`UnifiedMedia` with `ScreenVMFile` video and same-source `AMFile` audio; a separate
`ScreenIMFile` holds the selected final frame. This is not a linked frozen
wrapper. Select the parent for its hotspot and media marker. Hidden moving,
linked-video, audio and held children remain outside independent hotspot edits.

Native Continue, Time, URL, Marker and removal controls match the existing
helper while preserving every descendant, cursor payload, audio clock, source
definition and unrelated attribute. Whole-document lifecycle comparisons permit
only the command counter, thumbnail and native effect-selection cache. Removing
the hotspot retains the parent marker. A native save may finish after its UI
action returns; capture the completed save after closing the document.

The parent starts at one second, has a two-second source in-point and inverse
speed scalar `"1/2"`. Its moving portion ends at five seconds and its held portion
ends at seven seconds. The parent media marker at source point `8373120000`
maps to global tick `4186560000` (5.933… seconds), without applying its linked
children's mirrored clocks again. Native marker creation accepts the interactive
canvas resize prompt. The helper reproduces the native marker owner, point and
cache exactly.

A 72-second sequence places the destination parent before four native/helper
action pairs. Two fresh editor processes save and export the sequence. The first
save remaps 72 clip IDs and two Marker references, collapses 63 static held
descriptors and changes two track-height caches. All other values and bundled
source bytes remain equal. The independent reopen/save is byte-identical and
retains both Marker actions and their owner bindings.

The two 852×480, 30 fps movies have identical complete decoded RGB and stereo
44.1 kHz PCM streams. Thirty-six inspected frames retain moving, held and
outside-owner states. Sixteen native/helper sample pairs differ by at most
0.031 mean RGB byte levels per channel. Seventy-two audio-channel windows retain
the 440 Hz background and the 660 Hz sped-up recorded-system-audio tone in the
moving portion. The held portion retains background audio without the recorded
tone. This extends the earlier video-only recording observation to recorded audio.

Both exported Smart Player packages pass eight actual activations each: native
and helper Continue resume from the observed end pause, Time seeks to 0.5 seconds,
URL reaches the local same-tab destination, and Marker reaches the earlier
parent's held-section destination. Serve the complete package over HTTP with
byte-range support. The checked action spans remain six
seconds across the moving/held join, with stable bounds and end-pausing. Time
destinations serialize as 500 ms, Marker destinations as 5933 ms and URL actions
retain the same-tab choice. These controls do not establish linked frozen
wrappers, placeholders, forward Marker references or additional scene clocks.

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
