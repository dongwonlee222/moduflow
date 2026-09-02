# Issue 103 B2f Restart Recovery and Safe Cleanup Design

## Artifact Links

- **Issue:** `103-atomic-lifecycle-state-transaction`
- **Parent plan:** `specs/103-atomic-lifecycle-state-transaction/plan.md`, Task B2 Step 5
- **Predecessors:** B1 durable storage and journal primitives, B2d private completion, and B2e public apply/replay
- **Owner / decision maker:** Dongwon Lee
- **Phase:** execute, B2f design

## Decision

Implement restart recovery through three separately planned, tested, reviewed,
and committed slices:

1. **B2f1 — safe reopen and verification:** discover and reopen existing
   transaction workspaces, then strictly verify their journal, recovery manifest,
   preimages, and staged proposals without changing canonical or recovery files.
2. **B2f2 — deterministic single-transaction recovery:** recover one explicit
   transaction ID by completing only a provable finalization or by completing a
   provable reverse rollback. Ambiguous state remains `recovery_required`.
3. **B2f3 — terminal cleanup and project-wide barrier:** remove private material
   only after terminal state proof, make cleanup restart-safe, recover all
   discoverable incomplete work before a new apply, and block new mutation when
   any workspace cannot be resolved safely.

The slices share this design so reopening, recovery, cleanup, and the mutation
barrier remain one protocol. B2f1 is read-only. B2f2 may update canonical files
and journals but deliberately leaves terminal private material in place. B2f3
owns deletion and public-apply integration.

## Purpose

B2e can complete a fresh transaction and classify an exact evidence replay, but
it deliberately treats an existing evidence-absent transaction workspace as
`recovery_required`. The current storage module can create a new workspace but
cannot safely reopen one. Completed and rolled-back workspaces also retain
preimages, stages, manifests, and journals indefinitely.

B2f succeeds when:

> After a process stops at any durable journal boundary, ModuFlow can reopen
> only the exact private state it owns, prove and finish one valid recovery
> direction, safely scrub terminal private material, and prevent a new mutation
> from passing an unresolved transaction — without guessing, following a
> symlink, exposing original bytes, or deleting an unknown entry.

## Approaches Considered

### Three bounded slices with proof-driven recovery — selected

Separate read-only rehydration, canonical recovery, and destructive cleanup.
This makes every authority transition independently testable and keeps a
cleanup defect from being hidden inside rollback or finalization behavior.

### One combined recovery engine

Reopen, recover, delete, and connect the apply barrier in one implementation.
Rejected because journal selection, stale-lock handling, phase reconciliation,
and restart-safe deletion have distinct failure matrices. Combining them would
recreate the long-running, hard-to-localize work that this decomposition is
intended to avoid.

### Manual recovery and workspace deletion

Report the incomplete transaction and instruct the operator to remove files or
restore artifacts manually. Rejected because it cannot prove byte-identical
rollback, violates the single recovery entry-point contract, and risks deleting
the only remaining preimage.

## Product and Module Boundary

`scripts/project_lifecycle_transaction_storage.py` owns descriptor-safe reopen,
verification, and deletion primitives. It accepts fixed transaction IDs and
private handles, never arbitrary recovery paths, and continues to import no
transaction module.

`scripts/project_lifecycle_transaction.py` owns journal semantics, phase
selection, lock reclamation policy, recovery result mapping, canonical
rollback/finalization decisions, and the project-wide pre-apply barrier.

No lifecycle, loop, dashboard, roadmap, issue-index, or Production Record
adapter is connected in B2f. Those remain Stream C work.

## B2f1 — Safe Reopen and Verification

### Discovery

Discovery opens the bound canonical root, `.moduflow`, and `transactions`
through descriptor-relative `O_DIRECTORY | O_NOFOLLOW` traversal. It accepts
only real mode-`0700` transaction directories whose names satisfy the existing
logical transaction-ID contract. `lifecycle.lock` is the only accepted
non-directory control entry.

An unknown entry, symlink, special file, unsafe mode, duplicate identity, or
directory replacement is reported as a bounded unsafe-storage condition. B2f1
does not rename, chmod, unlink, repair, or quarantine it.

Explicit discovery selects exactly one requested transaction ID. Project-wide
discovery returns verified IDs in bytewise lexical order so tests and recovery
order are deterministic.

### Workspace reopening

Add a separate existing-workspace context manager. It never calls `mkdir`,
never adopts a caller-provided path, and never reuses the create-only
`private_transaction_workspace()` entry point. It opens the fixed workspace and
`preimages` directory by descriptor, verifies both are real private directories,
and yields the same closed private workspace-handle type used by current
storage operations.

