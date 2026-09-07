# Issue 136: Auto Playbook Checks Are Never Executed

**Status: superseded-by-123** — absorbed into `123-empty-declarations-file-disables-linkage-warning` on 2026-09-07. Both check that a file exists and never read what is in it. Nothing is dropped: `project_production.py:213`'s unreached evaluator and the `[auto]` check contract move across. Note that 136 was raised p2 → p1 on the same day for being a playbook defect, and 123 inherits that weight. Kept for the record; do not implement from this file.
**Priority: p2**

## 요약

플레이북의 `[auto]` 필수 점검을 평가하는 함수가 있는데
(`project_production.py:213`), 이 함수를 호출하는 커맨드·스킬·훅이 하나도
없습니다. 작성자가 `CHK001 [auto] section:측정 조건` 이라고 쓰면 강제될 거라
기대하지만 아무 일도 일어나지 않습니다.

단위 테스트만 이 함수를 부릅니다. 커버리지는 초록불인데 제품 동작은 없습니다.
지금 `[auto]` 와 `[review]` 는 둘 다 산문일 뿐 런타임 의미가 없습니다.

## Summary

`evaluate_auto_checks` evaluates three rule forms (`section:`, `forbidden:`,
`approved-copy:`) against a document. No command, skill, hook or sibling script
invokes it, so the `[auto]` / `[review]` distinction has no runtime meaning.

## Source

- Type: found while adopting playbooks on a real project, filed in
  `workspace/inbox.md` 2026-09-06
- Owner / decision maker: Dongwon Lee
- The reporter re-implemented the evaluator as a ~70-line unit test in that
  project to get the behaviour the playbook already described.

## 안 고치면

**플레이북**이 막힙니다 — 작성자가 적어둔 필수 점검이 한 번도 실행되지 않습니다.

2026-09-07 재판정: 플레이북이 목표의 일곱 가지에 명시되면서 **p2 → p1 격상
후보**가 됐습니다. 보관만 하고 건네줄 때 지켜지지 않으면 보관의 값이 없습니다.
**123과 합칠 후보**(둘 다 파일 존재만 보고 내용을 안 봄).

## Opportunity

Verified 2026-09-06 by grepping the name across `scripts/`, `commands/`,
`hooks/`, `skills/` and `tests/`:

| Site | Kind |
| --- | --- |
| `project_production.py:213` | its own definition |
| `tests/test_project_production.py:1456`, `:1464`, `:1480` | test calls |
| everything else | no hits |

**Correction.** The report says the grep returns "only its own definition". Three
test call sites also exist — which makes it worse: the evaluator is *tested but
unwired*, so the suite reports working code that no user-facing path reaches.

The checks are parsed (`parse_required_checks`, `:164`) and stored (`:387`). They
are never run.

## Scope

### In

- Call `evaluate_auto_checks` from whatever validates an analysis run against its
  playbook; surface failures with the check id and rule.
- Decide whether `doctor` also runs it for projects that have playbooks.

### Out

- Giving `[review]` runtime meaning. It is a human step by design.
- Adding rule forms. Wire up the three that exist first.
- The two smaller playbook findings in the same inbox entry (`process_ref_kind`
  has no `script` value; required sections are reported one at a time).

## Known Limit

Only the three implemented forms get enforced, and `approved-copy:` additionally
depends on an `Approved Copy Blocks` section existing — so a playbook without one
reports every such check as failing for a reason about the playbook, not the
document.

## Acceptance Criteria

- A document violating an `[auto] section:` check fails, naming the check id.
- The same for `forbidden:` and `approved-copy:`.
- A `[review]` check and a retired check never fail automatically (`:218`).
- The reporter's reproduction — five `[auto]` checks, a document violating two —
  produces two failures.

## Verification

Extend `tests/test_project_production.py` past the three existing unit calls with
a test that goes through the *invoking* path, so a future unwiring fails the
suite. The current tests would not have caught this.

## Entry Points

- `scripts/project_production.py:213` — `evaluate_auto_checks`
- `scripts/project_production.py:164` — `parse_required_checks`
- `scripts/project_production.py:387` — where `required_checks` is stored
- `tests/test_project_production.py:1456` — the tests that pass today

## Scope Fence

Do not add a second evaluator. The function is correct; only its caller is missing.

## Workflow Tasks

- [ ] plan → `specs/<issue>/plan.md`
- [ ] execute → wire the evaluator into the validating path
- [ ] review → `specs/<issue>/review.md`

## Related Issues

- related: `132-the-canonical-status-line-has-no-protection` (a rule written down
  but not enforced), `129-required-sections-are-named-but-never-checked`

## Next Command

`product:plan 136-auto-playbook-checks-are-never-executed`
