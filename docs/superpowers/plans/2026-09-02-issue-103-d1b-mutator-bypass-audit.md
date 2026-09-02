# Issue 103 D1b Mutator-Bypass Audit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans and superpowers:test-driven-development inline. Do not use subagents.

**Goal:** Make the operation audit prove that lifecycle transaction apply/recovery boundaries own every target, journal, lock, projected-state, and recovery persistence mutation while legacy lifecycle, loop, and Production Record adapters have no direct-write bypass.

**Architecture:** Preserve the exact function-level mutation inventory, but extend guarded ownership across module boundaries. A reviewed transaction persistence entry names its concrete mutation function and one or more qualified transaction owners. The audit resolves the transaction call graph across `project_lifecycle_transaction.py` and `project_lifecycle_transaction_storage.py`, treats a reached authorization helper as a guard only when it directly requires the declared capability, and requires that guard to dominate every owner path that reaches the mutation. Existing same-module `guarded_boundary` and `internal_guarded_helper` behavior remains unchanged.

**Tech Stack:** Python standard-library `ast`, JSON operation inventory, existing Issue 110 capability policy, and `unittest`.

## Global Constraints

- Work only in the existing Issue 103 worktree and preserve every existing untracked plan file.
- Do not add a broad module exemption or classify all transaction-module writes automatically. Every direct mutation function remains an explicit reviewed inventory item.
- Only `apply_lifecycle_transaction()` and `recover_incomplete_transaction()` may be transaction persistence owners; read-only inspection is not a mutation owner.
- Owner authorization must use operation `write` and must dominate the path into persistence. A guard after a persistence call, a missing owner, an unreachable helper, or a wrong operation fails closed.
- Remove obsolete lifecycle/loop/production writer entries. If any of those adapters regain a direct filesystem mutation, the normal unclassified-surface rule must fail the audit.
- Classify the fixed transaction `.moduflow` control directory as a reviewed project-control path; do not weaken canonical artifact-path checks.
- Do not begin D1c distribution/version/documentation work, D2 full discovery/release review, merge, push, or worktree cleanup.

---

### Task 1: RED contracts for qualified transaction ownership

**Files:**
- Modify: `tests/test_project_operation_audit.py`
- Test: `scripts/project_operation_audit.py`

**Interfaces:**
- Consumes: exact mutation findings plus reviewed inventory records.
- Produces: failing contracts for cross-module ownership, delegated authorization, dominance, and current-repository completeness.

- [ ] **Step 1: Extend the fixture project helper for multiple script modules**

Allow a test fixture to write both a boundary module and a storage module without changing existing single-module tests.

- [ ] **Step 2: Add a passing-contract test that is RED against the current audit**

Create a boundary whose public `apply()` calls a same-module `_authorize()` helper before `storage.persist()`. `_authorize()` directly calls `require_project_capability(context, "write")`; `persist()` performs a filesystem mutation. Inventory the exact storage function as `transaction_persistence` with a qualified owner record:

```json
{
  "module": "scripts/storage.py",
  "function": "persist",
  "mode": "transaction-apply",
  "scope": "target-project",
  "operation": "write",
  "classification": "transaction_persistence",
  "guard_owners": [
    {"module": "scripts/boundary.py", "function": "apply"}
  ],
  "rationale": "Persists only under the guarded transaction apply boundary."
}
```

Expected before implementation: invalid configuration because the classification and qualified owners are unsupported.

- [ ] **Step 3: Add fail-closed ownership tests**

Prove each of these remains invalid:

- the owner calls persistence before its delegated guard;
- the delegated guard declares `read` instead of `write`;
- the named owner does not reach the exact mutation helper;
- an owner or mutation function is missing;
- an empty or malformed `guard_owners` list is supplied;
- a transaction persistence entry names an owner other than the two approved lifecycle transaction boundaries in the current repository policy.

- [ ] **Step 4: Add public-adapter bypass and current-repository tests**

Add a fixture where a legacy adapter calls the transaction boundary but also performs its own `write_text()`; the extra direct mutation must remain unclassified. Add `test_current_repository_has_zero_operation_audit_gaps()` asserting valid output and zero unclassified, unguarded, stale, duplicate, and configuration errors.

- [ ] **Step 5: Run the focused tests and confirm RED**

```bash
python3 -m unittest -v tests.test_project_operation_audit
```

Expected: only the new transaction ownership/current-repository contracts fail; all existing Issue 110 audit tests continue to pass.

---

### Task 2: Implement cross-module guarded transaction ownership

**Files:**
- Modify: `scripts/project_operation_audit.py`
- Test: `tests/test_project_operation_audit.py`

**Interfaces:**
- Consumes: `transaction_persistence` entries with exact mutation functions and qualified `guard_owners`.
- Produces: the existing `moduflow.project-operation-audit.v1` result with the same zero-gap count semantics.

- [ ] **Step 1: Validate the new classification strictly**

Add `transaction_persistence` to the allowed classifications. Require `scope: target-project`, `operation: write`, a non-empty `guard_owners` list, and exact non-empty `module`/`function` strings for every owner. Reject `guard_owners` on unrelated classifications so the new shape cannot become a general exemption.

- [ ] **Step 2: Preserve qualified call metadata**

Keep both the leaf call name and the dotted call name in function metadata. Resolve only reviewed script modules named by the entry; do not guess arbitrary imports or follow external/library calls.

- [ ] **Step 3: Prove reachability from every declared owner**

