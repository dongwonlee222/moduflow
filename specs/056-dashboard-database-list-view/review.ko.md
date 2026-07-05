# 리뷰: 대시보드 DB/리스트 뷰

> 이 파일은 영문 `review.md`의 한글 읽기용 sidecar입니다. canonical은 영문입니다.

Issue: `056-dashboard-database-list-view`
Reviewed: 2026-07-03
Result: passed; ready for PR
Next: `product:pr 056-dashboard-database-list-view`

## 리뷰 범위

- `scripts/project_memory.py`
- `tests/test_project_memory.py`
- `commands/product-dashboard.md`
- `specs/056-dashboard-database-list-view/*`
- 생성된 검토 화면:
  - `memory/dashboard.html`
  - `memory/issue-056-dashboard-database-list-view.html`

## 발견 사항

blocking 또는 important 이슈는 없습니다.

## 체크

### 구현 리뷰

- `_collect_issue_table(root)`가 issue 파일을 안정적인 순서로 나열합니다.
- row에 issue id, number, title, status, goal, phase, next command, artifact coverage, linked memory count, relationship count, attention flags, updated date, issue-panel href가 포함됩니다.
- artifact coverage는 파일 존재 체크를 사용하고 한글 sidecar를 signal로 취급합니다.
- `render_project_view(root)`가 `ISSUE_ROWS`를 embed하면서 기존 issue/memory graph payload를 유지합니다.
- `이슈 DB`가 기본 탭이고 `#issue-db`, `#issues`, `#memory` hash 이동을 지원합니다.
- 이슈 상세 패널에 `← 이슈 DB로 돌아가기` 링크가 추가되어 `dashboard.html#issue-db`로 돌아갑니다.

### 스펙 / PM 리뷰

- 승인된 spec/design과 일치합니다: Git 파일을 canonical로 두고 Notion/Jira/Linear/GitHub식 list/database view를 추가했습니다.
- zero-backend 구조를 유지합니다.
- write-back 편집, 외부 sync, 신규 DB를 추가하지 않았습니다.
- 기존 graph와 drill-down 동작을 유지합니다.

### QA 리뷰

- 새 테스트가 issue table row 추출, artifact sidecar, attention flag, rendered control, row link, issue-panel DB return link를 커버합니다.
- 기존 project memory 테스트가 계속 통과합니다.
- 전체 테스트가 통과합니다.

## 검증

- `python3 -m unittest tests.test_project_memory` — 통과.
- `python3 -m unittest discover -s tests` — 통과, 167 tests.
- `python3 scripts/project_memory.py . --dashboard` — 통과.
- `python3 scripts/project_memory.py . --issue 056-dashboard-database-list-view` — 통과.
- `python3 -m py_compile scripts/project_memory.py` — 통과.
- 생성 HTML에 `이슈 DB`, `ISSUE_ROWS`, search control, missing filter, 056 issue row link, issue-panel DB return link 포함 확인.
- `python3 scripts/validate_project_artifacts.py .` — 통과.
- `python3 scripts/validate_moduflow.py .` — 통과.
- `python3 scripts/release_check.py .` — 통과.

## 알려진 한계

- 이 환경에서는 Playwright browser binary가 없고 설치된 Chrome도 sandbox 제약으로 종료되어 브라우저 자동화 검증을 수행하지 못했습니다.
- 대신 생성된 dashboard와 issue drill-down을 로컬에서 열어 사람 검토용으로 확인했습니다.
- `리뷰필요` 필터는 v1 triage 목적상 review 또는 PR handoff가 빠진 row를 넓게 포함합니다.

## 권장

`product:pr 056-dashboard-database-list-view`로 진행합니다.
