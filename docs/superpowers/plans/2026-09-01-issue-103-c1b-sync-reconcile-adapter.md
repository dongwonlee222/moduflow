# Issue 103 C1b Sync/Reconcile Adapter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans and superpowers:test-driven-development inline. Do not use subagents for this slice.

**Goal:** Route legacy `sync_lifecycle()` state/dashboard propagation through one recoverable `reconcile` transaction while retaining its existing result fields and CLI behavior.

**Architecture:** Keep the legacy read-side preflight that resolves one project context, authorizes execution, evaluates issue schema diagnostics, and chooses a deterministic reconcile owner. The transaction planner will build one shared projected issue evaluation from already-read issue bytes and use it to derive the unique active issue, phase, next command, dashboard source, loop projection, and optional issue index. `sync_lifecycle()` will contain no direct canonical write and will expose the complete engine result additively under `transaction`.

**Tech Stack:** Python 3 standard library, existing Issue 103 transaction engine, shared issue-schema evaluator, `unittest`, `unittest.mock`.

## Global Constraints

- Work only in `/Users/dongwon.lee/.config/superpowers/worktrees/moduflow/110-project-operation-capability-enforcement` on `codex/103-atomic-lifecycle-state-transaction`.
- Preserve every pre-existing untracked plan; stage only the files named in each commit step.
- Use RED/GREEN TDD and `apply_patch` for edits.
- Do not add a new schema, direct canonical writer, subprocess, Git, network, Prefect, or control-plane dependency.
- Preserve the legacy success keys `active`, `phase`, and `dashboard_updated`; preserve the legacy blocked keys and add only `transaction` when the engine was called.
- Keep archived/read-only denial before issue evaluation and before any transaction-local side effect.
- Do not begin C1c loop writer replacement, C2 production versions, D1 Doctor/audit, D2 full discovery/release, merge, push, or worktree cleanup.

---

### Task 1: RED Compatibility and Boundary Tests

**Files:**
- Modify: `tests/test_project_lifecycle.py`

**Interfaces:**
- Produces the exact `sync_lifecycle(root, *, project_context=None, actor="moduflow.lifecycle", source_event="sync_lifecycle", idempotency_key="", expected_issue_sha256="", require_issue_index=False, clock=None, fault_injector=None) -> dict` compatibility contract.

- [ ] **Step 1: Add a one-intent adapter test.** Mock `_load_lifecycle_transaction_module()`, call `sync_lifecycle()`, and assert exactly one `LifecycleIntent(action="reconcile")` is created for the unique active issue with actor/source/idempotency/hash/index inputs forwarded.
- [ ] **Step 2: Assert exact result compatibility.** For `applied`, retain `active`, `phase`, and `dashboard_updated`, with the full result under `transaction`. For `noop`, report `dashboard_updated=False`. For every engine failure status, return top-level `status="blocked"`, legacy fields, a bounded `errors` list, and `transaction`.
- [ ] **Step 3: Prove preflight failure ordering.** Existing malformed/unreadable issue diagnostics must return the prior blocked shape, without loading or calling the transaction engine.
- [ ] **Step 4: Prove the adapter owns no writes.** With the engine mocked, patch `Path.write_text`, `Path.write_bytes`, `os.replace`, and `os.unlink`; all must remain untouched.
- [ ] **Step 5: Run the new named tests and confirm RED.** Expected failure: the current `sync_lifecycle()` has no transaction inputs, calls no engine, and writes state/dashboard directly.

### Task 2: Shared Projected Routing in the Planner

**Files:**
- Modify: `scripts/project_lifecycle_transaction.py`
- Modify: `tests/test_project_lifecycle_transaction.py`

**Interfaces:**
- Consumes already-read owning issue bytes plus canonical issue sources.
- Produces one evaluated projected issue collection reused by state, loop, dashboard, and optional physical index rendering.

- [ ] **Step 1: Add RED projection tests.** Cover reconcile for an active issue at `spec`, `plan`, `execute`, `review`, and `release`; dependency-blocked routing; no-active selection; and a unique active issue whose configured source path differs from the reconcile owner.
- [ ] **Step 2: Add read-once and nested-path assertions.** Each canonical issue source is read at most once, configured roots are used, and poisoned default issue/workspace paths remain byte-identical.
- [ ] **Step 3: Build one projected issue evaluation.** Parse the owner from `issue_after`, parse every other canonical issue from its single safe read, and pass those normalized records through the shared issue evaluator.
- [ ] **Step 4: Derive all routing from that evaluation.** Select an active issue only when exactly one evaluated issue is active; derive phase with `infer_phase(..., evaluation=...)`; use its evaluated recommended command; and render dashboard source/index records from the same evaluated data.
- [ ] **Step 5: Run the named planner tests GREEN.** Re-run the existing target-order, read-once, backlog-preserving, nested-path, and projected-validation tests.

### Task 3: Transaction-Backed `sync_lifecycle()`

**Files:**
- Modify: `scripts/project_lifecycle.py`
- Modify: `tests/test_project_lifecycle.py`
- Modify: `tests/test_project_lifecycle_transaction.py`

**Interfaces:**
- Consumes Task 2 planner semantics and `apply_lifecycle_transaction()`.
- Produces one compatibility wrapper with no direct writes.

- [ ] **Step 1: Select a deterministic reconcile owner.** Use the unique active issue when present; otherwise use the first canonical issue ID. If no valid issue exists, fail closed with the legacy blocked shape and no engine call.
- [ ] **Step 2: Build and apply one reconcile intent.** Forward keyword-only transaction inputs and resolved project context; do not render or write state/dashboard in the adapter.
- [ ] **Step 3: Map the engine result.** Read `dashboard_updated` from the dashboard target's committed change state; retain preflight-derived compatibility `active`/`phase`; attach the full redacted engine result under `transaction`; convert non-success transaction statuses to the existing blocked CLI contract.
- [ ] **Step 4: Run legacy and real-engine integration tests.** Existing sync idempotency, dependency routing, custom paths, configured dashboard/decoy, unreadable issue, archived denial, and `--sync` exit behavior must pass unchanged except for the additive `transaction` field.
- [ ] **Step 5: Run focused verification.** Run:

```bash
python3 -m unittest tests.test_project_lifecycle tests.test_project_lifecycle_transaction tests.test_project_loop -q
python3 -m py_compile scripts/project_lifecycle.py scripts/project_lifecycle_transaction.py tests/test_project_lifecycle.py tests/test_project_lifecycle_transaction.py
/Users/dongwon.lee/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin/fallback/git diff --check
```

- [ ] **Step 6: Commit only C1b tracked files.** Commit `scripts/project_lifecycle.py`, `scripts/project_lifecycle_transaction.py`, `tests/test_project_lifecycle.py`, and `tests/test_project_lifecycle_transaction.py` as `feat(103): transact lifecycle reconcile`.

## Completion Gate

- [ ] `sync_lifecycle()` contains zero direct state/dashboard mutation.
- [ ] Every successful sync has one terminal transaction result under `transaction`.
- [ ] Shared projected evaluation determines active issue, phase, route, dashboard source, loop state, and optional index.
- [ ] Existing compatibility keys and `--sync` success/failure behavior remain stable.
- [ ] Focused lifecycle, transaction, and loop suites plus syntax/diff checks pass.
- [ ] C1c, C2, D1, and D2 remain explicitly unclaimed.
