# Motion Paths on linked moving recordings

Use the [Motion Path helper](helper.md#motion-path-json-editing) for explicit
points, Auto Orient, bypass and removal. Camtasia Mac 2026.2.5 (2026.136), format
10, supplies the native controls below. This adds root `UnifiedMedia` /
`ScreenVMFile` pairs with a same-source stereo `AMFile` child. It constructs no
recording. Group-contained paths have the additional controls below; stitched-child
linked paths retain separate contracts.
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

## Group-contained linked recordings

Version 0.69.0 extends the same helper to Group-only ancestors, including nested
Groups. Edit the selected linked recording through its wrapper or video ID.
Point times stay relative to that recording's visible timeline; Group placement
is not added to its source clock. The helper preserves every ancestor's clocks,
bounds, geometry and bindings. It performs no Group construction or resizing.
Other containing forms retain their own verification obligations.

Native Mac 2026.2.5 grouping moves the linked pair's start to zero while retaining
its source in-point at two seconds, inverse speed `"1/2"` and four-second visible
duration. The outer Group starts at timeline second one. The explicit native
**Edit → Resize Group → To Canvas Size** workflow supplies 640×360 bounds before
path editing. A second enclosing Group retains those bounds and moves the inner
Group's start to zero. Apply that native sizing operation when movement needs
the canvas-sized frame; the helper retains the recipient's existing clipping.

Native path construction in either Group depth retains source points
2822400000 and 4233600000 for local seconds one–two. Mirrored effects, stable
tokens and the typed video-only Auto Orient rotation match the root recording.
Ten complete native/helper comparisons cover the single-Group lifecycle above
and nested construction/orientation. Differences are exact command increments,
thumbnail caches and two constructor UI initializations: opening the selected
Group tab and adding `{"IsLocked":"False","trackHeight":"78"}` to its parent
track metadata. The helper preserves those ancestor fields instead of inventing
UI state. Native Group-tab closure changes only the observed open flag.

A 22-cell, 176-second comparison contains all ten native/helper pairs, a bare
Group recording and a background-only control. Two separate editor processes
produce identical complete RGB/PCM streams, with 5280 decoded frames per movie.
Both use 640×360 H.264 at 30 fps and stereo 44.1 kHz AAC, and both have positive
handles to the bundled MP4 and TREC. Sixty inspected phase frames show matching
movement, tangent orientation, restored bare states and canvas clipping in
single/nested Groups. Across 132 sampled frames, 60 native/helper pairs differ
by at most 0.776 mean RGB byte levels per channel; restored/bare comparisons stay
within 0.310 levels. These cell comparisons retain small encoding differences;
the two complete exports themselves match exactly.

All 176 audio-channel windows retain the 440 Hz background at amplitude
0.1358–0.1364. Recording-active windows retain 660 Hz at 0.13276–0.13288, with
maximum outside-interval/background-only amplitude below 0.000029. The first
save changes only 154 clip IDs. Independent native reopen/save is byte-identical.
All other project values, canonical inputs, source hashes and protected originals
survive. Nineteen snapshots pass the existing exact-build schema and hazard
checks; raw errors remain the known `MediaPath` enum omission. No profile change
is added. The actual standard-library CLI reproduces both rendered constructor
candidates, preserves inputs and repeats through the video aliases as no-ops.

The first cold open stopped responding in native capture-device initialization
with its input unchanged. After an authoritative responsiveness check, a
read-only sample and the owned editor PID's verified exit, a replacement process
saved/closed an empty disposable project and opened the unchanged sequence.
Both successful render sessions initialize with that empty input. Follow the
[native recovery procedure](native-verification.md#serialized-native-work-and-stability);
this observation establishes neither a source repair nor a permanent startup fix.
Completed disposable verification files are removed after incorporation and
installed-consumer acceptance.
