---
description: Prepare GitHub PR from completed issue/spec work.
argument-hint: "<issue id>"
---

# /product:pr

Prepare pull request.

## Do

1. Check branch, commits, changed files, tests, and linked issue.
2. Draft PR summary, test evidence, risk, screenshots, and rollout notes.
3. Save to `specs/<issue>/pr.md`.
4. Record PR state in team workflow:

```bash
python3 scripts/project_workflow.py <project-path> --pr-state --issue-id <issue id> --pr "<pr url or local pr-ready marker>" --reviewer "Reviewer"
```

5. Create PR with `gh` only when requested or already part of the workflow.
6. Store GitHub PR URLs back into Git-native artifacts; if GitHub sync fails, keep local `git-files` state valid and report the mirror failure separately.

## Next

- `/product:release` after PR is merged or approved
- `/product:review` if PR checks fail
