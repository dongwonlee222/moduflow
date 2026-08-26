# Issue 103 B2b-1 Durable Canonical Apply Design

## Artifact Links

- **Issue ID:** `103-atomic-lifecycle-state-transaction`
- **Source request:** 2026-08-26 continuation after B2a — keep the remaining apply, rollback, finalization, and recovery work in short reviewed slices.
- **Owner / decision maker:** Dongwon Lee
- **Phase:** plan
- **Next command:** write the B2b-1 implementation plan after human review

## Decision

Implement only the private successful canonical-apply path from durable `prepared` state through durable `post-validating` state.

B2b-1 rechecks targets in plan order while the existing B1b lock remains held. It atomically promotes each changed non-evidence staged proposal onto its canonical basename, synchronizes the target parent, verifies the installed bytes, and durably appends that target index to the `applying` journal. Unchanged targets are rechecked but not replaced or recorded. The provisional evidence target is left staged for B2c.

B2b-1 is not a public transaction engine and is not PR-ready by itself. If any operation fails after canonical replacement begins, it preserves the transaction workspace, preimages, recovery manifest, remaining staged proposals, and latest durable journal and raises a bounded error. B2b-2 will add immediate reverse-order rollback before any public adapter can call this boundary.

## Purpose and Success Boundary

B2a proves that every selected target matches the immutable A2 preimage before private preparation. Outside editors are not fenced by the ModuFlow lock, so a target can still change after that batch preflight. B2b-1 therefore performs a narrower preimage comparison at each target's turn and records durable forward progress after every successful replacement.

B2b-1 succeeds when:

> Under one existing write-authorized lifecycle lock, every unchanged ordinary target is reverified, every changed ordinary target is promoted in deterministic order and recorded durably, the provisional evidence target remains staged, and the journal reaches `post-validating` without constructing a terminal result.

The completed slice ends at this exact state:

```text
canonical ordinary targets = planned proposed bytes
canonical evidence target = original preimage/absence
evidence staged proposal = still present and private
journal phase = post-validating
applied_target_indexes = every changed non-evidence target in apply order
rollback_target_indexes = []
lock = held until the private context exits
```

## Selected Architecture

### Files and Ownership

- `scripts/project_lifecycle_transaction_storage.py` owns descriptor-relative single-target verification, staged-proposal ownership checks, canonical replacement, target-parent synchronization, and installed-byte verification.
- `scripts/project_lifecycle_transaction.py` owns timestamp validation, phase transitions, target iteration, applied-index accumulation, and durable journal ordering.
- `tests/test_project_lifecycle_transaction_storage.py` owns one-target replacement, descriptor safety, ownership/race, durability, and no-cleanup failure cases.
- `tests/test_project_lifecycle_transaction.py` owns lock continuity, target ordering, journal progress, evidence exclusion, pre-lock failure ordering, and the `post-validating` handoff.

No new module, public command, plugin, configuration, service, dependency, or resident process is introduced.

### Storage Interfaces

Add to the storage module:

```python
def verify_canonical_target(workspace, target) -> int:
    """Prove one canonical target still equals its immutable preimage."""


def apply_staged_target(workspace, target, staged_proposal) -> int:
    """Promote one verified ordinary proposal and return its target index."""
```

Both interfaces accept only the existing private `_PrivateTransactionWorkspace`, one validated `StorageTarget`, and, for apply, its matching `StagedProposal`. They return only a non-negative target index and never return bytes, paths, descriptors, hashes, modes, or metadata.

`verify_canonical_target()` reuses B2a's descriptor-relative preimage verifier against `workspace._root_fd`. It exists so unchanged ordinary targets can be rechecked without reopening the absolute canonical root or rechecking the full batch.

`apply_staged_target()` rejects unchanged targets, the `evidence` role, non-staged proposals, index mismatch, unexpected staging names, parent-device mismatch, and invalid private records with the existing `STORAGE_CONTEXT_INVALID` boundary before replacement.

### Verification Refactor

Refactor B2a's private `_verify_canonical_preimage()` implementation around one internal exact-state reader that can prove either:

- the target's original existence and `_before_bytes`/`before_sha256`; or
- the installed proposal's existence and `_after_bytes`/`after_sha256`.

The B2a public batch contract and its `LifecycleCanonicalConflict` behavior remain unchanged. Pre-replacement mismatch still raises `CANONICAL_PREIMAGE_CONFLICT`. Post-replacement inability to prove the proposed bytes raises the existing bounded `STORAGE_VERIFY_FAILED`, because canonical mutation has already occurred and rollback/recovery—not a pre-apply conflict result—is required.

