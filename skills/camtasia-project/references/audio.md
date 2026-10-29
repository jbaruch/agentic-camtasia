# Native audio processing and delivery

Additional observations target Camtasia Mac 2026.2.4, format 10.0. Retain the
user's mix and normalization choices. The synthetic comparisons deliberately
disabled **Project Settings → Auto-normalize loudness** to isolate processing;
the saved root has `shouldApplyLoudnessNormalization: false`.

## Sources and lossless controls

Native WAV import created an `AMFile` on an eight-second timeline. Source
track 0 describes 48000 Hz, mono, 16-bit input; project time remains separate.
**Update Media** successfully replaced that disposable source with another
WAV of the same duration. The media-bin display name retained the old label
while the actual clip/source changed. Check serialized paths and decoded
content rather than treating the bin label as proof of source identity.

A changing-tone MP4 control separately checks source replacement with project
normalization off. The backed-up bundled-source candidate retains old cached
source loudness statistics yet reproduces the actual native import's complete
video/audio streams. This scoped comparison does not make those statistics
valid for the new source or authorize disabling a user's normalization.
Preserve the user's mix and verify native source replacement and output when
normalization depends on new media measurements.

**Export → Export Audio Only** is separate from the ordinary local-video
export dialog. Its native formats are M4A, Wave, and MP3. The exercised Wave
options are **Output Mono** and 16-bit resolution, with native smoothing left
enabled. Actual output is eight-second `pcm_s16le`, 44100 Hz, one channel.
The video's project frame rate does not determine audio sample rate. The
ordinary local-file formats are MP4, MOV, GIF, and current-build WebM; choose
the delivery command appropriate to the requested output.

Native M4A and MP3 exports of the independently reopened Pitch specimen also
completed. Both output AAC/MP3 respectively at 44100 Hz with two channels,
despite the mono source; Wave's mono option does not govern those formats.
The automatic data-rate option produced approximately 128 kbit/s. Codec/container
padding made the decoded files slightly longer than eight seconds. Both retain
the measured approximately 880 Hz pitch. Per-channel RMS is approximately
0.1413 for AAC and 0.1343 for MP3 in the sampled middle window; this is a
specific lossy-export observation, not a universal gain contract. Compare
channels explicitly: a decoder's default stereo-to-mono matrix can change
the measured gain even when each channel is correct.

## Splits and transition audio

Four native linked-AV cases use the same bundled 48 kHz source: uncut, split
at four seconds, shared Fade with Use trimmed content on, and the same Fade
with it off. Wave exports use stereo, 16-bit resolution, and smoothing enabled;
actual delivery is eight seconds of `pcm_s16le` at 44100 Hz. Each case's
independently reopened Wave export is sample-for-sample identical to its first.
Both Fade settings equal the clean split control in lossless PCM and decoded
AAC. The visual trimmed-content change does not alter audio in this fixture.

Splitting alone changes native PCM beginning at sample frame 176400, exactly
four seconds. Against the uncut control, the maximum signed-16-bit difference
is 55 units and the eight-second RMS difference is 17.5008 units; 174823 of
352800 stereo sample frames differ. Source-file bytes, audio processing, and
global project fields are preserved apart from native bookkeeping. The
difference exists before AAC encoding. No external alignment, resampling, or
channel mixing was applied to make the outputs agree.

The AAC-decoded comparison has a larger maximum difference of 148 units and
begins at about 3.969819 seconds. Encoded output alone would give a misleading
change boundary. Use native lossless controls when locating an audio change;
unchanged audio objects do not establish sample identity. These measurements
do not identify the editor's internal cause or establish all source-rate,
trim, gap, transition, or retiming combinations.

Eight additional Fade cases separately exercise a six-second source skip,
a six-second edit with a 2.00x incoming clip, and a ten-second edit with a
two-second timeline gap. Each has first/reopened native stereo signed-16 Wave
exports at 44100 Hz with smoothing enabled. Three matching control pairs use
the same settings. Every pair reproduces its complete PCM exactly.

