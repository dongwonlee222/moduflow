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
4. Create PR with `gh` only when requested or already part of the workflow.

## Next

- `/product:release` after PR is merged or approved
- `/product:review` if PR checks fail