The create-only API keeps returning `STORAGE_CONFLICT` for an existing
workspace. Recovery is the only code allowed to reopen one.

### Journal authority and `journal.next`

`journal.json` is the current durable authority. Its exact bytes must be a
regular mode-`0600`, single-link file and must pass
`serialize_transaction_journal()` without normalization. Its transaction ID
must equal the workspace name.

An abandoned `journal.next` is not promoted automatically. If `journal.json`
is valid, B2f1 validates `journal.next` only as a same-identity legal successor
candidate and reports it separately. B2f2/B2f3 may later discard that exact
candidate and resume from `journal.json` plus actual canonical state. Malformed,
foreign, hard-linked, or impossible `journal.next` makes the workspace
`recovery_required`.

If `journal.json` is absent and `journal.next` is one exact valid `planned`
snapshot, no canonical replacement could have begun. The workspace is
classified as a pre-journal orphan for later safe terminalization. Any other
missing-current combination is unresolved and preserved.

### Manifest and payload rehydration

`prepared` and later non-terminal phases require one exact immutable recovery
manifest whose complete byte hash equals the journal's
`recovery_manifest_sha256`. Journal targets and manifest targets must match in
count, index, role, relative path, existence, and before/after hashes.

For each target:

- an existing preimage must be a private single-link mode-`0600` file with the
  exact manifest name, size, and before hash;
- an absent preimage must have no fabricated payload;
- a changed proposal must be the exact manifest-recorded single-link mode-`0600`
  stage on the recorded target-parent device, with the recorded inode, size,
  and after hash;
- an unchanged proposal must not have a stage;
- target-parent and canonical traversal must remain contained and no-follow.

Only after all cross-checks pass may B2f1 construct detached private storage
targets, preimage records, staged-proposal records, and one recovered state.
Private bytes are never placed in a public dictionary, exception, journal,
representation, log, or Git-tracked artifact.

`planned` and `staged` may lack an authoritative manifest. B2f1 therefore does
not adopt their unbound payloads as recovery truth. It uses only the validated
journal target metadata to prove canonical before-state; later cleanup treats
all remaining private entries as fixed-layout material that must pass a complete
inventory check before deletion.

## B2f2 — Deterministic Single-Transaction Recovery

### Authorization and lock ownership

Recovery requires the existing project `write` capability. Denial returns
before lock reclamation, journal changes, canonical changes, or cleanup. Doctor's
future read-only inspection remains separate D1 work.

Before canonical or journal mutation, recovery owns the exclusive lifecycle
lock. A current live lock is never removed. A lock may be reclaimed only when:

1. its strict owner record is valid and names the selected verified workspace;
2. its recorded local PID is proven absent (`ESRCH`);
3. PID reuse or permission uncertainty is treated as live and blocks recovery;
4. the lock entry still has the same inode and exact bytes immediately before
   unlink;
5. the transactions directory is synchronized after unlink; and
6. recovery then acquires a fresh owner record normally.

A malformed, foreign, replaced, or ownership-uncertain lock returns
`recovery_required`. This policy is intentionally conservative: a false live
classification delays recovery, while a false stale classification could allow
two writers.

### Phase decision table

| Loaded phase | Required action |
|---|---|
| `planned`, `staged`, or valid pre-journal orphan | Prove every canonical target exact before, persist `rolled-back` when a valid current journal exists, and report `rolled_back`. Never apply a proposal. |
| `prepared`, `applying`, or `post-validating` | Reconcile the journal prefix with actual exact before/after states, enter `rolling-back`, and restore/remove the provable applied prefix in reverse order. |
| `rolling-back` | Resume from the recorded rollback prefix after re-proving every target already recorded as restored. |
| `finalizing` | Complete only when every ordinary target is exact after, every unchanged target is exact before, and evidence is either exact after or exact staged while canonical evidence is exact before. Otherwise preserve and return `recovery_required`. |
| `complete` | Prove the full exact after-state and classify as terminal. Never roll it back after restart. |
| `rolled-back` | Prove the full exact before-state and classify as terminal. |
| `recovery-required` | Resume only when progress plus actual state selects one direction unambiguously; otherwise preserve it unchanged. |

### Rollback recovery

Journal progress is a lower bound, not permission to overwrite. A crash can
happen after a canonical replacement but before its progress snapshot, so the
engine classifies every changed target as exact before, exact after, or unknown.
Only one contiguous exact-after prefix may extend recorded applied progress.
Targets beyond it must be exact before. Unknown, reordered, or non-prefix state
is never overwritten.

