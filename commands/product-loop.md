---
description: Read goal and issue state, then recommend or run the next safe ModuFlow step.
argument-hint: "[--step|--until blocked]"
---

# /product:loop

Advance a goal by routing through existing ModuFlow commands.

## Do

1. Read `workspace/goal.md` and `workspace/loop-state.json` when present.
2. Inspect the linked issue, spec, plan, tasks, status, release, and update artifacts.
3. Recommend the next existing ModuFlow command.
4. Write state only when the user asks for mutation or when running `--step`.
5. Stop as soon as the goal is `done`, `blocked`, or `needs_decision`.
6. After any completed ModuFlow action, use the latest goal/loop state to produce the structured next handoff. Do this proactively; the user should not need to ask "다음은 뭐야?"
7. If the loop resumes after a pause, context compaction, approval prompt, or repeated validation pass, show the resume banner before recommending or running the next step.

## Resume Mode

Use this at the top of a resumed loop response:

```text
이어받음: <goal or issue id>
완료됨: <completed phases or artifacts>
지금: <current loop action>
다음: <next handoff target>
```

The banner should come from durable project state, not memory alone:

- `workspace/goal.md`
- `workspace/loop-state.json`
- active issue workflow tasks
- `specs/<issue>/status.md`
- latest verification records

Keep the banner short. It is a continuity marker, not a full status report.

## Recommendation Mode

Aliases: `다음`, `next`, `루프`.

Default `product:loop` is read-first and recommendation-oriented. It recommends one safe next action and includes the exact command. It does not mutate files unless the user explicitly asks for execution.

Expected output:

```text
다음은 <next work>가 맞습니다.

이유:
- <goal/loop state reason>
- <active issue phase reason>
- <verification/blocker reason>

다음 액션:
1. <concrete next step>
2. <state/artifact update if needed>
3. <verification or review step if needed>

그 뒤 우선순위:
- <next issue or track>: <why it follows>
- <next issue or track>: <why it follows>

바로 가려면 제가 <first action>부터 진행하면 됩니다.
```

## One-Step Mode

Aliases: `다음 실행`, `한 단계 진행`, `product:loop --step`.

`product:loop --step` may run at most one safe next action and then stop. One-step mode can mutate one safe artifact or state update, then must report what changed and the next command.

Safe one-step actions include:

- creating or updating goal, issue, spec, plan, tasks, status, reflection, dashboard, issue index, and roadmap artifacts
- running local validation commands
- recommending review, release, PR, or update commands

Unsafe actions require explicit user approval:

- package publishing
- GitHub writes
- cross-repo mutation
- destructive file or Git operations
- long-running unattended execution

## Stop States

- `done`: completion criteria are satisfied and verification is recorded; say what finished and recommend status or the next issue.
- `blocked`: the next action cannot proceed without external change; say the blocker and the smallest unblock request.
- `needs_decision`: a human decision is required before mutation; explain the repeated action or ambiguity and ask one concise question.
- `active`: safe to continue with the recommended next command.

## Completion Handoff

Every command that completes work should call back into this loop contract mentally or mechanically before answering the user. The final response should be based on:

- `workspace/goal.md`: objective and completion criteria
- `workspace/loop-state.json`: active issue, phase, status, blocker, and next command
- active issue workflow tasks: what is complete and what remains
- verification result: what passed, failed, or was not run

Default handoff is not a raw `Next Command` line. It must explain why the next action is next, list concrete next actions, and show follow-on priority when the goal has a queue. End with a visually obvious CTA such as `👉 바로 진행: 제가 <first action>부터 진행하면 됩니다.`

## State Updates

When mutating, update `workspace/loop-state.json` with:

- current goal
- linked issue
- phase
- mode
- next command
- attempts
- status
- blocker
- last action
- last verification
- git binding
- updated timestamp

Minimum loop-state v2 fields:

- `goal_id`: durable goal identifier
- `issue_ids`: ordered issue graph for the active goal
- `active_issue_id`: one issue cursor
- `phase`: current workflow phase inferred from artifacts
- `next_command`: next safe ModuFlow command
- `attempts.command/count/max`: repeated-step guard
- `status`: `active`, `needs_decision`, `blocked`, or `done`
- `git_binding.branch`: issue-bound branch name when execution has a branch
- `git_binding.execution_backend`: selected or recommended execution backend

`이거 해줘: <request>` should use `scripts/project_intake.py` semantics before creating work: classify the request, check related issues, attach to the active issue when it matches, generate issue candidates for new work, or append an inbox record when `--write` is requested.

The intake result may recommend three shaping paths:

- `create_issue` / `fast`: create the issue now; clear requests do not need an interview.
- `shape_then_issue` / `short`: ask 1-3 user-facing questions before issue/spec/goal creation.
- `panel_shape` / `panel`: use compressed multi-perspective product shaping through `/product:opportunity`; show only the final questions, not raw panel notes.

Simple user aliases should route here: `상태`, `다음`, `이거 해줘`, `완료`.

Record repeated failures or uncertainty in `specs/<issue>/reflection.md`.

## Implementation Readiness Routing

When the active issue is in `execute` phase and
`specs/<issue>/implementation-readiness.json` exists with
`"status": "not_ready"`, route back to:

```bash
product:plan <issue>
```

Report the blocker plainly: implementation readiness is not ready, and v1 is
report-only. The user can still explicitly approve execution, but the default
loop recommendation should repair the plan first.

## Next

- `/product:status` to inspect the current state
- `/product:review` after implementation steps complete
