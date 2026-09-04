# Spec: Playbook Process Reference and Verification Checklist Extension

Issue: `115-playbook-process-and-checklist-extension`
Owner / decision maker: Dongwon Lee
Phase: draft contract for review, 2026-09-03. No implementation, lifecycle transition, publication or installation is authorized by this document.
Source: [existing issue](../../issues/115-playbook-process-and-checklist-extension.md), the delivered `moduflow.playbook.v1` in `templates/production/playbook.md`, [the 2026-09-03 benchmark](../../knowledge/benchmarks/2026-09-03-deliverable-playbook-and-analysis-run-benchmark.md), and the [Issue 091 contract](../091-reproducible-analysis-runs-and-template-pack/spec.md) that consumes this change.
Prev: Issue 085 delivered · Next: Issue 091 Stream B2 and E1 consume these two fields.

## Problem

A recurring work request is re-explained every time because nothing holds a deliverable type's procedure and verification per project.

`moduflow.playbook.v1` is already the right carrier. It scopes by `applies_to_types`, `applies_to_channels` and `audiences`, lives in the project repository, and carries `version`, `status`, `approved_by`, `source_records`, `review_after`, `superseded_by`, `Approved Copy Blocks`, `Approved Structures` and `Do Not Repeat`. Two things are missing.

1. **No procedure reference.** `Reusable Patterns` is an unordered bullet list. There is no field saying which procedure — an agent skill, an approved document — this deliverable follows, or which version of it was in force.
2. **No verification list.** `Do Not Repeat` states prohibitions. There is no list of what a reviewer must confirm before the deliverable is considered checked.

Without these, Issue 091 would have had to invent a second per-project template system beside playbooks, which the 2026-09-03 benchmark rejected.

## Goals

1. Let a playbook name the external procedure it follows, with its version, or state explicitly that none is recorded.
2. Let a playbook carry a numbered, human-owned verification checklist with stable item IDs.
3. Change nothing else. Every existing playbook must parse, validate and render exactly as it does today.

## Non-Goals

- No ordered process steps and no process format defined inside ModuFlow. The benchmark found that portable skill packages already carry procedure versioned; ModuFlow stores the reference.
- No resolution, fetching, installation check or execution of a referenced procedure.
- No automatic checking. A checked item is a reviewer assertion, never proof that a run or deliverable passed.
- No change to `moduflow.production-record.v1`, the playbook renderer's existing sections, or any Issue 085 behavior.
- No cross-project promotion or sharing of playbooks; that remains Issue 107.
- No final-state enforcement for a production deliverable; that remains Issue 108.
- No approval screen, approval flow or delegation model. An approval stays a recorded date and an existing link.
- No schema relaxation elsewhere; Issue 101 owns record-schema discoverability.

## Existing Implementation and Reuse

Inspected baseline: `3585e84`, equal to `origin/main`.

| Existing surface | Reuse | Restriction |
| --- | --- | --- |
| `templates/production/playbook.md` (`moduflow.playbook.v1`) | Frontmatter keys and the six existing sections | Additive only; no section is renamed, reordered or removed |
| `scripts/project_production.py` | `parse_playbook`, `list_playbooks`, `decide_playbook_update`, and the `PLAYBOOK_SECTIONS` tuple that enumerates allowed sections | Extend in place; add no second parser (C8) and no new command surface |
| Error model in that module | `parse_playbook` **raises `ValueError`** on invalid input; it returns no diagnostics list, unlike `project_artifact_registry` | Stay with the raising model. Do not introduce a second error model inside one module |
| `tests/test_project_production.py` | Existing coverage as the backward-compatibility floor | Every existing case must still pass unchanged |
| `moduflow.production-record.v1` `playbook_refs` | Existing link from a record to its playbooks | Unchanged by this issue |

## Users & Scenarios

- An author writing a weekly analysis playbook records that it follows an external analysis skill at a stated version, and lists the four things a reviewer must confirm.
- A project with no external procedure records `process_ref.ref` as null with an explicit reason, and the playbook stays valid.
- A reviewer reads `Required Checks`, confirms items, and understands from the wording that a checked item is their own assertion.
- An existing playbook written before this change is opened, validated and rendered with no diff.

