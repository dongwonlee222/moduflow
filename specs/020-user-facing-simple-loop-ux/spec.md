# Spec 020: User-Facing Simple Loop UX

## Problem

ModuFlow now has a durable loop kernel, but the installed plugin surface still exposes too many internal nouns: goal, issue, spec, plan, workers, review, release, and doctor. A user should be able to make progress with a few natural phrases while ModuFlow handles the internal routing and artifact model.

## Goal

Make the default ModuFlow experience feel like a small PM assistant. The user can say `상태`, `다음`, `이거 해줘: ...`, or `완료`; ModuFlow maps that intent to the existing goal loop, issue/spec/plan workflow, and verification gates without hiding power-user `product:*` commands.

## Non-Goals

- Replacing existing `product:*` commands.
- Building a new web dashboard or visual UI.
- Full loose-request graph creation. Rich intake and splitting belongs to `022-intake-to-goal-graph`.
- Git branch, commit, PR, or external execution backend automation. That belongs to `021-git-binding-and-execution-backend`.
- Worker routing or worktree isolation changes. That belongs to `023-worker-routing-and-isolation`.

## User Command Surface

Default aliases should be short and Korean-first, with English equivalents where useful.

| User phrase | Intent | Internal route |
| --- | --- | --- |
| `상태`, `status` | Show current goal, active issue, phase, blocker, next action | `product:status` with concise mode |
| `다음`, `next`, `루프` | Recommend one safe next step | `product:loop` recommend mode |
| `다음 실행`, `한 단계 진행` | Run at most one safe step when mutation is allowed | `product:loop --step` |
| `이거 해줘: <request>` | Attach request to the active loop or create safe intake | route to `product:issue`, `product:spec`, or `product:inbox` depending on confidence |
| `완료`, `done` | Close current step only when required artifact and verification are present | phase-aware review/release/status update |
| `검사`, `doctor` | Validate setup and drift | `product:doctor` |

Advanced direct commands stay available and should appear only when the user asks for details or when ModuFlow recommends the next exact command.

## Response Design

### `상태`

Default status should fit in a short chat response:

```text
현재 목표: <goal>
현재 이슈: <issue> (<phase>)
다음: <plain-language next action>
명령: <product:* command>
막힘: 없음 | <blocker>
```

Avoid listing every artifact unless the user asks for detail. Mention verification only if it affects the next action.

### `다음`

`다음` should not expose the full phase ladder. It should return:

- the recommended next action in plain language
- the exact command for power users
- a one-sentence reason
- whether it is read-only, safe mutation, or needs approval

### `이거 해줘`

Routing rules:

1. If there is an active goal and active issue, prefer attaching the request to that loop when it is clearly related.
2. If the request is a new deliverable, create or recommend a new issue linked to the active goal.
3. If confidence is low, ask one concise clarification or create an inbox item rather than forcing the user to choose between ModuFlow internals.
4. Never create spec/plan/review artifacts without updating the issue Workflow Tasks checklist.

### `완료`

Completion should be guarded:

- If the current phase has required artifacts missing, explain the missing artifact and recommend the next command.
- If verification is missing, recommend the verification/review command.
- If all gates pass, mark the current step or issue complete and advance the active issue cursor.

## Routing Rules

- Natural aliases are resolved before command routing.
- Read-only aliases (`상태`, `다음`) should not mutate files unless explicitly asked.
- Mutation aliases (`이거 해줘`, `완료`, `다음 실행`) may update files only after choosing one safe action.
- Ambiguity gets at most one concise question. If a safe default exists, choose it and explain briefly.
- Every response ends with the next recommended command or a clear stop state.

## Files To Change

Expected implementation touchpoints:

- `commands/moduflow.md`: make the hub default to the simple command surface.
- `commands/product-status.md`: add concise default status output.
- `commands/product-loop.md`: clarify `다음` and `다음 실행` behavior.
- `skills/index/SKILL.md`: add natural-language routing behavior for the four default phrases.
- `skills/pm-execution-router/SKILL.md`: keep direct `product:*` routes but prefer simple aliases when the user intent is broad.
- Tests or validation fixtures for alias routing examples and output contract, if the implementation introduces script-level behavior.

## Acceptance Criteria

- `@ModuFlow 상태` returns a concise status view without requiring the user to understand internal artifact names.
- `@ModuFlow 다음` recommends one safe next action from the active loop and includes the exact command.
- `@ModuFlow 이거 해줘: ...` routes to the active loop, a new issue, or inbox with at most one clarification.
- `@ModuFlow 완료` does not close work unless the needed artifact and verification gates are satisfied.
- Existing advanced commands like `@ModuFlow product:spec 020-user-facing-simple-loop-ux` still work.
- Documentation and routing rules avoid exposing goal/issue/spec/plan internals unless useful.

## Risks

- Over-automation may mutate files when the user expected advice only. Mitigation: keep `상태` and `다음` read-only by default.
- Alias routing may hide useful precision from power users. Mitigation: always include the exact command in recommendations.
- `이거 해줘` may become a duplicate intake path. Mitigation: scan existing active goal/issue context before creating anything.

## Open Questions

- Should `다음` ever mutate by default, or should mutation require `다음 실행` / `product:loop --step`?
- Should `완료` close only the current workflow step first, or can it advance the active issue cursor when all gates pass?
- How much of the concise status contract should be enforced by tests versus command documentation in this plugin-only phase?

## Next Command

`product:plan 020-user-facing-simple-loop-ux`