Recovery persists `rolling-back` before the first restore, records each reverse
step durably, proves all changed targets exact before and all unchanged targets
unchanged, then persists `rolled-back`. It reuses the existing evidence-specific
rollback primitive when evidence is part of a provable rollback prefix.

### Finalization recovery

Recovery never reruns projected validation or canonical business validation.
It finalizes only the already durable, exact staged proposal selected before the
crash.

For `finalizing`, all ordinary changed targets must be exact after and every
unchanged target exact before. If canonical evidence is exact before and its
stage is exact, recovery may replace evidence, persist evidence progress, prove
the full after-state, and persist `complete`. If evidence is already exact after,
it may skip replacement and persist missing progress plus `complete`. Any other
combination stays `recovery_required`; recovery does not choose rollback merely
because finalization proof failed.

For `recovery-required`, a non-empty verified rollback prefix selects rollback.
A partial ordinary applied prefix with no evidence selects rollback. Confirmed
exact-after evidence selects finalization. The ambiguous state "all ordinary
targets after, evidence before, no recorded rollback, and no proof of whether
finalization had begun" remains `recovery_required`.

### Recovery report

Restart storage cannot always reconstruct the full original public apply result:
a crash immediately after `planned` may precede any authoritative staged
evidence. Recovery therefore returns a separate redacted recovery report instead
of inventing issue, action, actor, validation, or lifecycle fields.

The report schema is `moduflow.lifecycle-transaction-recovery.v1` and contains:

- project ID and canonical root;
- aggregate terminal status using the existing six-status vocabulary;
- ordered transaction records containing transaction ID, idempotency key,
  observed phase, resulting phase, status, safe error code, affected logical
  target metadata, and verified target count;
- no artifact bytes, absolute private paths, owner tokens, PID, stage names,
  preimage names, or validator diagnostics.

With an explicit transaction ID the report contains exactly one record. B2f3
extends the same report to ordered project-wide recovery. Apply results and
canonical redacted evidence continue using their existing schemas unchanged.

## B2f3 — Terminal Cleanup and Project-Wide Barrier

### Cleanup eligibility

Cleanup is allowed only after one of these proofs under the recovery-owned lock:

- `complete` journal plus the full exact canonical after-state; or
- `rolled-back` journal plus the full exact canonical before-state; or
- a valid pre-journal orphan plus the full exact canonical before-state and a
  complete fixed-layout inventory derived from its exact `planned`
  `journal.next` target metadata.

`recovery-required`, a malformed terminal journal, canonical drift, missing
terminal proof, or ambiguous inventory retains all remaining material.

### Complete inventory before deletion

Cleanup first validates the entire expected workspace inventory without deleting
anything. It accepts only the current terminal `journal.json`, an optional exact
abandoned `journal.next`, the exact recovery manifest when applicable, the
fixed `preimages` directory, and manifest-bound preimage/stage entries. Unknown,
changed, hard-linked, symlinked, special, or extra entries block cleanup.
For `planned`, `staged`, and pre-journal orphan cleanup without an authoritative
manifest, expected preimage and stage names are derived only from the validated
transaction ID and ordered journal targets; every present file must still match
the target's exact before/after size and hash.

After inventory proof, cleanup removes in this order:

1. exact staged proposals from their target parents, synchronizing each parent;
2. exact preimage payloads and then the empty `preimages` directory;
3. exact recovery manifest and exact abandoned `journal.next`;
4. terminal `journal.json` last;
5. the now-empty transaction workspace;
6. synchronize the transactions directory and release the owned lock.

Canonical redacted evidence is permanent project evidence and is never removed.

The operation is restart-safe. A terminal journal remains until all sensitive
material is gone, so an interruption can repeat cleanup while accepting only an
expected already-absent suffix. If cleanup stops after removing the terminal
journal, the only accepted remainder is one exact empty private workspace,
which may be removed and synchronized. Any other journal-less remainder is
preserved as `recovery_required`.

### Project-wide recovery

Calling `recover_incomplete_transaction(..., transaction_id="")` discovers
workspaces in deterministic order and produces one recovery report containing
one record per inspected transaction. It stops canonical recovery at the first
`conflict`, `denied`, or `recovery_required` record but retains already completed
records. Cleanup may continue only for already terminal, independently proven
workspaces.

Aggregate status is selected in this order:
`recovery_required`, `conflict`, `denied`, `applied`, `rolled_back`, then `noop`.
An empty healthy project returns `noop` with an empty transaction list.

### Public-apply barrier

