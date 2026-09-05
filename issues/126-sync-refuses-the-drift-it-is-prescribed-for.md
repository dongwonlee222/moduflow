# Issue 126: Sync Refuses The Drift It Is Prescribed For

**Status: backlog** — created 2026-09-05.
**Priority: p1**

## 요약

라이프사이클 드리프트가 생기면 검증기·doctor·오류 메시지가 **하나같이
`project_lifecycle.py --sync`를 해결책으로 지목**합니다. 그런데 실제로 돌리면
`PROJECTED_PROJECT_INVALID`로 거부합니다. 복구 진단은 `healthy`라 멈춘 트랜잭션도
없습니다. 문서화된 유일한 해결책이 자기가 고쳐야 할 상태에서 작동하지 않습니다.

## Summary

Lifecycle drift is reported by `validate_project_artifacts`, surfaced by
`project_doctor`, and each message ends with `(run project_lifecycle.py --sync)`.
Running it returns `status: blocked` — the reconcile transaction stops at
`projected-validation` with `PROJECTED_PROJECT_INVALID` and never commits. The
prescribed remedy cannot clear the condition it is prescribed for.

## Source

- Type: found during `product:review` of Issue 125
- Owner / decision maker: Dongwon Lee
- Date: 2026-09-05
- Evidence: `specs/125-bootstrap-dashboard-missing-active-issue-section/status.md`,
  "New defect found during review"

## Opportunity

Reproduced on this repository on 2026-09-05 by marking issue 125 `active` while
`.moduflow/state.json` still held `active_issue: ""`.

`validate_project_artifacts` reported three drifts, all with the same remedy:

```
lifecycle drift: .moduflow/state.json active_issue '' != issue-file active '125-…'
  (run project_lifecycle.py --sync)
lifecycle drift: dashboard Active Issue section omits active issue '125-…'
  (run project_lifecycle.py --sync)
lifecycle drift: dashboard Active Issue says 'None active' but issue files have active '125-…'
  (run project_lifecycle.py --sync)
```

`project_doctor` agreed — `lifecycle.drift: 3`, and its recommendation list
named the same command. Running it:

```
transaction.failed_stage         = projected-validation
transaction.status               = conflict
projected_validation.valid       = False
projected_validation.rule_ids    = [project-artifacts, issue-schema,
                                    lifecycle-consensus, production-records]
projected_validation.error_codes = ['PROJECTED_PROJECT_INVALID']
post_apply_validation.error_codes = ['POST_APPLY_VALIDATION_NOT_RUN']
status = blocked
errors = ['PROJECTED_VALIDATION_INVALID: Lifecycle reconcile transaction did not
           commit. Recommendation: Run product:doctor before retrying.']
```

Three things make this worse than a plain failure:

- **The advice is circular.** The transaction says run doctor; doctor says run
  sync. Neither names a state a person could change to break the loop.
- **Recovery is not the cause.** `recovery.status` is `healthy` with zero
  transactions, so this is not a stuck journal awaiting cleanup — Issue 103's
  recovery path is working correctly and has nothing to recover.
- **The issue schema is clean.** `project_issue_schema.py --report` returns zero
  diagnostics, so the projected state is not being rejected for a malformed
  issue file.

The immediate suspicion is that projected validation re-runs
`validate_project_artifacts` against a projection that does not yet include
every target the drift check reads, so the projected state still shows drift and
is rejected for it. That is a hypothesis from the error shape, **not verified** —
reproducing it is the first task, not the fix.

**This is currently invisible.** The drift was cleared by taking 125 to `done`,
which removed the active issue entirely. Someone without that option — an issue
that genuinely is active and must stay so — has no documented way forward.

## Scope

### In

- Reproduce the refusal in a fixture: an issue file marked `active` with
  `.moduflow/state.json` and the dashboard still showing none.
- Determine why the projected state fails `validate_project_artifacts`, and
  whether the projection is incomplete or the validation is being applied to the
  wrong snapshot.
- Make `--sync` either clear this drift or fail with a message naming a state
  the operator can act on. "Run product:doctor" is not that message when doctor
  answers "run sync".

### Out

- Changing what counts as lifecycle drift.
- Relaxing projected validation so the transaction commits regardless. Issue 103
  chose validate-before-replace deliberately; a transaction that commits an
  invalid projection is a worse defect than this one.
- The single-global-`active_issue` design itself, which `workspace/inbox.md`
  already records as a concurrent-work blocker.

## Acceptance Criteria

- A fixture reproduces `PROJECTED_PROJECT_INVALID` from a clean starting state,
  so the failure is regression-testable rather than anecdotal.
- With one issue `active` and both derived views stale, `--sync` either commits
  and clears all three drifts, or returns an error naming the specific artifact
  and field that blocks it.
- No error path recommends a command whose own error recommends the first one.
- Recovery diagnostics stay `healthy` throughout — this issue must not be
  mistaken for, or fixed by, the recovery path.
- Validate-before-replace is preserved: no change permits an invalid projection
  to commit.
- `python3 scripts/release_check.py .` passes, checking `valid` at the top level
  and not only the `checks` sub-dictionary.

## Verification

- Fixture: fresh project, one active issue, stale `state.json` and dashboard.
- Assert the drift list before, the transaction result, and the drift list after.
- Assert the same flow still works for the case that does succeed today, so the
  fix is not a rewrite of the working path.
- `tests/test_project_lifecycle.py`, `tests/test_project_lifecycle_transaction.py`.

## Entry Points

- `scripts/project_lifecycle.py:608` — `sync_lifecycle`
- `scripts/project_lifecycle_transaction.py` — projected validation stage
- `scripts/validate_project_artifacts.py` — the drift rules and their remedy text
- `scripts/project_doctor.py` — the recommendation that closes the loop

## Scope Fence

Do not fix this by weakening validation, and do not fix it by removing the drift
rule. The transaction refusing an invalid projection is correct behaviour; what
is wrong is that the only documented escape does not work.

## Workflow Tasks

- [ ] spec → `specs/126-sync-refuses-the-drift-it-is-prescribed-for/spec.md`
- [ ] plan → `specs/126-…/plan.md` + `tasks.md`
- [ ] execute → reproduction fixture, root cause, actionable failure
- [ ] review → `specs/126-…/review.md`

## Related Issues

- related: `103-atomic-lifecycle-state-transaction` (owns the transaction whose
  validation stage refuses), `048-artifact-lifecycle-sync`,
  `120-silent-status-fallback-in-issue-parser` (the status vocabulary that led
  here), `096-read-shaped-commands-that-write`

## Next Command

`product:spec 126-sync-refuses-the-drift-it-is-prescribed-for`
