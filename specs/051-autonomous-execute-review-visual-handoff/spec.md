# Spec: Autonomous Execute, Review, And Visual Handoff

Issue: `051-autonomous-execute-review-visual-handoff`
Next: `product:execute 051-autonomous-execute-review-visual-handoff`

## Problem

ModuFlow's command docs describe a flow where implementation uses workers, review uses specialized reviewers, and humans can inspect generated dashboard HTML. In practice, those steps are not bound together. The main agent often asks the user whether to continue, performs inline review, and reports text results without regenerating the dashboard and issue drill-down views.

## Users

- Dongwon Lee, who expects ModuFlow to continue through development, review, verification, and visual handoff without repeated "shall I proceed?" pauses.
- A coding agent using ModuFlow command docs to decide the next action.

## Goals

- Make the post-implementation handoff explicit, repeatable, and testable.
- Ensure review subagents are represented as required work products, not optional prose.
- Ensure dashboard-level visual inspection, including issue drill-down, is always part of the review handoff.

## Non-Goals

- No direct dependency on one host's subagent API.
- No automatic browser launching.
- No cloud execution backend.
- No replacement for `worker_orchestrator.py`.

## Requirements

1. Add `scripts/project_execution.py` with a `--review-handoff` mode.
2. The helper reads issue/spec/tasks/status artifacts and writes `specs/<issue>/review-handoff.md`.
3. The handoff includes:
   - implementation subagent dispatch summary
   - QA reviewer dispatch summary
   - PM/spec reviewer dispatch summary
   - verification commands
   - dashboard command: `python3 scripts/project_memory.py <project-path> --dashboard`
   - issue drill-down command: `python3 scripts/project_memory.py <project-path> --issue <issue>`
   - visual output paths: `memory/dashboard.html` and `memory/issue-<issue>.html`
4. `commands/product-execute.md` requires generating the handoff at implementation completion.
5. `commands/product-review.md` requires reviewer results plus dashboard and issue drill-down HTML before concluding review.

## Acceptance Criteria

- Tests can generate a handoff in a temp project without network access.
- The generated handoff names `implementation-worker`, `qa-reviewer`, and `pm-strategist/spec-architect`.
- The generated handoff includes `python3 -m unittest discover -s tests -v`, `python3 scripts/release_check.py .`, `memory/dashboard.html`, and `memory/issue-<issue>.html`.
- Release checks pass.

## Risks

- Host-specific subagent APIs differ. Mitigation: the helper produces a host-agnostic handoff that the main agent maps to available tools.
- HTML generation can be unavailable if `project_memory.py` is missing in adopted lightweight projects. Mitigation: include the command/path as a review requirement and let the command fail visibly.

## Next Command

`/product:execute 051-autonomous-execute-review-visual-handoff`
