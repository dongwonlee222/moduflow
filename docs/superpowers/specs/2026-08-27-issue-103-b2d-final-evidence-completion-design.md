# Issue 103 B2d Final Evidence Completion Design

## Artifact Links

- **Issue:** `103-atomic-lifecycle-state-transaction`
- **Parent plan:** `specs/103-atomic-lifecycle-state-transaction/plan.md`, Task B2 Step 3
- **Predecessors:** `e3467fb` (canonical post-apply validation), `7abed53` (post-apply contracts), `b128fb6` (same-lock rollback), and `46829c1` (pure redacted evidence rendering)
- **Owner / decision maker:** Dongwon Lee
- **Phase:** execute, B2d design

## Decision

Finish the successful private transaction path by binding final redacted evidence before durable staging, then applying that evidence as the last canonical target under the existing lifecycle lock. Persist `finalizing` before evidence replacement, record evidence progress durably, prove the complete canonical after-state, persist terminal `complete`, and only then yield a private completed state.

B2d does not add a public apply API. It extends the private transaction engine only far enough to make one successful local transaction durably complete and to roll back evidence plus ordinary targets when finalization fails.

## Purpose

B2c ends with ordinary targets applied, exact post-apply validation complete, and the durable journal still in `post-validating`. That state is deliberately incomplete: canonical evidence has not been written, evidence is not part of applied progress, and neither retry nor recovery may treat the transaction as successful.

B2d closes that success boundary. Its success condition is:

> The final redacted evidence bytes were part of the original durable staging and recovery manifest, evidence was replaced last under the same lock, every selected canonical target was proven exact after, and a terminal `complete` journal was flushed before private success became observable.

## Selected Architecture

### Prebind final evidence before any transaction I/O

The A2 planner continues to return a provisional evidence target. B2d accepts the immutable plan, its matching normalized `LifecycleIntent`, and the already successful projected-validation summary. Before lock acquisition or filesystem mutation, it:

1. prevalidates all success and worst-case rollback timestamps;
2. constructs the expected successful post-apply summary;
3. builds one strict internal `applied` result candidate;
4. renders final evidence through the existing `render_transaction_evidence()` boundary;
5. replaces only the final planned evidence target's proposed bytes, size, and SHA-256 in a detached rebound plan;
6. rebuilds the strict internal result candidate with the rebound target metadata and proves the rendered evidence bytes are unchanged.

The rendered evidence omits the final evidence target entirely, so changing that target's own size or hash cannot change the evidence bytes. This removes self-reference and lets the final evidence proposal exist before staging.

The rebound plan, not the provisional plan, is passed to preflight, preimage storage, proposal staging, recovery-manifest generation, journal serialization, apply, post-validation, finalization, and rollback. Therefore the first durable recovery manifest already describes the final evidence proposal. B2d never rewrites a staged evidence file or recovery manifest after post-validation.

### Private completion input

Add one frozen private completion input that carries only information unavailable from the public plan:

```python
@dataclass(frozen=True)
class _PrivateCompletionInput:
    intent: LifecycleIntent = field(repr=False, compare=False)
    next_command: str = field(repr=False, compare=False)
    projected_validation: object = field(repr=False, compare=False)
```

Construction normalizes and detaches the intent and resolved next command, freezes the projected summary, requires `projected_validation.valid is True`, and proves that the intent derives the plan's exact transaction ID and idempotency key in the plan's bound canonical context. The supplied next command must equal the pure next-command value used when the plan rendered state and loop projections. Unknown or inconsistent input fails before timestamp reads, lock acquisition, staging, journal creation, or canonical writes.

`actor` and `source_event` come only from the matching normalized intent; `next_command` comes from the separately checked resolved value. Plan identity, target metadata, action, lifecycle, project, and issue fields come from the rebound plan. Journal timestamps provide `created_at`, `started_at`, and the reserved successful `completed_at`.

### Existing private engine becomes the completion boundary

Extend the existing `_private_applied_workspace()` pre-yield path rather than wrapping it with a second lock or workspace. It receives the private completion input, binds evidence before entering `_private_prepared_workspace()`, and keeps the same lock from canonical preflight through terminal `complete` or rollback.

The success sequence is:

1. prepare the rebound plan, final evidence proposal, preimages, recovery manifest, and `prepared` journal;
2. apply every changed non-evidence target and persist ordinary progress;
3. persist `post-validating` and run B2c exact target proof plus one canonical validator call;
4. compare the actual redacted post-apply summary with the prebound successful summary;
5. persist `finalizing` with the complete ordinary applied prefix;
6. when evidence changed, finalize it last and persist a second `finalizing` snapshot with evidence progress; otherwise prove the unchanged evidence preimage without replacement;
7. prove every changed target exact after and every unchanged target exact before;
8. persist terminal `complete` with all changed indexes;
9. yield `_PrivateCompletedState` while the same lock and private workspace remain owned by the context manager.

