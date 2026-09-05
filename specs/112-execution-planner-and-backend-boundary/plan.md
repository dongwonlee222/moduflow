# Plan: Execution Planner and Backend Boundary

Issue: `112-execution-planner-and-backend-boundary`
Spec: `specs/112-execution-planner-and-backend-boundary/spec.md`
Prev: `product:spec` · Next: `product:workers 112-execution-planner-and-backend-boundary`

## Global Constraints

Constitution v1.0 applies (`workspace/constitution.md`). Plan-specific additions:

- **GC1 — No dispatch claim.** No function added by this issue may report that
  work was executed. `dispatched` stays `false` and `executed_by` stays null in
  every code path, including error paths.
- **GC2 — Refusal writes nothing.** A `needs_plan` or `not_applicable` result
  must leave the filesystem byte-identical. Assert absence of `worker-plan.*`
  after refusal, not just the return value.
- **GC3 — No host string in the routing result.** No `codex/`, no model name,
  no vendor vocabulary. Host mapping happens in an adapter, and a test greps
  the result payload for host tokens.
- **GC4 — Source order is identity.** Task IDs are assigned before filtering and
  never recomputed. Any change that renumbers survivors is a defect regardless
  of whether tests still pass.
- **GC5 — Do not re-plan `dispatchable_now`.** It shipped in `ba1269a`. Extend
  it if needed; do not reimplement its eligibility logic elsewhere.
- **GC6 — Match shipped dependency semantics.** A dependency on a completed task
  is satisfied (`w_o.py:246`). A stricter rule is a regression, not a hardening.

## Recommended Discipline

| Stream | Discipline / Adapter | Reason |
| --- | --- | --- |
| A — gate selection and refusal | Superpowers TDD + focused tests | Parser and filter behaviour must prove RED/GREEN before the contract is trusted. |
| B — routing decision | Superpowers TDD | `inline` versus `superpowers-sdd` is a pure function of declared boundaries; it should be provable in isolation. |
| C — host adapter boundary | product-design + review | The unproven part of this issue. Needs an interface decision reviewed before code, not after. |
| D — artifact ownership | product-converge | Canonical-versus-Superpowers divergence is a reconciliation question, which converge already models. |
| E — verification | verification-before-completion | Criteria 13 and 14 have no evidence yet; completion claims need fresh proof. |

The matrix is guidance, not an execution gate.

## Reference Implementation

A working prototype of Streams A and B already exists at
`specs/112-execution-planner-and-backend-boundary/evidence/`. It was run against
all 55 specs and carries 34 passing tests, including a parity assertion against
the shipped `parse_tasks`. Streams A and B are a **port with hardening**, not a
design from scratch: the gate logic is settled and the open work is integration,
the two notations, and the result schema.

Streams C, D and E have no prototype and hold this issue's real risk.

## File Structure

### Create

| Path | Purpose |
| --- | --- |
| `scripts/execution_routing.py` | Gates 1-3 and the `moduflow.execution-routing.v1` result. Kept separate from `worker_orchestrator` so the routing contract is importable without pulling in plan rendering. |
| `scripts/execution_host_adapter.py` | Maps one routing result to a host vocabulary. |
| `tests/test_execution_routing.py` | Stream A/B behaviour, ported from the prototype. |
| `tests/test_execution_host_adapter.py` | Cross-host fixtures for criterion 13. |
| `tests/fixtures/execution-routing/` | Notation fixtures, including the `\| Files:` form from 103/109/110. |

### Modify

| Path | Change |
| --- | --- |
| `scripts/worker_orchestrator.py` | `build_worker_plan` consumes the routing result instead of iterating raw tasks; `write_worker_plan` refuses on a non-`ok` status; `project_root` becomes relative; `isolation.worktree` and the model-name prompt text move behind the adapter. |
| `commands/product-workers.md` | Document the three results and that refusal is a normal outcome. |
| `commands/product-execute.md` | Document that the backend is chosen upstream and never dispatched by ModuFlow. |
| `skills/superpowers-execution-bridge/SKILL.md` | Consume `superpowers-sdd` as a routing result rather than deciding delegation itself. |
| `tests/test_worker_orchestration.py` | Existing expectations that assume every checkbox becomes a task. |

## Stable Interfaces

`scripts/execution_routing.py` is the only interface other streams consume.

