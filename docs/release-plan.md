# Initial release plan

The user froze feature scope on 2026-10-29: ship the existing coverage and add
missing capabilities as real projects require them. The target package version
is 0.1.0. The repository is
[jbaruch/agentic-camtasia](https://github.com/jbaruch/agentic-camtasia).

## Remaining release work

- Publish the source repository as requested by the user. Keep native media,
  vendor resources, machine diagnostics and agent installer state local.
- Prepare release automation and review for versioned package distribution.
- Select a license before advertising a particular reuse license.
- Run the existing deterministic gates and a clean installed-consumer acceptance
  check against the final release candidate. The latest code gate has 360 tests
  and 41 clean distribution files; these counts are observations, not exit criteria.
- Prepare the reviewable release and report any actual release blocker.

## Post-release feature backlog

All fourteen issues are enhancements and explicitly do not block v0.1.

| Issue | Capability |
| --- | --- |
| [#1](https://github.com/jbaruch/agentic-camtasia/issues/1) | Transition preset constructors |
| [#2](https://github.com/jbaruch/agentic-camtasia/issues/2) | Visual-effect constructors and animated controls |
| [#3](https://github.com/jbaruch/agentic-camtasia/issues/3) | Behavior authoring and phase editing |
| [#4](https://github.com/jbaruch/agentic-camtasia/issues/4) | Annotation constructors and shape/text controls |
| [#5](https://github.com/jbaruch/agentic-camtasia/issues/5) | Closed and dynamic caption authoring |
| [#6](https://github.com/jbaruch/agentic-camtasia/issues/6) | Quick Property bindings and media replacement |
| [#7](https://github.com/jbaruch/agentic-camtasia/issues/7) | Independent theme duplication |
| [#8](https://github.com/jbaruch/agentic-camtasia/issues/8) | Additional matte owners and curves |
| [#9](https://github.com/jbaruch/agentic-camtasia/issues/9) | Additional hotspot owners and scene clocks |
| [#10](https://github.com/jbaruch/agentic-camtasia/issues/10) | Additional quiz owners and destination clocks |
| [#11](https://github.com/jbaruch/agentic-camtasia/issues/11) | Further SCORM resume and interrupted sessions |
| [#12](https://github.com/jbaruch/agentic-camtasia/issues/12) | Resource closure beyond source-bin files |
| [#13](https://github.com/jbaruch/agentic-camtasia/issues/13) | Companion applications and connected imports |
| [#14](https://github.com/jbaruch/agentic-camtasia/issues/14) | Remaining Library lifecycle operations |

Use the distributed feature references as the contract for existing support.
Historical native observations describe their exercised build and specimen;
they do not require retaining test movies or repeating completed matrices.
