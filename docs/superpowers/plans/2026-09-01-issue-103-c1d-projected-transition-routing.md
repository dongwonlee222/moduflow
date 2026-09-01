# Issue 103 C1d Projected Transition Routing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans and superpowers:test-driven-development inline task-by-task. Do not use subagents for this slice.

**Goal:** Derive lifecycle transition and loop-update state, dashboard, loop cursor, phase, and next command from one shared evaluation of the projected issue set.

**Architecture:** Generalize the existing reconcile-only `_projected_issue_evaluation()` branch to `start`, `update`, `pause`, `resume`, `complete`, and update intents carrying `loop_change`. Canonical issue/state/loop/dashboard sources continue through descriptor-based no-follow reads; the shared issue evaluator may inspect only configured spec artifact paths to determine phase. A full loop-state update preserves operator-owned fields but has `active_issue_id`, `phase`, and `next_command` overwritten by the projected lifecycle route.

**Tech Stack:** Python 3 standard library, existing shared issue evaluator, Issue 103 pure renderers and transaction planner, `unittest`, `unittest.mock`.

## Global Constraints

- Work only in `/Users/dongwon.lee/.config/superpowers/worktrees/moduflow/110-project-operation-capability-enforcement` on `codex/103-atomic-lifecycle-state-transaction`.
- Preserve every existing untracked plan; use `apply_patch`; stage only named C1d files.
- Follow RED/GREEN TDD. Do not modify production code before observing the named routing tests fail for the current fixed `execute/select` branch.
- Preserve the stable transaction schema, target order, action mapping, old idempotency hashes without `loop_change`, and public adapter signatures.
- Canonical target bytes must still be read exactly once through `_read_regular_file_no_follow`; `Path.read_bytes()` and `Path.is_symlink()` remain forbidden in planning.
- `Path.is_file()` is permitted only for configured spec artifact coverage used by `build_artifact_index()`, never for issue/state/loop/dashboard/index/roadmap/evidence target rechecks.
- Leave `production-version` projected routing for C2; do not begin C2, D1, D2, full discovery, release checks, merge, push, or cleanup.

---

### Task 1: Projected Lifecycle Routing Contract

**Files:**
- Modify: `tests/test_project_lifecycle_transaction.py` in `TransactionPlanningTests`

**Interfaces:**
- Consumes: `plan_lifecycle_transaction(root, LifecycleIntent, *, project_context, clock)`.
- Produces: literal expected state/dashboard/loop routes for projected lifecycle actions.

- [ ] **Step 1: Write a RED transition route test.** For an issue with only `spec.md`, assert `start` projects `active_issue=BIZ-103`, `phase=spec`, and `next_command=product:plan BIZ-103`; the current fixed branch must fail with `phase=execute`.
- [ ] **Step 2: Extend the literal action matrix.** Cover `update`, `pause`, and `resume` preserving a uniquely active issue and its evaluated route; cover `complete` selecting no active issue and `product:status` after the projected issue becomes done.
- [ ] **Step 3: Add a second-active safety case.** Starting a backlog issue while another issue is active must project no unique active cursor so projected validation can reject the lifecycle conflict; it must never silently select either issue.
- [ ] **Step 4: Run the named tests and confirm RED.** Run `python3 -m unittest tests.test_project_lifecycle_transaction.TransactionPlanningTests.test_transitions_derive_routes_from_projected_issue_evaluation -q`; expected failure is `execute != spec`.

### Task 2: Loop Update Routing Ownership

**Files:**
- Modify: `scripts/project_loop.py`
- Modify: `scripts/project_lifecycle_transaction.py`
- Modify: `tests/test_project_lifecycle_transaction.py`
- Modify: `tests/test_project_loop.py`

**Interfaces:**
- Produces: `render_loop_state_update(loop_bytes, state, *, active_issue, phase, next_command) -> bytes`.

- [ ] **Step 1: Write a RED stale-loop-route test.** Submit `loop_change` containing `active_issue_id=BIZ-STALE`, `phase=release`, and `next_command=product:release BIZ-STALE` while projected issue `BIZ-103` is active at `spec`; assert rendered loop uses `BIZ-103`, `spec`, and `product:plan BIZ-103` while preserving `last_action` and attempts metadata.
- [ ] **Step 2: Run the named test and confirm RED.** The current full-state renderer must retain the stale values and fail.
- [ ] **Step 3: Add keyword-only routing inputs to the pure renderer.** Normalize the supplied state, then set `active_issue_id`, ensure the active ID is present in `issue_ids`, set `phase`, and set `next_command`; when no unique active issue exists, clear the active cursor and use `select`/`product:status`.
- [ ] **Step 4: Generalize shared evaluation.** Use `_projected_issue_evaluation()` for lifecycle actions other than `production-version`; remove the fixed transition `execute/select` branch; pass its literal route to state, dashboard, lifecycle loop projection, and full loop update rendering.
- [ ] **Step 5: Keep production routing deferred.** `production-version` retains the prior backlog-preserving branch until C2, so this slice does not change its contract.

### Task 3: No-Follow Boundary and Regression

**Files:**
- Modify: `tests/test_project_lifecycle_transaction.py`

**Interfaces:**
- Consumes: descriptor-based canonical source reader plus configured spec artifact coverage.
- Produces: an executable guard distinguishing canonical target reads from allowed spec coverage checks.

- [ ] **Step 1: Tighten the no-follow test.** Continue raising on every `Path.is_symlink()` and `Path.read_bytes()` call. Wrap `Path.is_file()` so it succeeds only for paths contained by the configured specs root and raises for canonical transaction targets.
- [ ] **Step 2: Assert read-once behavior remains.** Re-run `test_selected_sources_are_read_once_and_planning_never_mutates_the_tree`; every selected existing target must retain exactly one descriptor read.
- [ ] **Step 3: Run focused verification.** Run:

```bash
python3 -m unittest tests.test_project_lifecycle tests.test_project_lifecycle_transaction tests.test_project_loop -q
python3 -m py_compile scripts/project_lifecycle_transaction.py scripts/project_loop.py tests/test_project_lifecycle_transaction.py tests/test_project_loop.py
/Users/dongwon.lee/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin/fallback/git diff --check
```

- [ ] **Step 4: Commit C1d code.** Commit only `scripts/project_lifecycle_transaction.py`, `scripts/project_loop.py`, `tests/test_project_lifecycle_transaction.py`, and `tests/test_project_loop.py` as `feat(103): derive projected lifecycle routes`.
- [ ] **Step 5: Record C1 completion.** Mark C1d and original C1 Steps 1–5 complete only after the focused suite passes; keep C2/D1/D2 unclaimed.

## Completion Gate

- [ ] Every lifecycle transition derives state/dashboard/loop route from projected issue bytes and the shared evaluator.
- [ ] Full loop-state writes cannot inject stale active cursor, phase, or next command.
- [ ] Canonical targets retain descriptor no-follow reads and read-once behavior.
- [ ] Old non-loop idempotency hashes remain unchanged.
- [ ] Focused lifecycle/transaction/loop suites, compilation, and diff checks pass.
- [ ] C2, D1, and D2 remain explicitly unclaimed.
