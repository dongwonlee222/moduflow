---
description: Prepare or refresh Draft PR / PR-ready review state for issue work.
argument-hint: "<issue id>"
---

# /product:pr

Prepare or refresh the pull request review surface.

## Do

1. Check branch, commits, changed files, tests, linked issue, and whether a Draft PR already exists.
2. Before any `gh pr create`, run GitHub PR preflight:

```bash
python3 scripts/project_pr.py <project-path> --github-preflight
```

If `ok` is false or `mode` is `local-pr-ready`, do not run `gh pr create` in this environment. Record a local PR-ready marker and include the preflight error in `specs/<issue>/status.md` or `specs/<issue>/pr.md`.

3. Generate or refresh the PR handoff:

```bash
python3 scripts/project_pr.py <project-path> --issue-id <issue id> --write
```

4. Draft PR summary, test evidence, risk, screenshots, dashboard path, issue drill-down path, review findings, and rollout notes.
5. Save to `specs/<issue>/pr.md` and `specs/<issue>/human-review.ko.md`.
6. Record PR state in team workflow:

```bash
python3 scripts/project_workflow.py <project-path> --pr-state --issue-id <issue id> --pr "<pr url or local pr-ready marker>" --reviewer "Reviewer"
```

7. Create a Draft PR early only when preflight passes and GitHub sync mode explicitly allows GitHub writes. Otherwise use a local PR-ready marker.
8. Store GitHub PR URLs back into Git-native artifacts; if GitHub sync fails, keep local `git-files` state valid and report the mirror failure separately.
9. After `product:review`, refresh `specs/<issue>/pr.md` and mirror review/dashboard evidence into the GitHub PR body or a PR comment when possible.

## Human Gate

PR creation is not merge approval. Humans still review:

- Korean human-review packet: `specs/<issue>/human-review.ko.md`.
- GitHub PR diff and discussion.
- Dashboard and issue drill-down output.
- Required status checks and CI output.
- Merge readiness under branch protection rules.

Start Korean review from `human-review.ko.md`, then open the dashboard issue detail and PR diff only as needed. English artifacts remain canonical, but a PR should not ask a Korean reviewer to approve from English-only context.

## Next

- `/product:release` after PR is merged or approved
- `/product:review` if PR checks fail
