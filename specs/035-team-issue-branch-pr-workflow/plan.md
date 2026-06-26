# Plan: Team Issue Branch PR Workflow

## Issue

`035-team-issue-branch-pr-workflow`

## Status

Implemented and reviewed.

## Existing Fit

- `scripts/project_workflow.py` already initializes workflow files and writes handoff records.
- `scripts/project_loop.py` already recommends issue branches and validates branch-to-issue drift.
- `scripts/project_memory.py` now supports reviewable memory candidates.
- `commands/product-handoff.md`, `commands/product-pr.md`, and `commands/product-status.md` are the right PM-facing command docs to extend.

## Milestones

- [x] Add a `TeamWorkItem` parser/renderer in `scripts/project_workflow.py` for issue ownership, assignee, reviewer, status, branch, PR, blocker, and last handoff.
- [x] Add `start_issue_work(...)` helper that binds an issue to a deterministic branch name and records active ownership without creating GitHub dependencies.
- [x] Add `record_pr_state(...)` helper that stores PR-ready or external PR URL state in Git-visible workflow records.
- [x] Add `render_team_status(...)` helper that groups work into assigned, active, blocked, review, and done queues for PMs.
- [x] Add `suggest_completion_memory(...)` helper that returns Issue 034-compatible memory candidate inputs after completion.
- [x] Extend `scripts/validate_project_artifacts.py` to report team workflow drift: active issue without branch, review state without PR/reviewer, done state without review evidence, or stale active lock markers.
- [x] Update `commands/product-handoff.md`, `commands/product-pr.md`, and `commands/product-status.md` with the team flow and Korean natural-language examples.
- [x] Add tests in `tests/test_project_workflow.py`, `tests/test_project_loop.py`, and `tests/test_validation_distribution.py`.

## Test Plan

- `python3 -m unittest tests.test_project_workflow -v`
- `python3 -m unittest tests.test_project_loop -v`
- `python3 -m unittest tests.test_validation_distribution -v`
- `python3 -m unittest discover -s tests -v`
- `python3 scripts/validate_project_artifacts.py .`
- `python3 scripts/validate_moduflow.py .`

## File Plan

- `scripts/project_workflow.py`: team work item model, start/PR/status/memory helpers, CLI flags.
- `scripts/project_loop.py`: reuse branch naming and add any missing status helpers only if needed.
- `scripts/validate_project_artifacts.py`: drift validation.
- `commands/product-handoff.md`: team assignment/start/handoff UX.
- `commands/product-pr.md`: PR binding UX.
- `commands/product-status.md`: team status summary guidance.
- `tests/test_project_workflow.py`: main behavior tests.
- `tests/test_validation_distribution.py`: validation drift tests.
- `templates/workflow/*.md`: only if team status needs template updates.

## Next Command

`/product:release 035-team-issue-branch-pr-workflow`
