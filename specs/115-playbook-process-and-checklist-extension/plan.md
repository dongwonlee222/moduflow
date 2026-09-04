# Playbook Process Reference and Verification Checklist Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL after explicit implementation approval: `superpowers:executing-plans`; execute inline, task-by-task. Do not dispatch subagents. Checkboxes describe future work, not completed implementation.

**Goal:** Add two optional elements to the delivered playbook format so a project can fix a deliverable type's procedure reference and verification, with zero change to existing playbooks.

**Architecture:** Additive extension of `moduflow.playbook.v1` inside the existing `scripts/project_production.py` parser and renderer. No new module, no new command, no schema version bump, no migration.

**Tech Stack:** Existing Python 3 standard library, Markdown, `unittest`. No new dependencies.

Issue: `115-playbook-process-and-checklist-extension` · Owner: Dongwon Lee
Phase: draft plan, 2026-09-03. Implementation requires separate explicit approval.
Source / Prev: [spec](spec.md), [existing issue](../../issues/115-playbook-process-and-checklist-extension.md) · Next: `product:execute 115-playbook-process-and-checklist-extension`, then Issue 091 Streams B2 and E1.

## Global Constraints

Constitution v1.0 applies. Plan-specific additions:

- Additive only. No section renamed, reordered or removed; no schema version bump; no migration script.
- No new module, command, entry point or public API beyond the two elements, and no second error model: this module raises `ValueError`, it does not return diagnostics.
- No resolution, fetch, filesystem probe, installation check or execution of a referenced procedure.
- No code path marks, evaluates or completes a checklist item.
- One parser for the playbook format (C8); behavior changes ship with focused tests (C3); no gate swallows an exception (C2).
- Single-writer discipline on `scripts/project_production.py` and `templates/production/playbook.md`, shared with Issues 091, 107 and 108.
- Current authoring writes remain confined to `specs/115-playbook-process-and-checklist-extension/`.

## Contract and Dependencies

| Interface | Consumes | Produces |
| --- | --- | --- |
| Existing `parse_playbook(project_root, path)` | Playbook Markdown | Existing structure plus an optional `process_ref` mapping and an ordered `required_checks` list |
| The same function's existing error path | Invalid input | **Raises `ValueError`** naming `PLAYBOOK_PROCESS_REF_INCOMPLETE` or `PLAYBOOK_CHECK_ID_INVALID`. This module has no diagnostics list; do not add one |
| Existing `PLAYBOOK_SECTIONS` tuple | Required section names, all mandatory and order-checked by `_sections` | **Unchanged.** `Required Checks` is optional and must be read by a separate lookup, or every existing playbook breaks |
| Existing `project_memory.parse_frontmatter` | Flat `key: value` lines and block lists | No nested mappings, so `process_ref` uses four flat keys |
| Existing playbook renderer | One parsed playbook | Byte-identical output when neither addition is present |

Consumer: Issue 091 reads `process_ref` for the run's `execution_evidence` and reads item IDs into `checks[]` with `source: playbook`. Issue 091 does not modify the files in this plan.

## File Map

| File(s) | Change after approval |
| --- | --- |
| Existing `templates/production/playbook.md` | Optional `process_ref` frontmatter mapping and a `Required Checks` section with reviewer-assertion wording |
| Existing `scripts/project_production.py` | Extend `parse_playbook`, the `PLAYBOOK_SECTIONS` tuple and the renderer for the two additions; keep the existing `ValueError` error model; existing paths unchanged |
| Existing `tests/test_project_production.py` | New cases below; every existing case passes unchanged |

Nothing else is touched. `moduflow.production-record.v1`, command docs, entry points and distribution assets stay as they are.

## Stream A — Additive Format

### Task A1: `process_ref`

