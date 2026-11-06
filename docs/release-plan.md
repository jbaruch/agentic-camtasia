# Release plan

The initial 0.1 scope was frozen on 2026-10-29 and version 0.1.0 was published
on 2026-11-01. On 2026-11-05 the operator requested continued feature shipping,
with a patch or minor release after each feature. The repository is
[jbaruch/agentic-camtasia](https://github.com/jbaruch/agentic-camtasia).

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
| [#2](https://github.com/jbaruch/agentic-camtasia/issues/2) | Native-template constructors in 0.3.0 and LUT resource/range/easing controls in 0.4.0; linear typed-double effect curves in 0.5.0; nonlinear/point and other effect-specific controls remain. |
| [#3](https://github.com/jbaruch/agentic-camtasia/issues/3) | Native-template behavior construction, phase timing/static edits, bypass and removal shipped in 0.6.0. |
| [#4](https://github.com/jbaruch/agentic-camtasia/issues/4) | Standalone native-template constructors and existing shape/uniform text controls shipped in 0.7.0. |
| [#5](https://github.com/jbaruch/agentic-camtasia/issues/5) | Closed cue authoring, recognized-word corrections, root clock mapping/retiming and existing dynamic display controls shipped in 0.8.0. |
| [#6](https://github.com/jbaruch/agentic-camtasia/issues/6) | Group binding/value edits, linked text/color/media controls and native media replacement/clear shipped in 0.9.0. |
| [#7](https://github.com/jbaruch/agentic-camtasia/issues/7) | Independent native theme duplication, UUID/label restoration and separate logo resources verified/documented in 0.9.1. |
| [#8](https://github.com/jbaruch/agentic-camtasia/issues/8) | Nonlinear intensity intervals shipped in 0.10.0 and moving/frozen/stitched owners in 0.11.0; linked recording mirrors, point forms and matte interactions remain. |
| [#9](https://github.com/jbaruch/agentic-camtasia/issues/9) | Additional hotspot owners and scene clocks |
| [#10](https://github.com/jbaruch/agentic-camtasia/issues/10) | Additional quiz owners and destination clocks |
| [#11](https://github.com/jbaruch/agentic-camtasia/issues/11) | Further SCORM resume and interrupted sessions |
| [#12](https://github.com/jbaruch/agentic-camtasia/issues/12) | Resource closure beyond source-bin files |
| [#13](https://github.com/jbaruch/agentic-camtasia/issues/13) | Companion applications and connected imports |
| [#14](https://github.com/jbaruch/agentic-camtasia/issues/14) | Remaining Library lifecycle operations |

Use the distributed feature references as the contract for existing support.
Historical native observations describe their exercised build and specimen;
they do not require retaining test movies or repeating completed matrices.
