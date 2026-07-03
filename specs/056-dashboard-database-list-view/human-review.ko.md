# 한글 검토 패킷: 056-dashboard-database-list-view

> 영어 산출물은 canonical입니다. 이 파일은 사람이 PR을 검토하기 위한 한국어 읽기용 패킷입니다.

## 먼저 볼 것

- 대시보드: `memory/dashboard.html#issue-db`
- 이슈 상세: `memory/issue-056-dashboard-database-list-view.html`
- PR/로컬 마커: `local:056-dashboard-db-list-view-spec:review-ready`
- 브랜치: `codex/056-dashboard-db-list-view-spec`
- 리뷰어: `Dongwon`

## 이슈 요약

- 제목: 056-dashboard-database-list-view
- 설명: 그래프만으로는 운영 스캔이 어려우므로 이슈를 검색, 필터, 정렬, 그룹화할 수 있는 DB/리스트 뷰를 추가합니다.

## 사람이 확인할 내용

- 대시보드 DB에서 상태, 설명, 산출물 누락, 검증 플래그를 확인합니다.
- 이슈 상세 페이지에서 `한글` 탭을 먼저 보고, 필요한 경우 `English` 원문으로 내려갑니다.
- GitHub PR이 있으면 diff, conversation, status checks를 확인합니다.
- 아래 보류 조건에 해당하면 승인하지 말고 수정 요청합니다.

## 산출물 체크

| 산출물 | 용도 | 원문 | 한글 보기 |
| --- | --- | --- | --- |
| `spec.md` | 스펙 | `specs/056-dashboard-database-list-view/spec.md` | 가능 |
| `plan.md` | 계획 | `specs/056-dashboard-database-list-view/plan.md` | 가능 |
| `tasks.md` | 작업 | `specs/056-dashboard-database-list-view/tasks.md` | 가능 |
| `design.md` | 화면/설계 | `specs/056-dashboard-database-list-view/design.md` | 가능 |
| `status.md` | 상태/검증 | `specs/056-dashboard-database-list-view/status.md` | 가능 |
| `review.md` | 리뷰 | `specs/056-dashboard-database-list-view/review.md` | 가능 |
| `pr.md` | PR 핸드오프 | `specs/056-dashboard-database-list-view/pr.md` | 요약/상세 한글 개요로 대체 |
| `human-review.ko.md` | 한글 검토 패킷 | `specs/056-dashboard-database-list-view/human-review.ko.md` | 가능 |

## 검증 요약

- `python3 -m unittest tests.test_project_memory`
- `python3 -m unittest discover -s tests`
- `python3 scripts/project_memory.py . --dashboard`
- `python3 -m py_compile scripts/project_memory.py`
- generated HTML contains `이슈 DB`, `ISSUE_ROWS`, search controls, missing filter, and 056 issue row link
- generated dashboard script parses with Node `new Function`
- `python3 scripts/validate_project_artifacts.py .`
- `python3 scripts/validate_moduflow.py .`
- `python3 scripts/release_check.py .`

## 리뷰 결과

No blocking or important issues found.

## 보류 조건

- 테스트 또는 release check가 실패했습니다.
- 대시보드/상세 페이지가 생성되지 않았거나 최신 변경을 반영하지 않습니다.
- PR diff가 이슈 범위를 벗어났습니다.
- 사람이 이해할 수 있는 한글 개요 또는 검토 패킷이 없습니다.
- merge/release 승인자가 명확하지 않습니다.

## 승인 체크리스트

- [ ] 대시보드 DB에서 이슈 상태와 설명을 확인했습니다.
- [ ] 이슈 상세 페이지의 `한글` 탭을 확인했습니다.
- [ ] PR diff 또는 로컬 변경 범위를 확인했습니다.
- [ ] 검증 결과가 통과했거나 실패 사유를 이해했습니다.
- [ ] 보류 조건에 해당하지 않습니다.

## 다음 액션

- 승인 가능하면 PR에서 approve 또는 로컬에 승인 기록을 남깁니다.
- 보류하면 `product:review 056-dashboard-database-list-view`로 되돌려 수정합니다.
