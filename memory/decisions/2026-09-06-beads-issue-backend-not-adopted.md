---
id: 2026-09-06-beads-issue-backend-not-adopted
kind: decision
title: 이슈 백엔드는 지금 Beads로 바꾸지 않는다
issue_id: 112-execution-planner-and-backend-boundary
spec: 
source_event: 2026-09-06 Beads v1.2.2 격리 실측 후 채택 여부 판단
source_artifacts:
  - knowledge/benchmarks/2026-09-06-beads-v1-2-2-empirical-issue-engine-benchmark.md
  - knowledge/benchmarks/2026-09-06-issue-and-knowledge-tooling-landscape.md
review_after: 
supersedes: []
superseded_by: []
depends_on: []
references:
  - workspace/inbox.md
storage_policy: local
mirror_targets: []
owner: Dongwon Lee
date: 2026-09-06
tags: []
summary: Beads를 지금 채택하지 않는다. 실측이 통과시킨 것은 한 체크아웃 안의 두 프로세스인데, 실제로 필요한 것은 두 컴퓨터이고 그 구간은 미검증이다. 대신 team-state의 거짓 lock을 native로 고치고, 두 조건이 모두 충족되면 재검토한다.
rationale: 다섯 가지다. (1) 혼자 클론해 이어서 작업하는 것은 이미 된다 — 깨지는 것은 두 사람이 동시에 붙을 때뿐이고 그 두 번째 사람이 아직 없다. (2) Beads 실측이 증명한 것은 embedded Dolt 한 체크아웃 안의 직렬화이고, 필요한 것은 두 컴퓨터의 remote/server 동작이라 증명 구간과 필요 구간이 어긋난다. (3) 그 구간을 넘으려면 Dolt 서버 운영과 push/pull 규율이 추가된다 — 1인 프로젝트에 인프라 한 대가 늘어난다. (4) v1.2.2는 실수 배포된 1.2.0/1.2.1을 1.1 계열로 되돌린 recovery release라, 다인 운영에 필요한 work leases·events journal·sync federation·HTTP API가 정확히 빠져 있다. (5) native 대안이 작다 — 원자적 잠금은 project_lifecycle_transaction.py의 os.O_EXCL 기반 _acquire_lifecycle_lock에 이미 있고, .moduflow/state/ 는 이미 gitignore돼 있고, dispatchable_now도 이미 있다. 새 스케줄러가 아니라 있는 것 넷을 잇는 일이다.
evidence: knowledge/benchmarks/2026-09-06-beads-v1-2-2-empirical-issue-engine-benchmark.md (원자적 claim·의존성·memory 통과, 다기기/remote 미검증). 코드 확인 — project_workflow.py:194 upsert_team_item이 기존 lock_state/locked_by를 읽지 않고 무조건 병합, start_issue_work:242-243이 locked_by를 그대로 덮어씀. grep 결과 worktree를 생성하는 코드는 0건이며 worker_orchestrator.py:408·476의 문자열 두 곳뿐이다.
alternatives: 지금 전면 채택 — 미검증 구간이 필요의 전부라 기각. shadow pilot 즉시 착수 — 동시 작업자가 실재하지 않아 통과해도 쓸 곳이 없으므로 보류. 아무것도 안 함 — team-state의 lock 필드가 강제되지 않으면서 강제되는 것처럼 보이는 상태가 남으므로 기각.
reversal_conditions: 두 조건이 모두 충족되면 재검토한다. (1) 동시 작업자가 실제로 2명 이상 생긴다 — 예정이 아니라 실재. (2) P0 시험(두 컴퓨터 Dolt remote push/pull 동시 편집 + 원격 장애·쓰기 중단·복구)을 통과한다. 하나만으로는 부족하다 — 사람이 없으면 문제가 없고, P0가 깨지면 채택해도 문제가 남는다. 추가 중단 사유 셋: v1.2 전용 기능에 의존하는 설계가 필요해지면, embedded 모드에서 bd doctor 부재를 ModuFlow doctor가 대신하지 못하면, 쓰기 불가 홈에서 ~/.dolt 초기화 panic이 팀원 PC에서 재현되면.
confidence: medium
---

# 이슈 백엔드는 지금 Beads로 바꾸지 않는다

## Summary

Beads를 지금 채택하지 않는다. 실측이 통과시킨 것은 한 체크아웃 안의 두 프로세스인데,
실제로 필요한 것은 두 컴퓨터이고 그 구간은 미검증이다. 대신 `team-state.json`의
거짓 lock을 native로 고치고, 아래 두 조건이 모두 충족되면 재검토한다.

## Rationale

1. **필요한 것은 이미 된다.** 혼자 클론해서 이어서 작업하는 것은 동작한다
   (`workspace/inbox.md`, 2026-09-05). 깨지는 것은 두 사람이 **동시에** 붙을
   때뿐이고, 그 두 번째 사람이 아직 없다.
