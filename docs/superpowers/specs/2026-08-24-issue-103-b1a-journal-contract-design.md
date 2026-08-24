# Issue 103 B1a Journal Contract Design

## Artifact Links

- **Issue ID:** `103-atomic-lifecycle-state-transaction`
- **Source request:** 2026-08-24 execution continuation — finish Issue 103 in short, independently reviewable slices after A3 projected validation.
- **Owner / decision maker:** Dongwon Lee
- **Phase:** plan
- **Next command:** write the B1a journal-contract implementation plan

## Decision

Implement only the pure recovery-journal contract in the next slice. B1a defines the exact redacted JSON snapshot, allowed phase vocabulary, legal phase transitions, and progress invariants. It performs no filesystem I/O and does not acquire a lock, create a transaction directory, persist payloads, stage proposed files, replace canonical files, roll back, recover, or finalize durable evidence.

This separates protocol correctness from filesystem durability. B1b will own exclusive lock behavior, B1c will own private staging and atomic journal persistence, and B1d will own redacted evidence rendering.

## Purpose

Issue 103 must survive interruption without guessing which canonical targets were replaced or restored. The journal is the private, local record used by later apply and recovery code. If its schema, phase, or progress can be interpreted loosely, recovery may make an unsafe choice.

B1a succeeds when:

> Given one proposed journal snapshot, ModuFlow either returns an exact detached redacted dictionary or rejects it with a stable bounded error, without touching the filesystem.

## Selected Architecture

### Schema

The schema name is:

```python
JOURNAL_SCHEMA = "moduflow.lifecycle-transaction-journal.v1"
```

Every snapshot has exactly these keys:

```text
schema
transaction_id
idempotency_key
phase
targets
recovery_manifest_sha256
applied_target_indexes
rollback_target_indexes
created_at
updated_at
```

The contract deliberately excludes canonical-root paths, artifact bytes, proposed bytes, temporary absolute paths, exception messages, and secrets.

### Target Records

`targets` reuses the existing redacted transaction target schema and order. It contains logical project-relative paths, before/after hashes, proposed byte counts, validation rule IDs, and apply/rollback ordering. It never contains `PlannedTarget._before_bytes` or `PlannedTarget._after_bytes`.

Target indexes refer to positions in this ordered redacted target list. A later deterministic storage layout may use the same indexes for numbered recovery payloads, without adding private payload paths to the journal contract.

### Recovery Manifest Hash

`recovery_manifest_sha256` is either `absent` before a private manifest exists or a lowercase SHA-256 digest. B1c will create the manifest and replace `absent` with its digest before the journal reaches `prepared`.

The journal stores only the manifest hash. Manifest entries and original artifact bytes remain in restrictive transaction-private storage.

### Progress

`applied_target_indexes` records successfully replaced changed targets in forward apply order. `rollback_target_indexes` records successfully restored or removed targets in reverse order.

Both lists must contain unique non-boolean integers within the target range. Applied progress must be a prefix of changed targets in apply order. Rollback progress must be a prefix of the reverse applied order and therefore cannot name an unapplied target.

### Phase Vocabulary

Only these phases are accepted:

```text
planned
staged
prepared
applying
post-validating
finalizing
rolling-back
complete
rolled-back
recovery-required
```

Normal forward transitions are:

```text
planned -> staged -> prepared -> applying -> post-validating -> finalizing -> complete
```

Failure and cleanup transitions are:

```text
planned|staged -> rolled-back|recovery-required
prepared|applying|post-validating|finalizing -> rolling-back|recovery-required
rolling-back -> rolled-back|recovery-required
```

`applying -> applying` and `rolling-back -> rolling-back` are allowed only for durable progress snapshots. Terminal `complete` and `rolled-back` snapshots have no outgoing transition. An explicit recovery attempt may move `recovery-required` to `rolling-back` or `finalizing`; normal execution may not do so.

### Pure Interfaces