```
build_routing(tasks, project_root) -> moduflow.execution-routing.v1
    status         "ok" | "needs_plan" | "not_applicable"
    backend        "inline" | "superpowers-sdd" | None
    routing_reason non-empty for every status
    gaps           [{task_id, kind: "no_boundary"|"unreadable_notation"|"dangling_dependency", detail}]
    tasks          selected tasks with boundaries and dependencies; [] unless ok
    written        [] always for this function
    dispatched     False always
    executed_by    None always
    project_root   repository-relative
    next_command
```

- **A produces, B consumes**: Stream B receives the Gate 1/2 survivors and adds
  only `backend` and `routing_reason`. B never re-reads `tasks.md`.
- **B produces, C consumes**: the adapter receives a complete `ok` result and
  returns host-shaped instructions. It may not modify the result.
- **C produces, worker_orchestrator consumes**: plan rendering reads adapter
  output for worktree and prompt text, and the routing result for everything else.
- **D is orthogonal**: reconciliation reads canonical artifacts and Superpowers
  links; it does not touch the routing result.

`gaps` carrying a `kind` is what makes criterion 7 testable and lets
`product:plan` tell an author which of the two problems they have.

## Implementation Readiness Contracts

- **API contract mapping**: not applicable. No HTTP surface; the contract is the
  Python function signature and result schema documented under Stable Interfaces.
- **Test strategy**: Stream A/B port the prototype's 34 tests and add notation
  fixtures. Stream C proves criterion 13 with three host fixtures. Stream D
  proves criterion 14 with a conflicting-completion fixture. Every gate has a
  RED case before its GREEN.
- **Storybook required states**: not applicable, no UI.
- **MSW fixture baseline**: not applicable, no API-backed UI.
- **Playwright smoke matrix**: not applicable, no browser-visible flow.
- **Permission/role model**: not applicable to this issue. Capability and
  identity enforcement stay as they are; identity is Issue 122.
- **Release/rollback verification**: `python3 scripts/release_check.py .` green,
  and `product:workers` on 029 still produces a usable plan. Rollback is
  reverting the commit range; no data migration is introduced.

## Streams

### Stream A — Selection and refusal

Port Gates 1 and 2 from the prototype into `scripts/execution_routing.py`, then
harden two things the prototype does not do: typed `gaps` with a `kind`, and
recognition of the `| Files:` notation as `unreadable_notation` rather than
`no_boundary`.

Deciding whether to *parse* the pipe notation is deliberately out of scope. This
issue reports it accurately; the drift itself is an authoring-convention question.

### Stream B — Routing decision

Port Gate 3. Boundary collision is path containment via fnmatch, not string
equality. `inline` is a success result and must be asserted as one.

### Stream C — Host adapter boundary

The unproven stream. Move `codex/` and the model-name prompt text out of the
routing result and behind `scripts/execution_host_adapter.py`, then prove with
Claude Code, Codex and Copilot fixtures that the same result maps three ways
with no canonical artifact change.

Design the adapter interface and get it reviewed before writing the mapping.

### Stream D — Canonical artifact ownership

Detect and report when a canonical task and its linked Superpowers execution
detail disagree about completion. Report, never auto-resolve: canonical wins and
the divergence surfaces.

### Stream E — Integration and verification

Wire `worker_orchestrator` onto the routing result, update the three command and
skill documents, and re-run the corpus. The corpus verdict distribution is
recorded evidence, not a pass/fail gate.

## Gates

| Gate | Condition |
| --- | --- |
| Test | `python3 -m unittest discover -s tests` green; new suites present |
| Corpus | 029 still plans; 001 still refuses; 023 still `not_applicable` |
| Review | Stream C interface reviewed before its mapping code |
| Release | `python3 scripts/release_check.py .` 14/14 |
| Rollback | Revert the commit range; no migration to undo |

## Dogfood Condition

This plan's own `tasks.md` declares `[files:]` and `[depends:]` on every task,
so it must pass the gates this issue specifies. Once Stream A lands, running the
routing on `112` itself must return `ok`. A spec that fails its own gate is not
ready to ship.

## Next

- `python3 scripts/spec_consistency.py . --issue-id 112-execution-planner-and-backend-boundary`
- `product:workers 112-execution-planner-and-backend-boundary`
- `product:execute` after the Stream C interface review