## Proposed Solution

### R1 — `process_ref`

Four optional frontmatter keys. **They are flat keys, not a nested mapping.** `project_memory.parse_frontmatter` reads `key: value` lines and block lists only; a nested YAML mapping would be silently dropped, so the contract uses flat keys.

| Key | Type and rule |
| --- | --- |
| `process_ref_kind` | `skill`, `document`, or `none` |
| `process_ref` | Stable external reference or project-relative path; empty means not recorded |
| `process_ref_version` | Version or tag string in force; empty means not recorded |
| `process_ref_missing` | Block list of `<field>: <reason>` entries naming every empty value among the two above |

An empty `process_ref` or `process_ref_version` that is not named in `process_ref_missing` raises `ValueError` whose message names `PLAYBOOK_PROCESS_REF_INCOMPLETE`, matching this module's existing raising behavior. `process_ref_kind: none` requires both values empty and one `process_ref_missing` entry explaining that no procedure is recorded.

The reference is stored, never resolved. ModuFlow performs no network fetch, no filesystem probe of an external skill, and no installation check, and never claims the referenced procedure is available. A playbook with none of the four keys is valid and raises nothing; absence is a normal state and never means "no constraints".

### R2 — `Required Checks`

A new **optional** Markdown section holding a numbered checklist.

`_sections(body, PLAYBOOK_SECTIONS)` requires every listed section to exist and to appear in order, so adding `Required Checks` to `PLAYBOOK_SECTIONS` would make every existing playbook fail with `missing section`. The section is therefore read by a separate optional lookup and `PLAYBOOK_SECTIONS` is left unchanged.

- Item IDs are `CHK` plus three digits, ascending, unique within one playbook, and **stable across versions**. Reusing an ID for a different meaning is the failure this rule prevents; a changed meaning takes a new ID.
- Each item is `- CHK001 [auto] <rule>` or `- CHK001 [review] <what the reviewer confirms>` with nonempty text.
- **`review` items are human assertions**, exactly as before: nothing marks, evaluates or completes them.
- **`auto` items are machine-checkable rules**, limited to three forms and nothing else: `section:<name>` requires that section to be present and nonempty; `forbidden:<text>` requires that literal string to be absent; `approved-copy:<block label>` requires that approved copy block's text to appear. An `auto` item whose rule is not one of the three raises `ValueError` naming `PLAYBOOK_CHECK_RULE_UNSUPPORTED`. This is a string and section check, not an evaluation engine, and it never judges quality.
- A duplicate ID, a non-ascending or renumbered sequence, an ID outside the pattern, or an empty item text raises `ValueError` naming `PLAYBOOK_CHECK_ID_INVALID`.
- An empty section, and an absent section, are both valid and raise nothing.
- Retired items are marked `(retired)` in place and never deleted or renumbered, so a historical record referencing `CHK002` still resolves.

The section wording states that a checked item is a reviewer assertion. Nothing in this issue marks, evaluates or auto-completes an item, and no consumer may treat a checklist item as evidence that a run or deliverable passed. Issue 091 consumes item IDs into a run's `checks[]` with `source: playbook`; Issue 108 may later require evidence at a final-state gate. Neither ownership moves here.

### R3 — What a version number means

`moduflow.playbook.v1` already has a `version` field with no stated rule for when it changes. That was tolerable while nothing consumed it; Issue 091 now pins the version a run used, so an undefined number makes the pin meaningless.

- **Major** — a change that could alter a deliverable's outcome or acceptance: a `Required Checks` item added, retired or redefined; `process_ref` pointing at a different procedure; an `Approved Structures` change; `applies_to_types`, `applies_to_channels` or `audiences` narrowing.
- **Minor** — a change that cannot: wording of an existing check, `Approved Copy Blocks` phrasing that keeps the same claim, notes, or `review_after`.
- A version never decreases, and any content change requires a bump. Content changed without a bump is the failure this rule prevents; a validator cannot detect it across separate edits, so it is stated as a rule and enforced in review.

