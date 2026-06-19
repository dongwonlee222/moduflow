---
description: ModuFlow entry point. Show status and next action, or route a natural-language request to the right product command.
argument-hint: "[action e.g. 시작 | 루프 | 상태 | 이슈 003 시작]"
---

# /moduflow

Single entry point for the ModuFlow plugin. The user only needs to remember `/moduflow` — this hub routes everything else.

Request: $ARGUMENTS

## Do

1. **No arguments** → act as concise `product:status`:
   - Read `.moduflow/state.json`, `workspace/loop-state.json`, `workspace/goal.md`, and `workspace/dashboard.md` when present.
   - If ModuFlow is **not initialized** in this project (no `.moduflow/`), say so and offer `/moduflow 시작` (`product:start`).
   - If initialized, report only current goal, active issue, phase, blocker, and next action.
   - Show the exact next command for power users.
   - Do not print the full command catalog unless the user asks for `help`, `도움말`, or `명령어`.

2. **With arguments** → route using the ModuFlow `index` skill rules (`skills/index/SKILL.md`). Resolve simple aliases before exposing workflow internals. Examples:
   - `시작`, `start` → `product:start`
   - `상태`, `status`, `현재 상황` → concise `product:status`
   - `다음`, `next`, `루프` → read-only `product:loop`
   - `다음 실행`, `한 단계 진행` → one safe `product:loop --step`
   - `이거 해줘: ...` → run intake routing semantics: active issue attach, new issue candidate, goal graph candidate, or inbox record
   - `완료`, `done` → guarded completion; verify before closing
   - `목표`, `goal` → `product:goal`
   - `이슈`, `issues` → `product:issues`
   - `검사`, `doctor` → `product:doctor`
   - `로드맵`, `roadmap` → `product:roadmap`
   - `003 시작`, `003 완료` → issue lifecycle action on issue `003`
   - anything else → pick the closest `product:*` command; if ambiguous, ask one concise clarification before mutating files.

3. Always end by showing the **next recommended action and command** so the user can chain without asking "what next?" or memorizing names. This is required after every completed action, including spec, plan, execute, review, release, or issue lifecycle updates. Exact `product:*` input is a power-user escape hatch and should be honored directly.
4. If a workflow resumes after a long task, context compaction, approval pause, or validation loop, show a short resume banner before continuing so the user can see that ModuFlow is continuing from durable state rather than restarting.

## Resume Banner

Use this before continuing resumed work:

```text
이어받음: <goal or issue id>
완료됨: <already completed items>
지금: <current action>
다음: <next handoff target>
```

Keep it compact and grounded in artifacts such as `workspace/loop-state.json`, `workspace/goal.md`, active issue tasks, and verification records. Do not expose internal context-compaction mechanics unless the user asks.

## Required Next Handoff Format

After completing work, use this Korean-first handoff shape:

```text
다음은 <next work>가 맞습니다.

이유:
- <reason 1>
- <reason 2>
- <reason 3>

다음 액션:
1. <concrete action 1>
2. <concrete action 2>
3. <concrete action 3>

그 뒤 우선순위:
- <issue/id>: <why it is next>
- <issue/id>: <why it follows>
- <issue/id>: <why it follows>

👉 바로 진행: 제가 <first action>부터 진행하면 됩니다.
```

Keep it concise. Include only sections that are useful, but do not replace this with a bare `Next Command` line after completed work. The final CTA line must be visually easy to scan; use `👉 바로 진행:` unless the host cannot render emoji.

## Quick command list

Show this only when the user asks `help`, `도움말`, `명령어`, or "what can I do":

```
설정/시작    /moduflow 시작        (product:start)   프로젝트 초기화
점검        /moduflow 검사        (product:doctor)  설치·아티팩트 검증
목표        /moduflow 목표        (product:goal)    목표 설정/조회
루프        /moduflow 루프        (product:loop)    다음 단계 자동 추천·실행
상태        /moduflow 상태        (product:status)  현재 진행 상태
이슈        /moduflow 이슈        (product:issues)  이슈 목록
로드맵      /moduflow 로드맵      (product:roadmap) Now/Next/Later

전체 35개 명령어는 /moduflow:product- 입력 시 자동완성으로 확인.
자연어도 가능: "모두플로우 시작", "루프 돌려줘", "003 완료 처리".
```

## Notes

- This hub does not replace the granular `product:*` commands; it routes to them.
- For full routing rules (Korean natural language, issue lifecycle), follow `skills/index/SKILL.md`.
