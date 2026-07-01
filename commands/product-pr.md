---
description: Prepare or refresh Draft PR / PR-ready review state for issue work.
argument-hint: "<issue id>"
---

# /product:pr

Prepare or refresh the pull request review surface.

## Do

1. Check branch, commits, changed files, tests, linked issue, and whether a Draft PR already exists.
2. Generate or refresh the PR handoff:

```bash
python3 scripts/project_pr.py <project-path> --issue-id <issue id> --write
```

3. Draft PR summary, test evidence, risk, screenshots, dashboard path, issue drill-down path, review findings, and rollout notes.
4. Save to `specs/<issue>/pr.md`.
5. Record PR state in team workflow:

```bash
python3 scripts/project_workflow.py <project-path> --pr-state --issue-id <issue id> --pr "<pr url or local pr-ready marker>" --reviewer "Reviewer"
```

6. Create a Draft PR early when requested, already part of the workflow, or GitHub sync mode explicitly allows GitHub writes. Otherwise use a local PR-ready marker.
7. Store GitHub PR URLs back into Git-native artifacts; if GitHub sync fails, keep local `git-files` state valid and report the mirror failure separately.
8. After `product:review`, refresh `specs/<issue>/pr.md` and mirror review/dashboard evidence into the GitHub PR body or a PR comment when possible.

## Human Gate

PR creation is not merge approval. Humans still review:

- GitHub PR diff and discussion.
- Dashboard and issue drill-down output.
- Required status checks and CI output.
- Merge readiness under branch protection rules.

## Next

- `/product:release` after PR is merged or approved
- `/product:review` if PR checks fail
