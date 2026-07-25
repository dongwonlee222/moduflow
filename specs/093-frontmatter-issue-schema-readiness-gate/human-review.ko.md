# 한글 검토 패킷: 093-frontmatter-issue-schema-readiness-gate

> 영어 산출물은 canonical입니다. 이 파일은 사람이 PR을 검토하기 위한 한국어 읽기용 패킷입니다.

## 먼저 볼 것

- 대시보드: `memory/dashboard.html#issue-db`
- 이슈 상세: `memory/issue-093-frontmatter-issue-schema-readiness-gate.html`
- PR/로컬 마커: `local:093-frontmatter-issue-schema-readiness-gate:draft-pr-ready`
- 브랜치: `codex/093-frontmatter-issue-schema-readiness-gate`
- 리뷰어: `Dongwon Lee`

## 이슈 요약

- 제목: Issue 093: Frontmatter Issue Schema and Readiness/Dependency Gate
- 설명: Normalize YAML-frontmatter and Markdown issue formats through one parser, then block ready/execute routing when dependencies, definition readiness, lifecycle state, body status, or next command contradict one another.

## 사람이 확인할 내용

- 대시보드 DB에서 상태, 설명, 산출물 누락, 검증 플래그를 확인합니다.
- 이슈 상세 페이지에서 `한글` 탭을 먼저 보고, 필요한 경우 `English` 원문으로 내려갑니다.
- GitHub PR이 있으면 diff, conversation, status checks를 확인합니다.
- 아래 보류 조건에 해당하면 승인하지 말고 수정 요청합니다.

## 산출물 체크

| 산출물 | 용도 | 원문 | 한글 보기 |
| --- | --- | --- | --- |
| `spec.md` | 스펙 | `specs/093-frontmatter-issue-schema-readiness-gate/spec.md` | 가능 |
| `plan.md` | 계획 | `specs/093-frontmatter-issue-schema-readiness-gate/plan.md` | 요약/상세 한글 개요로 대체 |
| `tasks.md` | 작업 | `specs/093-frontmatter-issue-schema-readiness-gate/tasks.md` | 요약/상세 한글 개요로 대체 |
| `design.md` | 화면/설계 | 없음 | 요약/상세 한글 개요로 대체 |
| `status.md` | 상태/검증 | `specs/093-frontmatter-issue-schema-readiness-gate/status.md` | 요약/상세 한글 개요로 대체 |
| `review.md` | 리뷰 | `specs/093-frontmatter-issue-schema-readiness-gate/review.md` | 요약/상세 한글 개요로 대체 |
| `pr.md` | PR 핸드오프 | `specs/093-frontmatter-issue-schema-readiness-gate/pr.md` | 요약/상세 한글 개요로 대체 |
| `human-review.ko.md` | 한글 검토 패킷 | `specs/093-frontmatter-issue-schema-readiness-gate/human-review.ko.md` | 가능 |

## 검증 요약

Current as of the post-review merge of `main` into this branch. These supersede
the E2 numbers recorded above, which were taken at `ab682e3` before the review
fix and the merge.

| Check | Command | Result |
| --- | --- | --- |
| Full suite | `python3 -m unittest discover -s tests` | 741 passed, `OK` |
| Release gates | `python3 scripts/release_check.py .` | `valid: true`, zero errors, every sub-check `ok` |
| Lifecycle drift | `python3 scripts/project_lifecycle.py . --drift` | `[]` |
| Project artifacts | `python3 scripts/validate_project_artifacts.py .` | `valid: true`, zero errors |
| Package | `python3 scripts/validate_moduflow.py .` | passed |
| Commit capability | `python3 scripts/project_git_handoff.py . --operation commit` | `mode: local-git-write`, `ok: true` |
| GitHub PR preflight | `python3 scripts/project_pr.py . --github-preflight` | `ok: true`, `mode: github-draft-pr` |

Test count moved 737 to 741 through the four regression tests added while
clearing review condition 1.

Known gaps carried into the PR:

- The converge evidence step is not usable on this branch — it collected 1 of
  44 commits and no implementation file while reporting `errors: []`. Cause and
  scope are in review finding 1; tracked as issue `095`. Per
  `product-review.md` step 5 converge is reported, never gating.
- The review was coordinator-judged inline rather than dispatched to review
  subagents, so findings are single-reviewer judgments.

## no-issue 선언 (issue 075)

- 선언 없음 — 모든 동작 변경이 이슈에 연결되어 있습니다.

## 리뷰 결과

### 1. Converge evidence collects 1 of 44 commits, silently — CONFIRMED, important

`product-review.md` step 5 calls converge "the final evidence step." On this
branch it is nearly blind.

Evidence, from `scripts/project_converge.py --evidence --json` at review head:

- `commits`: **1** (of 44 on the branch)
- `files`: **7** — `.moduflow/state.json`, the issue file, `spec.md`,
  `spec.ko.md`, `workspace/dashboard.md`, `workspace/loop-state.json`,
  `workspace/roadmap.md`
- `errors`: `[]`

Not one implementation file is collected. `scripts/project_issue_schema.py`
(2,540 lines), all eight consumer changes, and every test file are absent. A
converge judge fed this evidence would rule on 093 having seen none of its
implementation, and nothing in the payload signals that 43 commits were
dropped.

Root cause is a resolver asymmetry. Two modules answer "which issue owns this
commit?" with different rules:

| Module | Sources |
| --- | --- |
| `scripts/linkage_check.py` | `trailer`, `branch` (`git branch --contains`) |
| `scripts/project_converge.py` | `trailer`, `merge-subject` |

`resolve_commits()` in `project_converge.py:168` has no branch fallback. On an
unmerged branch whose commits carry no `Issue:` trailer, only the single
trailer-bearing commit matches. `linkage_check` passes the same branch because
its branch fallback resolves all 44.

**Not a 093 regression.** `git diff --name-only main...HEAD` confirms 093
touches neither `project_converge.py` nor `linkage_check.py`. This is a
pre-existing defect surfaced by reviewing an unusually large branch. It should
be its own issue, not a merge blocker for 093 — but it does mean the converge
evidence for *this* review is not usable, and the review verdict rests on the
test suite, release gates, and inline reading instead.

Suggested fix direction: give `resolve_commits()` the same branch fallback
`linkage_check.resolve_issue_for_commit()` already has, or have it delegate to
that function outright. Either way, an unmatched-commit count belongs in the
payload so under-collection can never again be silent.

### 2. `infer_issue_phase` default flip — REFUTED as a fail-open, but exposed a real crash

**Resolution (2026-07-25, after the initial pass).** The fail-open reading below
was tested and does not hold. Probing `recommend_loop` directly:

| Case | Result |
| --- | --- |
| Checkbox-less issue, artifacts present, no readiness file | `phase=execute` but `status=needs_decision`, blocked by the delegation gate |
| Checkbox-less issue, no artifacts | Routed to `product:spec` by the structural gate |
| Issue file unreadable (`chmod 000`) | `ISSUE_SOURCE_UNREADABLE`, routed to `product:doctor` |
| Issue file a dangling symlink | `phase=issue`, inert |

Every route reaches a gate. The `status` to `execute` flip changes which phase
is *named*, not whether execution is authorized — approval still comes from the
delegation and structural gates. The hypothesised divergence between
`evaluate_project` and `infer_issue_phase` also does not exist for path
resolution: `issue_path()` and `list_normalized_issues()` both go through
`configured_project_paths()` with containment guards.

**What the probe did find** is a different, confirmed defect in the same seam.
`list_normalized_issues()` skipped any `*.md` path that existed but was not a
file, with no record and no diagnostic. A directory named `<issue-id>.md` was
therefore absent from evaluation, `evaluated_active_issue()` returned `None`,
and `infer_issue_phase()` reached `read_text()` on a directory — raising
`IsADirectoryError` out of `recommend_loop` instead of failing closed. This is
the same silent-skip class as finding 1, and it sits inside 093's own new
module.

Fixed in this review: the guard now admits any *existing* non-file path so
`parse_issue()`'s `OSError` handler produces a proper blocked record, matching
the permission case exactly. Dangling symlinks still resolve to nothing and stay
skipped. Four regression tests were added — two at the schema layer, two at the
loop layer, the latter also pinning the checkbox-less routing so it cannot
become fail-open later. Suite: 741 passing, `release_check` `valid: true`.

The original analysis is kept below for the record.

---

*Original reading (superseded by the resolution above):*

### 2-original. `infer_issue_phase` default flipped from inert to actionable — PLAUSIBLE, medium

`a50947b` ("advance loop after structural execution gate") changed
`scripts/project_loop.py:258`:

```
-    return "status"
+    return "status" if has_workflow_checkbox else "execute"
```

An issue file with no workflow checkboxes previously routed to
`product:status` (inert). It now routes to `product:execute` (actionable).

The concern is the ungated path. In `recommend_loop()`, when
`evaluated_active_issue()` returns `None` the structural gate is skipped
entirely and control falls through to `infer_issue_phase`. The issue-077
readiness gate that follows only blocks on a *present* verdict:

```
readiness = load_implementation_readiness(root, active_issue_id)
if readiness and readiness.get("status") == "not_ready":
```

A missing `implementation-readiness.json` does not block. So an issue file that
exists, is absent from the schema evaluation, carries no workflow checkboxes,
and has no readiness artifact would be routed to `product:execute` with no gate
having passed on it — a fail-open default inside a change set whose stated
principle is fail-closed.

I did not construct a repro, so this is **plausible, not confirmed**: it
depends on `evaluate_project()` omitting an issue file that exists on disk, and
I did not establish that this is reachable. Before merge, either demonstrate
that the state is unreachable and say so in `status.md`, or add a regression
test pinning the checkbox-less + unevaluated + no-readiness combination to a
non-executing route.

### 3. 43 of 44 commits carry no `Issue:` trailer — CONFIRMED, low (process)

Merged history on `main` uses the `Issue: <id>` trailer (for example
`docs: record issue 089 merge approval`). This branch uses a `fix(093):`
subject scope instead and omits the trailer on all but the first commit.

`release_check`'s linkage gate passes only because of the branch-name
fallback, which makes the linkage evidence positional rather than durable:

- Reviewing the branch in a detached-HEAD worktree fails the gate outright —
  reproduced during this review, all 44 commits reported unlinked.
- If the branch is renamed or deleted after merge, the fallback's input is
  gone.

Finding 1 is the concrete consequence. Adding trailers on future commits (or
at rebase time) makes both linkage and converge resolve the same way.

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
- 보류하면 `product:review 093-frontmatter-issue-schema-readiness-gate`로 되돌려 수정합니다.
