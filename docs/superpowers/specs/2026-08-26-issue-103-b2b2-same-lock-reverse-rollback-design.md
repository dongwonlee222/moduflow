# Issue 103 B2b-2 Same-Lock Reverse Rollback Design

## Artifact Links

- **Issue ID:** `103-atomic-lifecycle-state-transaction`
- **Source request:** 2026-08-26 continuation after B2b-1 durable canonical apply.
- **Owner / decision maker:** Dongwon Lee
- **Phase:** design approved in conversation; written-spec review pending
- **Predecessor:** `docs/superpowers/specs/2026-08-26-issue-103-b2b1-durable-canonical-apply-design.md`
- **Next command:** write the B2b-2 implementation plan after written-spec approval

## Decision

Add immediate deterministic rollback for bounded failures raised before `_private_applied_workspace()` yields its successful `post-validating` state.

B2b-2 keeps the existing B1b lifecycle lock held, classifies every changed non-evidence canonical target as exact `before` or exact `after`, derives the attempted forward prefix, and restores that prefix in reverse order. Existing targets are replaced from verified preimages; newly created targets are removed. Every completed reverse step is durably journaled.

Successful rollback becomes a private `TRANSACTION_ROLLED_BACK` signal instead of re-raising the original apply error. Unknown canonical state or any rollback/journal failure becomes `TRANSACTION_RECOVERY_REQUIRED`, with all private recovery material retained.

B2b-2 does not catch exceptions thrown by a caller after the context has yielded. B2c will move post-apply validation inside the same private boundary so validation failures can use this rollback mechanism without treating arbitrary caller failures as transaction failures.

## Purpose and Success Boundary

B2b-1 intentionally preserved state and released the lock on failure because no public caller could reach the incomplete path. B2b-2 closes that temporary gap for same-process, pre-yield failures.

B2b-2 succeeds when either:

1. the forward path reaches durable `post-validating` and yields `_PrivateAppliedState` unchanged; or
2. a bounded forward failure occurs, every attempted ordinary target is proven restored to its exact preimage/absence in reverse order, a durable `rolled-back` journal exists, and `LifecycleApplyRolledBack` is raised while the lock remains continuously held until rollback persistence finishes.

The successful rollback boundary is exact:

```text
canonical ordinary targets = exact original bytes/absence
canonical evidence target = original bytes/absence
evidence staged proposal = retained and private
journal phase = rolled-back
applied_target_indexes = attempted changed non-evidence prefix
rollback_target_indexes = exact reverse of applied_target_indexes
workspace/preimages/manifest = retained
public transaction result = not constructed
```

If exact rollback cannot be proven, B2b-2 makes one attempt to persist `recovery-required`, retains every recovery artifact and the actual canonical state, and raises `LifecycleRecoveryRequired`. If that final persistence also fails, the latest earlier durable journal remains authoritative.

## Alternatives Considered

1. **Actual-state reconciliation plus reverse rollback — selected.** It covers replacement success followed by parent-sync, installed-verification, or progress-journal failure, where durable and in-memory progress can lag canonical state.
2. **Use only the in-memory `applied` list — rejected.** `apply_staged_target()` can mutate canonical state and fail before returning, so the current target would be omitted.
3. **Skip immediate rollback and depend on restart recovery — rejected.** It would release the lock with a known partial write and violate the same-operation rollback contract.
4. **Implement full crash recovery now — rejected.** Loading old workspaces, stale-state classification, replay, and finalization belong to B2d and would recreate an oversized slice.

## Selected Architecture

### Files and Ownership

- `scripts/project_lifecycle_transaction_storage.py` owns exact state classification, durable preimage verification, rollback-stage creation, descriptor-relative replacement/removal, parent synchronization, and final before-state proof.
- `scripts/project_lifecycle_transaction.py` owns bounded signals, timestamp reservation, forward-prefix derivation, reverse ordering, rollback/recovery-required journal ordering, and same-lock exception handling.
- `tests/test_project_lifecycle_transaction_storage.py` owns restore/remove mechanics, descriptor safety, race/failure behavior, and preservation tests.
- `tests/test_project_lifecycle_transaction.py` owns forward-boundary failure matrices, lock continuity, prefix reconciliation, journal chaining, signals, and success compatibility.

