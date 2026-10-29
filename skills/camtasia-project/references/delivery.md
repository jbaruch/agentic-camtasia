# Native local video delivery

These observations target Camtasia Mac 2026.2.4. Local-file settings belong to
the export workflow; a filename suffix or project format does not select a
codec. Inspect the actual output streams. Audio-only delivery has a separate
contract in [audio](audio.md), and interactive packages in
[advanced features](advanced-features.md).

## WebM transparency

Native **Export → Local File → WebM → Options → Transparent background**
controls alpha independently of the visible project background. The exercised
options use Current dimensions, automatic frame rate, quality 60, keyframe
interval 30, and audio data rate 192 kbit/s. Actual output is VP9 video at
640×360/30 fps and stereo Opus at 48000 Hz. The eight-second video's container
lasts 8.028 seconds with this audio encoding; inspect stream bounds separately.

A real recorded-pointer Isolation effect removes the screen image. With
Transparent background enabled, the native WebM's sampled frame has alpha
0 through 255, including partially transparent cursor edges. Compositing over
a colored background confirms the cursor alone. Disabling the option produces
a fully opaque sampled frame. Both native exports completed in Export History.

The default FFmpeg VP9 probe reports `yuv420p` even with `alpha_mode: 1`.
The verification explicitly decodes with libvpx-vp9 to RGBA and examines the
alpha plane. Neither that pixel-format label alone nor a black preview proves
alpha is absent. Check actual transparency in the intended destination too.
[Chrome's WebM alpha documentation](https://developer.chrome.com/blog/alpha-transparency-in-chrome-video)
describes VP8/VP9 compositing; this is not a claim of identical behavior in every
browser, player, or editor.

The exported transparent WebM also imports natively into this same Camtasia
build. On a green project canvas its native MP4 export shows the isolated
cursor over green; a saved copy independently reopens and rerenders. The source
uses microsecond edit-rate bounds distinct from its 30 fps video/48000 Hz audio
sample rates, and the native linked wrapper/children remain intact. Exported
pixels do not retain the original TREC's editable recorded cursor events.
The silent Opus import also exposes the large native loudness decimal described
in [the format map](project-format.md).

## QuickTime and preserved canvas alpha

The native QuickTime codec menu offers H.264, HEVC (H265), Apple ProRes 4444,
and Apple ProRes 422. Native ProRes 4444 exported as `ap4h`, `yuva444p12le`,
640×360 with stereo AAC at 44100 Hz and an eight-second container.
The other native codec exports also completed at 640×360/30 fps for eight
seconds with stereo AAC at 44100 Hz: H.264 uses `avc1`/High/`yuv420p`, HEVC uses
`hvc1`/Main/`yuv420p`, and ProRes 422 uses `apcn`/Standard/`yuv422p10le`.
These describe the exercised options, not every encoder setting.

ProRes 4444's alpha-capable pixel format does not establish transparent output: the
recorded-cursor specimen's decoded alpha was entirely 255.

A separate closed disposable copy set `timeline.backgroundColor` from
`[0, 0, 0, 255]` to `[0, 0, 0, 0]`. Native reopen/save retained the zero alpha,
but its subsequent ProRes 4444 output was still entirely opaque in the sampled
frame. The tested alpha-zero MOV/GIF exports also rasterize a checkerboard
background; that pattern is opaque image content, not an alpha plane. The native project-settings color picker exposed RGB controls. Do not
use that preserved JSON component as proof of transparent MOV rendering, or
silently rewrite a user's canvas alpha to obtain transparency. WebM's explicit
export option is the demonstrated native transparent-video path for this build.
This observation does not prohibit other source/build workflows from working;
verify their actual alpha before promising delivery.

## GIF timing and loops

Native GIF options offer Project Dimensions, percentage/custom dimensions,
automatic or fixed frame rate, dithering, and loop counts 1–5 or Infinite.
The 640×360 automatic-rate specimen has 240 frames with 30/40 ms delays summing
to eight seconds. A 50%-size, 15 fps, dithered specimen has 120 frames at
320×180 with 60/70 ms delays, also summing to eight seconds. Both sampled
frames are opaque. Inspect per-frame delays rather than multiplying one rounded
delay by the frame count.

The native three-loop setting writes Netscape repeat metadata 2. The native
Infinite setting writes 65534, rather than the zero infinite-loop sentinel
specified by [Pillow's GIF contract](https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html#gif).
Do not describe the native file as mathematically unlimited from its UI label.
For a requested unlimited GIF, retain the native original and create a copy
with zero loop metadata using a GIF-aware tool. The verified correction changes
only the observed repeat-count bytes and preserves every decoded RGBA frame
and frame delay. Inspect the actual application block; do not reuse a fixed
byte offset or modify an unrecognized/multiple block blindly.

## Native batch delivery

Apply the [serialized native stability procedure](native-verification.md#serialized-native-work-and-stability)
before this workflow. On an installation showing the recorded helper/watchdog
failure pattern, use individual local exports and omit Batch Export and Export
History. The successful batch observations below describe earlier runs.

**Export → Batch Export → Add Project** accepts multiple saved `.cmproj`
bundles. Select an explicit output directory and inspect **Options**: the
verified run uses MP4, Current dimensions, H.264, automatic frame/data rate,
and enabled audio. Queue dimensions/durations initially show zero while the
editor loads them; wait for real values before starting.

The native queue completed thirteen eight-second 640×360 projects. Outputs
use project basenames, rather than the earlier individual export filenames.
Require the native completion result and inspect every output's streams.
A populated output directory or one successful row does not establish that the
whole batch succeeded. Preserve originals and use a fresh output directory
when comparing persistence or avoiding name collisions.
