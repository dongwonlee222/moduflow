# Issue 013: project_doctor 게이트화 + release_check 테스트 누락 보강

## Summary

`project_doctor.py`가 항상 `return 0`이라 release_check 안에서 무력 게이트였다. moduflow 미초기화/missing 시 exit 1을 반환하도록 수정하고, release_check 테스트 목록에서 누락됐던 `test_validation_distribution`을 추가한다. Shipped as 0.2.6.

## Source

- Type: internal review (검증 체계 분석 2026-06-16)
- Finding: `scripts/project_doctor.py:251 return 0` 무조건 통과; `release_check.py` 테스트 목록에 `test_validation_distribution` 누락(검증 스크립트 self-test가 릴리스 게이트에서 안 돌아감).

## Context

`result["moduflow"]["initialized"]`(= not missing) 기반으로 exit code를 결정한다. moduflow repo 자체는 missing=[]이라 release_check는 통과 유지. 진단 도구가 실질 게이트로 승격된다.

## Acceptance Criteria

- 초기화된 repo → `project_doctor.py .` exit 0. ✅
- 미초기화 디렉토리 → exit 1. ✅ (회귀 테스트 추가)
- release_check가 `test_validation_distribution` 포함 실행. ✅
- 기존 release_check `.` PASS 유지. ✅

## Workflow Tasks

- [x] execute → `scripts/project_doctor.py`, `scripts/release_check.py` (0.2.6)
- [x] review → `tests/test_validation_distribution.py` 회귀 테스트 2종 + discover PASS
- (spec/plan 생략: 소규모 동작 수정)

## Next Command

`product:status`