No new module, public command, configuration, service, dependency, process, plugin, runner, or external system is added.

### Storage Interfaces

Add:

```python
def classify_canonical_target(workspace, target) -> str:
    """Return exact 'before' or 'after'; reject every unknown state."""


def rollback_canonical_target(workspace, target, preimage) -> int:
    """Restore one exact after-state target to its before state."""
```

Both accept only the existing private workspace and detached validated storage records. They return no bytes, paths, hashes, descriptors, metadata, or mutable values.

`classify_canonical_target()` is valid only for changed non-evidence targets. It returns:

- `"before"` when exact original bytes or original absence are proven;
- `"after"` when exact proposed bytes are proven;
- `LifecycleStorageError("STORAGE_CANONICAL_STATE_UNKNOWN")` for foreign bytes, missing/present mismatch, unsafe traversal, symlink, directory, unstable identity, read failure, or any state that is neither exact before nor exact after.

Changed targets have distinct before and after states. Unchanged and evidence targets are rejected with `STORAGE_CONTEXT_INVALID`.

`rollback_canonical_target()` validates the target/preimage relationship and rechecks that the target remains exact `after` immediately before mutation.

### Existing-Target Restoration

For `target.existed == True`, rollback performs:

1. verify the private preimage record index, state, deterministic name, size, digest, device/inode, mode `0600`, link count `1`, exact bytes, and stable identity;
2. open the canonical target parent through descriptors;
3. create a deterministic `.moduflow-rollback-<transaction-digest>-<index>` file in that parent with exclusive/no-follow flags and mode `0600`;
4. write the original bytes, synchronize the file, and reverify stage ownership, mode, link count, size, digest, and bytes;
5. reverify the canonical basename is exact `after`;
6. call `os.replace(rollback_stage, canonical_basename, src_dir_fd=parent_fd, dst_dir_fd=parent_fd)`;
7. synchronize the target parent;
8. prove the canonical basename is exact `before`.

The rollback stage is separate from the consumed forward stage. The restored file remains mode `0600`; mode, ownership, ACL, and xattr preservation remain outside the A2 byte contract.

### Newly Created Target Removal

For `target.existed == False`, the preimage must be the exact `absent` marker. Rollback opens the target parent, proves exact `after`, calls `os.unlink(canonical_basename, dir_fd=parent_fd)`, synchronizes the parent, and proves absence.

No recursive delete, parent removal, canonical parent creation, or path-based unlink is allowed.

### Already-Before Targets

An index inside the attempted prefix may already be exact `before`, for example after an unrelated exact restoration. It requires no storage mutation but is still appended to `rollback_target_indexes` in reverse order because the original state is proven.

## Attempted-Prefix Reconciliation

The forward loop retains indexes whose `apply_staged_target()` calls returned successfully. On a bounded forward failure, B2b-2 classifies every changed non-evidence target in apply order.

The attempted prefix length is the maximum of:

- the length of the in-memory successful-return prefix; and
- one past the last changed ordinary target classified exact `after`.

Every target after that prefix must be exact `before`. Every target inside it must be exact `before` or `after`. Any unknown state or non-prefix relationship becomes recovery-required without speculative mutation.

This covers replacement followed by parent-sync failure, installed-verification failure, progress-journal failure, and an earlier attempted target already restored while a later target remains exact after. The resulting indexes remain a prefix of changed non-evidence indexes and satisfy the existing journal invariant.

## Orchestration and Journal Flow

### Bounded Signals

Add:

```python
class LifecycleApplyRolledBack(RuntimeError):
    code = "TRANSACTION_ROLLED_BACK"


class LifecycleRecoveryRequired(RuntimeError):
    code = "TRANSACTION_RECOVERY_REQUIRED"
```

`LifecycleApplyRolledBack` exposes only the original bounded error code, attempted applied-index tuple, rollback-index tuple, and final journal SHA-256.

