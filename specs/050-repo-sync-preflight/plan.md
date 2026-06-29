# Repo Sync Preflight Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a safe repo freshness preflight so `product:sync` and status workflows catch stale branches before reading Git-file artifacts.

**Architecture:** Add a focused `scripts/project_sync.py` helper that shells out to Git through a tiny injectable runner. Keep command docs as the user-facing contract. Tests exercise the helper with a fake runner, avoiding network and real repo mutation.

**Tech Stack:** Python standard library, `unittest`, existing ModuFlow command markdown docs.

---

### Task 1: Add RED Tests For Repo State Detection

**Files:**
- Create: `tests/test_project_sync.py`
- Create later: `scripts/project_sync.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_project_sync.py` with tests for gone upstream, behind default branch, and remote-only issue detection.

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_project_sync -v`

Expected: FAIL because `scripts/project_sync.py` does not exist yet.

### Task 2: Implement `scripts/project_sync.py`

**Files:**
- Create: `scripts/project_sync.py`
- Test: `tests/test_project_sync.py`

- [ ] **Step 1: Implement the minimal helper**

Add importable functions:

- `inspect_repo_sync(path=".", runner=None)`
- `format_recommendations(result)`

The helper should collect branch/upstream/default remote/behind-ahead/worktree/issue visibility and return a JSON-serializable dict.

- [ ] **Step 2: Run focused tests**

Run: `python3 -m unittest tests.test_project_sync -v`

Expected: PASS.

### Task 3: Update Command Docs

**Files:**
- Modify: `commands/product-sync.md`
- Modify: `commands/product-status.md`

- [ ] **Step 1: Document repo preflight in `product:sync`**

Add repo sync before vendor sync, including `git-files` mode explanation and approval-gated fast-forward.

- [ ] **Step 2: Document stale state in `product:status`**

Make stale branch and GitHub Issues vs Git-file issue visibility explicit in the status dashboard contract.

### Task 4: Update ModuFlow Artifacts

**Files:**
- Modify: `workspace/loop-state.json`
- Modify: `workspace/roadmap.md`
- Modify: `workspace/dashboard.md`
- Create: `specs/050-repo-sync-preflight/status.md`

- [ ] **Step 1: Mark Issue 050 active and link next command**

Update workspace state so the loop points at Issue 050.

- [ ] **Step 2: Record verification in status**

Write a concise status artifact after tests pass.

### Task 5: Verify

**Files:**
- All changed files.

- [ ] **Step 1: Run focused tests**

Run: `python3 -m unittest tests.test_project_sync -v`

- [ ] **Step 2: Run full release check**

Run: `python3 scripts/release_check.py .`

Expected: valid true.

## Self-Review

- Spec coverage: all requirements map to Tasks 1-5.
- Placeholder scan: no TBD/TODO placeholders.
- Scope check: focused on repo preflight only; no GitHub Issue mirroring.

## Next Command

`product:execute 050-repo-sync-preflight`
