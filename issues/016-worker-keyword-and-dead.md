# Issue 016: assign_worker 키워드 충돌 + dead worker 정의 동기화

**Status: superseded-by-023** — absorbed into `023-worker-routing-and-isolation` (done). Status line added 2026-07-05 (issue 066 legacy-schema migration).

## Summary

`assign_worker`(`worker_orchestrator.py:46-50`)가 WORKER_RULES를 순서대로 첫 매치 반환해, "acceptance" 같은 키워드가 의도와 다른 워커로 오배정된다. 또한 `workers/` 파일과 WORKER_RULES가 불일치한다.

## Source

- Type: internal review (스웜 분석 2026-06-16)
- Finding:
  - 키워드 우선순위 충돌(예: "acceptance"가 qa-reviewer보다 pm-strategist에 먼저 매칭). 테스트는 다른 단어를 써서 충돌 미커버.
  - dead workers: `spec-architect`, `roadmap-planner`는 `workers/`에 파일 존재하나 WORKER_RULES에 미배정 → 절대 배정 안 됨.

## Context

`WORKER_RULES`(9-18) 순서 의존 매칭. workers/ 8개 vs 배정 가능 6개.

## Acceptance Criteria

- WORKER_RULES에 전용/우선순위 키워드 부여로 qa↔pm 등 충돌 해소.
- 충돌 케이스("acceptance") 테스트 추가.
- spec-architect/roadmap-planner를 WORKER_RULES에 추가하거나 미사용 파일 제거.
- doctor에 "workers/ 파일 ↔ WORKER_RULES 일치" 검사.

## Workflow Tasks

- [ ] spec → `specs/016-worker-keyword-and-dead/spec.md`
- [ ] execute → WORKER_RULES 정비 + doctor 검사
- [ ] review → 키워드 충돌 + 일치 검사 테스트
- (plan 생략: 소규모)

## Next Command

`product:spec 016`
