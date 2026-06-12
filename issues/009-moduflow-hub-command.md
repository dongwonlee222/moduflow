# Issue 009: ModuFlow Hub Command And 0.2.4 Release

## Summary

Add a single `/moduflow` hub entry point so users only need to remember one command, release it as `0.2.4`, sync the Codex personal marketplace, and document the entry point in the README.

## Source

- Type: daily work log
- Link: user conversation
- Date: 2026-06-12

## Context

Users could not invoke `/moduflow` because the plugin shipped 35 `product-*` commands but no command file named after the plugin itself. Well-formed Claude plugins (feature-dev, ralph-loop) expose a hub command matching the plugin name as the single thing users must remember. ModuFlow lacked this hub, so the name was unmemorable and `/moduflow` returned "Unknown command."

## Completed Today

- Added `commands/moduflow.md` hub entry point.
  - No-arg: behaves as `product:status` (status + next action + quick command list).
  - With args: routes natural language to the right `product:*` command via the `index` skill (`시작`/`루프`/`상태`/`003 완료` etc).
- Bumped plugin version `0.2.3` to `0.2.4`.
- Passed `release_check.py` (`valid: true`; validate_moduflow, tests, project_doctor, artifacts all OK).
- Copied the hub into the active plugin cache so it works in the current session without reinstall.
- Pushed `main` and moved tag `v0.2.4` to cover the full release.
- Ran `register_codex_personal_marketplace.py` — registered with `INSTALLED_BY_DEFAULT`.
- Documented the `/moduflow` entry point at the top of the README `## Commands` section.

## Decisions

- Keep all 35 `product-*` commands unchanged; add only the hub (minimum change, no compatibility break).
- Do not rename commands or drop the `product-` prefix.
- The hub is a thin router over `skills/index/SKILL.md`, not a replacement for granular commands.

## Follow-Ups

- `register_codex_personal_marketplace.py` does not propagate the base version: the Codex manifest still reads `0.2.3+codex.<ts>` instead of `0.2.4`. Functionality is correct (symlinked source) but the version string is stale. Fix the script to read the base version from `.claude-plugin/plugin.json`.
- Verify `/moduflow` in a fresh Claude session and `@ModuFlow` in a new Codex thread.

## Acceptance Criteria

- `/moduflow` resolves as a command (no longer "Unknown command"). ✅
- No-arg shows status + next action + quick command list. ✅
- Natural-language args route to the correct `product:*` command. ✅
- The 35 `product-*` commands remain available. ✅
- Released as `0.2.4` with passing `release_check.py`. ✅

## Links

- Hub + version commit: `e7eea2c`
- README docs commit: `63ac32b`
- Tag: `v0.2.4`
- Status: `specs/009-moduflow-hub-command/status.md`

## Next Command

`product:status`
