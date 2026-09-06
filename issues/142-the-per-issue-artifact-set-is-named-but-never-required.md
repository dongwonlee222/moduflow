# Issue 142: The Per-Issue Artifact Set Is Named But Never Required

**Status: backlog** — created 2026-09-06.
**Priority: p1**

## 요약

이슈 하나를 끝내려면 만들어야 하는 파일이 정해져 있습니다 — `spec` `plan`
`tasks` `review`. 코드에 이름까지 적혀 있습니다. 그런데 **그게 있는지 아무도 안
봅니다.** 끝난 이슈 95건 중 **네 개를 다 갖춘 건 25건(26%)**, **아예 하나도 없이
끝난 게 20건**입니다. 파일이 없어도 `done`이 되고, 검사도 통과하고, 출시도
됩니다.

## Summary

`scripts/project_issue_schema.py:44` names the set:

```python
_ARTIFACT_PHASES = ("spec", "plan", "tasks", "review", "release")
```

Coverage over that tuple is computed at `:1215`, `:1271` and `:1291` — and it is
used only to *derive* an issue's phase from which files happen to exist. Nothing
compares the set against what a completed issue should hold. `grep` for
`_ARTIFACT_PHASES` or `coverage[` in `scripts/validate_project_artifacts.py` and
`scripts/release_check.py` returns nothing.

The artifacts are a naming convention that the product reads and never requires.

## Source

- Type: owner question, 2026-09-06 — "이슈마다 만들어야 하는 파일들이 있을 거
  아니야 그런 것들도 확실히 정해져 있는지도 봐봐"
- Owner / decision maker: Dongwon Lee
- Measured against all 138 issue files in this repository the same day

## Opportunity

Every `done` issue in this repository, grouped by which of `spec.md`, `plan.md`,
`tasks.md`, `review.md` exist under `specs/<issue-id>/`:

| Count | Holds |
| --- | --- |
| 25 | spec, plan, tasks, review |
| 27 | spec, plan, tasks |
| 20 | **nothing** |
| 9 | spec, plan |
| 5 | spec |
| 4 | spec, plan, review |
| 3 | spec, tasks |
| 1 each | spec+review · review only |

Twenty-six percent of finished work carries the full set. Twenty-one percent
carries none of it.

The twenty with nothing:

```
008 009 010 012 013 033 036 037 042 044 055 061 064 065 066 067 119 125 126 127
```

### The exception that is not written down

Three of those twenty — 125, 126 and 127 — were closed during sessions on
2026-09-05 and 2026-09-06 under a stated "S-grade bugfix exception": a small
fix skips spec and plan, with issue 125 cited as the precedent.

**That exception exists nowhere in the repository.** `grep -rniE "S-grade|s급|
bugfix exception|skip.*spec"` across `commands/product-issue.md`,
`commands/product-execute.md` and `docs/*.md` returns nothing. It was agreed in
conversation and applied to real closures, and the next person — or the next
session — has no way to know it exists, what qualifies, or who may invoke it.

This is the more serious half. A missing rule produces inconsistent artifacts. A
rule that lives only in chat produces artifacts nobody can audit, because the
standard they were judged against was never written.

### Why it matters beyond tidiness

`review.md` is where an issue records whether the thing it built actually worked.
Twenty-seven issues have a spec, a plan and a task list, and no record of the
outcome. The product's own premise is a human reviewing what an agent did; for
those twenty-seven the review step was skipped and nothing noticed.

## Scope

### In

- Decide and record what a `done` issue must hold. The current tuple is a
  reasonable starting point but has never been ratified — `release.md` is in
  `_ARTIFACT_PHASES` and no issue in this repository has one.
- Write the S-grade exception down: what qualifies, which artifacts it waives,
  what it requires instead, and where the waiver is recorded **on the issue**
  so a reader can tell an exempt issue from a neglected one.
- A gate that fails a transition to `done` when the required set is absent and
  no waiver is declared. It runs at the transition, not in a later sweep.
