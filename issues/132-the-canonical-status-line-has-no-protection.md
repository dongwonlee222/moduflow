# Issue 132: The Canonical Status Line Has No Protection

**Status: backlog** — created 2026-09-06.
**Priority: p1**

## 요약

라이프사이클의 **정본은 이슈 파일의 `**Status:**` 한 줄**입니다. 그런데 그 한 줄에는
아무 보호가 없고, 그것을 베낀 사본(`state.json`·대시보드)에는 7,524줄짜리 트랜잭션과
저널·롤백이 붙어 있습니다. **보호가 거꾸로 걸려 있습니다.** 그래서 세 가지가 깨져
있습니다 — `superseded`로 가려면 손으로 파일을 고쳐야 하고, `pause`는 상태를 안 바꾸고,
**빈 `plan.md` 하나로 단계가 "계획 완료"로 올라갑니다.**

## Summary

`scripts/project_lifecycle.py:2-8` states the rule: the code "does NOT write back
to issue files (canonical source is human-authored)." Everything downstream —
`.moduflow/state.json`, `workspace/dashboard.md`, `workspace/loop-state.json`, the
issue index — is a projection, and every write to those runs through
`apply_lifecycle_transaction` with a journal and rollback.

The projections are transactional. The source they project is a hand-edited line
of Markdown with no schema enforcement at write time.

## Source

- Type: architecture review, 2026-09-06
- Owner / decision maker: Dongwon Lee
- Found while auditing the process end to end after a week in which three
  lifecycle defects (125, 126, 127) all traced back to state disagreement

## Opportunity

Three symptoms, each verified:

### 1. `superseded` can only be entered by hand

`commands/product-issue.md:14` declares four lifecycle states and
`scripts/project_issue_schema.py:612` recognises `superseded`, treating it at
`:1531` as satisfying a dependency. But `project_lifecycle_transaction.py:142`
defines `_LIFECYCLES` as `{backlog, active, done}`, and
`project_lifecycle.py:848`'s `--target-status` offers the same three.

Seven issues in this repository are `superseded-by-*` today. Every one of them
got there by someone editing Markdown, outside the transaction that exists to
make exactly this kind of change safe.

### 2. `pause` does not pause anything

`project_lifecycle_transaction.py:143-147` maps `start`, `pause` and `resume` all
to `active`. A paused issue and an issue being worked on right now are
indistinguishable in the canonical source. The action is accepted, journalled,
and changes nothing a reader can see.

### 3. Phase is decided by a file existing, not by its content

`project_issue_schema.py:1290-1292` sets an issue's phase to the last stage whose
`specs/<id>/<phase>.md` exists. The content is never read. **An empty `plan.md`
promotes an issue to "planned."**

This is the same shape as the `[auto]` checks that never run and the `review_after`
field nothing reads: a signal that looks like a gate and is actually a filename.

### Why it matters more than it looks

Issues 125, 126 and 127 were all, at root, the product disagreeing with itself
about state. Each was fixed downstream. None of them touched the fact that the
upstream value they all derive from is written by hand with no check at the moment
of writing — the drift detector runs later, and only reports.

## Scope

### In

- Bring `superseded` into the transaction: add it to `_LIFECYCLES` and to
  `--target-status`, so entering it is journalled and reversible like the others.
- Give `pause` a distinct canonical representation, or remove the action. An
  accepted action that changes nothing is worse than an absent one.
- Make phase depend on the artifact being non-empty and structurally plausible,
  not merely present. Define "plausible" narrowly — a required heading is enough;
  this is not a content review.
- A validation rule that runs at the moment a `**Status:**` line is written by
  the transaction, not only in the later drift sweep.

### Out

- Making the code write back to issue files as a matter of course. The canonical
  source stays human-authored and human-readable; this issue adds checks around
  the write, not an owner change. `project_lifecycle.py:2-8` stays true.
- Changing the four state names or the inline `**Status:**` convention. Issue 048
  and 069 settled those.
- The drift detector itself, which works.
- Retrofitting the seven existing `superseded-by-*` issues. Once the transition
  exists they can be migrated; doing it in the same change hides whether the
  transition works.

## Known Limit

None of this stops someone opening the file in an editor and typing anything they
like. That is a property of a git-native product with human-readable state and it
is not a defect. What can be fixed is that the product's *own* paths bypass their
own transaction, and that a file's existence is mistaken for its content.

## Acceptance Criteria

- `--target-status superseded` works and is journalled, and the resulting issue
  file is byte-identical to what a correct hand edit would produce.
- A paused issue is distinguishable from an active one in the canonical source,
  or `pause` no longer exists. Whichever is chosen is stated in the issue before
  implementation.
- An empty or heading-less `specs/<id>/plan.md` does not promote the issue's
  phase, and a test asserts it with a zero-byte file.
- The three symptoms have separate tests, so fixing one cannot silently mask
  another.
- `python3 scripts/release_check.py .` passes, `valid` checked at the top level.

## Verification

- Fixture: an issue taken to `superseded` through the transaction; assert the
  journal record and the resulting file.
- Fixture: `pause` then read canonical state; assert the chosen behaviour.
- Fixture: a zero-byte `plan.md` and a `plan.md` with only a heading; assert the
  phase for each.
- `tests/test_project_lifecycle.py`, `tests/test_project_lifecycle_transaction.py`,
  `tests/test_project_issue_schema.py`.

## Entry Points

- `scripts/project_lifecycle.py:2-8` — the rule this issue works within
- `scripts/project_lifecycle_transaction.py:142` — `_LIFECYCLES`, missing `superseded`
- `scripts/project_lifecycle_transaction.py:143-147` — `pause` mapped to `active`
- `scripts/project_issue_schema.py:1290-1292` — phase from file existence
- `scripts/project_lifecycle.py:848` — `--target-status` choices

## Scope Fence

Do not fix this by having the code own the issue file. The value of a git-native
product is that the state is a file a person can read and diff; taking that away
to make it safe would be trading the product for the guarantee.

## Workflow Tasks

- [ ] spec → `specs/<issue>/spec.md`
- [ ] plan → `specs/<issue>/plan.md` + `tasks.md`
- [ ] execute → superseded transition, pause decision, phase content check
- [ ] review → `specs/<issue>/review.md`

## Related Issues

- related: `048-artifact-lifecycle-sync` (established the canonical convention),
  `103-atomic-lifecycle-state-transaction` (owns the transaction that lacks
  `superseded`), `126-sync-refuses-the-drift-it-is-prescribed-for` (done),
  `127-completed-issues-keep-their-execution-binding` (done),
  `120-silent-status-fallback-in-issue-parser` (an unrecognised status is
  silently demoted — the parser side of the same weakness),
  `133-only-one-person-can-work-at-a-time`

## Next Command

`product:spec 132-the-canonical-status-line-has-no-protection`
