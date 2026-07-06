# 한글 검토 패킷: 074-sync-fetch-sandbox-handling

> 영어 산출물은 canonical입니다. 이 파일은 사람이 PR을 검토하기 위한 한국어 읽기용 패킷입니다.

## 먼저 볼 것

- 대시보드: `memory/dashboard.html#issue-db`
- 이슈 상세: `memory/issue-074-sync-fetch-sandbox-handling.html`
- PR/로컬 마커: `local:074-sync-fetch-sandbox-handling:draft-pr-ready`
- 브랜치: `codex/074-sync-fetch-sandbox-handling`
- 리뷰어: `Reviewer`

## 이슈 요약

- 제목: Issue 074: Sync Fetch Sandbox Handling
- 설명: `project_sync.py` should support approval-sensitive hosts where a top-level `git fetch` is allowed but a Python subprocess `git fetch --quiet` cannot write `.git/FETCH_HEAD`.

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
| `status.md` | 상태/검증 | `specs/074-sync-fetch-sandbox-handling/status.md` | 요약/상세 한글 개요로 대체 |
| `review.md` | 리뷰 | `specs/074-sync-fetch-sandbox-handling/review.md` | 요약/상세 한글 개요로 대체 |
| `pr.md` | PR 핸드오프 | `specs/074-sync-fetch-sandbox-handling/pr.md` | 요약/상세 한글 개요로 대체 |
| `human-review.ko.md` | 한글 검토 패킷 | `specs/074-sync-fetch-sandbox-handling/human-review.ko.md` | 가능 |

## 검증 요약

- `python3 scripts/project_sync.py . --no-fetch` reported local refs without the blocked internal fetch warning.
- `python3 -m unittest tests.test_project_sync -v` passed.
- `python3 scripts/release_check.py .` passed.
- `python3 scripts/validate_project_artifacts.py .` passed.

## 리뷰 결과

- Spec compliance: pass. The hotfix adds an explicit `--no-fetch` path while preserving default automatic fetch behavior.
- Quality: pass. The new behavior is small, parameterized, and covered by a focused regression test. Existing fetch failure and timeout behavior remains covered.
- Risk: low. The default code path remains auto-fetch; `--no-fetch` is opt-in for approval-sensitive hosts after a top-level `git fetch`.

## 보류 조건

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
- 보류하면 `product:review 074-sync-fetch-sandbox-handling`로 되돌려 수정합니다.
