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
- 설명: 평소의 “이슈 만들어줘” 경로는 빠르게 유지하면서, 요청이 애매하거나 위험하거나 전략적이거나 너무 넓을 때만 1-3개 질문으로 가볍게 shaping하는 라우터를 추가합니다.

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

- 2026-07-09: 구현 전 RED 확인 — 신규 intake 테스트가 `shaping_path` 부재와 애매한/전략 요청의 기존 `create_issue` 라우팅 때문에 실패했습니다.
- 2026-07-09: `python3 -m unittest tests.test_project_intake.ProjectIntakeTests -v` 통과, 10 tests OK.
- 2026-07-09: `python3 scripts/validate_moduflow.py .` 통과.
- 2026-07-09: `python3 scripts/validate_project_artifacts.py .` 통과. 기존 optional memory warning만 있습니다.
- 2026-07-09: `python3 scripts/release_check.py .` 통과.
- 2026-07-09: 확장 intake matrix 통과, 13 tests OK. README 개선, 버그 수정, 벤치마크 조사, 지표 진단, API 구현은 fast로 가고, 채택/전략 질문은 short/panel로 가는 것을 확인했습니다.

## no-issue 선언 (issue 075)

- 선언 없음 — 모든 동작 변경이 이슈에 연결되어 있습니다.

## 리뷰 결과

차단 이슈는 없습니다.

수용한 잔여 리스크:

- 첫 구현은 애매한/전략적 요청을 키워드 휴리스틱으로 판단합니다. 일부러 작고 테스트 가능하게 시작했으며, 실제 사용 예시가 쌓이면 분류를 더 정교하게 만들 수 있습니다.
- 명확한 실행 도메인(`dev`, `design`, `data`, `docs`, `ops`, `research`, `business`)이 있으면 요청에 `왜`나 `개선`이 들어가도 fast path로 둡니다. 정말 전략적인 질문에 실행 도메인 단어가 섞이는 경우 false negative가 생길 수 있어 후속 튜닝 때 봐야 합니다.
- panel shaping은 완전한 다중 에이전트 엔진이 아니라 압축된 라우팅 메타데이터와 문서 규칙입니다. 더 깊은 skill matrix/discipline 자동화는 079에서 다룹니다.
- 리뷰는 현재 세션에서 inline으로 수행했습니다. PR/merge 전 별도 리뷰 패스를 한 번 더 권장합니다.

후속 운영 원칙:

- 앞으로 라우터나 discipline 추천을 최적화할 때는 감으로 바꾸지 않고, 여러 실제 요청 예시를 모아 회귀 테스트로 고정하고 RED/GREEN을 확인한 뒤 문서에 규칙을 반영합니다.

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
