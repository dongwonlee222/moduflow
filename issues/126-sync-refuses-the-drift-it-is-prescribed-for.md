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

### Root cause — verified 2026-09-06

The first write of this issue guessed that the projection was incomplete. It was
not. The cause was found by reconstructing the projected state by hand and
calling `validate_project` on it directly, which returned the three errors the
transaction had thrown away. Three faults stacked:

**1. Stale execution binding that nothing clears.** `workspace/loop-state.json`
still carried issue 111's binding long after 111 was `done`. Verbatim, as found:

```json
"git_binding": {
  "mode": "git-files",
  "branch": "codex/111-runtime-provenance-and-validation-mode-separation",
  "base_branch": "main",
  "commits": ["a1e5ae6", "aac78e5", "a7ccdca", "517ec64", "b5c3ce3"],
  "execution_backend": {"type": "codex", "status": "active",
                        "reason": "User approved inline Issue 111 implementation"}
}
```

`issue_id` was already `None` and `phase` `select`, so the loop believed no issue
was in flight while still holding an active backend bound to a branch that no
longer existed. Completing an issue does not release its binding.

**2. The branch rule cannot express main-based work.**
`project_loop.branch_matches_issue` (`scripts/project_loop.py:81-84`) is
`return issue_id in branch`. The working branch was `main`, so the check failed
for issue 125 — and fails for *every* issue worked on `main`, which is how this
repository is worked. The rule assumes a per-issue branch and has no vocabulary
for its absence.

**3. The transaction discards the errors it collected.**
`_summarize_validation_result` (`scripts/project_lifecycle_transaction.py:1308-1372`)
keeps `valid`, `rule_ids` and `error_codes` and drops the `errors` list. The
operator receives `PROJECTED_PROJECT_INVALID` — a code naming no artifact and no
field — while the process that produced it held three sentences that named both.
This is the multiplier: (1) and (2) are ordinary bugs, and (3) is what turned
them into forty minutes of guessing.

The advice is circular for the same reason: the transaction says run doctor,
doctor says run sync, and neither can name a state to change because the layer
that knew was the layer that stayed silent.

Recovery was not involved — `recovery.status` was `healthy` with zero
transactions — and `project_issue_schema.py --report` returned zero diagnostics.
Both were ruled out before the cause was found.

**Resolution applied, cause not fixed.** `workspace/loop-state.json` was cleared
by hand (`branch: null`, `commits: []`, `execution_backend.status:
"not_selected"`), after which issue 112 started cleanly. All three faults remain
in the code, and fault (2) will refuse again on the next issue worked on `main`.

## Scope

This issue owns fault (3) and the circular advice. Faults (1) and (2) — the
binding that is never released and the branch rule that cannot express
main-based work — are owned by `127-completed-issues-keep-their-execution-binding`.

### Corrected 2026-09-06 — the sentences cannot ride on the transaction

The first draft of this scope said to carry the `errors` list through
`_summarize_validation_result`. That is the wrong place, and the repository says
so in a test written by issue 103:

```python
# test_projected_validation_summary_is_stable_redacted_and_detached
self.assertEqual(summary, {"valid": ..., "rule_ids": [...], "error_codes": [...]})
rendered = json.dumps(summary, ensure_ascii=False)
self.assertNotIn("private", rendered)
```

Redaction is a property of the summary **object**, not only of the journal.
`serialize_transaction_result` enforces the same on the whole result envelope
(`_assert_exact_keys`, "logical paths and hashes only"). Widening any of them to
carry prose would trade issue 103's guarantee for this issue's.

There is also a better reason not to. Validation runs against a private staging
copy under `.moduflow/.txn-<id>-projected-<id>/`, so its paths name a directory
that no longer exists when the operator reads the error. What they need is the
**canonical** project — the files they can open.

So the refusal re-validates the real root and reports that, labelled as the
current project's problems rather than as the projection's reason.

### In