The generalized reader retains B2a's guarantees:

- root/parent traversal uses directory descriptors and `O_NOFOLLOW`;
- the final entry is checked before open, against the opened descriptor, and after read;
- exact size, SHA-256, and constant-time byte equality are required;
- every descriptor closes on every exit;
- no absolute child path or `Path.resolve()` is used.

### One-Target Promotion

For one changed ordinary target, `apply_staged_target()` performs:

1. validate workspace, target, proposal, index, role, state, staging name, size, digest, and parent-device binding;
2. reverify the canonical target against its immutable preimage;
3. reverify the staged proposal's device/inode, mode `0600`, link count, exact bytes, and digest;
4. call `os.replace(staged_basename, canonical_basename, src_dir_fd=parent_fd, dst_dir_fd=parent_fd)` within the already opened target parent;
5. call `os.fsync(parent_fd)` so the directory-entry change is durable;
6. verify the canonical basename now identifies a regular file with the exact proposed size, digest, and bytes;
7. return `target.index`.

The staged proposal is already on the target parent filesystem, so this one-file promotion is an atomic directory-entry replacement. The overall multi-target operation remains application-level atomicity and must never be described as one kernel-atomic transaction.

B2b-1 performs no canonical `mkdir`, `unlink`, write, truncate, chmod, or path-based copy. A promoted staged file retains its restrictive mode `0600`; no file-mode preservation contract is added to the byte-oriented A2 target schema in this slice.

### Portable Race Limit

The B1b lock serializes ModuFlow writers but cannot stop unrelated processes. Portable POSIX filesystems provide no compare-and-swap operation that atomically combines byte comparison with replacement of an existing pathname. B2b-1 narrows the exposure by comparing immediately before `os.replace()` and verifying immediately after parent synchronization, but it does not claim to eliminate an external write in those unavoidable instruction gaps.

B2c post-validation will inspect the complete applied state, and B2b-2/B2d will restore or recover any state that cannot be proven. No mtime, inode, or open-descriptor shortcut is represented as external-writer fencing.

## Orchestration and Journal Flow

### Private Applied State

Add one private detached state:

```python
@dataclass(frozen=True)
class _PrivateAppliedState:
    storage_targets: tuple
    preimages: tuple
    staged_proposals: tuple
    recovery_manifest: transaction_storage.RecoveryManifest
    applied_target_indexes: tuple[int, ...]
    journal_sha256: str
    created_at: str
    _workspace: object = field(repr=False, compare=False)
```

Add `created_at` to `_PrivatePreparedState` so every later journal snapshot preserves the original `planned` timestamp without reading or parsing a private journal pathname.

Add the context boundary:

```python
@contextmanager
def _private_applied_workspace(
    plan: LifecycleTransactionPlan,
    *,
    journal_clock=None,
    lock_clock=None,
    lock_pid=None,
    lock_token_factory=None,
):
    """Apply ordinary targets and yield durable post-validating state."""
```

This context enters `_private_prepared_workspace()` and performs all remaining work before that inner context exits. The existing lifecycle lock therefore remains continuously held from B2a batch preflight through `post-validating` persistence.

### Pre-Lock Timestamp Snapshot

Malformed timestamps must fail before lock acquisition or private/canonical side effects. `_private_applied_workspace()` therefore:

1. validates the plan, writable bound context, and detached storage targets;
2. derives the ordered changed non-evidence indexes;
3. consumes and validates exactly `5 + len(changed_non_evidence_indexes)` journal timestamps before entering `_private_prepared_workspace()`:
   - three for `planned`, `staged`, and `prepared`;
   - one for initial `applying`;
   - one after each successful ordinary replacement;
   - one for `post-validating`;
4. passes the first three validated values to `_private_prepared_workspace()` through a bounded iterator and uses only the remaining fixed values during apply.

The duplicated private plan/context validation is intentional and side-effect free. Denial, malformed plan, invalid target layout, invalid journal timestamp, or invalid phase transition still fails before lock acquisition.

### Journal Serializer Extension

Extend `_serialized_journal_bytes()` with defaulted immutable progress inputs:

```python
def _serialized_journal_bytes(
    plan,
    phase,
    *,
    created_at,
    updated_at,
    recovery_manifest_sha256,
    applied_target_indexes=(),
    rollback_target_indexes=(),
):
```

