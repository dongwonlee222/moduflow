# Project-Aware Production Library Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL after explicit implementation approval: `superpowers:executing-plans`; execute inline, task-by-task. Do not dispatch subagents for the shared renderer. Checkboxes below describe future work, not completed implementation.

**Goal:** Add a production-records tab, a playbooks tab and one global project selector to the existing generated dashboard, without redesigning its visual language or rebuilding what already works.

**Architecture:** Two new collectors beside the existing ones in `scripts/project_memory.py`, both delegating all parsing to `scripts/project_production.py`. One pure coverage function decides the three-state playbook treatment. The renderer reuses the existing `.db` / `.dbbar` / `.chip` / `.badge` / `.flag` / `.empty` classes. No backend, no second parser, no new persistence.

Issue: `086-project-aware-production-library-dashboard` · Owner: Dongwon Lee
Phase: draft plan, 2026-09-04. Implementation requires separate explicit approval.
Source / Prev: [spec](spec.md), [design](design.md), [prototype](prototype.html), [existing issue](../../issues/086-project-aware-production-library-dashboard.md). The design was reconciled with Issues 115 and 091 on 2026-09-04.
Next: `product:execute 086-project-aware-production-library-dashboard` after a recorded readiness check.

## Global Constraints

Constitution v1.0 applies. Plan-specific additions:

- Additive only. Do not simplify or rebuild the Issue DB collector, either Cytoscape graph, the hash routing, or the issue/memory drill-down in order to add tabs.
- Preserve the existing visual language exactly: `#2a78d6` active tab, 1px `#ddd` borders, 8px radius, `#f5f5f3` tab and table header, `#fafaf8` filter bar, `#dcebfb`/`#16467e` active chip, 13px table text.
- All production-record and playbook parsing goes through `scripts/project_production.py`. This module adds no second parser (C8).
- Read-only. No screen action promotes a record, applies a playbook, marks a required check, or writes any file.
- No backend, no second dashboard store, and no page that mixes two projects' records in one payload.
- Analysis runs are out of scope; they belong to Issue 092.
- Current authoring writes stay inside `specs/086-project-aware-production-library-dashboard/`.

## Contract and Dependencies

| Interface | Consumes | Produces |
| --- | --- | --- |
| `_collect_production_records(root, *, project_context)` | One resolved project | Rows of `{id, title, deliverable_type, audiences, retrieval_trigger, lifecycle, playbook_refs, path, sections}`; delegates parsing to `project_production.list_production_records` |
| `_collect_playbooks(root, *, project_context)` | One resolved project | Rows of `{id, title, deliverable_types, retrieval_trigger, process_ref, required_checks, version, status, approved_by, approved_at, source_records, path}`; delegates to `project_production.list_playbooks` |
| `playbook_coverage(record, playbooks) -> str` | One record and the project's playbooks | `"named"`, `"no-standard"` or `"unapplied"`. Pure, no I/O, no HTML |
| `render_project_view(root, *, project_context=None)` (existing) | One resolved project | Existing three tabs unchanged, plus the two new tabs and the selector |

Existing functions reused unchanged: `project_production.list_production_records`, `list_playbooks`, `parse_production_record`, `parse_playbook`; `project_registry` context resolution; `project_operation` read capability. Prerequisites: Issues 085, 115 and 091 are delivered on `main` at 0.3.62.

## File Map

| File(s) | Responsibility / change after approval |
| --- | --- |
| Existing `scripts/project_memory.py` | Two collectors, the coverage function, and the two new tabs inside `render_project_view`; existing collectors untouched |
| Existing `scripts/project_production.py` | **Read-only.** Called, not modified |
| Existing `commands/product-dashboard.md` | Document the new tabs and the read-only boundary |
| New `tests/test_dashboard_production_views.py` | Collectors, coverage states, empty states, and rendered markup assertions |
| Existing `tests/test_project_memory.py` | Regression floor for the three existing tabs |
| Existing `scripts/validate_moduflow.py`, `scripts/release_check.py` | Register the new suite |

## Recommended Discipline

| Stream | Discipline | Reason |
| --- | --- | --- |
| A — collectors and coverage | TDD, pure functions first | The coverage judgment must be testable without rendering HTML |
| B — tabs | executing-plans inline + visual diff against the prototype | The shared renderer has one writer |
| C — selector | TDD + regression-first | This is the only structural change; existing tabs must be proven unchanged before and after |
| D — evidence | verification-before-completion | Screenshots and empty states are observations, not assertions |

---

## Stream A — Collectors and Coverage

### Task A1: Two collectors

- [ ] Add `_collect_production_records` and `_collect_playbooks` beside the existing collectors, each resolving one project context and requiring read capability before touching project content.
- [ ] Delegate every parse to `project_production`; surface its `ValueError` as a per-row warning rather than failing the whole view.
- [ ] Return only the fields the tables and modals need. No source bodies, no absolute paths, no other project's rows.
- [ ] Tests: populated project, empty project, one malformed record among valid ones, and a project whose playbooks directory does not exist.

**Verify:** `python3 -m unittest tests.test_dashboard_production_views -v`

### Task A2: The three-state coverage judgment

- [ ] Implement `playbook_coverage(record, playbooks)` returning `named`, `no-standard` or `unapplied`.
- [ ] `named` when the record has any `playbook_refs`. `unapplied` when it has none and some **approved** playbook lists the record's `deliverable_type` in `applies_to_types`. `no-standard` otherwise.
- [ ] Match on exact `deliverable_type` membership only. Do not consult channel or audience. A candidate or deferred playbook never triggers `unapplied`.
- [ ] Tests: each state; a candidate-only playbook of the same type yielding `no-standard`; a record whose type matches nothing; a record already naming a playbook while another approved one also matches.