Walk the bounded script call graph from each qualified owner to the exact direct mutation function. Same-module calls keep existing behavior; a cross-module hop is accepted only when the dotted call targets the reviewed mutation module or one of its internal functions. Cycles terminate through a qualified `(module, function)` visited set.

- [ ] **Step 4: Prove delegated guard dominance**

Within each declared owner, treat a call as a delegated guard only when its reached same-module helper directly calls `require_project_capability(..., "write")`. For every first owner call that can reach the mutation, require a direct or delegated write guard to dominate that call using the existing statement/block dominance logic. Never infer authorization from a helper name.

- [ ] **Step 5: Keep existing classifications backward compatible**

Do not change the behavior of `guarded_boundary`, `internal_guarded_helper`, `package_maintenance`, or `external_control`. Their current fixture tests remain the regression gate.

- [ ] **Step 6: Run GREEN for the audit unit suite**

```bash
python3 -m unittest -v tests.test_project_operation_audit
python3 -m py_compile scripts/project_operation_audit.py
```

Expected: all audit tests pass before changing the real repository inventory except the current-repository zero-gap assertion.

---

### Task 3: Replace obsolete writer ownership with transaction persistence inventory

**Files:**
- Modify: `config/project-operation-entrypoints.json`
- Modify: `config/canonical-path-literals.json`
- Test: `tests/test_project_operation_audit.py`
- Test: `tests/test_canonical_path_guard.py`

**Interfaces:**
- Consumes: the direct mutation findings in transaction boundary/storage modules and the Task 2 ownership proof.
- Produces: zero unclassified/unguarded/stale/duplicate/configuration gaps and a reviewed fixed control-path classification.

- [ ] **Step 1: Remove obsolete direct-writer entries**

Delete inventory ownership for:

- `scripts/project_lifecycle.py:sync_lifecycle`
- `scripts/project_loop.py:write_loop_state`
- `scripts/project_production.py:create_production_record`

These functions remain guarded compatibility adapters, but they no longer own persistence and therefore must not appear as mutation owners.

- [ ] **Step 2: Inventory every direct transaction mutation function**

Add exact `transaction_persistence` entries for all findings reported in:

- `scripts/project_lifecycle_transaction.py`
- `scripts/project_lifecycle_transaction_storage.py`

Declare `apply_lifecycle_transaction`, `recover_incomplete_transaction`, or both as qualified owners according to actual call-graph reachability. Do not assign an owner merely to satisfy counts; an unreachable declaration must fail the Task 2 proof.

- [ ] **Step 3: Classify the fixed transaction control path**

Add `scripts/project_lifecycle_transaction.py` / `join:.moduflow` to `config/canonical-path-literals.json` as `project_control_path`, with rationale limited to transaction locks, journals, and private recovery data. Canonical issue/dashboard/roadmap/production paths must still resolve from the project context.

- [ ] **Step 4: Run the real-repository audit gates**

```bash
python3 scripts/project_operation_audit.py .
python3 scripts/canonical_path_guard.py .
python3 -m unittest -v \
  tests.test_project_operation_audit \
  tests.test_canonical_path_guard
```

Expected: both commands exit zero; operation audit has zero unclassified, unguarded, stale, duplicate, and configuration errors; canonical-path guard has zero prohibited findings.

---

### Task 4: Focused verification, tracking, and commits

**Files:**
- Modify: `specs/103-atomic-lifecycle-state-transaction/plan.md`
- Modify: `specs/103-atomic-lifecycle-state-transaction/tasks.md`
- Modify: `docs/superpowers/plans/2026-09-02-issue-103-d1b-mutator-bypass-audit.md`

**Interfaces:**
- Consumes: Tasks 1-3.
- Produces: completed D1b evidence with D1c active.

- [ ] **Step 1: Run focused adapter and audit regression**

```bash
python3 -m unittest -v \
  tests.test_project_operation_audit \
  tests.test_canonical_path_guard \
  tests.test_project_lifecycle \
  tests.test_project_loop \
  tests.test_project_production
python3 -m py_compile \
  scripts/project_operation_audit.py \
  scripts/project_lifecycle_transaction.py \
  scripts/project_lifecycle_transaction_storage.py
git diff --check
```

Expected: all focused tests and static checks pass. Do not run or claim full discovery/source release completion in D1b.

- [ ] **Step 2: Commit implementation separately from tracking**

```bash
git add \
  scripts/project_operation_audit.py \
  config/project-operation-entrypoints.json \
  config/canonical-path-literals.json \
  tests/test_project_operation_audit.py
git commit -m "test(103): enforce transaction mutation ownership"
```

- [ ] **Step 3: Record D1b completion**

Mark D1b complete, leave D1 open, and make D1c distribution/release/architecture gates active. Record fresh test counts and commit:

```bash
git add \
  specs/103-atomic-lifecycle-state-transaction/plan.md \
  specs/103-atomic-lifecycle-state-transaction/tasks.md \
  docs/superpowers/plans/2026-09-02-issue-103-d1b-mutator-bypass-audit.md
git commit -m "docs(103): record transaction audit completion"
```

## Completion Gate

- [ ] Every direct transaction mutation function is explicitly inventoried and proven reachable only through a declared write-authorized transaction owner.
- [ ] Lifecycle, loop, and Production Record adapters own no direct persistence; reintroducing one fails as an unclassified mutation.
- [ ] The operation audit and canonical-path guard report zero gaps on the current repository.
- [ ] Existing Issue 110 audit classifications remain backward compatible.
- [ ] D1c distribution/release/docs and D2 full verification remain open.
