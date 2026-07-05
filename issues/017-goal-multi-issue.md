# Issue 017: Goal multi-issue supervise 스키마/문서 정합

**Status: superseded-by-019** — absorbed into `019-loop-kernel-and-state-model` (done). Status line added 2026-07-05 (issue 066 legacy-schema migration).

## Summary

문서는 goal이 "one or more issues"를 supervise한다고 하지만, 데이터 모델(`loop-state.json` `issue_id` 단수, goal.md `Linked Issue` 단수, state.json `active_issue` 단수)은 1:1만 표현 가능하다. 선언-구현 불일치를 해소한다.

## Source

- Type: internal review (워크플로우 일관성 분석 2026-06-16)
- Finding: `product-goal.md:2`·router는 multi-issue 선언, 스키마는 전부 단수.

## Context

현재 구현은 사실상 "goal 1 ↔ issue 1" 직렬 루프. 여러 issue 집계·다음 issue 선택·goal 완료 판정 로직 부재.

## Acceptance Criteria

- 택1: (A) `loop-state.json`을 `issue_ids: []` + `active_issue_id`로 확장(v2) + loop의 issue 선택/완료판정 로직, 또는 (B) 문서를 "one"으로 정정해 선언-구현 일치.
- 선택한 방향이 goal.md·router·index SKILL에 일관 반영.

## Workflow Tasks

- [ ] spec → `specs/017-goal-multi-issue/spec.md`
- [ ] plan → `specs/017-goal-multi-issue/plan.md`
- [ ] execute → 스키마 또는 문서 정합
- [ ] review → 정합 검증

## Next Command

`product:spec 017`