It converts the tuples to new lists and delegates every prefix, evidence, manifest, and phase invariant to `serialize_transaction_journal()`. Existing B1c calls keep their current empty progress through defaults.

### Exact Phase Order

Inside the still-open prepared context:

```text
prepared / []
→ applying / []
→ target 0 turn
→ applying / [first changed ordinary index]
→ remaining target turns and progress snapshots
→ post-validating / [all changed ordinary indexes]
```

For each ordinary target in `apply_order`:

- `changed == False`: call `verify_canonical_target()` once and persist no progress update;
- `changed == True`: call `apply_staged_target()` once, append its returned index, then persist one new `applying` journal;
- `role == "evidence"`: stop ordinary iteration without verifying, replacing, consuming its staged file, or recording its index.

After the ordinary loop, persist `post-validating` with the complete changed non-evidence index tuple and yield `_PrivateAppliedState`. `rollback_target_indexes` remains empty in every B2b-1 snapshot.

`persist_serialized_journal()` always receives the SHA-256 returned by the immediately previous successful persistence as `expected_previous_sha256`. Journal replacement and workspace-directory synchronization remain owned by B1c3.

## Failure Semantics

B2b-1 is fail-closed and performs no speculative cleanup:

- immediate preimage mismatch: `LifecycleCanonicalConflict` with `CANONICAL_PREIMAGE_CONFLICT` and safe target index;
- invalid workspace/target/proposal relationship: `LifecycleStorageError("STORAGE_CONTEXT_INVALID")`;
- staged entry missing, replaced, symlinked, mode-changed, link-count changed, or device/inode changed: existing bounded owner/verify storage error;
- `os.replace()` failure: new bounded `LifecycleStorageError("STORAGE_REPLACE_FAILED")`;
- parent synchronization failure after replace: existing `STORAGE_DURABILITY_UNCERTAIN`;
- installed canonical bytes or identity cannot be proven: existing `STORAGE_VERIFY_FAILED`;
- journal persistence failure: existing B1c3 bounded storage error;
- invalid pre-lock timestamp or journal record: existing `LifecycleJournalError`.

No error string or representation contains an absolute root, logical path, role, bytes, digest, device/inode, mode, OS error, staging name, manifest payload, journal payload, or exception detail.

### Journal Lag Is Explicit

Canonical replacement, parent synchronization, and journal replacement cannot be committed as one kernel operation. If interruption or failure happens after canonical promotion but before the corresponding progress journal is durable, `applied_target_indexes` is a confirmed lower bound rather than proof that the next target was untouched.

B2b-1 preserves all evidence needed for later classification:

- durable preimages and their absence markers;
- immutable recovery manifest and target/proposal hashes;
- the latest durable journal and its confirmed applied prefix;
- unconsumed staged proposals;
- canonical installed bytes where promotion succeeded.

It does not remove, recreate, restore, retry, restage, advance the journal, emit a terminal result, or claim rollback. B2b-2 and B2d must inspect both the durable journal and actual canonical/stage hashes before deciding what happened.

The lock is released through the existing context-manager path. Because B2b-1 is private and not connected to any public command, no product caller can enter this incomplete failure behavior before B2b-2 is implemented.

B2b-2 will extend `_private_applied_workspace()` by catching apply failures *inside* the still-active `_private_prepared_workspace()` context, performing reverse-order rollback while the same lock remains held, and only then leaving the inner context. The interim B2b-1 failure path releases the lock without rollback solely because no public caller can reach it; this is not the final Issue 103 failure contract.

## Test Contract

### Storage Tests

1. Apply one existing and one previously absent ordinary target; assert exact proposed bytes, restrictive mode `0600`, returned index, removed staging basename, and unchanged unrelated entries.
2. Assert all parent and final operations use descriptor-relative no-follow access, `os.replace()` receives source/destination dir descriptors for the same target parent, and `os.fsync(parent_fd)` occurs before installed-byte verification returns.
3. Reverify an unchanged target without replacement, synchronization, stage consumption, or canonical mutation.
4. Reject evidence, unchanged, mismatched-index, wrong-state, wrong-name, wrong-device, missing, symlinked, non-regular, replaced, mode-changed, linked, truncated, expanded, or corrupted staged proposals before canonical replacement.
5. Inject canonical substitution immediately before replacement and require `CANONICAL_PREIMAGE_CONFLICT` with zero replacement calls.
6. Inject replacement failure, parent-sync failure, and post-replacement verification failure. Preserve the current canonical entry, preimage, manifest, remaining stages, and unknown-state evidence without cleanup or retry.
7. Assert returned values and exception string/repr contain no private paths, payloads, hashes, inode/device values, staging names, or OS errors.
8. Preserve every B2a batch/single-target verification test after the internal exact-state refactor.

