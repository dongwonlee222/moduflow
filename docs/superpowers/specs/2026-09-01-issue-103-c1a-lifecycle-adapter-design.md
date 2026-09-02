# Issue 103 C1a Lifecycle Transition Adapter Design

## Artifact Links

- **Issue:** `103-atomic-lifecycle-state-transaction`
- **Parent plan:** `specs/103-atomic-lifecycle-state-transaction/plan.md`, Stream C / Task C1
- **Depends on:** B2f3d fresh-apply recovery barrier through commit `47fe00d`
- **Decision maker:** Dongwon Lee

## Decision

Add one thin lifecycle adapter to `scripts/project_lifecycle.py`. The adapter translates lifecycle command arguments into the existing `LifecycleIntent` contract and delegates every selected artifact mutation to `apply_lifecycle_transaction()`. The same module exposes CLI transition and recovery modes while preserving all existing read-only modes and the legacy `--sync` mode unchanged for this slice.

C1 remains intentionally split:

- **C1a (this design):** lifecycle transition API plus transition/recovery CLI;
- **C1b:** replace `sync_lifecycle()` direct state/dashboard writes with a transaction-backed reconcile adapter;
- **C1c:** replace `write_loop_state()` direct writes with a transaction-backed loop adapter.

This prevents Stream C from becoming another large multi-file change and does not claim that every legacy writer is closed after C1a alone.

## Selected Architecture

### Python adapter

`project_lifecycle.py` adds:

```python
def transition_lifecycle(
    root,
    issue_id,
    action,
    *,
    actor,
    source_event,
    target_status=None,
    idempotency_key="",
    expected_issue_sha256="",
    loop_blocker="",
    require_issue_index=False,
    project_context=None,
    clock=None,
    fault_injector=None,
):
    """Apply one lifecycle transition through the Issue 103 transaction."""
```

The function imports `project_lifecycle_transaction` inside the call boundary to avoid the existing renderer dependency cycle: the transaction module already imports lifecycle renderers from `project_lifecycle.py`.

The adapter constructs exactly one `LifecycleIntent` and returns the strict `moduflow.lifecycle-transaction.v1` dictionary from `apply_lifecycle_transaction()` without reshaping, duplicating, or independently writing any target.

Supported actions are `start`, `update`, `pause`, `resume`, and `complete`. `target_status` is optional for `update`; fixed-action target semantics remain owned by `normalize_lifecycle_intent()`. `reconcile` remains owned by C1b because its compatibility result and no-active-issue ownership require a separate decision.

### CLI modes

The existing positional `project_path` and flags `--state`, `--drift`, `--sync`, `--issues`, and `--ready` remain compatible. Two mutually exclusive modes are added:

```text
--transition {start,update,pause,resume,complete}
--recover [TRANSACTION_ID]
```

Transition mode accepts:

```text
--issue-id ISSUE_ID
--target-status {backlog,active,done}
--actor ACTOR
--source-event SOURCE_EVENT
--idempotency-key KEY
--expected-issue-sha256 SHA256
--loop-blocker TEXT
--require-issue-index
```

`--issue-id`, `--actor`, and `--source-event` are required in transition mode. Recovery without a value processes the project-wide frozen inventory; recovery with a value processes only that logical transaction ID. Transition-only arguments are rejected in recovery and read-only modes.

Priority/roadmap flags are deferred to C1b. Passing only a priority to the current roadmap renderer would implicitly replace dependency and release-order values with defaults, so adding that CLI shape in C1a would be unsafe.

### Result and exit contract

- Transition prints the exact strict transaction JSON.
- Recovery prints the exact strict recovery JSON.
- `applied` and `noop` exit `0`.
- `denied`, `conflict`, `rolled_back`, and `recovery_required` exit `1`.
- Invalid or incompatible CLI arguments exit `2` through `argparse` before transaction/recovery entry points are called.
- Python callers receive the strict result and decide their own process behavior.

## Data Flow

```text
lifecycle API/CLI arguments
  -> LifecycleIntent
  -> apply_lifecycle_transaction()
  -> recovery barrier / fresh plan / projected validation
  -> lock / journal / deterministic apply or rollback
  -> strict transaction result
```

Recovery mode uses:

```text
--recover [id]
  -> recover_incomplete_transaction(root, id-or-empty)
  -> strict recovery report
```

The adapter never reads an issue to derive a competing target state, never calls lifecycle renderers directly, and never writes issue, state, loop, dashboard, index, roadmap, evidence, lock, or journal files itself.

## Compatibility

- Existing lifecycle query functions and their return shapes remain unchanged.
- Existing `sync_lifecycle()` behavior remains unchanged until C1b; its direct writer is explicitly still present after this slice.
- Existing `main()` default and read-only flag output remains unchanged.
- New transition/recovery output is additive and uses existing Issue 103 schemas rather than a new wrapper schema.
- Direct script execution and package import both resolve the transaction module through a local lazy-import helper.

## Fail-Closed Behavior

- Missing required transition metadata is rejected before transaction entry.
- Invalid action/target combinations are rejected by the existing normalization contract.
- Invalid recovery/transition flag combinations exit `2` before filesystem mutation.
- Project capability denial, optimistic conflict, rollback, and recovery-required outcomes are returned without exception-message leakage.
- Adapter errors do not expose canonical absolute paths, artifact bytes, private workspace names, lock PID/token values, or recovery payload details.

## Test Contract

1. Python adapter tests patch only the transaction entry point and assert exact `LifecycleIntent` construction for every supported action.
2. A public-boundary test patches direct `Path.write_text`, `Path.write_bytes`, `os.replace`, and `os.unlink` boundaries in `project_lifecycle.py`; the adapter itself must call none of them.
3. One integration test uses a nested Issue 109 context and proves only configured canonical targets change through the real transaction engine while poisoned default paths remain byte-identical.
4. CLI tests cover transition success, recovery-all, recovery-one, exact JSON output, status-to-exit mapping, and invalid combinations exiting `2` without calling apply/recovery.
5. Existing `tests.test_project_lifecycle`, `tests.test_project_lifecycle_transaction`, and `tests.test_project_loop` suites must stay green.

## Alternatives Rejected

1. **CLI-only transaction calls:** less code initially, but every Python caller would need to reconstruct intent validation and result handling.
2. **Lifecycle compatibility API inside the transaction engine:** centralizes too much responsibility and makes the engine depend on CLI/product semantics it should not own.
3. **All of C1 in one change:** removes bypasses sooner but combines lifecycle CLI, reconcile ownership, loop compatibility, and roadmap semantics into a high-risk review unit.

## Out of Scope

- `sync_lifecycle()` transaction-backed reconcile and its legacy compatibility result;
- `write_loop_state()` transaction adapter;
- roadmap priority/dependency/release-order CLI mutation;
- Production Record version transactions;
- Doctor diagnostics, mutation audit, distribution/release gates, PR, merge, or plugin release;
- Prefect or the automation control plane.

## Completion Condition

C1a is complete when lifecycle transition and recovery API/CLI paths delegate exclusively to the Issue 103 transaction boundaries, invalid combinations fail before mutation, existing read-only/sync compatibility remains green, and no claim is made that C1b/C1c bypass removal is already complete.
