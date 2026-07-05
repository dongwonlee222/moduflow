# Vendor Freshness Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Detect drift between `vendor.lock.json` pinned GitHub sources and their actual latest commit, and record a reviewed baseline.

**Architecture:** New `scripts/vendor_freshness.py`, same injectable-`runner` DI pattern as `scripts/project_sync.py` (a `(args, cwd) -> CommandResult`-shaped callable), calling `gh api repos/{owner}/{repo}/commits/{pin}` instead of `git`.

---

### Task 1: RED tests

**Files:** Create `tests/test_vendor_freshness.py`

- [ ] Fixture lock data (2-3 github sources, one with `last_synced`, one without).
- [ ] Test: source with no `last_synced` → `drifted: True`.
- [ ] Test: `last_synced.sha` matches fake latest → `drifted: False`.
- [ ] Test: `last_synced.sha` differs → `drifted: True`, both shas present.
- [ ] Test: `gh api` call fails (non-zero) → `error` set, no exception, remaining sources still checked.
- [ ] Test: `local-plugin` type source is skipped entirely (not in results).
- [ ] Test: `--sync` (or a `sync_last_synced()` function) writes `last_synced` back into the lock file for checked sources.
- [ ] Run `python3 -m unittest tests.test_vendor_freshness -v` → confirm FAIL.

### Task 2: Implement

**Files:** Create `scripts/vendor_freshness.py`

- [ ] `run_gh(args, cwd)`: subprocess wrapper for `gh`, same `CommandResult` shape as `project_sync.CommandResult` (import/reuse it, don't redefine).
- [ ] `_parse_owner_repo(url)`: extract `owner/repo` from a `https://github.com/...` URL; return `None` on unrecognized shape.
- [ ] `check_vendor_freshness(lock_path, runner=None)`: implements spec Requirement 1.
- [ ] `sync_last_synced(lock_path, results, runner=None)` or a `--sync` CLI flag: implements spec Requirement 2.
- [ ] CLI `main()`: default prints freshness report; `--sync` also writes.
- [ ] Run tests → PASS. Run full suite for regressions.

### Task 3: Docs

**Files:** `commands/product-sync.md`

- [ ] Add a vendor freshness summary step before the existing vendor pin/pull steps, matching spec Requirement 3.

### Task 4: Verify + apply

- [ ] `python3 scripts/release_check.py .`
- [ ] Run `python3 scripts/vendor_freshness.py . --sync` for real against the live `vendor.lock.json` (per user's explicit approval to refresh the lock markers now).
- [ ] Mark issue 053 workflow tasks + Status: done; sync lifecycle; commit + push per the `061` auto-push policy.

## Next Command

`product:execute 053-vendor-freshness-gate`
