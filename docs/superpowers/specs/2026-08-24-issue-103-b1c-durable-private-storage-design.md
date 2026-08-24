# Issue 103 B1c Durable Private Storage Design

## Artifact Links

- **Issue ID:** `103-atomic-lifecycle-state-transaction`
- **Parent slice:** B1 secure lock, staging, journal, and evidence primitives
- **Predecessors:** B1a journal contract and B1b exclusive lifecycle lock
- **Owner / decision maker:** Dongwon Lee
- **Phase:** plan
- **Next command:** review this design, then write the B1c1 implementation plan

## Decision

Define one Issue 103-specific durable private-storage design, then implement it
through three separately approved slices:

1. **B1c1 — private workspace and preimages:** create the transaction-private
   workspace and store verified original bytes or an explicit absence marker.
2. **B1c2 — same-filesystem proposed staging:** prepare verified proposed bytes
   beside each target on its destination filesystem and finalize one immutable
   recovery manifest.
3. **B1c3 — atomic journal persistence:** durably advance the already-defined
   B1a journal through `planned`, `staged`, and `prepared` without changing a
   canonical target.

The three slices share this design so their durability ordering remains one
protocol. Each slice still receives its own implementation plan, tests, review,
approval, and commit.

B1c1 and B1c2 first implement and test storage primitives without routing a
public mutation through them. B1c3 is the slice that connects those primitives
into the final pre-apply durability order. This keeps the implementation slices
small without temporarily exposing an incomplete production workflow.

## Purpose

B1a defines which recovery snapshots are valid, and B1b prevents concurrent
lifecycle writers. Before B2 may replace a canonical file, Issue 103 must also
prove that every original byte and every proposed byte needed for deterministic
rollback or continuation exists in durable, restrictive local storage.

B1c succeeds when:

> Under one write-authorized B1b lock, ModuFlow can create a private recovery
> workspace, store and verify preimages, stage and verify proposed files on
> their destination filesystems, bind them with an immutable manifest, and
> durably persist a `prepared` journal that names only the manifest hash — while
> every canonical target remains byte-for-byte unchanged.

## Product Boundary

B1c is internal transaction storage, not a user-visible product capability.
It adds no command, plugin, setting, runner, service, schedule, resident process,
external dependency, Git call, network call, or remote operation.

The storage code lives in a new focused module:

```text
scripts/project_lifecycle_transaction_storage.py
```

The existing `project_lifecycle_transaction.py` remains responsible for plan
types, project-context binding, Issue 110 write authorization, the B1b lock,
journal-contract validation, and later B2 orchestration. The storage module owns
only descriptor-safe local storage primitives and imports no transaction module.
This one-way dependency avoids a circular import and prevents the existing
transaction module, already over 2,400 lines, from absorbing another independent
filesystem subsystem.

The B1b lock implementation is not moved or rewritten. B1c storage entry points
are private and are called only while the existing lock context is active.

## Authorization and Ownership Order

Every mutation follows this order:

1. Require a `LifecycleTransactionPlan` in the transaction module.
2. Rebind its canonical root and detached project context.
3. Require Issue 110 `write` capability.
4. Acquire the B1b exclusive lifecycle lock.
5. Translate planned targets into storage-module input values.
6. Create or open B1c private storage through no-follow descriptors.
7. Perform only the approved B1c slice operations.

Denied or invalid input performs zero `mkdir`, file creation, write, chmod,
unlink, replacement, or synchronization calls. Storage-module handles are
private values created only by the guarded workspace opener; later operations
consume that handle instead of accepting arbitrary absolute paths.

## Internal Interfaces

The transaction module converts each `PlannedTarget` into a detached immutable
storage target containing its index, logical metadata, hashes, size, and private
before/after bytes. The storage module does not accept a transaction plan or
import its class.

The private interface is shaped as:

```python
@contextmanager
def private_transaction_workspace(
    canonical_root,
    transaction_id,
):
    """Yield an owned descriptor-backed workspace handle."""


def store_preimages(workspace, storage_targets):
    """Return immutable verified preimage records."""


def stage_proposed_targets(workspace, storage_targets):
    """Return immutable verified same-filesystem staging records."""


def finalize_recovery_manifest(
    workspace,
    storage_targets,
    preimages,
    staged_proposals,
):
    """Return the SHA-256 of one immutable synchronized manifest."""


def persist_serialized_journal(
    workspace,
    journal_bytes,
    *,
    expected_previous_sha256,
):
    """Atomically persist exact validated bytes and return their SHA-256."""
```

