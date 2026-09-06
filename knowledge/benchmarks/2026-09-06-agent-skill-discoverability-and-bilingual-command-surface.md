---
kind: benchmark
title: Agent skill discoverability and bilingual command surface
date: 2026-09-06
confidence: high for inspected public skill patterns and ModuFlow 0.3.67 package inventory
decision_supported: Reduce the visible ModuFlow command and skill surface while keeping natural-language routing and internal capabilities
sources:
  - https://github.com/anthropics/skills
  - https://code.claude.com/docs/en/slash-commands
  - https://github.com/openai/skills/blob/main/skills/.system/skill-creator/SKILL.md
  - https://github.com/openai/plugins
  - https://github.com/obra/superpowers
  - https://github.com/basicmachines-co/basic-memory/blob/main/plugins/codex/skills/bm-remember/SKILL.md
  - https://github.com/basicmachines-co/basic-memory/blob/main/plugins/codex/README.md
---

# Agent skill discoverability and bilingual command surface

## Why This Benchmark Exists

ModuFlow 0.3.67 exposes 41 source commands, 11 top-level skills and 27 Codex
`source-command-product-*` projections. The user can already open the `/` palette,
but its descriptions are English and internal workflow concepts appear beside
ordinary product actions. The practical problem is not whether slash commands
work; it is whether a user can recognize the right action without memorizing
ModuFlow's internal architecture. Korean and English requests must be equivalent;
Korean is not a replacement for English support.

The user explicitly rejected documented abbreviations such as `/product:d` and
`/product:rev`: they save keystrokes but create another vocabulary to memorize.

## Benchmarked Patterns

| Reference | Observed pattern | ModuFlow implication |
|---|---|---|
| Anthropic Skills | A skill description states what it does and when to use it; examples live with the skill | Put one plain Korean sentence and a realistic Korean example on each user-facing action |
| Claude Code skills | `user-invocable: false` separates background knowledge from the `/` menu | Hide bridges, policies and internal reference skills instead of teaching them to users |
| OpenAI skill guidance | Prefer short action-oriented names, discriminating descriptions and progressive disclosure; UI metadata can be separate from the skill body | Keep human-facing Korean labels/examples separate from model-routing descriptions and detailed procedures |
| Superpowers | Skills are named for lifecycle actions such as planning, debugging and review, not for the architecture that implements them | Expose actions and outcomes; keep orchestration mechanics internal |
| Basic Memory | Lightweight `remember` is separate from a durable `decide` record and a resumable checkpoint; user wording is preserved for quick capture | Route “메모해줘”, “기억해줘”, “정했어” and “찾아줘” to different internal record kinds without making the user choose a folder |

## Product Decision Recommended by the Benchmark

### One remembered entry point

The primary interaction is one command followed by ordinary Korean or English.
Each pair below must route to the same behavior:

```text
/moduflow 메모해줘: 가입 화면이 복잡하다는 고객 의견
/moduflow note this: customers say the signup screen is too complex
/moduflow 이걸 할 일로 만들어줘: 로그인 오류 수정
/moduflow create an issue: fix the login error
/moduflow 결정으로 남겨줘: 로그인은 이메일부터
/moduflow record this decision: build email login first
/moduflow Beads와 Linear를 비교해줘
/moduflow compare Beads and Linear for our use case
/moduflow 기억해줘: 고객 인터뷰는 매주 화요일
/moduflow remember: customer interviews happen every Tuesday
/moduflow 전에 로그인 방식 뭐로 정했지?
/moduflow find what we decided about the login method
/moduflow 지금 상황 보여줘
/moduflow show status
/moduflow 다음에 뭐 하면 돼?
/moduflow what should I do next?
/moduflow 승인한 계획 진행해줘
/moduflow execute the approved plan
/moduflow 완료 조건을 확인해줘
/moduflow review the acceptance criteria
/moduflow 출시 가능한지 확인해줘
/moduflow check whether this is ready to release
```

Do not document shorthand such as `/product:d`, `/product:m` or `/product:rev`.
Autocomplete is a discovery aid, not a second command language.

### Small visible shortcut set

Keep these full commands visible for users who prefer the palette. The user does
not need to memorize them because the Korean description and example explain the
choice.

