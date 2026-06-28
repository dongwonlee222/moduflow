---
id: 2026-06-28-planning-artifact-templates-benchmark
kind: evidence
title: 기획 산출물 템플릿 외부 벤치마킹 (이슈 046)
date: 2026-06-28
tags: [benchmark, planning-harness, prd, design-doc, templates, mermaid, issue-046]
summary: 기획 하네스 원문과 GitHub의 검증된 PRD/design-doc/IA/journey 템플릿을 조사해, ModuFlow 046 기획 산출물 템플릿의 외부 레퍼런스로 정리. 핵심 발견은 "고정 순서 스킬 체인 + Mermaid/Markdown canonical"이 ModuFlow specs/<issue>/ 구조와 1:1 대응한다는 점.
owner: Dongwon Lee
confidence: high
source_event: benchmarking_session
issue_id: 046-planning-artifact-templates
source_artifacts:
  - "memory/evidence/2026-06-28-planning-artifact-templates-benchmark.md"
references:
  - "https://maily.so/makersnote/posts/1gz2e564z3q"
  - "https://news.hada.io/topic?id=30870"
  - "https://github.com/snarktank/ai-dev-tasks/blob/main/create-prd.md"
  - "https://github.com/eugeneyan/ml-design-docs"
  - "https://mermaid.js.org/syntax/userJourney.html"
  - "https://dev.to/gochev/creating-ux-with-textmarkdown-2mm"
reversal_conditions: ai-dev-tasks/ml-design-docs가 폐기되거나, ModuFlow가 Markdown canonical을 벗어나 비-텍스트 산출물로 전환하는 경우.
---

# 기획 산출물 템플릿 외부 벤치마킹 (이슈 046)

> 조사 일자: 2026-06-28. 기획 하네스 원문 + GitHub 검증 레포 기반.

## 1. 기획 하네스 산출물 체계 (원문 확인)

핵심: 개별 템플릿이 아니라 **고정 순서 스킬 체인** + Mermaid/Markdown canonical. 상위기획은 AI 자동화가 쉬운데 상세기획이 수작업이라는 문제의식에서, `CLAUDE.md` 규칙 + 슬래시 스킬로 파이프라인을 통제한다.

| 순서 | 스킬 | 산출물 |
|---|---|---|
| 1 | `/search-documents` | 정책/기존문서 컨텍스트 수집 |
| 2 | `/split-requirements` | 요구사항 분해 |
| 3 | `/sequence_diagram` | 시퀀스 다이어그램 (Mermaid) |
| 4 | `/user-flow` | 유저 플로우차트 |
| 5 | `/logic-check` | 예외 케이스 |
| 6 | `/release-note` | 공유용 요약 |
| 7 | `/deploy-jira` | 태스크화 |

실제 흐름: `시퀀스(Mermaid) → 유저 플로우 → 통합 HTML 대시보드`. ModuFlow `specs/<issue>/` 구조와 거의 1:1 대응.

## 2. 산출물 8종별 레퍼런스

| # | 산출물 | 레퍼런스 (★) | 핵심 패턴 |
|---|---|---|---|
| 1 | 요구사항/PRD | snarktank/ai-dev-tasks (★7.7k) | 착수 전 **AI 명확화 질문 3-5개** → Goals/User Stories/Functional Reqs/**Non-Goals** |
| 2 | 사례 벤치마킹 | (범용 MD 레포 부재 — 확인) | Feature Comparison Matrix 표: 행=기능, 열=경쟁사, 셀=점수 + "갭/기회" 결론. AI가 웹 리서치로 수집 |
| 3 | 해결방안 | eugeneyan/ml-design-docs (★706) | Methodology + **Alternatives considered** + Appendix |
| 3b | 의사결정(ADR) | DesignDocumentTemplates (★138) | Context→Decision→Alternatives→Consequences→Rollout. bold-label 패턴 |
| 4 | 사용자 시나리오 | ai-dev-tasks User Stories (추론) | As a/I want/So that + 인수조건 + 예외 경로 |
| 5 | 정보구조 IA | utext (Markdown→IA) | 중첩 리스트(트리) + 화면 인벤토리 표 |
| 6 | 고객 여정 | Mermaid `journey` (공식) | `journey`/`section`/`Task: <1~5>: <actor>` 감정 점수 |
| 7 | 상세 화면 기획 | utext + ASCII 와이어프레임 | 목적→진입경로→요소목록→인터랙션/예외 |
| 8 | 다이어그램 | Mermaid (GitHub 네이티브 렌더) | ```mermaid 펜스 시퀀스/플로우. 별도 도구 불필요 |

## 3. ModuFlow 046 핵심 권고

1. **산출물 간 파이프라인 순서를 템플릿에 명시** (이전/다음 포인터). 하네스의 진짜 가치는 템플릿 품질이 아니라 고정 순서.
2. **모든 다이어그램 Mermaid 통일** — 시퀀스/플로우/고객여정 모두 커버, GitHub/Obsidian 네이티브 렌더, Markdown canonical 정합.
3. **Non-Goals + Alternatives considered 필수 섹션화** — ai-dev-tasks·ml-design-docs 공통 차별 요소. 범위 통제 + 의사결정 아카이브.
4. **벤치마킹은 Feature Comparison Matrix 표 패턴 내장** — 범용 MD 레포 부재 확인. AI 웹 수집 + 표 구조 + 갭 결론.
5. **(선택) 각 템플릿에 AI 명확화 질문 블록** — 빈 템플릿을 던지지 않고 질문→채움. "필요하면 만든다" 제약과 정합.

## 확인된 사실 vs 추론

- 확인: ★수치, Mermaid journey 점수 1~5, 하네스 스킬 체인, utext 문법은 도구로 직접 검증.
- 추론: 시나리오=User Stories 매핑, 범용 벤치마킹 MD 레포 부재 결론(검색 결과 도메인 특화 AI skill뿐).
