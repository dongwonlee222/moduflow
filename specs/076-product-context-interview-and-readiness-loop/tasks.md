# Tasks: Fast Path Shaping Router (076)

Issue: `076-product-context-interview-and-readiness-loop`
Plan: `specs/076-product-context-interview-and-readiness-loop/plan.md`

## Stream A — Intake Router Behavior

- [x] A1 — Add tests for fast, short-shaping, and panel routing in `tests/test_project_intake.py`.
- [x] A2 — Run the failing intake test slice.
- [x] A3 — Add shaping signal/question helpers to `scripts/project_intake.py`.
- [x] A4 — Wire `shaping_path`, `shaping_reason`, `question_count`, `suggested_questions`, and `durable_context` into `route_intake`.
- [x] A5 — Run `python3 -m unittest tests.test_project_intake.ProjectIntakeTests -v`.

## Stream B — Command and Skill Surface

- [x] B1 — Document fast/shaping/panel routing in `skills/pm-execution-router/SKILL.md`.
- [x] B2 — Update `commands/product-loop.md` recommendation contract.
- [x] B3 — Update `commands/product-issue.md` fast-path wording.
- [x] B4 — Update `commands/product-opportunity.md` as the shaping destination.
- [x] B5 — Update `commands/product-spec.md` to preserve shaped product rationale.

## Stream C — Artifact Handoff

- [x] C1 — Keep `tasks.md` synchronized with the plan streams.
- [x] C2 — Check the issue's plan workflow task.
- [x] C3 — Update status and roadmap to review-ready state.

## Stream D — Verification

- [x] D1 — Run focused intake tests.
- [x] D2 — Run ModuFlow artifact validation.
- [x] D3 — Run release gate.
- [x] D4 — Record verification in status.
