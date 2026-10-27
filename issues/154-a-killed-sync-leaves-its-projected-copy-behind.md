# Issue 154: 죽은 sync가 투영 사본을 남긴다

**Status: backlog** — created 2026-10-27.
**Priority: p1**

## 요약

on_stop 훅이 sync를 시간 초과로 죽이면(SIGKILL) `.moduflow/.txn-<id>-projected-<hex>/`
투영(지금 상태를 베껴 만든 사본)이 지워지지 않고 남습니다. chargesuccess에서
10/14~10/27 사이에 11개, 합계 약 16GB가 쌓였습니다.

## Summary

`_private_projected_root` removes its copy in a `finally` block. `subprocess.run(timeout=…)`
in `hooks/on_stop.py` kills the sync child with SIGKILL on timeout, so the block never runs.
The copy contains every canonical role root, `workspace/` included (2.3GB in chargesuccess),
so the copy alone takes most of the hook's 5-second budget.

## Source

- Type: bug — 2026-10-27, 소유자가 chargesuccess 디스크 사용량에서 발견 (16GB를
  `/Volumes/One Touch/_mac-offload/2026-10-27_chargesuccess-moduflow-txn/`로 옮김)
- Owner / decision maker: Dongwon Lee

## 안 고치면

모두플로를 쓰는 프로젝트마다 Stop 한 번에 workspace 크기만큼 디스크가 사라지고, 아무도 알아채지 못합니다. 목표의 일곱 가지 중 **프로세스**가 막힙니다 — 훅이 돌 때마다 사용자의 디스크를 갉아먹는 도구는 꺼지게 됩니다.

## 원인

시간 초과 로그 11건 = 남은 사본 11개.

```
$ grep -c "sync subprocess timed out" ~/projects/chargesuccess/.moduflow/logs/hooks.log
11
$ ls -d "/Volumes/One Touch/_mac-offload/2026-10-27_chargesuccess-moduflow-txn"/.txn-* | wc -l
11
$ ls -A ".../.txn-19053e75fe8495df0718cbd61ee19367-projected-19216eb1dc1eeeb1"
.moduflow issues knowledge memory playbooks specs workflow workspace
```

시간 초과 시 하위 프로세스는 SIGKILL을 받습니다 — `finally`가 실행되지 않습니다.

```
$ python3 -c "import subprocess,inspect;s=inspect.getsource(subprocess.run);i=s.find('except TimeoutExpired');print(s[i:i+60])"
except TimeoutExpired as exc:
            process.kill()
```

sync 한 번이 예산(5초, `SELF_BUDGET_SECONDS`)에 붙어 있습니다 (디스크 캐시가 데워진 상태).

```
$ du -sh ~/projects/chargesuccess/workspace
2.3G
$ cd ~/projects/chargesuccess && /usr/bin/time -p python3 ~/projects/moduflow/scripts/project_lifecycle.py . --sync
exit=1
real 4.16
```

`lifecycle.lock`은 남아 있지 않았습니다 (`.moduflow/transactions/` 비어 있음).

## Scope

- `_private_projected_root`: 사본을 만든 프로세스가 살아 있는 동안 사본 디렉터리에
  `flock`을 겁니다. 커널이 프로세스 사망 시(SIGKILL 포함) 잠금을 풉니다.
- 새 사본을 만들기 전에 같은 `.moduflow/`의 고아 사본을 지웁니다. 조건: 이름이 정확히
  `.txn-<hex>-projected-<16 hex>`이고, `flock`이 바로 잡히고, 일정 시간 이상 지난 것.
  나이 조건은 mkdir과 flock 사이의 틈, 그리고 잠금을 걸지 않는 이전 버전 프로세스를 보호합니다.

## Scope Fence

- `workspace/`를 사본에서 빼지 않습니다 — 검증이 `workspace/roadmap.md`·
  `workspace/analysis-runs.md`를 읽습니다.
