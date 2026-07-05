# Version Bump On Done Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Classify a completing issue's commit message into a semver level and bump `.claude-plugin/plugin.json` in the same commit, wired into the `061` auto-commit-push flow.

**Architecture:** Pure-function module `scripts/version_bump.py` — no subprocess/DI needed (unlike `project_sync.py`/`vendor_freshness.py`), since this only reads/writes a local JSON file and classifies a string.

---

### Task 1: RED tests

**Files:** Create `tests/test_version_bump.py`

- [ ] `classify_bump`: `feat:` → minor, `fix:` → patch, `feat!:` → major, `feat(053):` (scoped) → minor, `BREAKING CHANGE:` footer → major, `docs:`/`chore:`/no-prefix/`merge:` → none.
- [ ] `bump_version`: each of `major`/`minor`/`patch`/`none` from a fixed `"0.2.15"` baseline, plus a case bumping `patch` when patch is already non-zero (`"0.2.15"` → `"0.2.16"`) to confirm no truncation bug.
- [ ] `apply_bump`: fixture `plugin.json` (`tempfile.TemporaryDirectory`, matching repo test convention) + a `feat:` message → file updated, returns new version; a `docs:` message → file untouched, returns unchanged version.
- [ ] Run `python3 -m unittest tests.test_version_bump -v` → confirm FAIL.

### Task 2: Implement

**Files:** Create `scripts/version_bump.py`

- [ ] `classify_bump(message)` per spec Requirement 1 — regex on the type/scope prefix, not literal string prefixes (spec Risk #1).
- [ ] `bump_version(version_str, level)` per spec Requirement 2 — parse/reassemble `major.minor.patch`.
- [ ] `apply_bump(plugin_json_path, commit_message)` per spec Requirement 3.
- [ ] Run tests → PASS. Run full suite for regressions.

### Task 3: Wire into 061's flow

**Files:** `docs/host-adapter-guidance.md`

- [ ] Add a step to the "Auto Commit + Push On Issue Done" section: before staging the completion commit, run `apply_bump` against the commit message and include the resulting `.claude-plugin/plugin.json` change in the same commit.

### Task 4: Verify + close

- [ ] `python3 scripts/release_check.py .`
- [ ] Mark issue 063 workflow tasks + Status: done; sync lifecycle.
- [ ] This commit itself is the first one to dogfood the new flow — classify this session's own commit message and bump `.claude-plugin/plugin.json` before committing+pushing.

## Next Command

`product:execute 063-version-bump-on-done`
