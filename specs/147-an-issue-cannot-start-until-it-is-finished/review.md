# Review: An Issue Cannot Start Until It Is Finished

Issue: 147-an-issue-cannot-start-until-it-is-finished

## What shipped

`708327b`. Two small changes to two files.

`scripts/validate_project_artifacts.py` — `linked_artifacts` blanks unchecked
Workflow Tasks rows before collecting links. One regex pair and one helper.

`scripts/project_lifecycle.py` — `refusal_lines` takes `issue_id` and `action`,
and a new `projected_validation_sentences` rebuilds the rejected projection and
validates it. The impossible instruction is deleted.

Ten new tests. Version 0.3.78.

## Did it work

The only test that matters ran against the live repository:

```
104 start: applied
Status: active — created 2026-08-19; unblocked 2026-09-07; started 2026-09-07
state.json active_issue: 104-project-aware-natural-language-request-orchestrator
valid: true / drift: 0
```

Issue 104 started through the transaction with `spec.md` present and `plan.md`,
`tasks.md`, `review.md` absent — the exact case that refused this morning. The
hand-edit workaround was never used.

The refusal, before and after, on a real rejection:

```
before:  PROJECTED_VALIDATION_INVALID

after:   The current project validates clean; the projection is what failed.
         Rebuilt it and found 2 problem(s):
           - lifecycle drift: multiple active issues in issue files: [...]
           - multiple active issues in issue files: [...]
```

2066 tests, OK. `release_check` valid.

## What this issue was actually about

Not the checkbox rule — that fix is eight lines. It was that **finding the cause
required rebuilding the projection by hand in a Python session.** The product
detected the failure, refused correctly, discarded the reason, and then told the
reader to look up a record that is never written.

Every step of that was working as specified. Issue 103's redaction is right for a
journal. Issue 126's refusal is right to decline guessing. The transaction is
right to throw the staging copy away. The gap was that nobody owned the
operator's view, so five correct decisions composed into a wall.

## Three things worth carrying forward

- **A wrong probe nearly buried this.** Setting 104 to `active` by hand and
  validating produced no missing-artifact error, which read as proof the link
  check was innocent. It was not — that check reads its subject from
  `state.json`, which still said `''`, so it never ran. **A check that reads its
  subject from a projection cannot be exercised by editing the canonical file.**
- **The safe way to write an issue was the vague one.** `specs/<issue>/plan.md`
  started fine because `linked_artifacts` skips angle brackets; the real path
  refused. The product was rewarding imprecision, and nothing would have shown
  that except hitting it.
- **Two of my own tests were wrong before the code was.** They used an empty temp
  directory to exercise the projection-only branch, but an empty directory fails
  canonical validation first and takes the other branch. The fixture for "the
  canonical project is clean" is this repository.

## Known gaps

- **The rebuild is a re-run, not a recording.** It runs later than the failure,
  against a tree that may have changed, and can therefore disagree with what was
  actually rejected. The message says so. A recording would need the transaction
  to keep the projection, which is a larger change and would push against issue
  103's contract.
- **It copies the project — about 950 files here.** Acceptable on a stop path,
  and nothing calls it in a loop. If something ever does, this becomes a problem
  quickly.
- **An unchecked row's artifact is now invisible to this check.** If a required
  artifact is missing at completion, nothing here catches it. Issue 142 is the
  right owner — it is adding a rule about what a `done` issue must hold — and
  this issue deliberately did not build half of that gate.
- **`tasks.md` rides the `plan` row's checkbox.** It has no row of its own. That
  is stated and tested rather than incidental, but it is a convention, not a
  guarantee: an issue that lists `tasks.md` on a different row gets that row's
  checkbox instead.

## Next

`/moduflow loop`. 104 is active and its plan is next.
