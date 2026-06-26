---
description: Initialize team workflow artifacts or create handoff-ready workflow records.
argument-hint: "[project path] [--write|--record]"
---

# /product:handoff

Create or inspect team workflow handoff artifacts.

## Do

1. Initialize workflow files:

```bash
python3 scripts/project_workflow.py <project-path> --write
```

2. Create a workflow record:

```bash
python3 scripts/project_workflow.py <project-path> --record --issue-id 005-team-workflow --state ready-for-review --owner "Owner" --reviewers "QA,PM" --approver "Approver" --blocker "none" --next-command "product:review 005-team-workflow"
```

3. Start assigned issue work in team mode:

```bash
python3 scripts/project_workflow.py <project-path> --start --issue-id 035-team-issue-branch-pr-workflow --owner "PM" --assignee "Developer" --reviewer "Reviewer"
```

4. Render team status for PMs:

```bash
python3 scripts/project_workflow.py <project-path> --team-status
```

5. Preserve existing workflow files.

## Korean Team Flow

- "새 이슈 만들고 민수에게 맡겨줘" -> create/update issue, set owner/assignee/reviewer, then show team status.
- "035 시작해줘" -> record active assignee, lock state, and recommended `codex/<issue-id>` branch.
- "팀 상태 보여줘" -> render active, review, blocked, ready, and done work from `workflow/team-state.json`.
- "완료 처리해줘" -> run completion gates, then suggest Issue 034 memory candidates for durable decisions and lessons.

## Next

- `/product:review` to verify readiness
- `/product:risks` to inspect active risk
