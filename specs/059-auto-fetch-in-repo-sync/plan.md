# Auto Fetch In Repo Sync Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `inspect_repo_sync()` fetch remote refs itself, with a bounded timeout and a soft-fail path, so `product:sync`/`product:status` never compare against a stale local Git cache without saying so.

**Architecture:** Add one `git fetch` call as the first Git call inside `inspect_repo_sync()` (`scripts/project_sync.py`), through the same injectable `runner` used by every other Git call in that function. Catch `subprocess.TimeoutExpired` in `run_command` so a hang can't propagate as an exception. Surface the outcome as two new result fields (`fetched`, `fetch_warning`) rather than raising or silently continuing.

**Tech Stack:** Python standard library (`subprocess`), `unittest`, existing `FakeRunner` test harness in `tests/test_project_sync.py`.

---

### Task 1: Add RED Tests For Fetch Outcomes

**Files:**
- Modify: `tests/test_project_sync.py`
- Modify later: `scripts/project_sync.py`

- [ ] **Step 1: Write three failing tests**

Add to `ProjectSyncTests`:
- `test_fetch_success_sets_fetched_true`: `FakeRunner` returns exit 0 for `("git", "fetch", "--quiet")`; assert `result["fetched"] is True` and `result["fetch_warning"] is None`.
- `test_fetch_failure_sets_warning`: `FakeRunner` returns a non-zero `CommandResult` (e.g. exit 1, stderr `"fatal: unable to access ..."`) for the fetch call; assert `result["fetched"] is False`, `fetch_warning` contains the stderr text, and `branch`/`upstream`/`default_remote` are still populated from the (already-configured) `FakeRunner` responses.
- `test_fetch_timeout_sets_warning`: `FakeRunner` raises `subprocess.TimeoutExpired` for the fetch call (extend `FakeRunner.__call__` to raise when the response value is the sentinel, or add a `TimeoutRunner` helper); assert `result["fetched"] is False`, `fetch_warning` mentions timeout, and no exception escapes `inspect_repo_sync`.

- [ ] **Step 2: Run and confirm RED**

Run: `python3 -m unittest tests.test_project_sync -v`

Expected: the three new tests FAIL (KeyError on `fetched`/`fetch_warning`, or `AttributeError`/`TypeError` since the fetch call and timeout handling don't exist yet).

### Task 2: Implement Fetch + Timeout Handling

**Files:**
- Modify: `scripts/project_sync.py`

- [ ] **Step 1: Add timeout handling to `run_command`**

`run_command` currently calls `subprocess.run(..., check=False)` with no timeout. Add an optional `timeout` kwarg (default `None`, so existing calls are unaffected) and catch `subprocess.TimeoutExpired`, returning a `CommandResult` with a distinguishable returncode (e.g. `124`, matching the shell convention for timeout) and a message in `stderr` (e.g. `f"timed out after {timeout}s"`).

- [ ] **Step 2: Call fetch first inside `inspect_repo_sync`**

Right after the `is_repo` check (before the branch/upstream reads), call:

```python
fetch_result = _run(runner, ["git", "fetch", "--quiet"], cwd)
```

Note: the `runner` protocol is `(args, cwd) -> CommandResult`, so `timeout` can't be threaded through the existing signature without changing every call site. Two options — pick the simpler one at implementation time:
(a) give `run_command` a module-level default timeout (5s) applied only when the first arg is `"fetch"`, or
(b) add a `timeout` kwarg to `run_command` and have `_run`/`runner` pass it through only for this call, defaulting to `None` elsewhere.
Prefer (a): it keeps the `runner` signature stable for every existing test and call site, and only `run_command` (the real implementation) needs to know fetch gets a timeout — `FakeRunner` in tests doesn't call `subprocess` at all, so it's unaffected either way.

Set `GIT_TERMINAL_PROMPT=0` in the subprocess environment for this call (or all `run_command` calls) so a credential prompt fails fast instead of hanging — per spec Risk #3.

- [ ] **Step 3: Derive `fetched`/`fetch_warning` and add to result dict**

```python
fetched = fetch_result.returncode == 0
fetch_warning = None
if not fetched:
    stderr = (fetch_result.stderr or "").strip()
    fetch_warning = f"git fetch failed: {stderr}" if stderr else "git fetch failed"
```

Add `"fetched": fetched, "fetch_warning": fetch_warning` to the `result` dict before `format_recommendations(result)` is called (recommendations need to see it in the next step).

- [ ] **Step 4: Prepend a recommendation when `fetched` is false**

In `format_recommendations`, before the existing checks, add:

```python
if result.get("fetched") is False:
    recommendations.append(
        f"Could not fetch from the remote ({result.get('fetch_warning')}); freshness numbers below reflect the last local fetch, not the current remote."
    )
```

- [ ] **Step 5: Run focused tests**

Run: `python3 -m unittest tests.test_project_sync -v`

Expected: PASS, including the three new tests and all pre-existing ones (fetch defaults to skipped/no-op in `FakeRunner`-driven tests unless a test explicitly configures the fetch key — existing tests must add a passing fetch response or the `FakeRunner`'s "unexpected command" fallback will now trigger for the new `("git", "fetch", "--quiet")` call. Add a default passing fetch entry to each existing test's `FakeRunner` responses dict as part of this step).

### Task 3: Update Command Docs

**Files:**
- Modify: `commands/product-sync.md`
- Modify: `commands/product-status.md`

- [ ] **Step 1: `product:sync` — describe the fetch as automatic**

Remove/replace any instruction implying a manual `git fetch` precedes the freshness check; state that `inspect_repo_sync()` fetches internally with a 5s timeout and degrades to cached refs on failure.

- [ ] **Step 2: `product:status` — same update**

`product-status.md`'s step 1 currently says "Run a non-destructive `git fetch` first, then compare..." — update it to say the fetch now happens inside the repo-sync helper automatically; the manual instruction is only needed for hosts that call Git directly instead of through `project_sync.py`.

### Task 4: Verify

**Files:**
- All changed files.

- [ ] **Step 1: Run focused tests**

Run: `python3 -m unittest tests.test_project_sync -v`

- [ ] **Step 2: Run full release check**

Run: `python3 scripts/release_check.py .`

Expected: `valid: true`.

- [ ] **Step 3: Mark issue 059 workflow tasks complete and update state**

Update `issues/059-auto-fetch-in-repo-sync.md` Workflow Tasks (plan, execute) and Status line; run `python3 scripts/project_lifecycle.py . --sync`.

## Self-Review

- Spec coverage: Requirements 1-4 → Task 2; Requirement 5 → Task 2 Step 4; Requirement 6 → Task 3; Requirement 7 → Task 1.
- Placeholder scan: no TBD/TODO placeholders.
- Scope check: focused on the fetch step and its failure modes; no `git pull`/merge/rebase logic added, matching the spec's Non-Goals.

## Next Command

`product:execute 059-auto-fetch-in-repo-sync`
