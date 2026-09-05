# Status: Project-Aware Production Library Dashboard

Issue: `086-project-aware-production-library-dashboard`
Phase: plan-ready
Updated: 2026-07-10

## Completed

- Canonical English and Korean specs completed.
- Compared table/detail layout alternatives.
- Rejected a new application shell in favor of preserving the existing ModuFlow UI.
- Approved a full-width Production Records table with dimmed modal details.
- Approved project selector placement, new Production Records and Playbooks tabs, responsive behavior, and external/internal copy separation.
- Interactive prototype and design specification completed.
- Issue lifecycle corrected to active so the current-work graph focus targets Issue 086.

## Execution — 2026-09-04 / 2026-09-05

- T01-T08: 제작 기록·플레이북 수집기, 세 상태 커버리지 판정, 두 탭 렌더링, 상세 모달, 테스트.
- T09: `moduflow.dashboard-projects.v1` 봉투 하나로 payload 통합, 프로젝트 선택기, `?project=<id>` 복원.
- T10: `118-portfolio-mode-dashboard` 로 이관 (2026-09-05, Dongwon Lee 승인). `spec.md` "Amendment — 2026-09-05" 참조.
- T11: 신규 스위트를 릴리스 게이트에 등록.

## Defects Found and Fixed

- 2026-09-05: T07/T08 에서 들어온 `.join('\n')` 두 곳이 파이썬 문자열 단계에서
  실제 개행으로 변환돼, 렌더된 페이지의 스크립트가 통째로 파싱 실패하고
  있었습니다. 탭·표·그래프가 전부 죽은 상태였는데 테스트 25개는 통과하고
  있었습니다 — 전부 마커 존재 검사였기 때문입니다. 수정과 함께, 렌더된
  스크립트에 개행으로 끊긴 문자열 리터럴이 있는지 보는 회귀 가드를
  넣었습니다. 브라우저에서 직접 확인하지 않았으면 못 찾았을 결함입니다.
- 2026-09-05: 오케스트레이터가 이관된 T10 을 `dispatchable` 로 계속
  제안했습니다. `[deferred → <issue>]` 를 상태로 인식하도록 고쳤습니다
  (Issue 112).

## Verification

- `tests.test_dashboard_production_views` + `tests.test_project_memory`: 101 tests, OK.
- `scripts/release_check.py`: 14/14 게이트 통과.
- 브라우저 확인: `?project=does-not-exist` → 경고 후 `?project=moduflow` 로
  정정, 선택기 비활성, 이슈 119건 렌더, 탭 전환 동작.

## Pending

- 이슈 상태 전환 (`backlog` → `done`). 사람 승인이 필요한 정규 전환입니다 (C6).

## Blockers

- None.

## Next Command

`product:issue 118-portfolio-mode-dashboard`