- on_stop에 SIGTERM 유예를 넣지 않습니다 — Python은 SIGTERM 기본 동작에서 `finally`를
  실행하지 않고, 2.3GB를 지우는 시간도 남은 예산에 들어가지 않습니다. 고아 정리가 있으면
  얻는 것이 없습니다.
- chargesuccess가 매번 거부되는 이유(lifecycle drift·`RUNS_SCHEMA_UNSUPPORTED`)는 이 이슈
  밖입니다.

## Known Limit

- 정리는 다음 투영 때 일어나고, 생긴 지 10분이 안 된 사본은 남깁니다. 10/16처럼 8분
  사이에 시간 초과가 세 번 나면 그동안 사본 셋(약 7GB)이 남아 있습니다.
- **kill 자체는 계속됩니다.** on_stop은 sync가 성공해야 `.last-sync`를 쓰므로, 매번
  거부되는 프로젝트(chargesuccess)는 Stop마다 투영을 다시 만들고 예산에 걸려 죽습니다.
  이 이슈는 그 뒤를 치울 뿐 반복을 멈추지 않습니다. 반복을 멈추려면 거부된 sync의 재시도
  간격을 두거나 투영 비용을 줄여야 하며, 이 이슈 밖입니다.
- flock을 지원하지 않는 파일시스템(`ENOLCK`·`ENOTSUP`·`EOPNOTSUPP`)에서는 잠금 없이
  투영하고, 정리도 하지 않습니다 — 수정 전과 같습니다.
- 훅은 플러그인 캐시의 `scripts/`를 실행합니다. 캐시가 갱신되기 전까지 chargesuccess에는
  반영되지 않습니다.

## Acceptance Criteria

- 투영 중에 SIGKILL로 죽은 프로세스의 사본이 다음 투영 뒤 남지 않는다.
- 살아 있는 프로세스가 잠근 사본은 지워지지 않는다.
- 위 두 경우를 하위 프로세스로 재현하는 회귀 테스트가 PASS한다.

## Verification

```
$ python3 -m unittest -v tests.test_project_lifecycle_transaction.TransactionPlanningTests.test_private_projected_root_removes_copy_left_by_sigkilled_owner tests.test_project_lifecycle_transaction.TransactionPlanningTests.test_private_projected_root_keeps_copy_of_live_owner
... ok
... ok
Ran 2 tests in 0.172s
OK
```

## Workflow Tasks

- [x] 원인 확정 (위 `## 원인`)
- [x] 수정: `scripts/project_lifecycle_transaction.py` — `_remove_orphaned_projected_roots`,
  사본에 `flock`. 새 함수는 `config/project-operation-entrypoints.json`에 등록
  (operation audit가 미분류 쓰기 함수를 거부함)
- [x] 회귀 테스트 추가·실행 — `tests/test_project_lifecycle_transaction.py`
  `test_private_projected_root_removes_copy_left_by_sigkilled_owner`,
  `test_private_projected_root_keeps_copy_of_live_owner`,
  `test_private_projected_root_projects_unlocked_where_flock_is_unsupported`. 수정 전
  코드에서 첫째가 FAIL(`AssertionError: True is not false`), 수정 후 셋 다 `ok`.
- 전체 스위트(2,146개): 기준선 대비 새 실패는
  `test_the_transaction_module_is_unchanged_by_this_issue` 하나뿐입니다. 이 테스트는
  `git diff HEAD -- scripts/project_lifecycle_transaction.py`가 비어 있어야 통과하므로,
  커밋 전 작업 트리에서는 FAIL입니다. 나머지 실패 5개는 기준선에서도 실패합니다.
- [ ] 리뷰

## Related Issues

- 126, 147 — projected-validation 거부. 147의 거부 진단도 투영을 다시 만듭니다.
- 153 — 트랜잭션 모듈 분할.

## Next Command

`/moduflow execute 154`
