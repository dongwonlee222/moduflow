# Issue 130: Decision Requests A Human Cannot Read

**Status: superseded-by-129** — absorbed into `129-required-sections-are-named-but-never-checked` on 2026-09-06. Merged because both halves need one section-content checker and no checker exists today; running them apart builds it twice. Nothing here was dropped — the five slots, the owner-decides/ratification split, and the §15 evidence all moved across. Kept for the record; do not implement from this file.
**Priority: p1**

## 요약

모두플로가 사람에게 승인을 요청할 때, **판단에 필요한 것을 안 줍니다.** 명세 112의
결정 4건은 "fail-closed at plan level, and the resulting 19 refused specs" 같은
한 줄짜리 항목입니다. 왜 필요한지, 지금 뭐가 문제인지, 19개가 뭔지, 다른 선택지는
뭔지, 승인하면 뭐가 좋아지는지 — 하나도 없습니다. 결정 요청에 5칸을 강제합니다.

## Summary

ModuFlow is a human-in-the-loop product: it stops and asks a person to approve.
The artifact it hands them is a bulleted list of noun phrases written for the
spec's author. Nothing in the schema requires a decision request to state why
the decision exists, what breaks today, what the alternatives cost, or what
approval buys.

## Source

- Type: bug — reported by the owner, 2026-09-06
- Owner / decision maker: Dongwon Lee
- Reported verbatim: "기준 미달이면 실행 계획을 안 만든다 19개 거부된다 이런것도
  바로 이해 안되거든?? 사람이 이해하기 쉽게 정리가 되어야해 휴먼인더루프 하려면"

## Opportunity

`specs/112-execution-planner-and-backend-boundary/spec.md` §15, as shipped:

```markdown
Reviewers must approve:

- fail-closed at plan level, and the resulting 19 refused specs (section 10);
- the whole-name section exclusion list and its growth path (section 6.1);
- treating a dependency on a completed task as satisfied (section 6.2);
- the `inline` conditions, in particular that shared state forces `inline`.
```

Four decisions, four noun phrases. To answer the first one a reader must know:

- what a worker plan is and why a file boundary matters,
- that plans are produced today with no boundary at all,
- that 19 of 55 specs would be refused, and that 34 others are simply finished,
- that two alternatives exist and what each costs.

None of it is in §15. All of it was available — `evidence/SIMULATION-REPORT.md`
holds the counts and enumerates the three options with their costs — but the
decision request does not carry it, and the reader has no reason to know that
file exists.

**Measured:** the owner could not act on §15 as written. The decision was made
only after the four facts above were assembled by hand from the simulation
report, and it took a round trip to do it.

There is precedent for the fix in this product. `commands/product-issue.md`
step 7 already requires a Korean `## 요약` on every issue **at creation time**,
with the stated reason that the slot exists "so the path is taken at creation
time rather than remembered later". The same argument applies to a decision
request, and no equivalent slot exists.

## Scope

### In

- **Separate the decisions a person must make from the ones only needing
  ratification.** §15 listed four items at equal weight. Only the first was a
  real decision — it costs the owner 19 refused specs. The other three each
  have a measured wrong answer (substring matching deleted 4 real tasks; string
  comparison put two workers on one file) or are already the shipped behaviour.
  Presenting all four identically made the owner read three engineering
  corrections to find the one judgement call. A decision request must say
  which is which, and the machine-verifiable ones must be stated in one line.
- A decision request must carry five things: why the decision exists, what
  goes wrong today, a concrete measured example, the alternatives with their
  costs, and what approval changes.
- The five slots are in Korean, matching the `## 요약` convention — the audience
  is the owner, not the spec's author.
- A check that fails a spec whose decision section has an empty or missing slot.
- `commands/product-spec.md` states the requirement, as step 7 does for issues.

### Out

- Judging whether the writing is *good*. A machine can check that a slot is
  filled, not that it is clear. See Known Limit.
- Rewriting the 55 existing specs. Only specs that carry an open decision
  need the slots; a spec whose decisions are already approved is history.
- Conversation style outside ModuFlow artifacts. That is covered by the two
  lines added to `~/.claude/CLAUDE.md` v8.2 on 2026-09-06 and is not a
  ModuFlow concern.
- The review packet (`human-review.ko.md`) and the dashboard. They render what
  the spec holds; fixing the source is the prerequisite.

## Known Limit

Filled slots can still be unreadable. This makes the omission impossible, not
the prose good. Stating it up front so a passing check is not mistaken for a
readable decision.

## Acceptance Criteria

- Every decision is marked either "owner decides" or "ratification", and a
  ratification item is one line. A spec with an unmarked decision fails.
- A spec with an open decision and any empty slot fails validation, and the
  failure names the spec, the decision, and the missing slot in Korean.
- A spec whose decisions are all approved passes without the slots.
- §15 of spec 112 passes once its remaining three decisions carry the slots.
- The failure message is itself readable by the owner — it names what to write,
  not a rule id.
- `python3 scripts/release_check.py .` passes, `valid` checked at the top level.

## Verification

- Fixture spec with one open decision missing the "what breaks today" slot.
- Fixture spec with all decisions approved and no slots.
- Run against the 55 live specs; assert only specs with open decisions fail.
- Hand the rendered output of a filled decision to the owner and confirm it can
  be acted on without a round trip. This is the only criterion that matters and
  it cannot be automated.

## Entry Points

- `specs/112-execution-planner-and-backend-boundary/spec.md:340` — §15, the
  example this issue is derived from
- `commands/product-spec.md` — where the requirement is stated
- `commands/product-issue.md` step 7 — the `## 요약` precedent to copy
- `scripts/validate_project_artifacts.py` — where the check would run
- `docs/output-format.md` — the existing output convention

## Scope Fence

Do not add the slots and then let them be filled with the English phrase that
was already there. The slot is for the reader, and the reader is the owner.

## Workflow Tasks

- [ ] spec → `specs/<issue>/spec.md`
- [ ] plan → `specs/<issue>/plan.md` + `tasks.md`
- [ ] execute → five-slot requirement, check, command text
- [ ] review → `specs/<issue>/review.md`

## Related Issues

- **The five field-name display labels (`rationale` → `왜 이렇게 정했나요?` and the
  rest) are owned by issue 131**, decided 2026-09-06. This issue cites them and
  does not define or implement them.
- related: `129-required-sections-are-named-but-never-checked` (the same shape one
  layer up — an issue that records a cause nobody can trust, versus a decision
  nobody can read), `112-execution-planner-and-backend-boundary` (the spec that
  exposed this), `121-constitution-amendment-invalidates-pilot-evidence`
  (proposes making the Korean-summary path a constitution principle)

## Next Command

`product:spec 130-decision-requests-a-human-cannot-read`
