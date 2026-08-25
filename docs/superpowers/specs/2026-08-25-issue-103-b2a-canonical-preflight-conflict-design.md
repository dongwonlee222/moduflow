# Issue 103 B2a Canonical Preflight Conflict Design

## Artifact Links

- **Issue ID:** `103-atomic-lifecycle-state-transaction`
- **Source request:** 2026-08-25 execution continuation after B1d — split B2 into short conflict, apply/rollback, finalization, and crash-recovery boundaries.
- **Owner / decision maker:** Dongwon Lee
- **Phase:** plan
- **Next command:** write the B2a implementation plan after human review

## Decision

Implement only the read-only canonical preflight that runs under the existing B1b lifecycle lock and before B1c creates a private transaction workspace or persists `planned` journal state.

B2a reopens every selected canonical target through descriptor-relative no-follow traversal and proves that its current existence and complete bytes still equal the A2 plan's immutable preimage. If any target cannot be proven equal, B2a raises one bounded conflict before journal, preimage, proposal, manifest, or canonical mutation. It does not return a terminal transaction result and does not replace or remove any file.

## Purpose

Planning and projected validation happen before the exclusive lifecycle lock. An external editor or another non-ModuFlow process can therefore change a selected target after A2 reads it. The B1b lock serializes ModuFlow writers but does not stop outside editors.

B2a succeeds when:

> Under one write-authorized lifecycle lock, ModuFlow either proves every selected canonical target still equals the fixed plan preimage or reports the first bounded conflict without creating transaction-private state or changing canonical data.

This is the batch preflight required before recovery preparation. It does not eliminate the narrower compare immediately before each B2b replacement because an external edit can still occur after B2a returns.

## Selected Architecture

### Files and Ownership

- `scripts/project_lifecycle_transaction_storage.py` owns descriptor-safe canonical reads because it already owns `StorageTarget`, canonical-root traversal for staged proposals, exact-byte verification, and storage-safe bounded errors.
- `scripts/project_lifecycle_transaction.py` owns orchestration order and calls the verifier inside `_exclusive_lifecycle_lock()` before `private_transaction_workspace()`.
- `tests/test_project_lifecycle_transaction_storage.py` owns target-state and race cases.
- `tests/test_project_lifecycle_transaction.py` owns authorization, lock, and zero-private-write ordering.

No new module, public command, plugin, configuration, or service is introduced.

### Internal Interfaces

Add to the storage module:

```python
class LifecycleCanonicalConflict(RuntimeError):
    """Stable canonical-preimage conflict without paths or payloads."""

    def __init__(self, target_index):
        self.code = "CANONICAL_PREIMAGE_CONFLICT"
        self.target_index = target_index
        super().__init__(self.code)


def verify_canonical_preimages(canonical_root, storage_targets) -> tuple[int, ...]:
    """Return ordered indexes whose current canonical state matches exactly."""
```

`target_index` must be a non-negative, non-boolean integer already supplied by one validated `StorageTarget`. The exception string and representation contain only `CANONICAL_PREIMAGE_CONFLICT`; the index remains a separate internal attribute for later B2 result mapping.

Success returns the exact ordered tuple `tuple(range(len(storage_targets)))`. It returns no bytes, descriptors, paths, hashes, inode values, or mutable records.

### Authorization and Ordering

`_private_prepared_workspace()` retains its existing pre-lock validation order:

1. require `LifecycleTransactionPlan`;
2. bind its canonical root/context and require Issue 110 `write` capability;
3. validate detached storage targets, journal timestamps, legal phase transitions, and initial `planned` bytes;
4. acquire the B1b lifecycle lock;
5. call `verify_canonical_preimages(root, storage_targets)`;
6. only after all targets match, create the private workspace and continue the existing `planned → staged → prepared` sequence.

A denied or malformed plan therefore still fails before lock acquisition. A canonical conflict occurs while the lock exists but before the transaction workspace exists. Normal context exit releases the unchanged lock, leaving only the existing `.moduflow/transactions` control directory.

### Descriptor-Safe Batch Verification

The verifier accepts only an absolute canonical root and one non-empty, sequential tuple of valid `StorageTarget` values. Invalid arguments raise the existing `LifecycleStorageError("STORAGE_CONTEXT_INVALID")` before canonical reads.

It opens the canonical root once as a real directory using `O_RDONLY | O_DIRECTORY | O_CLOEXEC | O_NOFOLLOW`. For each target in plan order it duplicates the root descriptor, then opens every parent component relative to the previous descriptor with the same directory/no-follow flags. It never resolves an absolute child pathname, follows a symlink, calls `Path.resolve()`, or trusts a caller-provided staging path.

For a target planned as present:

1. inspect the final directory entry with `follow_symlinks=False`;
2. require a regular non-symlink file;
3. open the basename read-only with `O_CLOEXEC | O_NOFOLLOW`;
4. require the entry metadata and opened descriptor to identify the same regular device/inode;
5. read at most the expected byte count plus one byte;
6. require exact size, SHA-256, and constant-time byte equality with `StorageTarget._before_bytes`;
7. inspect the directory entry again and require the same device/inode and regular-file type.

For a target planned as absent, the parent must be a real existing directory and the final entry must return `ENOENT`. Any present entry, including a regular file, symlink, directory, socket, device, or broken link, is a conflict.

Every target is read at most once. Unchanged targets are still checked because the fixed plan binds their original state even though B2b will not replace them. The final evidence target is also checked, including its expected absence, so an existing evidence file is never overwritten silently.

