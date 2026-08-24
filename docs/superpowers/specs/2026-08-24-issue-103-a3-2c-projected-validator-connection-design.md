# Issue 103 A3.2c Projected Validator Connection Design

## Artifact Links

- **Issue ID:** `103-atomic-lifecycle-state-transaction`
- **Parent plan:** `specs/103-atomic-lifecycle-state-transaction/plan.md`, Task A3 Steps 4-6
- **Predecessors:** commit `d22ef04` (`feat(103): define projected validation summary`) and commit `8966d8a` (`feat(103): overlay projected transaction state`)
- **Owner / decision maker:** Dongwon Lee
- **Phase:** execute, A3.2c design

## Decision

Add the public read-only boundary `validate_projected_transaction(plan: LifecycleTransactionPlan) -> dict` as a thin orchestrator over the already-reviewed A3 components. It enters `_private_projected_state(plan)`, calls `validate_project_artifacts.validate_project()` exactly once with the private root and its rebound Issue 109 context, converts the full validator result through `_summarize_projected_validation()`, and returns only that redacted summary.

The validator already invokes issue-schema, lifecycle-consensus, Production Record, loop, memory, workflow, and repository-link checks. A3.2c therefore does not call lifecycle or Production Record validators a second time. It also does not alter `validate_project_artifacts.py`; A3.1 already made its issue-schema path evaluation honor the supplied detached context.

## Purpose

A3.2a defines a stable redacted summary, and A3.2b materializes a verified private copy containing every proposed target byte. A3.2c connects those two boundaries to the existing project validator without granting any canonical replacement behavior. Its success condition is:

> Validate the complete proposed project state only below the authorized private root, return no validator payload or private path, remove the projected tree on every exit path, and leave every canonical byte unchanged.

## Selected Architecture

### Public entry point

```python
def validate_projected_transaction(plan: LifecycleTransactionPlan) -> dict:
    """Validate one private projected state without replacing canonical targets."""
```

The function performs this order:

1. Reject a non-`LifecycleTransactionPlan` argument with the existing bounded `TypeError` contract before entering validation orchestration.
2. Enter `_private_projected_state(plan)`. That boundary performs Issue 110 `write` authorization, target preflight, safe snapshot copying, proposed-byte overlay, digest verification, projected-context rebinding, and cleanup ownership.
3. Call `validate_project_artifacts.validate_project(projected.root, project_context=projected.context)` exactly once while the projected root exists.
4. Pass the complete `moduflow.project-validation.v1` result directly to `_summarize_projected_validation()`.
5. Return only `valid`, the fixed `rule_ids`, and stable `error_codes`.
6. Exit the projected-state context so populated private files and the randomized private root are removed before control returns to the caller.

The function never returns the projected root, projected context, validator result, diagnostic text, warnings, issue-schema payloads, lifecycle drift messages, or artifact bytes.

### Import and call boundary

`project_lifecycle_transaction.py` imports the `validate_project_artifacts` module, not a copied function alias. Tests can patch `validate_project_artifacts.validate_project` at the real call boundary and prove call count and arguments. There is no circular dependency: the validator imports the registry directly and loads lifecycle, loop, issue-schema, and Production Record modules only as validator dependencies; it does not import the transaction module.

No subprocess or CLI adapter is used. The Python call preserves the detached projected context and avoids serializing either the private path or full validator output.

### Validation semantics

An invalid proposed project is an expected validation result, not an orchestration exception. The existing summary helper maps the full result as follows:

- project-level errors produce `PROJECTED_PROJECT_INVALID`;
- issue-schema errors produce `PROJECTED_ISSUE_SCHEMA_INVALID`;
- lifecycle drift produces `PROJECTED_LIFECYCLE_DRIFT`;
- a malformed or internally inconsistent validator result produces `PROJECTED_VALIDATION_CONTRACT_INVALID`;
- a valid result produces `valid: true` and an empty `error_codes` list.

The fixed `rule_ids` remain `project-artifacts`, `issue-schema`, `lifecycle-consensus`, and `production-records`. Production failures are present in the validator's project-level `errors` list and therefore collapse to `PROJECTED_PROJECT_INVALID`; A3.2c does not add a second, divergent Production Record result shape.

Warnings do not make projected validation invalid because the existing project validator defines validity from project errors, issue-schema errors, and lifecycle drift. Warnings remain omitted from the transaction summary.

## Error Contract

Expected validation findings return a summary. Operational failures raise bounded errors:

- Issue 110 denials propagate unchanged as `project_operation.ProjectOperationDenied` and occur before projected filesystem side effects or validator invocation.
- Existing projected-state failures propagate unchanged as `LifecycleProjectedValidationError`, including context, target, source, copy, overlay, cleanup, and safety codes defined by A3.2b.
- An unexpected exception from the validator or summary boundary becomes `LifecycleProjectedValidationError("PROJECTED_VALIDATION_FAILED")`.
- A non-plan input retains a direct `TypeError` rather than being mislabeled as a validator runtime failure.

`PROJECTED_VALIDATION_FAILED` exposes only its stable code. The original exception may remain as Python exception chaining for internal debugging, but neither `str(error)` nor the returned summary contains the validator message, canonical path, randomized projected path, diagnostic payload, `_before_bytes`, or `_after_bytes`.

If cleanup itself fails while another operation is leaving the context, the existing `PROJECTED_ROOT_CLEANUP_FAILED` contract remains authoritative because the private tree's lifecycle cannot be claimed complete.

## Canonical Stability and Cleanup

A3.2c owns no canonical write primitive. It does not call file writes, `os.replace`, lock creation, journal persistence, evidence persistence, Git, subprocess, network, or external systems. All writes are limited to the A3.2b private root below canonical `.moduflow` after authorization.

Tests snapshot all canonical fixture files before the call and compare them byte-for-byte afterward for valid-result, invalid-result, and validator-exception paths. They also assert no `*-projected-*` child remains and no canonical replacement boundary was called.

## Test Contract

Implementation follows RED/GREEN TDD with focused tests only:

1. Patch the module-level validator call with a valid complete result; assert exactly one call, assert the root exists during the call, assert the supplied context is bound to that root, and assert the exact redacted valid summary.
2. Call the real validator against deliberately malformed projected issue, state, and Production Record target bytes whose plan size/digest metadata remains internally correct; assert stable summary codes, no validator text or private path in the summary, canonical byte equality, and complete cleanup.
3. Return malformed validator contracts from the patched boundary; assert the existing `PROJECTED_VALIDATION_CONTRACT_INVALID` summary.
4. Raise an unexpected validator exception containing a private path and payload; assert only `PROJECTED_VALIDATION_FAILED`, unchanged canonical bytes, and complete cleanup.
5. Substitute a write-denied detached context; assert the validator is never called and the existing A3.2b zero-side-effect authorization behavior remains intact.
6. Patch canonical replacement boundaries during public projected validation and assert zero calls.

Focused verification consists of the transaction test module, the existing Issue 110 project-operation module, the single fast validator context/readiness tests needed by this boundary, Issue 103 spec consistency, Python compilation, and diff hygiene. A diagnostic run measured the existing minimal validator test at approximately `0.07s` and current private materialization plus one real validator call at approximately `0.02s` on the local workspace.

The complete `tests.test_validation_distribution` module, full discovery, and release check remain deferred to D2 because they exercise broader distribution/release paths unrelated to this thin connection and caused the earlier long-running behavior.

## Rejected Alternatives

1. **Duplicate validation logic in the transaction module — rejected.** It would create a second definition of project validity, drift from the established validator, and bypass A3.1's context-bound fixes.
2. **Invoke the validator CLI in a subprocess — rejected.** It adds process latency, serializes the full private result, weakens direct context injection, and creates unnecessary private-path exposure risk.
3. **Call project, lifecycle, and Production Record validators independently — rejected.** `validate_project()` already invokes those checks. Repeating them wastes time and can produce divergent or duplicated findings.
4. **Add a public validator injection parameter — rejected.** The approved Issue 103 interface is `validate_projected_transaction(plan)`; module-boundary patching provides test isolation without expanding the public API.

## Out of Scope

- changing `scripts/validate_project_artifacts.py` or `tests/test_validation_distribution.py` unless implementation reveals a proven context bug not covered by A3.1;
- changing projected snapshot, overlay, context, or summary semantics already reviewed in A3.2a/A3.2b;
- canonical apply, post-apply validation, replacement ordering, locks, journals, persisted evidence, rollback, crash recovery, or idempotent replay;
- routing existing lifecycle mutation commands through the transaction boundary;
- Git, subprocess, network, or remote-system operations;
- complete validation-distribution, full test discovery, and release checks before D2.

Those behaviors remain in later Issue 103 streams. A3.2c ends when the projected proposal can be validated and summarized without canonical mutation.