| Command | Bilingual menu copy | Example intents |
|---|---|---|
| `/moduflow` | `[도움/Help] 하고 싶은 일을 말하면 알맞은 기능을 찾아줍니다` | `다음에 뭐 하면 돼?` / `what should I do next?` |
| `/product:inbox` | `[메모/Note] 아직 정리되지 않은 생각·요청·버그를 저장합니다` | `이 의견 메모해줘` / `note this feedback` |
| `/product:issue` | `[할 일/Issue] 해야 할 일을 실행 가능한 작업으로 만듭니다` | `이슈로 만들어줘` / `create an issue` |
| `/product:decision` | `[선택/Decision] 이미 정한 내용을 나중에도 알 수 있게 남깁니다` | `결정으로 남겨줘` / `record this decision` |
| `/product:benchmark` | `[비교/Compare] 다른 제품이나 사례를 찾아 차이를 정리합니다` | `Beads와 Linear를 비교해줘` / `compare Beads and Linear` |
| `/product:memory` | `[기억/Memory] 중요한 내용을 저장하거나 전에 저장한 내용을 찾습니다` | `기억해줘` / `remember this`; `찾아줘` / `find` |
| `/product:status` | `[현황/Status] 지금 어디까지 했고 무엇이 막혔는지 보여줍니다` | `상태 보여줘` / `show status` |
| `/product:loop` | `[다음/Next] 지금 해야 할 일 하나를 골라줍니다` | `다음에 뭐 해?` / `what is next?` |
| `/product:execute` | `[진행/Execute] 준비가 끝난 작업을 실제로 시작합니다` | `진행해줘` / `execute the plan` |
| `/product:review` | `[확인/Review] 만든 결과가 요청대로 작동하는지 점검합니다` | `검토해줘` / `review the result` |
| `/product:release` | `[출시/Release] 배포 전에 확인하고 출시를 진행합니다` | `출시 가능한가?` / `is this ready to release?` |

### Internal-only capabilities

Do not expose implementation vocabulary as user choices. Route it from
`/moduflow` or from one of the visible actions:

- knowledge, evidence, research, report and promote;
- opportunity, goal, spec, plan and roadmap when they are workflow steps rather
  than the user's immediate intent;
- profile, migrate, sync, doctor, portfolio, projects, weekly, handoff, risks,
  workers and production;
- all router, bridge, adapter and policy skills;
- generated `source-command-product-*` skills that duplicate command behavior.

Advanced behavior remains available through natural Korean requests to
`/moduflow`; hiding a separate menu entry must not remove the underlying
capability.

## Decision and Memory Interaction

`product:decision` is currently written as though the human must supply issue ID,
spec path, evidence, caveats and a next action. That is too much ceremony for an
ordinary choice. The user should provide only the choice:

```text
/moduflow 결정으로 남겨줘: 로그인은 이메일부터
```

ModuFlow should infer the issue, reason and alternatives from the active
conversation and project artifacts. When the reason is genuinely missing, ask one
plain question: `이 선택을 한 가장 큰 이유가 무엇이었나요?`

Keep the structured internal fields, but translate them in user-facing review:

| Internal term | User-facing Korean |
|---|---|
| rationale | 왜 이렇게 정했나요? |
| alternatives | 다른 선택은 무엇이었나요? |
| caveats | 조심할 점이 있나요? |
| retrieval_trigger | 언제 다시 살펴보면 될까요? |
| evidence | 참고한 자료가 있나요? |

Memory routing should follow the user's Korean or English sentence rather than
requiring the user to choose a storage taxonomy:

| User expressions | Internal destination |
|---|---|
| `메모해줘`, `note this`, `capture this` for an unshaped thought | inbox |
| `기억해줘`, `remember this` for a durable fact, promise or preference | memory |
| `정했어`, `결정으로 남겨줘`, `we decided`, `record this decision` for a choice among options | decision |
| `비교해줘`, `compare`, `benchmark` for external alternatives | benchmark |
| `찾아줘`, `전에 뭐였지?`, `find`, `what did we decide?` | memory search across the relevant record kinds |

Meetings, references and knowledge folders stay implementation details. The user
asks to save or find content; ModuFlow chooses the record kind and location.

## Acceptance Criteria for a Future Implementation

1. The default user needs to remember only `/moduflow`.
2. The visible shortcut allowlist contains only the hub and the ten actions above.
3. Every visible item has a Korean-first bilingual label and at least one Korean
   and one English input example; no documented one-letter or partial abbreviation
   exists.
4. Internal skills remain model-usable but do not appear as user actions.
5. A one-sentence decision can be saved without asking the user to fill a form.
6. Equivalent Korean and English intents route identically in tests: `메모해줘` /
   `note this`, `기억해줘` / `remember this`, `정했어` / `we decided`,
   `비교해줘` / `compare`, and `찾아줘` / `find`.
7. Claude and Codex packages expose equivalent human-facing choices even if their
   packaging mechanisms differ.

## Retrieval Trigger

Re-read when changing command descriptions, slash-menu visibility, Codex skill UI
metadata, Claude invocation controls, the `/moduflow` natural-language router, or
the decision/memory capture experience.