- The failure message names the missing file and the command that creates it, in
  Korean.
- Decide what happens to the 95 already-closed issues. Recommended: nothing —
  they are history, and back-filling would manufacture documents nobody wrote.
  Whatever is decided must be stated, not left implicit.

### Out

- Judging whether a spec or review is any *good*. A machine can check a file
  exists and has a required heading. Issue 129 owns readability.
- Back-filling artifacts for closed issues. See above; if the decision changes,
  it is a separate issue.
- Deriving phase from file existence — that is issue 132's third defect and its
  fix is a prerequisite here, not part of this. A gate built on a phase value
  that an empty `plan.md` can promote would inherit the same hole.
- The `release.md` artifact's purpose. It is named in the tuple and unused; this
  issue may drop it from the required set but does not define it.

## Known Limit

A gate can require that `review.md` exists. It cannot require that anyone read
it. The measurable outcome here is that a closed issue carries a record of its
own outcome — not that the record is true.

And a waiver that is easy to declare becomes the default. Whatever the S-grade
rule turns out to be, it has to be narrower than "the author decided it was
small", or this issue will have replaced an unwritten exception with a rubber
stamp.

## Acceptance Criteria

- The required set for a `done` issue is stated in one place, and
  `commands/product-issue.md` points at it.
- A transition to `done` with a missing required artifact and no declared waiver
  fails, and the message names the file and the command that creates it.
- A declared waiver is visible on the issue itself, so an exempt issue and a
  neglected one are distinguishable by reading the file.
- The S-grade exception is written down with its qualifying conditions, and a
  fixture asserts a fix that does not qualify is refused.
- The 95 closed issues are unaffected, and a test asserts the gate does not
  retroactively invalidate them.
- `python3 scripts/release_check.py .` passes, `valid` checked at the top level.

## Verification

- Fixture: an issue taken to `done` with no `spec.md`; assert refusal and the
  message content.
- Fixture: the same issue with a declared S-grade waiver; assert it passes and
  the waiver is readable in the issue file.
- Fixture: an issue that does not qualify for the waiver but declares one;
  assert refusal.
- Run against the 138 live issues; assert zero existing `done` issues change
  state.
- `tests/test_project_issue_schema.py`, `tests/test_project_lifecycle.py`.

## Entry Points

- `scripts/project_issue_schema.py:44` — `_ARTIFACT_PHASES`, the set that is
  named
- `scripts/project_issue_schema.py:1215`, `:1271`, `:1291` — where coverage is
  computed and used only to derive phase
- `scripts/validate_project_artifacts.py` — no reference to the set
- `scripts/release_check.py` — no reference to the set
- `commands/product-issue.md` — where the requirement should be stated
- `templates/specs/` — `spec.md`, `plan.md`, `tasks.md`, `status.md`; note there
  is no `review.md` template

## Scope Fence

Do not satisfy this by generating the missing files. An auto-created `review.md`
that says nothing is worse than an absent one: it converts a visible gap into an
invisible one, and every count in this issue would then read as healthy.

## Workflow Tasks

- [ ] spec → `specs/<issue>/spec.md`
- [ ] plan → `specs/<issue>/plan.md` + `tasks.md`
- [ ] execute → required-set definition, waiver format, transition gate
- [ ] review → `specs/<issue>/review.md`

## Related Issues

- blocked_by: `132-the-canonical-status-line-has-no-protection` — its third
  defect is that phase comes from a file existing rather than its content. A
  completion gate built on that value inherits the hole, so 132 lands first.
- related: `129-required-sections-are-named-but-never-checked` (owns whether
  the artifacts can be read; this owns whether they exist),
  `129-required-sections-are-named-but-never-checked`,
  `120-silent-status-fallback-in-issue-parser`,
  `141-adoption-reports-success-on-an-incomplete-setup` (the same shape one
  level out — a step reports success against a standard narrower than the one
  the user has in mind)

## Next Command

`product:spec 142-the-per-issue-artifact-set-is-named-but-never-required`
