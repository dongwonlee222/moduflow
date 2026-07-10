# 한글 검토 패킷: 085-project-production-records-and-playbooks

> 영어 산출물은 canonical입니다. 이 파일은 사람이 PR을 검토하기 위한 한국어 읽기용 패킷입니다.

## 먼저 볼 것

- 대시보드: `memory/dashboard.html#issue-db`
- 이슈 상세: `memory/issue-085-project-production-records-and-playbooks.html`
- PR/로컬 마커: `https://github.com/dongwonlee222/moduflow/pull/17`
- 브랜치: `codex/085-project-production-records-and-playbooks`
- 리뷰어: `Dongwon Lee`

## 이슈 요약

- 제목: Issue 085: Project Production Records and Playbooks
- 설명: 반복 제작물의 결과물, 판단, 실패, 재사용 패턴을 프로젝트별로 축적하고 사람 승인 플레이북으로 관리합니다.

## 사람이 확인할 내용

- 대시보드 DB에서 상태, 설명, 산출물 누락, 검증 플래그를 확인합니다.
- 이슈 상세 페이지에서 `한글` 탭을 먼저 보고, 필요한 경우 `English` 원문으로 내려갑니다.
- GitHub PR이 있으면 diff, conversation, status checks를 확인합니다.
- 아래 보류 조건에 해당하면 승인하지 말고 수정 요청합니다.

## 산출물 체크

| 산출물 | 용도 | 원문 | 한글 보기 |
| --- | --- | --- | --- |
| `spec.md` | 스펙 | `specs/085-project-production-records-and-playbooks/spec.md` | 가능 |
| `plan.md` | 계획 | `specs/085-project-production-records-and-playbooks/plan.md` | 요약/상세 한글 개요로 대체 |
| `tasks.md` | 작업 | `specs/085-project-production-records-and-playbooks/tasks.md` | 요약/상세 한글 개요로 대체 |
| `design.md` | 화면/설계 | 없음 | 요약/상세 한글 개요로 대체 |
| `status.md` | 상태/검증 | `specs/085-project-production-records-and-playbooks/status.md` | 요약/상세 한글 개요로 대체 |
| `review.md` | 리뷰 | `specs/085-project-production-records-and-playbooks/review.md` | 요약/상세 한글 개요로 대체 |
| `pr.md` | PR 핸드오프 | `specs/085-project-production-records-and-playbooks/pr.md` | 요약/상세 한글 개요로 대체 |
| `human-review.ko.md` | 한글 검토 패킷 | `specs/085-project-production-records-and-playbooks/human-review.ko.md` | 가능 |

## 검증 요약

- Focused production suite: 24 passed.
- Full repository suite: 483 passed.
- Spec consistency: 0 findings.
- Package, project, release, lint, and security gates: passed.

## no-issue 선언 (issue 075)

- 선언 없음 — 모든 동작 변경이 이슈에 연결되어 있습니다.

## 리뷰 결과

1. **High — same-day/title ID collision blocked distinct records.** Resolved by preserving the simple base ID for the first record and deterministically adding source context when a different capture key collides. Added a regression test proving both records are created without overwrite.
2. **Medium — CLI usage errors raised `SystemExit(2)` instead of returning `2`.** Resolved with a returning argument parser and a focused direct-`main(argv)` test.
3. **Medium — missing `--issue-id` and `--source-context` returned mutation failure `1`.** Resolved by classifying the missing source as a usage error and returning `2`.

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
- 보류하면 `product:review 085-project-production-records-and-playbooks`로 되돌려 수정합니다.