2. **증명 구간과 필요 구간이 어긋난다.** 실측이 통과시킨 것은 embedded Dolt
   한 체크아웃 안의 직렬화다. 필요한 것은 두 컴퓨터의 remote/server 동작이고,
   벤치마크가 스스로 미검증으로 표시한 바로 그 구간이다.
3. **넘으려면 서버가 필요하다.** JSONL은 원본도 백업도 아니라고 Beads 자신이
   말한다. 1인 프로젝트에 Dolt 서버 운영과 push/pull 규율이 추가된다.
4. **v1.2.2에 팀 기능이 없다.** recovery release라 work leases·events journal·
   sync federation·HTTP API가 빠져 있다. 다인 운영에 필요한 것이 정확히 빠진
   버전을 다인 운영 때문에 도입하는 셈이 된다.
5. **native 대안이 작다.** 잠금(`_acquire_lifecycle_lock`, `os.O_EXCL`),
   머신-로컬 상태 경로(`.moduflow/state/`, 이미 gitignore), 의존성 인지 선택
   (`dispatchable_now`)이 **이미 있다**. 키 확장 + 파일 위치 이동 + 함수 승격 +
   write→render 전환이면 된다.

## Evidence

- `knowledge/benchmarks/2026-09-06-beads-v1-2-2-empirical-issue-engine-benchmark.md`
  — 원자적 claim, 의존성 해제, `remember`/`prime` 통과. 다기기·remote·복구 미검증.
- 코드 확인 (2026-09-06): `scripts/project_workflow.py:194 upsert_team_item`이
  기존 `lock_state`/`locked_by`를 읽지 않고 무조건 병합한다.
  `start_issue_work:242-243`이 `locked_by`를 그대로 덮어쓴다. lock 미강제 확정.
- `grep worktree scripts/*.py` — worktree를 생성하는 코드는 0건.
  `worker_orchestrator.py:408`·`476`의 문자열 두 곳뿐이다. 걷어낼 runtime은
  실행 코드가 아니라 어휘다.

## Alternatives

지금 전면 채택 — 미검증 구간이 필요의 전부라 기각. shadow pilot 즉시 착수 —
동시 작업자가 실재하지 않아 통과해도 쓸 곳이 없으므로 보류. 아무것도 안 함 —
lock 필드가 강제되지 않으면서 강제되는 것처럼 보이는 상태가 남으므로 기각.

## Scope

이 결정은 **백엔드 선택**에 관한 것이고, Issue 112(실행 계획 게이트)와는 다른
축이다. 112는 원래 범위 그대로 Stream C 인터페이스 리뷰로 진행한다. 백엔드
작업이 필요해지면 112에 흡수하지 않고 좁게 범위를 잡은 후속 이슈로 낸다
(벤치마크 "Next Action"과 동일).

## Next Action

- native 수정 2건: `upsert_team_item`에 compare-and-set 전제조건 추가,
  `team-state.json`을 직접 write에서 projection으로 강등. 별도 이슈 채번 대기.
- P0 시험(두 컴퓨터 push/pull + 복구)은 ModuFlow 코드 0줄이므로 여유 될 때
  재두고 결과를 벤치마크에 덧붙인다.

## Links

- Benchmark: `knowledge/benchmarks/2026-09-06-beads-v1-2-2-empirical-issue-engine-benchmark.md`
- Landscape: `knowledge/benchmarks/2026-09-06-issue-and-knowledge-tooling-landscape.md`
- Issue: `112-execution-planner-and-backend-boundary` (출처이며, 구현 범위는 아님)

## Reversal Conditions

두 조건이 **모두** 충족되면 재검토한다. (1) 동시 작업자가 실제로 2명 이상 생긴다
— 예정이 아니라 실재. (2) P0 시험(두 컴퓨터 Dolt remote push/pull 동시 편집 +
원격 장애·쓰기 중단·복구)을 통과한다. 하나만으로는 부족하다 — 사람이 없으면
문제가 없고, P0가 깨지면 채택해도 문제가 남는다.

추가 중단 사유 셋: v1.2 전용 기능(work leases 등)에 의존하는 설계가 필요해지면,
embedded 모드의 `bd doctor` 부재를 ModuFlow doctor가 대신하지 못하면, 쓰기 불가
홈에서 `~/.dolt` 초기화 panic이 팀원 PC에서 재현되면.

## Retrieval Trigger

Beads 재검토, 이슈 백엔드 선택, `team-state.json` lock 변경, `active_issue`
공유 상태 제거, 다인 동시 작업 설계, 또는 "이슈 트래커를 바꿀까" 류의 요청이
올 때 다시 읽는다.