`LifecycleRecoveryRequired` exposes only the original bounded error code, bounded rollback error code, confirmed applied-index tuple, confirmed rollback-index tuple, and last known durable journal SHA-256.

Constructors validate every field. `str()` and `repr()` contain only the top-level stable signal code. They never render roots, logical paths, roles, bytes, payload hashes, staging names, device/inode values, modes, OS text, manifest/journal payloads, or exception details.

The forward catch accepts only `LifecycleCanonicalConflict`, `LifecycleStorageError`, and `LifecycleJournalError`. Programming errors, `KeyboardInterrupt`, and unrelated caller exceptions are not converted.

### Pre-Lock Timestamp Reservation

Let `n` be the changed non-evidence target count. Validate exactly `8 + 2*n` timestamps before lock acquisition:

- `5 + n` existing forward timestamps;
- one initial `rolling-back` timestamp;
- `n` possible rollback progress timestamps;
- one terminal `rolled-back` timestamp;
- one reserved `recovery-required` timestamp.

The success path uses only the first `5 + n` values. Unused rollback values are deliberately prevalidated so malformed input fails before lock or storage effects on every possible path.

### Successful Reverse Sequence

Persist this exact hash-chained sequence:

```text
current prepared/applying/post-validating journal
→ rolling-back / applied=<attempted prefix>, rollback=[]
→ one rolling-back snapshot per reverse index
→ rolled-back / rollback=<full reverse prefix>
→ raise TRANSACTION_ROLLED_BACK
```

`created_at` remains the original planned timestamp. Evidence is never included. The lock exists during classification, every restore/remove operation, final verification, and every persistence.

### Recovery-Required Sequence

If classification, rollback mutation, verification, or rollback journal persistence fails:

1. stop reverse processing immediately;
2. retain local confirmed applied and rollback prefixes;
3. make one attempt to persist `recovery-required` with the reserved timestamp and latest successful journal SHA;
4. retain the earlier durable journal if this attempt fails;
5. raise `LifecycleRecoveryRequired` from the bounded rollback failure.

No retry, cleanup, second restore, stage recreation, forward retry, lock reacquisition, or recursive error handling occurs.

### Catch Boundary

The forward `try/except` ends before yielding `_PrivateAppliedState`. A caller exception after yield is not rolled back in B2b-2. B2c owns moving post-validation inside this catch boundary.

## Failure Codes and Preservation

Storage uses these bounded codes:

- invalid workspace/target/preimage relationship: `STORAGE_CONTEXT_INVALID`;
- canonical state neither exact before nor exact after: `STORAGE_CANONICAL_STATE_UNKNOWN`;
- rollback-stage collision or unsafe ownership: existing bounded conflict/owner code;
- rollback-stage write failure: existing `STORAGE_WRITE_FAILED`;
- rollback replacement failure: existing `STORAGE_REPLACE_FAILED`;
- newly created target removal failure: new `STORAGE_REMOVE_FAILED`;
- file or parent synchronization uncertainty: existing `STORAGE_DURABILITY_UNCERTAIN`;
- restored/absent state cannot be proven: existing `STORAGE_VERIFY_FAILED`;
- journal persistence failure: existing B1c3 bounded storage code.

On recovery-required, retain:

- workspace and restrictive directory modes;
- exact preimages and absence markers;
- immutable recovery manifest;
- latest durable journal and hash;
- unconsumed forward stages;
- any rollback stage, including partial or uncertain state;
- actual canonical bytes/absence left by the failed step;
- provisional evidence stage.

No error rendering contains private payload or path data.

## Portable Race Limit

The B1b lock serializes ModuFlow writers but not unrelated processes. B2b-2 narrows races through immediate exact-state checks and descriptor-relative mutation, then verifies the final before state. Portable POSIX cannot atomically combine byte comparison with replace or unlink.

An unrelated mutation in an instruction gap produces unknown state, verification failure, or recovery-required. B2b-2 never claims that inode, mtime, an open descriptor, or the ModuFlow lock fences external writers.

## Test Contract

### Storage Tests

