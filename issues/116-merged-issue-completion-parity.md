# Issue 116: Merged Issue Completion Parity

**Status: backlog** — created 2026-09-04.
**Priority: p1**
**Blocked-by:**

## Summary

Report an issue whose commits are merged into the canonical remote branch while its own lifecycle state is still `backlog` or `active`, so a completed delivery cannot sit unrecorded until someone notices.

## Source

- Type: observed failure during the 0.3.62 release
- Owner / decision maker: Dongwon Lee
- Observed: 2026-09-04. After PRs #48 and #49 merged, Issue 091 had 15 linked commits on `origin/main` and Issue 115 had 1, and both issues still read `Status: backlog`. Nothing reported the contradiction; `product:status` surfaced it only because a human asked what was inconsistent.

## Opportunity

Issue 095 already resolved the hard half. One shared attribution index answers "which issue owns this commit" under `trailer > branch > merge-subject` precedence, and cross-consumer parity is enforced. Counting the 15 and 1 above used exactly that index.

The reverse question has no owner. Nothing asks "this issue has merged commits — why is it not done?". Recording completion is a manual step today, and a forgotten step leaves the repository claiming work is unstarted while it ships in the released package.

## Scope

### In

- Detect issues with commits merged into the canonical remote branch whose lifecycle state is not `done`, using the Issue 095 attribution index; add no second attribution path.
- Report the count of merged commits and the current state so the reader can judge, rather than asserting the issue should be closed.
- Surface it where lifecycle inconsistencies already surface, following the existing diagnostic and recommendation shape.
- Treat an issue that is deliberately open with partial delivery as a normal reportable state, not an error.

### Out

- Automatically transitioning any issue to `done`. Lifecycle transitions stay human-approved and pass through the existing transaction.
- A second attribution index, precedence rule, or commit parser.
- Blocking a release on this signal before the reported cases are reviewed.
- Judging whether the merged work actually satisfies the issue's acceptance criteria.

## Acceptance Criteria

- An issue with merged commits on the canonical remote branch and a non-`done` state is reported with its issue id, merged commit count and current state.
- An issue that is `done`, and an issue with no merged commits, are both silent.
- Attribution comes from the Issue 095 shared index; no new precedence rule is introduced.
- Nothing transitions an issue automatically; the report names the next command and stops.
- A deliberately partial delivery can be acknowledged without the report treating it as a defect.
- `python3 scripts/release_check.py .` passes.

## Verification

- `python3 -m unittest tests.test_linkage_check tests.test_project_doctor -v`
- `python3 scripts/validate_project_artifacts.py .`
- `python3 scripts/release_check.py .`

## Entry Points

- `scripts/linkage_check.py`
- `scripts/project_doctor.py`
- `tests/test_linkage_check.py`

## Scope Fence

This reports a contradiction between merged history and recorded lifecycle state. It does not close issues, does not judge delivery quality, and does not replace the human approval that owns lifecycle transitions.

## Workflow Tasks

- [ ] spec → `specs/116-merged-issue-completion-parity/spec.md`
- [ ] plan → `specs/116-merged-issue-completion-parity/plan.md`
- [ ] execute → detection, reporting and focused tests
- [ ] review → `specs/116-merged-issue-completion-parity/review.md`

## Related Issues

- blocks:
- blocked_by:
- duplicates:
- follows_up: `095-commit-issue-resolution-parity`
- supersedes:
- related: `048-artifact-lifecycle-sync`, `093-frontmatter-issue-schema-readiness-gate`, `099-vendor-and-host-sync-drift-detection`, `105-schema-migration-and-doctor-triage`

## Links

- Goal: `workspace/goal.md`
- Roadmap: `workspace/roadmap.md`
- Observed during: `specs/091-reproducible-analysis-runs-and-template-pack/status.md`

## Next Command

`product:spec 116-merged-issue-completion-parity`.
