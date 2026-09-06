# Tasks: Required Sections Are Named But Their Content Is Never Checked

Issue: 129-required-sections-are-named-but-never-checked

## Ready

- [ ] 없음 — T01~T11 완료.

- [x] T01 — `tests/test_section_content_rules.py`, every test above, recorded RED
- [x] T02 — `parse_type_token()`: `- Type:` → `(token, prose)`, closed set of four
- [x] T03 — `SECTION_RULES` table and `validate_section_content()`, called from
      `validate_project`
- [x] T04 — cause rule: `## 원인` required on `bug`, holds output or `원인 미상`,
      no hedging, scoped to the section
- [x] T05 — `## 원인` added to the three real bug issues, moved out of
      `## Opportunity` by hand
- [x] T06 — decision rule: five Korean slots, `[사장님 결정]` / `[확인만]` marking,
      unapproved items only
- [x] T07 — spike rule: `## Goal` + `## Findings`, the Beads contract
- [x] T08 — `commands/product-issue.md` and `commands/product-spec.md` state the
      rules; `templates/issues/` carries the token line
- [x] T09 — entry gate: `product:issue` and `scripts/project_promote.py` assign
      the token instead of asking for it
- [x] T10 — spec 112 §15's three remaining decisions marked or slotted
- [x] T11 — full suite, `release_check.py`, version bump

## In Progress

- [ ]

## Done

작업은 Ready 칸에서 체크했습니다. 검토서: `review.md`.

## Blocked

- [ ] Migrating the 107 free-prose `Type:` lines. Out of scope by decision; they
      are skipped, not failed. Revisit only if the skip turns out to swallow the
      check — the risk the spec names first.
