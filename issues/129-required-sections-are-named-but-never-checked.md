# Issue 129: Required Sections Are Named But Their Content Is Never Checked

**Status: backlog** — created 2026-09-06. Absorbed issue 130 on 2026-09-06.
**Priority: p1**

## 요약

사람이 읽고 판단해야 하는 칸이 **비어 있거나 추측으로 채워져 있어도 아무도 안
봅니다.** 두 가지가 같은 구멍입니다 — 버그 이슈의 **원인 칸에 확인 안 된 추측**이
들어가서 다음 사람을 엉뚱한 코드로 보내고(한 세션에 3번 다시 씀), 명세의 **승인
요청 칸**에는 왜 필요한지·지금 뭐가 문제인지·다른 선택지가 뭔지가 아예
없습니다(112 결정 4건, 전부 한 줄짜리 명사구). 칸을 정하고, **내용을 검사하는
장치 하나**를 만듭니다.

## Summary

Two defects, one missing mechanism. An artifact section can be absent, empty, or
filled with a guess, and validation passes either way. The issue schema enforces
no required sections and no content rule.

This issue was merged from 129 and 130 on 2026-09-06. Running them separately
would build the same section-content checker twice.

## Source

- Type: bug — three reworks in one session, 2026-09-06 (the cause half)
- Type: bug — reported by the owner, 2026-09-06 (the decision half): "기준 미달이면
  실행 계획을 안 만든다 19개 거부된다 이런것도 바로 이해 안되거든?? 사람이
  이해하기 쉽게 정리가 되어야해 휴먼인더루프 하려면"
- Owner / decision maker: Dongwon Lee
- Merge decided 2026-09-06 — no checker exists today, so the two halves are one
  build

## 원인

검사기가 없어서가 아니라, **검사기가 붙을 자리가 없어서**입니다. 아래는 이 이슈를
쓰기 직전 저장소 상태입니다.

```
$ grep -c "_ARTIFACT_PHASES\|coverage\[" scripts/validate_project_artifacts.py scripts/release_check.py
scripts/validate_project_artifacts.py:0
scripts/release_check.py:0

$ grep -l "^## 원인" issues/*.md | wc -l
0

$ grep -h "^- Type:" issues/*.md | sed 's/.*Type: //' | sort | uniq -c | sort -rn | head -3
  13 user product direction
  12 product direction
   7 user multi-project orchestration improvement request

$ grep -l "^- Type:.*bug" issues/*.md | wc -l
4
```

세 줄이 각각 하나씩 말합니다. 검증기는 아티팩트 집합을 아예 참조하지 않고, 원인을
담는 섹션은 저장소에 하나도 없으며, 유형 칸은 "무슨 종류인가"가 아니라 "누가 왜
제기했나"를 담고 있어서 142개 중 4개만 버그로 식별됩니다.

## 안 고치면

이슈의 원인 칸에 추측이 들어가서 다음 사람이 엉뚱한 코드를 봅니다. 한 세션에 세 번 다시 썼습니다. — 기록

## Opportunity

### A — a cause slot that accepts a guess

Three reworks, same shape: a conclusion stated before the command that would
settle it was run.

| Where | Written | Actual |
| --- | --- | --- |
| Issue 126 | "the projection is probably incomplete" | wrong; the transaction had discarded its error list. Rewritten whole |
| Issue 120 | "this bug has never fired" | it had. Priority raised p2 → p1 |
| Commit `83f95c5` | "tests pass" (25 of 1858 run) | 3 failures |

Issue 126 is the important one. It **did** label the guess:

> That is a hypothesis from the error shape, **not verified**.

The label was honest and it still misled — the next reader went to the projection
code instead of to `_summarize_validation_result`, the function that drops the
error list. Labelling a guess is not enough; the guess must not be in the cause
slot at all.

**Corrected 2026-09-06 during spec.** An earlier draft said "8 of 129 issues are
bug-shaped, and 7 already paste real command output". That number cannot be
reproduced. Re-measured against 142 issues: `- Type:` is free prose (107 issues
carry it, with values like `user product direction`), and only **four** match
`Type:.*bug` — one of them a false positive. Three issues are machine-identifiable
as bugs.

And **no issue has a `## Cause` section**; the cause sits inside `## Opportunity`.
So the rule "the cause slot holds nothing but output" has no slot to attach to.
Creating that anchor is part of the work, not a precondition of it.

