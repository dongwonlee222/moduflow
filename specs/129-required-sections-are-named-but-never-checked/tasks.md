# Tasks: Required Sections Are Named But Their Content Is Never Checked

Issue: 129-required-sections-are-named-but-never-checked

## Ready

- [ ] T01 — `tests/test_section_content_rules.py`, every test above, recorded RED
- [ ] T02 — `parse_type_token()`: `- Type:` → `(token, prose)`, closed set of four
- [ ] T03 — `SECTION_RULES` table and `validate_section_content()`, called from
      `validate_project`
- [ ] T04 — cause rule: `## Cause` required on `bug`, holds output or `원인 미상`,
      no hedging, scoped to the section
- [ ] T05 — `## Cause` added to the three real bug issues, moved out of
      `## Opportunity` by hand
- [ ] T06 — decision rule: five Korean slots, `[사장님 결정]` / `[확인만]` marking,
      unapproved items only
- [ ] T07 — spike rule: `## Goal` + `## Findings`, the Beads contract
- [ ] T08 — `commands/product-issue.md` and `commands/product-spec.md` state the
      rules; `templates/issues/` carries the token line
- [ ] T09 — entry gate: `product:issue` and `scripts/project_promote.py` assign
      the token instead of asking for it
- [ ] T10 — spec 112 §15's three remaining decisions marked or slotted
- [ ] T11 — full suite, `release_check.py`, version bump

## In Progress

- [ ]

## Done

- [ ]

## Blocked

- [ ] Migrating the 107 free-prose `Type:` lines. Out of scope by decision; they
      are skipped, not failed. Revisit only if the skip turns out to swallow the
      check — the risk the spec names first.