1. Classify existing and absent changed targets as exact before, then as exact after following B2b-1 promotion.
2. Reject unchanged, evidence, malformed records, unsafe parents, symlinks, directories, foreign bytes, unstable identity, missing/present mismatches, and ambiguous state without mutation.
3. Restore an existing exact-after target from a verified private preimage through a same-parent rollback stage; assert original bytes, mode `0600`, returned index, stage consumption, parent synchronization, and final proof.
4. Remove a newly created exact-after target descriptor-relatively; assert parent synchronization, exact absence, returned index, and unchanged unrelated entries.
5. Reject mutated, replaced, missing, symlinked, mode-changed, linked, or corrupted preimages before canonical mutation.
6. Inject canonical races immediately before replace/unlink and preserve foreign entries without overwrite.
7. Inject rollback-stage create/write/fsync/verify, replace, unlink, parent-sync, and final-verification failures. Assert no retry or cleanup and preserve inspectable state.
8. Assert returned values and exception string/repr are redacted.
9. Preserve B1c preimage/manifest, B2a preflight, and B2b-1 apply regressions.

### Transaction Tests

1. Inject bounded forward failures before the first replacement, after each replacement, during parent sync/postverification, during each progress journal, and during post-validating persistence.
2. Assert attempted-prefix reconciliation when the journal lags canonical state and when an earlier attempted target is already exact before.
3. Assert existing and newly created targets return to exact original bytes/absence in reverse changed-target order while the same lock remains present.
4. Assert hash-chained initial `rolling-back`, one progress snapshot per reverse index, and terminal `rolled-back`; created time remains constant and updated times use reserved values.
5. Assert successful rollback raises only `TRANSACTION_ROLLED_BACK` with safe attributes and never yields `_PrivateAppliedState`.
6. Inject classification, restore/remove, rollback progress-journal, terminal-journal, and recovery-required-journal failures. Assert `TRANSACTION_RECOVERY_REQUIRED`, confirmed prefixes, latest durable phase, and retained recovery material.
7. Make each of `8 + 2*n` timestamps malformed and assert zero lock, workspace, journal, stage, canonical mutation, rollback, Git, subprocess, network, or public call.
8. Assert the B2b-1 success path stays compatible apart from prevalidating unused rollback timestamps.
9. Throw from the context body after `_PrivateAppliedState` is yielded and assert B2b-2 performs no rollback.
10. Preserve authorization, journal, prepared-phase, evidence-rendering, and redaction regressions.

Tests use only standard-library `unittest`, `unittest.mock`, and local temporary directories. They do not spawn processes, simulate real restart, access Git/network, run validation-distribution, run full discovery, or run release gates.

## Out of Scope

- post-apply validator execution or validation-summary construction;
- rollback of a future B2c validation failure until validation moves inside this boundary;
- final evidence rendering, rebinding, or replacement;
- terminal public `LifecycleTransactionResult` construction or adapter mapping;
- private payload, stage, manifest, journal, or workspace cleanup;
- loading an existing incomplete journal after restart;
- stale lock handling, lock takeover, retry, replay, idempotency lookup, or deterministic crash recovery;
- public lifecycle, loop, roadmap, issue-index, Production Record, CLI, Doctor, audit, distribution, review, PR, or release integration;
- canonical parent creation/removal, recursive deletion, mode/ACL/xattr/ownership preservation, Git metadata, remote calls, plugins, runners, Prefect, databases, subprocesses, network access, or external dependencies.

## Compatibility and Product Weight

- B2b-1 successful apply behavior and `_PrivateAppliedState` remain compatible.
- Existing public lifecycle, loop, production, validation, Doctor, and release commands remain unchanged and cannot reach B2b-2.
- The journal schema and phase vocabulary remain unchanged; B2b-2 activates existing `rolling-back`, `rolled-back`, and `recovery-required` invariants.
- B2b-2 adds two private storage interfaces, two bounded private signals, rollback orchestration inside the existing private context, and focused tests in existing files.
- It adds no module, command, configuration, startup work, scheduled task, resident process, dependency, database, network call, or external control plane.
- Full validation-distribution, discovery, audit, and release verification remain deferred until D2.
