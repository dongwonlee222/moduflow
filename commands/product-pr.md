---
description: Prepare or refresh Draft PR / PR-ready review state for issue work.
argument-hint: "<issue id>"
---

# /product:pr

Prepare or refresh the pull request review surface.

## Do

1. Check branch, commits, changed files, tests, linked issue, and whether a Draft PR already exists.
2. Before any local `git add`/`commit`/`push`, run the commit capability preflight:

```bash
python3 scripts/project_git_handoff.py <project-path>
```

- `mode: local-git-write` — proceed with normal local Git commands.
- `mode: github-api-commit` — local `.git` writes are blocked (e.g. `index.lock` cannot be created); use the GitHub API (`gh api`, or an MCP GitHub tool) to create/update the branch and commit files instead of local git commands. Do not ask the user to run terminal Git commands for this — the API path replaces that step.
- `mode: blocked` — neither path is available; only then ask the user to run the needed Git commands manually, citing `reason`.

Record the chosen `mode`, `reason`, branch, base ref, commit URL/SHA, and file count in `specs/<issue>/pr.md` whenever the mode is not `local-git-write`, so PR/release artifacts can cite how the commit was made.

3. Before any `gh pr create`, run GitHub PR preflight:

```bash
python3 scripts/project_pr.py <project-path> --github-preflight
```

If `ok` is false or `mode` is `local-pr-ready`, do not run `gh pr create` in this environment. Record a local PR-ready marker and include the preflight error in `specs/<issue>/status.md` or `specs/<issue>/pr.md`.

4. Generate or refresh the PR handoff:

```bash
python3 scripts/project_pr.py <project-path> --issue-id <issue id> --write
```

5. Draft PR summary, test evidence, risk, screenshots, dashboard path, issue drill-down path, review findings, and rollout notes.
6. Save to `specs/<issue>/pr.md` and `specs/<issue>/human-review.ko.md`.
7. Record PR state in team workflow:

```bash
python3 scripts/project_workflow.py <project-path> --pr-state --issue-id <issue id> --pr "<pr url or local pr-ready marker>" --reviewer "Reviewer"
```

8. Create a Draft PR early only when preflight passes and GitHub sync mode explicitly allows GitHub writes. Otherwise use a local PR-ready marker.
9. Store GitHub PR URLs back into Git-native artifacts; if GitHub sync fails, keep local `git-files` state valid and report the mirror failure separately.
10. After `product:review`, refresh `specs/<issue>/pr.md` and mirror review/dashboard evidence into the GitHub PR body or a PR comment when possible.

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