### Transaction Integration Tests

1. Apply a mixed plan containing changed, unchanged, absent/new, and evidence targets. Assert ordinary changed targets receive exact proposed bytes, unchanged bytes remain exact, and evidence remains at its preimage/absence with its staged proposal intact.
2. Record exact journal phases and progress: `planned`, `staged`, `prepared`, initial `applying`, one `applying` snapshot per changed ordinary target, then `post-validating`.
3. Assert `created_at` is constant, `updated_at` follows the prevalidated timestamp sequence, every persistence is hash-chained, and applied indexes are the exact changed non-evidence prefix.
4. Assert the lifecycle lock exists during every target verification, replacement, synchronization, and journal persistence and is released after success or failure.
5. Make each pre-lock timestamp position malformed in turn and assert zero lock, workspace, stage, journal, replacement, synchronization, or canonical changes.
6. Inject conflict/storage/journal failure before the first replacement and after each replacement boundary. Assert no terminal result, rollback, cleanup, post-validation, evidence replacement, recovery, Git, subprocess, network, or public adapter call.
7. Assert failure retains the transaction workspace, preimages, manifest, latest durable journal, remaining stages, and actual canonical state for B2b-2/B2d inspection.
8. Preserve existing authorization, B2a conflict, B1c prepared-phase, journal-contract, and evidence-rendering focused regressions.

Tests use only standard-library `unittest`, `unittest.mock`, and local temporary directories. They do not spawn processes, simulate real crashes, access Git or the network, or run validation-distribution, full discovery, or release gates.

## Alternatives Considered

1. **Storage-owned single-target promotion plus orchestration-owned journal progress — selected.** It keeps descriptor/durability mechanics separate from protocol ordering and gives B2b-2 reusable bounded primitives.
2. **Call `os.replace()` directly from the transaction orchestrator — rejected.** It mixes path ownership, proposal verification, descriptor lifetime, durability, and journal sequencing in one already large module.
3. **Replace every target and persist one final progress snapshot — rejected.** A crash would erase deterministic knowledge of the confirmed applied prefix and violate the per-replacement journal contract.
4. **Apply provisional evidence with ordinary targets — rejected.** B1d excludes self-reference and requires final result/evidence binding after post-validation.
5. **Add rollback to the same slice — rejected.** The combined failure matrix recreates the oversized long-running boundary this decomposition is intended to avoid.
6. **Use mtime/inode/open descriptors as a portable external-writer fence — rejected.** They support identity checks but cannot make comparison plus pathname replacement atomic.
7. **Add OS-specific `renameat2` or filesystem snapshots — rejected.** They are not portable, do not solve replacement of every existing pathname consistently, and would add platform/product weight.

## Out of Scope

- rollback, reverse restoration/removal, rollback journals, or rollback verification;
- post-apply validator execution or projected/canonical cross-artifact validation;
- final result/status construction, `conflict`, `rolled_back`, `recovery_required`, `applied`, or `noop` return envelopes;
- final evidence rendering/rebinding/replacement or evidence applied-index progress;
- private payload/stage/manifest cleanup or terminal `complete` journal;
- incomplete-journal loading, retry, idempotency lookup, stale-state classification, or crash recovery;
- public lifecycle, loop, roadmap, issue-index, Production Record, CLI, Doctor, operation inventory, distribution, review, PR, or release adapters;
- canonical parent creation, file-mode preservation, ACL/xattr preservation, Git metadata handling, remote calls, plugins, runners, Prefect, databases, subprocesses, network access, or external dependencies.

## Compatibility and Product Weight

- A1/A2/A3, B1a/B1b/B1c/B1d, and B2a public and private validated contracts remain compatible.
- Existing lifecycle, loop, production, validation, Doctor, and release commands remain unchanged and cannot call B2b-1.
- The journal schema and phase vocabulary do not change; B2b-1 activates existing `applying` and `post-validating` invariants.
- B2b-1 adds two internal storage functions, one private orchestration context, one private state, progress parameters on an existing private serializer, and focused tests in existing files.
- It adds no module, command, configuration, dependency, startup work, scheduled task, resident process, public decision, or external system.
- Full validation-distribution, discovery, audit, and release verification remain deferred until D2.