### B — a decision request that carries nothing to decide with

`specs/112-execution-planner-and-backend-boundary/spec.md` §15, as shipped:

```markdown
Reviewers must approve:

- fail-closed at plan level, and the resulting 19 refused specs (section 10);
- the whole-name section exclusion list and its growth path (section 6.1);
- treating a dependency on a completed task as satisfied (section 6.2);
- the `inline` conditions, in particular that shared state forces `inline`.
```

Four decisions, four noun phrases. To answer the first, a reader must know what a
worker plan is and why a file boundary matters, that plans are produced today
with no boundary at all, that 19 of 55 specs would be refused while 34 others are
simply finished, and that two alternatives exist with costs. None of it is in
§15. All of it was in `evidence/SIMULATION-REPORT.md`, which the reader has no
reason to know exists.

**Measured:** the owner could not act on §15 as written. The decision was made
only after those four facts were assembled by hand, and it took a round trip.

### Why they are one issue

Both are a section that looks like a gate and is a heading. `commands/product-issue.md`
has nine "Do" steps, all about shape and metadata, none requiring that a stated
cause be reproduced. `commands/product-spec.md` requires no decision slots at
all. `scripts/project_issue_schema.py` enforces no required sections for either.

There is precedent for the fix in this product: `commands/product-issue.md` step
7 already requires a Korean `## 요약` on every issue **at creation time**, "so the
path is taken at creation time rather than remembered later". The same argument
covers both halves, and no equivalent slot exists for either.

## Scope

### In

**One checker.** A rule table of the form *(artifact type, section, content
rule)*, evaluated where validation already runs. Both halves are entries in it.

**Cause (A):**

- A required cause section on bug-shaped issues holding either pasted command
  output or the literal `원인 미상`.
- A check that fails when it contains hedging language: `추측`, `~것 같`,
  `~로 보임`, `hypothesis`, `suspicion`, `likely`, `probably`.
- `commands/product-issue.md` states the rule, and states that a symptom-only
  issue with no cause is complete and correct.

**Decision (B):**

- **Separate the decisions a person must make from the ones only needing
  ratification.** §15 listed four at equal weight. Only the first was a real
  decision — it costs the owner 19 refused specs. The other three each have a
  measured wrong answer (substring matching deleted 4 real tasks; string
  comparison put two workers on one file) or are already the shipped behaviour.
  Presenting all four identically made the owner read three engineering
  corrections to find the one judgement call. A ratification item is one line.
- A decision request carries five things: why the decision exists, what goes
  wrong today, a concrete measured example, the alternatives with their costs,
  and what approval changes.
- The five slots are in Korean, matching the `## 요약` convention — the audience
  is the owner, not the spec's author.
- `commands/product-spec.md` states the requirement, as step 7 does for issues.

**Plain language (added 2026-09-06, owner-approved).**

- Both commands carry a rule: **a word the reader is meeting for the first time
  is explained where it is used, or not used at all.** The test is one question —
  *would someone seeing this word for the first time know what it means?*
- Not machine-checkable, and stated as such so a passing validation is never
  mistaken for a readable artifact.
- It exists because the five slots were not enough. On 2026-09-06 two decision
  requests had every slot filled and the owner still could not act on either:
  one said "the diagnostic must reach `doctor` output" without saying that
  `doctor` output is a 31-key JSON dump, and one said "remove the translator"
  about a translator that does not exist yet. **Filling a slot and being read
  are different things**, and the earlier scope only covered the first.

### Out

- Non-bug issues. Feature and opportunity issues have no cause to prove — issue
  121 has no pasted output and is correct as written. The check keys off issue
  type.
- Judging whether the content is *good*: whether a pasted output supports the
  stated cause, or whether a filled slot reads clearly. See Known Limit.
- Rewriting the 55 existing specs. Only specs carrying an **open** decision need
  the slots; a spec whose decisions are approved is history.
- Wiring the check into the stop hook. Validation runs at `release_check` today;
  moving it earlier is a separate change, and doing both at once means a failure
  cannot be attributed to either.
- Conversation style outside ModuFlow artifacts — covered by two lines added to
  `~/.claude/CLAUDE.md` v8.2 on 2026-09-06.
