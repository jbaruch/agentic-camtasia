# Verification guide

The plugin combines deterministic helper tests with native Camtasia observations.
The distributed feature references carry the observed serialization and output
contracts. Completed test movies, projects, screenshots and audit logs are deleted
once their findings are incorporated.

## Automated checks

```bash
bash scripts/check.sh
```

The gate runs locked optional verification dependencies, Ruff lint/format,
Pyright, generated-fixture unit tests and ACR package validation. The initial
release candidate passes 360 core tests and selects 41 distribution files.
Tests cover preservation, exact clocks, refusals, stale baselines, ownership,
backups, schema boundaries and native-process contracts.

Core helpers use Python's standard library. `jsonschema` is an optional pinned
verification dependency. Binary/native vendor fixtures are excluded from the
package; deterministic test fixtures are generated in the test suite.

## Installed consumers

An isolated ACR build at commit `845af87cdb1c867fb1afb3012d82c1cfdfadfb7c` has
installed and realized the package into Codex, Claude Code and Cursor layouts.
Checks cover rebased references, installed script/reference bytes, hooks, state
consistency and actual helper commands from installed paths. The most recent
transition check executes eight native controls per layout, with thirty CLI
commands across the three layouts.

The globally installed ACR 0.2.1 supports GitHub sources; local-path acceptance
uses the isolated build and does not replace the global CLI.

## Native evidence

Native findings target Mac 2025.0.3/format 9 or Mac 2026.2.4/format 10, as named
by each contract. Save/reopen and actual rendering are verified separately.
Independent reopened exports are compared as decoded picture/audio streams,
with sampled visual inspection and appropriate audio or player checks.

| Area | Authoritative feature contract |
| --- | --- |
| Curves, animation markers, easing and Motion Paths | [Animations](../skills/camtasia-project/references/animations.md) |
| Transition presets, boundaries and JSON helper | [Transitions](../skills/camtasia-project/references/transitions.md) |
| Effects, mattes, hotspots and quiz delivery | [Advanced features](../skills/camtasia-project/references/advanced-features.md) |
| Captions and recognition/display clocks | [Captions](../skills/camtasia-project/references/captions.md) |
| Audio processing and delivery | [Audio](../skills/camtasia-project/references/audio.md) |
| Recorded pointer, clicks, keystrokes and windows | [Cursors](../skills/camtasia-project/references/cursors.md) |
| Group bindings, themes and replacements | [Quick Properties](../skills/camtasia-project/references/quick-properties.md), [media properties](../skills/camtasia-project/references/media-quick-properties.md) |
| Library resources, identity and archive reuse | [Library](../skills/camtasia-project/references/library.md) |
| Embedded/external animation resources | [Lottie](../skills/camtasia-project/references/lottie.md), [media](../skills/camtasia-project/references/media.md) |
| Current builds and output formats | [Mac versions](../skills/camtasia-project/references/mac-versions.md), [delivery](../skills/camtasia-project/references/delivery.md) |

Use the [native verification procedure](../skills/camtasia-project/references/native-verification.md)
for exact app selection, health preflight, backed-up save/reopen, serialized
exports and failure recovery. The proprietary AppleScript invocation has the
named platform-bound testing carve-out; its Python boundary remains tested.

## Interpretation

- Partial structural or schema checks do not prove native rendering.
- Raw community errors and exact-build profile corrections stay separate.
- Source-file hashes do not establish all font, installation or internal-resource dependencies.
- Native evidence establishes the exercised specimen, not every parameter combination.
- Missing functionality is tracked in the [post-release backlog](https://github.com/jbaruch/agentic-camtasia/issues).
