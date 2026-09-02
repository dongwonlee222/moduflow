# Issue 103 B1b Exclusive Lifecycle Lock Design

## Artifact Links

- **Issue ID:** `103-atomic-lifecycle-state-transaction`
- **Parent slice:** B1 secure lock, staging, journal, and evidence primitives
- **Owner / decision maker:** Dongwon Lee
- **Phase:** plan
- **Next command:** write the B1b exclusive-lock implementation plan

## Decision

Add only one internal project-local lifecycle lock primitive to the existing `project_lifecycle_transaction.py` module. B1b is not a new product feature, command, plugin, service, or Issue. It prevents two Issue 103 transactions from mutating the same project concurrently.

The primitive fails closed. An existing lock is never reclaimed automatically, even when its PID appears inactive. B2 recovery and later Doctor diagnostics will own explicit recovery behavior.

## Purpose

Issue 103 cannot provide deterministic multi-file apply and rollback if two processes can replace the same targets simultaneously. B1b succeeds when:

> One write-authorized lifecycle transaction exclusively owns `.moduflow/transactions/lifecycle.lock`, concurrent acquisition is rejected without changing the existing lock, and release removes only the exact lock created by that owner.

## Selected Architecture

### Location and Scope

- Fixed control directory: `<canonical-root>/.moduflow/transactions/`
- Fixed lock file: `<canonical-root>/.moduflow/transactions/lifecycle.lock`
- Implementation: existing `scripts/project_lifecycle_transaction.py`
- Tests: existing `tests/test_project_lifecycle_transaction.py`

No new module or user-visible entry point is introduced. The empty `transactions` control directory may remain after release because B1c journal storage will use the same directory.

### Internal Interface

```python
@contextmanager
def _exclusive_lifecycle_lock(
    plan: LifecycleTransactionPlan,
    *,
    clock=None,
    pid=None,
    token_factory=None,
):
    """Yield one private lock owner and remove only its unchanged lock."""
```

The production defaults use the current UTC time, `os.getpid()`, and a cryptographically random hexadecimal owner token. Tests inject deterministic values. The yielded owner value is internal and redacted; it never exposes file descriptors through a public serializer.

### Authorization Order

1. Require a `LifecycleTransactionPlan`.
2. Resolve and bind the plan to its canonical project context.
3. Require Issue 110 `write` capability.
4. Only after authorization, open or create the transaction control directory and lock file.

`project_operation.ProjectOperationDenied` remains unchanged. Invalid plan/context input is converted to a bounded lock error. A denied or invalid request performs zero directory creation, lock creation, deletion, replacement, subprocess, Git, or network operations.

### Safe Directory Traversal

The implementation uses directory file descriptors and component-relative operations:

1. Open canonical root as a real directory without following symlinks.
2. Open the existing `.moduflow` directory without following symlinks.
3. Create `transactions` with mode `0700` only when absent.
4. Open `transactions` as a real directory without following symlinks and enforce mode `0700`.
5. Perform lock creation, verification, and deletion relative to the open transactions directory descriptor.

`.moduflow` itself is not created by B1b. A missing, non-directory, replaced, or symlinked control path fails with `LOCK_PATH_UNSAFE`.

### Owner Record

The lock file uses mode `0600` and contains canonical UTF-8 JSON plus one trailing newline:

```json
{
  "acquired_at": "2030-01-01T00:00:00Z",
  "owner_token": "0123456789abcdef0123456789abcdef",
  "pid": 12345,
  "schema": "moduflow.lifecycle-transaction-lock.v1",
  "transaction_id": "txn-..."
}
```

The record contains only transaction identity and generated lock-ownership metadata. It excludes project paths, target paths, artifact bytes, hashes, actor data, recovery payloads, exception messages, credentials, and user-provided secrets. The generated owner token is used only to distinguish lock owners and is not an external authentication credential.

The owner token distinguishes two processes executing the same deterministic transaction ID. PID and time are diagnostics only; they never authorize release or automatic reclamation.

### Acquisition

