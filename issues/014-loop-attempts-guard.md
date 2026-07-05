# Issue 014: Loop attempts 무한루프 가드

**Status: superseded-by-019** — absorbed into `019-loop-kernel-and-state-model` (done; guard lives in `scripts/project_loop.py`). Status line added 2026-07-05 (issue 066 legacy-schema migration).

## Summary

`loop-state.json`의 `attempts` 필드를 실제로 증가·임계 차단하는 로직이 없다. 같은 `next_command`를 무한 추천/실행하는 것을 막을 코드 게이트를 추가한다.

## Source

- Type: internal review (loop 견고성 분석 2026-06-16)
- Finding: `attempts`는 스키마(`templates/workspace/loop-state.json`)에만 존재; 증가/차단 로직 0줄. `commands/product-loop.md`에 max_attempts 규칙 없음.

## Context

loop는 100% 자연어 규약이라 무한루프 차단이 LLM 자발 판단에만 의존한다. N회 반복 또는 `last_verification` 미갱신 시 자동으로 `status="needs_decision"` + blocker 기록이 필요하다.

## Acceptance Criteria

- 동일 `next_command`가 N회(예: 3) 연속이거나 검증 진전 없으면 `status=needs_decision`로 전환.
- `attempts` 증가가 mutating step마다 반영.
- `product-loop.md` + adapter `goal-loop.yaml`에 max_attempts 규칙 문서화.
- doctor/validate가 loop-state 필드·타입 검증(현재는 파일 존재만, `validate_moduflow.py:77`).

## Workflow Tasks

- [ ] spec → `specs/014-loop-attempts-guard/spec.md`
- [ ] plan → `specs/014-loop-attempts-guard/plan.md`
- [ ] execute → loop-state 가드 로직 + 문서
- [ ] review → 회귀 테스트(N회 반복 시 needs_decision)

## Next Command

`product:spec 014`
