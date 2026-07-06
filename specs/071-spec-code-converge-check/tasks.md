# Tasks: 071-spec-code-converge-check

Plan: `specs/071-spec-code-converge-check/plan.md`
Status: ready-for-execute · Parallel: A1 → (A2 ∥ B1) → B2 → D1

## Stream A — deterministic engine

- [ ] A1. `scripts/project_converge.py --evidence`: commit resolution (trailer + merge-subject), current-file bundle with caps + explicit `truncated`, single-parse of AC (checkbox + prose) and plan Global Constraints, evidence JSON per schema, non-zero exit on git/bundle failure in both output modes + `tests/test_project_converge.py` (FakeRunner) — depends: none
- [ ] A2. `--apply-judgment` mode: converge.md dated-section append (never overwrite), tasks.md CV append per fixed grammar with source-ref dedup, byte-for-byte no-op on fully-converged, low = report-only + idempotency/regression-reappend tests — depends: A1

## Stream B — judgment + integration

- [ ] B1. `templates/converge-judgment-prompt.md` (evidence-only input, prefer-unverifiable, Judgment JSON schema) + `commands/product-converge.md` (standalone flow, inline fallback per GC9, no-evidence handling, non-gate framing) — depends: A1 (schema)
- [ ] B2. `commands/product-review.md`: converge as final review evidence step; reported, never blocking — depends: B1

## Stream D — fixtures + dogfood

- [ ] D1. Fixtures exercising `missing` / `unrequested` / `unverifiable`; dogfood run on issue 075 end-to-end with its converge.md committed; docs sweep — depends: A2, B1

## Verification per task

- A1/A2: focused unittest incl. exit-code, caps, no-op, dedup idempotency paths.
- B1/B2: doc/template tasks — `validate_project_artifacts.py` + reviewer read; prompt template exercised by D1.
- D1: the dogfood run is the verification.

## Gates recap

test → self-application (dogfood on 075) → review (071 reviews itself with the new auto-run) → release (version bump in completion commit, linkage gate on `codex/071-*`). Rollback: revert merge commit; additive files.