No canonical evidence is visible before step 6. No completed state is visible before step 8.

### Evidence-specific storage boundary

Keep ordinary apply/rollback APIs role-restricted. Add evidence-specific storage operations that reuse the existing descriptor-relative, no-follow, same-filesystem, `0600`, replace, parent-`fsync`, and exact-byte proof rules:

```python
def finalize_staged_evidence(workspace, target, staged_proposal) -> int:
    """Replace exactly one changed final evidence target from its final stage."""


def classify_finalized_evidence(workspace, target) -> str:
    """Return exact 'before' or 'after' for one changed evidence target."""


def rollback_finalized_evidence(workspace, target, preimage) -> int:
    """Restore or remove one exact-after evidence target to exact before."""
```

Each function requires `target.role == "evidence"`; the existing ordinary functions continue to reject evidence. Unchanged evidence is never replaced and remains verified through `verify_canonical_target()`.

### Private completed state

Add one frozen state:

```python
@dataclass(frozen=True)
class _PrivateCompletedState:
    storage_targets: tuple[transaction_storage.StorageTarget, ...] = field(repr=False, compare=False)
    preimages: tuple[transaction_storage.StoredPreimage, ...] = field(repr=False, compare=False)
    staged_proposals: tuple[transaction_storage.StagedProposal, ...] = field(repr=False, compare=False)
    recovery_manifest: transaction_storage.RecoveryManifest = field(repr=False, compare=False)
    applied_target_indexes: tuple[int, ...]
    projected_validation: object = field(repr=False, compare=False)
    post_apply_validation: object = field(repr=False, compare=False)
    transaction_result: object = field(repr=False, compare=False)
    verified_target_count: int
    journal_sha256: str
    created_at: str
    completed_at: str
    _workspace: object = field(repr=False, compare=False)
```

The validation summaries and internal strict result are detached and recursively frozen. `transaction_result` is not yet a public return value; B2e will own public result mapping. The state representation exposes no absolute paths, content bytes, recovery names, result fields, validation details, or workspace handles.

## Journal and Timestamp Contract

B2d uses the existing phases and adds no journal field or schema:

```text
post-validating -> finalizing -> finalizing -> complete
```

The first `finalizing` snapshot records all changed ordinary indexes. When evidence changed, the second records its index after exact evidence replacement. Unchanged evidence causes no replacement and no duplicate progress snapshot. `complete` records every changed index in plan order and no rollback indexes.

All timestamps are read and validated before lock acquisition. The count covers the longest finalization-then-rollback path, not merely the success path. Let `n` be the changed ordinary-target count and `e` be `1` when evidence changed or `0` when it remained exact before. Prevalidate exactly `9 + 2*n + 2*e` timestamps. When `e == 1`, the longest path includes:

- three preparation timestamps;
- applying start plus `n` ordinary progress timestamps;
- one post-validating timestamp;
- finalizing start plus evidence progress;
- rollback start plus `n + 1` reverse progress timestamps;
- one rolled-back timestamp;
- one reserved recovery-required timestamp.

When `e == 0`, evidence progress and evidence rollback timestamps are absent. Unused branch timestamps remain private. No clock read occurs under the lock.

## Complete After-State Proof

Before `complete`, verify every target in plan order:

- changed non-evidence: `classify_canonical_target()` must return `after`;
- changed evidence: `classify_finalized_evidence()` must return `after`;
- unchanged target, including unchanged evidence: `verify_canonical_target()` must prove exact before.

The verified count must equal the full target count. Any exact-before changed target is a bounded finalization failure. Any unknown, foreign, unsafe, or unprovable state enters rollback and never writes `complete`.

The `complete` journal is the authoritative terminal record. A private staged evidence file that says `applied` is not authoritative, and canonical evidence without a matching terminal journal remains recoverable incomplete state for B2f.

## Failure and Rollback Contract

Finalization remains inside the existing bounded pre-yield failure boundary.

- Failure before evidence replacement rolls back the changed ordinary prefix.
- Failure after evidence may have been replaced reconciles evidence plus ordinary targets against exact before/after states.
- Confirmed exact-after evidence rolls back first, followed by ordinary targets in reverse plan order.
- Exact-before entries are treated as already restored but still appear in verified rollback progress.
- Foreign or unprovable evidence is never overwritten speculatively.
- Before terminal `rolled-back`, the existing complete rollback proof verifies every selected target exact before.
- Any rollback or proof failure persists one best-effort `recovery-required` journal and retains preimages, staged proposals, manifest, and journal.

