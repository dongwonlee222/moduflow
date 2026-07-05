# Issue 018: 상태 단일 소스 + dashboard 드리프트 + 워크플로우 그림 통합

**Status: superseded-by-019** — absorbed into `019-loop-kernel-and-state-model` (done). Status line added 2026-07-05 (issue 066 legacy-schema migration).

## Summary

`next_command`가 state.json·loop-state.json·goal.md 3곳에 중복되고, state.json↔dashboard.md의 active_issue가 실제로 드리프트한다. 또한 workflow.md 다이어그램에 goal·loop이 누락돼 두 워크플로우 모델이 분리돼 있다.

## Source

- Type: internal review (워크플로우 일관성 분석 2026-06-16)
- Finding:
  - next_command 3중 소스, 동기화 규칙 부재.
  - `workspace/issues.md` 생성 주체 미정(어떤 명령도 생성 안 함, status/issues는 의존).
  - `docs/workflow.md`에 goal/loop 노드 없음.

## Context

dashboard는 state.json에서 파생되는 view여야 하나 갱신 규칙·정합 검증 없음.

## Acceptance Criteria

- next_command 단일 소스를 state.json으로 지정, 나머지는 참조.
- issue lifecycle 변경 시 dashboard active_issue 자동 동기화 + `workspace/issues.md` 재생성 주체 명시.
- workflow.md에 goal/loop를 supervise 레이어로 통합.

## Workflow Tasks

- [ ] spec → `specs/018-state-single-source/spec.md`
- [ ] plan → `specs/018-state-single-source/plan.md`
- [ ] execute → 단일 소스 규칙 + dashboard 동기화 + 그림 통합
- [ ] review → 드리프트 회귀 점검

## Next Command

`product:spec 018`
