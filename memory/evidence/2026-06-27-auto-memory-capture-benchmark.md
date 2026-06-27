---
id: 2026-06-27-auto-memory-capture-benchmark
kind: evidence
title: AI 도구 자동 메모리 캡처 패턴 벤치마킹
date: 2026-06-27
tags: [benchmark, memory, auto-capture, mem0, copilot, chatgpt, cursor, windsurf]
summary: Mem.ai, Screenpipe, Notion AI, Linear, Copilot Memory, Cursor, Windsurf, Claude Code, ChatGPT Memory 등 8개 도구의 자동 메모리 캡처 트리거/아키텍처/한계를 분석. ModuFlow 자동화 설계에 적용할 패턴 도출.
owner: Dongwon Lee
confidence: high
source_event: benchmarking_session
references:
  - "memory/evidence/2026-06-27-github-platform-benchmark.md"
reversal_conditions: 새로운 표준 자동 메모리 레이어(예: MCP Memory 표준화)가 업계 표준으로 자리잡는 경우
---

# AI 도구 자동 메모리 캡처 패턴 벤치마킹

## 진짜로 자동 캡처되는 도구 (사용자 액션 불필요)

| 도구 | 트리거 | 캡처 내용 | 한계 |
|---|---|---|---|
| **Screenpipe** | 2초마다 스크린샷 + 오디오 | 모든 것 (OCR + STT) | 프라이버시 위험, 중요도 구분 없음 |
| **ChatGPT Dreaming** | 세션 종료 후 백그라운드 비동기 | 반복 패턴/선호 추론 | 불투명, 오추론 위험 |
| **Windsurf Cascade** | 세션 중 패턴 감지 | 아키텍처 결정, 라이브러리 선호 | 확률적, 노이즈 포함 가능 |
| **Claude Code MEMORY.md** | 작업 완료 시 에이전트 자기 기록 | 학습된 패턴, 환경 특이사항 | 신뢰도 편차 있음 |
| **Copilot Memory** | 레포 상호작용 패턴 감지 | 코딩 컨벤션, 아키텍처 패턴 | 28일 만료, 레포 단위 |

## 핵심 패턴: Candidate → Approval → Durable Memory

현대 시스템의 표준 파이프라인:
```
Raw content → Extraction LLM → 후보 생성 → 신뢰도 점수 → 임계값 초과 시 영구 저장
                                              ↓
                                    낮은 신뢰도 / 이미 존재 / 충돌 시 → 거절
```

## 트리거 신뢰도 순위

```
1. 명시적 사용자 액션 ("이거 저장해줘")  → 가장 신뢰, 가장 수동
2. on-save / on-commit (git hook)         → 코드 결정 캡처에 최적
3. 세션 종료 시 (session-end hook)        → Claude Code, ChatGPT Dreaming
4. 상태 변경 시 (status change)           → Notion: 페이지 → Complete → AI 트리거
5. 시간 기반 연속 (time-based)            → Screenpipe (2초마다)
6. AI 추론 백그라운드                     → ChatGPT Dreaming, Windsurf
```

## Mem0 오픈소스 아키텍처 (가장 정교)

- 모든 LLM 상호작용 후 Extraction LLM 실행
- 3가지 메모리 스코프: User(크로스 세션), Session(단기), Agent(에이전트별)
- 벡터DB(의미) + 그래프DB(관계) 이중 구조
- MCP 호환 서버 제공, Apache 2.0 라이선스

## ModuFlow에 적용할 베스트 아키텍처

```
git commit   → hook → AI가 커밋 메시지+diff 요약 → memory/.candidates/ 저장
product:release → 자동 → 이슈 완료 결정 → memory/.candidates/ 저장
세션 종료    → MCP(Mem0) → 세션 학습 추출 → 영구 저장
```
