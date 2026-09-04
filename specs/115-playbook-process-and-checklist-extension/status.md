# Status: Playbook Process Reference and Verification Checklist Extension

Issue: `115-playbook-process-and-checklist-extension` · Owner: Dongwon Lee
Phase: implementation complete and verified in this worktree on 2026-09-03. Not committed, not merged, not published, not installed. The canonical lifecycle state is unchanged and still `backlog`.
Source: [spec](spec.md), [plan](plan.md) · Next: owner review, then an explicit lifecycle transition through the existing transaction path.

## What Changed

| File | Change |
| --- | --- |
| `scripts/project_production.py` | Added `OPTIONAL_PLAYBOOK_SECTIONS`, `PLAYBOOK_CHECK_RE`, `AUTO_RULE_RE`, `_optional_section`, `parse_process_ref`, `parse_required_checks`, `evaluate_auto_checks`; `parse_playbook` now returns `process_ref`, `required_checks` and `retrieval_trigger` |
| `templates/production/playbook.md` | Optional `process_ref_kind` / `process_ref` / `process_ref_version` / `process_ref_missing` keys, an optional `retrieval_trigger` key, an optional `Required Checks` section with reviewer-assertion wording, and the major/minor version rule in Revision History |
| `tests/test_project_production.py` | Added `PlaybookProcessRefAndChecksTest` with 14 cases |

`PLAYBOOK_SECTIONS` is unchanged. `moduflow.production-record.v1`, the record parser, sharing behavior, final-state semantics and every command surface are untouched.

## Three Plan Corrections Found by Reading the Code

The plan as written would not have worked. Each was corrected in the spec and plan before implementation.

1. **`Required Checks` cannot join `PLAYBOOK_SECTIONS`.** `_sections` requires every listed section to exist and to appear in order, so adding it would have raised `missing section: Required Checks` for every existing playbook. It is read through a new optional lookup instead.
2. **`process_ref` cannot be a nested mapping.** `project_memory.parse_frontmatter` reads flat `key: value` lines and block lists only; a nested YAML mapping would have been silently dropped. Four flat keys are used.
3. **This module raises, it does not return diagnostics.** The first draft borrowed `project_artifact_registry`'s diagnostics style, which would have put two error models in one module. Invalid input raises `ValueError` with the stable code in the message.

## Verification Observed 2026-09-03

| Gate | Command | Result |
| --- | --- | --- |
| Focused suite | `python3 -m unittest tests.test_project_production` | 47 tests, OK. 33 existing pass unchanged; 14 new |
| Full suite | `python3 -m unittest discover -s tests` | 1,692 tests in 654s, OK. Baseline before this change was 1,680 |
| Project artifacts | `python3 scripts/validate_project_artifacts.py .` | exit 0 |
| Release policy | `python3 scripts/release_check.py .` | exit 0, `valid: true`, no errors, no check `ok: false`; its internal full-suite run returned 0 |
| Template self-parse | `parse_playbook` on `templates/production/playbook.md` | `process_ref` kind `none` with one explained missing entry; `CHK001 [auto]`, `CHK002 [review]`; the six required sections unchanged |

## Acceptance Criteria

| AC | Result |
| --- | --- |
| AC1 existing playbook byte-identical, existing tests unchanged | Met — 33 existing cases pass, `PLAYBOOK_SECTIONS` untouched |
| AC2 `process_ref` round-trips; unnamed empty value raises `PLAYBOOK_PROCESS_REF_INCOMPLETE` | Met |
| AC3 reference never resolved, fetched or probed; absence raises nothing | Met — a test patches `Path.exists` to fail on any probe |
| AC4 check IDs validated for pattern, uniqueness, ascending order; retired kept in place | Met |
| AC5 no `review` item is marked or completed; `auto` limited to three rule forms | Met — unsupported rule raises `PLAYBOOK_CHECK_RULE_UNSUPPORTED` |
| AC6 template states the major/minor rule; no comparison logic, history store or migration | Met |
| AC6b `retrieval_trigger` parses when present, valid when absent, findable through existing search | Met — no search code changed; `search_production` already covers playbooks and `_search_text` already read the key |
| AC7 no change to record format, sharing, final state or command surface | Met |
| AC8 validators and release policy pass | Met |

## `retrieval_trigger` — Added 2026-09-04

Requested during review: a playbook was findable only by id and title, so a task that did not already know the exact name would not find it. `moduflow.production-record.v1` already had `retrieval_trigger` and `_search_text` already read that key for every searched item, so the field was the only thing missing. It is optional, absent parses to an empty string, and no search code changed. Issue 086 renders it as the playbook tab's "when to use" column.

## Not Done

- Not committed, pushed, merged, released or installed.
- Canonical lifecycle state is still `backlog`; the transition belongs to an explicit transaction, not a hand edit.
- `release_check.py` does not yet validate the shape of the plugin's own playbook assets. This was listed in plan Task A3 and is the one open item; it is additive and does not affect the results above.
- Issue 091 remains blocked until this issue's lifecycle state is transitioned.
