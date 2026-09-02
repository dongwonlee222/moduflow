# Issue 103 C1c Loop Mutation Adapter Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans and superpowers:test-driven-development inline. Do not use subagents.

**Goal:** Remove the last public C1 direct writer by routing `write_loop_state()` through the lifecycle transaction while preserving its returned canonical `Path` on success.

**Architecture:** Add an additive immutable `loop_change` payload to `LifecycleIntent`, valid only for `update`. The planner renders that normalized full loop state in memory instead of the lifecycle-derived loop projection. `write_loop_state()` selects the state's active issue, sends one update intent, returns the configured loop path for `applied`/`noop`, and raises a bounded error for all other terminal statuses.

## Constraints

- Work only in the designated Issue 103 worktree and preserve all existing untracked plans.
- Use RED/GREEN TDD and `apply_patch`; stage only named files.
- Preserve authorization before engine loading and all side effects.
- Preserve `write_loop_state(root, state, *, project_context=None) -> Path` for successful callers; new transaction controls are keyword-only.
- Do not begin C2, D1, D2, full discovery, release checks, merge, push, or cleanup.

### Task 1: RED Adapter and Contract Tests

- [x] Add `write_loop_state()` tests for one exact `LifecycleIntent(action="update", loop_change=<normalized state>)`, configured context forwarding, canonical returned path, engine failure mapping, and zero direct file writes.
- [x] Add contract tests that `loop_change` is immutable, participates in idempotency, and is accepted only for `update`.
- [x] Confirm RED before implementation.

### Task 2: Pure Loop Replacement Planning

- [x] Add `render_loop_state_update(loop_bytes, state)` as a pure renderer matching the prior normalized JSON bytes.
- [x] Extend `LifecycleIntent` normalization/identity with frozen `loop_change`.
- [x] When `loop_change` exists, render only the loop target from it; issue/state/dashboard/index/roadmap/evidence still follow the same transaction plan and validation gates.
- [x] Add a nested configured real-engine test proving the configured loop changes and poisoned defaults remain unchanged.

### Task 3: Public Adapter and Verification

- [x] Replace `mkdir`/`write_text` in `write_loop_state()` with the lazy transaction boundary.
- [x] Select `active_issue_id` or the first normalized `issue_ids` entry; fail before engine loading when neither exists.
- [x] Preserve the configured loop path return for `applied`/`noop`; raise a bounded `RuntimeError` for failure statuses.
- [x] Run lifecycle, transaction, and loop focused suites, syntax compilation, and `git diff --check` (208 tests).
- [x] Commit code as `a770e75 feat(103): transact loop state writes`; C1c is complete and C1d retains the remaining original C1 Step 4 work.

## Completion Gate

- [x] No public lifecycle or loop adapter directly writes canonical state/dashboard/loop artifacts.
- [x] Full loop-state compatibility is represented in the transaction idempotency identity.
- [x] Configured workspace selection and decoy preservation are proven.
- [x] Focused suites pass; C1d/C2/D1/D2 remain unclaimed.
