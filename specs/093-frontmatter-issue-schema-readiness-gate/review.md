# Review: 093-frontmatter-issue-schema-readiness-gate

Reviewer: Claude Opus 5 (coordinator-inline)
Date: 2026-07-25
Head reviewed: `098c0f3a61942fd5b1d1f56b0141f65dcfca1016`
Base: `4808fccc526647edc481d0f11775bd1b62b37ee7` (`main`)

## Review mode limitation

`product-review.md` prescribes dispatching `qa-reviewer` and
`pm-strategist` / `spec-architect` subagents. This session ran with subagent
dispatch withheld, so review concerns were judged inline by the coordinator.
The command's documented fallback for the converge step ("coordinator judges
and records the limitation if dispatch is unavailable") is applied here to the
whole review. Findings below are therefore single-reviewer judgments, not
independent multi-reviewer consensus.

## Verification reproduced

Re-ran at review time, in the issue's own worktree with the branch attached:

- `python3 -m unittest discover -s tests` — 737 passed, `OK`.
- `python3 scripts/release_check.py .` — `valid: true`, zero errors, every
  sub-check `ok` including `linkage_gate` and `version_bump_gate`.
- Working tree clean at `098c0f3`.

The E2 numbers recorded in `status.md` reproduce exactly.

## Findings

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

### 2. `infer_issue_phase` default flipped from inert to actionable — PLAUSIBLE, medium

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

## Acceptance criteria

Checked against `spec.md`. All eight criteria are covered by tests in
`tests/test_project_issue_schema.py` (92 focused tests pass), including the
BIZ-038/039-blocked and BIZ-040-to-spec fixtures. The "every consumer uses the
shared normalized parser" criterion is additionally pinned by
`ProjectIssueSchemaCrossConsumerParityTests`, and `git diff --check` plus the
static search recorded in `status.md` show no second parser surviving in the
consumers.

## Reference improvements

Reference improvements: none found.

## Verdict

**Approve with conditions.**

The implementation is sound on the evidence available: 737 tests pass, all
release gates are green, the shared-parser boundary holds, and the
read-only migration dogfood is proven non-mutating by a before/after digest.

Conditions before merge:

1. Resolve finding 2 — either a reachability argument recorded in `status.md`
   or a regression test.
2. Register finding 1 as a new issue. It is pre-existing and must not block
   093, but it should not merge unrecorded, because it silently weakens the
   review step for every future issue.

Finding 3 is advisory.
