---
description: Create or update the active goal that supervises one or more Git-native issues.
argument-hint: "<objective or issue id>"
---

# /product:goal

Create or update a durable goal.

## Do

1. Identify the target project root and current Git state before writing.
2. Check whether the objective already maps to an existing issue.
3. Create or update `workspace/goal.md`.
4. Create a backing issue when no linked issue exists, unless the user explicitly wants goal-only tracking.
5. Update `workspace/loop-state.json` with active goal, linked issue, status, and next command.
6. Keep the goal above issues. Do not replace issue, spec, plan, status, release, or update artifacts.

## Goal Fields

- objective
- owner
- linked issue
- completion criteria
- constraints
- budget
- status: `active`, `done`, `blocked`, or `needs_decision`
- blocker
- next command
- updated

## Output

Return a concise goal summary:

```text
Goal: <objective>
Linked issue: <issue id or none>
Status: active
Next command: product:loop
```

## Safety

- Do not mutate unrelated project repositories.
- Do not create duplicate issues when an existing issue matches the objective.
- Ask one concise clarification if the objective, owner, or linked issue is ambiguous.

## Next

- `/product:loop` to choose the next workflow step
- `/product:issue` if the goal needs a new durable work item
