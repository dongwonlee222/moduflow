# Issue 103 B2e Public Apply and Idempotent Replay Design

## Artifact Links

- **Issue:** `103-atomic-lifecycle-state-transaction`
- **Parent plan:** `specs/103-atomic-lifecycle-state-transaction/plan.md`, Task B2 Steps 2–3
- **Predecessors:** `b5bcf6e` (private transaction completion), `f940087` (safe evidence finalization), and `785d22e` (prebound final evidence)
- **Owner / decision maker:** Dongwon Lee
- **Phase:** execute, B2e design

## Decision

Add the first public `apply_lifecycle_transaction()` boundary as a thin orchestrator over the existing planner, projected validator, and B2d private completion engine. Before starting a fresh private transaction, classify the canonical completed evidence already captured by the read-only plan. Return `noop` only when that evidence proves the same semantic transaction and the selected canonical targets still equal the completed after-state.

B2e maps one valid transaction attempt to the six public terminal statuses: `applied`, `noop`, `denied`, `conflict`, `rolled_back`, or `recovery_required`. It does not recover work after restart, scan unrelated transaction workspaces, or remove private recovery material. Those remain B2f responsibilities.

## Purpose

B2d can complete one transaction durably but exposes only `_PrivateCompletedState`. Calling it again for the same intent is intentionally rejected because its final evidence already exists and its private workspace is durable. A public caller therefore still lacks:

- one stable apply entry point;
- a strict public result for B2d success and bounded failures;
- a zero-write retry path that returns the original transaction reference;
- a safe distinction between a completed retry and conflicting or damaged evidence.

B2e closes that boundary without adding recovery, cleanup, adapters, external services, or new dependencies.

## Approaches Considered

### Canonical evidence first, then the private engine — selected

Use the evidence bytes and current target preimages already captured by `plan_lifecycle_transaction()`. Strictly classify the evidence before projected validation, lock acquisition, staging, or journal creation. Exact completed evidence returns `noop`; absent evidence enters the fresh apply path; malformed, foreign, or drifted evidence returns `conflict`.

This keeps retries cheap, avoids creating a second private workspace, and treats permanent canonical evidence as the completed-transaction lookup record.

### Invoke B2d and translate `FINALIZATION_EVIDENCE_ALREADY_PRESENT`

Always run projected validation and enter the B2d completion preparation, then catch the existing evidence-present error as `noop`. Rejected because a retry performs unnecessary validation and timestamp work, depends on a private finalization error for public semantics, and reaches the private workspace boundary before recognizing a completed transaction.

### Use the durable journal as the primary completed index

Open `.moduflow/transactions/<transaction-id>/journal.json` and use terminal `complete` as the retry lookup source. Rejected for B2e because safe journal reopening, incomplete phase classification, restart recovery, and cleanup ownership belong together in B2f. Canonical evidence is already the permanent public-safe record.

## Selected Architecture

### Public orchestration boundary

`apply_lifecycle_transaction()` keeps the planned public signature:

```python
def apply_lifecycle_transaction(
    project_root,
    intent: LifecycleIntent,
    *,
    project_context=None,
    clock=None,
    fault_injector=None,
) -> dict:
    """Return one strict moduflow.lifecycle-transaction.v1 result."""
```

For a valid transaction request it performs these bounded steps:

1. normalize the intent and build one immutable read-only plan;
2. resolve the plan's detached canonical context and require `write` capability before any transaction-local or canonical write;
3. classify the final planned evidence target as absent, completed, or conflicting;
4. return a strict `noop` immediately for completed evidence;
5. for absent evidence, run `validate_projected_transaction()` exactly once;
6. if projected validation is valid, create one `_PrivateCompletionInput` from the normalized intent, the plan-derived next command, and the detached projected summary;
7. invoke `_private_applied_workspace()` once and copy its strict internal result to the public boundary;
8. translate only known bounded signals into a strict terminal result.

Planning may read canonical sources before authorization, but denial occurs before projected-root creation, lock acquisition, transaction workspace creation, temporary files, journal writes, evidence writes, or canonical replacement. Invalid caller contracts and planner contract errors remain safe exceptions rather than fabricated transaction results.

