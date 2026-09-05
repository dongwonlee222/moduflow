# 한글 검토 패킷: 125-bootstrap-dashboard-missing-active-issue-section

## 왜 필요한지

미기록 — 이슈·명세 근거로 작성하세요. 구현 내용이나 테스트 통과로 추정하지 않습니다.

## 해결해야 할 문제

미기록 — 이슈·명세 근거로 작성하세요. 구현 내용이나 테스트 통과로 추정하지 않습니다.

## 기대 효과

미기록 — 이슈·명세 근거로 작성하세요. 구현 내용이나 테스트 통과로 추정하지 않습니다.

> 영어 산출물은 canonical입니다. 이 파일은 사람이 PR을 검토하기 위한 한국어 읽기용 패킷입니다.

## 먼저 볼 것

- 대시보드: `memory/dashboard.html#issue-db`
- 이슈 상세: `memory/issue-125-bootstrap-dashboard-missing-active-issue-section.html`
- PR/로컬 마커: `local:125-bootstrap-dashboard-missing-active-issue-section:draft-pr-ready`
- 브랜치: `codex/125-bootstrap-dashboard-missing-active-issue-section`
- 리뷰어: `Reviewer`

## 이슈 요약

- 제목: Issue 125: Bootstrap Dashboard Missing Active Issue Section
- 설명: `project_lifecycle.render_dashboard_projection` raises
`ValueError: dashboard requires an Active Issue section` when the dashboard has
no `## Active Issue` heading. Both bootstrap paths write a dashboard without one,
so every session end fails for a newly created or newly migrated project.

## 사람이 확인할 내용

- 대시보드 DB에서 상태, 설명, 산출물 누락, 검증 플래그를 확인합니다.
- 이슈 상세 페이지에서 `한글` 탭을 먼저 보고, 필요한 경우 `English` 원문으로 내려갑니다.
- GitHub PR이 있으면 diff, conversation, status checks를 확인합니다.
- 아래 보류 조건에 해당하면 승인하지 말고 수정 요청합니다.

## 산출물 체크

| 산출물 | 용도 | 원문 | 한글 보기 |
| --- | --- | --- | --- |
| `spec.md` | 스펙 | 없음 | 요약/상세 한글 개요로 대체 |
| `plan.md` | 계획 | 없음 | 요약/상세 한글 개요로 대체 |
| `tasks.md` | 작업 | 없음 | 요약/상세 한글 개요로 대체 |
| `design.md` | 화면/설계 | 없음 | 요약/상세 한글 개요로 대체 |
| `status.md` | 상태/검증 | 없음 | 요약/상세 한글 개요로 대체 |
| `review.md` | 리뷰 | 없음 | 요약/상세 한글 개요로 대체 |
| `pr.md` | PR 핸드오프 | `specs/125-bootstrap-dashboard-missing-active-issue-section/pr.md` | 요약/상세 한글 개요로 대체 |
| `human-review.ko.md` | 한글 검토 패킷 | `specs/125-bootstrap-dashboard-missing-active-issue-section/human-review.ko.md` | 가능 |

## 검증 요약

- 검증 기록이 아직 `status.md`에 정리되지 않았습니다.

## no-issue 선언 (issue 075)

- 선언 없음 — 모든 동작 변경이 이슈에 연결되어 있습니다.

## 리뷰 결과

- 리뷰 결과가 아직 `review.md`에 정리되지 않았습니다.

## 보류 조건

- 왜 필요한지·해결해야 할 문제·기대 효과가 미기록이거나 근거 없이 추정됐습니다.
- 테스트 또는 release check가 실패했습니다.
- 대시보드/상세 페이지가 생성되지 않았거나 최신 변경을 반영하지 않습니다.
- PR diff가 이슈 범위를 벗어났습니다.
- 사람이 이해할 수 있는 한글 개요 또는 검토 패킷이 없습니다.
- 검토 패킷이 최신 PR diff 또는 로컬 변경 범위를 반영하지 않습니다.
- merge/release 승인자와 승인 근거가 명확하지 않습니다.

## 승인 체크리스트

- [ ] 대시보드 DB에서 이슈 상태와 설명을 확인했습니다.
- [ ] 이슈 상세 페이지의 `한글` 탭을 확인했습니다.
- [ ] PR diff 또는 로컬 변경 범위를 확인했습니다.
- [ ] 검증 결과가 통과했거나 실패 사유를 이해했습니다.
- [ ] release 대상이면 rollback/post-release check와 승인 기록을 확인했습니다.
- [ ] 보류 조건에 해당하지 않습니다.

## 다음 액션

- 승인 가능하면 PR에서 approve 또는 로컬에 승인 기록을 남깁니다.
- 보류하면 `product:review 125-bootstrap-dashboard-missing-active-issue-section`로 되돌려 수정합니다.
