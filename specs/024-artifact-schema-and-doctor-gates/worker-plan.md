# Worker Plan: 024-artifact-schema-and-doctor-gates

Mode: `sequential`
Parallel eligible: `false`

## Tasks

| ID | Worker | Group | Status | Files | Depends | Task |
| --- | --- | --- | --- | --- | --- | --- |
| T01 | `qa-reviewer` | `sequential` | done | tests/test_validation_distribution.py | - | Add schema gate RED tests |
| T02 | `implementation-worker` | `group-2` | done | scripts/validate_project_artifacts.py | T01 | Implement active issue linked artifact validation |
| T03 | `roadmap-planner` | `group-3` | done | scripts/validate_project_artifacts.py | T02 | Implement dashboard/roadmap/next_command drift checks |
| T04 | `implementation-worker` | `sequential` | done | scripts/project_doctor.py | T03 | Surface schema gates in project doctor |
| T05 | `qa-reviewer` | `sequential` | done | specs/024-artifact-schema-and-doctor-gates/status.md, specs/024-artifact-schema-and-doctor-gates/release.md | T04 | Run full verification and release 024 |

## Isolation

- T01: `codex/024-artifact-schema-and-doctor-gates-t01`
- T02: `codex/024-artifact-schema-and-doctor-gates-t02`
- T03: `codex/024-artifact-schema-and-doctor-gates-t03`
- T04: `codex/024-artifact-schema-and-doctor-gates-t04`
- T05: `codex/024-artifact-schema-and-doctor-gates-t05`

## Merge Order

- T01 → T02 → T03 → T04 → T05

## Worker Inventory

- All worker files are covered by routing rules.

## Risks

- Task 1 touches shared state: Add schema gate RED tests
- Task 4 touches shared state: Surface schema gates in project doctor
- Task 5 touches shared state: Run full verification and release 024
- scripts/validate_project_artifacts.py is expected by T02 and T03

## Next Command

`product:execute 024-artifact-schema-and-doctor-gates`
