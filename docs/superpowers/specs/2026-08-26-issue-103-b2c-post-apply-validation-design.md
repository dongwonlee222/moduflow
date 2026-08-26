# Issue 103 B2c Post-Apply Validation Design

## Artifact Links

- **Issue:** `103-atomic-lifecycle-state-transaction`
- **Parent plan:** `specs/103-atomic-lifecycle-state-transaction/plan.md`, Task B2 Step 3
- **Predecessors:** `b128fb6` (same-lock reverse rollback), `18f0da9` (canonical restore), and A3 projected-validation commits through `8966d8a`
- **Owner / decision maker:** Dongwon Lee
- **Phase:** execute, B2c design

## Decision

Validate the actual canonical project inside the existing private applied-workspace boundary, after every changed non-evidence target has been promoted and the journal is durably `post-validating`, but before private state is yielded to a caller. The same lifecycle lock remains held throughout exact target verification, one canonical project-validator call, validation-summary construction, and any resulting reverse rollback.

B2c adds no public command or final transaction result. It produces a private post-validated state on success and enriches the existing rollback signals with a redacted post-apply validation summary when validation caused the rollback.

## Purpose

Projected validation proves the proposed combined view before replacement. B2b proves deterministic apply and rollback. B2c closes the gap between those boundaries by proving that the bytes now present in the real canonical project are exactly the planned bytes and still satisfy project-wide validation.

Its success condition is:

> While the original transaction lock remains held, prove every target's exact phase-appropriate bytes or absence, validate the canonical project once through its resolved context, and either return a redacted successful summary or enter the existing same-lock rollback path.

## Selected Architecture

### Integration boundary

Extend the pre-yield portion of `_private_applied_workspace()` rather than wrapping it in a second context manager. The control flow becomes:

1. prepare, stage, and apply ordinary targets as implemented by B2b;
2. persist `post-validating` with the complete ordinary applied-index prefix;
3. verify exact planned target results;
4. call the canonical project validator once;
5. summarize the validator result;
6. return `_PrivatePostValidatedState` when valid;
7. otherwise raise a bounded post-apply validation error inside the existing B2b catch;
8. reconcile and roll back through `_rollback_failed_apply()` under the same lock.

The `yield` remains outside the bounded catch. Exceptions raised by the caller after a successful private state is yielded are not transaction failures and do not trigger rollback.

### Private success state

Add a frozen private value:

```python
@dataclass(frozen=True)
class _PrivatePostValidatedState:
    storage_targets: tuple[transaction_storage.StorageTarget, ...]
    preimages: tuple[transaction_storage.StoredPreimage, ...]
    staged_proposals: tuple[transaction_storage.StagedProposal, ...]
    recovery_manifest: transaction_storage.RecoveryManifest
    applied_target_indexes: tuple[int, ...]
    post_apply_validation: object
    verified_target_count: int
    journal_sha256: str
    created_at: str
    _workspace: object = field(repr=False, compare=False)
```

`post_apply_validation` is a detached, frozen, JSON-compatible summary. It contains no validator diagnostics, paths, artifact bytes, recovery names, or exception text. `verified_target_count` counts every planned target proven in its expected B2c phase state.

The evidence proposal remains staged and its canonical target remains unchanged. Evidence is verified and applied only during later finalization.

### Exact canonical target proof

For each storage target in plan order:

- changed non-evidence target: `classify_canonical_target()` must return literal `after`;
- unchanged non-evidence target: `verify_canonical_target()` must prove its exact original bytes or absence;
- evidence target: `verify_canonical_target()` must prove its exact original bytes or absence because it remains staged and has not been finalized.

An exact `before` result for a changed target is an invalid post-apply result, but it remains safe for rollback reconciliation to recognize as already restored. A state that is neither exact before nor exact after is indeterminate and becomes recovery-required when the rollback classifier cannot prove a safe state.

