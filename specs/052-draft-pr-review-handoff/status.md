# Status: Draft PR Review Handoff

Issue: `052-draft-pr-review-handoff`

## State

- Created: 2026-07-01
- Phase: done
- Owner: Codex

## Done

- Issue created.
- Spec created.
- Plan created.
- `tests/test_project_pr.py` added for PR handoff behavior.
- `scripts/project_pr.py` added with `--issue-id <issue> --write`.
- `commands/product-execute.md` updated to recommend early Draft PR / PR-ready state.
- `commands/product-review.md` updated so review refreshes PR evidence after dashboard generation.
- `commands/product-pr.md` updated to prepare or refresh the PR surface.
- `specs/052-draft-pr-review-handoff/pr.md` generated.
- Dashboard and issue drill-down generated as derived views.
- PM/spec subagent review completed and findings incorporated.
- QA/release subagent review completed and findings incorporated.

## Pending

- None.

## Next Command

`product:status`

## Verification

- `python3 -m unittest tests.test_project_pr -v` passed.
- `python3 scripts/project_pr.py . --issue-id 052-draft-pr-review-handoff --write` generated `specs/052-draft-pr-review-handoff/pr.md`.
- `python3 scripts/project_memory.py . --dashboard` generated `memory/dashboard.html`.
- `python3 scripts/project_memory.py . --issue 052-draft-pr-review-handoff` generated `memory/issue-052-draft-pr-review-handoff.html`.
- `python3 scripts/project_lifecycle.py . --drift` returned `[]`.
- `python3 scripts/release_check.py .` passed.
