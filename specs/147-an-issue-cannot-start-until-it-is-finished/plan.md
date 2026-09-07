# Plan: An Issue Cannot Start Until It Is Finished

Issue: 147-an-issue-cannot-start-until-it-is-finished

## Approach

Two independent fixes, tests first for each.

1. **R1 — the ordering.** `linked_artifacts` blanks out unchecked Workflow Tasks
   rows before collecting links. Scoped to that one section; `## Links` and
   `## Entry Points` keep today's behaviour because they name things that exist.
2. **R2 — the diagnosis.** `refusal_lines` gains `issue_id` and `action`, and a
   new `projected_validation_sentences` rebuilds the rejected projection and
   validates it directly. Only on the refusal path — it copies the project.
3. **R3** falls out of R2: the impossible instruction is deleted rather than
   repaired, because the detail is now in the message.

Issue 103's redaction is untouched. Nothing is read out of the result envelope
or the journal; the projection is rebuilt from the canonical files instead.

## Work Streams

- Implementation: `scripts/validate_project_artifacts.py` (one regex pair and
  one helper), `scripts/project_lifecycle.py` (`refusal_lines` signature,
  `projected_validation_sentences`).
- QA: below, RED first.
- Release: version bump, `release_check.py`.

## Verification

- `tests/test_section_content_rules.py` — six tests for R1, including the live
  issue 104 case and the checked-row guard.
- `tests/test_refusal_names_what_it_saw.py` — four tests for R2/R3, using this
  repository as the clean-canonical fixture.
- Live: start issue 104 through the transaction and record the result.
- Full suite and `release_check`.

## Rollback

Both changes are additive and local. Reverting restores the previous behaviour
exactly; no data is migrated and no artifact shape changes.

The one lasting effect is that issues written from now on may leave real paths in
unchecked rows, where before the only safe form was `specs/<issue>/…`. That is
the intended direction and a revert would make those issues unstartable again.

## Next Command

`/moduflow execute 147-an-issue-cannot-start-until-it-is-finished`
