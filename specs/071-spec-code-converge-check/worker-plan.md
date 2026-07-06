# Worker Plan: 071-spec-code-converge-check

Mode: `sequential`
Parallel eligible: `false`

## Tasks

| ID | Worker | Group | Status | Files | Depends | Task |
| --- | --- | --- | --- | --- | --- | --- |
| T01 | `qa-reviewer` | `sequential` | ready | - | - | A1. `scripts/project_converge.py --evidence`: commit resolution (trailer + merge-subject), current-file bundle with caps + explicit `truncated`, single-parse of AC (checkbox + prose) and plan Global Constraints, evidence JSON per schema, non-zero exit on git/bundle failure in both output modes + `tests/test_project_converge.py` (FakeRunner) — depends: none |
| T02 | `qa-reviewer` | `group-1` | ready | - | - | A2. `--apply-judgment` mode: converge.md dated-section append (never overwrite), tasks.md CV append per fixed grammar with source-ref dedup, byte-for-byte no-op on fully-converged, low = report-only + idempotency/regression-reappend tests — depends: A1 |
| T03 | `ux-flow-worker` | `sequential` | ready | - | - | B1. `templates/converge-judgment-prompt.md` (evidence-only input, prefer-unverifiable, Judgment JSON schema) + `commands/product-converge.md` (standalone flow, inline fallback per GC9, no-evidence handling, non-gate framing) — depends: A1 (schema) |
| T04 | `data-reviewer` | `sequential` | ready | - | - | B2. `commands/product-review.md`: converge as final review evidence step; reported, never blocking — depends: B1 |
| T05 | `release-manager` | `group-4` | ready | - | - | D1. Fixtures exercising `missing` / `unrequested` / `unverifiable`; dogfood run on issue 075 end-to-end with its converge.md committed; docs sweep — depends: A2, B1 |

## Isolation

- T01: `codex/071-spec-code-converge-check-t01`
- T02: `codex/071-spec-code-converge-check-t02`
- T03: `codex/071-spec-code-converge-check-t03`
- T04: `codex/071-spec-code-converge-check-t04`
- T05: `codex/071-spec-code-converge-check-t05`

## Merge Order

- T01 → T02 → T03 → T04 → T05

## Worker Inventory

- All worker files are covered by routing rules.

## Risks

- Task 1 touches shared state: A1. `scripts/project_converge.py --evidence`: commit resolution (trailer + merge-subject), current-file bundle with caps + explicit `truncated`, single-parse of AC (checkbox + prose) and plan Global Constraints, evidence JSON per schema, non-zero exit on git/bundle failure in both output modes + `tests/test_project_converge.py` (FakeRunner) — depends: none
- Task 3 touches shared state: B1. `templates/converge-judgment-prompt.md` (evidence-only input, prefer-unverifiable, Judgment JSON schema) + `commands/product-converge.md` (standalone flow, inline fallback per GC9, no-evidence handling, non-gate framing) — depends: A1 (schema)
- Task 4 touches shared state: B2. `commands/product-review.md`: converge as final review evidence step; reported, never blocking — depends: B1

## Next Command

`product:execute 071-spec-code-converge-check`
