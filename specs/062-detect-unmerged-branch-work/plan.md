# Detect Unmerged Branch Work Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Extend `inspect_repo_sync()` to detect remote branches with `Status: done` issues that aren't `done` on `origin/main`.

**Architecture:** New function `find_unmerged_branch_work(runner, cwd, default_remote)` in `scripts/project_sync.py`, using the same injectable `runner` and `_run`/`CommandResult` plumbing as every other check in that file. Reuses `project_lifecycle._issue_status` for parsing instead of a second regex.

---

### Task 1: RED tests

**Files:** Modify `tests/test_project_sync.py`

- [ ] Test: branch ahead of default with a `done` issue not `done` on default → reported.
- [ ] Test: branch ahead of default, no status-differing issues → not reported.
- [ ] Test: no branches ahead of default → `unmerged_branch_work == []`, no extra recommendation.
- [ ] Run `python3 -m unittest tests.test_project_sync -v` → confirm FAIL (function doesn't exist yet).

### Task 2: Implement

**Files:** Modify `scripts/project_sync.py`

- [ ] Add `_list_remote_branches`, `_issue_ids_in_ref`, `_status_at_ref`, `find_unmerged_branch_work` (per spec Requirement 1).
- [ ] Import `_issue_status` from `project_lifecycle` (same-package import, not a copy).
- [ ] Call `find_unmerged_branch_work` from `inspect_repo_sync`, add `unmerged_branch_work` to the result dict.
- [ ] Add the recommendation line in `format_recommendations`.
- [ ] Run tests → confirm PASS. Run full suite (`python3 -m unittest discover -s tests`) for regressions.

### Task 3: Docs

**Files:** `commands/product-sync.md`, `commands/product-status.md`

- [ ] Mention unmerged-branch-work detection alongside the existing repo-sync preflight bullets.

### Task 4: Verify + close

- [ ] `python3 scripts/release_check.py .`
- [ ] Mark issue 062 workflow tasks + Status: done; sync lifecycle; commit + push per the `061` auto-push policy.

## Next Command

`product:execute 062-detect-unmerged-branch-work`
