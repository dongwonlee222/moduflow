# Worker Plan: 023-worker-routing-and-isolation

Mode: `sequential`
Parallel eligible: `false`

## Tasks

| ID | Worker | Group | Status | Files | Depends | Task |
| --- | --- | --- | --- | --- | --- | --- |
| T01 | `qa-reviewer` | `group-1` | done | tests/test_worker_orchestration.py | - | Add failing worker routing tests |
| T02 | `data-reviewer` | `group-2` | done | scripts/worker_orchestrator.py | T01 | Implement metadata-aware worker routing |
| T03 | `implementation-worker` | `sequential` | done | scripts/worker_orchestrator.py | T02 | Add file-overlap and shared-state parallel fallback |
| T04 | `implementation-worker` | `group-3` | done | scripts/worker_orchestrator.py | T03 | Add worktree isolation and merge order output |
| T05 | `release-manager` | `group-4` | done | commands/product-workers.md, commands/product-execute.md, README.md | T04 | Update worker command docs |
| T06 | `qa-reviewer` | `group-1` | done | specs/023-worker-routing-and-isolation/status.md, specs/023-worker-routing-and-isolation/release.md | T05 | Run full verification and release 023 |

## Isolation

- T01: `codex/023-worker-routing-and-isolation-t01`
- T02: `codex/023-worker-routing-and-isolation-t02`
- T03: `codex/023-worker-routing-and-isolation-t03`
- T04: `codex/023-worker-routing-and-isolation-t04`
- T05: `codex/023-worker-routing-and-isolation-t05`
- T06: `codex/023-worker-routing-and-isolation-t06`

## Merge Order

- T01 → T02 → T03 → T04 → T05 → T06

## Worker Inventory

- All worker files are covered by routing rules.

## Risks

- Task 3 touches shared state: Add file-overlap and shared-state parallel fallback
- scripts/worker_orchestrator.py is expected by T02 and T03
- scripts/worker_orchestrator.py is expected by T02 and T04

## Next Command

`product:execute 023-worker-routing-and-isolation`