`fault_injector` remains a test-only public seam. B2e must not introduce production scheduling, retry loops, subprocesses, Git operations, network access, or background work through it.

### Completed-evidence classifier

The classifier receives only the immutable plan and normalized intent. It does not perform a second path lookup: it uses the final evidence target's `_before_bytes`, `existed`, and hash captured by the planner, plus the current-before metadata of the other planned targets.

Classification is exact:

- **Absent:** the evidence target did not exist when planned. Continue to projected validation and fresh apply.
- **Completed:** the evidence is strict `moduflow.lifecycle-transaction-evidence.v1`, has `status == "applied"`, and matches the plan's transaction ID, idempotency key, project ID, issue ID, action, target lifecycle, and normalized source event. Its ordinary target roles, logical paths, order, and completed hashes must match the selected plan, and every current ordinary target must still equal the recorded completed after-state.
- **Conflicting:** evidence exists but is malformed, has unknown or missing fields, names another semantic transaction, has a different target layout, or its recorded completed state no longer matches current canonical target hashes or absence markers.

The classifier never treats parseable JSON alone as completion. It never overwrites conflicting evidence and never consults unrestricted content outside the selected plan.

An explicitly supplied idempotency key must still pass `assert_idempotency_key_matches()` during normalization/planning. Reusing a key for another normalized intent remains `IDEMPOTENCY_KEY_CONFLICT`; it cannot become `noop` merely because a transaction-shaped file exists.

### Public `noop` result

The `noop` result points to the original deterministic `transaction_id` and reuses the completed evidence's redacted transaction fields, ordinary target records, validation summaries, next command, actor/source, and original timestamps. It changes only the public status to `noop` and appends one synthesized current evidence target:

- role and logical path come from the plan;
- `existed` is `true`;
- before and after SHA-256 are the exact captured evidence-byte hash;
- byte count is the captured evidence length;
- `changed` is `false`;
- validation rule and plan/rollback order retain the standard evidence target contract.

This makes the returned target list strict and complete without inventing the evidence file's historical preimage, which the self-excluding evidence format intentionally does not contain. The result is passed through `serialize_transaction_result()` before return.

No projected root, clock reservation for the private engine, lock, workspace, stage, journal, validator call, replacement, rollback, or cleanup occurs on the `noop` path.

### Fresh `applied` result

For absent evidence, projected validation must return the exact successful A3 summary. The public boundary derives the next command from the plan rather than trusting a second caller-supplied derived value, then delegates all mutation ownership to B2d.

After `_private_applied_workspace()` yields `_PrivateCompletedState`, the public function returns a detached JSON value built from `completed_state.transaction_result`. It does not reconstruct success from mutable canonical files, rerender evidence, rerun validation, or write another journal snapshot. B2d's terminal `complete` journal and canonical evidence remain the authorities for that completed attempt.

## Terminal Result Mapping

Only validated, redacted values enter public results.

| Condition | Status | Failed stage | Public meaning |
|---|---|---|---|
| B2d yields `_PrivateCompletedState` | `applied` | empty | One transaction completed and its final result is authoritative. |
| Exact completed evidence and exact current after-state | `noop` | empty | The same semantic transaction already completed; no write was attempted. |
| `project_operation.ProjectOperationDenied` | `denied` | `authorization` | Write policy rejected the attempt before side effects. |
| Existing evidence mismatch, invalid projected state, canonical preflight mismatch, or lock contention | `conflict` | the bounded pre-apply stage | The attempt made no canonical change and must not overwrite current state. |
| `LifecycleApplyRolledBack` | `rolled_back` | the original bounded failure stage | Some apply/finalization work may have occurred, but exact before-state restoration was proven. |
| `LifecycleRecoveryRequired`, an existing same-transaction private workspace without completed evidence, or indeterminate lock/storage ownership | `recovery_required` | the bounded uncertain stage | Safe completion or rollback cannot be proven; durable material is retained. |

Known error codes are copied from safe exception fields or assigned from a closed B2e mapping. `rollback_status` is `not-required`, `verified`, or `required` according to the terminal status. Projected and post-apply summaries use the existing strict redacted schemas; missing stages receive deterministic bounded failure summaries rather than validator text.