- [ ] Parse the optional `process_ref` mapping with `kind`, `ref`, `version`, `missing_evidence`.
- [ ] Validate `process_ref_kind` in `skill` / `document` / `none`; require every empty value among `process_ref` and `process_ref_version` to appear in `process_ref_missing` with a nonempty reason, else raise `ValueError` naming `PLAYBOOK_PROCESS_REF_INCOMPLETE`.
- [ ] Require `kind: none` to carry null `ref` and `version` and one explaining entry.
- [ ] Treat an absent key as valid and raise nothing; never treat absence as unconstrained in downstream wording.
- [ ] Store the reference only: no fetch, no path probe, no installation check, no availability claim.
- [ ] Tests: each `kind`, null `ref` with and without `missing_evidence`, null `version` with and without it, absent key, and an assertion that no filesystem or network access occurs for the reference.

**Verify:** `python3 -m unittest tests.test_project_production -v`

### Task A2: `Required Checks`

- [ ] Read `Required Checks` through a new **optional** section lookup and parse it into an ordered list of `{id, kind, text, rule, retired}`. Do not add it to `PLAYBOOK_SECTIONS`; that tuple is mandatory-and-ordered and would break every existing playbook.
- [ ] Support `[auto]` and `[review]` item kinds. Implement `auto` evaluation for exactly three rule forms — `section:<name>`, `forbidden:<text>`, `approved-copy:<label>` — and raise `ValueError` naming `PLAYBOOK_CHECK_RULE_UNSUPPORTED` for anything else. No evaluation engine, no quality judgment.
- [ ] Validate `CHK` plus three digits, uniqueness, ascending order and nonempty text, else raise `ValueError` naming `PLAYBOOK_CHECK_ID_INVALID`.
- [ ] Treat an empty or absent section as valid; keep `(retired)` items in place without renumbering.
- [ ] Render the section with wording stating that a checked item is a reviewer assertion; expose no marking or completion API.
- [ ] Document the major/minor `version` rule in the template and its rendered guidance; add no comparison logic, history store or migration.
- [ ] Parse an optional `retrieval_trigger` frontmatter key into the playbook, absent or empty being valid, and add it to the template. Change no search code: `search_production` already covers playbooks and `_search_text` already reads this key.
- [ ] Tests: valid list, duplicate ID, renumbered sequence, malformed ID, empty text, empty section, a retired item still resolving, and absence of any completion path.

**Verify:** `python3 -m unittest tests.test_project_production -v`

### Task A3: Backward compatibility proof

- [ ] Round-trip every existing playbook fixture through parse and render and assert a byte-identical result.
- [ ] Assert that adding one element does not alter another field's serialization or section order.
- [ ] Re-run the full existing `tests/test_project_production.py` unchanged.
- [ ] Register playbook-shape validation for the plugin's own assets in `scripts/release_check.py`, so a playbook change is checked the way code is.

**Verify:** `python3 -m unittest tests.test_project_production -v`, `python3 scripts/validate_project_artifacts.py .`, `python3 scripts/release_check.py .`

## Verification Commands and Gates

| Gate | Command | Passing condition |
| --- | --- | --- |
| Focused suite | `python3 -m unittest tests.test_project_production -v` | New cases pass; every existing case passes unchanged |
| Full suite | `python3 -m unittest discover -s tests -v` | No failure; the existing suite is the regression floor |
| Project artifacts | `python3 scripts/validate_project_artifacts.py .` | No error diagnostics |
| Release policy | `python3 scripts/release_check.py .` | All checks pass, including commit↔issue linkage |

## Implementation Readiness Inputs

- The exact integration base commit and a re-check that no other task is writing `scripts/project_production.py` or `templates/production/playbook.md`.
- Explicit human implementation approval (C6). This plan is not that approval.

## Coverage and Execution Order

| Requirement | Task |
| --- | --- |
| R1 `process_ref` | A1 |
| R2 `Required Checks` | A2 |
| R3 version semantics | A2 |
| R4 `retrieval_trigger` | A2 |
| R5 backward compatibility | A3 |
| AC1, AC7, AC8 | A3 |
| AC2, AC3 | A1 |
| AC4, AC5, AC6 | A2 |

Order: **A1 → A2 → A3.** One writer throughout.

## Next Command

`product:review 115-playbook-process-and-checklist-extension`, then Issue 091 Streams B2 and E1.
