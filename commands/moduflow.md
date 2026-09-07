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
   - `그래프`, `graph`, `의사결정 그래프` → `product:dashboard` (decision-graph dashboard; distinct from progress `workspace/dashboard.md`)
   - `검사`, `doctor` → `product:doctor`
   - `로드맵`, `roadmap` → `product:roadmap`
   - `003 시작`, `003 완료` → issue lifecycle action on issue `003`
   - anything else → pick the closest `product:*` command; if ambiguous, ask one concise clarification before mutating files.

   Preserve exact `product:*` commands and the aliases above as ModuFlow-owned lifecycle work.
   For any other natural-language request — `/moduflow 모두충전 대시보드 이슈 진행해줘` —
   run the whole pipeline, not one stage of it:

   ```bash
   python3 <bundled-moduflow-root>/scripts/request_routing.py "$ARGUMENTS" <registry-path>
   ```

   **This replaced a direct call to `capability_routing.py` on 2026-09-07, and the
   replacement is the point of issue 104.** That call was stage 3. Reaching it from here
   skipped stage 1 (which project?) and stage 2 (is there already an issue for this?), so
   the hub could route a specialist against an unresolved project. `resolve_project`
   already existed; nothing forced a caller through it first. Now the order is the
   module's, not the caller's.

   Read the result and act on `status`:

   - `ambiguous` — print `question`, exactly one, and **stop**. Nothing was written.
   - `refused` / `blocked` — print `next_command` and stop. `written` is `[]`; say so
     plainly rather than leaving the person to wonder what changed.
   - `ok` — `overlap_candidates` holds this project's open issues with the one line each
     says about who is blocked without it. **Read them and say which one this request
     belongs to**, or say it is new work. No score is provided and none should be
     invented: measured over 147 issues, no mechanical rule tells same work from
     different work, so this judgement is yours. Then re-run with
     `--chosen-issue <id>`.

   **Nothing is written without `--commit`.** A bare sentence is a question: it reports
   what it would do and changes nothing. Say what will happen, get a yes, then re-run
   with `--commit`. Do not add `--commit` on the first pass because the request sounded
   decisive.

   Resolve the script and registry from the installed/bundled ModuFlow package, not from
   the target project.

   Consume `moduflow.capability-routing.v1` as follows:

   - `none` → continue in ModuFlow and load no specialist.
   - `delegate` → load at most one specialist, and only when its availability is `available`
     and its permission state is `allowed`; otherwise show the returned fallback or approval need.
   - `sequence` → run only `current_stage`, save its declared output artifact, then re-route with
     that path as `--completed-artifact`. `sequence_state` is `ready`, `blocked`, or `complete`;
     never activate all stages together.
   - `clarify` → ask the returned single question and load no specialist.

   Every non-`none` handoff reports adapter ID, selection reason, permission, availability,
   issue ID, and output artifact. The helper is read-only routing metadata; it does not invoke,
   install, or mutate a specialist.

   For a sole current `spec-kit` stage, load `skills/spec-kit-validation-bridge/SKILL.md` only
   when availability is `available`, permission is `read`, and permission state is `allowed`.
   The bridge checks project opt-in, loads the safety overlay before exactly one approved
   template, and returns advisory output. On any non-ready handoff, show its native fallback and
   stop. Never persist automatically; only explicit ModuFlow approval may use the adapter's
   `--write` path.

3. Always end by showing the **next recommended action and command** so the user can chain without asking "what next?" or memorizing names. This is required after every completed action, including spec, plan, execute, review, release, or issue lifecycle updates. Exact `product:*` input is a power-user escape hatch and should be honored directly.
4. If a workflow resumes after a long task, context compaction, approval pause, or validation loop, show a short resume banner before continuing so the user can see that ModuFlow is continuing from durable state rather than restarting.

## Argument Resolution

`/moduflow <name>` runs that command. `/moduflow inbox` does what
`commands/product-inbox.md` says to do. The `product:` prefix is neither typed
nor shown.

Resolve the **first** argument in this order, and stop at the first hit:

1. **Exact** match on `commands/product-<arg>.md` → read that file and follow it,
   passing every remaining argument as its input.
2. **Exact** match on `commands/<arg>.md` → same.
3. No exact match → fall through to the natural-language routing in `## Do`
   step 2. Do not guess by prefix, substring, or edit distance.

Exact matching is what keeps `/moduflow issue` (create one) and
`/moduflow issues` (list them) apart. A prefix rule would collapse them.

**All 41 commands resolve this way, including the 29 that are hidden from the
menu.** Hiding a command from the `/` list must never make it unreachable —
`commands/product-<name>.md` is read the same way whether or not the entry is
listed. If a name resolves to no file, say so and show the nearest listed
command; never silently run something else.

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
처음 한 번
  /moduflow start        이 프로젝트에 모두플로를 설치합니다
  /moduflow goal         무엇을 이루려는지 한 줄로 정합니다
  /moduflow roadmap      지금·다음·나중에 할 일을 놓습니다

매일
  /moduflow status       어디까지 왔는지 대시보드로 봅니다
  /moduflow loop         다음 단계를 골라서 실행합니다
  /moduflow inbox        떠오른 것을 일단 적어 둡니다

이슈마다
  /moduflow issue        할 일 하나를 이슈로 만듭니다
  /moduflow release      출시 준비·배포·되돌리기

필요할 때
  /moduflow decision     정한 것을 이유와 함께 남깁니다
  /moduflow memory       다음에도 기억할 것을 저장합니다
  /moduflow doctor       설치와 파일이 온전한지 점검합니다

예시
  /moduflow inbox 로그인 화면이 느리다는 제보
  /moduflow decision build email login first

명세·계획·구현·검토는 /moduflow loop 가 알아서 넘깁니다.
목록에 없는 명령도 이름만 쓰면 실행됩니다 — /moduflow knowledge 처럼.
```

## Notes

- This hub does not replace the granular `product:*` commands; it routes to them.
- For full routing rules (Korean natural language, issue lifecycle), follow `skills/index/SKILL.md`.