Create `lifecycle.lock` with:

```text
O_CREAT | O_EXCL | O_WRONLY | O_CLOEXEC | O_NOFOLLOW
```

If it already exists, return `LOCK_HELD` without opening, parsing, rewriting, truncating, chmodding, or deleting it. No PID liveness check is performed.

After exclusive creation, write all owner bytes, enforce mode `0600`, and retain the created file's device/inode identity for release verification. A short write or creation failure returns a bounded error. Cleanup after a partial creation removes the directory entry only when it still identifies the inode created by this acquisition; otherwise it is preserved fail-closed.

### Release

On context exit, release performs all of these checks relative to the retained transaction directory descriptor:

1. The current `lifecycle.lock` is a regular non-symlink file.
2. Its device and inode equal the file created by this owner.
3. Its complete bytes exactly equal the original owner bytes using constant-time comparison.

Only then is the file unlinked. Missing, replaced, mutated, expanded, or truncated content is preserved and returns `LOCK_OWNER_MISMATCH`. The implementation never removes the transaction control directory.

If both the protected body and release fail, the release failure is raised with the body failure chained as its cause because a retained or uncertain lock requires explicit operational attention.

## Safe Error Contract

`LifecycleLockError`, a `RuntimeError` subtype, carries only one stable code:

- `LOCK_CONTEXT_INVALID`
- `LOCK_PATH_UNSAFE`
- `LOCK_HELD`
- `LOCK_CREATE_FAILED`
- `LOCK_OWNER_MISMATCH`
- `LOCK_RELEASE_FAILED`

Error strings never include canonical paths, existing lock contents, PIDs, tokens, timestamps, OS error strings, or artifact data.

## Test Contract

B1b uses focused local tests only:

1. Write denial occurs before every filesystem mutation boundary.
2. The first owner creates exactly one mode-`0600` regular lock below a mode-`0700` control directory.
3. Owner JSON is deterministic under injected PID, time, and token and contains no project/artifact data.
4. A concurrent acquisition returns `LOCK_HELD` and leaves the first owner's bytes and metadata unchanged.
5. Two acquisitions with the same transaction ID still have different owner tokens.
6. Normal exit and protected-body failure remove the unchanged owner lock.
7. Mutation, replacement, deletion, symlink substitution, or inode mismatch prevents deletion and returns `LOCK_OWNER_MISMATCH`.
8. Unsafe `.moduflow` or `transactions` path components are rejected without traversal.
9. Partial owner-record write failure cleans only the inode created by that acquisition.
10. No PID liveness check, signal, subprocess, Git, network, journal, staging, apply, or rollback boundary is called.

## Alternatives Considered

1. **Existing transaction module with an opaque owner token — selected.** It adds no new user-facing surface and keeps this small Issue 103 slice easy to locate.
2. **Separate persistence module — deferred.** It would improve long-term file separation, but adding another module now made B1b sound like a new product component. Revisit only if B1c cannot remain understandable in the existing module.
3. **Transaction ID as sole ownership proof — rejected.** Transaction IDs are deterministic, so two processes handling the same intent could delete each other's lock.
4. **PID liveness check and stale-lock auto-removal — rejected.** PID reuse and check/delete races can steal a live lock and violate the transaction guarantee.

## Out of Scope

- journal schema changes or journal file persistence;
- preimage payloads, manifests, proposed-file staging, `fsync`, and atomic replacement;
- canonical target apply, post-validation, rollback, and crash recovery;
- stale-lock diagnosis or manual/automatic recovery commands;
- durable evidence rendering;
- lifecycle/production public adapter routing;
- any new command, plugin, background worker, external dependency, Git call, or network call.

## Compatibility and Product Weight

- A1 through B1a behavior remains unchanged.
- Existing lifecycle, loop, production, and validation commands remain unchanged.
- The lock exists only while a later Issue 103 transaction is executing.
- B1b adds no startup work, scheduled work, resident process, package dependency, configuration field, or user decision.
- The next slice remains separately approved; B1b does not authorize B1c persistence implementation.
