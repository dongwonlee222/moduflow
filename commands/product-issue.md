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
5. If GitHub CLI is available and requested, create or sync the GitHub issue.

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