This explicit proof is required even when the project validator returns valid. Project validity alone does not prove that every planned target matches its expected phase-specific SHA-256 and byte length.

Before terminal `rolled-back`, extend the existing rollback proof across the complete planned set: every changed non-evidence target must be exact before, every unchanged target must still match its preimage, and evidence canonical state must remain exact before. A mismatch in any target makes rollback recovery-required. This prevents an external editor from changing an unchanged or evidence target during the lock interval while the transaction incorrectly claims byte-identical rollback.

### Canonical validator connection

Use the resolved canonical root and detached Issue 109 project context already owned by the plan. Call:

```python
validate_project_artifacts.validate_project(
    canonical_root,
    project_context=canonical_context,
)
```

exactly once, while the lifecycle lock remains present. Do not create a second projected root and do not call individual issue, lifecycle, loop, or Production Record validators independently; `validate_project()` already coordinates them.

The validator is read-only. B2c performs no Git, subprocess, network, remote, database, scheduled, or external operation.

## Validation Summary Contract

Preserve the existing summary shape:

```python
{
    "valid": bool,
    "rule_ids": list[str],
    "error_codes": list[str],
}
```

Post-apply rule IDs are fixed and ordered:

1. `canonical-targets`;
2. `project-artifacts`;
3. `issue-schema`;
4. `lifecycle-consensus`;
5. `production-records`.

Add a stage-specific summarizer rather than returning `PROJECTED_*` codes in the `post_apply_validation` field. Stable post-apply codes are:

- `POST_APPLY_TARGET_MISMATCH`: at least one changed target is exact before instead of exact after;
- `POST_APPLY_TARGET_UNPROVEN`: an exact target result cannot be proven;
- `POST_APPLY_PROJECT_INVALID`: project-level validation errors;
- `POST_APPLY_ISSUE_SCHEMA_INVALID`: issue-schema errors;
- `POST_APPLY_LIFECYCLE_DRIFT`: lifecycle drift;
- `POST_APPLY_VALIDATION_CONTRACT_INVALID`: malformed or internally inconsistent validator result;
- `POST_APPLY_VALIDATION_FAILED`: unexpected validator or summary execution failure.

Warnings remain omitted and do not make validation invalid, matching the existing project-validator contract.

The existing projected-validation summary and its `PROJECTED_*` codes remain unchanged.

## Error and Rollback Contract

Add one bounded private error:

```python
class LifecyclePostApplyValidationError(RuntimeError):
    """Stable post-apply validation failure with a redacted summary."""
```

It exposes only:

- `code`: `POST_APPLY_VALIDATION_INVALID` or `POST_APPLY_VALIDATION_FAILED`;
- `post_apply_validation`: a frozen redacted summary.

`str()` and `repr()` contain only the stable code. Underlying exceptions may be chained for local debugging but their messages never enter summaries, signals, journals, evidence, or returned values.

Include this error in the existing pre-yield bounded failure tuple. `_rollback_failed_apply()` continues to own classification, reverse restoration, rollback journal progress, and terminal signaling.

When the original failure carries a post-apply summary, copy that detached summary into:

- `LifecycleApplyRolledBack.post_apply_validation` after verified rollback;
- `LifecycleRecoveryRequired.post_apply_validation` when rollback cannot be proven.

For earlier forward-apply failures that occur before B2c runs, the new signal attribute is `None`. This preserves B2b behavior while allowing later public result/evidence work to distinguish “not run” from an actual invalid post-apply summary.

## Journal and Timestamp Behavior

B2c adds no journal phase and no successful journal write. The existing durable `post-validating` snapshot already means ordinary canonical targets were applied and post-validation is the next unfinished operation.

- success: the latest journal remains `post-validating` for later finalization;
- validation failure: B2b transitions from `post-validating` to `rolling-back`;
- verified rollback: terminal `rolled-back`;
- indeterminate rollback: terminal or best-effort `recovery-required`.

