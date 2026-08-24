# Issue 103 Plan Review

**Verdict: plan-ready** — the specification is approved, dependencies are complete, all acceptance criteria map to implementation tasks, and readiness checks pass; implementation has not started.

## Findings

1. **Resolved — physical issue-index target was ambiguous.** The spec now names optional `workspace/issue-index.json` and distinguishes it from the always-rebuilt in-memory dependency index.
2. **Resolved — pause/resume could imply unsupported issue states.** The plan preserves the canonical active issue and changes only loop blocker/status metadata.
3. **Resolved — Production Record version identity was unspecified.** Transaction production intents now require an explicit semantic version while legacy unversioned records remain readable without migration.
4. **Resolved — roadmap updates could rewrite narrative prose.** The plan restricts automation to one bounded managed projection block and selects it only for roadmap-owned changes.
5. **Pass — dependency contract.** Issues 109 and 110 are merged; canonical paths and central write authorization are available.
6. **Pass — execution decomposition.** Eight reviewable tasks define contracts, projected validation, journal/recovery, adapters, diagnostics/audit, and completion gates.
7. **Pass — safety model.** Authorization precedes all transaction-local writes; hashes, lock, journal, reverse rollback, and `recovery_required` cover concurrent edits and crashes.
8. **Pass — scope fence.** No database, remote transaction, resolver rewrite, capability-policy rewrite, or legacy schema migration is included.

## Acceptance Coverage

- Failure and crash boundaries → B1/B2.
- Nested canonical paths and zero-write denial → A2/B2.
- Concurrent edits and idempotency collisions → B2.
- Lifecycle action retries and conditional index/roadmap targets → C1.
- Production version uniqueness → C2.
- Zero drift, bypass detection, Doctor recovery, and release gates → D1/D2.

## Constitution

Constitution: v1.0 checked — no violations.

## Next

Human reviews this plan PR. After explicit execution approval, run `product:execute 103-atomic-lifecycle-state-transaction`; the implementation will use RED/GREEN task boundaries and require a separate implementation PR/merge approval.

---

# A2 Read-only Planner Implementation Review — 2026-08-24

**Verdict: pass** — A2.5a corrected the two projection defects and A2.5b closed all three planner-boundary findings with RED/GREEN regression coverage. A3 projected validation may proceed as a separately approved slice.

## Verification Evidence

- `python3 -m unittest -q tests.test_project_lifecycle_transaction tests.test_project_lifecycle tests.test_project_loop` → 63 tests passed.
- `git diff --check` → passed.
- Direct multi-issue reproduction → physical issue-index output contained only `BIZ-103` and dropped `BIZ-200`.
- Direct backlog-update reproduction → state and loop incorrectly selected `BIZ-103` for `product:execute` while the issue remained `backlog`.
- Direct context-mismatch reproduction → planner read `shadow/issues/BIZ-103.md` while `context["paths"]["issues"]` still identified `issues/`.
- Direct immutability reproduction → mutating the input `validation_rules` list changed the frozen `PlannedTarget` value.
- A2.5a regression → 161 transaction/lifecycle/loop/issue-schema tests passed; spec consistency reported zero findings.
- A2.5b RED → context-map mismatch, descriptor-only reading, unreadable descriptor, and deep target immutability regressions failed for the intended reasons.
- A2.5b GREEN → 4 focused regressions passed; 162 transaction/lifecycle/loop/issue-schema tests passed.
- `git diff --check` → passed.

## Blocking Findings

1. **Resolved in A2.5a — physical issue-index data loss.** The planner now normalizes every canonical issue from one in-memory read, overlays the owning projected issue bytes, and renders the complete physical index.
2. **Resolved in A2.5a — backlog-preserving actions activated execution.** State/dashboard/loop projections now create an execution cursor only for projected `active`; `update`, `reconcile`, and `production-version` preserve backlog selection behavior.
3. **Resolved in A2.5b — resolved context maps could diverge.** `_safe_planning_child()` now requires `paths[role]` and `relative_paths[role]` to identify the same role root and returns `PLAN_CONTEXT_INVALID` before target selection when they differ.
4. **Resolved in A2.5b — no-follow check had a race window.** Planner sources are now opened component-by-component with no-follow descriptors, verified as regular through the opened descriptor, and consumed with descriptor reads instead of reopening a checked pathname.
5. **Resolved in A2.5b — `PlannedTarget` was not deeply immutable.** `__post_init__()` now detaches validation rules and private byte containers into immutable tuple/bytes values.

## Gate

A2 is complete and no longer blocks A3. Projected validation, staging, apply, and rollback remain outside this reviewed planner boundary and require their own approved implementation slice.
