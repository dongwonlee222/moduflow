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

3. Preserve existing workflow files.

## Next

- `/product:review` to verify readiness
- `/product:risks` to inspect active risk
