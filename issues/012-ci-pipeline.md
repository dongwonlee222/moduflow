# Issue 012: CI Pipeline (테스트·검증 자동화)

**Status: done** — shipped as 0.2.6 (commit 7fbb967; `.github/workflows/ci.yml` live). Status line added 2026-07-05 (issue 066 legacy-schema migration).

## Summary

GitHub Actions CI를 추가해 push/PR마다 unit tests + validate_moduflow + release_check를 자동 실행한다. 회귀를 사람 손이 아닌 파이프라인이 차단한다. Shipped as 0.2.6.

## Source

- Type: internal review (loop/swarm/검증 견고성 분석 2026-06-16)
- Finding: `.github/workflows/` 부재 → 검증 스크립트가 수동 실행에만 의존, 회귀 자동 차단 없음.

## Context

release_check.py·tests는 누군가 로컬에서 돌려야만 작동했다. 0.2.5까지 CI가 없어 "validate 통과" 주장이 자동 검증되지 않았다(PR #2가 그 예).

## Acceptance Criteria

- push(main)·PR에서 `unittest discover -s tests` 실행. ✅
- `validate_moduflow.py .` + `release_check.py .` 실행. ✅
- 하나라도 실패하면 워크플로우 red. ✅

## Workflow Tasks

- [x] execute → `.github/workflows/ci.yml` (0.2.6)
- [x] review → 로컬 discover + release_check PASS 확인
- (spec/plan 생략: 소규모 인프라 추가)

## Next Command

`product:status`
