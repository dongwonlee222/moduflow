# 한글 검토 패킷: 079-plan-discipline-skill-matrix

> 영어 산출물은 canonical입니다. 이 파일은 사람이 PR을 검토하기 위한 한국어 읽기용 패킷입니다.

## 먼저 볼 것

- 대시보드: `memory/dashboard.html#issue-db`
- 이슈 상세: `memory/issue-079-plan-discipline-skill-matrix.html`
- PR/로컬 마커: `local:079-plan-discipline-skill-matrix:draft-pr-ready`
- 브랜치: `codex/079-plan-discipline-skill-matrix`
- 리뷰어: `Dongwon Lee`

## 이슈 요약

- 제목: Issue 079: Plan Discipline and Skill Matrix
- 설명: `product:plan`이 이슈나 작업별로 어떤 Superpowers discipline 또는 ModuFlow adapter skill을 써야 하는지 자동으로 드러내게 합니다. 에이전트가 writing-plans, TDD, review, verification, product design, data analysis, frontend QA 등을 언제 써야 하는지 계획 단계에서 알 수 있게 하는 작업입니다.

## 사람이 확인할 내용

- 대시보드 DB에서 상태, 설명, 산출물 누락, 검증 플래그를 확인합니다.
- 이슈 상세 페이지에서 `한글` 탭을 먼저 보고, 필요한 경우 `English` 원문으로 내려갑니다.
- GitHub PR이 있으면 diff, conversation, status checks를 확인합니다.
- 아래 보류 조건에 해당하면 승인하지 말고 수정 요청합니다.

## 산출물 체크

| 산출물 | 용도 | 원문 | 한글 보기 |
| --- | --- | --- | --- |
| `spec.md` | 스펙 | `specs/079-plan-discipline-skill-matrix/spec.md` | 요약/상세 한글 개요로 대체 |
| `plan.md` | 계획 | `specs/079-plan-discipline-skill-matrix/plan.md` | 요약/상세 한글 개요로 대체 |
| `tasks.md` | 작업 | `specs/079-plan-discipline-skill-matrix/tasks.md` | 요약/상세 한글 개요로 대체 |
| `design.md` | 화면/설계 | 없음 | 요약/상세 한글 개요로 대체 |
| `status.md` | 상태/검증 | `specs/079-plan-discipline-skill-matrix/status.md` | 요약/상세 한글 개요로 대체 |
| `review.md` | 리뷰 | `specs/079-plan-discipline-skill-matrix/review.md` | 요약/상세 한글 개요로 대체 |
| `pr.md` | PR 핸드오프 | `specs/079-plan-discipline-skill-matrix/pr.md` | 요약/상세 한글 개요로 대체 |
| `human-review.ko.md` | 한글 검토 패킷 | `specs/079-plan-discipline-skill-matrix/human-review.ko.md` | 가능 |

## 검증 요약

- 2026-07-09: `python3 scripts/spec_consistency.py . --issue-id 079-plan-discipline-skill-matrix` 통과, findings 0.
- 2026-07-09: `python3 scripts/validate_moduflow.py .` 통과.
- 2026-07-09: `python3 scripts/validate_project_artifacts.py .` 통과. 기존 optional memory warning만 있습니다.
- 2026-07-09: `python3 scripts/release_check.py .` 통과.

## no-issue 선언 (issue 075)

- 선언 없음 — 모든 동작 변경이 이슈에 연결되어 있습니다.

## 리뷰 결과

차단 이슈는 없습니다.

확인한 점:

- `product:plan`에 `Recommended Discipline` 섹션 요구사항과 예시 매트릭스가 추가됐습니다.
- Superpowers bridge에 writing-plans, TDD, product-design, data-analysis, Storybook/MSW, Playwright/QA, review, verification-before-completion 추천 기준이 들어갔습니다.
- PM router에는 spec 이후 plan이 추천 discipline을 드러내야 한다는 연결 규칙이 들어갔습니다.
- 079 자체 plan이 `Recommended Discipline` 섹션을 포함해 dogfood 역할을 합니다.
- 077 readiness gate와 078 frontend QA template scope는 건드리지 않았습니다.

수용한 잔여 리스크:

- v1은 문서/프롬프트 규칙입니다. 실제 자동 추천 엔진은 아직 없습니다.
- 추천 기준은 human-readable 형태라 당장 parser 검증은 하지 않습니다. 실제 plan 사례가 더 쌓이면 regression test로 고정할 수 있습니다.
- 기존 과거 plan들은 수정하지 않았습니다.

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
- 보류하면 `product:review 079-plan-discipline-skill-matrix`로 되돌려 수정합니다.
