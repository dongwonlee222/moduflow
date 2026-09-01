# Issue 103 D1a Doctor Recovery Diagnostics Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans and superpowers:test-driven-development inline. Do not use subagents.

**Goal:** Let Doctor report incomplete lifecycle transactions and an exact safe recovery command without acquiring a lock, reading recovery payload bytes, or mutating archived/read-only projects.

**Architecture:** Add one read-only `inspect_recovery_transactions()` API beside the transaction recovery API. It reuses no-follow workspace discovery and strict journal parsing, filters terminal journals, and returns only phase, logical target roles/paths, safe hashes, and stable error codes. `project_doctor.py` embeds that result, adds actionable recovery recommendations, and treats incomplete or unsafe recovery state as an unhealthy Doctor result while keeping the inspection itself read-only.

**Tech Stack:** Python standard library, existing lifecycle transaction journal/storage contracts, project capability policy, `unittest` and `unittest.mock`.

## Global Constraints

- Work only in the existing Issue 103 worktree and preserve all existing untracked plan files.
- Doctor may require only project `read`; archived/read-only projects remain inspectable.
- Diagnostics must not call `recover_incomplete_transaction()`, acquire lifecycle locks, create directories or temporary files, persist journals, replace/unlink files, or read preimage/staged payload bodies.
- Output must exclude absolute recovery workspace paths, journal bytes, preimage bytes, staged bytes, and unrestricted artifact content.
- Terminal `complete` and `rolled-back` journals are silent; incomplete phases are `planned`, `staged`, `prepared`, `applying`, `post-validating`, `finalizing`, `rolling-back`, and `recovery-required`.
- Unsafe discovery/control/journal state fails closed with a stable code and no guessed recovery action.
- Full discovery and source release gates remain deferred to D2.

---

### Task 1: Read-only transaction diagnostic API

**Files:**
- Modify: `scripts/project_lifecycle_transaction.py:63-130,3656-3860,4896-5050`
- Test: `tests/test_project_lifecycle_transaction.py:1270-1750,3460-3860`

**Interfaces:**
- Consumes: `transaction_storage.discover_recovery_workspaces(root)`, `_private_recovered_journal_workspace(root, transaction_id)`, strict serialized journal targets, and Issue 110 `read` capability.
- Produces: `inspect_recovery_transactions(project_root, *, project_context=None) -> dict` with schema `moduflow.lifecycle-recovery-diagnostics.v1`.

- [x] **Step 1: Write RED diagnostic contract tests**

Add tests in `TransactionPlanningTests` using `prepare_restart_recovery_case()`:

```python
def test_recovery_diagnostics_are_read_only_redacted_and_actionable(self):
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        context, plan, _applied, _rollback = self.prepare_restart_recovery_case(
            root, "prepared"
        )
        with (
            mock.patch.object(transaction, "recover_incomplete_transaction") as recover,
            mock.patch.object(transaction.transaction_storage.os, "mkdir") as mkdir,
            mock.patch.object(transaction.transaction_storage.os, "replace") as replace,
            mock.patch.object(transaction.transaction_storage.os, "unlink") as unlink,
        ):
            result = transaction.inspect_recovery_transactions(
                root, project_context=context
            )

        self.assertEqual(result["status"], "incomplete")
        self.assertEqual(result["transactions"][0]["transaction_id"], plan.transaction_id)
        self.assertEqual(result["transactions"][0]["phase"], "prepared")
        self.assertIn("issue", result["transactions"][0]["affected_roles"])
        self.assertNotIn(str(root), json.dumps(result))
        recover.assert_not_called()
        mkdir.assert_not_called()
        replace.assert_not_called()
        unlink.assert_not_called()
```

Also parameterize `prepared`, `applying`, `post-validating`, `rolling-back`, and `recovery-required`; assert terminal journals are filtered; unsafe discovery and malformed journals return `status: unsafe` with only a stable `error_code`.

- [x] **Step 2: Run the diagnostic slice and verify RED**

Run:

