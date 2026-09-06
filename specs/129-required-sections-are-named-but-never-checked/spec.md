# Spec: Required Sections Are Named But Their Content Is Never Checked

Issue: 129-required-sections-are-named-but-never-checked

## Problem

Two artifacts hand a person something to act on, and neither slot is checked. A
bug issue's cause can be an unverified guess — three reworks in one session came
from that. A spec's decision request can be four noun phrases with nothing to
decide with — spec 112 §15 cost the owner a round trip. `scripts/project_issue_schema.py`
enforces no required sections; `commands/product-spec.md` requires no decision
slots.

## Users

The person reading an artifact somebody else wrote and deciding what to do next.
For decision requests that is the owner; for bug causes it is whoever picks the
issue up.

## What the measurement changed

The issue assumed the checker could find its targets. Measured 2026-09-06, it
cannot — on either side.

**Issue side.** `- Type:` is free prose. Across 142 issues, 107 carry the line and
its values are sentences: `user product direction` (13), `product direction` (12),
`user multi-project orchestration improvement request` (7). Only **four** match
`Type:.*bug`, and one of those is a false positive — `Type: found while asking
how ModuFlow tracks a bug reported through the inbox`. So three issues are
machine-identifiable as bugs.

**There is no cause section.** `grep -l "^## Cause" issues/*.md` returns zero. The
cause lives inside `## Opportunity`, mixed with everything else. The rule "the
cause slot holds nothing but output" has no slot to apply to.

**Spec side.** Nine of 78 specs carry a decision section, under nine different
headings: `## Design Decisions`, `## Product Decisions`, `## Decision`,
`## Confirmed Design Decisions`, `## Review Gate`, `## 17. Human Review Decisions`,
`## 15. Human Review Decisions`, `## 6. Decision — Non-ASCII Status Tokens`,
`## Open-Source Pattern Review`. Two use `Reviewers must approve` (103 and 112).

**Correction to the issue.** It states "8 of 129 issues are bug-shaped, and 7 of
those already paste real command output." That number cannot be reproduced from
`Type:` and is not used here. The issue will be corrected rather than the spec
built on it.

**So the first half of this work is creating the anchors.** A content rule needs
a section to attach to and a way to know which artifacts it applies to. Neither
exists today. That is the part the issue did not say, and it is why this spec is
larger than "add a check".

## Goals

- One rule table, evaluated in one place, holding both rules and accepting a
  third without a new code path.
- A bug issue's cause is either pasted output or `원인 미상`, and never a hedge.
- A spec's open decision carries five slots a person can act on, and separates
  what the owner decides from what only needs ratifying.
- Every failure names the file and what to write, in Korean.

## Non-Goals

- Migrating 107 free-prose `Type:` lines, or the nine existing decision headings
  on `done` specs. New and open artifacts adopt the anchors; history does not.
- Judging quality. Whether pasted output supports the stated cause, or whether a
  filled slot reads clearly, is beyond a machine. See Risks.
- Non-bug issues. Feature and opportunity issues have no cause to prove.
- Moving validation into the stop hook. It runs where validation runs today.
- The five field-name display labels — issue 131 shipped them on 2026-09-06.

## Requirements

### R1 — The anchors

**Issue type.** `- Type:` must begin with one token from a closed set —
`bug`, `feature`, `opportunity`, `chore`, `audit` — optionally followed by ` — `
and any prose. `- Type: bug — reported by the owner, 2026-09-06` is valid and is
already the shape three issues use. An issue with no `Type:` line, or with prose
in the token position, is **skipped, not failed**: 107 issues predate this and
failing them would make the check unrunnable on day one.

**Cause section.** An issue whose type token is `bug` requires `## Cause`. Zero
exist today; the three real bug issues get one, moved out of `## Opportunity`.

**Decision section.** `## Human Review Decisions`, with an optional `N. ` number
prefix. 103 and 112 already use it. The other seven headings belong to `done`
specs and are not touched.

### R2 — The rule table

One table, entries of the form *(artifact kind, section, content rule)*,
evaluated in `scripts/validate_project_artifacts.py` where validation already
runs. The two rules below are its first two entries. A test asserts a third can
be added as data.

