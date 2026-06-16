# Issue 015: 워커 병렬 판정 기준(파일 disjoint) + worktree 격리

## Summary

병렬 적격 판정이 "작업 독립성"이 아니라 "워커 도메인 수"(`worker_orchestrator.py:88` `len(unique_workers) >= 2`)를 봐서 양방향 오판한다. 또한 병렬 워커 격리(worktree)·병합 순서가 전무하다.

## Source

- Type: internal review (스웜 견고성 분석 2026-06-16)
- Finding:
  - `scripts/worker_orchestrator.py:88` 적격 기준이 도메인 수 기반.
  - 코드베이스 전체 `worktree` 0건 → 병렬 워커 파일 동시수정 충돌 구조적 가능.
  - worker-plan에 `merge_order` 없음.

## Context

- 독립 구현 태스크 5개 → 전부 implementation-worker(도메인 1) → sequential 오판.
- 의존 cross-domain 태스크 2개 → 도메인 2 → parallel-eligible 오판.
- `tasks.md`에 파일 귀속 정보 없어 "separate files" 기준을 코드가 검사 불가.

## Acceptance Criteria

- 적격 판정 = (파일 집합 disjoint) AND (의존 그래프 비순환) AND (shared-state 0). 도메인 수는 기회 신호로만.
- `tasks.md` 태스크에 `files:` 메타 수용.
- worker-plan.json에 `merge_order`(위상정렬) 추가.
- `product:execute`에 worktree 생성→실행→순차 머지→정리 단계 명문화.

## Workflow Tasks

- [ ] spec → `specs/015-worker-disjoint-isolation/spec.md`
- [ ] plan → `specs/015-worker-disjoint-isolation/plan.md`
- [ ] execute → orchestrator 판정 로직 + execute 격리 단계
- [ ] review → 오판 양방향 회귀 테스트

## Next Command

`product:spec 015`
