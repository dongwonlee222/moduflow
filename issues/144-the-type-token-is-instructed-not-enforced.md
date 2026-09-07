# Issue 144: The Type Token Is Instructed, Not Enforced

**Status: superseded-by-142** — absorbed into `142-the-per-issue-artifact-set-is-named-but-never-required` on 2026-09-07. Both are the same shape — something is named in code and nothing checks it — and 142 builds the checking place. Running them apart builds it twice. Nothing is dropped: the token scope question, the 107 legacy issues and the `TODO(blocking-execution)` constraint all move across. Kept for the record; do not implement from this file.
**Priority: p2**

## 요약

이슈 129가 유형별 검사 규칙을 만들었는데, **유형을 안 써도 아무 일도 안 일어납니다.**
`product:issue`에 "붙여라"라고 적어만 뒀지 강제가 없습니다. 옛 이슈 107개는 일부러
건너뛰게 해 뒀는데, **새 이슈도 계속 문장으로 쓰면 규칙이 영원히 안 걸립니다.**
그러면 129는 장식이 됩니다.

## Summary

Issue 129 shipped `SECTION_RULES` keyed on a closed token set
(`bug` `feature` `chore` `spike`). An issue whose `- Type:` holds prose parses to
`None` and every type-keyed rule skips it. That skip is deliberate — 107 issues
predate the set and failing them would get the rule switched off — but it is
also the whole surface area of the defect: nothing distinguishes a legacy issue
from one written today with prose in the token position.

## Source

- Type: chore — follow-up named in `specs/129-required-sections-are-named-but-never-checked/review.md`
  on the day 129 shipped
- Owner / decision maker: Dongwon Lee

## 안 고치면

이슈 유형을 안 써도 아무 일이 안 일어나서 129의 규칙이 한 자리 숫자 이슈에만 걸립니다. — 기록. **142와 합칠 후보.**

## Opportunity

`scripts/validate_project_artifacts.py`, `parse_type_token`:

```python
if token not in TYPE_TOKENS:
    return (None, value)
```

and `check_sections`:

```python
if rule.kind == "issue" and token is None:
    continue
```

Together: no token, no rules, no message. `commands/product-issue.md` step 9 now
tells the agent to assign one, and `templates/issues/issue.md` carries a
`{{type_token}}` slot — both are instruction. `scripts/project_promote.py` is the
only path that guarantees *something* lands there, and what it lands is a
`TODO(blocking-execution)` marker, which also parses to `None`.

Measured 2026-09-06, immediately after 129 shipped: 142 issues, 107 with a
`Type:` line, and the number carrying a valid token is the handful written today.
Every rule in `SECTION_RULES` currently fires on a single-digit population.

kubernetes is the counter-example 129's own spec cites: twelve `kind/` labels
survive as a taxonomy because four issue templates each force exactly one at
creation. ModuFlow now has the taxonomy and the templates, and no forcing.

## Scope

### In

- Decide what counts as an issue that must carry a token. Candidates: created
  after a stated date, or created after a stated issue number, or carrying a
  marker the template writes. Each is checkable; none is obviously right, which
  is why 129 stopped rather than guessing.
- A check that fails such an issue when the token is missing or is prose.
- The failure names the file and lists the four tokens, in Korean.
- Leave the 107 legacy issues passing, asserted by test.

### Out

- Migrating the 107. They keep their prose. If that changes it is a separate
  decision with a separate issue.
- Adding tokens to the set. `bug` `feature` `chore` `spike` were settled on
  2026-09-06 against twelve external sources; reopening that is not this.
- Making `project_promote.py` guess a token. It writes a blocking TODO on
  purpose — a guess there would seed the exact field the cause rule keys off.
  A promoted issue is already marked not-executable; this issue must not turn
  that into a hard failure at promote time.

## Known Limit

A gate can require a token. It cannot require the right one. Someone who does
not want to write a `## 원인` can type `chore` and be believed — `chore` is the
bucket and demands nothing. That is the cost of having a bucket, and the
alternative (no bucket) was rejected in 129 for a reason.

## Acceptance Criteria

- The definition of "must carry a token" is stated in one place and cited by
  `commands/product-issue.md`.
- An issue in scope with a prose `Type:` fails validation; the message names the
  file and the four tokens in Korean.
- An issue in scope with no `Type:` line at all fails the same way.
- All 107 legacy issues pass, asserted against the live tree.
- A promoted issue carrying `TODO(blocking-execution)` does not hard-fail at
  promote time.
- `python3 scripts/release_check.py .` passes, `valid` checked at the top level.

## Verification

- Fixture in scope with prose in the token position → fails.
- Fixture in scope with no `Type:` line → fails.
- Fixture out of scope with prose → passes.
- Run against all live issues; assert the failing set is exactly the expected
  names.
- `tests/test_section_content_rules.py`.

## Entry Points

- `scripts/validate_project_artifacts.py` — `parse_type_token`, `TYPE_TOKENS`,
  `check_sections`, `validate_section_content`
- `commands/product-issue.md` steps 9–10 — the instruction that is not enforced
- `templates/issues/issue.md` — the `{{type_token}}` slot
- `scripts/project_promote.py` — the `TODO(blocking-execution)` producer
- `specs/129-required-sections-are-named-but-never-checked/review.md` — where
  this gap was recorded rather than quietly left

## Scope Fence

Do not close this by removing the skip and failing all 107. That is the failure
mode 129's plan named first: a rule that fires on history gets switched off
rather than fixed, and switching it off costs more than the gap does.

## Workflow Tasks

- [ ] spec → `specs/<issue>/spec.md`
- [ ] plan → `specs/<issue>/plan.md` + `tasks.md`
- [ ] execute → scope definition, the check, the message
- [ ] review → `specs/<issue>/review.md`

## Related Issues

- follows_up: `129-required-sections-are-named-but-never-checked` (shipped the
  rules this makes fire)
- related: `142-the-per-issue-artifact-set-is-named-but-never-required` (the same
  shape one level up — a set that is named and never required),
  `120-silent-status-fallback-in-issue-parser` (an unrecognised value silently
  demoted rather than reported)

## Next Command

`product:spec 144-the-type-token-is-instructed-not-enforced`