- The five field-name display labels (`rationale` → `왜 이렇게 정했나요?` and the
  rest). **Owned by issue 131**, shipped 2026-09-06 in `commands/product-decision.md`.
  This issue cites them.
- The review packet and the dashboard. They render what the artifact holds;
  fixing the source is the prerequisite.

## Known Limit

Both halves catch the failure that happened, not every failure. A confidently
worded wrong cause with real output pasted under it passes. Filled slots can
still be unreadable. This makes the omission impossible, not the prose true —
stating it up front so a passing check is not mistaken for a correct artifact.

## Acceptance Criteria

- A bug issue whose cause section contains hedging language fails validation,
  naming the issue file and the offending phrase.
- The same issue passes once the cause is replaced with `원인 미상`.
- The three machine-identifiable bug issues pass once given a `## Cause`, and
  the 107 issues whose `Type:` is free prose are skipped rather than failed.
- Non-bug issues are unaffected.
- Every decision is marked either "owner decides" or "ratification", and a
  ratification item is one line. A spec with an unmarked decision fails.
- A spec with an open decision and any empty slot fails, and the failure names
  the spec, the decision, and the missing slot in Korean.
- A spec whose decisions are all approved passes without the slots.
- §15 of spec 112 passes once its remaining three decisions carry the slots.
- Both halves run through **one** rule table; a test asserts a third rule can be
  added without a new code path.
- Every failure message names the file and what to write — not a rule id.
- Both commands state the plain-language rule with at least one worked
  before/after example. Asserted by a test that the section exists; whether the
  writing obeys it cannot be tested and is not claimed to be.
- `python3 scripts/release_check.py .` passes, `valid` checked at the top level.

## Verification

- Fixture bug issue with a hedged cause → fails, message names the phrase.
- Same fixture with `원인 미상` → passes.
- Fixture feature issue with no cause section → passes.
- Fixture spec with one open decision missing the "what breaks today" slot.
- Fixture spec with all decisions approved and no slots.
- Run against all 129 existing issues and 55 specs; assert only genuine
  violations fail.
- Hand the rendered output of a filled decision to the owner and confirm it can
  be acted on without a round trip. This is the only criterion that matters and
  it cannot be automated.

## Entry Points

- `commands/product-issue.md` — nine Do steps with no proof requirement; step 7
  is the `## 요약` precedent to copy
- `commands/product-spec.md` — where the decision requirement is stated
- `scripts/project_issue_schema.py` — enforces no required sections today
- `scripts/validate_project_artifacts.py` — where the rule table would run
- `specs/112-execution-planner-and-backend-boundary/spec.md:340` — §15, the
  decision example
- `issues/126-sync-refuses-the-drift-it-is-prescribed-for.md` — the rewrite the
  cause rule is derived from
- `docs/output-format.md` — the existing output convention

## Scope Fence

Do not add a suppression list, and do not extend the cause check to non-bug
issues. A cause that cannot be classified is a rule to sharpen, not an exception
to file.

Do not add the decision slots and then let them be filled with the English
phrase that was already there. The slot is for the reader, and the reader is the
owner.

## Workflow Tasks

- [x] spec → `specs/<issue>/spec.md`
- [x] plan → `specs/<issue>/plan.md` + `tasks.md`
- [x] execute → rule table, cause rule, five-slot rule, both command texts
- [x] review → `specs/<issue>/review.md`

## Related Issues

- supersedes: `130-decision-requests-a-human-cannot-read` — absorbed 2026-09-06.
  Merged rather than sequenced because no section-content checker exists and
  running them apart builds it twice.
- related: `126-sync-refuses-the-drift-it-is-prescribed-for` (the rewrite that
  produced the cause rule), `120-silent-status-fallback-in-issue-parser`,
  `128-linked-artifact-check-runs-for-one-issue-only` (a check that ignores
  without saying why), `112-execution-planner-and-backend-boundary` (the spec
  that exposed the decision half),
  `121-constitution-amendment-invalidates-pilot-evidence` (proposes making the
  Korean-summary path a constitution principle),
  `131-command-surface-is-too-wide-and-english-only` (owns the five display
  labels this issue cites),
  `142-the-per-issue-artifact-set-is-named-but-never-required` (the same shape
  one level up — whether the artifacts exist at all)

## Next Command

`product:spec 129-required-sections-are-named-but-never-checked`
