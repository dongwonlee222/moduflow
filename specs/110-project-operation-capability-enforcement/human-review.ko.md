# 한글 검토 패킷: 110-project-operation-capability-enforcement

> 영어 산출물은 canonical입니다. 이 파일은 사람이 PR을 검토하기 위한 한국어 읽기용 패킷입니다.

## 먼저 볼 것

- 대시보드: `memory/dashboard.html#issue-db`
- 이슈 상세: `memory/issue-110-project-operation-capability-enforcement.html`
- PR/로컬 마커: `https://github.com/dongwonlee222/moduflow/pull/42`
- 브랜치: `codex/110-project-operation-capability-enforcement`
- 리뷰어: `Reviewer`

## 이슈 요약

- 제목: Issue 110: Project Operation Capability Enforcement
- 설명: Separate project discovery from operation authorization by returning explicit project status and read/write/execute/publish capabilities, then enforcing those capabilities before every mutating workflow.

## 사람이 확인할 내용

- 대시보드 DB에서 상태, 설명, 산출물 누락, 검증 플래그를 확인합니다.
- 이슈 상세 페이지에서 `한글` 탭을 먼저 보고, 필요한 경우 `English` 원문으로 내려갑니다.
- GitHub PR이 있으면 diff, conversation, status checks를 확인합니다.
- 아래 보류 조건에 해당하면 승인하지 말고 수정 요청합니다.

## 산출물 체크

| 산출물 | 용도 | 원문 | 한글 보기 |
| --- | --- | --- | --- |
| `spec.md` | 스펙 | `specs/110-project-operation-capability-enforcement/spec.md` | 가능 |
| `plan.md` | 계획 | `specs/110-project-operation-capability-enforcement/plan.md` | 요약/상세 한글 개요로 대체 |
| `tasks.md` | 작업 | `specs/110-project-operation-capability-enforcement/tasks.md` | 요약/상세 한글 개요로 대체 |
| `design.md` | 화면/설계 | 없음 | 요약/상세 한글 개요로 대체 |
| `status.md` | 상태/검증 | `specs/110-project-operation-capability-enforcement/status.md` | 요약/상세 한글 개요로 대체 |
| `review.md` | 리뷰 | `specs/110-project-operation-capability-enforcement/review.md` | 요약/상세 한글 개요로 대체 |
| `pr.md` | PR 핸드오프 | `specs/110-project-operation-capability-enforcement/pr.md` | 요약/상세 한글 개요로 대체 |
| `human-review.ko.md` | 한글 검토 패킷 | `specs/110-project-operation-capability-enforcement/human-review.ko.md` | 가능 |

## 검증 요약

- Issue 110 focused suites: 572/572 passed.
- Full discovery: 1,339/1,339 passed.
- Project artifact validation: `valid: true`, `errors: []`.
- Spec consistency: 0 errors, 0 warnings, 0 info.
- Lifecycle drift: `[]` before review artifact synchronization.
- Mutation audit: `valid: true`; 64/64 classified with every gap count at zero.
- Diff hygiene: `git diff --check` clean.
- Independent code review: merge-ready for implementation; no Critical or Important finding remains.
- Source release check: `valid: true`, `errors: []`; operation audit, version bump, focused tests, validation, linkage, lint, and security checks passed.

## no-issue 선언 (issue 075)

- 선언 없음 — 모든 동작 변경이 이슈에 연결되어 있습니다.

## 리뷰 결과

1. **Resolved — mutable capability projection could fail open.** Authorization now recomputes the expected policy from observed inputs and validates the complete normalized projection before allowing an operation.
2. **Resolved — public team-state writer bypassed its parent guard.** `write_team_state()` now resolves context and enforces `execute` before directory or file creation.
3. **Resolved — static audit proved only guard presence.** It now verifies operation literals, guard dominance, direct/nested helper ownership, and broader filesystem/network surfaces.
4. **Resolved — external-control was initially too broad.** It is publish-only and network-only; mixed file/Git mutation fails the audit.
5. **Resolved — open flags/modes could hide behind assignments.** Reaching assignments are evaluated at call position; multiple, augmented, unresolved, and nested-scope cases fail closed as dynamic mutation.
6. **Resolved — explicit-root compatibility used raw trust alone.** It now requires `explicit_root` provenance and exact `active/project-local` synthetic inputs.
7. **Resolved — Antigravity canonical control path and nested rewrite helper were not fully classified.** Both are explicitly reviewed, and helper calls are dominated by the outer execute guard.
8. **No open Critical or Important finding** remains after independent re-review of `60f7651`.

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

- Dongwon Lee가 Codex 대화에서 병합을 명시적으로 승인했고, PR #42는 CI 통과 후 `5f173f4`로 병합됐습니다.
- 다음 작업은 `product:plan 103-atomic-lifecycle-state-transaction`입니다.