### R3 — Cause content

`## Cause` must hold either a fenced block containing command output, or the
literal `원인 미상` on its own line.

It must not contain: `추측`, `~것 같`, `~로 보임`, `hypothesis`, `suspicion`,
`likely`, `probably`. A match fails and the message quotes the phrase.

Issue 126 is why the ban is on the phrase rather than on an unlabelled guess. It
*did* label its guess — "That is a hypothesis from the error shape, **not
verified**" — and the next reader still went to the wrong function. Labelling was
not enough.

### R4 — Decision content

A spec whose `## Human Review Decisions` section exists and has any unapproved
item requires, per item:

- `왜 이 결정이 필요한가요?`
- `지금 무엇이 잘못되고 있나요?`
- `실제로 측정된 예시`
- `다른 선택지와 그 비용`
- `승인하면 무엇이 달라지나요?`

Each item is marked `[사장님 결정]` or `[확인만]`. A `[확인만]` item is one line
and needs no slots — it has a measured right answer and is being ratified, not
decided. An unmarked item fails.

This is the §15 lesson: four items at equal weight, only the first a real
judgement call. The owner read three engineering corrections to find the one
decision that was his.

A spec whose decisions are all approved passes without slots. A spec with no
decision section passes.

### R5 — Messages

Every failure names the file, the section, and what to write — in Korean, no rule
id. `commands/product-issue.md` and `commands/product-spec.md` state the rules,
following the `## 요약` precedent at `product-issue.md` step 7.

## Acceptance Criteria

- A bug issue whose `## Cause` contains a hedge fails; the message quotes the
  phrase and names the file.
- The same issue passes with `원인 미상`.
- A bug issue with no `## Cause` fails.
- An issue whose `Type:` token is not in the closed set is skipped, and a test
  asserts the 107 legacy issues neither fail nor are silently treated as bugs.
- The three real bug issues pass once given a `## Cause`.
- A spec with an unapproved decision missing any slot fails, naming spec,
  decision, and slot in Korean.
- An unmarked decision item fails; a `[확인만]` one-liner passes.
- A spec with all decisions approved, and a spec with no decision section, pass.
- Spec 112 §15 passes once its three remaining decisions carry slots or are
  marked `[확인만]`.
- Both rules run through one table; a test adds a third rule as data only and
  asserts it fires.
- Run against all 142 issues and 78 specs: only the intended artifacts fail, and
  the list of failures is asserted by name.
- `python3 scripts/release_check.py .` passes, `valid` checked at the top level.

## Verification Strategy

- Fixtures per rule: hedged cause, `원인 미상`, missing `## Cause`, non-bug type,
  absent `Type:` line.
- Fixtures per decision case: missing slot, unmarked item, `[확인만]` one-liner,
  all-approved, no section.
- A third rule added as data, asserting no code path was added.
- The 142 issues and 78 specs, with the expected failure list frozen.
- Hand a filled decision to the owner and confirm he can act without a round
  trip. Not automatable, and the only one that matters for R4.

## Risks

- **The skip rule could swallow the check.** 107 issues have prose in the type
  position and are skipped. If new issues keep writing prose there, the cause
  rule never fires and this ships as decoration. Mitigation: `commands/product-issue.md`
  states the closed set, and a test asserts every issue created after this lands
  carries a valid token. Without that second half, R1's skip is a hole.
- **A confidently worded wrong cause with real output pasted under it passes.**
  This catches the failure that happened, not every failure.
- **Filled slots can still be unreadable.** The check makes omission impossible,
  not prose true.
- **Hedge words in Korean are ambiguous.** `~것 같` appears in ordinary prose. The
  rule applies only inside `## Cause`, which is why the section anchor has to
  exist before the phrase ban can be safe.

## Open Questions

- Whether `## Cause` should be required on bug issues at creation time or only
  before `done`. Creation time matches the `## 요약` precedent; before-`done`
  matches issue 142's gate. **Recommendation: creation time**, because the whole
  point is that the cause is written when it is known, not reconstructed later.
- Whether the closed type set is the right five. Nothing measured decides this;
  the owner reviews it in the plan.

## Next Command

`/moduflow plan 129-required-sections-are-named-but-never-checked`
