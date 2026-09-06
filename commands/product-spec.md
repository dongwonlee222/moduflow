---
description: Create or update spec/PRD artifacts for an issue.
argument-hint: "<issue id>"
user-invocable: false
---

# /product:spec

Turn a Git issue into a spec.

## Clarify only when needed

Before writing `spec.md`, read the issue, linked opportunity, benchmark, inbox, and prior notes. If they already answer target user, pain point, in/out of scope, success signal, and main exception paths, write the spec without extra questions.

Ask the user only when the missing answer changes scope, priority, risk, or acceptance criteria. Default to **1-3 concise questions**, not a long interview. Preserve shaped product rationale from opportunity/issue/interview notes so execution and review do not lose the original context.

## Do

1. Create `specs/<issue-id>-<slug>/spec.md`.
2. Fill the template below. `## Non-Goals` and `## Alternatives Considered` are **required** — they are what separates a usable spec from a thin one (scope control + decision archive).
3. Include at least one **Mermaid diagram** when the issue has any flow, sequence, or state (most do). Mermaid renders natively on GitHub and Obsidian, so the canonical `spec.md` is also the visual artifact — no separate file needed.
4. Keep the Git issue linked, and add the pipeline pointers (previous/next artifact) so the planning chain stays connected.
5. **Korean reading sidecar (049, new artifacts forward).** English `spec.md` stays canonical. When authoring a *new* spec, also write `spec.ko.md` beside it — same content in Korean prose — so the 047 panel's `English / 한글` toggle can show it to a Korean reviewer. Convention, not a gate: a missing `.ko.md` simply falls back to English. Do not retro-translate existing specs; do not translate the canonical file in place.

## Template

````markdown
# Spec: <title>

Issue: `<issue-id>`
Prev: <upstream artifact, e.g. opportunity / benchmark> · Next: <product:plan>

## Problem
<pain point — who hurts, when, why it matters>

## Goals
<numbered outcomes>

## Non-Goals
<explicitly out of scope — required>

## Users & Scenarios
<as a / I want / so that + main + exception paths>

## Proposed Solution
<the approach>

```mermaid
flowchart TD
    A[entry] --> B[step] --> C[outcome]
```

## Alternatives Considered
<options weighed and why rejected — required>

## Acceptance Criteria
<verifiable checks>

## Risks & Open Questions
````

## Constitution Assumed (issue 073)

Specs assume `workspace/constitution.md` — do not restate its principles in a spec. Only constraints specific to this issue belong in the spec body; shared engineering law arrives by reference when the plan is written.

## Selective depth (not every artifact on every issue)

The diagram, Non-Goals, and Alternatives belong in essentially every spec. The heavier planning artifacts — user scenario detail, IA tree, customer journey, screen plans — are produced **only when the issue warrants them** (a UX feature needs screens; a refactor does not). Reach for `/product:design` / `/product:analyze` then, not by default. See `046-planning-artifact-templates`.

## 승인 요청 쓰는 법 (issue 129)

승인 요청은 `## Human Review Decisions`에 씁니다. 번호가 붙어도(`## 15. Human
Review Decisions`) 같은 섹션입니다.

**항목마다 둘 중 하나를 반드시 붙입니다.**

- `[확인만]` — 측정된 정답이 있거나 이미 그렇게 동작 중인 것. **한 줄이면 됩니다.**
- `[사장님 결정]` — 진짜 판단이 필요한 것. **아래 다섯 칸을 다 채웁니다.**

```markdown
- [사장님 결정] <결정할 내용>
  - 왜 이 결정이 필요한가요? …
  - 지금 무엇이 잘못되고 있나요? …
  - 실제로 측정된 예시 …
  - 다른 선택지와 그 비용 …
  - 승인하면 무엇이 달라지나요? …
```

칸 이름은 한국어입니다. 읽는 사람이 명세를 쓴 사람이 아니라 사장님이기 때문입니다 —
이슈의 `## 요약`과 같은 이유입니다.

**왜 강제하나.** 명세 112 §15는 넷을 똑같은 무게의 명사구로 늘어놓았고, 그중 하나만
진짜 결정이었습니다. 나머지 셋은 측정된 정답이 있는 교정이었습니다. 사장님은 판단할
하나를 찾으려고 셋을 읽어야 했고, 결정에 필요한 네 가지 사실은 아무도 열어 볼 이유가
없는 `evidence/SIMULATION-REPORT.md`에 있었습니다. 한 번 왕복했습니다.

이미 승인된 항목(`**[approved …]**`)과 끝난 이슈의 명세는 검사하지 않습니다.

## 전문용어

**전문용어를 본문에 그대로 씁니다. 설명이 필요하면 그 뒤 괄호에 한 줄 답니다.**

기준은 말이 어려운지가 아니라 **읽는 사람이 그 말을 아는지**입니다.

- 안다 → 그냥 씁니다. `라우터`, `서버`, `트랜잭션`, `API`
- 모른다 → 용어 먼저, 괄호에 한 줄. `투영(지금 상태를 베껴 만든 사본)`
- **이미 이름이 있는 것에 새 이름을 지어내지 않습니다.** 검색도 안 되고 문장만 길어집니다
- 로마자는 필요할 때만. 한글로 쓰는 말에는 안 붙입니다
- 헷갈리면 답니다. 순서만 지키면 잘못 달아도 읽힙니다

기계는 검사할 수 없습니다. 사람이 지키는 규칙입니다.

**실패 예 — 셋 다 실제로 썼던 것입니다:**

| 이렇게 썼다 | 왜 틀렸나 |
| --- | --- |
| `말길 알아듣는 장치(라우터, router)` | 지어낸 말이 앞, 아는 말이 뒤. 로마자까지 불필요 |
| `되돌릴 수 있게 묶어서 처리하는 것(트랜잭션)` | 같은 뒤집힘. 결제 16년차에게 `트랜잭션`은 설명 대상이 아님 |
| `진단이 doctor 출력에 나와야 하는가` | 용어만 있고 그게 뭔지 아무 데도 없음 |

**근거** — 네 출처가 같은 말을 합니다. Google: "If the majority of your audience
is likely to recognize and understand the term, then you don't need to spell it
out." Microsoft: "Don't create a new word if one already exists." plainlanguage.gov:
"We have one rule for dealing with definitions: use them rarely." 국립국어원
「2025 전문용어 표준화 안내서」: 토착화한 외래어(버스, 컴퓨터)는 바꿔 쓰지 않고,
간결성 항목은 "불필요하게 음절 수가 길어지지 않도록 한다".

## Next

- `/moduflow analyze` if metrics or evidence are needed
- `/moduflow design` if UX flow, IA, journey, or screens are warranted
- `/moduflow plan` when the spec is ready

## Reference

Template patterns benchmarked in `memory/evidence/2026-06-28-planning-artifact-templates-benchmark.md` (ai-dev-tasks PRD, ml-design-docs, Mermaid).
