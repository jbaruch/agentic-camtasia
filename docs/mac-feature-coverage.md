# Mac feature coverage

Feature scope is frozen for v0.1 at the user's request. This summary distinguishes
reusable JSON editing from broader native feature knowledge. Missing capabilities
are [post-release issues](https://github.com/jbaruch/agentic-camtasia/issues);
they are added when a real project needs them.

## Initial package

| Family | Reusable editing or documented native support |
| --- | --- |
| Projects and sources | Inspection, IDs/references, partial validation, exact numeric handling, source manifests, candidate staging, guarded writes and backups. |
| Animation | Visual intervals, easing, removal and empty markers; explicit Motion Path points, orientation, bypass and removal on verified visual owners, including frozen/stitched forms. |
| Transitions | Root-track Fade construction and existing scalar/duration/removal editing. Native references cover all 179 current palette presets, one/shared edges, short clips, source skips, gaps, retiming and preroll. |
| Effects and mattes | Existing static visual effect edits; supported track/media matte constructors, modes, intensity curves and lifecycle. Native references cover current visual, LUT and gesture families. |
| Annotations and behaviors | Native specimens for all 134 annotation entries and thirteen behaviors, with text/UTF-8, shape, arrow, modifier and phase contracts. General authoring helpers are follow-ups. |
| Captions and audio | Native closed/dynamic caption structures, word/style edits, retiming and interchange; current audio presets, processing, alignment, fades, ducking and output formats. |
| Cursors and input | Native recorded/generated paths, smoothing, click presets, keystroke styles and Window Spotlight, with source clocks and output controls. |
| Hotspots | JSON action editing and observed single-scene nested/retimed marker clocks, with actual browser click/seek tests and the Group reload-drift guard. |
| Quizzes and surveys | JSON question/answer/feedback editing, supported owner transfers, four question/survey kinds, SCORM 1.2 and three 2004 edition outputs; fourth-edition session resume. |
| Quick Properties and themes | Native color/text/typography/media binding lifecycles, linking, replacement/clear, theme application and resource/package contracts. |
| Library and resources | Native archive reuse, names, sorting and copy/move identities; hard-link hazards, collision-safe intake and isolated rendering. Lottie/SVG dependency and relocation findings remain explicit. |
| Delivery | Native MP4, MOV codecs, WebM, GIF and audio outputs; Smart Player interactions, captions and quiz packages. Resource and codec limits are documented per specimen. |

Individual helpers retain their named Mac build, format and owner restrictions.
The [feature map](../skills/camtasia-project/references/features.md) and linked
references define each supported representation; the
[helper contract](../skills/camtasia-project/references/helper.md) defines commands.

## Known follow-ups

- General transition/effect/behavior/annotation/caption and Quick Property authoring.
- Theme duplication and additional requested Library lifecycle operations.
- Further owner/container/scene clocks in matte, hotspot and quiz editing.
- Further requested SCORM interrupted-session and resume behavior.
- Dependency closure beyond source-bin files, including physical fonts and internal assets.
- Actual companion-app and connected-import handoffs where those apps/services are available.

See [issues #1–#14](https://github.com/jbaruch/agentic-camtasia/issues) for concrete
acceptance criteria and [the release scope](release-plan.md) for maintenance
priority. Completed native matrices are reused; new setting combinations are
checked as requested rather than treated as an open-ended release gate.
