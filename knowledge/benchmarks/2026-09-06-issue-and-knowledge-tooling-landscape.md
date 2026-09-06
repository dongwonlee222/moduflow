---
kind: benchmark
title: 에이전트 시대의 이슈·지식 도구 지형 (2026-09 조사)
issue_id: 112-execution-planner-and-backend-boundary
spec: 
decision_supported: 자체 하네스 유지 여부 및 이슈 백엔드 외부화 판단
date: 2026-09-06
confidence: medium — 공개 자료 기반 2차 조사. 실행 검증은 Beads 벤치마크 문서에만 있다
sources:
  - https://github.com/steveyegge/beads
  - https://steve-yegge.medium.com/beads-best-practices-2db636b9760c
  - https://aidenapp.org/issue-tracking-for-ai-agents
  - https://dev.to/krlz/spec-driven-development-in-2026-what-it-is-the-tooling-and-how-teams-actually-use-it-2fk2
  - https://github.com/github/spec-kit
  - https://aidenapp.org/linear-claude-code
  - https://github.com/anthropics/claude-code/issues/12925
  - https://developer.upsun.com/posts/ai/git-worktrees-for-parallel-ai-coding-agents
  - https://addyosmani.com/blog/code-agent-orchestra/
  - https://github.com/basicmachines-co/basic-memory
  - https://mem0.ai/blog/state-of-ai-agent-memory-2026
  - https://dev.to/lofcz/why-your-ai-workflow-design-might-be-overcomplicated-1hfb
---

# 에이전트 시대의 이슈·지식 도구 지형 (2026-09 조사)

## 이 문서가 있는 이유

ModuFlow가 풀려던 네 가지 — 이슈 단위 히스토리, 다인 사용, 프로젝트 지식·의사결정
관리, 등록→제작→검증 게이트 — 를 다른 곳에서는 어떻게 푸는지 조사한 결과다.
"우리가 만든 것이 돌아가느냐"가 아니라 "직접 만드는 것이 여전히 맞느냐"를 판단하기
위한 자료다.

**성격 주의**: 이 문서는 공개 자료 기반 2차 조사다. 실행으로 확인한 것은
`2026-09-06-beads-v1-2-2-empirical-issue-engine-benchmark.md` 한 건뿐이며,
아래 내용은 그 실측을 둘러싼 맥락이다. 수치를 근거로 쓸 때는 출처를 다시 열 것.

## 1. 이슈 — git-native 트래커로 수렴 중

Beads(`bd`)가 사실상 기준점이 됐다. 조사 시점 GitHub ★26.9k, fork 1.8k,
Claude Code·Copilot·Factory.ai 연동. Steve Yegge가 "50 First Dates 문제"
— 에이전트가 어제 작업을 기억 못 하고 깨어나는 것 — 를 이름 붙여 제기했다.

설계에서 가져올 만한 것:

- **해시 기반 ID**로 다중 브랜치·다중 에이전트 머지 충돌을 회피
- **의존성 그래프 + `bd ready`** — 에이전트가 "다음 할 일"을 스스로 고름
- **원자적 claim** — 동시 선점 시 한 명만 성공
- **semantic memory decay** — 닫힌 이슈를 요약 압축해 토큰 예산 절약
- `bd remember`/`bd prime` — 프로젝트 원칙을 저장하고 프롬프트에 주입

핵심 논지는 "에이전트에게 없는 것은 지속되는 상태·소유권·완료 기준이고,
이슈 트래커가 정확히 그것을 외부화한다"는 것이다.

## 2. 그러나 다수는 트래커를 만들지 않는다

대다수는 기존 트래커에 MCP를 붙인다. Linear는 Cursor·OpenAI Codex·Devin을
**네이티브 에이전트로 이슈 할당**까지 지원한다. Claude Code는 조사 시점(2026-07
기준 자료) Linear 에이전트 디렉토리에 없고 feature request가 열려 있어,
Linear MCP 서버나 Cyrus 같은 브리지로 우회한다.

→ ModuFlow 관점의 함의: 자체 이슈 저장소를 계속 소유할 이유는 "제품 맥락(목표·
스펙·AC·의사결정·증거)이 이슈에 붙어 있어야 한다"는 것뿐이다. 실행 상태·담당자·
ready 질의만 필요하다면 그 부분은 살 수 있는 물건이다.

## 3. 스펙 — Spec Kit이 표준이 됐고, 비판도 명확하다

GitHub Spec Kit이 사실상 공통 어휘가 됐다(ModuFlow도 어댑터로 사용).
초기 도입 사례에서 잘 다듬은 스펙으로 작업할 때 에이전트 1차 성공률이
유의미하게 올라간다는 보고가 있다. 다만 사람의 시간이 구현 타이핑에서
**리뷰와 명확화로 이동**할 뿐이라는 것이 일관된 관찰이다.