Before planning a fresh mutation, `apply_lifecycle_transaction()` performs
project resolution and write authorization without reading selected canonical
targets, then runs project-wide recovery. If recovery leaves any unresolved
workspace, apply returns `recovery_required` and does not plan, project,
validate, lock for a fresh transaction, stage, or replace.

After recovery clears, apply creates a fresh plan and projected validation. When
the fresh transaction lock is acquired, it performs a second read-only
workspace scan under that same lock before canonical preflight and workspace
creation. This closes the race with another process that could stop between the
first recovery pass and lock acquisition. Any newly observed unrelated
incomplete workspace blocks the fresh apply without modifying it.

Completed workspace cleanup happens before replay planning; canonical evidence
remains, so an exact retry still returns B2e `noop`. The barrier does not delete
or reinterpret canonical evidence.

## Error and Privacy Contract

New failures use stable closed codes grouped under:

- `RECOVERY_DISCOVERY_*` for unsafe transaction-directory inventory;
- `RECOVERY_JOURNAL_*` for current/next journal authority failures;
- `RECOVERY_MANIFEST_*` for journal/manifest mismatch;
- `RECOVERY_PAYLOAD_*` for preimage or staged-proposal mismatch;
- `RECOVERY_STATE_*` for canonical state that does not select one safe action;
- `RECOVERY_LOCK_*` for live, foreign, or uncertain lock ownership;
- `RECOVERY_CLEANUP_*` for terminal inventory or deletion uncertainty.

Exact code names are fixed in each slice's implementation plan and tests.
Exception strings and representations contain only a closed code. Recovery
reports expose logical roles, relative canonical paths, hashes, counts, phases,
and closed codes; they never expose private names or bytes.

## Test Contract

Implementation uses focused `unittest` RED/GREEN slices.

### B2f1 tests

1. Reopen exact private directories without creation or mutation.
2. Reject symlink, special, replaced, wrong-mode, hard-linked, foreign-ID, and
   unknown entries.
3. Strictly load every valid journal phase and reject malformed progress.
4. Cross-check journal, manifest, preimages, and stages including nested target
   parents and poisoned default paths.
5. Classify valid and invalid `journal.next` combinations without promotion or
   deletion.
6. Prove private bytes and paths never enter public values, errors, or reprs.

### B2f2 tests

1. Simulate restart at every persisted journal boundary and target position.
2. Prove prepared/applying/post-validating/rolling-back recovery produces exact
   reverse rollback and a durable terminal journal.
3. Prove both finalizing crash positions finish only from complete exact proof.
4. Preserve ambiguous and foreign canonical states as `recovery_required`.
5. Resume only unambiguous `recovery-required` rollback/finalization cases.
6. Reclaim only an exact absent-PID matching lock; live, reused, malformed, and
   replaced locks remain blocking.
7. Prove recovery reports are deterministic and redacted.

### B2f3 tests

1. Clean complete and rolled-back workspaces only after full terminal proof.
2. Inject interruption after every deletion and directory synchronization, then
   prove retry completes safely.
3. Reject unknown or changed inventory before the first deletion.
4. Scan and recover multiple transaction IDs in deterministic order and stop at
   the first unresolved canonical recovery.
5. Prove public apply recovers before planning and performs the second under-lock
   barrier scan.
6. Prove a barrier race cannot create a second workspace or canonical write.
7. Preserve all A1–B2e planner, projection, storage, journal, apply, rollback,
   finalization, replay, denial, and result regressions.

Focused B2f tests do not run full discovery, complete validation-distribution,
or release gates. Those remain D2 work.

## Out of Scope

- lifecycle, loop, dashboard, roadmap, issue-index, and Production Record
  mutation adapters;
- Doctor diagnostics and the exact CLI recovery command;
- operation audit, full distribution, release gates, PR publication, merge, or
  plugin release;
- any Git, subprocess, network, remote, database, service, scheduler, Prefect,
  or automation control-plane integration;
- changing the existing plan, journal, apply-result, or canonical evidence
  schemas;
- automatically resolving ambiguous `recovery-required` state.

## Compatibility

- The create-only private workspace API remains create-only.
- B1 journal phases, transition vocabulary, manifest layout, staging names, and
  evidence renderer remain unchanged.
- B2d completion and same-process rollback semantics remain unchanged.
- B2e completed-evidence replay remains the authoritative public `noop` path.
- Recovery adds one report schema but does not change apply-result or evidence
  consumers.
- No dependency, plugin setting, CLI command behavior, or canonical artifact
  path changes in B2f.
- Existing untracked Issue 103 implementation plans remain untouched and
  unstaged.
