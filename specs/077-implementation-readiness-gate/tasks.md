# Tasks: 077-implementation-readiness-gate

Issue: `077-implementation-readiness-gate`

## Implementation

- [x] T1 Readiness checker — `scripts/project_execution.py`, `tests/test_project_execution.py`
- [x] T2 Readiness CLI/artifact writer — `scripts/project_execution.py`, `tests/test_project_execution.py`
- [x] T3 Loop routing for `not_ready` — `scripts/project_loop.py`, `tests/test_project_loop.py`
- [x] T4 Command and skill guidance — `commands/product-execute.md`, `commands/product-plan.md`, `commands/product-loop.md`, `skills/superpowers-execution-bridge/SKILL.md`
- [x] T5 Dogfood readiness artifact and validation — `specs/077-implementation-readiness-gate/implementation-readiness.json`, `status.md`

## Acceptance Coverage

- AC1 `product:execute` readiness step → T2, T4
- AC2 concrete missing contracts/severity → T1, T2
- AC3 conditional frontend checks → T1
- AC4 machine-readable artifact → T2, T5
- AC5 `product:loop` recommends `product:plan` on `not_ready` → T3
- AC6 `product:plan` readiness evidence guidance → T4
- AC7 validation passes → T5

## Next

`product:review 077-implementation-readiness-gate`
