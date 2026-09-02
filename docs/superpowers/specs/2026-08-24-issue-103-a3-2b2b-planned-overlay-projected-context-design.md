# Issue 103 A3.2b2b Planned Overlay and Projected Context Design

## Artifact Links

- **Issue ID:** `103-atomic-lifecycle-state-transaction`
- **Parent plan:** `specs/103-atomic-lifecycle-state-transaction/plan.md`, Task A3 Step 3
- **Predecessor:** commit `3b30f70` (`feat(103): copy safe projected snapshots`)
- **Owner / decision maker:** Dongwon Lee
- **Phase:** execute, A3.2b2b design

## Decision

Add a separate private projected-state context manager above the existing snapshot-only `_private_projected_root(plan)` boundary. The new boundary validates every planned target before filesystem side effects, overlays only each target's private `_after_bytes` through no-follow descriptors, verifies the projected bytes, derives a projected Issue 109 context, and yields both values for the later validator integration.

The existing `_private_projected_root(plan)` remains responsible only for authorized canonical snapshot copying and populated-root cleanup. This preserves the independently reviewed A3.2b2a behavior and keeps projected validation orchestration out of the copy primitive.

## Purpose

A3.2b2a produces an ephemeral private copy of current canonical validator inputs. A3.2b2b turns that snapshot into the proposed transaction state without touching canonical files. Its success condition is:

> Inside one authorized private context, every planned logical target contains exactly its immutable proposed bytes, every projected role path resolves below that private root, and exiting the context leaves canonical bytes unchanged and removes the projected tree.

## Selected Architecture

### `_private_projected_state(plan)`

```python
@dataclass(frozen=True)
class _ProjectedState:
    root: Path
    context: dict = field(repr=False, compare=False)

@contextmanager
def _private_projected_state(plan):
    """Yield one verified _ProjectedState for later validation."""
```

The context manager performs this order:

1. Validate the plan type and enforce Issue 110 `write` authorization without filesystem side effects.
2. Preflight every `PlannedTarget` and reject malformed or conflicting target metadata.
3. Enter `_private_projected_root(plan)` to create the bounded canonical snapshot from A3.2b2a.
4. Reopen that root through canonical root and `.moduflow` no-follow directory descriptors.
5. Overlay every target's `_after_bytes` in plan order.
6. Verify each projected file's exact byte count and SHA-256 digest.
7. Build a projected Issue 109 context whose root and role paths point only into the private tree.
8. Yield `_ProjectedState(root=projected_root, context=projected_context)`.
9. Close overlay descriptors; the wrapped A3.2b2a context removes the populated tree in `finally`.

The yielded value is internal and never serialized. Its detached context remains a dictionary because existing validators require a dictionary project context; the frozen wrapper prevents field rebinding but does not make that ephemeral dictionary public. It does not expose descriptors, canonical bytes, recovery payloads, or temporary paths through public transaction output.

### Target preflight

A private preflight helper accepts only the plan's immutable `tuple[PlannedTarget, ...]`. Before entering `_private_projected_root(plan)`, it verifies:

- every item is a `PlannedTarget`;
- `relative_path` is a non-empty project-relative POSIX logical path with no absolute, Windows-absolute, backslash, empty, `.`, or `..` component;
- no target is rooted at `.git` and no target path is duplicated;
- `after_size == len(_after_bytes)`;
- `after_sha256 == sha256(_after_bytes)`;
- the declared digest uses the existing lowercase SHA-256 grammar.

Any failure raises `LifecycleProjectedValidationError("PROJECTED_TARGET_INVALID")`. Authorization occurs first, but preflight completes before descriptor opens, projected directory creation, snapshot copying, or overlay writes.

### Descriptor-relative overlay

Overlay reuses the A3.2b2a private directory conventions:

- open canonical root, canonical `.moduflow`, and the projected child with `O_DIRECTORY | O_NOFOLLOW | O_CLOEXEC` where supported;
- validate and create target parent directories relative to the projected-root descriptor;
- create missing parents with mode `0700`;
- accept only an absent destination or an existing regular non-symlink file;
- create a missing target with `O_RDWR | O_CREAT | O_EXCL`, or open an existing target with `O_RDWR | O_NOFOLLOW`, verify it with `fstat`, and call `ftruncate` only after its regular-file classification succeeds;
- set every overlaid target to mode `0600`;
- write the immutable `_after_bytes` with complete partial-write handling;
- seek to the beginning, read the stored bytes through the same descriptor, and verify size and SHA-256.

