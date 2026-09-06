# Issue 133: Only One Person Can Work At A Time

**Status: backlog** — created 2026-09-06.
**Priority: p1**

## 요약

`.moduflow/state.json`에 **활성 이슈 칸이 하나**뿐이고 그 파일이 git으로 공유됩니다.
두 사람이 동시에 일하면 전이할 때마다 같은 칸에 서로의 이슈 번호를 씁니다. 막아줄
잠금이 있긴 한데 **강제되지 않습니다** — `upsert_team_item`이 기존 `lock_state`를
읽지 않고 그냥 덮어씁니다. 실제로 오늘 두 세션이 같은 저장소에서 부딪혔습니다.

## Summary

Two coupled defects. `.moduflow/state.json` holds a single global `active_issue`
and is tracked in git, so every lifecycle transition writes the same field.
`workflow/team-state.json` carries per-issue `lock_state` and `locked_by` that
look like the answer, but nothing enforces them.

## Source

- Type: architecture review plus a live incident, 2026-09-06
- Owner / decision maker: Dongwon Lee
- Reported in `workspace/inbox.md` as a concurrent-work blocker
- Confirmed by code reading recorded in
  `memory/decisions/2026-09-06-beads-issue-backend-not-adopted.md`

## Opportunity

### It happened today

Two sessions worked this checkout at the same time on 2026-09-06. One was writing
a handoff document describing this very problem while the other committed four
changes underneath it. `workspace/handoff-2026-09-06.md:20-22` records the
collision as it happened. Nothing was lost, because the two sessions happened not
to write the same field at the same moment — that is luck, not a guarantee.

A second symptom the same day: issues 126 and 127 were finished but could not be
marked `active` while 112 held the slot, so their code landed while their status
said `backlog`. The inventory then listed completed work as ready to start.

### The lock is not enforced

`scripts/project_workflow.py:194` — `upsert_team_item` merges into the existing
record **without reading** `lock_state` or `locked_by`, and `start_issue_work`
(`:242-243`) overwrites them outright. So a lock can be taken by one person and
silently replaced by the next. Confirmed by reading the code, not inferred.

The primitive that would work already exists: `_acquire_lifecycle_lock`
(`scripts/project_lifecycle_transaction.py:2199`) uses `os.O_EXCL`. Its key is the
transaction id; widening it to the issue id is the shape of the fix.

### Where the issue backend fits

ID allocation, dependencies, ready queries and atomic claim are the part of this
that a replaceable issue backend could own. Beads was evaluated on 2026-09-06 and
**not adopted** — the empirical run cleared two processes inside one checkout, and
the case that matters is two machines, which is unmeasured. Only a narrow shadow
pilot is on the table. That decision is a premise here, not a question:
`memory/decisions/2026-09-06-beads-issue-backend-not-adopted.md`.

**The point of this issue is that the single `active_issue` and the unenforced
lock must be fixed whether or not any backend is ever adopted.** They are ModuFlow's
own defects.

## Scope

### In

- Make "what I am working on right now" per-person rather than a single shared
  field. Which mechanism — a local file outside git, a per-actor key, or the
  existing `team-state.json` promoted to canonical — is the design question this
  issue answers.
- Enforce the lock: `upsert_team_item` must read `lock_state` and `locked_by` and
  refuse a conflicting write, rather than merging over it. Compare-and-set, keyed
  on the issue id, reusing the `os.O_EXCL` primitive that already exists.
- Demote `team-state.json` from a direct write target to a projection, so the
  lock cannot be edited around the transaction that is supposed to own it.
- A test that simulates two writers claiming the same issue and asserts exactly
  one wins with a message naming who holds it.

### Out

- Adopting Beads or any external issue backend. Decided 2026-09-06; only a shadow
  pilot is open, and it is not this issue.
- Migrating existing issues to another store.
- The two-machine push/pull trial. It needs a second Mac and is awaiting the
  owner's decision on whether to use the company Codex environment.
- Changing what an issue file looks like. Issues stay readable Markdown in the
  repo.
- The lifecycle transaction itself, which works.

## Known Limit

Enforcing a lock in a git-tracked file cannot stop two people who are offline from
both claiming the same issue and discovering it at merge time. What it can stop is
one process silently overwriting another's claim inside one checkout, and one
person seeing a stale claim as if it were free. Anything stronger needs a shared
service, which is out of scope and is what the Beads evaluation was about.

## Acceptance Criteria

- Two concurrent claims on the same issue produce exactly one winner, and the
  loser receives a message naming the current holder — not a silent overwrite.
- A lifecycle transition by one actor does not change another actor's recorded
  current work.
- `team-state.json` cannot be written except through the transaction, asserted by
  a test that attempts a direct write.
- The 2026-09-06 collision is reproducible as a fixture and passes after the fix.
- Existing single-user behaviour is unchanged — a test asserts a solo session
  sees no new prompts, locks or failures.
- `python3 scripts/release_check.py .` passes, `valid` checked at the top level.

## Verification

- Fixture: two writers, same issue, asserting one winner and a named holder.
- Fixture: two actors transitioning different issues, asserting neither disturbs
  the other's current work.
- Fixture: a direct write to `team-state.json`, asserting refusal.
- Fixture: a solo session end to end, asserting no behaviour change.
- `tests/test_project_workflow.py`, `tests/test_project_lifecycle_transaction.py`.

## Entry Points

- `.moduflow/state.json` — the single global `active_issue`
- `scripts/project_workflow.py:194` — `upsert_team_item`, merges without reading
  the lock
- `scripts/project_workflow.py:242-243` — `start_issue_work`, overwrites it
- `scripts/project_lifecycle_transaction.py:2199` — `_acquire_lifecycle_lock`, the
  `os.O_EXCL` primitive to widen
- `workflow/team-state.json` — the artifact to demote to a projection
- `workspace/handoff-2026-09-06.md:20-22` — the incident

## Scope Fence

Do not solve this by adopting an external backend; that was decided and declined
on 2026-09-06. Do not solve it by removing the lock fields because they are
unused — they are the right idea, unenforced.

## Workflow Tasks

- [ ] spec → `specs/<issue>/spec.md`
- [ ] plan → `specs/<issue>/plan.md` + `tasks.md`
- [ ] execute → per-person current work, compare-and-set lock, team-state as projection
- [ ] review → `specs/<issue>/review.md`

## Related Issues

- related: `132-the-canonical-status-line-has-no-protection` — the same layer.
  132 protects the value; this protects who may change it.
- related: `103-atomic-lifecycle-state-transaction` (owns the lock primitive),
  `035-team-issue-branch-pr-workflow` (introduced `team-state.json`),
  `005-team-workflow-state` , `048-artifact-lifecycle-sync`
- related: `112-execution-planner-and-backend-boundary` — 112 settles what
  ModuFlow executes versus what the host executes. This issue settles who may
  claim work. Deliberately separate axes; the Beads benchmark was removed from
  112 for that reason.

## Next Command

`product:spec 133-only-one-person-can-work-at-a-time`
