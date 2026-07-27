# 한글 검토 패킷: 095-commit-issue-resolution-parity

> 영어 산출물은 canonical입니다. 이 파일은 사람이 PR을 검토하기 위한 한국어 읽기용 패킷입니다.

## 먼저 볼 것

- 대시보드: `memory/dashboard.html#issue-db`
- 이슈 상세: `memory/issue-095-commit-issue-resolution-parity.html`
- PR/로컬 마커: `local:095-commit-issue-resolution-parity-fix:draft-pr-ready`
- 브랜치: `codex/095-commit-issue-resolution-parity-fix`
- 리뷰어: `Reviewer`

## 이슈 요약

- 제목: Issue 095: Commit-to-Issue Resolution Parity
- 설명: Make every consumer that asks "which issue owns this commit?" resolve it through one shared function, and make under-collection impossible to report silently.

## 사람이 확인할 내용

- 대시보드 DB에서 상태, 설명, 산출물 누락, 검증 플래그를 확인합니다.
- 이슈 상세 페이지에서 `한글` 탭을 먼저 보고, 필요한 경우 `English` 원문으로 내려갑니다.
- GitHub PR이 있으면 diff, conversation, status checks를 확인합니다.
- 아래 보류 조건에 해당하면 승인하지 말고 수정 요청합니다.

## 산출물 체크

| 산출물 | 용도 | 원문 | 한글 보기 |
| --- | --- | --- | --- |
| `spec.md` | 스펙 | `specs/095-commit-issue-resolution-parity/spec.md` | 요약/상세 한글 개요로 대체 |
| `plan.md` | 계획 | `specs/095-commit-issue-resolution-parity/plan.md` | 요약/상세 한글 개요로 대체 |
| `tasks.md` | 작업 | `specs/095-commit-issue-resolution-parity/tasks.md` | 요약/상세 한글 개요로 대체 |
| `design.md` | 화면/설계 | 없음 | 요약/상세 한글 개요로 대체 |
| `status.md` | 상태/검증 | `specs/095-commit-issue-resolution-parity/status.md` | 요약/상세 한글 개요로 대체 |
| `review.md` | 리뷰 | 없음 | 요약/상세 한글 개요로 대체 |
| `pr.md` | PR 핸드오프 | `specs/095-commit-issue-resolution-parity/pr.md` | 요약/상세 한글 개요로 대체 |
| `human-review.ko.md` | 한글 검토 패킷 | `specs/095-commit-issue-resolution-parity/human-review.ko.md` | 가능 |

## 검증 요약

- Task 1 집중 테스트: `92/92 PASS`
- 5개 모듈 집중 테스트: `195/195 PASS`
- 예상 실패(expected failure): `0`
- 산출물 검증: `valid: true`, `errors: []`
- lifecycle drift: `[]`
- `git diff --check`: 통과
- 독립 스펙 리뷰: Task 1, Task 2 모두 통과
- 독립 품질 리뷰: Task 1 통과. Task 2에서 발견한 Important 2건은
  `4f5d14a`에서 수정 후 재검토 통과
- 아직 남은 것: 교정 브랜치 전체 테스트, release check, 전체 브랜치
  최종 리뷰. 아직 완료 또는 릴리스 가능 상태로 판정하지 않습니다.

## no-issue 선언 (issue 075)

- 선언 없음 — 모든 동작 변경이 이슈에 연결되어 있습니다.

## 리뷰 결과

- 내용 커밋은 `trailer > branch > merge-subject` 전역 우선순위로 단일
  소유자를 가집니다.
- 여러 이슈의 이력을 연결하는 merge boundary는 복수 이슈에 귀속될 수
  있습니다.
- 두 소비자는 같은 attribution index와 같은 정책을 조회합니다.
- 교정 커밋: `21d1290`, `881d81d`, `ef149a8`, `4f5d14a`
- GitHub PR은 아직 생성되었다고 기록하지 않습니다. 현재는 로컬 Draft
  PR-ready 마커이며, merge에는 사람의 명시적 승인이 필요합니다.

## Issue 096 후속 제안

095는 Issue 096 파일을 수정하지 않습니다. 아래 항목은 Issue 096에 넘길
제안 범위입니다.

- `--evidence`의 명시적 쓰기 동작
- issue-id 경로 순회 차단
- 저장소 밖으로 해석되는 symlink 거부
- 모든 쓰기 경로 사전 고지

Issue 096 실행 전 canonical 이슈에 위 acceptance criteria, 095 의존성,
플러그인 업데이트 게이트를 추가해야 합니다. 설치된 ModuFlow 플러그인은
095와 096이 모두 안전해질 때까지 업데이트하지 않습니다.

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
- 보류하면 `product:review 095-commit-issue-resolution-parity`로 되돌려 수정합니다.