B2c reuses the rollback timestamps already prevalidated by B2b. It does not consume extra clock values, reacquire the lock, or create a second recovery workspace.

## Failure Ordering

The post-apply sequence is fail-closed:

1. prove all target results in their expected B2c phase state;
2. call the canonical validator;
3. validate and freeze the summary;
4. produce private success state.

If exact target proof fails, the project validator is not called. If the validator returns invalid or malformed output, no success state is yielded. Any bounded B2c failure enters rollback before the lock can be released.

Programming errors, `KeyboardInterrupt`, `SystemExit`, and caller-body exceptions remain outside the bounded catch and are never converted into transaction outcomes.

## Test Contract

Implementation follows RED/GREEN TDD with focused tests.

1. Prove a valid canonical result verifies every target in order, calls `validate_project()` exactly once with the canonical root/context while the lock exists, returns the exact redacted summary/count, leaves evidence staged and canonical evidence unchanged, and keeps the journal `post-validating`.
2. Return invalid, malformed, and warning-only validator results; assert the exact post-apply summary codes and warning semantics.
3. Force a changed target to exact before and assert validator zero-call, same-lock rollback, `POST_APPLY_TARGET_MISMATCH`, and exact original canonical state.
4. Inject foreign state into changed, unchanged, and evidence targets; assert `TRANSACTION_RECOVERY_REQUIRED`, `POST_APPLY_TARGET_UNPROVEN`, retained recovery material, and no speculative overwrite or false rolled-back claim.
5. Raise a validator exception containing private paths/payloads and assert only stable redacted codes reach the error and rollback signal.
6. Assert successful rollback and recovery-required signals detach and validate optional post-apply summaries; forward apply failures retain `None`.
7. Throw from the caller body after `_PrivatePostValidatedState` is yielded and assert zero validation retry, classification, or rollback.
8. Preserve projected validation, B2b apply/rollback, journal, authorization, evidence staging, and redaction regressions.

Tests use only `unittest`, `unittest.mock`, and local temporary directories. They do not spawn processes, simulate real restart, access Git/network, run full discovery, run complete validation-distribution, or run release gates.

## Rejected Alternatives

### Outer post-validation context

Wrapping `_private_applied_workspace()` would technically retain the inner lock while the outer body runs, but it would duplicate rollback timestamps, journal hash plumbing, failure conversion, and private workspace access. The ownership boundary would be harder to audit.

### Rebuild a projected root from canonical state

This adds another full copy and validates a derivative snapshot instead of the actual canonical project. It is slower and still requires separate exact target proof.

### Duplicate individual validators

Calling issue, lifecycle, loop, and Production Record validators separately creates a second definition of project validity and risks divergent results. The established bound `validate_project()` call remains authoritative.

## Out of Scope

- final evidence rebinding, rendering, staging, or canonical replacement;
- `finalizing` or `complete` journal transitions;
- public `apply_lifecycle_transaction()` result mapping;
- idempotent replay and completed-evidence lookup;
- restart/crash loading through `recover_incomplete_transaction()`;
- cleanup or scrubbing of preimages, stages, manifests, journals, or workspaces;
- lifecycle/loop/production public adapters;
- Doctor, audit, distribution, and release-gate integration;
- any plugin, runner, Prefect, service, daemon, database, configuration, schedule, or external control plane.

## Compatibility

- No public command, CLI JSON, plugin, setting, or dependency changes.
- Existing projected-validation behavior remains unchanged.
- B2b successful apply behavior gains one mandatory pre-yield validation step and returns the more specific private post-validated state.
- Existing B2b rollback signals keep their codes and progress semantics; the new optional summary attribute is additive.
- Existing public lifecycle, loop, production, validation, Doctor, and release commands still cannot reach this private boundary.
- The journal schema and phase vocabulary remain unchanged.
- Fifteen existing untracked Issue 103 implementation plans remain untouched and unstaged.
