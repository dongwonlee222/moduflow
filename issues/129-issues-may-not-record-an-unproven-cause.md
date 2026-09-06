# Issue 129: Issues May Not Record An Unproven Cause

**Status: backlog** — created 2026-09-06.
**Priority: p1**

## 요약

버그 이슈의 원인 칸에 **확인 안 된 추측**이 들어가면 다음 사람을 엉뚱한 코드로
보냅니다. 2026-09-06 한 세션에서 3번 다시 썼습니다. 원인 칸에는 실제 실행 출력만
쓰고, 재현 못 했으면 "원인 미상"으로 남기게 강제합니다.

## Summary

`commands/product-issue.md` has nine "Do" steps, all about shape and metadata,
and none requiring that a stated cause be reproduced. The issue schema enforces
no required sections. So an unverified guess and a verified finding are written
the same way and read the same way.

## Source

- Type: bug — three reworks in one session, 2026-09-06
- Owner / decision maker: Dongwon Lee

## Opportunity

Three reworks, same shape — a conclusion stated before the command that would
settle it was run:

| Where | Written | Actual |
| --- | --- | --- |
| Issue 126 | "the projection is probably incomplete" | wrong; the transaction had discarded its error list. Rewritten whole |
| Issue 120 | "this bug has never fired" | it had. Priority raised p2 → p1 |
| Commit `83f95c5` | "tests pass" (25 of 1858 run) | 3 failures |

Issue 126 is the important one. It **did** label the guess:

> That is a hypothesis from the error shape, **not verified**.

The label was honest and it still misled — the next reader went to the
projection code instead of to `_summarize_validation_result` (the function that
drops the error list). Labelling a guess is not enough; the guess has to not be
in the cause slot at all.

Current state, measured 2026-09-06: 8 of 129 issues are bug-shaped, and 7 of
those already paste real command output. The habit exists. What is missing is
the rule that the cause slot holds nothing else.

## Scope

### In

- A required cause section on bug-shaped issues holding either pasted command
  output or the literal `원인 미상`.
- A check that fails when the cause section contains hedging language
  (`추측`, `~것 같`, `~로 보임`, `hypothesis`, `suspicion`, `likely`, `probably`).
- `commands/product-issue.md` states the rule, and states that a symptom-only
  issue with no cause is complete and correct.

### Out

- Non-bug issues. Feature and opportunity issues have no cause to prove —
  issue 121 has no pasted output and is correct as written. The check must key
  off issue type, not run on all 129.
- Judging whether a pasted output actually supports the stated cause. A machine
  cannot do that; see Known Limit.
- Wiring the check into the stop hook. Validation runs at `release_check` today;
  moving it earlier is a separate change, and doing both at once means a
  failure cannot be attributed to either.

## Known Limit

This catches the failure that happened, not every failure. A confidently worded
wrong cause with real output pasted under it passes. Stating that up front so
the gate is not later mistaken for proof of correctness.

## Acceptance Criteria

- A bug issue whose cause section contains hedging language fails validation,
  naming the issue file and the offending phrase.
- The same issue passes once the cause is replaced with `원인 미상`.
- All 8 existing bug issues pass unchanged except where they genuinely hedge.
- Issue 121 and the other 121 non-bug issues are unaffected.
- The failure message names the file and the phrase — not a code. A person who
  reads only the failure knows what to edit.
- `python3 scripts/release_check.py .` passes, `valid` checked at the top level.

## Verification

- Fixture bug issue with a hedged cause → fails, message names the phrase.
- Same fixture with `원인 미상` → passes.
- Fixture feature issue with no cause section → passes.
- Run against all 129 existing issues; assert only genuine hedges fail.

## Entry Points

- `commands/product-issue.md` — the nine Do steps with no proof requirement
- `scripts/project_issue_schema.py` — enforces no required sections today
- `scripts/validate_project_artifacts.py` — where the check would run
- `issues/126-sync-refuses-the-drift-it-is-prescribed-for.md` — the rewrite this
  rule is derived from

## Scope Fence

Do not extend the check to non-bug issues, and do not add a suppression list.
A cause that cannot be classified is a rule to sharpen, not an exception to file.

## Workflow Tasks

- [ ] spec → `specs/<issue>/spec.md`
- [ ] plan → `specs/<issue>/plan.md` + `tasks.md`
- [ ] execute → cause section rule, hedge check, command text
- [ ] review → `specs/<issue>/review.md`

## Related Issues

- related: `126-sync-refuses-the-drift-it-is-prescribed-for` (the rewrite that
  produced this rule), `120-silent-status-fallback-in-issue-parser`,
  `128-linked-artifact-check-runs-for-one-issue-only` (the other case of a
  check that refuses or ignores without saying why)

## Next Command

`product:spec 129-issues-may-not-record-an-unproven-cause`