B2e does not catch arbitrary `BaseException` or relabel an unknown failure as success. It also does not claim `rolled_back` unless the B2d signal proves complete rollback.

## Same-Transaction Workspace Boundary

B2e deliberately checks completed evidence before entering B2d. This permits retrying a B2d-completed transaction even though its private workspace remains durable until B2f cleanup.

If canonical evidence is absent but the same transaction workspace already exists, B2e does not delete, reuse, or guess its phase. It returns `recovery_required` and retains the workspace. Detecting, reopening, and resolving its journal is B2f.

B2e does not scan other transaction IDs before a fresh apply. B2f will add the project-wide incomplete-transaction barrier required before the API is connected to public mutation adapters in Stream C.

## Error and Privacy Contract

- Returned results contain logical paths, sizes, hashes, rule IDs, stable error codes, and timestamps only.
- Evidence parser failures never expose rejected JSON values, payload bytes, absolute paths, validator diagnostics, staging names, journal contents, recovery names, owner tokens, PIDs, or original exception text.
- `str()` and `repr()` of new bounded errors contain only closed error codes.
- The classifier accepts no symlink, special file, duplicate target, path escape, reordered target, unknown field, unsupported schema, or non-`applied` evidence as completion.
- Conflict and denial paths make zero filesystem writes.
- `noop` is not used to conceal canonical drift; drift is a conflict.

## Test Contract

Implementation follows focused RED/GREEN TDD.

1. Prove a fresh valid intent calls planning and projected validation once, enters B2d once, and returns the exact strict `applied` result from `_PrivateCompletedState`.
2. Apply once, retry the same semantic intent, and prove the second result is `noop`, points to the original transaction, preserves original redacted evidence fields, and synthesizes only an unchanged self-evidence target.
3. Prove `noop` performs zero projected-root creation, validator calls, timestamp reads for the private engine, lock, private workspace, stage, journal, replace, rollback, Git, subprocess, or network operations.
4. Reject malformed, foreign, unknown-key, non-`applied`, reordered, duplicate-target, wrong-hash, target-layout, and canonical-drift evidence as `conflict` with zero writes.
5. Prove an explicit key reused for a different normalized intent remains `IDEMPOTENCY_KEY_CONFLICT` and never reaches replay classification or mutation.
6. Map write denial to `denied` before every transaction-local side effect.
7. Map projected invalidity, canonical preflight mismatch, and lock contention to deterministic `conflict` results without claiming rollback.
8. Map B2d verified rollback and indeterminate recovery signals to `rolled_back` and `recovery_required`, preserving only safe progress and validation summaries.
9. Treat an evidence-absent existing same-transaction workspace as `recovery_required` and prove no cleanup or reuse occurs.
10. Prove every returned value passes `serialize_transaction_result()`, is detached from source dictionaries, and leaks none of the forbidden private values.
11. Preserve the focused A1–B2d planner, projection, storage, journal, apply, rollback, validation, and finalization regressions.

Tests use `unittest`, `unittest.mock`, and local temporary directories. They do not simulate real process restart, recover incomplete journals, clean recovery material, run full discovery, run complete validation-distribution, or run release gates. Those remain deferred to B2f and D2.

## Out of Scope

- `recover_incomplete_transaction()` and restart-time phase handling;
- scanning or blocking unrelated incomplete transaction workspaces;
- recovery manifest, preimage, staged proposal, journal, lock-remnant, or workspace cleanup;
- lifecycle, loop, dashboard, issue-index, roadmap, or Production Record public adapters;
- Doctor, operation audit, distribution, release gates, PR publication, merge, or plugin release;
- any Git, subprocess, network, remote, database, service, scheduler, Prefect, or automation control-plane integration.

## Compatibility

- No existing public mutation function is routed through the new boundary in B2e.
- The A2 plan schema, result schema, evidence schema, journal schema, and phase vocabulary do not change.
- The B2d private completion input, evidence binding, completion sequence, rollback ownership, and completed state remain unchanged.
- No dependency, plugin setting, CLI JSON, project artifact schema, or canonical path changes.
- Existing untracked Issue 103 implementation plans remain untouched and unstaged.
