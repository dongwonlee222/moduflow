# Tasks: Project Production Records and Playbooks

Issue: `085-project-production-records-and-playbooks`
Plan: `specs/085-project-production-records-and-playbooks/plan.md`
Status: implementation-and-review-complete · Mode: sequential inline execution · Order: A1 → A2 → B1 → C1 → D1 → E1 → F1

## Stream A — Canonical data model

- [x] **A1. Parser + templates** — create `scripts/project_production.py`, `templates/production/{record,playbook}.md`, and parser RED/GREEN tests; produces normalized record/playbook interfaces — depends: none.
- [x] **A2. Init + duplicate-safe capture** — add optional directory initialization, `--new-record`, capture key, and `created/update_required/noop` behavior — depends: A1.

## Stream B — Human-gated Playbooks

- [x] **B1. Approval decisions** — exact `.moduflow/humans.json` identity match, approve/reject/defer audit, source-record validation, and idempotency tests — depends: A2.

## Stream C — Reuse

- [x] **C1. Search + retrieval** — structured filters, deterministic ranking, approved-first context, project isolation, and explicit truncation — depends: B1.

## Stream D — Trust gates

- [x] **D1. Project validation** — integrate canonical production validator into `validate_project_artifacts.py`; missing relative files/invalid approvals error, absolute paths/staleness warn, lightweight projects remain valid — depends: C1.

## Stream E — Product surface

- [x] **E1. Command + routing + distribution** — add `product:production`, memory/router/index guidance, README entry, required package files, and distribution tests — depends: D1.

## Stream F — Dogfood and review

- [x] **F1. Two-type fixture + full verification** — banner and PR records, approved playbook, end-to-end tests, independent review, status/roadmap updates, full release gates — depends: E1.

## Interfaces

- A1 owns `parse_production_record`, `parse_playbook`, list collectors, and normalized payload shapes.
- A2 owns initialization, record creation, capture keys, and CLI entry.
- B1 consumes A1/A2 records and produces audited Playbook state transitions.
- C1 consumes normalized records/playbooks and produces `items/truncated/dropped_count/total_matches` for future Issue 086 use.
- D1 consumes only `validate_production_project`; it must not reparse Production Record/Playbook Markdown.
- E1 documents the frozen interfaces and adds no behavior.
- F1 proves the complete contract and is the review handoff.

## Verification

- [x] `python3 -m unittest tests.test_project_production -v` — 24 passed.
- [x] `python3 -m unittest discover -s tests -v` — 483 passed.
- [x] `python3 scripts/spec_consistency.py . --issue-id 085-project-production-records-and-playbooks` — 0 findings.
- [x] `python3 scripts/validate_moduflow.py .` — 137 required files checked.
- [x] `python3 scripts/validate_project_artifacts.py .` — valid; one pre-existing optional-memory warning.
- [x] `python3 scripts/release_check.py .` — valid; all gates passed.
- [x] `git diff --check` — clean.

## Next Command

`product:pr 085-project-production-records-and-playbooks`
