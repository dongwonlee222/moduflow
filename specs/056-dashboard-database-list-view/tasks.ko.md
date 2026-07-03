# 작업: 대시보드 DB/리스트 뷰

> 이 파일은 영문 `tasks.md`의 한글 읽기용 sidecar입니다. canonical은 영문입니다.

Issue: `056-dashboard-database-list-view`
Plan: `specs/056-dashboard-database-list-view/plan.md`

## Stream A — 데이터 수집

- [ ] `scripts/project_memory.py`에 `_collect_issue_table(root)` 추가.
- [ ] 이슈 번호 추출 helper 추가.
- [ ] `## Next Command` parser 추가.
- [ ] 파일 존재 체크 기반 artifact coverage helper 추가.
- [ ] artifact coverage 기반 phase 추론 추가.
- [ ] attention flag helper 추가.
- [ ] issue graph edge 기반 relationship count 추가.
- [ ] updated date fallback 추가.

## Stream B — 대시보드 UI

- [ ] `render_project_view(root)`에 `ISSUE_ROWS` JSON embed.
- [ ] `PROJECT_VIEW_TEMPLATE`에 `이슈 DB` tab 추가.
- [ ] `이슈 DB`를 기본 탭으로 두고 `#issue-db` 지원.
- [ ] `#issues`, `#memory` 유지.
- [ ] compact toolbar 추가: search, view chip, group select, sort select.
- [ ] 기본 컬럼 table renderer 추가.
- [ ] status/attention filter 추가.
- [ ] sort 동작 추가.
- [ ] `issue-<id>.html` row link 추가.
- [ ] graph resize/fit은 graph tab에서만 실행되게 보장.

## Stream C — 테스트

- [ ] `_collect_issue_table` row count와 deterministic order 테스트.
- [ ] status/title/next command parsing 테스트.
- [ ] 한글 sidecar 포함 artifact coverage 테스트.
- [ ] spec/plan/review/PR/KO/next 누락 attention flag 테스트.
- [ ] linked memory count 테스트.
- [ ] `render_project_view`가 `이슈 DB`, `ISSUE_ROWS`, toolbar controls, row links를 포함하는지 테스트.
- [ ] 기존 project memory 테스트 재실행.

## Stream D — 검증

- [ ] `python3 -m unittest tests.test_project_memory` 실행.
- [ ] `python3 scripts/project_memory.py . --dashboard` 실행.
- [ ] `memory/dashboard.html` 시각 확인.
- [ ] `python3 scripts/validate_project_artifacts.py .` 실행.
- [ ] `python3 scripts/validate_moduflow.py .` 실행.
- [ ] `python3 scripts/release_check.py .` 실행.

## Stream E — 핸드오프

- [ ] 구현 요약을 issue session log에 기록.
- [ ] `workspace/roadmap.md`, `workspace/loop-state.json` 업데이트.
- [ ] execute 후 review artifacts 준비.
- [ ] 구현 후 다음 명령: `product:review 056-dashboard-database-list-view`.
