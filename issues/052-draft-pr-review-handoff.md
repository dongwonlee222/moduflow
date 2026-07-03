# Issue: `052-draft-pr-review-handoff`

**Status: done** — created 2026-07-01, started 2026-07-01, done 2026-07-01.

## Outcome

ModuFlow moves the human review surface earlier: a Draft PR or local PR-ready marker is created before review finishes, and review, verification, dashboard, and issue drill-down evidence are attached to the PR handoff.

## Why

Issue 051 fixed the broken `execute -> review -> dashboard` flow, but the PR still appeared too late. GitHub-native workflows usually make the PR the collaboration surface: humans review the diff, CI/status checks run on the branch, and merge remains gated by approval. ModuFlow should align with that pattern without forcing automatic merge or GitHub writes.

## Scope

### In

- Add a PR handoff helper that writes `specs/<issue>/pr.md`.
- Make `product:pr` support early Draft PR / local PR-ready state.
- Make `product:review` refresh PR evidence after subagent review and dashboard generation.
- Make `product:execute` recommend early Draft PR or PR-ready state after meaningful work starts.
- Add tests proving the PR handoff contains review, dashboard, and human gate evidence.

### Out

- No automatic merge.
- No forced GitHub PR creation when GitHub sync is unavailable or not approved.
- No branch protection configuration automation.

## Acceptance Criteria

- `scripts/project_pr.py --issue-id 052-draft-pr-review-handoff --write` writes `specs/052-draft-pr-review-handoff/pr.md`.
- The PR handoff includes Draft PR timing, branch, PR marker/URL, reviewer, review command, dashboard path, issue drill-down path, required status checks, and human approval checkpoints.
- `product:execute`, `product:review`, and `product:pr` describe when PR state is created and refreshed.
- `python3 -m unittest tests.test_project_pr -v` passes.
- `python3 scripts/release_check.py .` passes.

## Workflow Tasks

- [x] spec -> `specs/052-draft-pr-review-handoff/spec.md`
- [x] plan -> `specs/052-draft-pr-review-handoff/plan.md`
- [x] execute -> `scripts/project_pr.py`, command docs, tests
- [x] review -> `specs/052-draft-pr-review-handoff/review.md`
- [x] PR handoff -> `specs/052-draft-pr-review-handoff/pr.md`
- [x] dashboard verification -> `memory/dashboard.html`, `memory/issue-052-draft-pr-review-handoff.html`

## Related Issues

- follows_up: `051-autonomous-execute-review-visual-handoff`
- related: `035-team-issue-branch-pr-workflow`, `039-automated-review-checklists-and-safety-lint-gates`

## Sessions

- 2026-07-01: User asked where PR appears in the end-to-end ModuFlow flow and approved moving toward a GitHub-style Draft PR-centered review model.

## Links

- Spec: `specs/052-draft-pr-review-handoff/spec.md`
- Status: `specs/052-draft-pr-review-handoff/status.md`
- PR Handoff: `specs/052-draft-pr-review-handoff/pr.md`
- Roadmap: `workspace/roadmap.md`

## Next Command

`/product:status`