A destination symlink, directory, special file, or non-directory parent raises `PROJECTED_TARGET_UNSAFE`. Other descriptor, write, read-back, size, or digest failures raise `PROJECTED_OVERLAY_FAILED`. Both errors remain bounded to the stable code and contain no artifact content or absolute canonical/projected path.

### Projected Issue 109 context

The projected context is rebuilt rather than mutating or shallow-copying the plan's detached canonical context. It contains only the fields later validation consumers require:

- the original context schema and `status="resolved"`;
- the original `project_id`;
- `canonical_root` set to the private projected root;
- a detached copy of `relative_paths`;
- `paths` rebuilt as `<projected-root>/<relative-path>` for every canonical role;
- detached policy metadata fields when present: `project_status`, `trust_scope`, `capabilities`, `capability_reasons`, `policy_inputs`, and `policy_trust_scope`.

Resolver-only `candidates`, `question`, `warnings`, and `reason_code` fields are omitted because they are not validator inputs and may contain stale canonical-resolution detail. The new context must pass `project_registry.context_for_operation(projected_root, project_context=context)`, and every rebuilt role path must be contained by the projected root.

The original frozen `plan._project_context`, its canonical root, and all canonical role paths remain byte-for-byte and value-for-value unchanged.

## Error Contract

This slice adds three stable internal error codes:

- `PROJECTED_TARGET_INVALID`: malformed path, duplicate target, wrong size, or wrong declared digest detected during preflight;
- `PROJECTED_TARGET_UNSAFE`: a projected destination or parent is not a real directory/regular file or is a symlink/special node;
- `PROJECTED_OVERLAY_FAILED`: descriptor I/O or read-back verification fails after valid preflight.

Existing errors retain their meanings:

- Issue 110 denials remain `project_operation.ProjectOperationDenied`;
- snapshot materialization retains `PROJECTED_CONTEXT_INVALID`, `PROJECTED_ROOT_UNAVAILABLE`, `PROJECTED_SOURCE_UNSAFE`, and `PROJECTED_COPY_FAILED`;
- final cleanup retains `PROJECTED_ROOT_CLEANUP_FAILED`.

No error includes `_before_bytes`, `_after_bytes`, an absolute canonical path, the randomized projected-root path, or recovery content.

## Test Contract

Implementation follows RED/GREEN TDD in this order:

1. Build a plan selecting issue, state, loop, dashboard, issue-index, roadmap, Production Record, and evidence targets; assert every projected target equals `_after_bytes`, uses mode `0600`, and has the declared SHA-256.
2. Assert newly required evidence and Production Record parents use mode `0700` and unrelated copied files retain their canonical snapshot bytes.
3. Substitute invalid path, duplicate path, size mismatch, and digest mismatch plans; assert `PROJECTED_TARGET_INVALID` before `os.open`, `os.mkdir`, copying, or overlay writes.
4. Create a destination-type collision after planning; assert `PROJECTED_TARGET_UNSAFE`, no canonical mutation, and complete projected-root cleanup.
5. Inject one overlay write/read-back failure; assert `PROJECTED_OVERLAY_FAILED`, redacted error text, unchanged canonical bytes, and complete cleanup.
6. Assert the projected context's root and all role paths are private-root-contained, relative paths match the canonical context, resolver-only fields are absent, and the canonical frozen context is unchanged.
7. Re-run the A3.2b1/A3.2b2a lifecycle tests to prove the snapshot-only context remains independently usable.

Focused verification remains limited to the transaction module, Issue 110 project-operation module, Issue 103 spec consistency, compilation, and diff hygiene. The known long-running complete `tests.test_validation_distribution` module and release check remain deferred to D2.

## Rejected Alternatives

1. **Overlay inside `_private_projected_root(plan)` — rejected.** It merges snapshot and proposal responsibilities, changes A3.2b2a's observable contract, and makes copying impossible to test independently.
2. **Path-based overlay after the snapshot yields — rejected.** It is shorter but weakens the descriptor/no-follow boundary and repeats unsafe path resolution.
3. **Yield a live file descriptor from the snapshot context — rejected.** It leaks lifecycle ownership to callers and makes cleanup correctness depend on external descriptor handling.

## Out of Scope

- invoking `validate_project_artifacts.validate_project()` or any lifecycle/Production Record validator;
- producing a projected validation summary;
- modifying `scripts/validate_project_artifacts.py` or `tests/test_validation_distribution.py`;
- canonical replacement, locking, journal durability, evidence persistence, apply, rollback, or recovery;
- Git, subprocess, network, or remote-system operations;
- full test discovery and release checks.

Those behaviors remain in A3.2c or later Issue 103 streams.
