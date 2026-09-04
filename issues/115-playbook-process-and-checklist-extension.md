# Issue 115: Playbook Process Reference and Verification Checklist Extension

**Status: backlog** — created 2026-09-03.
**Priority: p1**
**Blocked-by:**

## Summary

Add two additive fields to `moduflow.playbook.v1` — an external `process_ref` and a numbered, human-owned `Required Checks` checklist — so a project can fix a deliverable type's procedure reference and verification without introducing a second template system.

## Source

- Type: follow-up extension of a delivered format, split out of Issue 091 planning
- Owner / decision maker: Dongwon Lee
- Approved: 2026-09-03, ownership split recommended in `specs/091-reproducible-analysis-runs-and-template-pack/spec.md` and accepted by Dongwon Lee
- Trend evidence: `knowledge/benchmarks/2026-09-03-deliverable-playbook-and-analysis-run-benchmark.md`

## Opportunity

Recurring work requests are re-explained every time because nothing holds a deliverable type's procedure and verification per project. `moduflow.playbook.v1` already scopes by `applies_to_types`, `applies_to_channels` and `audiences`, already lives in the project repository, and already carries version, approval, supersession, `Approved Copy Blocks` and `Approved Structures`. It is missing exactly two things: a reference to the procedure, and a checklist of what must be verified.

Issue 091 needs both to deliver reproducible analysis runs, but `moduflow.playbook.v1` and `scripts/project_production.py` are owned by Issue 085 and are also on the path of Issues 107 and 108. `workspace/goal.md` requires that Issues 085 and 086 be extended through follow-ups rather than replaced, so the format change belongs here and Issue 091 consumes it.

## Scope

### In

- Add `process_ref` as `{kind, ref, version, missing_evidence}` naming an external procedure such as an agent skill or an approved document, with its version. A null `ref` is valid only with a nonempty `missing_evidence`.
- Add a numbered `Required Checks` section (`CHK001`, `CHK002`, …) with stable IDs across playbook versions; changing an item's meaning requires a new ID.
- Preserve every existing playbook section, field and behavior; an existing playbook without the two new fields must still parse and validate unchanged.
- Record the file collision set shared with Issues 091, 107 and 108 before implementation.

### Out

- Storing ordered process steps, or defining any process format inside ModuFlow.
- Assuming a referenced procedure is installed, or resolving it over the network.
- Treating a checked item as proof that a run or deliverable passed.
- Cross-project playbook promotion or sharing, which remains Issue 107.
- Final-state enforcement for a production deliverable, which remains Issue 108.
- Any approval screen, approval flow, or delegation model. An approval stays a recorded date and an existing link.
- Rewriting `moduflow.production-record.v1`, the existing playbook renderer, or any Issue 085 behavior.

## Acceptance Criteria

- An existing playbook with neither new field parses, validates and renders byte-identically to the current behavior.
- `process_ref` round-trips, and a null `ref` without `missing_evidence` is rejected with an explicit diagnostic.
- A referenced procedure that is absent is recorded as absent; nothing assumes or requires its installation.
- `Required Checks` items carry stable numbered IDs; a duplicate or silently renumbered ID is rejected.
- A checked item is reported as a reviewer assertion and never as run or deliverable verification.
- No change to production record format, sharing behavior, or final-state semantics.
- `python3 scripts/release_check.py .` passes.

## Verification

- `python3 -m unittest tests.test_project_production -v`
- `python3 scripts/validate_project_artifacts.py .`
- `python3 scripts/release_check.py .`

## Entry Points

- `templates/production/playbook.md`
- `scripts/project_production.py`
- `tests/test_project_production.py`

## Scope Fence

This is an additive extension of a delivered format owned by Issue 085. It does not rewrite that issue, does not create a second template system, and does not take on sharing (107) or final-state enforcement (108).

## Workflow Tasks

- [x] benchmark → `knowledge/benchmarks/2026-09-03-deliverable-playbook-and-analysis-run-benchmark.md`
- [x] spec → `specs/115-playbook-process-and-checklist-extension/spec.md`
- [x] plan → `specs/115-playbook-process-and-checklist-extension/plan.md`
- [x] execute → two additive fields, backward-compatible parsing, and focused tests; evidence in `specs/115-playbook-process-and-checklist-extension/status.md`
- [ ] review → `specs/115-playbook-process-and-checklist-extension/review.md`

## Related Issues

- blocks: `091-reproducible-analysis-runs-and-template-pack`
- blocked_by:
- duplicates:
- follows_up: `085-project-production-records-and-playbooks`
- supersedes:
- related: `101-production-record-schema-friction`, `107-shared-approved-playbook-layer`, `108-production-approval-and-verification-gates`

## Links

- Goal: `workspace/goal.md`
- Roadmap: `workspace/roadmap.md`
- Benchmark: `knowledge/benchmarks/2026-09-03-deliverable-playbook-and-analysis-run-benchmark.md`
- Consumer contract: `specs/091-reproducible-analysis-runs-and-template-pack/spec.md`

## Next Command

`product:spec 115-playbook-process-and-checklist-extension`, then Issue 091 Stream E.