All descriptors close on success and every error. The verifier calls only `os.open`, `os.dup`, `os.stat`, `os.fstat`, `os.read`, and `os.close`.

### Conflict Classification

B2a intentionally uses one fail-closed classification:

```text
CANONICAL_PREIMAGE_CONFLICT
```

It covers:

- present-to-absent or absent-to-present changes;
- byte, size, or SHA-256 mismatch;
- parent or target symlink substitution;
- target replacement before, during, or after its read;
- non-directory parent or non-regular target;
- inability to open, stat, or read a selected canonical target safely.

At this boundary, inability to prove the exact preimage is operationally equivalent to a conflict: B2 must not prepare or apply. B2a does not guess whether the cause was an external edit, permission change, filesystem error, or malicious race.

The error never contains the canonical root, logical path, role, expected/current hash, byte count, OS error, artifact content, or exception detail. Later B2 orchestration may combine the safe `target_index` with the already redacted public target record; B2a itself does not construct a public result.

## Relationship to B2b

B2a proves one coherent batch snapshot before private preparation, but portable filesystems cannot freeze outside writers. B2b must therefore re-use the same single-target descriptor verifier immediately before each canonical replacement and must compare the current target to the expected state for that point in the apply sequence.

B2a does not implement that second comparison or a canonical replacement. The separation is explicit:

```text
B2a: lock -> batch preflight -> private preparation
B2b: before each replace -> single-target recheck -> replace -> journal progress
```

If a B2b recheck fails after earlier targets were replaced, B2b owns reverse-order rollback. No rollback can be required from a B2a conflict because B2a runs before the first replacement.

## Test Contract

### Storage Tests

1. Verify a mixed tuple of present, absent, changed, and unchanged targets and return all ordered indexes without changing any canonical file.
2. Confirm each present target is read once and every parent/final component uses descriptor-relative no-follow calls.
3. Reject present-to-absent, absent-to-present, changed bytes, shortened/expanded bytes, symlink, directory, parent symlink, and non-directory parent with the exact conflict code and correct internal target index.
4. Inject directory-entry replacement before open, during read, and after read; require conflict and no unknown-entry cleanup.
5. Reject invalid root or target tuples with `STORAGE_CONTEXT_INVALID` before any canonical read.
6. Patch `os.mkdir`, `os.write`, `os.fsync`, `os.replace`, and `os.unlink` and prove zero mutation calls.
7. Assert exception string/repr never contains a secret root, logical path, artifact bytes, hash, or OS error.

### Transaction Integration Tests

1. Mutate a selected target after planning, enter `_private_prepared_workspace()`, and assert `CANONICAL_PREIMAGE_CONFLICT` while the B1b lock is held.
2. Assert conflict occurs before `private_transaction_workspace`, journal persistence, preimage storage, proposal staging, manifest creation, replacement, or synchronization.
3. Assert the lock is released after conflict, no transaction-ID workspace exists, and every canonical target retains its conflicting/current bytes.
4. On an unchanged project, assert the verifier runs once under the lock before the private workspace opens and the existing B1c3 flow still reaches `prepared`.
5. Preserve existing denial and malformed-plan zero-side-effect behavior.

Tests use only local temporary directories, standard-library `unittest`, and deterministic plans. They do not spawn processes, perform real crash tests, access Git or the network, or run full discovery/release gates.

## Alternatives Considered

1. **Batch preflight under lock before private workspace creation — selected.** It detects known conflicts before durable recovery state exists and preserves the original execution-protocol ordering.
2. **Verify after `prepared` using the existing private workspace root descriptor — rejected.** It reuses a descriptor but turns an ordinary pre-apply conflict into a retained journal/recovery workspace requiring later cleanup semantics.
3. **Add a standalone verifier without connecting orchestration — rejected.** It would be testable but would not enforce that B1c preparation follows a successful comparison.
4. **Reuse the A2 planning reader directly — rejected.** Its errors describe planning roles and it does not re-check final directory-entry identity after reading; B2 needs a storage-focused race-safe contract.
5. **Hold open every canonical target descriptor until replacement — rejected.** An open descriptor does not pin the directory entry against replacement, consumes one descriptor per target, and still cannot prevent external edits.
6. **Use file mtimes or inode numbers as the concurrency token — rejected.** The approved contract is exact existence plus content hash/bytes; timestamps are not reliable semantic identity.

## Out of Scope

- canonical target creation, replacement, removal, chmod, or parent creation;
- per-target compare immediately before replacement;
- journal phases after `prepared` or apply-progress persistence;
- terminal conflict/noop result construction or idempotent replay;
- projected or post-apply validation execution;
- evidence rebinding, evidence-target finalization, or private payload cleanup;
- rollback, crash recovery, stale-lock/workspace recovery, or Doctor diagnostics;
- public lifecycle/production adapters, operation inventory, distribution, or release gates;
- Prefect, another runner, plugin, service, database, background process, Git operation, subprocess, network call, or external dependency.

## Compatibility and Product Weight

- A1 result/status contracts, A2 planning, A3 projected validation, and B1a/B1b/B1c/B1d contracts remain unchanged.
- Existing lifecycle, loop, production, validation, and Doctor commands remain unchanged.
- B2a adds one internal exception, one read-only storage function, and one orchestration call in existing modules.
- It adds no module, public API, command, configuration field, startup work, resident process, scheduled task, package dependency, or user decision.
- Full validation-distribution and release verification remain deferred until D2.