```python
def serialize_transaction_journal(journal: dict) -> dict:
    """Validate and return a detached redacted journal snapshot."""


def validate_journal_phase_transition(
    current_phase: str,
    next_phase: str,
    *,
    recovery: bool = False,
) -> None:
    """Reject an illegal journal transition without side effects."""
```

`serialize_transaction_journal()` follows the existing strict plan/result serializer style: dictionaries only, exact keys, detached lists/dictionaries, logical target paths, safe hashes, and no caller-owned mutable values in the return value.

### Safe Error Contract

Contract failures raise `LifecycleJournalError`, a `ValueError` subtype with a stable `code` and a bounded message containing no record values.

Required codes:

- `JOURNAL_RECORD_INVALID`
- `JOURNAL_SCHEMA_UNSUPPORTED`
- `JOURNAL_PHASE_INVALID`
- `JOURNAL_TRANSITION_INVALID`
- `JOURNAL_PROGRESS_INVALID`

The serializer converts lower-level target validation failures to `JOURNAL_RECORD_INVALID` so an error cannot echo a caller-provided path or value.

## Phase-Dependent Invariants

- `planned` and `staged` require empty applied and rollback progress.
- `prepared` requires a manifest SHA-256 and empty applied and rollback progress.
- `applying` may contain a forward applied prefix and requires empty rollback progress.
- `post-validating` and `finalizing` require every changed target to appear in applied progress and require empty rollback progress.
- `rolling-back` requires rollback progress to be a reverse prefix of applied progress.
- `complete` requires every changed target applied, no rollback progress, and a manifest SHA-256.
- `rolled-back` requires every applied target represented in rollback progress; a pre-apply cleanup may use two empty progress lists.
- `recovery-required` preserves any structurally valid progress prefix so a later explicit recovery can inspect it.

B1a validates these invariants but does not decide when to persist snapshots. B1c owns durability ordering, and B2 owns apply/recovery decisions.

## Alternatives Considered

1. **Implement all of B1 in one filesystem-heavy change — rejected.** Lock ownership, safe staging, durable replacement, and evidence would make failures slow to isolate and recreate the long-running task problem.
2. **Use a frozen journal dataclass — rejected for this boundary.** The journal is a sequence of persisted JSON snapshots, not one immutable domain object. Exact dictionary validation keeps disk loading and in-memory serialization on the same path.
3. **Accept a loose dictionary and validate only during recovery — rejected.** Corrupt or ambiguous progress could be persisted and discovered only after interruption, when the recovery path must be most conservative.

## Test Contract

B1a uses fast pure unit tests only:

1. Accept one valid snapshot for every allowed phase.
2. Reject missing/unknown keys and unsupported schemas without echoing values.
3. Reject unknown phases and illegal normal/recovery transitions.
4. Reject duplicate, boolean, negative, out-of-range, non-prefix, and wrong-order progress.
5. Enforce phase-dependent manifest and progress invariants.
6. Prove returned targets and progress lists are detached from caller-owned inputs.
7. Prove artifact bytes, private plan fields, absolute temporary paths, and exception details cannot enter serialized output or error strings.
8. Patch filesystem mutation boundaries and prove zero calls.

The implementation modifies only `scripts/project_lifecycle_transaction.py` and `tests/test_project_lifecycle_transaction.py` after a separate implementation plan is reviewed.

## Out of Scope

- lock creation, ownership records, stale-lock policy, and lock release;
- transaction directory creation and permissions;
- preimage payloads, recovery manifests, and same-filesystem proposed staging;
- `mkstemp`, file/directory `fsync`, and atomic journal replacement;
- canonical hash rechecks, apply, post-apply validation, rollback, and recovery;
- durable evidence rendering and evidence target finalization;
- public lifecycle/production adapters, Doctor diagnostics, and release checks.

No filesystem persistence code is accepted into the B1a commit.

## Compatibility

- A1 intent, plan/result schemas, idempotency, and terminal result statuses remain unchanged.
- A2 immutable plans and A3 private projected validation remain unchanged.
- Existing evidence planning remains unchanged until B1d defines the complete evidence document.
- Existing public lifecycle, loop, and Production Record writers remain unchanged until Stream C.
