# Issue 095: Commit-to-Issue Resolution Parity

**Status: active** — created 2026-07-25, started 2026-07-26; stream A implemented.
**Priority: p1**
**Blocked-by:**

## Summary

Make every consumer that asks "which issue owns this commit?" resolve it through one shared function, and make under-collection impossible to report silently.

## Source

- Type: finding from the independent review of issue 093
- Link: `specs/093-frontmatter-issue-schema-readiness-gate/review.md` finding 1
- Date: 2026-07-25

## Problem

Two modules answer the same question with different rules:

| Module | Sources recognized |
| --- | --- |
| `scripts/linkage_check.py` | `trailer`, `branch` (`git branch --contains`) |
| `scripts/project_converge.py` | `trailer`, `merge-subject` |

`resolve_commits()` in `project_converge.py:168` has no branch fallback. On an
unmerged branch whose commits carry no `Issue:` trailer, only trailer-bearing
commits are collected.

Measured on issue 093's branch at head `098c0f3`:

- `commits`: 1 of 44
- `files`: 7, none of them implementation — no `project_issue_schema.py`
  (2,540 lines), no consumer change, no test
- `errors`: `[]`

`product-review.md` step 5 calls converge "the final evidence step." A judge
fed that payload would rule on 093 having seen none of its implementation, and
nothing in the payload signals that 43 commits were dropped. Adding one
trailer-bearing commit during the review moved the count from 1 to 2,
confirming the mechanism directly.

Meanwhile `release_check`'s linkage gate passed the same branch, because its
branch fallback resolves all 44. So the two gates disagree about the same
history, and the weaker one is the one feeding review evidence.

This is the failure class issue 093 was built to eliminate — a gate reporting
success while the evidence contradicting it sits in reach — applied to commits
rather than issues.

## Product Decision

- One shared resolver owns commit-to-issue resolution. `project_converge.py`
  delegates to it rather than carrying a second implementation.
- Collection results report how many commits in range went unmatched. A
  reviewer must never have to count commits by hand to notice a gap.
- Branch-name resolution stays a fallback, not the primary channel: it is
  positional evidence that disappears when a branch is renamed or deleted, and
  it fails outright in a detached-HEAD worktree.

## Scope

### In

- A single commit-to-issue resolution path shared by `linkage_check.py` and
  `project_converge.py`.
- An unmatched-commit count, and the resolution source per commit, in the
  converge evidence payload.
- Regression tests covering: trailer-only history, branch-only history, mixed
  history, detached HEAD, and post-merge branch deletion.

### Out

- Changing the `Issue:` trailer format or the `codex/<issue-id>` branch
  convention.
- Rewriting existing commit history to add trailers.
- Making converge gate the review verdict — it stays reported, never blocking.

## Acceptance Criteria

- `project_converge.py` and `linkage_check.py` resolve identical commit sets
  for the same range, proven by a parity test.
- Converge evidence on issue 093's branch collects all 44 commits and includes
  `project_issue_schema.py`.
- The evidence payload reports an unmatched-commit count; a run that drops
  commits cannot report an empty `errors` list with no other signal.
- Resolution succeeds in a detached-HEAD worktree for trailer-bearing commits
  and reports the limitation for branch-only ones.
- `python3 scripts/release_check.py .` passes.

## Verification

- `python3 -m unittest tests.test_linkage_check tests.test_project_converge -v`
- `python3 scripts/project_converge.py . --issue-id 093-frontmatter-issue-schema-readiness-gate --evidence --json`
- `python3 scripts/release_check.py .`

## Entry Points

- `scripts/project_converge.py`
- `scripts/linkage_check.py`
- `tests/test_project_converge.py`
- `tests/test_linkage_check.py`

## Scope Fence

Do not change the trailer or branch-naming conventions, and do not rewrite
existing history. Do not make converge gate the review verdict.

## Workflow Tasks

- [x] spec → `specs/095-commit-issue-resolution-parity/spec.md`
- [x] plan → `specs/095-commit-issue-resolution-parity/plan.md` + `tasks.md`
- [ ] execute → PR / commits (stream A done: `scripts/commit_resolution.py`)
- [ ] review → review notes

## Related Issues

- blocks:
- blocked_by:
- duplicates:
- follows_up: `093-frontmatter-issue-schema-readiness-gate`
- supersedes:
- related: `071-spec-code-converge-check`, `075-issue-less-context-capture`

## Sessions

- 2026-07-25: found during the independent review of issue 093.
- 2026-07-26: stream A landed. Implementing it surfaced a rule the spec had assumed away — branch containment is not branch authorship. `git rev-list <branch>` attributed 279 commits to issue 093 where the branch contributed 52, because a branch cut from main carries all of main as ancestors; `--not main` yields 0 once merged. Merged work is now delimited by the merge commit's second-parent side minus its first-parent side, computed from the log records already parsed, so it adds no subprocess. Converge-equivalent collection on 093 moved from 10 to 57 and includes `scripts/project_issue_schema.py`.
- 2026-07-26: reproduced on `main` at `6bca2b4` after 093 merged — converge collects 10 commits (trailer 9, merge-subject 1) with `errors: []`, while `linkage_check` attributes 53 over the same window. Merging raised the count but did not close the gap, confirming the defect is structural rather than a branch-lifetime artifact. Spec and plan written.

## Links

- Spec: `specs/095-commit-issue-resolution-parity/spec.md`
- Status: `specs/095-commit-issue-resolution-parity/status.md`
- Roadmap: `workspace/roadmap.md`

## Next Command

`/product:execute 095-commit-issue-resolution-parity`