This rule is documentation plus rendered guidance in the template. It adds no comparison logic, no history store and no migration.

### R4 — `retrieval_trigger`

`moduflow.production-record.v1` already carries `retrieval_trigger`, a one-line statement of when a record should be pulled up, and `_search_text` already reads that key for every searched item. Playbooks do not carry it, so a playbook is findable only by its id and title. A task that does not already know the exact name will not find it, which is how a recurring job silently reverts to whatever tool the current session happens to have.

- `retrieval_trigger` is an optional frontmatter key holding one nonempty line, for example `고객사에 안내 메일을 보낼 때`.
- Absent or empty is valid and parses to an empty string; an existing playbook is unaffected.
- No search code changes. `search_production` already covers playbooks and `_search_text` already reads this key, so populating it makes a playbook findable from a natural request immediately.
- It states when to retrieve, never what to do. Procedure stays in `process_ref` and verification in `Required Checks`.

Issue 086 renders this as the "when to use" column of the playbook tab. Without it that tab is a list of titles.

### R5 — Backward compatibility

Both additions are optional. An existing playbook with neither key nor section parses, validates and renders byte-identically to current behavior; a round-trip through the parser and renderer produces no diff. Adding one field or the section does not alter any other field's serialization or section order.

## Alternatives Considered

1. **Recommended: two additive, optional elements on the delivered format.** One carrier, one parser, no migration, no second template system.
2. **Ordered process steps inside the playbook.** Rejected: duplicates portable skill packaging and makes ModuFlow own a procedure format.
3. **A separate per-project analysis template layer.** Rejected in the Issue 091 benchmark: a second template system with its own versioning and approval beside playbooks.
4. **A new playbook schema version `v2`.** Rejected: a migration for two optional elements, with no behavior that requires it.

## Acceptance Criteria

- **AC1** An existing playbook with neither addition parses, validates and renders byte-identically; the existing `tests/test_project_production.py` cases pass unchanged.
- **AC2** `process_ref` round-trips, and a null `ref` or `version` not named in `missing_evidence` raises `ValueError` naming `PLAYBOOK_PROCESS_REF_INCOMPLETE`; the module gains no second error model.
- **AC3** A referenced procedure is never resolved, fetched, probed or claimed available; an absent `process_ref` and an absent or empty checklist are valid and raise nothing.
- **AC4** `Required Checks` item IDs are validated for pattern, uniqueness and ascending order; a duplicate or renumbered ID raises `ValueError` naming `PLAYBOOK_CHECK_ID_INVALID`; a retired item stays in place.
- **AC5** No code path marks, evaluates or completes a `review` item, and the rendered wording states that a confirmed `review` item is a reviewer assertion. An `auto` item is evaluated only through the three supported rule forms, and an unsupported rule raises rather than passing.
- **AC6** The template and its rendered guidance state the major/minor rule, and no comparison logic, history store or migration is added for it.
- **AC6b** `retrieval_trigger` parses when present, is valid when absent, and makes a playbook findable through the existing `search_production` path with no search-code change.
- **AC7** No change to production record format, sharing behavior, final-state semantics, or any command surface.
- **AC8** `python3 scripts/validate_project_artifacts.py .` and `python3 scripts/release_check.py .` pass, and `release_check.py` validates the shape of the plugin's own playbook assets.

## Risks & Open Questions

- **Shared-file risk.** `scripts/project_production.py` and `templates/production/playbook.md` are also on the path of Issues 107 and 108, and Issue 091 blocks on this issue. One writer at a time; re-check the collision set against the integration base before starting.
- **ID stability depends on people.** Nothing can stop an author from reusing `CHK002` for a new meaning inside one edit. The validator catches duplicates and renumbering, not a silent redefinition; the retired-in-place rule and review are the mitigation.
- **Reference rot.** A `process_ref` may point at a skill that is renamed or never installed. This is accepted: the field records what was in force, and absence is explicit rather than repaired.

## Next Command

`product:plan 115-playbook-process-and-checklist-extension` — review the [implementation plan](plan.md), then request explicit implementation approval. This spec authorizes no code change.
