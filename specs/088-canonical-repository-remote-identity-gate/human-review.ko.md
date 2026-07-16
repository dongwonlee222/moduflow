# 한글 검토 패킷: 088-canonical-repository-remote-identity-gate

> 영어 산출물은 canonical입니다. 이 파일은 사람이 PR을 검토하기 위한 한국어 읽기용 패킷입니다.

## 먼저 볼 것

- 대시보드: `memory/dashboard.html#issue-db`
- 이슈 상세: `memory/issue-088-canonical-repository-remote-identity-gate.html`
- PR/로컬 마커: `https://github.com/dongwonlee222/moduflow/pull/25`
- 브랜치: `codex/088-canonical-repository-remote-identity-gate`
- 리뷰어: `Reviewer`

## 이슈 요약

- 제목: Issue 088: Canonical Repository/Remote Identity Gate
- 설명: Store the canonical repository, remote identity, and base branch in the project profile, then stop execute, PR, release, or push workflows before any write when the current repository does not match that identity.

## 사람이 확인할 내용

- 대시보드 DB에서 상태, 설명, 산출물 누락, 검증 플래그를 확인합니다.
- 이슈 상세 페이지에서 `한글` 탭을 먼저 보고, 필요한 경우 `English` 원문으로 내려갑니다.
- GitHub PR이 있으면 diff, conversation, status checks를 확인합니다.
- 아래 보류 조건에 해당하면 승인하지 말고 수정 요청합니다.

## 산출물 체크

| 산출물 | 용도 | 원문 | 한글 보기 |
| --- | --- | --- | --- |
| `spec.md` | 스펙 | `specs/088-canonical-repository-remote-identity-gate/spec.md` | 가능 |
| `plan.md` | 계획 | `specs/088-canonical-repository-remote-identity-gate/plan.md` | 요약/상세 한글 개요로 대체 |
| `tasks.md` | 작업 | `specs/088-canonical-repository-remote-identity-gate/tasks.md` | 요약/상세 한글 개요로 대체 |
| `design.md` | 화면/설계 | 없음 | 요약/상세 한글 개요로 대체 |
| `status.md` | 상태/검증 | `specs/088-canonical-repository-remote-identity-gate/status.md` | 요약/상세 한글 개요로 대체 |
| `review.md` | 리뷰 | `specs/088-canonical-repository-remote-identity-gate/review.md` | 요약/상세 한글 개요로 대체 |
| `pr.md` | PR 핸드오프 | `specs/088-canonical-repository-remote-identity-gate/pr.md` | 요약/상세 한글 개요로 대체 |
| `human-review.ko.md` | 한글 검토 패킷 | `specs/088-canonical-repository-remote-identity-gate/human-review.ko.md` | 가능 |

## 검증 요약

- `python3 -m unittest discover -s tests -p 'test_*.py'` — 528 tests passed.
- Focused identity/link/issue suites — 40 tests passed after the generic-provider capability fix.
- Focused identity/Git handoff suites — 35 tests passed after Git-root and API-fallback fixes.
- `python3 -m unittest tests.test_project_git_handoff -v` — 8 tests passed after the linked-worktree fix.
- `python3 scripts/spec_consistency.py . --issue-id 088-canonical-repository-remote-identity-gate` — 0 errors, 0 warnings.
- `python3 scripts/validate_moduflow.py .` — passed, 137 required files checked.
- `python3 scripts/validate_project_artifacts.py .` — valid, 0 errors.
- `python3 scripts/release_check.py .` — valid; validation, linkage, lint, security, version bump, tests, and doctor checks passed.
- Live `release` identity decision — `allowed: true`, status `match`, project root and provider repository/default branch/archive/fork evidence matched.

## no-issue 선언 (issue 075)

- 선언 없음 — 모든 동작 변경이 이슈에 연결되어 있습니다.

## 리뷰 결과

1. **Important — generic providers advertised GitHub write/release capability. Resolved.** `github_write` and `release` now require `provider == github`; a regression test proves a healthy generic remote can execute/commit/push but cannot create GitHub PRs or releases.
2. **Important — accidental parent Git roots could pass. Resolved.** The inspector now emits `git_root_mismatch`, reports mismatch status, and blocks every write capability when the observed Git root differs from the requested project root.
3. **Important — local-only/generic projects could select GitHub API commit fallback. Resolved.** `github_api_commit` now maps to the shared `github_write` capability, and the handoff checks it before calling `gh`.
4. **Important — linked worktrees were misclassified as locally unwritable. Resolved.** The handoff now resolves a `.git` worktree pointer to the actual Git directory before its non-destructive probe; the regression test was observed failing before the fix and passing afterward.

No unresolved critical or important code findings remain.

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
- 보류하면 `product:review 088-canonical-repository-remote-identity-gate`로 되돌려 수정합니다.
