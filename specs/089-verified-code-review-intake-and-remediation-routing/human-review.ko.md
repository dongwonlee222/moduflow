# 한글 검토 패킷: 089-verified-code-review-intake-and-remediation-routing

> 영어 산출물은 canonical입니다. 이 파일은 사람이 PR을 검토하기 위한 한국어 읽기용 패킷입니다.

## 먼저 볼 것

- 대시보드: `memory/dashboard.html#issue-db`
- 이슈 상세: `memory/issue-089-verified-code-review-intake-and-remediation-routing.html`
- PR/로컬 마커: `https://github.com/dongwonlee222/moduflow/pull/26`
- 브랜치: `codex/089-verified-code-review-intake-and-remediation-routing`
- 리뷰어: `Dongwon Lee`

## 이슈 요약

- 제목: Issue 089: Verified Code-Review Intake and Remediation Routing
- 설명: Verify external code-review findings before disposition, record evidence and conflicts, route accepted remediation by release risk, and generate reviewable GitHub issue candidates plus CognitiveDemand metadata.

## 사람이 확인할 내용

- 대시보드 DB에서 상태, 설명, 산출물 누락, 검증 플래그를 확인합니다.
- 이슈 상세 페이지에서 `한글` 탭을 먼저 보고, 필요한 경우 `English` 원문으로 내려갑니다.
- GitHub PR이 있으면 diff, conversation, status checks를 확인합니다.
- 아래 보류 조건에 해당하면 승인하지 말고 수정 요청합니다.

## 산출물 체크

| 산출물 | 용도 | 원문 | 한글 보기 |
| --- | --- | --- | --- |
| `spec.md` | 스펙 | `specs/089-verified-code-review-intake-and-remediation-routing/spec.md` | 가능 |
| `plan.md` | 계획 | `specs/089-verified-code-review-intake-and-remediation-routing/plan.md` | 요약/상세 한글 개요로 대체 |
| `tasks.md` | 작업 | `specs/089-verified-code-review-intake-and-remediation-routing/tasks.md` | 요약/상세 한글 개요로 대체 |
| `design.md` | 화면/설계 | 없음 | 요약/상세 한글 개요로 대체 |
| `status.md` | 상태/검증 | `specs/089-verified-code-review-intake-and-remediation-routing/status.md` | 요약/상세 한글 개요로 대체 |
| `review.md` | 리뷰 | `specs/089-verified-code-review-intake-and-remediation-routing/review.md` | 요약/상세 한글 개요로 대체 |
| `pr.md` | PR 핸드오프 | `specs/089-verified-code-review-intake-and-remediation-routing/pr.md` | 요약/상세 한글 개요로 대체 |
| `human-review.ko.md` | 한글 검토 패킷 | `specs/089-verified-code-review-intake-and-remediation-routing/human-review.ko.md` | 가능 |

## 검증 요약

- TDD implementation commits: `f3804b9`, `962cae3`, `d539f22`, `c794028`, `e7f84c4`, `4bad53d`.
- Synthetic manual intake returned `action: preview`, schema `moduflow.review-intake.v1`, a reference SHA-256, invoked only manual/Superpowers adapters, and skipped GitHub/security/Spec Kit.
- Dry-run left `workspace/reviews` absent; the user's external review source was neither read nor copied during dogfood.
- Source-adapter verification: 5 tests passed.
- Review-intake focused verification after review fixes: 47 tests passed.
- Full `unittest` discovery contains 582 tests; the release test gate passed with zero failures.
- Spec consistency: 0 errors, 0 warnings, 0 info findings.
- `validate_moduflow.py`: passed, 145 required files checked.
- `validate_project_artifacts.py`: passed; only pre-existing non-blocking optional/link-role warnings remain.
- `release_check.py`: passed all package, artifact, linkage, lint, security, version, test, doctor, and documentation gates.
- GitHub CI `test`: passed on Draft PR #26 before the review-fix commit; a fresh run is required after push.
- Staged review: four important findings reproduced and fixed; details in `review.md`.
- Dashboard and issue drill-down generated; local `file://` browser rendering was blocked by browser security policy and was not bypassed.
- Converge: 20 AC entries unverifiable because the evidence parser marked them non-parseable and truncated the bundle; non-blocking limitation recorded in `converge.md`.

## no-issue 선언 (issue 075)

- 선언 없음 — 모든 동작 변경이 이슈에 연결되어 있습니다.

## 리뷰 결과

1. **Important — source reviewer self-verification across run IDs** (`scripts/review_intake.py`)
   - Before: the same reviewer identity could become Verifier by changing only `run_id`.
   - Resolution: source-reviewer independence now compares actor identity independently of run ID; Router independence still compares the logical run.
   - Evidence: `test_source_reviewer_cannot_self_verify_with_new_run_id` failed before the fix and now passes.

2. **Important — partial acceptance could reuse the rejected remedy** (`scripts/review_intake.py`)
   - Before: a `partial_accept` candidate defaulted to the original recommendation.
   - Resolution: partial acceptance requires `accepted_scope`, records it in disposition history, and uses it as the candidate title.
   - Evidence: `test_partial_accept_requires_accepted_scope` and `test_partial_accept_candidate_uses_accepted_scope_not_original_remedy` failed before the fix and now pass.

3. **Important — review ID path traversal at decision intake** (`scripts/project_review.py`)
   - Before: `--apply-decisions --review-id ../../...` reached filesystem lookup before ID validation.
   - Resolution: decision intake validates the review ID before constructing the packet path.
   - Evidence: `test_decision_update_rejects_review_id_path_traversal` reproduced the escaped lookup and now passes with `review_id_invalid`.

4. **Important — final validation trusted manually edited disposition fields** (`scripts/review_intake.py`)
   - Before: `--validate --final` checked only the disposition state name.
   - Resolution: final validation now requires rationale, confirmed evidence for `accept`, and evidence plus accepted scope for `partial_accept`.
   - Evidence: three final-validation regression tests failed before the fix and now pass.

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
- 보류하면 `product:review 089-verified-code-review-intake-and-remediation-routing`로 되돌려 수정합니다.
