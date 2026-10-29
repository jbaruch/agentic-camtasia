

# Agent Rules <!-- tessl-managed -->

@.tessl/RULES.md follow the [instructions](.tessl/RULES.md)

## Release scope

- Feature scope for v0.1 is frozen at the user's request. Converge on shipping.
- Follow [the release plan](docs/release-plan.md) for remaining release work.
- Known feature gaps are post-release issues in `jbaruch/agentic-camtasia`; implement them when requested by a real project.
- Do not expand native feature or parameter matrices as a release prerequisite.

## Working storage

- Keep only current disposable test inputs, the matching Camtasia app and the schema cache under `build/native-verification`.
- Delete completed test projects, media, exports, screenshots, logs and audit records after incorporating the behavior into the plugin and tests.
- Do not maintain or recreate historical verification archives.
- Check free disk space and working-directory size before preparing each native test batch.