Concrete private dataclass names may be selected in the B1c1 plan, but their
field meanings and ownership boundaries may not change. Workspace descriptors
remain internal to the handle lifetime and never enter a journal, manifest,
public result, exception string, or caller-supplied path.

## Storage Layout

The fixed project-local control layout is:

```text
<canonical-root>/.moduflow/transactions/
├── lifecycle.lock
└── <transaction-id>/
    ├── journal.json
    ├── journal.next                 # present only during an update
    ├── recovery-manifest.json
    └── preimages/
        ├── 000000.bin
        ├── 000001.bin
        └── ...
```

`transactions`, the transaction workspace, and `preimages` use mode `0700`.
The journal, manifest, preimages, and proposed staging files use mode `0600`.
The implementation enforces these modes through open descriptors rather than
trusting the caller's umask.

The transaction ID must already satisfy the bounded logical identifier contract
used by the immutable plan. B1c neither accepts caller-provided workspace names
nor resolves an arbitrary storage path.

Proposed staging files do not live in the central workspace. Each changed target
gets a bounded hidden staging filename in its existing real parent directory.
The name is derived from the SHA-256 of the transaction ID plus the six-digit
target index, so a later recovery process can locate a pre-manifest artifact
without accepting a caller-provided filename:

```text
<target-parent>/.moduflow-stage-<transaction-digest>-<six-digit-index>
```

This guarantees that a later B2 replacement can remain on the destination
filesystem, including when a contained target directory is a mount point.
B1c never creates a missing canonical parent directory. A missing, symlinked,
replaced, or non-directory target parent is a bounded storage failure.

## Descriptor-Safe Traversal

All directory traversal starts from the already bound canonical root and uses
component-relative descriptors with `O_DIRECTORY`, `O_CLOEXEC`, and
`O_NOFOLLOW` where the platform provides them.

- `.moduflow`, `transactions`, the transaction workspace, `preimages`, and every
  target parent component must be real directories.
- Workspace and payload creation use `O_CREAT | O_EXCL`; existing entries are
  never truncated, adopted, chmodded as ownership proof, or silently reused.
- Proposed files are created relative to the open destination-parent descriptor.
- The fixed `journal.next` entry is created exclusively relative to the open
  transaction-workspace descriptor, not through an unresolved absolute pathname.
- Replacement uses source and destination directory descriptors.
- Reads used for verification open regular non-symlink files and compare the
  opened descriptor's device and inode with the entry examined before opening.

Hard links are not treated as ownership proof. Cleanup additionally requires a
link count of one, the device/inode captured at exclusive creation, and the exact
expected bytes or hash.

## B1c1 — Private Workspace and Preimages

B1c1 creates a new transaction workspace exclusively. An existing workspace for
the transaction ID returns a stable conflict and is preserved without inspection
or reuse. Automatic stale-workspace reclamation is forbidden.

For each planned target, the storage input binds:

- target index, logical role, and project-relative path;
- whether the canonical target existed when planned;
- before and after SHA-256 values and proposed byte count;
- private detached before and after bytes.

An existing target's original bytes are written once as
`preimages/<six-digit-index>.bin`. B1c1 verifies the payload size and SHA-256 by
reading the created descriptor before accepting it. A target planned as absent
gets an explicit absence value in memory and no fabricated zero-byte preimage.
Unchanged targets still receive an original-state record because later recovery
must bind the entire ordered target set, but no unnecessary proposed staging file
is created for them.

Every accepted preimage is file-synchronized before B1c1 returns. The preimages
directory is directory-synchronized after its entries are created. B1c1 does not
create the recovery manifest or advance the journal to `prepared`.

## B1c2 — Proposed Staging and Recovery Manifest

B1c2 stages only targets whose planned `changed` value is true. It walks the
logical target parent from the canonical-root descriptor without following
symlinks, derives the one bounded staging name, creates a mode-`0600` regular
file exclusively, writes the exact private proposed bytes, then verifies:

- the file is on the destination-parent device;
- its size equals the planned proposed size;
- its SHA-256 equals the planned after hash;
- its device and inode still equal the entry created by this operation.

The proposed file is synchronized before it can enter the manifest. Its parent
directory is synchronized after creation. B1c2 does not rename it over the
canonical target.

After every required preimage and proposed file is verified, B1c2 writes one
immutable canonical JSON manifest plus a trailing newline:

```text
schema: moduflow.lifecycle-transaction-recovery-manifest.v1
transaction_id
targets[]
```

Each ordered target entry binds its index, role, logical relative path,
existence state, before/after hashes, preimage state, and proposed state. A
present preimage records its private workspace-relative filename, byte count,
and hash. An absent preimage records only `absent`. A staged proposal records its
project-relative hidden filename, byte count, hash, device, and inode. An
unchanged proposal records only `unchanged`.

The manifest never contains absolute paths, artifact bytes, actor/source data,
lock tokens, PIDs, exception messages, credentials, or other caller secrets.
It is created with `O_CREAT | O_EXCL`, verified from its descriptor,
file-synchronized, and followed by a workspace-directory synchronization. It is
never updated in place. Its recovery hash is SHA-256 over the complete exact file
bytes, including the trailing newline.

## B1c3 — Atomic Journal Persistence

The transaction module first validates each proposed snapshot through the B1a
`serialize_transaction_journal()` contract and renders canonical JSON bytes plus
one trailing newline. The storage module accepts only those already-serialized
bytes and does not duplicate or weaken the journal schema.

Every journal update includes an expected previous SHA-256 value, or `absent`
for the first write. Before creating a temporary journal, B1c3 verifies that the
current regular non-symlink `journal.json` exactly matches that expectation. It
never blindly overwrites an unknown snapshot.

The write sequence is fixed:

1. Create mode-`0600` `journal.next` exclusively inside the opened transaction
   workspace.
2. Write all bytes and enforce mode `0600`.
3. Read the descriptor back and verify exact bytes and SHA-256.
4. Synchronize the temporary file.
5. Replace `journal.json` atomically using workspace-relative descriptors.
6. Synchronize the transaction workspace directory.

B1c3 supports only this pre-apply durability sequence:

```text
workspace -> planned -> preimages/proposals -> manifest -> staged -> prepared
```

- `planned` is durable before preimage or proposal preparation is treated as an
  active transaction record.
- The immutable recovery manifest is written and synchronized after all
  preimages and proposed files are verified and synchronized.
- `staged` is durable only after that fixed-path manifest exists; its B1a
  `recovery_manifest_sha256` field remains `absent` because the phase contract
  does not yet authorize recovery from it.
- `prepared` is durable only after its `recovery_manifest_sha256` equals the
  exact manifest-file hash.

Later progress snapshots (`applying`, `post-validating`, `finalizing`, rollback,
and terminal phases) reuse the atomic writer but are not invoked or implemented
as workflows until B2.

## Failure and Cleanup Contract

B1c is fail-closed and does not perform automatic crash recovery.

- An existing workspace, preimage, manifest, destination staging filename, or
  unexpected journal state is never reused, truncated, or deleted to make
  progress.
- A partial object may be removed only when the current operation proves it
  created that exact regular-file device/inode and its content still equals the
  owned partial or complete bytes expected at that point.
- A mutated, replaced, deleted, expanded, truncated, symlinked, or otherwise
  uncertain object is preserved.
- Before `prepared`, the current process may clean only its provably owned
  partial files and empty directories through explicit descriptor-relative
  names. It never uses recursive deletion, globs, or path-based tree removal.
- Once `prepared` is durable, all preimages, staged proposals, manifest, and
  journal are retained for B2.
- If atomic replacement may have succeeded but the following directory
  synchronization fails, durability is uncertain. B1c preserves every artifact
  and returns a bounded uncertainty error instead of retrying or deleting.
- No PID liveness check, age threshold, stale-lock removal, or stale-workspace
  cleanup is allowed. B2 recovery and later Doctor diagnostics own those
  decisions.

If both a protected operation and cleanup fail, the cleanup/storage failure is
raised with the original failure chained as its cause because retained private
state requires operational attention.

## Safe Error Contract

Storage I/O failures raise `LifecycleStorageError`, a `RuntimeError` subtype,
with exactly one stable code and no path, payload, PID, token, timestamp, hash
value, temporary filename, OS error text, or caller-provided secret in its
string representation.

The bounded codes are:

- `STORAGE_CONTEXT_INVALID`
- `STORAGE_PATH_UNSAFE`
- `STORAGE_CONFLICT`
- `STORAGE_CREATE_FAILED`
- `STORAGE_WRITE_FAILED`
- `STORAGE_VERIFY_FAILED`
- `STORAGE_OWNER_MISMATCH`
- `STORAGE_JOURNAL_STATE_MISMATCH`
- `STORAGE_DURABILITY_UNCERTAIN`

