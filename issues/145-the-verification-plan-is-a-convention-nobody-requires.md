# Issue 145: The Verification Plan Is A Convention Nobody Requires

**Status: superseded-by-142** — absorbed into `142-the-per-issue-artifact-set-is-named-but-never-required` on 2026-09-07. Same shape and same checking place. Nothing is dropped: the canonical heading, the runnable-command content rule, and the verdict owed on `product-plan.md`'s TDD matrix all move across. Kept for the record; do not implement from this file.
**Priority: p1**

## 요약

**"이걸 어떻게 확인할 것인가"를 적는 칸이 명세에는 79개 중 11개에만 있습니다.**
계획은 69개 중 20개입니다. 게다가 이름이 제각각이라(`Verification Strategy`,
`Testing Strategy`, `Tests`, `Validation`…) 기계가 찾지도 못합니다. 그리고
`product:plan`은 TDD 표를 실어 놓고 **"이건 안내일 뿐 실행을 막지 않는다"**고
스스로 적어 뒀습니다. **확인 방법을 안 적어도 아무 일도 안 일어납니다.**

## Summary

Every ModuFlow artifact template carries a verification slot, and almost no spec
or plan fills one. Nothing checks. `commands/product-plan.md` goes further and
states in writing that its TDD guidance is not a gate.

## Source

- Type: bug — reported by the owner, 2026-09-06: "이슈를 만들고 계획을 짜고 할때
  tdd 기반으로 해둬야 안 빠트릴거 같은데 … 검증 계획도 있어야 하지 않을까"
- Owner / decision maker: Dongwon Lee

## 원인

```
$ grep -l "^## .*\(Verification\|Verify\|Test\|Validation\)" specs/*/spec.md | wc -l
11
$ ls specs/*/spec.md | wc -l
79

$ grep -l "^## .*\(Verification\|Verify\|Test\)" specs/*/plan.md | wc -l
20
$ ls specs/*/plan.md | wc -l
69

$ grep -h "^## .*\(Verification\|Verify\|Test\|Validation\)" specs/*/spec.md | sed 's/^## //' | sort | uniq -c | sort -rn
   3 Verification Strategy
   2 Verification
   2 Testing Strategy
   1 Validation
   1 Test Strategy
   1 16. Verification Strategy
   1 13. Verification Strategy

$ grep -c "Verification" scripts/validate_project_artifacts.py scripts/project_issue_schema.py
scripts/validate_project_artifacts.py:0
scripts/project_issue_schema.py:0
```

Three facts, all from those four commands. Specs carry a verification section 14%
of the time and plans 29%. Seven different headings across eleven specs, so even
the ones that have it are not findable by name. And no validator mentions the
word at all.

Issues are the exception and are fine: 64 of 143 carry `## Verification`, and only
**4 open issues** lack one. The gap is downstream — the artifact that says what
will be built does not say how anyone will know it worked.

### The discipline is declared non-binding in writing

`commands/product-plan.md:28-40` ships a matrix — "A — behavior change →
Superpowers TDD + focused tests | Routing, parser, command, or validator behavior
must prove RED/GREEN" — and then:

> The matrix is guidance, not an execution gate. Do not block `product:execute`
> from this section alone; issue 077 owns implementation-readiness gates.

So the strongest statement this product makes about proving behaviour explicitly
disclaims enforcement, and points at an issue for the enforcement.

### Why this is the same defect twice already named

Issue 142: the per-issue artifact set is named and never required. Issue 129: the
sections a reader depends on are named and never checked. This is the third
instance of the shape, and unlike the other two it now has a mechanism waiting —
129 shipped `SECTION_RULES`, and a verification rule is a row in it.

## 안 고치면

명세 79개 중 11개에만 검증 계획이 있습니다. 무엇이 됐는지 확인할 방법이 없습니다. — 기록. **142와 합칠 후보.**

## Scope

### In

- One canonical heading for the verification section in specs and plans. The
  seven existing names are the same problem the nine decision headings were
  (issue 129) — pick one and cite it in the commands.
- A `SECTION_RULES` row requiring it on open specs and plans, with a content rule
  narrow enough to be honest: at least one runnable command or one named test
  file. Prose alone is not a verification plan.
- Decide whether the `product:plan` TDD matrix becomes binding, and for which
  stream. If it stays guidance, say so where a reader will see it rather than in
  a note under the table.
- `commands/product-spec.md` and `commands/product-plan.md` state the
  requirement, as `product-issue.md` step 7 does for `## 요약`.

### Out

- Retrofitting 68 specs and 49 plans. History keeps its shape; only open work is
  checked, the rule 129 already established.
- Judging whether the named commands actually verify anything. A machine can
  check that a command is named, not that running it proves the claim.
- Implementation-readiness gates in general — `issues/077` owns those, and
  `product-plan.md` already points there. This issue is about the artifact
  carrying a verification plan, not about blocking execution on it.
- Issues. 4 open ones lack the section; that is a fix, not an issue.

## Known Limit

A required section produces a filled section. Someone can write `python3 -m
unittest` and satisfy the rule without having thought about what could go wrong.
What this removes is the case where nobody wrote anything at all — 68 specs
today — not the case where someone wrote something thin.

## Acceptance Criteria

- One heading is canonical, stated in one place and cited by both commands.
- An open spec or plan with no verification section fails, naming the file and
  the heading in Korean.
- A section with no runnable command and no named test file fails.
- `done` and `superseded` artifacts are unaffected, asserted against the live
  tree.
- The 4 open issues missing `## Verification` are fixed in the same change.
- The TDD matrix's binding status is stated explicitly, whichever way it goes.
- `python3 scripts/release_check.py .` passes, `valid` checked at the top level.

## Verification

- Fixture spec with no verification section → fails.
- Fixture with a prose-only section → fails.
- Fixture with one named test file → passes.
- Fixture that is `done` with no section → passes.
- Run against all 79 specs and 69 plans; assert the failing set is exactly the
  open ones.
- `tests/test_section_content_rules.py`.

## Entry Points

- `scripts/validate_project_artifacts.py` — `SECTION_RULES`, where the row goes
- `commands/product-plan.md:28-40` — the TDD matrix and its disclaimer
- `commands/product-spec.md` — where the requirement is stated
- `templates/specs/spec.md`, `templates/specs/plan.md` — the slots that exist
- `specs/129-required-sections-are-named-but-never-checked/spec.md` — the rule
  table this extends

## Scope Fence

Do not make this a row that fires on all 79 specs. 129's plan named that failure
first and it happened within a minute of its first live run: a rule that fails
history gets switched off rather than fixed.

## Workflow Tasks

- [ ] spec → `specs/<issue>/spec.md`
- [ ] plan → `specs/<issue>/plan.md` + `tasks.md`
- [ ] execute → canonical heading, the rule, both command texts, the TDD verdict
- [ ] review → `specs/<issue>/review.md`

## Related Issues

- follows_up: `129-required-sections-are-named-but-never-checked` (shipped the
  table this is a row in, and settled the open-work-only rule)
- related: `142-the-per-issue-artifact-set-is-named-but-never-required` (the same
  shape at the file level), `077` (owns implementation-readiness gates, which
  this deliberately does not touch),
  `144-the-type-token-is-instructed-not-enforced` (the same gap between
  instruction and enforcement)

## Next Command

`product:spec 145-the-verification-plan-is-a-convention-nobody-requires`
