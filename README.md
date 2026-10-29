# Agentic Camtasia

An [Agentic Context Registry](https://github.com/jbaruch/agentic-context-registry)
plugin for editing Camtasia project JSON with Claude Code, Codex and Cursor.

The plugin supplies rules, two skills, a session hook and Python helpers. It
preserves native project data, stages edits separately and verifies changed
output in Camtasia. Its format references come from native Mac saves, rendered
comparisons, public documentation and a separately identified community schema.

## Install

After the first versioned GitHub release is available:

```bash
acr install github:jbaruch/agentic-camtasia --agent codex --agent claude-code --agent cursor --freshness none --non-interactive
acr realize
```

Until then, clone the published source and install its absolute path from a
separate consumer project using an ACR build with local-path support:

```bash
git clone https://github.com/jbaruch/agentic-camtasia.git
# From a separate consumer project:
acr install /absolute/path/to/agentic-camtasia --agent codex --agent claude-code --agent cursor --freshness none --non-interactive
acr realize
```

Local-path installs require a newer ACR build than
0.2.1; the three agent layouts have been exercised with ACR commit `845af87`.

Python 3.11+ is required. Core helpers use the standard library. Native
save/reopen/export checks require a licensed matching Camtasia installation on
macOS. Schema auditing uses the optional pinned `jsonschema` dependency.

## What it does

| Area | Support |
| --- | --- |
| Project safety | Inspect and validate structure, hash source files, stage candidates, compare changes, apply with baseline/ownership checks and backups. |
| Animations | Author and remove visual intervals, set easing, create empty markers and edit explicit Motion Path points and orientation. |
| Effects and mattes | Edit existing static visual effects; author supported media/track mattes, intensity curves, bypass and removal. |
| Transitions | Construct Fade transitions and edit existing duration/scalar controls or remove transitions, preserving endpoint clocks and audio. |
| Interactivity | Author and edit supported hotspots, quizzes, surveys, feedback and owner/clock transfers. |
| Feature references | Captions, audio, annotations, behaviors, cursor/click effects, Quick Properties, themes, Library assets, Lottie/SVG dependencies and delivery formats. |
| Native checks | Read-only process health and a backed-up save/reopen adapter with separate rendering status. |

Example requests:

- “Inspect this project and find missing media.”
- “Add a zoom while preserving narration and cleanup effects.”
- “Correct these dynamic captions and keep their word timing.”
- “Add a Fade at this cut.”
- “Work out how this Camtasia build stores an unfamiliar effect.”

## Workflow

1. Inspect the saved project and identify clips by ID and role.
2. Read the relevant native feature contract and stage a separate candidate.
3. Validate and diff it; apply only to a saved, closed project with its baseline hash.
4. Reopen in the matching editor, inspect for repairs and verify the changed output.

```bash
python3 -B skills/camtasia-project/scripts/project.py inspect "My Film.cmproj"
python3 -B skills/camtasia-project/scripts/project.py source-manifest "My Film.cmproj"
python3 -B skills/camtasia-project/scripts/project.py validate candidate.json --media-root "My Film.cmproj"
python3 -B skills/camtasia-project/scripts/project.py diff "My Film.cmproj" candidate.json
```

The [helper contract](skills/camtasia-project/references/helper.md) documents all
editing commands. The [feature map](skills/camtasia-project/references/features.md)
links each representation to its native evidence and limitations.

## Plugin contents

| Artifact | Purpose |
| --- | --- |
| [Project safety](rules/camtasia-project-safety.md) | Ownership, closed-project writes, backups, preservation and resource dependencies. |
| [Timing](rules/camtasia-timing.md) | Rational values and timeline/source/nested clock domains. |
| [Feature evidence](rules/camtasia-feature-evidence.md) | JSON-first editing and versioned native discovery. |
| [Validation](rules/camtasia-validation.md) | Structural checks, native output and handoff requirements. |
| [Camtasia project skill](skills/camtasia-project/SKILL.md) | Inspect, create, edit, relink and validate projects. |
| [Camtasia feature skill](skills/camtasia-feature/SKILL.md) | Investigate unfamiliar serialization through documentation and native examples. |
| [Session hook](hooks/session_context.py) | Read-only project-context reminder for the installed agent. |

## Scope and limits

Native contracts target Mac 2025.0.3/format 9 and Mac 2026.2.4/format 10; individual
helpers retain their exact build/owner restrictions. Structural validation and
successful saves do not establish rendered support. Source-bin closure does not
establish fonts, installation assets or internal SVG/Lottie dependencies.

No complete official project JSON schema is asserted. Community-schema omissions
and native compatibility corrections remain separate. Vendor media, fonts,
presets, shaders and private recordings are excluded from this repository.

The initial feature scope is frozen. Known gaps are tracked as
[post-release enhancements](https://github.com/jbaruch/agentic-camtasia/issues?q=is%3Aissue+is%3Aopen+label%3Aenhancement)
and will be added as real projects need them. See the
[coverage summary](docs/mac-feature-coverage.md) and
[verification guide](docs/verification.md).

## Development

With `uv`, `acr`, `ruff` and `pyright` installed:

```bash
bash scripts/check.sh
```

This runs locked verification dependencies, lint/format checks, Pyright, generated
fixture tests and ACR distribution validation. Before committing, run
`gitleaks git --pre-commit --staged --redact --no-banner`.
Native tests use disposable projects and serialized editor exports. Completed
working media, logs and audit records are deleted after findings enter the
references and tests. `tessl.json` configures the author's coding policy; this
plugin is distributed through `agent-plugin.yaml`.
