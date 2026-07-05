---
description: Create or update a Git-native issue artifact.
argument-hint: "<opportunity id or issue title>"
---

# /product:issue

Create the durable work item.

## Do

1. Check existing issues for overlap before creating a new issue.
2. Create or update `issues/<id>-<slug>.md`.
3. Include lifecycle metadata: phase, created, started, target end, completed, and last updated.
4. Link opportunity, owner, scope, priority, acceptance criteria, related issues, sessions, and related artifacts.
5. Add a **Workflow Tasks** checklist. Every artifact-producing step (spec, plan, design, execute, review) is a tracked task with its artifact link and status — never produce an artifact off the books. As each step runs, check its box and link the artifact. This keeps the workflow itself visible inside the issue.
6. If GitHub CLI is available and requested, create or sync the GitHub issue (see GitHub Issue Sync below).

## GitHub Issue Sync (opt-in)

Project a git-file issue to a GitHub Issue only when the user explicitly asks — never automatically. Skips itself when `.moduflow/config.json`'s `git.github_sync` is `"off"`.

```bash
python3 scripts/project_github_issues.py . --issue-id <id> --sync
```

- First sync creates the GitHub Issue (title from the issue heading, body from `## Outcome`, label `moduflow:<status>`) and writes `- GitHub: <url>` into the issue file's `## Links` section.
- Later syncs reuse that link and refresh the status label on the existing GitHub Issue — no duplicates.
- Missing `moduflow:backlog|active|done|superseded` labels are created in the repo before use.
- One-way only: `issues/<id>.md` stays canonical; the GitHub Issue is a projection. GitHub-side edits never flow back.

## Granularity Rule

One issue = one deliverable with its own lifecycle. The workflow steps that produce planning artifacts (spec, plan, design) are **tasks inside that issue**, not separate top-level issues — this avoids infinite regress (a "write the spec" issue would itself need a spec). The artifact is always tracked; only the unit is the issue's task list. Split into a new issue only when a step grows into its own deliverable.

## Lifecycle Actions

Support short commands and Korean natural-language equivalents:

- `issue <id> start`, `<id> 시작해줘`: set phase, started date, active issue, dashboard, and issue index.
- `issue <id> update "..."`, `<id>에 진행 내용 추가`: append progress to the issue or current session log.
- `issue <id> pause`, `<id> 멈춰줘`: summarize current progress and next action.
- `issue <id> resume`, `<id> 다시 시작해줘`: make it active and show recent context.
- `issue <id> complete`, `<id> 완료 처리해줘`: set completed date, phase, dashboard, roadmap, and issue index.

## Related Issue Check

Before creating a new issue, scan `issues/*.md` and `workspace/issues.md` when present. If the request overlaps an existing issue, recommend one of:

- update existing issue
- create a follow-up issue
- link as related
- mark as duplicate

## Session Convention

Use `sessions/<issue-slug>/<date>-<agent-or-purpose>.md` for repeated work logs when detailed context should be preserved.

## Next

- `/product:spec` for new product work
- `/product:plan` for small obvious work
- `/product:roadmap` when priority changed