B1a `LifecycleJournalError` remains the contract error for an invalid journal
snapshot. B1b `LifecycleLockError` remains the lock error. B1c does not collapse
those existing error types into generic storage failures.

## Test Contract

### B1c1 Focused Tests

1. Denied, malformed, or unbound context fails before every filesystem mutation.
2. Workspace and preimages use exact `0700`/`0600` modes.
3. Existing targets persist exact before bytes; absent targets persist only an
   absence marker.
4. Size/hash re-verification detects short, expanded, or corrupted writes.
5. Existing workspaces, files, symlinks, and non-directory components are
   preserved and rejected.
6. Partial-write cleanup removes only the exact inode and owned bytes created by
   the failing operation.

### B1c2 Focused Tests

1. Only changed targets receive proposed staging files.
2. Every proposed file is a mode-`0600` regular file on its parent device with
   the exact planned size and SHA-256.
3. Missing or unsafe parent components fail without directory creation.
4. Canonical targets remain byte-for-byte unchanged after success and every
   injected failure.
5. The manifest and derived staging names are immutable and deterministic, and
   the manifest contains no absolute path or artifact bytes.
6. Mutation, replacement, deletion, symlink substitution, inode mismatch, and
   synchronization failures preserve uncertain files.

### B1c3 Focused Tests

1. Invalid B1a journal snapshots fail before temporary-file creation.
2. Initial persistence requires an absent journal; updates require the exact
   previous digest.
3. Call-order assertions prove write/verify, file synchronization, atomic
   replacement, and directory synchronization ordering.
4. Failure injection covers every write, verification, synchronization,
   replacement, and cleanup boundary.
5. A failure after replacement but before directory synchronization returns
   `STORAGE_DURABILITY_UNCERTAIN` and preserves all private artifacts.
6. The focused integration reaches `prepared` with the exact manifest hash and
   proves every canonical selected target remains byte-for-byte unchanged.

Tests use standard-library `unittest` and deterministic transaction identities.
They do not launch subprocesses, kill processes, perform real crash tests,
access Git or the network, run full discovery, or run release gates. Each
implementation slice keeps its focused verification small and separately timed.

## Alternatives Considered

1. **One dedicated Issue 103 storage module with three implementation slices —
   selected.** It keeps one coherent durability protocol while preventing both a
   large all-at-once change and further growth of the transaction orchestration
   module.
2. **Add all storage helpers to `project_lifecycle_transaction.py` — rejected.**
   It adds fewer files but mixes plan, validation, lock, payload storage, journal
   persistence, future apply, and recovery responsibilities in one already large
   module.
3. **Build a reusable ModuFlow persistence framework — rejected.** It would add
   abstractions, configuration, and compatibility surface not required by Issue
   103 and would make the product heavier before a second consumer exists.
4. **Keep every proposed file under `.moduflow/transactions` — rejected.** A
   contained target may be on another filesystem, making later atomic replacement
   impossible.
5. **Use random adjacent staging names — rejected.** A crash before the immutable
   manifest is written would leave a staging file that recovery cannot derive
   from the durable `planned` journal.
6. **Automatically reclaim old workspaces using PID or age — rejected.** PID reuse,
   clock ambiguity, and check/delete races can destroy live recovery state.

## Out of Scope

- canonical target replacement or parent-directory creation;
- optimistic canonical hash rechecks immediately before apply;
- post-apply validation;
- rollback, resume, finalization, or explicit crash recovery;
- durable evidence rendering or evidence target replacement;
- stale lock/workspace diagnosis and Doctor recovery commands;
- public lifecycle, loop, dashboard, roadmap, index, or Production adapters;
- operation inventory, distribution, full validation, and release gates;
- a generic persistence API, plugin, runner, service, external dependency,
  background task, Git operation, network call, or remote side effect.

These remain separate Issue 103 approval boundaries. B2 is the first slice that
may replace or recover a canonical target.

## Compatibility and Product Weight

- A1 intent/result contracts, A2 immutable planning, A3 projected validation,
  B1a journal validation, and B1b lock behavior remain unchanged.
- Existing lifecycle, loop, Production Record, validation, and Doctor commands
  remain unchanged.
- The new module is imported only by Issue 103 transaction internals and adds no
  startup work or resident state.
- B1c introduces one internal file and one focused test module, then grows them
  through three reviewed commits instead of adding three product components.
- Full validation-distribution and release verification remain deferred until the
  Issue 103 D2 integration boundary.