Within each family, every Fade output equals its control in both lossless PCM
and decoded AAC. This includes all four independently saved audio/visual
preroll combinations on the source skip, coupled on/off settings on the retimed
join, and coupled on/off one-sided fades around the gap. Six-second outputs
have 264600 stereo sample frames; ten-second outputs have 441000. Exact whole-
signal and boundary-window comparisons apply no alignment, channel mixing,
resampling, or equality tolerance. The gap retains the control's silent interval.
These results establish no audio change for these exercised Fade fixtures;
they do not make `useAudioPreRoll` irrelevant for every transition or mix.
Read the [independent flag and video results](transitions.md#edited-av-boundaries-and-independent-preroll-flags).

## AI Noise Removal

The native preset saves `VSTEffect-DFN3NoiseRemoval` in
`categoryAudioEffects`. Its UI amount 80 maps to bare numeric
`parameters.Amount: 0.8`; `parameters.Bypass: 0.0` is separate from the outer
`bypassed` flag. Preserve casing and the complete native metadata, including
`ExtandableEffectData` (that is the observed spelling). The probe's opaque
string is approximately 244 kB. Amount alone is not a replacement for that
editor/plugin data. Keep the appropriate native runtime available; the source
bin is not a complete inventory of processing dependencies.

The generated clean-speech reference and fixed noisy input establish a real
native cleanup result. At the native 80 setting, reference-quiet output RMS
decreased about 11.5 dB, reference-projected SNR increased from 18.9 to 25.2 dB,
and fitted speech gain changed about −0.13 dB. Measurements separately report
the best correlation alignment (−528 samples in this comparison); they do not
establish a universal latency or perceptual-quality guarantee. Check both noise
and retained speech when choosing settings.

The independently reopened native project retained amount 80. A fresh native
Wave export after reopening is sample-for-sample identical to the first output.
This verifies persistence of the demonstrated processor state, rather than
only acceptance of a saved effect name. Private/native payloads and the test
media are excluded from distribution.

## Pitch

The native preset saves `Pitch` with bare numeric `pitch`, `effectBlend`,
`smoothness`, and `tightness`. The observed defaults include blend 100 and
smoothness/tightness 50; preserve those additional controls when changing pitch.
Setting the native Pitch field to 1200 changed the synthetic 440 Hz tone to
approximately 880 Hz (880.25 Hz in the sampled FFT). Both native exports remain
eight seconds. The probe kept clip scalar 1: changing pitch is distinct from
retiming the clip or relabeling its sample rate.
Independent native reopen retained the Pitch field at 1200; the subsequent
M4A and MP3 exports preserve the shifted tone. The exact-build profile admits
the observed `Pitch` identifier.

## Audio Compression

The native Medium variation saves `WinCompression`, not the UI label, with
bare parameters `ratio: 10.0`, `threshold: -20.0`, `gain: 9.0`, `attack: 0.0`,
`release: 3500.0`, and `preset: 1`. Independent reopen retained Medium and
the displayed ratio, threshold, and gain. Preserve the attack/release values;
this observation does not establish units for arbitrary processor fields.

On an alternating quiet/loud synthetic tone, the native export reduces the
absolute peak from about 0.854 to 0.349. The quiet level after a loud section
also remains suppressed: middle-window RMS is about 0.199 in the first quiet
section and about 0.039 in later quiet sections. This is a stateful processor,
so an isolated gain calculation or a global loud/quiet average does not describe
its recovery. Check attack/release behavior across boundaries, and do not
silently replace the native preset with sample-wise normalization. The current
profile admits the native `WinCompression` identifier.

## Native Fade In and Fade Out

The presets modify `AMFile.parameters.volume`, a typed `double` envelope;
they do not add `FadeIn`/`FadeOut` effect identifiers. On the eight-second
speed-1 tone, Fade In writes point keyframes at zero with value 0 and at one
second with value 1. Fade Out writes value 1 at zero and seven seconds and
value 0 at eight seconds. Each point has equal `time`/`endTime` and zero `duration`.
The times use the observed media clock of 705600000 ticks per second; preserve
the owning clock when trim/speed differs.

Both specimens independently reopened. Native Wave measurements show the
expected ramps, unchanged middle level, and unchanged tone frequency. A fresh
Fade Out export after reopening has identical decoded PCM to the first export.
Keep existing volume automation when adding a fade; a preset applied to an
already automated clip requires a before/after diff and boundary check.

## Emphasize and other tracks

Native `Emphasize` uses bare `emphasizeAmount`, `emphasizeRampPosition`,
`emphasizeRampInTime`, and `emphasizeRampOutTime`. UI amount 80 maps to 0.8;
the one-second ramps save as 705600000 ticks. The observed positions are
Outside = 0, Span = 1, and Inside = 2. All three saved modes independently
reopened with their controls retained.

The two-track probe places a foreground 880 Hz tone at seconds 2–6 over an
eight-second 440 Hz background. At amount 80, the background's steady amplitude
falls from approximately 0.200 to 0.040, while the foreground stays approximately
0.200. Outside ramps occupy seconds 1–2 and 6–7; Inside ramps occupy 2–3 and
5–6; Span ramps occupy 1.5–2.5 and 5.5–6.5. The native outputs verify all three
placements. This processing affects other clips outside the foreground's own
bounds in the Outside/Span modes. Preserve neighboring audio and test the
whole transition; checking only the selected clip is insufficient. Multiple
overlapping Emphasize effects require a separate mix test.

## Audio-based media alignment

Select the intended timeline clips and use the native context menu **Sync
Media**. The exercised two-audio case anchors the lower track and moves the
upper track. At time zero, Camtasia refused a result requiring a negative start
and instructed moving the lower-track media. Leave enough timeline room for
the estimated offset; retain a pre-sync copy and inspect which clips moved.

Sync changes ordinary clip `start` values; this specimen added no effect or
new source. Read the saved ticks rather than reconstructing an offset from
the frame-formatted duration label. Native estimates can land between frames.
An independently measured 1.500-second input delay, with the lower clip at
2 seconds, gave upper starts of 0.496 and 0.512 seconds in two native runs.
These are approximate results, not a stable bias or a correction to apply to
other projects. Check transient alignment and audible phase/echo after syncing.

A separate known-delay refinement placed the upper clip at 0.500 seconds.
The test used gain 0.5 on both clips to prevent clipping during comparison;
the aligned sum closely matched the expected reference-projected gain 0.9.
Both the second native estimate and the refinement independently reopened
and produced sample-identical Wave exports. Preserve the intended final mix:
these duplicate speech tracks were a measurement fixture, not a recommendation
to retain both microphones in every delivery.
