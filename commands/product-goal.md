---
description: 지금 무엇을 이루려는지 한 줄로 정합니다. 이슈들이 여기에 매달립니다. (set the goal)
argument-hint: "<objective or issue id>"
---


# /product:goal

Create or update a durable goal.

## 사용 예시

```
/moduflow goal 결제 실패율을 1% 아래로 내린다
/moduflow goal cut the payment failure rate below 1%
```

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
Next command: `/moduflow loop`
```

## Safety

- Do not mutate unrelated project repositories.
- Do not create duplicate issues when an existing issue matches the objective.
- Ask one concise clarification if the objective, owner, or linked issue is ambiguous.

## Next

- `/moduflow loop` to choose the next workflow step
- `/moduflow issue` if the goal needs a new durable work item
