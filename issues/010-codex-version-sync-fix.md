# Issue 010: Codex Manifest Version Sync Fix

**Status: done** — created 2026-06-12, completed 2026-06-12 (status line added 2026-07-05).

## Summary

Fix `register_codex_personal_marketplace.py` so the Codex manifest base version follows the canonical `.claude-plugin/plugin.json` version instead of staying stale after a release. Resolves the open follow-up from issue 009.

## Source

- Type: daily work log
- Link: user conversation (follow-up to issue 009)
- Date: 2026-06-12

## Context

After releasing 0.2.4, the Codex personal marketplace still reported `0.2.3+codex.<ts>`. The registration script's `plugin_version()` read the version directly from `.codex-plugin/plugin.json`, which no release step updates, so the base version never advanced. Commands and skills were correct (symlinked source), but the version string and the Codex cache directory name were stale.

## Completed Today

- Added `canonical_base()` — reads the base version from `.claude-plugin/plugin.json` (single source of truth), falling back to the Codex manifest base when absent.
- Rewrote `plugin_version()` — composes `{canonical_base}+{existing codex suffix}`, preserving the existing `+codex.<ts>` suffix so the result stays deterministic, and writes the synced version back to `.codex-plugin/plugin.json`.
- Verified with `python3 -m unittest tests.test_codex_personal_install` → OK.
- Re-ran registration → Codex manifest and cache now report `0.2.4+codex.20260612135441`.
- Confirmed `release_check.py` still `valid: true`.

## Decisions

- `.claude-plugin/plugin.json` is the single source of truth for the base version.
- Preserve the existing Codex build timestamp suffix rather than regenerating it, to keep registration deterministic and test-stable.
- Accept the cosmetic `ensure_ascii=False` re-encoding of `.codex-plugin/plugin.json` (Korean `defaultPrompt` now stored as UTF-8 literals); JSON value is unchanged.

## Acceptance Criteria

- Codex manifest base version matches `.claude-plugin/plugin.json`. ✅
- `+codex.<ts>` suffix preserved (deterministic). ✅
- `test_codex_personal_install` passes. ✅
- `release_check.py` remains `valid: true`. ✅

## Links

- Fix commit: `9d41324`
- Resolves follow-up in: `issues/009-moduflow-hub-command.md`
- Status: `specs/010-codex-version-sync-fix/status.md`

## Next Command

`product:status`