Add one bounded `LifecycleFinalizationError` whose string and representation expose only one of these exact codes:

- `FINALIZATION_INPUT_INVALID`: completion input, projected summary, result candidate, or evidence binding is inconsistent before I/O;
- `FINALIZATION_POST_APPLY_MISMATCH`: the actual successful B2c summary differs from the prebound expected summary;
- `FINALIZATION_TARGET_MISMATCH`: a target is exact before where finalization requires exact after.

Existing storage failures retain their established `STORAGE_*` or `CANONICAL_PREIMAGE_CONFLICT` codes. Exception strings, representations, signals, journals, and frozen summaries contain no validator diagnostics, artifact bytes, absolute paths, staging names, rejected metadata, or original exception text.

A caller-body exception after `_PrivateCompletedState` is yielded is outside the transaction boundary. It does not retry finalization or roll back a terminal complete transaction.

## Alternatives Considered

### Late evidence restaging and manifest replacement

Render evidence after post-validation, replace its staged file, rewrite the recovery manifest, and then finalize. Rejected because a crash between stage, manifest, and journal replacement creates multiple authority combinations and forces B2d to design a second manifest-switch protocol.

### Finalize provisional evidence and rewrite canonical evidence later

Apply the A2 placeholder first and replace it with full evidence after `complete`. Rejected because `complete` would temporarily certify incomplete evidence, recovery would bind the wrong hash, and evidence would no longer be the last atomic transaction target.

### Defer evidence until public API and recovery are implemented

Keep B2c as the end of the private engine and combine evidence with B2e/B2f. Rejected because it produces an oversized slice and prevents isolated failure injection around final evidence replacement and terminal completion.

## Test Contract

Implementation follows RED/GREEN TDD with focused local tests.

1. Prove final evidence bytes are bound before lock and are identical when only self-target metadata changes.
2. Prove the first recovery manifest and changed staged evidence already contain the final evidence bytes and hash; unchanged final evidence remains verified and unstaged.
3. Prove success persists exact `finalizing`, evidence-progress, and `complete` journal order under one lock.
4. Prove evidence is replaced last, uses mode `0600`, and canonical bytes equal `render_transaction_evidence(transaction_result)`.
5. Prove complete after-state verification covers changed ordinary, changed evidence, and unchanged targets in plan order.
6. Inject failure before, during, and after evidence replacement and prove evidence-first reverse rollback plus exact complete rollback.
7. Inject foreign evidence and ordinary states during finalization/rollback and prove `recovery_required`, retained recovery materials, and no speculative overwrite.
8. Reject mismatched intent, invalid projected summary, invalid clock input, and malformed completion metadata before any I/O.
9. Prove validator output, exceptions, private paths, provisional evidence bytes, and recovery names never enter evidence, journal, signals, or state representations.
10. Prove caller-body exceptions after terminal completion cause no validation retry, evidence retry, journal write, or rollback.
11. Preserve B1/B2a/B2b/B2c storage, journal, apply, rollback, projected-validation, and post-validation regressions.

Tests use `unittest`, `unittest.mock`, and local temporary directories. They do not spawn processes, access Git/network, simulate real restart, run full discovery, run complete validation-distribution, or run release gates. Those remain deferred to B2f and D2.

## Out of Scope

- public `apply_lifecycle_transaction()` and public result mapping;
- idempotent replay, completed-evidence lookup, and `noop`;
- loading or recovering incomplete journals after restart;
- recovery manifest, preimage, stage, journal, or workspace cleanup;
- lifecycle, loop, roadmap, issue-index, or Production Record public adapters;
- Doctor, operation audit, distribution, release gates, PR publication, merge, or plugin release;
- any Git, subprocess, network, remote, database, service, scheduler, Prefect, or automation control-plane integration.

## Compatibility

- No public command, CLI JSON, plugin, setting, dependency, or external integration changes.
- The A2 public plan serializer and provisional planner output remain unchanged.
- B1d pure evidence serialization remains unchanged and is reused as the only evidence renderer.
- Ordinary storage functions keep rejecting evidence; new evidence-specific functions are additive.
- The journal schema and phase vocabulary remain unchanged.
- B2c post-apply summaries and failure signals remain unchanged; finalization failures reuse the same rollback ownership and redaction rules.
- Existing untracked Issue 103 implementation plans remain untouched and unstaged.
