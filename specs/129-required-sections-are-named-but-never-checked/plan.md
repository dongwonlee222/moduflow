# Plan: Required Sections Are Named But Their Content Is Never Checked

Issue: 129-required-sections-are-named-but-never-checked

## Approach

The checker is the small part. The anchors are the work, and the order matters:
a content rule written before its section exists has nothing to run against, and
a rule that fires on 142 legacy artifacts on day one gets switched off.

So: anchors first, table second, rules third, entry gate last.

1. **`SECTION_RULES`, a module-level table** in `scripts/validate_project_artifacts.py`,
   next to `REQUIRED_PATHS`. Entries are data: *(artifact kind, section heading,
   content predicate, Korean failure message)*. One new function,
   `validate_section_content(root, errors, warnings, *, project_context=None)`,
   iterating it — the same shape as `validate_issue_status_lines` at `:385`,
   which already walks `issues/` and appends findings.
2. **The type token.** Parse `- Type:` into `(token, prose)`. Token must be one
   of `bug` `feature` `chore` `spike`. Anything else — prose, or absent — yields
   `None` and the artifact is skipped by every type-keyed rule.
3. **`## Cause` on bug issues**, and the three real bug issues get one, moved out
   of `## Opportunity`. This is a content move by hand, not a script: the cause
   is a judgement about which paragraph is the cause.
4. **`## Human Review Decisions` slots**, applied only to unapproved items.
5. **The entry gate.** `commands/product-issue.md` and `scripts/project_promote.py`
   assign the token rather than asking for it. Without this, R1's skip rule is a
   hole and the whole thing ships as decoration — kubernetes keeps twelve `kind/`
   labels precisely because its four templates each force one.

Steps 1–2 land together or neither works. Step 5 is not optional garnish; it is
what makes steps 3–4 fire on anything written after today.

## Work Streams

- PM: the four tokens are settled (owner, 2026-09-06). The five Korean decision
  slot names are copy the owner reviews.
- Design: none.
- Data: no stored key changes. `- Type:` gains a required first token; the prose
  it carries today survives after the em-dash.
- Implementation: `scripts/validate_project_artifacts.py` (table, parser, one
  validator, one call site in `validate_project`), three issue files gaining
  `## Cause`, `commands/product-issue.md`, `commands/product-spec.md`,
  `scripts/project_promote.py`, `templates/issues/`.
- QA: below, RED first.
- Release: version bump, `release_check.py`, `Issue:` trailer on behaviour
  commits.

## Verification

- `test_type_token_parsing` — the four tokens with and without prose tails;
  prose-only and absent both yield `None`.
- `test_legacy_issues_are_skipped_not_failed` — the 107 free-prose issues produce
  zero errors. Asserted against the live tree, so a rule that starts failing
  history fails the suite instead.
- `test_bug_issue_requires_a_cause_section` — missing `## Cause` fails.
- `test_cause_rejects_hedging` — each banned phrase fails and is quoted back.
- `test_cause_accepts_output_or_unknown` — a fenced block passes; `원인 미상`
  passes.
- `test_hedging_outside_cause_is_ignored` — the same phrase in `## Opportunity`
  passes. The ban is scoped to the section, which is why the section had to exist
  first.
- `test_decision_requires_five_slots` / `test_decision_item_must_be_marked` /
  `test_ratification_item_may_be_one_line` / `test_approved_spec_needs_no_slots`
  / `test_spec_without_decision_section_passes`.
- `test_a_third_rule_needs_no_code` — append an entry to `SECTION_RULES` in the
  test, assert it fires. This is the claim that the table is a table.
- `test_the_live_tree_failure_list_is_exactly_expected` — run over all 142 issues
  and 78 specs with the expected failure set frozen by name.
- Full suite, then `python3 scripts/release_check.py .` with `valid` read at the
  top level.

## Rollback

The validator is additive: one table, one function, one call. Reverting the
execute commit restores current behaviour exactly. The three `## Cause` sections
are content moves inside files that stay valid either way.

The irreversible part is social, not technical — once `product:issue` assigns a
token, issues written afterwards carry it, and a revert leaves them carrying a
field nothing reads. Harmless, but worth naming: the token outlives the checker.

## Next Command

`/moduflow execute 129-required-sections-are-named-but-never-checked`
