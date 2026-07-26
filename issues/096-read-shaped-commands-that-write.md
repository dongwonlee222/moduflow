# Issue 096: Read-Shaped Commands That Write

**Status: backlog** — created 2026-07-26.
**Priority: p2**
**Blocked-by:**

## Summary

Stop commands that read like inspection from silently overwriting completed artifacts, starting with `project_converge.py --evidence`.

## Source

- Type: observed twice during issue 095 implementation and review
- Link: `specs/095-commit-issue-resolution-parity/status.md` — Known gaps
- Date: 2026-07-26

## Problem

`python3 scripts/project_converge.py <path> --issue-id <id> --evidence --json` reads as an
inspection command. Its output goes to stdout, its flag is named for gathering evidence, and
`commands/product-review.md` step 5 presents it as the way to *look at* an issue's commits.

It also rewrites `specs/<issue>/converge-evidence.json` with no confirmation and no dry-run
flag.

Measured twice on 2026-07-26 while working on issue 095: running it to inspect issue 093's
collection silently replaced 093's completed review record — a `generated` date and a commit
list captured at review time, on an issue that is done and merged. Both times the overwrite
was noticed only because `git status` happened to be checked afterwards, and both times it was
reverted by hand. Nothing in the command's output said a file had changed.

The independent reviewer of issue 095 was told explicitly not to run it, and recorded that
instruction as a limitation on the review: a reviewer could not use the project's own evidence
tool to examine evidence.

This is the same failure class issue 095 exists for, one level up. A gate reports success
while what it destroyed sits outside the report — except here the destroyed thing is the
historical record a later reviewer would have compared against.

## Product Decision

- Inspection is the default. Writing is opt-in, not opt-out.
- An artifact that belongs to a completed issue is not rewritten by a command run for a
  different issue's investigation.
- Any write announces itself in the command's own output, in both `--json` and human modes.

## Scope

### In

- A read-only default for `--evidence`, with writing behind an explicit flag.
- A survey of the other `scripts/*.py` entry points for the same shape — a read-sounding flag
  that mutates a tracked file without saying so.
- Regression tests that fail if an inspection-shaped invocation modifies the working tree.

### Out

- Changing the evidence schema or what converge collects.
- Adding confirmation prompts to genuinely write-shaped commands (`--apply-judgment`,
  `--write`), which already name what they do.
- Retroactively restoring evidence files overwritten before this issue.

## Acceptance Criteria

- `--evidence` without a write flag leaves the working tree byte-identical; proven by a test
  that diffs the tree around the call.
- When a write does occur, the path written appears in stdout in both output modes.
- The audit lists every `scripts/*.py` flag that writes a tracked file, and each is either
  named for writing or moved behind an explicit flag.
- `python3 scripts/release_check.py .` passes.

## Verification

- `python3 -m unittest tests.test_project_converge -v`
- `python3 scripts/release_check.py .`

## Entry Points

- `scripts/project_converge.py`
- `commands/product-review.md`
- `tests/test_project_converge.py`

## Scope Fence

Do not change the converge evidence schema, what it collects, or the review verdict logic.

## Workflow Tasks

- [ ] spec → `specs/096-read-shaped-commands-that-write/spec.md`
- [ ] plan → `specs/096-read-shaped-commands-that-write/plan.md`
- [ ] execute → PR / commits
- [ ] review → review notes

## Related Issues

- blocks:
- blocked_by:
- duplicates:
- follows_up: `095-commit-issue-resolution-parity`
- supersedes:
- related: `071-spec-code-converge-check`

## Sessions

- 2026-07-26: observed twice while implementing and reviewing issue 095. Registered rather
  than fixed inline, to keep it out of 095's scope.

## Links

- Spec: `specs/096-read-shaped-commands-that-write/spec.md`
- Roadmap: `workspace/roadmap.md`

## Next Command

`/product:spec 096-read-shaped-commands-that-write`