```bash
python3 -m unittest -v \
  tests.test_project_lifecycle_transaction.TransactionPlanningTests.test_recovery_diagnostics_are_read_only_redacted_and_actionable
```

Expected: `AttributeError` because `inspect_recovery_transactions` does not exist.

- [x] **Step 3: Implement the strict detached diagnostic envelope**

Add the constant and serializer helpers:

```python
RECOVERY_DIAGNOSTICS_SCHEMA = "moduflow.lifecycle-recovery-diagnostics.v1"
_INCOMPLETE_JOURNAL_PHASES = frozenset({
    "planned", "staged", "prepared", "applying", "post-validating",
    "finalizing", "rolling-back", "recovery-required",
})

def _recovery_diagnostic_target(target):
    return {
        "role": target["role"],
        "relative_path": target["relative_path"],
        "before_sha256": target["before_sha256"],
        "after_sha256": target["after_sha256"],
        "changed": target["changed"],
    }
```

`inspect_recovery_transactions()` must resolve/detach the project context, require `read`, discover transaction IDs in byte-sorted order, open only control snapshots, reuse `_load_recovered_journal_state()`, filter `complete`/`rolled-back`, and return:

```python
{
    "schema": RECOVERY_DIAGNOSTICS_SCHEMA,
    "status": "healthy" if not records else "incomplete",
    "error_code": "",
    "transactions": [
        {
            "transaction_id": transaction_id,
            "phase": journal["phase"],
            "affected_roles": sorted({target["role"] for target in targets}),
            "targets": targets,
        }
    ],
}
```

Catch only stable recovery discovery/read/storage failures and return `status: unsafe`, the exception code, and an empty transaction list. Do not catch project capability denial.

- [x] **Step 4: Run transaction diagnostics and recovery regression tests**

Run:

```bash
python3 -m unittest -v \
  tests.test_project_lifecycle_transaction.TransactionPlanningTests.test_recovery_diagnostics_are_read_only_redacted_and_actionable \
  tests.test_project_lifecycle_transaction.TransactionPlanningTests.test_recovery_workspace_discovery_and_reopen_are_read_only \
  tests.test_project_lifecycle_transaction.TransactionPlanningTests.test_public_project_wide_recovery_recovers_cleans_and_retries_noop
```

Expected: all pass; no recovery mutation mock is called by diagnostics.

- [x] **Step 5: Commit the diagnostic boundary** (`4feb071`)

```bash
git add scripts/project_lifecycle_transaction.py tests/test_project_lifecycle_transaction.py
git commit -m "feat(103): inspect incomplete transactions read only"
```

### Task 2: Doctor integration and exit semantics

**Files:**
- Modify: `scripts/project_doctor.py:65-110,474-705`
- Test: `tests/test_project_doctor.py:286-526`

**Interfaces:**
- Consumes: `inspect_recovery_transactions(project_root, project_context=context)` from Task 1.
- Produces: `result["recovery"]`, shell-safe recovery recommendations, and nonzero Doctor CLI status for `incomplete` or `unsafe` recovery state.

- [x] **Step 1: Write RED Doctor adapter tests**

Add a lazy-loader unit test with an archived/read-only context and a fake diagnostic boundary:

```python
diagnostics = {
    "schema": "moduflow.lifecycle-recovery-diagnostics.v1",
    "status": "incomplete",
    "error_code": "",
    "transactions": [{
        "transaction_id": "txn-103",
        "phase": "prepared",
        "affected_roles": ["issue", "state"],
        "targets": [],
    }],
}
```

Assert Doctor calls the inspector once with the detached context, includes the result unchanged, and adds exactly one shell-safe recommendation equivalent to:

```text
python3 scripts/project_lifecycle.py <canonical-project-root> --recover txn-103
```

Add cases for `healthy` (no recommendation) and `unsafe` (generic repair guidance without a guessed transaction command). Patch the boundary's `recover_incomplete_transaction` to raise if Doctor calls it.

- [x] **Step 2: Run Doctor tests and verify RED**

