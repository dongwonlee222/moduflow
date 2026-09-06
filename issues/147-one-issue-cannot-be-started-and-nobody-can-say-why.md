# Issue 147: One Issue Cannot Be Started And Nobody Can Say Why

**Status: backlog** — created 2026-09-07.
**Priority: p1**

## 요약

이슈 104를 `active`로 바꾸려는데 **트랜잭션이 계속 거부합니다.** 같은 명령이
이슈 132에서는 됩니다. 정본 파일은 깨끗하고(`valid: true`, 드리프트 0), 거부는
`PROJECTED_VALIDATION_INVALID` 하나만 남깁니다. **왜 거부하는지 알 방법이 지금
없습니다.** 우회해서 손으로 고칠 수는 있는데, 그러면 이슈 132가 신고한 바로 그
"손으로 고치기"가 됩니다.

## Summary

`project_lifecycle.py --transition start` refuses issue 104 with
`PROJECTED_VALIDATION_INVALID` and commits nothing. The same command applied to
issue 132 seconds earlier, from the same starting state. Canonical validation is
clean before and after, so issue 126's refusal — correctly — declines to name a
cause and says the failure is projection-only.

That refusal is working as designed. What is missing is any way to see inside the
projection it rejected.

## Source

- Type: bug — hit while activating issue 104 after 112 closed, 2026-09-07
- Owner / decision maker: Dongwon Lee
- Transaction id: `txn-fe868e0fe334e7b4bb57fa80f99897a7`

## 원인

원인 미상.

Reproduced, and the difference between the two issues is not explained by
anything measured:

```
$ python3 scripts/project_lifecycle.py . --transition start \
    --issue-id 132-the-canonical-status-line-has-no-protection \
    --actor test --source-event probe
  status: applied

$ python3 scripts/project_lifecycle.py . --transition start \
    --issue-id 104-project-aware-natural-language-request-orchestrator \
    --actor "Dongwon Lee" --source-event "112 closed 2026-09-07; 104 unblocked"
  status: conflict
  failed_stage: projected-validation
  error_code: PROJECTED_VALIDATION_INVALID
  rollback_status: not-required

$ python3 scripts/validate_project_artifacts.py .
  "valid": true, lifecycle_drift: []
```

The refusal text, from `project_lifecycle.refusal_lines` (issue 126):

> Lifecycle transaction did not commit. The current project validates clean, so
> the projected state was rejected for something the canonical files do not
> show. This is a projection-only failure — re-run with the transaction id above
> and report it; do not edit files at random.

**Two hypotheses were tested and both are wrong.** Recording them so the next
reader does not repeat them:

- *The `**Blocked-by:**` line I had edited was malformed.* Removed it; still
  refuses.
- *`linked_artifacts` collects every `specs/` path in the issue regardless of
  checkbox state, so 104's unwritten `plan.md`, `tasks.md` and `review.md` count
  as missing links.* Setting 104 to `active` by hand produces only the three
  expected drift errors and no missing-artifact error, so this is not it.

Setting the status line by hand does work, and leaves the project clean once the
projections are synced. That is the workaround, and it is exactly the bypass
issue 132 exists to close.

## Opportunity

`PROJECTED_VALIDATION_INVALID` is a single code covering every way a projected
state can fail. Issue 103 redacted the transaction's result envelope to logical
identifiers and hashes only — a deliberate contract, and the right one for a
journal record. But it means a projection-only failure is unreadable by design,
and 126's fix could only make the refusal honest about that, not informative.

So the product has a failure class it can detect, refuse, and never explain. The
recovery path (`--recover <txn-id>`) exists; whether it surfaces the rejected
projection is the first thing to check.

## Scope

### In

- Make a projection-only failure diagnosable. The minimum is that the operator
  can see *which* projected artifact failed *which* check — file and rule, not
  prose.
- Decide where that detail lives. The journal record stays redacted (issue 103);
  the operator-facing path is the question. `--recover <txn-id>` is the obvious
  candidate and already exists.
- Whichever way it goes, the refusal message points at the command that shows
  the detail. Today it says "report it", which is not an action.
- Explain the 132-versus-104 difference, or state that it could not be
  determined. A closed issue that never says why one worked is a worse record
  than an open one.

### Out

- Un-redacting the journal record or the transaction result envelope. Issue 103
  settled that and three contract tests enforce it.
- Changing what `PROJECTED_VALIDATION_INVALID` refuses. The refusal may well be
  correct; this issue is about seeing why.
- The one-active-issue limit — that is issue 133, and it is what made the 132
  probe block 143 immediately afterwards.
- `pause` not pausing. Hit during the same session (a `pause` returned `applied`
  and left the issue `active`), and it is already issue 132's second defect.

## Known Limit

If the projection is rejected by a check that has no artifact to point at, there
may be nothing to show beyond a rule name. A rule name is still more than the
current output, and the acceptance criteria should not promise a file path in
every case.

## Acceptance Criteria

- A projection-only refusal names at least the failing check, and the failing
  artifact when one exists.
- The refusal message names the command that shows the detail, and that command
  works against the transaction id in the same output.
- Starting issue 104 either succeeds or fails with a message a person can act
  on. Both outcomes close this issue; a silent success does not.
- The journal record and result envelope stay byte-identical in shape. A test
  asserts the issue 103 redaction contract is untouched.
- `python3 scripts/release_check.py .` passes, `valid` checked at the top level.

## Verification

- Fixture reproducing a projection-only rejection; assert the message names the
  check.
- `--recover` against that transaction id; assert it returns something the
  message promised.
- The three issue 103 redaction contract tests, unchanged and passing.
- Re-run the 104 start and record the outcome in the review.

## Entry Points

- `scripts/project_lifecycle_transaction.py` — the projected-validation stage
- `scripts/project_lifecycle.py` — `refusal_lines`, `project_validation_sentences`
- `scripts/project_lifecycle.py:848` — `--target-status`, and `--recover`
- `specs/126-sync-refuses-the-drift-it-is-prescribed-for/` — the fix that made
  the refusal honest, and the boundary it could not cross
- `specs/103-atomic-lifecycle-state-transaction/spec.md` — the redaction contract

## Scope Fence

Do not make the projected state readable by relaxing the issue 103 redaction.
The journal is a durable record with a deliberate contract; the operator needs a
view, not a looser record. If the only way to explain a refusal is to weaken the
journal, say so and stop.

## Workflow Tasks

- [ ] spec
- [ ] plan
- [ ] execute
- [ ] review

## Related Issues

- related: `126-sync-refuses-the-drift-it-is-prescribed-for` (done — made the
  refusal honest; this is the half it could not reach),
  `103-atomic-lifecycle-state-transaction` (done — owns the redaction contract
  that makes the projection opaque),
  `132-the-canonical-status-line-has-no-protection` (the hand-edit workaround
  is the bypass 132 exists to close, and its `pause` defect was hit in the same
  session), `133-only-one-person-can-work-at-a-time` (the one-active limit that
  made a probe block the next issue),
  `146-the-validator-throws-away-severity-at-the-last-step` (the same shape one
  layer out — structure exists and is destroyed before a reader sees it)

## Next Command

`product:spec 147-one-issue-cannot-be-started-and-nobody-can-say-why`
