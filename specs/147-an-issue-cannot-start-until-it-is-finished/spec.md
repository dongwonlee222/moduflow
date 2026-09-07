# Spec: An Issue Cannot Start Until It Is Finished

Issue: 147-an-issue-cannot-start-until-it-is-finished

## Problem

Two defects, found together on 2026-09-07 while trying to start issue 104.

**Ordering.** `validate_active_issue_links` requires every `specs/`, `workspace/`
or `memory/` path named anywhere in the active issue to exist. A Workflow Tasks
checklist names all four artifacts — `spec.md`, `plan.md`, `tasks.md`,
`review.md` — so an issue that writes real paths cannot become active until all
four exist. `review.md` is written last. **An issue must be finished to begin.**

Issue 132 starts fine because it writes `specs/<issue>/plan.md`, and
`linked_artifacts` skips any path containing `<` or `>`
(`validate_project_artifacts.py:321`). The issue that names its artifacts
precisely is the one that is punished.

**Diagnosis.** The refusal is `PROJECTED_VALIDATION_INVALID` and nothing else.
Extracting the two missing filenames took rebuilding the projection by hand in a
Python session. Everything the product offers is a dead end:

- One error code covers every way a projected state can fail.
- Issue 103 redacts the result envelope to logical identifiers and hashes.
  Correct for a journal; it also makes the failure unreadable.
- **The refusal's own instruction is impossible.** It says to re-run with the
  transaction id and report it. `--recover txn-fe868e0f…` returns
  `RECOVERY_JOURNAL_MISSING`, and the id appears nowhere in the repository — a
  projected-validation failure never reaches the journal stage, so the id names
  a record that was never written.

## Users

Whoever runs a lifecycle transition and is told no. Today that is the owner and
me; the same refusal reaches any agent doing the same thing.

## Goals

- An issue can start with the artifacts it actually has.
- A projection-only refusal names the failing artifact and rule.
- The refusal's instructions are things the reader can do.
- Issue 103's redaction contract is untouched.

## Non-Goals

- Un-redacting the journal record or the transaction result envelope. Three
  contract tests enforce that and they stay green.
- Changing what `PROJECTED_VALIDATION_INVALID` refuses. Some projections should
  be rejected; this is about seeing why.
- The one-active-issue limit (issue 133) or `pause` not pausing (issue 132's
  second defect). Both were hit the same session and both belong to their issues.
- Removing the placeholder skip in `linked_artifacts`. `specs/<id>/spec.md` in
  documentation is not a link and should stay skipped.

## Requirements

### R1 — A workflow checklist is a plan, not a manifest

The Workflow Tasks section lists what an issue *will* produce. Its rows must not
be read as artifacts that must already exist.

**The rule: a checked row's artifact must exist; an unchecked row's must not be
required.** That is what the checkbox already means, and it makes the ordering
work in both directions — a row marked `[x]` whose file is missing is a real
defect and stays caught.

Scoped to the Workflow Tasks section. Links elsewhere in an issue — `## Links`,
`## Entry Points`, `## Related Issues` — keep today's behaviour, because those
name things that exist.

### R2 — The refusal names what it saw

When a lifecycle transaction fails at projected-validation and the canonical
project is clean, `refusal_lines` rebuilds the projection and reports its
errors, in Korean, naming file and rule.

This extends the pattern issue 126 established rather than inventing one. 126
re-validates the **canonical** project because the transaction's own summary is
redacted; the gap it could not cross is that a projection-only failure has
nothing canonical to report. Rebuilding the projection is the same move one
level deeper.

The rebuild happens **only on the refusal path**. It copies the project, so it
is not free; a refusal is already a stop, and being told why is worth one copy.

### R3 — No instruction that cannot be followed

The current text ends: "re-run with the transaction id above and report it".
Measured: that cannot be done. Either the message names a command that works, or
it names none.

Since R2 puts the detail in the refusal itself, the instruction becomes
unnecessary and is removed rather than repaired.

## Acceptance Criteria

- Issue 104 starts with `spec.md` present and `plan.md`, `tasks.md`,
  `review.md` absent. This is the exact case that failed.
- An issue whose Workflow Tasks use real paths and one using
  `specs/<issue>/…` placeholders both start. A test asserts both.
- A checked row (`- [x] spec → …`) whose file is missing still fails. The fix
  must not turn the check off.
- A projection-only refusal lists each projected error with its file, in Korean.
- No refusal text tells the reader to look up a transaction id.
- The issue 103 redaction contract tests pass unchanged, and a test asserts the
  transaction module's result envelope keys are unchanged.
- `python3 scripts/release_check.py .` passes, `valid` checked at the top level.

## Verification Strategy

- Fixture: issue with `- [x] spec` (file present) and `- [ ] plan` (absent) →
  starts.
- Fixture: issue with `- [x] plan` and the file absent → refuses, naming it.
- Fixture: placeholder paths → starts, unchanged from today.
- Fixture: a projection-only failure → assert the refusal names the artifact.
- The three issue 103 redaction tests, unchanged.
- Live: start issue 104 and record the outcome.

## Risks

- **R1 could hide a real missing artifact.** An unchecked row whose file is
  genuinely required later is now invisible to this check. Issue 142 is the
  right owner for that — it is adding a rule about which artifacts a `done`
  issue must hold — and this spec must not duplicate it. Stated so the two do
  not each build half a gate.
- **R2 copies the project on every projection-only refusal.** ~950 files here.
  Acceptable on a stop path; it would not be acceptable in a loop, and nothing
  should call it in one.
- **The rebuild can disagree with the original.** It runs later, against a tree
  that may have changed. The message must say it is a re-run, not a recording,
  so a reader who sees different errors is not misled.

## Open Questions

- Whether `tasks.md` should be checked at all. It has no row of its own — it is
  named on the `plan` row alongside `plan.md`. Whatever R1 does with it should
  be stated, not incidental.

## Next Command

`/moduflow plan 147-an-issue-cannot-start-until-it-is-finished`
