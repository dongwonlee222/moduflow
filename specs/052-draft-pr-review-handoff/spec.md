# Spec: Draft PR Review Handoff

Issue: `052-draft-pr-review-handoff`
Next: `product:status`

## Problem

ModuFlow's improved review flow still waits too long to create the GitHub-visible review surface. Humans should not have to choose between a local dashboard and a late PR; the PR should become the collaboration surface early, while the dashboard and issue drill-down remain the visual inspection surface.

## Users

- Dongwon Lee, who wants to see where human confirmation happens in the full flow.
- Coding agents using ModuFlow, which need an explicit contract for when PR state is created, refreshed, and handed to humans.

## Goals

- Treat Draft PR / PR-ready state as an early review surface.
- Keep merge and release authority human-gated.
- Mirror review, verification, dashboard, and issue drill-down evidence into `pr.md` and, when available, GitHub PR body/comments.
- Preserve local `git-files` mode when GitHub write access is unavailable.

## Non-Goals

- No automatic merge.
- No forced remote PR creation.
- No branch protection setup automation.
- No replacement for GitHub's own review and status check UI.

## Requirements

1. Add `scripts/project_pr.py`.
2. The helper writes `specs/<issue>/pr.md`.
3. The PR handoff includes:
   - branch
   - Draft PR URL or local PR-ready marker
   - reviewer
   - `product:review <issue>` and `product:pr <issue>` commands
   - dashboard and issue drill-down paths
   - PR body contract
   - human approval checkpoints
   - GitHub gate alignment
4. `product:execute` explains early Draft PR / PR-ready timing.
5. `product:review` refreshes `pr.md` after verification and dashboard generation.
6. `product:pr` becomes a prepare-or-refresh command, not only a late final step.

## Acceptance Criteria

- Tests generate a PR handoff in a temp project without network access.
- The handoff names Draft PR, branch, PR marker, reviewer, dashboard, issue drill-down, required status checks, and human approval.
- Release checks include the new PR handoff tests.

## Risks

- Early PR can look like premature completion. Mitigation: generated handoff states that PR creation is not merge approval.
- GitHub sync can fail in local or sandboxed hosts. Mitigation: use local PR-ready markers and report mirror failures separately.

## Next Command

`/product:status`
