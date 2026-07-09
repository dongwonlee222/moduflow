# 한글 검토 패킷: 076-product-context-interview-and-readiness-loop

> 영어 산출물은 canonical입니다. 이 파일은 사람이 PR을 검토하기 위한 한국어 읽기용 패킷입니다.

## 먼저 볼 것

- 대시보드: `memory/dashboard.html#issue-db`
- 이슈 상세: `memory/issue-076-product-context-interview-and-readiness-loop.html`
- PR/로컬 마커: `https://github.com/dongwonlee222/moduflow/pull/12`
- 브랜치: `codex/076-product-context-interview-and-readiness-loop`
- 원격 브랜치: `origin/codex/076-product-context-interview-and-readiness-loop`
- GitHub PR 생성 URL: `https://github.com/dongwonlee222/moduflow/pull/12`
- 리뷰어: `Dongwon Lee`

## 이슈 요약

- 제목: Issue 076: Fast Path Shaping Router
- 설명: Keep the normal "make an issue" path fast, while adding a lightweight shaping router that asks 1-3 questions only when a request is vague, risky, strategic, or too broad to turn into an agent-ready issue.

## 사람이 확인할 내용

- 대시보드 DB에서 상태, 설명, 산출물 누락, 검증 플래그를 확인합니다.
- 이슈 상세 페이지에서 `한글` 탭을 먼저 보고, 필요한 경우 `English` 원문으로 내려갑니다.
- GitHub PR이 있으면 diff, conversation, status checks를 확인합니다.
- 아래 보류 조건에 해당하면 승인하지 말고 수정 요청합니다.

## 산출물 체크

| 산출물 | 용도 | 원문 | 한글 보기 |
| --- | --- | --- | --- |
| `spec.md` | 스펙 | `specs/076-product-context-interview-and-readiness-loop/spec.md` | 요약/상세 한글 개요로 대체 |
| `plan.md` | 계획 | `specs/076-product-context-interview-and-readiness-loop/plan.md` | 요약/상세 한글 개요로 대체 |
| `tasks.md` | 작업 | `specs/076-product-context-interview-and-readiness-loop/tasks.md` | 요약/상세 한글 개요로 대체 |
| `design.md` | 화면/설계 | 없음 | 요약/상세 한글 개요로 대체 |
| `status.md` | 상태/검증 | `specs/076-product-context-interview-and-readiness-loop/status.md` | 요약/상세 한글 개요로 대체 |
| `review.md` | 리뷰 | `specs/076-product-context-interview-and-readiness-loop/review.md` | 요약/상세 한글 개요로 대체 |
| `pr.md` | PR 핸드오프 | `specs/076-product-context-interview-and-readiness-loop/pr.md` | 요약/상세 한글 개요로 대체 |
| `human-review.ko.md` | 한글 검토 패킷 | `specs/076-product-context-interview-and-readiness-loop/human-review.ko.md` | 가능 |

## 검증 요약

- 2026-07-09: RED confirmed before implementation: new intake tests failed on missing `shaping_path` and old `create_issue` routing for ambiguous/strategic requests.
- 2026-07-09: `python3 -m unittest tests.test_project_intake.ProjectIntakeTests -v` passed, 10 tests OK.
- 2026-07-09: `python3 scripts/validate_moduflow.py .` passed.
- 2026-07-09: `python3 scripts/validate_project_artifacts.py .` passed with only the existing optional memory warning.
- 2026-07-09: `python3 scripts/release_check.py .` passed.
- 2026-07-09: Expanded intake matrix passed, 13 tests OK. Manual case sweep confirmed README improvement, bug fix, benchmark research, metric diagnostics, and API implementation route fast; adoption and strategy questions route short/panel.

## no-issue 선언 (issue 075)

- 선언 없음 — 모든 동작 변경이 이슈에 연결되어 있습니다.

## 리뷰 결과

No blocking issues found.

Accepted residual risks:

- The first implementation uses keyword heuristics for ambiguous/strategic requests. This is intentionally small and testable; richer classification can follow after real usage examples.
- The heuristic now treats clear execution domains (`dev`, `design`, `data`, `docs`, `ops`, `research`, `business`) as fast path even when the request contains words like "왜" or "개선"; this should be watched against future false negatives where a domain word appears in a genuinely strategic question.
- Panel shaping is represented as compressed routing metadata and docs, not a full multi-agent execution engine. That keeps 076 scoped; deeper skill-matrix/discipline automation belongs to 079.
- Review was performed inline in the current session. A separate review pass is still recommended before PR/merge.

Follow-on operating rule:

- Future routing or discipline optimization should be treated as data-backed tuning: collect representative request examples, encode them as regression tests, verify RED/GREEN, then update docs with the resulting rule.

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
- 보류하면 `product:review 076-product-context-interview-and-readiness-loop`로 되돌려 수정합니다.
