# Issue 103 Implementation Review

**Verdict: pass** — all eleven acceptance criteria are implemented and verified; direct D2 review found no open P0, P1, or P2 defect.

## D2 Findings

1. **Resolved — repeated lifecycle reconciliation could become unrecoverable after a human issue edit.** Full discovery exposed the legacy Stop-hook regression. Commit `476d9f3` gives default reconcile intents an exact issue-snapshot identity and removes only proven successful private recovery state before subsequent edits.
2. **Resolved — first real transaction lacked its evidence parent.** Test fixtures pre-created `workspace/transactions`, but an initialized real project did not. Migration now creates and tracks `workspace/transactions/.gitkeep`, and the real Issue 103 completion transaction applied with projected/post-apply validation both valid.
3. **Resolved — completed reconcile could restore a false loop cursor.** Loop rendering now clears cursors for non-active lifecycles, and normalization preserves an explicit null cursor instead of falling back to the first historical issue ID.
4. **Pass — authorization and containment.** Write denial precedes lock, journal, staging, temporary, evidence, and canonical side effects; nested contexts, decoys, traversal, symlink, non-regular, and unreadable targets are covered.
5. **Pass — failure, rollback, and crash recovery.** Every durable phase and target position has failure/restart coverage; outcomes are exact rollback, terminal completion, or explicit `recovery_required`.
6. **Pass — idempotency and concurrency.** Identical lifecycle and production intents replay as `noop`; key, evidence, preimage, and semantic-version conflicts fail closed without overwriting external edits.
7. **Pass — conditional targets.** Optional issue index remains absent unless selected, roadmap prose changes only for roadmap-owned priority changes, and Production Record versions are explicit and unique while legacy records remain readable.
8. **Pass — evidence and privacy.** Public results and Git-tracked evidence contain logical paths, hashes, bounded error codes, validation summaries, status, and next command; private preimages and payload bytes remain in restrictive local recovery storage only.
9. **Pass — adapters and bypass audit.** Lifecycle, loop, and Production public writers delegate to transaction persistence; operation audit classifies 93/93 mutation surfaces with zero unclassified, unguarded, or stale entries.
10. **Pass — distribution and compatibility.** Required runtime/test assets and focused release modules are registered; Issue 048 drift checks and the Stop hook remain compatible on a current minimal project.

## Acceptance and QA Evidence

- Final full discovery: 1,571 tests passed in 462.485s.
- Focused D2 suite: 495 tests passed; final post-fix targeted suites: 252 tests passed.
- Project artifact validation: `valid: true`, `errors: []`.
- Spec consistency: 0 errors, 0 warnings, 11/11 acceptance criteria covered.
- Lifecycle drift: `[]`.
- Operation audit: `valid: true`; 93 classified and zero gaps.
- Diff hygiene: `git diff --check` clean.
- Visual handoff: `memory/dashboard.html` and `memory/issue-103-atomic-lifecycle-state-transaction.html` regenerated.

## Review Roles

- Implementation review: performed directly by the main Codex agent because the user explicitly prohibited subagents.
- QA review: fresh focused and full local gates plus release-gate inputs.
- PM/spec review: implementation mapped line-by-line to all acceptance criteria and issue non-goals.
- Security/privacy review: containment, no-follow descriptors, restrictive recovery storage, redaction, denial ordering, and cleanup paths reviewed with no open P0/P1/P2 finding.

Constitution: v1.0 checked — no violations.

---

# Historical Plan Review

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
