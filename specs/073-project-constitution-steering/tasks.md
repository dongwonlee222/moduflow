# Tasks: 073-project-constitution-steering

Plan: `specs/073-project-constitution-steering/plan.md`
Status: ready-for-execute · Mode: inline coordinator (no worker split — judgment-class doc work) · Order: A1 → (B1 ∥ B2 ∥ B3) → D1

## Stream A — the document

- [ ] A1. `workspace/constitution.md` + `constitution.ko.md`: header (v1.0 pending ratification, amendment procedure, unlogged-edit-void + revert path, AGENTS.md jurisdiction line), ~10 origin-referenced principles from practiced law, amendment log with pending-v1.0 row — depends: none

## Stream B — consumption wiring

- [ ] B1. `commands/product-plan.md` reference-form GC instruction (+ additions-not-amendments distinction) + `commands/product-spec.md` constitution-assumed note — depends: A1
- [ ] B2. Compliance line in `commands/product-review.md` + review-handoff template string in `scripts/project_execution.py` (string edit only, GC1) — depends: A1
- [ ] B3. `commands/product-converge.md` transitive-enforcement sentence — depends: A1

## Stream D — closeout

- [ ] D1. 073's own review carries the first compliance line; status.md notes next-issue reference-form dogfood (spec AC); review handoff; Draft PR body carries the explicit v1.0 ratification ask — depends: B1, B2, B3

## Verification per task

- A1: every principle's origin ref resolves (coordinator check); validate_project_artifacts clean.
- B1/B2/B3: full test suite green (template-string regression insurance); reviewer read.
- D1: compliance line present in 073's review.md; ratification ask visible in PR body.

## Gates recap

test → self-application (own review uses the line) → review (converge auto-run) → release (version bump in completion commit; human ratification = merge approval). Rollback: revert merge; docs + one template string.

## Converge Findings (auto)

- [ ] CV-1 [medium] unverifiable: AC requires the NEXT issue's plan to use the reference form with dogfood evidence recorded in status.md. That artifact is absent from the bundle and the event is future-facing relative to these commits; cannot judge. — AC#8, from converge 2026-07-07
