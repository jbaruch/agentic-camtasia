# Release plan

The initial 0.1 scope was frozen on 2026-10-29 and version 0.1.0 was published
on 2026-11-01. On 2026-11-05 the operator requested continued feature shipping,
with a patch or minor release after each feature. The repository is
[jbaruch/agentic-camtasia](https://github.com/jbaruch/agentic-camtasia).

On 2026-11-06 the operator defined the final release as **1.0.0, feature-complete**
across all remaining gaps in this plan, including closed/deferred issue families.
The [feature-completion plan](feature-completion-plan.md) tracks that requirement.
An issue's closed/deferred state alone does not establish 1.0 completion.

The source repository and feature backlog are public. ACR 0.2.1 resolves GitHub
installs from versioned package releases.

## Subsequent releases

- Keep native media, vendor resources, machine diagnostics and agent installer
  state local when preparing subsequent updates.
- Ship each feature separately through a reviewed PR and a semver bump in both
  manifests and the Python lockfile's root-package entry.
- Run the deterministic CI gates before tag-triggered ACR publication. Confirm
  the resulting GitHub release assets and an installed-consumer acceptance check.
- Apply the temporary Claude review waiver recorded in `AGENTS.md`; retain the
  current-head Codex policy review.
- Run the existing deterministic gates and a clean installed-consumer acceptance
  check against each release candidate. Counts are observations, not exit criteria.
- Keep the MIT license in the source repository.

## Post-release feature backlog

All fourteen issues are enhancements and explicitly do not block v0.1.

| Issue | Capability |
| --- | --- |
| [#1](https://github.com/jbaruch/agentic-camtasia/issues/1) | Transition preset constructors shipped in 0.2.0. |
| [#2](https://github.com/jbaruch/agentic-camtasia/issues/2) | Native-template constructors in 0.3.0 and LUT resource/range/easing controls in 0.4.0; linear typed-double effect curves in 0.5.0 and nonlinear intervals in 0.13.0; recording/frozen/stitched effect curves in 0.18.0 and native-template construction/lifecycle in 0.19.0; explicit created-cursor point editing in 0.23.0 and standalone recorded-cursor overrides/restoration in 0.24.0; explicit generated/recorded cursor click authoring in 0.25.0; root linked moving recording effect constructors/lifecycle and complete timed-template copying in 0.27.0, plus interval-curve authoring/clearing in 0.28.0; Group-contained linked moving recording construction/lifecycle and timed-template copying in 0.30.0, plus interval-curve authoring/clearing in 0.31.0. Other point and effect-specific controls remain. |
| [#3](https://github.com/jbaruch/agentic-camtasia/issues/3) | Native-template behavior construction, phase timing/static edits, bypass and removal shipped in 0.6.0; direct moving/frozen recordings and stitched parents in 0.20.0; root linked moving recording mirrors with source/timeline reset preservation in 0.29.0; Group-contained linked moving recording construction, phase editing and lifecycle in 0.33.0; selected native phase-style copying, including activation/None and reset preservation, in 0.34.0. Further linked forms and preset-specific controls retain separate contracts. |
| [#4](https://github.com/jbaruch/agentic-camtasia/issues/4) | Standalone native-template constructors and existing shape/uniform text controls shipped in 0.7.0; static mixed rich-style ranges in 0.21.0; mixed-style substring replacement, insertion and deletion in 0.22.0. Discrete timed rich-style steps and effective-state clearing ship in 0.36.0. Native sizing/ligature switches ship in 0.37.0 and static region strength/color/inversion edits in 0.38.0. Standalone keystroke key/style/visibility edits with explicit geometry ship in 0.39.0; Group-contained keystroke edits and the native Group sizing workflow ship in 0.40.0. Standalone Sketch Motion drawing-time and stroke controls ship in 0.41.0. Group-contained and trimmed/speed-adjusted Sketch Motion controls ship in 0.42.0. Root and Group-contained text wrapping and outline placement, including retained timed rich states, ship in 0.43.0. Continuous text-outline intervals, coupled easing/removal and Group/trim/speed clocks ship in 0.44.0. Remaining native shape/text controls retain separate contracts. |
| [#5](https://github.com/jbaruch/agentic-camtasia/issues/5) | Closed cue authoring, recognized-word corrections, root clock mapping/retiming and existing dynamic display controls shipped in 0.8.0. |
| [#6](https://github.com/jbaruch/agentic-camtasia/issues/6) | Group binding/value edits, linked text/color/media controls and native media replacement/clear shipped in 0.9.0. |
| [#7](https://github.com/jbaruch/agentic-camtasia/issues/7) | Independent native theme duplication, UUID/label restoration and separate logo resources verified/documented in 0.9.1. |
| [#8](https://github.com/jbaruch/agentic-camtasia/issues/8) | Nonlinear intensity intervals shipped in 0.10.0 and moving/frozen/stitched owners in 0.11.0; atomic media/track compositions with Group/root interaction controls in 0.12.0; root linked moving recording mattes with recorded-audio preservation in 0.26.0; Group-contained linked moving recording lifecycle/intensity curves and mixed track controls in 0.32.0. Native linked-recording frame extensions, stitched-parent mattes and unstitched silent holds ship in 0.35.0. Further containers and point forms remain. |
| [#9](https://github.com/jbaruch/agentic-camtasia/issues/9) | Standalone frozen-recording and stitched-parent hotspots with marker clocks shipped in 0.14.0. Linked variants, placeholders and additional scene clocks remain. |
| [#10](https://github.com/jbaruch/agentic-camtasia/issues/10) | Standalone frozen-recording and stitched-parent quiz authoring, editing, retiming and owner transfer shipped in 0.15.0. Linked variants, audio/placeholders, additional destinations and scene clocks remain. |
| [#11](https://github.com/jbaruch/agentic-camtasia/issues/11) | Further SCORM resume and interrupted sessions |
| [#12](https://github.com/jbaruch/agentic-camtasia/issues/12) | Lottie image inventory/embedding shipped in 0.16.0 and SVG image inspection/byte-preserving PNG embedding in 0.17.0; general packing, fonts and other render-resource closure remain. |
| [#13](https://github.com/jbaruch/agentic-camtasia/issues/13) | Companion applications and connected imports |
| [#14](https://github.com/jbaruch/agentic-camtasia/issues/14) | Remaining Library lifecycle operations |

Use the distributed feature references as the contract for existing support.
Historical native observations describe their exercised build and specimen;
they do not require retaining test movies or repeating completed matrices.