**Verify:** `python3 -m unittest tests.test_dashboard_production_views -v`

---

## Stream B — The Two Tabs

### Task B1: Production Records tab

- [ ] Append one tab after the existing three; do not reorder or restyle them.
- [ ] Render the `.db` table with Production Record, Type, Audience, Retrieval trigger, Status and Playbook columns, reusing `.dbbar`, `.chip`, `.badge` and `.flag`.
- [ ] Render coverage as the playbook id, a neutral `기준 없음` badge, or a `기준 미적용` attention flag, and state in the bottom panel that the flag means a standard exists and no reference was recorded, which may be intentional.
- [ ] Render the `.empty` panel with wording that nothing has been registered yet.
- [ ] Tests: each coverage state appears with the expected class; the empty panel renders; no record body text leaks into the table.

**Verify:** `python3 -m unittest tests.test_dashboard_production_views -v`

### Task B2: Playbooks tab

- [ ] Append the second tab with name, applies-to type, `retrieval_trigger`, `process_ref`, required-check counts and version with approval badge.
- [ ] Render `process_ref` kind `none` as `없음`, and an absent `process_ref` as an empty cell, so the two stay distinguishable.
- [ ] Show required checks as counts split by kind, for example `자동 3 · 사람 2`.
- [ ] Give only `approved` playbooks the green treatment; candidates and deferred items must not read as current policy.
- [ ] Emit no control that marks, completes or clears a check item.
- [ ] Tests: an approved and a candidate playbook render differently; `none` versus absent `process_ref`; check counts; no completion affordance exists in the markup.

**Verify:** `python3 -m unittest tests.test_dashboard_production_views -v`

### Task B3: Detail modals

- [ ] Reuse one modal shell for both tabs. Record detail renders all nine Issue 085 sections with External Copy and Internal Reporting Copy visibly separated; playbook detail renders approver, date, review state, source records and supersession history.
- [ ] Modal open/close/focus behaviour follows the design; the full-width table stays intact underneath.
- [ ] Tests: both modals render their required sections; closing restores focus; opening a second row replaces rather than stacks.

**Verify:** `python3 -m unittest tests.test_dashboard_production_views -v`

---

## Stream C — One Global Project Selector

### Task C1: Regression floor first

- [ ] Before touching the selector, capture generated-output equivalence for the three existing tabs and assert it holds after every later change. This is the only structural task and the existing views are the thing most likely to break.
- [ ] Tests compare generated before/after equivalence; never pin issue or edge counts, which change with the repository.

**Verify:** `python3 -m unittest tests.test_project_memory tests.test_dashboard_production_views -v`

### Task C2: One payload, one selection

- [ ] Add the selector above the tabs. One selection drives header status, Issue DB, both graphs, records, playbooks and next action from the same project payload.
- [ ] No view owns or persists its own project id. Switching clears stale selected issue, record and memory details before rendering the target.
- [ ] `?project=<id>#<view>` restores a valid project and view; an invalid id falls back visibly.
- [ ] `All Projects` renders summary counts and attention states only, and requires a concrete project before any record detail.
- [ ] Tests: switch clears prior selection; invalid id falls back with a visible warning; no second project's rows appear in a payload.

**Verify:** `python3 -m unittest tests.test_dashboard_production_views -v`

---

## Stream D — Integration and Evidence

### Task D1: Registration and docs

- [ ] Register `tests/test_dashboard_production_views.py` in `scripts/release_check.py` and any new assets in `scripts/validate_moduflow.py`.
- [ ] Update `commands/product-dashboard.md` with the two tabs and the read-only boundary.

**Verify:** `python3 scripts/validate_project_artifacts.py .` and `python3 scripts/release_check.py .`

### Task D2: Observed evidence

- [ ] Capture desktop and mobile screenshots for: unchanged Issue DB, populated records table, open record modal, playbooks table, empty state, and the `All Projects` summary.
- [ ] Record them as observations with the fixture identity used; an expected layout is not an observed one.
- [ ] Note that the ModuFlow repository holds zero production records, so the empty state is the view seen most often here; a populated observation needs a synthetic fixture or a separately authorized project.

**Verify:** recorded observations in `status.md`

---

## Verification Commands and Gates

| Gate | Command | Passing condition |
| --- | --- | --- |
| New suite | `python3 -m unittest tests.test_dashboard_production_views -v` | All collector, coverage, render and selector cases pass |
| Existing dashboard | `python3 -m unittest tests.test_project_memory -v` | No regression in the three existing tabs |
| Full suite | `python3 -m unittest discover -s tests -v` | No failure |
| Project artifacts | `python3 scripts/validate_project_artifacts.py .` | No error diagnostics |
| Release policy | `python3 scripts/release_check.py .` | All checks pass |

## Implementation Readiness Inputs

- Explicit human implementation approval (C6). This plan is not that approval.
- The integration base commit, and confirmation that no other task is writing `scripts/project_memory.py`.
- A decision on where a populated screenshot comes from, since this repository has no production records.

## Coverage and Execution Order

| Requirement | Task |
| --- | --- |
| AC1, AC2, AC12 | A1, B1, C2 |
| AC3, AC4, AC5, AC6, AC7 | C1, C2 |
| AC8, AC9 | A1, B1, B3 |
| AC10, AC10a | A1, B2, B3 |
| AC10b | A2, B1 |
| AC10c | Out of scope by design; asserted by absence |
| AC11, AC13, AC14 | C1, D1, D2 |

Order: **A1 → A2 → B1 → B2 → B3 → C1 → C2 → D1 → D2.** The two tabs are additive and land first so any regression in the existing views is unambiguously attributable to the selector, which is the only structural change.

## Next Command

`product:review 086-project-aware-production-library-dashboard`, then request explicit implementation approval.
