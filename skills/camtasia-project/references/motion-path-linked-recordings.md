# Motion Paths on linked moving recordings

Use the [Motion Path helper](helper.md#motion-path-json-editing) for explicit
points, Auto Orient, bypass and removal. Camtasia Mac 2026.2.5 (2026.136), format
10, supplies the native controls below. This adds root `UnifiedMedia` /
`ScreenVMFile` pairs with a same-source stereo `AMFile` child. It constructs no
recording and does not establish Group-contained or stitched-child linked paths.
The helper's shared recording-owner guard checks that scope, complete equal
visual clocks, positive rate/inverse speed and canonical unique visual tokens.

## Placement, clocks and companions

Native Motion Path application creates matching wrapper/video `MediaPath`
effects with stable `effectIndex: "0"`; audio receives no path. The exercised
recording starts at timeline second one, selects source seconds two–ten and
plays at 2×, ending at timeline second five over an eight-second background.
Adding the path at timeline second two creates points at clip-relative seconds
one–two. Their source-position ticks are 2822400000 and 4233600000 at edit rate
705600000. The first value is `[0,0,0]`; the second is `[256,144,0]`, with the
existing native Bézier controls `[128,0,0]`, `[128,144,0]` and `"eioe"`.
No visual animation interval is added. Explicit point replacement retains the
existing helper's point/interpolation contract, separately from interval curves.

Auto Orient sets both path controls to one, adds wrapper reset metadata
`default-MediaPath-mediaPathAutoOrient: "0"` and adds the video-only rotation
`{"type":"double","defaultValue":0.0,"interp":"eioe"}`. Bypass removes that
rotation; re-enable restores it. Orientation changes while bypassed leave it
absent. Turning orientation off or removing the path removes the companion and
retains reset history. Unknown nonzero or animated rotation still refuses.

Eight complete native/helper comparisons cover construction, orientation,
bypass, off/on while disabled, enable, off while enabled and removal. They
differ only in thumbnail caches and exactly one native command-count increment.
Source definitions, recording processing, recorded cursors, original geometry,
audio and all owner clocks survive. Wrapper/video selectors produce the same
candidate; new tokens also reserve existing audio-effect identities.

## Native output and persistence

An eighteen-cell, 144-second sequence contains all eight native/helper pairs,
an independent bare recording and a background-only control. Two exports from
separate editor processes repeat all 4320 decoded RGB frames per movie and the
complete stereo PCM streams exactly. Output is 640×360 H.264 at 30 fps with
stereo 44.1 kHz AAC. Both editor processes have positive handles to the matching
MP4 and TREC within the test bundle.

Sixty inspected phase frames show matching movement, path-tangent rotation,
static bypass/removal and the native endpoint's canvas clipping. Across 108
sampled frames, 48 native/helper pairs differ by at most 0.788 mean RGB byte
levels per channel. Bypass/removal versus the bare control differ by at most
0.304 levels. These separately encoded cells retain small differences; exact
stream equality above compares the two complete exports. The permission notice
inside the recorded picture is source content, not a new OS permission grant.

All 144 measured audio-channel windows retain the 440 Hz background tone at
amplitude 0.1358–0.1364. Recording-active windows retain 660 Hz at
0.13276–0.13288; outside that interval or in the background-only cell it stays
below 0.000029. Motion and orientation do not move the recorded audio interval.

The first save changes only 105 clip IDs and the thumbnail. Independent native
reopen/save is byte-identical. Thirteen snapshots pass their existing exact-build
schema profiles and native hazard checks; raw errors are the known `MediaPath`
enum omission. No schema correction is added. Canonical inputs, bundled source
hashes and protected originals remain unchanged. The real standard-library CLI
matches the rendered helper payload and repeats as a no-op. Completed disposable
projects, exports and audit records are removed after incorporation into the
plugin and tests. Other linked owner/container forms retain separate native
verification obligations.