Run:

```bash
python3 -m unittest -v tests.test_project_doctor.ProjectCapabilityDoctorTests
```

Expected: missing `recovery` result and loader calls.

- [x] **Step 3: Add the Doctor adapter**

Add `load_lifecycle_transaction()` beside the existing lazy loaders. In `inspect_project()`, call its read-only inspector after resolving `context`, then add:

```python
"recovery": recovery_diagnostics,
```

Use `shlex.join()` with the list below so paths containing spaces cannot produce an unsafe command:

```python
["python3", "scripts/project_lifecycle.py", str(project_root), "--recover", transaction_id]
```

For `unsafe`, recommend inspecting `.moduflow/transactions` permissions and running Doctor again; do not emit a recovery command. Update `main()` so success additionally requires `result["recovery"]["status"] == "healthy"`.

- [x] **Step 4: Run Doctor and transaction focused suites**

Run:

```bash
python3 -m unittest -v tests.test_project_doctor tests.test_project_lifecycle_transaction
```

Expected: all pass, including archived/read-only diagnostics.

- [x] **Step 5: Commit Doctor integration** (`7607e7d`)

```bash
git add scripts/project_doctor.py tests/test_project_doctor.py
git commit -m "feat(103): surface transaction recovery in doctor"
```

### Task 3: Command documentation and D1a verification

**Files:**
- Modify: `commands/product-doctor.md:13-73`
- Modify: `specs/103-atomic-lifecycle-state-transaction/plan.md:338-366`
- Modify: `specs/103-atomic-lifecycle-state-transaction/tasks.md:31-50`
- Modify: `docs/superpowers/plans/2026-09-01-issue-103-d1a-doctor-recovery-diagnostics.md`

**Interfaces:**
- Consumes: Task 1 diagnostic schema and Task 2 Doctor result/recommendation semantics.
- Produces: documented read-only behavior and a completed D1a slice with D1b audit work active.

- [x] **Step 1: Document the recovery diagnostic contract**

Update `commands/product-doctor.md` to state:

- Doctor reads journal control metadata only and never performs recovery.
- `healthy` has no incomplete transaction, `incomplete` lists exact IDs/phases/roles/hashes, and `unsafe` fails closed without guessing.
- Recovery occurs only through the exact `project_lifecycle.py <root> --recover <id>` command after a human reviews the diagnostic.
- Archived/read-only projects may be diagnosed but recovery remains mutation-gated.

- [x] **Step 2: Run focused verification**

Run:

```bash
python3 -m unittest \
  tests.test_project_doctor \
  tests.test_project_lifecycle_transaction \
  tests.test_project_lifecycle
python3 -m py_compile \
  scripts/project_doctor.py \
  scripts/project_lifecycle_transaction.py
git diff --check
```

Expected: all D1a-focused tests and static checks pass. The fresh run passed 211 tests. `tests.test_validation_distribution` remains a D1c gate because its two current-repository release assertions also require D1b audit/path classifications and the later version gate; a diagnostic run passed its other 47 tests and exposed only those deferred gates.

- [x] **Step 3: Update tracking and commit**

Mark D1a complete, leave D1 open, and set D1b mutator-bypass audit as active. Then commit:

```bash
git add \
  commands/product-doctor.md \
  specs/103-atomic-lifecycle-state-transaction/plan.md \
  specs/103-atomic-lifecycle-state-transaction/tasks.md \
  docs/superpowers/plans/2026-09-01-issue-103-d1a-doctor-recovery-diagnostics.md
git commit -m "docs(103): record doctor recovery diagnostics"
```

## Completion Gate

- [x] Doctor exposes every valid incomplete transaction without reading payload bodies or performing recovery.
- [x] Unsafe recovery state fails closed with stable redacted output and a nonzero Doctor result.
- [x] Archived/read-only projects remain diagnosable, while the recovery command remains the only mutation path.
- [x] D1b audit and D1c distribution/release work remain open; D2 full gates remain deferred.
