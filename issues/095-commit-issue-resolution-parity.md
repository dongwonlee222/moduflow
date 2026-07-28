# Issue 095: Commit-to-Issue Resolution Parity

**Status: active** — created 2026-07-25, started 2026-07-26; attribution redesign plan complete and ready for guarded execution.
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

- Both query directions use the same attribution index and policy:
  `trailer > branch > merge-subject`.
- A content commit has one owner under that precedence. A merge boundary may
  be attributed to multiple issues when it connects their histories.
- Cross-consumer parity proves that the commit named by `linkage_check.py` is
  among the issues that `project_converge.py` claims, and that every commit
  collected by converge resolves through the shared policy.
- Converge evidence for issue 093 includes
  `scripts/project_issue_schema.py`.
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
- [x] plan → active redesign `specs/095-commit-issue-resolution-parity/plan.md` + `tasks.md`; corrective history → `docs/superpowers/plans/2026-07-27-095-corrective-completion.md`
- [x] execute → corrective branch `codex/095-commit-issue-resolution-parity-fix`; shared resolver plus both consumer migrations
- [x] redesign → `docs/superpowers/specs/2026-07-27-095-attribution-architecture-redesign.md`
- [x] failure history → `specs/095-commit-issue-resolution-parity/failure-history.md`
- [x] implementation readiness → `specs/095-commit-issue-resolution-parity/implementation-readiness.json`
- [x] workers → `specs/095-commit-issue-resolution-parity/worker-plan.md` + `worker-plan.json`
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
- 2026-07-27: corrective TDD removed the four Round 9 expected failures, made issue discovery and graph failures fail closed, and applied one global precedence policy. Task 1 passed 92/92 focused tests; the five-module focused suite passed 195/195 with zero expected failures. Independent spec and quality reviews passed after two Important base-selection findings were fixed in `4f5d14a`. Full-suite and release gates remain the final review step.
- 2026-07-27: stopped the corrective patch loop after repeated review findings proved the global-base architecture unsound. The current branch reached 221/221 focused tests, but full discovery failed 2 of 885 because an unrelated historical octopus ambiguity leaked into the release gate; a separate review reproduced normal trunk advancement being misclassified as an ambiguous base. Approved redesign: per-issue fork points, graph-corroborated merge content, and caller-scoped diagnostics.
- 2026-07-27: preserved twenty failure families as an append-only design corpus. Future architecture requirements, plans, invariant tests, and Critical/Important review findings must trace to its `FH-*` ids; focused tests alone cannot close an entry.
- 2026-07-27: replaced the superseded global-base execution plan with six redesign streams: graph snapshot, per-topic fork points and stacked deltas, merge/content claims, scoped diagnostics, consumer scope integration, and invariant/full-gate review. Every stream names its failure-history inputs and RED/GREEN boundary.
- 2026-07-27: implementation readiness reported `ready`; the worker plan found overlapping graph/resolver files and shared-state risk across every task, so execution is sequential T01→T09. Dongwon Lee selected the recommended host-subagent workflow with per-task spec and quality reviews.
- 2026-07-27: completed T01 graph snapshot and failure-semantics boundary at `8068f98`. Review-discovered `FH-021` and `FH-022` now have executable regressions; the four direct consumer suites pass 105/105, and separate spec and quality reviews approved the result. T02 historical fork-point derivation is next.
- 2026-07-27: completed T02 historical fork-point derivation at `d25bbdd`. Independent review found and closed snapshot-time ref drift, incomplete criss-cross merge bases, and a missing comparable-candidate invariant as `FH-023`–`FH-025`; the direct consumer gate passes 117/117 with no open review finding. T03 stacked topic deltas are next.
- 2026-07-27: prepared an Issue 096 handoff proposing explicit `--evidence` writes, issue-id path traversal prevention, repo-external symlink rejection, and write-path announcements. Issue 095 does not modify Issue 096; its canonical issue must add these acceptance criteria, the dependency on 095, and the plugin-update gate before execution. The installed plugin remains on hold until both issues are safe.
- 2026-07-28: completed T03 stacked topic deltas at `2a000c0`. Repeated publication/base/diagnostic/range failures were preserved as `FH-002`, `FH-003`, `FH-010`, `FH-022`, and `FH-026`–`FH-031`; the cumulative direct-consumer gate passed 231/231 to terminal exit, and independent spec and quality reviews reported no open finding. T04 merge-boundary/content-side claims are next.
- 2026-07-28: completed T04 merge-boundary/content-side separation at `24bfd3c`. Review-discovered nested, unresolved, octopus-overlap, partial-side, and local-ambiguity failures were preserved under `FH-005` and `FH-016` before correction. The cumulative direct-consumer gate passed 267/267, and independent spec and quality reviews reported no open finding. T05 structured/scoped diagnostics are next.
- 2026-07-28: completed T05 structured/scoped diagnostics at `8221ea0`. The retired bare resolver exposed stale linkage fixtures (`FH-027`), and review found fatal ownership leakage (`FH-010`) plus duplicated compatibility errors (`FH-032`); all were recorded before correction. The cumulative gate passed 279/279 with clean independent spec and quality reviews. T06 release-SHA linkage scope is next.

## Links

- Spec: `specs/095-commit-issue-resolution-parity/spec.md`
- Redesign: `docs/superpowers/specs/2026-07-27-095-attribution-architecture-redesign.md`
- Failure history: `specs/095-commit-issue-resolution-parity/failure-history.md`
- Implementation readiness: `specs/095-commit-issue-resolution-parity/implementation-readiness.json`
- Worker plan: `specs/095-commit-issue-resolution-parity/worker-plan.md`
- Status: `specs/095-commit-issue-resolution-parity/status.md`
- Roadmap: `workspace/roadmap.md`

## Next Command

`product:execute 095-commit-issue-resolution-parity`
