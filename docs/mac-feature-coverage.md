# Mac feature coverage

This summary distinguishes reusable JSON editing from broader native feature
knowledge. Version 0.1 has shipped. Continued work follows the
[release plan](release-plan.md); the operator's feature-complete 1.0 requirement
includes all remaining gaps in the [completion plan](feature-completion-plan.md).

## Current coverage

| Family | Reusable editing or documented native support |
| --- | --- |
| Projects and sources | Inspection, IDs/references, partial validation, exact numeric handling, source manifests, candidate staging, guarded writes and backups. |
| Animation | Visual intervals, easing, removal and empty markers; explicit Motion Path points, orientation, bypass and removal on verified visual owners, including frozen/stitched forms. |
| Transitions | Root-track Fade construction and existing scalar/duration/removal editing. Native references cover all 179 current palette presets, one/shared edges, short clips, source skips, gaps, retiming and preroll. |
| Effects and mattes | Native-template visual effect creation, static edits and typed effect curves on ordinary and moving/frozen/stitched recording owners; LUT resource/range/easing controls; supported track/media mattes including moving/frozen recordings and stitched parents, modes, linear/nonlinear intensity curves and lifecycle. Native references cover current visual, LUT and gesture families. |
| Annotations and behaviors | Native specimens for all 134 annotation entries and thirteen behaviors. Annotation template construction preserves clocks, drawing modifiers and one-sided Fades; root or Group-contained Sketch Motion drawing-time/thickness/RGB controls include trimmed/speed-adjusted clips; existing shape controls, text wrapping/outline placement, continuous text-outline width/RGBA and remix fill/stroke intervals with coupled geometry/easing/removal, Unicode text, static mixed rich-style ranges and styled substring edits are editable. Behavior template construction, phase timing/static edits, bypass and removal include direct moving/frozen recordings and stitched parents; [recording controls](../skills/camtasia-project/references/behavior-recordings.md) retain native clock origins. |
| Captions and audio | Explicit caption-scene sequencing, closed cue/RTF/global-style editing, recognized-word edits, supported root/Group/stitched clocks, retained audio-file sample offsets and existing dynamic display controls. Native interchange and current audio processing, alignment, fades, ducking and outputs remain separately documented. |
| Cursors and input | Explicit generated cursor point editing on root ordinary/linked video and complete path overrides/restoration on standalone moving recordings, including trimmed 2× clocks and static holds. Explicit left/right authored clicks support generated paths and standalone recordings. Smoothing, click presets, keystroke styles and Window Spotlight retain separate source clocks and output controls. |
| Hotspots | JSON action editing and observed single-scene nested/retimed marker clocks, with actual browser click/seek tests and the Group reload-drift guard. |
| Quizzes and surveys | JSON question/answer/feedback editing, supported owner transfers, four question/survey kinds, SCORM 1.2 and three 2004 edition outputs; fourth-edition session resume. |
| Quick Properties and themes | Reusable Group binding, text/color and media replacement/clear helpers, native theme application and independent duplication, and resource/package contracts. |
| Library and resources | Native archive reuse, names, sorting and copy/move identities; hard-link hazards, collision-safe intake and isolated rendering. Lottie/SVG image inspection and explicit PNG embedding with native relocation checks; fonts and other dependency limits remain explicit. |
| Delivery | Native MP4, MOV codecs, WebM, GIF and audio outputs; Smart Player interactions, captions and quiz packages. Resource and codec limits are documented per specimen. |

Individual helpers retain their named Mac build, format and owner restrictions.
The [feature map](../skills/camtasia-project/references/features.md) and linked
references define each supported representation; the
[helper contract](../skills/camtasia-project/references/helper.md) defines commands.

## Known follow-ups

- Further effect/behavior controls, further animated annotation styles, other caption RTF forms/display controls and additional themed/animated Quick Property controls.
- Additional requested Library lifecycle operations and theme resource combinations.
- Further owner/container/scene clocks in matte, hotspot and quiz editing.
- Further requested SCORM interrupted-session and resume behavior.
- Dependency closure beyond source-bin files, including physical fonts and internal assets.
- Actual companion-app and connected-import handoffs where those apps/services are available.

See [issues #1–#14](https://github.com/jbaruch/agentic-camtasia/issues) for concrete
acceptance criteria and [the release scope](release-plan.md) for maintenance
priority. Completed native matrices are reused; new setting combinations are
checked as requested rather than treated as an open-ended release gate.
