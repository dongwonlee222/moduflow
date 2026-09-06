# Review: Required Sections Are Named But Their Content Is Never Checked

Issue: 129-required-sections-are-named-but-never-checked

## What shipped

`ba75b0f`. `SECTION_RULES` and four helpers in
`scripts/validate_project_artifacts.py`, called once from `validate_project`;
22 tests; `commands/product-issue.md` steps 9–10 and a new section in
`commands/product-spec.md`; `templates/issues/issue.md`; a type-token producer in
`scripts/project_promote.py`; and three real artifacts brought into compliance.
Both manifests 0.3.69.

## Did it work

- 22 new tests, green. Recorded RED first at 34 errors.
- Full suite: **1927 tests, OK**, 263s.
- `release_check.py` → `valid: true`, no failing gate.
- `validate_project_artifacts.py .` → `valid: true`, zero errors, with the rules
  live.

## The part that mattered, and it was not the checker

The issue said "add a check". The check is about forty lines. The work was that
the check had nothing to attach to:

- `- Type:` held **provenance**, not kind. 107 of 142 issues carry prose there.
- No issue had a cause section at all — zero.
- Nine of 78 specs carried a decision section, under nine different headings.

So the shape of the change is a token parser, a section finder, and a table —
and the two content rules are the smallest part of it. Anything written as
"just add a validation rule" for an artifact this product has never structured
will have the same ratio.

## The trap the plan named, sprung on schedule

Wiring the rules in without a status filter failed `specs/103` and `specs/120`
on decisions settled long ago. The plan had written this down — "a rule that
fires on 142 legacy artifacts on day one gets switched off" — and it happened
within a minute of the first live run.

Fixed by checking only `backlog` and `active` work, and by skipping items already
marked `**[approved …]**`. That leaves the rule firing on exactly the artifacts a
person could still act on.

## Three artifacts fixed rather than exempted

- **129** gained a `## 원인` holding real command output: the three greps showing
  the validator never references the artifact set, that no `## 원인` existed, and
  that only 4 of 142 issues are machine-identifiable as bugs.
- **112 §15**'s three ratified items got `[확인만]`. They were already approved in
  prose; the marker makes that machine-visible.
- **120**'s three decisions were rewritten — two `[확인만]`, one `[사장님 결정]`
  with all five slots filled from the spec's own sections 6 and 7. **This is the
  first decision request the rule has actually made readable**, and it is the
  only evidence so far that the rule does what it exists to do.

## Decisions taken during execute

- **`promote` writes a blocking TODO, not a guess.** A promoted record does not
  say which of the four it is. Inferring one would put an unverified claim in the
  exact field the cause rule keys off — the failure this issue exists to prevent.
  It uses the convention issue 121 established for the Korean slot, so the marker
  already means "not executable until a person fills it".
- **Inline YAML comment in the issue template**, not a schema change, so the
  guidance sits where someone writing an issue will see it.
- Two `test_project_promote` assertions were updated: the `- Type:` line shape,
  and the TODO count 7 → 8. Both are the designed change, not a test bent to fit.

## Known gaps

- **The skip rule is still the biggest risk, and it is not closed.** 107 issues
  are skipped. `product-issue.md` now tells the agent to assign a token, but
  nothing *fails* when a new issue arrives without one — the entry gate is
  instruction, not enforcement. If issues keep being written with prose in the
  type position, these rules never fire and this ships as decoration. The honest
  next step is a check that new issues carry a token, which needs a definition of
  "new" this issue does not have.
- **Codex is unverified** for none of this — it is pure Python and Markdown, so
  it applies equally. Noted only because 131's mechanism did not.
- **The `unreadable` hedge list is Korean-and-English guesswork.** Seven phrases,
  chosen from the three reworks that happened. A confident wrong cause with real
  output pasted under it still passes.
- **`## Goal` and `## Findings` have never fired.** No issue is `- Type: spike`
  yet. The rule is written and tested against fixtures only.

## Next

`/moduflow loop`. The issue can close once the owner accepts the skip-rule gap
as a follow-up rather than part of this.
