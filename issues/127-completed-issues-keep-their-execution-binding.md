# Issue 127: Completed Issues Keep Their Execution Binding

**Status: backlog** — created 2026-09-06.
**Priority: p1**

## 요약

이슈가 `done`이 되어도 `workspace/loop-state.json`의 `git_binding`이 그대로
남습니다. 끝난 이슈의 브랜치·커밋·활성 백엔드를 계속 들고 있습니다. 게다가
브랜치 일치 규칙이 `issue_id in branch`라서 `main`에서 작업하면 **모든 이슈가**
불일치로 걸립니다. 이 저장소는 `main`에서 작업합니다.

## Summary

Two faults that only fail together, and did on 2026-09-05:

1. Completing an issue does not release its `git_binding` in
   `workspace/loop-state.json`.
2. `branch_matches_issue` is `return issue_id in branch`, which no branch named
   `main` can ever satisfy.

Held separately each is survivable. Together, a repository worked on `main`
carries a dead binding that fails validation for every subsequent issue.

## Source

- Type: root cause found while diagnosing Issue 126, 2026-09-06
- Owner / decision maker: Dongwon Lee
- Evidence: `issues/126-sync-refuses-the-drift-it-is-prescribed-for.md`,
  "Root cause — verified 2026-09-06"

## Opportunity

Found in `workspace/loop-state.json` on 2026-09-05, with `issue_id: null` and
`phase: "select"` — the loop believed nothing was in flight:

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

Issue 111 was `done`. The branch no longer existed. `execution_backend.status`
was still `active`.

### Fault 1 — nothing releases the binding

No completion path clears `git_binding`. The value persists until a later
transaction happens to overwrite it, or until someone edits the file by hand —
which is how this one was cleared.

### Fault 2 — the branch rule assumes a branch per issue

```python
# scripts/project_loop.py:81-84
def branch_matches_issue(issue_id, branch):
    return issue_id in branch
```

`validate_git_binding_for_issue` (`scripts/project_loop.py:153-161`) calls it.
There is no case for main-based work: the rule can only answer "the branch name
contains the issue id", so working on `main` — this repository's own practice —
is indistinguishable from working on the wrong branch. The blast radius is every
issue, not one.

The combination is what produced the Issue 126 refusal: a dead binding pointing
at a branch that fails a rule that main can never pass.

## Scope

### In

- Release `git_binding` when an issue reaches `done`, in the same transaction
  that records the completion, so the release is atomic with it.
- Give `branch_matches_issue` a defined answer for main-based work rather than
  falling through to "no match": either an explicit allowed-base-branch case or
  a binding mode that declares no per-issue branch is expected.
- A regression test that takes an issue to `done` and asserts the binding is
  released, and one that validates an issue while on `main`.

### Out

- The `errors` list the transaction discards, and the circular advice — issue 126.
- Introducing branch policy. This issue makes the existing rule state what it
  already assumes; it does not decide whether per-issue branches are required.
- Retroactively repairing bindings in other repositories.

## Acceptance Criteria

- Taking an issue to `done` leaves `git_binding` with no branch, no commits, and
  `execution_backend.status` not `active`.
- Validating an issue while checked out on `main` does not fail for branch
  mismatch, and the reason is stated in the result rather than inferred.
- A binding genuinely pointing at the wrong per-issue branch still fails. The
  fix must not be "accept everything".
- The two faults are covered by separate tests, so a later change that
  reintroduces one is caught even if the other still holds.
- `python3 scripts/release_check.py .` passes, `valid` checked at the top level.

## Verification

- Fixture: issue taken from `active` to `done`; assert binding before and after.
- Fixture: issue validated on `main`; assert pass with a stated reason.
- Fixture: issue validated on `codex/999-unrelated`; assert it still fails.
- `tests/test_project_loop.py`, `tests/test_project_lifecycle_transaction.py`.

## Entry Points

- `scripts/project_loop.py:81-84` — `branch_matches_issue`
- `scripts/project_loop.py:153-161` — `validate_git_binding_for_issue`
- `scripts/project_lifecycle_transaction.py` — the completion transaction that
  should release the binding
- `workspace/loop-state.json` — the artifact that held the dead value

## Scope Fence

Do not make the branch check permissive to get past it. A binding pointing at
the wrong branch must still fail; what is missing is the case for having no
per-issue branch at all.

## Found While Fixing — 2026-09-06

`project_doctor.py:808` already skips the branch check when the branch is
`main` or `master`:

```python
if loop_state and branch and branch not in {"main", "master"}:
```

So the product already knew base-branch work is legitimate — in one place, as a
hardcoded pair of names, while `validate_git_binding_for_issue` did not know it
at all. The two now disagree in a narrower way: a project whose base branch is
`develop` is handled by the new rule and not by the doctor's hardcode.

**Not fixed here.** The doctor's behaviour is correct today; this is a duplicate
implementation of one concept, not a second instance of the bug. Recorded rather
than widened.

## Workflow Tasks

- [x] execute → binding release, base-branch case, 15 regression tests
- [ ] review → `specs/<issue>/review.md`

No spec or plan: two functions and a test file, with acceptance criteria already
written above. Below the threshold where a spec adds anything, per the S-grade
bugfix exception used for issue 125.

## Related Issues

- pairs_with: `126-sync-refuses-the-drift-it-is-prescribed-for` — this issue
  removes the refusal; 126 makes the next one readable.
- related: `103-atomic-lifecycle-state-transaction` (owns the completion
  transaction), `048-artifact-lifecycle-sync`,
  `112-execution-planner-and-backend-boundary` (owns backend selection, whose
  `status: active` is the field left stale here)

## Next Command

`product:spec 127-completed-issues-keep-their-execution-binding`