반복되는 비판 넷: **검증 없음**, 문서 과잉, 프로즈 스펙의 비결정성, 약한 반복.
현재 권고는 *spec-as-source가 아니라 spec-anchored*, 수용 기준은 EARS 형식,
**코드가 진실이고 테스트가 집행자**.

→ ModuFlow 함의: Issue 112가 채택한 fail-closed 게이트와 "정본 artifact가
완료 진실"(spec §9)은 이 비판에 대한 응답으로 읽힌다. 방향이 어긋나지 않는다.

## 4. 다인·다에이전트 동시 작업 — 공유 상태 파일이 아니라 worktree + PR

Conductor(Mac), Composio Agent Orchestrator, GitHub Agent HQ Mission Control이
모두 **에이전트당 git worktree 1개 + diff 우선 리뷰** 구조다. 전체 클론 없이
격리된 작업 공간을 준다는 점이 채택 이유로 반복 언급된다.

**공유 `state.json` 하나를 모두가 쓰는 모델은 이 흐름에 없다.**
ModuFlow `.moduflow/state.json`의 전역 `active_issue`가 정확히 그 반대 구조다.

## 5. 지식·메모리 — 마크다운 KB가 사실상 표준

에이전트가 이미 읽는 형식(AGENTS.md·CLAUDE.md·llms.txt·스펙 파일)이고 사람에게도
읽히며 락인이 없다는 이유로, 2026년의 팀 지식베이스는 압도적으로 마크다운이다.
Basic Memory는 Obsidian vault를 MCP로 read/write한다(`write_note`/`read_note`/
`search_notes`).

설계 패턴: **스코프 태깅** — 저장할 때 `user_id`/`agent_id`/`session_id`/`org_id`를
붙이고 회수 시 병합·랭킹. 접근제어는 별도로 만들지 않고 **git 권한을 그대로 상속**.

→ ModuFlow 함의: `memory/`·`knowledge/` 분류 체계는 업계 패턴과 어긋나지 않는다.
문제는 형식이 아니라 **유입 경로**다. 저장 시점·회수 경로가 없으면 분류만 남는다.

## 6. 커뮤니티 정서 — 자체 대형 오케스트레이션은 대체로 실패로 회고된다

반복 보고되는 실패 양상: 무한 루프와 토큰 소모, 코드를 쓰지 않고 완료로 표시하는
"phantom execution", 그리고 **정교한 프롬프트를 전부 지우고 기본값으로 돌아갔더니
성능이 거의 같더라**는 관찰. 리서치·개요·초안·편집·SEO를 각각 에이전트로 나눈
파이프라인이 잘 쓴 단일 프롬프트 30초 작업을 5분에 처리했다는 사례도 있다.

→ ModuFlow 함의: Issue 112의 Scope Fence("실행 엔진을 더하지 말라")와
GC1("실행했다고 보고하는 함수를 추가하지 말라")이 이 실패 양상에 대한 방어다.
스코프 펜스를 무르는 제안이 나오면 이 절을 근거로 거절할 수 있다.

## 판단에 쓴 방식

이 조사는 "무엇이 인기 있나"가 아니라 **"우리가 소유해야 할 층은 어디까지인가"**를
가르는 데 썼다. 결론은 세 층 분리다.

```
제품 맥락 (목표·스펙·AC·의사결정·증거·게이트·보고)   → ModuFlow가 계속 소유
이슈 신원·의존성·ready·원자적 claim·담당자·상태     → 살 수 있는 물건 (후보)
실제 에이전트 실행·worktree·재시도·commit·PR·CI     → 호스트 런타임 (Claude/Codex/Git)
```

가운데 층의 채택 여부 결정은
`memory/decisions/2026-09-06-beads-issue-backend-not-adopted.md`에 있다.

## Retrieval Trigger

이슈 트래커·백로그 도구를 바꿀지 검토할 때, 자체 하네스를 더 만들지 말지 판단할 때,
다인 동시 작업 구조를 설계할 때, 지식·메모리 레이어의 유입 경로를 설계할 때,
또는 "요즘 다들 어떻게 하나"라는 질문이 다시 올 때 읽는다.

## 한계

- 2차 조사다. Beads 외에는 직접 돌려보지 않았다.
- 별 수·다운로드 수는 조사 시점 값이며 근거로 인용할 때 재확인이 필요하다.
- Linear의 Claude Code 미지원은 2026-07 기준 자료라 이미 바뀌었을 수 있다.