- On refusal, report the canonical project's validation findings — plain
  artifact errors, lifecycle drift, and error-severity issue-schema diagnostics
  (which already carry `source_path` and `field`).
- Say so honestly when the canonical project is clean: the projection was
  rejected for something the canonical files do not show. Naming a cause there
  would be the guess this issue exists to stop.
- Break the circular advice. The refusal names artifacts, not "run
  product:doctor", whose own remedy is to run sync.
- One implementation, shared by `sync_lifecycle` and
  `project_loop.write_loop_state`, so the two refusals cannot drift.
- A fixture reproducing the refusal, so the failure is regression-testable
  rather than anecdotal.
- A guard test asserting `scripts/project_lifecycle_transaction.py` is
  unmodified, so a later author cannot pay for this issue with issue 103's
  redaction.

### Out

- Changing what counts as lifecycle drift.
- Relaxing projected validation so the transaction commits regardless. Issue 103
  chose validate-before-replace deliberately; a transaction that commits an
  invalid projection is a worse defect than this one.
- The stale binding and the branch rule — issue 127.
- Widening the transaction result, its validation summaries, or the journal
  record. All three are redacted by issue 103 and stay that way.
- `project_doctor`. Its recommendation to run sync is now correct — sync either
  commits or names the artifacts — so the circle is broken from this side and
  doctor needs no change. Recorded rather than silently skipped.
- The single-global-`active_issue` design itself, which `workspace/inbox.md`
  already records as a concurrent-work blocker.

## Acceptance Criteria

- A refusal names at least one artifact path and the field within it. An
  operator who reads only the refusal can locate the state to change without
  reconstructing the projection.
- `error_codes` is retained for machine callers; the sentences are added
  alongside, not substituted for it.
- No error path recommends a command whose own error recommends the first one.
- A fixture reproduces the refusal from a clean starting state and asserts the
  named artifact appears in the output.
- Recovery diagnostics stay `healthy` throughout — this issue must not be
  mistaken for, or fixed by, the recovery path.
- Validate-before-replace is preserved: no change permits an invalid projection
  to commit.
- `python3 scripts/release_check.py .` passes, checking `valid` at the top level
  and not only the `checks` sub-dictionary.

## Verification

- Fixture: fresh project, one active issue, stale `state.json` and dashboard.
- Assert the refusal text contains the artifact path, not only the error code.
- Assert the same flow still works for the case that does succeed today, so the
  fix is not a rewrite of the working path.
- `tests/test_project_lifecycle.py`, `tests/test_project_lifecycle_transaction.py`.

## Entry Points

- `scripts/project_lifecycle_transaction.py:1308-1372` — `_summarize_validation_result`,
  where the `errors` list is dropped
- `scripts/project_lifecycle_transaction.py:3549` — `validate_projected_transaction`
- `scripts/project_lifecycle.py:608` — `sync_lifecycle`, the caller that renders
- `scripts/project_doctor.py` — the recommendation that closes the loop

## Scope Fence

Do not fix this by weakening validation, and do not fix it by removing the drift
rule. The transaction refusing an invalid projection is correct behaviour; what
is wrong is that it refuses without saying what it saw.

## Workflow Tasks

- [x] execute → reproduction fixture, canonical-project reporting, 15 tests
- [ ] review → `specs/<issue>/review.md`

No spec or plan: one shared function and a test file, with the design decision
recorded in Scope above. Per the S-grade bugfix exception used for issue 125.

## Related Issues

- related: `103-atomic-lifecycle-state-transaction` (owns the transaction whose
  validation stage refuses), `048-artifact-lifecycle-sync`,
  `120-silent-status-fallback-in-issue-parser` (the status vocabulary that led
  here), `096-read-shaped-commands-that-write`
- pairs_with: `127-completed-issues-keep-their-execution-binding` — 127 removes
  the refusal seen here; this issue makes the next refusal readable. Fixing only
  127 leaves the next unrelated failure just as opaque.

## Next Command

`product:spec 126-sync-refuses-the-drift-it-is-prescribed-for`
