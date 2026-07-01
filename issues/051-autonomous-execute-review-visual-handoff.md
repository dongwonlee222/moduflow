# Issue: `051-autonomous-execute-review-visual-handoff`

**Status: done** — created 2026-07-01, started 2026-07-01, done 2026-07-01.

## Outcome

ModuFlow execution stops feeling like disconnected prompts: after implementation, it produces a review handoff that includes subagent dispatch instructions, verification commands, and the dashboard plus issue drill-down paths for human inspection.

## Why

The current docs say `product:execute` and `product:review` should use subagents, but the workflow often falls back to inline manual work. The dashboard visual surface and its issue drill-down are also separate manual steps, so the user does not automatically get the promised HTML inspection surface after development/review.

## Scope

### In

- Add a small execution handoff helper that turns an issue's tasks/spec/status into a concrete `review-handoff.md`.
- Include implementation-worker and review-worker dispatch blocks in the handoff.
- Include required verification commands and dashboard plus issue drill-down generation commands/paths.
- Update `product:execute` and `product:review` docs so the handoff is part of the normal flow.
- Add tests proving the handoff contains subagent review and visual HTML instructions.

### Out

- Building a full hosted subagent execution backend.
- Forcing automatic GitHub PR creation.
- Replacing host-specific subagent APIs; the handoff stays host-agnostic.

## Acceptance Criteria

- `scripts/project_execution.py --review-handoff --issue-id 051-autonomous-execute-review-visual-handoff --write` writes `specs/051-autonomous-execute-review-visual-handoff/review-handoff.md`.
- The handoff includes implementation subagent, QA reviewer, PM/spec reviewer, verification commands, `memory/dashboard.html`, and the issue drill-down output path.
- `product:execute` docs make handoff generation part of implementation completion.
- `product:review` docs require review subagent results, dashboard HTML, and issue drill-down HTML before concluding.
- `python3 -m unittest tests.test_project_execution -v` passes.
- `python3 scripts/release_check.py .` passes.

## Workflow Tasks

Every artifact-producing step is a tracked task here — never produce a spec/plan/design/review off the books. Check the box and link the artifact when done.

- [x] spec → `specs/051-autonomous-execute-review-visual-handoff/spec.md`
- [x] plan → `specs/051-autonomous-execute-review-visual-handoff/plan.md`
- [x] execute → `scripts/project_execution.py`, command docs, tests
- [x] review → `specs/051-autonomous-execute-review-visual-handoff/review.md`
- [x] create review handoff artifact
- [x] generate dashboard and issue drill-down handoff instructions

## Related Issues

- follows_up: `050-repo-sync-preflight`
- related: `023-worker-routing-and-isolation`, `028-real-subagent-execution-backend`, `047-issue-artifact-drilldown`, `049-bilingual-artifact-view`

## Sessions

- 2026-07-01: User observed that ModuFlow flow breaks after development, does not truly use subagents, and does not automatically provide the promised HTML visual inspection surface.

## Links

- Spec: `specs/051-autonomous-execute-review-visual-handoff/spec.md`
- Status: `specs/051-autonomous-execute-review-visual-handoff/status.md`
- Handoff: `specs/051-autonomous-execute-review-visual-handoff/review-handoff.md`
- Roadmap: `workspace/roadmap.md`

## Next Command

`/product:status`
