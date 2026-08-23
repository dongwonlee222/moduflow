# Issue 103 A2 Planner Boundary Design

## Artifact Links

- **Issue ID:** `103-atomic-lifecycle-state-transaction`
- **Source request:** 2026-08-23 execution review — clarify the purpose of the internal API and proceed one boundary at a time after repeated A2 implementation stalls.
- **Owner / decision maker:** Dongwon Lee
- **Phase:** plan
- **Next command:** `product:plan 103-atomic-lifecycle-state-transaction` for the A2 planner slice

## Decision

Implement only the read-only lifecycle transaction planner in the next slice. The planner computes an immutable in-memory change set and a redacted public preview. It does not authorize writes, create directories, stage files, validate a projected root, replace canonical files, or perform recovery.

The term **public API** means a stable Python entry point shared by ModuFlow commands. It is not an HTTP or externally hosted API.

## Purpose

Lifecycle commands currently risk deriving or writing issue, state, loop, dashboard, roadmap, index, Production Record, and evidence artifacts independently. Issue 103 introduces one transaction boundary so every mutating workflow eventually uses the same planned target set, validation gate, apply order, and rollback evidence.

The planner is the first boundary. Its success condition is:

> Given one resolved project context and one normalized lifecycle intent, compute exactly what would change without causing any filesystem mutation.

## Selected Architecture

### `PlannedTarget`

An immutable internal value for one selected artifact:

```python
@dataclass(frozen=True)
class PlannedTarget:
    role: str
    relative_path: str
    existed: bool
    before_sha256: str
    after_sha256: str
    after_size: int
    changed: bool
    validation_rules: tuple[str, ...]
    apply_order: int
    rollback_order: int
    _before_bytes: bytes = field(repr=False)
    _after_bytes: bytes = field(repr=False)
```

Bytes remain in memory for the later projected-validation and rollback layers. They are immutable and excluded from representations, public dictionaries, errors, evidence, and logs.

### `LifecycleTransactionPlan`

An immutable internal value for the complete operation:

```python
@dataclass(frozen=True)
class LifecycleTransactionPlan:
    schema: str
    transaction_id: str
    idempotency_key: str
    project_id: str
    canonical_root: str
    issue_id: str
    action: str
    target_lifecycle: str | None
    targets: tuple[PlannedTarget, ...]
    _project_context: Mapping = field(repr=False)
```

The class exposes `to_public_dict(self) -> dict`. That method constructs only the exact `moduflow.lifecycle-transaction-plan.v1` schema fields and delegates final validation to `serialize_transaction_plan()`. The project context is recursively detached and frozen at construction. Later authorization code may create a detached dictionary from that snapshot, but callers cannot mutate a completed plan through the original context object.

### Entry Point

```python
def plan_lifecycle_transaction(
    project_root,
    intent: LifecycleIntent,
    *,
    project_context=None,
    clock=None,
) -> LifecycleTransactionPlan:
    """Compute one immutable transaction plan without filesystem writes."""
```

`to_public_dict()` returns `moduflow.lifecycle-transaction-plan.v1` with the existing target record field `after_bytes` representing the proposed byte count. It never returns `_before_bytes`, `_after_bytes`, a staging path, or recovery content.

## Planning Flow

1. Bind `project_root` to one resolved Issue 109 context with `context_for_operation()`.
2. Normalize and deep-freeze the `LifecycleIntent` with the Issue 103 A1 contract.
3. Resolve every logical target from the bound context.
4. Reject path escape, symlink traversal, non-regular required targets, and unreadable required targets before reading content.
5. Read each selected target at most once.
6. Render proposed bytes in memory with pure renderers.
7. Build immutable target values and sort them in this exact order: `issue`, `state`, `loop`, `dashboard`, `issue-index`, `roadmap`, `production-record`, `evidence`.
8. Return the immutable plan. No write authorization is required because planning has no side effects.

## Target Selection

Always selected:

- owning issue Markdown from the canonical `issues` role;
- `.moduflow/state.json` under the canonical root;
- `loop-state.json` and `dashboard.md` under the canonical `workspace` role;
- redacted transaction evidence under `transactions/<transaction-id>.json` below the canonical `workspace` role.

Conditionally selected:

- `issue-index.json` when it already exists or `require_issue_index=True`;
- `roadmap.md` only when `roadmap_change` is present;
- one Production Record only when `production_change` is present.

Missing `issue-index` is a valid absent preimage when explicitly required. A new Production Record and evidence target are also valid absent preimages. Required issue, state, loop, and dashboard targets must exist as regular, non-symlink files. A selected roadmap must already exist because its unmanaged bytes must be preserved.

## Safe Error Contract

Planner failures raise `LifecyclePlanError`, a `ValueError` subtype with:

- stable `code`;
- logical `role`;
- project-relative `relative_path` when available;
- a bounded message containing no artifact bytes, absolute temporary paths, or recovery payloads.

Required codes for this slice:

- `PLAN_CONTEXT_INVALID`
- `PLAN_TARGET_MISSING`
- `PLAN_TARGET_UNREADABLE`
- `PLAN_TARGET_NOT_REGULAR`
- `PLAN_TARGET_SYMLINK`
- `PLAN_PATH_ESCAPE`
- `PLAN_RENDER_INVALID`

## Rejected Alternatives

1. **Plain dictionary containing raw bytes — rejected.** It makes accidental logging and serialization of source content too easy.
2. **Public dictionary plus process-global cache — rejected.** Hidden state breaks deterministic restart behavior and creates concurrency ambiguity.
3. **Dictionary subclass with mutable private attributes — rejected.** The current inherited `plan._project_context` test demonstrates the problem: callers can alter authorization state after planning.

## Test Contract

The planner slice uses RED/GREEN TDD in this order:

1. Replace the mutable `plan._project_context` expectation with immutable plan and detached-context assertions.
2. Assert required and conditional target selection plus exact target order.
3. Assert nested Issue 109 paths are the only paths read and poisoned defaults remain byte-identical.
4. Assert every selected source is read at most once.
5. Assert mutating the original intent/context after planning cannot change the plan or its public preview.
6. Assert the public preview contains logical paths, hashes, byte counts, and validation rule IDs only.
7. Assert planning makes zero calls to directory creation, temporary-file creation, file writes, replacement, Git, subprocess, or network boundaries.
8. Assert symlinks, path escape, missing required targets, and unreadable/non-regular targets fail with the stable safe errors above.

## Out of Scope for This Slice

- write capability enforcement;
- transaction staging directories;
- projected-root copying and overlay;
- project, lifecycle, and Production Record validation;
- canonical replacement, journal durability, rollback, crash recovery, and public mutation adapters.

Those behaviors consume the immutable plan in separately reviewed slices. No implementation of them is accepted into the planner commit.

## Compatibility

- The A1 `LifecycleIntent`, identity hashes, terminal status vocabulary, and plan/result schema names remain unchanged.
- Existing lifecycle and loop public writers remain unchanged in this slice.
- Existing pure renderer additions may be retained as planner dependencies, but their public mutation routing remains deferred.
- The follow-on A2 plan amendment must replace the previous `plan_lifecycle_transaction() -> dict` declaration with `LifecycleTransactionPlan`; `to_public_dict()` preserves the exact redacted dictionary schema for consumers.
