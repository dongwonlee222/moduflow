# Issue 147: An Issue Cannot Start Until It Is Finished

**Status: backlog** — created 2026-09-07.
**Priority: p1**

## 요약

**이슈를 시작하려면 그 이슈의 산출물이 이미 다 있어야 합니다.** 순서가 거꾸로입니다.

이슈 104를 `active`로 바꾸려 했더니 거부당했습니다. 이유는 `plan.md`와 `review.md`가
없어서입니다 — **그건 활성화한 다음에 쓰는 파일입니다.** 검토서는 맨 마지막에 씁니다.
즉 **끝나야 시작할 수 있습니다.**

이슈 132는 같은 명령이 됩니다. 132는 워크플로에 `specs/<issue>/plan.md`라고 자리표시자를
써서 검사기가 건너뛰기 때문입니다. **실제 경로를 정확히 적은 쪽이 벌을 받습니다.**

## Summary

`project_lifecycle.py --transition start` refuses issue 104 with
`PROJECTED_VALIDATION_INVALID` and commits nothing. The same command applied to
issue 132 seconds earlier, from the same starting state, and canonical validation
is clean before and after.

The cause turned out to be the link checker treating a Workflow Tasks checklist
as a list of files that must already exist. Finding that took reproducing the
projection by hand — nothing the product offers would show it, and one of the two
things the refusal tells the reader to do cannot be done at all.

## Source

- Type: bug — hit while activating issue 104 after 112 closed, 2026-09-07
- Owner / decision maker: Dongwon Lee
- Transaction id: `txn-fe868e0fe334e7b4bb57fa80f99897a7`

## 원인

`validate_active_issue_links` requires every `specs/`, `workspace/` or `memory/`
path mentioned anywhere in the **active** issue to exist. A Workflow Tasks
checklist names all four artifacts, so an issue that writes real paths cannot
become active until all four exist — including `review.md`, which is written
last.

Extracted from the rejected projection directly, because the refusal cannot
show it:

```
$ python3 - <<'EOF'
  plan = plan_lifecycle_transaction(Path("."), LifecycleIntent(
      issue_id="104-…", action="start", actor="probe", source_event="diagnose"))
  with _private_projected_state(plan) as proj:
      validate_project(proj.root, project_context=proj.context)
EOF
  valid: False
  • specs/104-…/plan.md      linked artifact missing
  • specs/104-…/review.md    linked artifact missing
```

The difference from issue 132, which starts fine:

```
104:  - [ ] plan → `specs/104-project-aware-…/plan.md`      ← real path, checked
132:  - [ ] plan → `specs/<issue>/plan.md`                   ← placeholder, skipped
```

`linked_artifacts` skips any path containing `<` or `>`
(`validate_project_artifacts.py:321`). So the check is avoided by writing a
vaguer link, and the issue that names its artifacts precisely is the one that
cannot start.

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

**A wrong test nearly buried this.** Setting 104 to `active` by hand and running
the validator produced only drift errors and no missing-artifact error, which
looked like proof the link check was innocent. It was not:
`validate_active_issue_links` reads the active issue from `.moduflow/state.json`,
which still said `''`, so the check never ran. The probe was measuring nothing.
Recorded because the same mistake is easy to repeat — a check that reads its
subject from a projection cannot be exercised by editing the canonical file.

Setting the status line by hand does work, and leaves the project clean once the
projections are synced. That is the workaround, and it is exactly the bypass
issue 132 exists to close.

## Opportunity — two defects, one visible and one not

**The ordering defect.** A Workflow Tasks checklist is a plan for what will be
written, and the link checker reads it as a list of what must already exist. The
four rows exist precisely because the artifacts do not yet. Today the product
rewards writing `specs/<issue>/plan.md` — a link that points nowhere and is
therefore skipped — over the real path.

**The diagnosis defect.** Finding the two lines above took reproducing the
projection by hand in a Python session. Everything the refusal offers is a dead
end:

- `PROJECTED_VALIDATION_INVALID` is one code covering every way a projected
  state can fail.
- Issue 103 redacted the result envelope to logical identifiers and hashes only.
  Right for a journal record; it also makes a projection-only failure unreadable
  by design, and 126's fix could only make the refusal honest, not informative.
- **The refusal's own instruction cannot be followed.** It says "re-run with the
  transaction id above and report it". Measured:
  `--recover txn-fe868e0fe334e7b4bb57fa80f99897a7` returns
  `RECOVERY_JOURNAL_MISSING`, and grepping the repository for that id finds
  nothing. A transaction failing at projected-validation never reaches the
  journal stage — `rollback_status: not-required` says so — so the id refers to a
  record that was never written.

`--recover` reads `.moduflow/control/transactions/`, which holds **0 files**;
successful transactions write evidence to `workspace/transactions/` instead. Two
different places, and only the second has ever held anything.

## Scope

### In

- **A Workflow Tasks row is not a required artifact.** An issue must be able to
  start with only the artifacts that exist. Whether the fix is exempting the
  checklist section, honouring the checkbox state, or checking only artifacts up
  to the current phase is a design decision for the spec.
- Make a projection-only failure diagnosable. The minimum is that the operator
  can see *which* projected artifact failed *which* check — file and rule, not
  prose.
- Decide where that detail lives. The journal record stays redacted (issue 103);
  the operator-facing path is the question. `--recover <txn-id>` is the obvious
  candidate and already exists.
- Whichever way it goes, the refusal message points at the command that shows
  the detail. Today it says "report it", which is not an action.
- Fix the refusal's dead instruction. Either the transaction id survives a
  projection failure, or the message stops telling the reader to look it up.

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
- Issue 104 starts with `spec.md` written and `plan.md`, `tasks.md` and
  `review.md` absent. That is the case that failed.
- An issue whose Workflow Tasks name real paths is not penalised relative to one
  using `specs/<issue>/…` placeholders. A test asserts both start.
- The refusal names a command that works, or names no command.
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

- [x] spec → `specs/147-an-issue-cannot-start-until-it-is-finished/spec.md`
- [x] plan → `specs/147-an-issue-cannot-start-until-it-is-finished/plan.md` + `tasks.md`
- [x] execute → workflow-row scoping, projection rebuild, dead instruction removed
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

`product:spec 147-an-issue-cannot-start-until-it-is-finished`
