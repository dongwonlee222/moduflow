# Worker Plan: 112-execution-planner-and-backend-boundary

Mode: `sequential`
Parallel eligible: `false`

## Tasks

| ID | Worker | Group | Status | Files | Depends | Task |
| --- | --- | --- | --- | --- | --- | --- |
| T01 | `qa-reviewer` | `group-1` | ready | scripts/execution_routing.py, tests/test_execution_routing.py | - | Port Gate 1 and Gate 2 from the evidence prototype into a standalone routing module with its RED/GREEN tests |
| T02 | `implementation-worker` | `group-2` | ready | scripts/execution_routing.py | T01 | Add typed gaps carrying a kind of no_boundary, unreadable_notation or dangling_dependency |
| T03 | `spec-architect` | `group-3` | ready | tests/fixtures/execution-routing/pipe-notation-tasks.md, tests/test_execution_routing.py | T02 | Add notation fixtures covering the pipe form used by specs 103, 109 and 110 and assert it reports unreadable_notation |
| T04 | `implementation-worker` | `group-2` | ready | scripts/execution_routing.py, tests/test_execution_routing.py | T01 | Port Gate 3 with fnmatch path containment and assert inline is a success result |
| T05 | `spec-architect` | `group-3` | ready | docs/superpowers/specs/2026-09-05-issue-112-host-adapter-interface.md | T04 | Design and document the host adapter interface for review before any mapping code |
| T06 | `implementation-worker` | `group-2` | ready | scripts/execution_host_adapter.py | T05 | Implement the adapter and move the codex worktree prefix and model-name prompt text out of the routing result |
| T07 | `implementation-worker` | `group-2` | ready | tests/test_execution_host_adapter.py, tests/fixtures/execution-routing/hosts.json | T06 | Prove one routing result maps to Claude Code, Codex and Copilot with no canonical artifact change |
| T08 | `data-reviewer` | `group-4` | ready | scripts/execution_routing.py, tests/test_execution_routing.py | T02 | Detect and report canonical versus Superpowers completion divergence without auto-resolving it |
| T09 | `implementation-worker` | `sequential` | ready | scripts/worker_orchestrator.py | T04, T06 | Consume the routing result in the worker plan builder, refuse to write on a non-ok status, and emit a relative project root |
| T10 | `qa-reviewer` | `group-1` | ready | tests/test_worker_orchestration.py | T09 | Update the existing worker orchestration tests that assume every checkbox becomes a worker task |
| T11 | `implementation-worker` | `group-2` | ready | commands/product-workers.md, commands/product-execute.md, skills/superpowers-execution-bridge/SKILL.md | T09 | Update the worker, execute and Superpowers bridge documents to describe refusal as a normal outcome |
| T12 | `implementation-worker` | `group-2` | ready | specs/112-execution-planner-and-backend-boundary/status.md | T03, T07, T08, T10, T11 | Re-run the corpus and this issue's own dogfood check, then record the verdict distribution as evidence |
| T13 | `qa-reviewer` | `group-1` | ready | - | - | `python3 -m unittest discover -s tests` green with the new suites present. |
| T14 | `implementation-worker` | `group-2` | ready | - | - | Corpus behaviour holds: 029 plans, 001 refuses, 023 is not_applicable. |
| T15 | `spec-architect` | `group-3` | ready | - | - | Stream C interface reviewed before its mapping code was written. |
| T16 | `data-reviewer` | `group-4` | ready | - | - | `python3 scripts/release_check.py .` reports 14 of 14. |
| T17 | `implementation-worker` | `group-2` | ready | - | - | Running the routing on issue 112 itself returns `ok`. |

## Isolation

- T01: `codex/112-execution-planner-and-backend-boundary-t01`
- T02: `codex/112-execution-planner-and-backend-boundary-t02`
- T03: `codex/112-execution-planner-and-backend-boundary-t03`
- T04: `codex/112-execution-planner-and-backend-boundary-t04`
- T05: `codex/112-execution-planner-and-backend-boundary-t05`
- T06: `codex/112-execution-planner-and-backend-boundary-t06`
- T07: `codex/112-execution-planner-and-backend-boundary-t07`
- T08: `codex/112-execution-planner-and-backend-boundary-t08`
- T09: `codex/112-execution-planner-and-backend-boundary-t09`
- T10: `codex/112-execution-planner-and-backend-boundary-t10`
- T11: `codex/112-execution-planner-and-backend-boundary-t11`
- T12: `codex/112-execution-planner-and-backend-boundary-t12`
- T13: `codex/112-execution-planner-and-backend-boundary-t13`
- T14: `codex/112-execution-planner-and-backend-boundary-t14`
- T15: `codex/112-execution-planner-and-backend-boundary-t15`
- T16: `codex/112-execution-planner-and-backend-boundary-t16`
- T17: `codex/112-execution-planner-and-backend-boundary-t17`

## Dispatchable Now

- `T01` — scripts/execution_routing.py, tests/test_execution_routing.py

## Merge Order

- T01 → T02 → T03 → T04 → T05 → T06 → T07 → T08 → T09 → T10 → T11 → T12 → T13 → T14 → T15 → T16 → T17

## Worker Inventory

- All worker files are covered by routing rules.

## Risks

- Task 9 touches shared state: Consume the routing result in the worker plan builder, refuse to write on a non-ok status, and emit a relative project root
- scripts/execution_routing.py is expected by T01 and T02
- tests/test_execution_routing.py is expected by T01 and T03
- scripts/execution_routing.py is expected by T01 and T04
- tests/test_execution_routing.py is expected by T01 and T04
- scripts/execution_routing.py is expected by T01 and T08
- tests/test_execution_routing.py is expected by T01 and T08

## Next Command

`product:execute 112-execution-planner-and-backend-boundary`
