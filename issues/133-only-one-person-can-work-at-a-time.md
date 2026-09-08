# Issue 133: Only One Person Can Work At A Time

**Status: backlog** — created 2026-09-06.
**Priority: p0**

## 요약

`.moduflow/state.json`에 **활성 이슈 칸이 하나**뿐이고 그 파일이 git으로 공유됩니다.
두 사람이 동시에 일하면 전이할 때마다 같은 칸에 서로의 이슈 번호를 씁니다. 막아줄
잠금이 있긴 한데 **강제되지 않습니다** — `upsert_team_item`이 기존 `lock_state`를
읽지 않고 그냥 덮어씁니다. 실제로 오늘 두 세션이 같은 저장소에서 부딪혔습니다.

## 2026-09-08 재현 — 증상이 이 이슈가 적은 것과 다릅니다

맥 한 대에서 bare 원격 하나와 clone 둘(`macA`·`macB`)로 재현했습니다.

```
macA: 001 시작 → commit → push
macB: 002 시작 → commit → pull

CONFLICT (content): .moduflow/state.json
CONFLICT (content): workspace/dashboard.md
CONFLICT (content): workspace/loop-state.json

  <<<<<<< HEAD
    "active_issue": "002-second",     ← macB
  =======
    "active_issue": "001-first",      ← macA
  >>>>>>>
```

**"서로 덮어쓴다"가 아닙니다. git 이 충돌로 막습니다.**

그리고 **이슈 파일은 안 깨집니다** — `issues/` 충돌 0건, `001`과 `002` 둘 다
`active` 로 멀쩡히 남습니다. **정본은 무사합니다.**

| | |
|---|---|
| 잃는 것 | **없음.** 정본인 이슈 파일은 안전하다 |
| 실제로 겪는 것 | **pull 할 때마다 파일 셋을 손으로 푸는 일** |
| 왜 문제인가 | 사람이 안 쓴 파일이다. 트랜잭션이 만든 **투영**인데 충돌은 사람이 푼다 |

### 그래서 고칠 것이 좁아집니다

`.moduflow/state/` 는 **이미 gitignore 돼 있습니다.** 머신마다 다른 값을 두는
자리가 이미 있는데 `active_issue` 가 공유되는 자리에 있습니다. 그것 하나입니다.

**잠금 강제(`upsert_team_item`)는 오늘 효과가 없습니다.** `team-state.json` 이
이 저장소에 없고, 충돌은 잠금이 아니라 git 이 잡고 있습니다. 그 부분은
`107`·`108`·`094` 와 같은 **"팀이 생기면"** 조건입니다.

**이 이슈의 원래 원인 분석(`upsert_team_item` 이 `lock_state` 를 덮어쓴다)은
코드로는 여전히 맞습니다.** 틀린 것은 그것이 오늘 겪는 증상의 원인이라는 연결
쪽입니다.


## 2026-09-08 — A″ 로 처리했습니다. 완전하지 않고, 왜 그런지

`.gitattributes` 에 `merge=ours` 셋을 넣고, **각 클론이 드라이버를 등록했는지
`product:doctor` 가 보고**하게 했습니다. `project_migrate` 도 새 프로젝트에
같은 파일을 만듭니다.

```
새 클론에서 doctor:
  "이 클론은 `.gitattributes` 의 `merge=ours` 를 지킬 수 없습니다 —
   `git config merge.ours.driver true` 를 한 번 실행하세요."

드라이버 등록 후 두 컴퓨터 시나리오:
  Merge made by the 'ort' strategy.
  충돌: 없음
  macB active_issue: 002-second      ← 자기 값 유지
  이슈 파일: active / active          ← 둘 다 무사
```

### 왜 A(칸 옮기기)가 아니라 A″ 인가

A는 `active_issue` 를 이미 gitignore 된 `.moduflow/state/` 로 옮기는 것이고,
**완료 조건 ②를 완전히 만족하는 유일한 안**입니다. 하지만 실측하니
`state.json` 을 여는 곳이 **11개 파일 34곳**이고 그중 셋이 트랜잭션(7,524줄)·
검사기(1,015줄)·훅입니다.

A″ 는 `.gitattributes` 한 파일과 `doctor` 검사 하나입니다. **되돌리기도
파일 하나 지우면 끝입니다.**

### A″ 의 한계 — 숨기지 않습니다

**드라이버는 `.git/config` 에 있고 clone 을 따라가지 않습니다.** 받은 사람이
명령 한 줄을 쳐야 합니다. 그러므로 **완료 조건 ②를 완전히 만족하지 않습니다.**
`doctor` 가 안 친 클론을 보고하는 것이 그 간극을 메우는 방식이고, 이슈 151에서
"설정이 필요한데 아무도 안 알려줘서 4주간 몰랐다"를 고친 것과 같은 장치입니다.

**A 는 여전히 유효한 안이고, A″ 가 그것을 막지 않습니다.** 두 컴퓨터를 실제로
쓰기 시작해서 이 한 줄이 부담이 되면 A 로 갑니다. 그때 이 이슈를 다시 엽니다.


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

## 안 고치면

두 컴퓨터에서 일하면 활성 이슈 칸을 서로 덮어씁니다. 사장님이 두 대를 쓰십니다. — 기록

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
