# Issue 090: Project Knowledge and Artifact Registry

**Status: backlog** — created 2026-07-16.
**Priority: p1**

## Summary

Make `workspace/knowledge.md` a structured project wiki and add `workspace/artifacts.md` as the canonical registry for reports, local files, Google Sheets, related issues, periods, and draft/final state.

## Source

- Type: user product direction
- Link: local Codex session, 2026-07-16
- Owner / decision maker: Dongwon Lee
- Current phase: spec/plan implementation approved 2026-09-02; existing task to execute inline. The canonical backlog projection is retained because 111 occupies the single active lifecycle slot while awaiting real-host observations; see implementation approval for the failed, non-writing start attempt.

## Problem

Analysis knowledge and deliverable links become scattered across sessions, issue logs, local paths, and Google Sheets. Teams need a stable place for metric definitions, recurring sources, interpretation caveats, final reports, and the exact artifact considered final.

## Product Decision

- `workspace/knowledge.md` is the curated project wiki for definitions, analytical rules, recurring sources, interpretation traps, and durable conclusions.
- `workspace/artifacts.md` is the canonical human-readable registry for project materials.
- Dashboard and search views derive from these files; they do not become a second source of truth.
- Existing memory entries and decision records are linked, not duplicated.
- Domain caveats such as “external ScalarData population is not identical to the internal KPI population” must be expressible as durable interpretation knowledge with evidence and scope.

## Scope

### In

- A structured `workspace/knowledge.md` template covering metric definitions, analysis criteria, recurring data sources, Google Sheet/report links, final conclusions, and interpretation caveats.
- A structured `workspace/artifacts.md` registry with document name, purpose, local path, external link, related issue, reference period, lifecycle state, owner, and last updated date.
- Stable IDs and validation for artifact entries and links.
- `product:knowledge` initialization, inspection, and update guidance.
- Migration guidance for existing knowledge, reports, memory, and scattered workspace links.
- Dashboard-ready parsing without duplicating canonical content.

### Out

- Uploading local files to Google Drive automatically.
- Copying sensitive originals into the repository.
- Replacing detailed reports, Sheets, issues, memory entries, or decision records.
- Building the dashboard UI in this issue.

### Discovery and Handoff Requirements — 2026-09-02 Planning Draft

- Extend the existing scope with a stable material ID, one-line purpose, when-to-read guidance, as-of date/reference period, draft/approved/superseded state, owner, optional original locators and related issue IDs.
- Read the short project wiki/catalog first, then only explicitly selected originals; do not copy source bodies or company data into shared Git/plugin assets.
- Distinguish a missing required link from an unavailable optional private original, and separate metadata validity, freshness, source availability and committed-share readiness.
- Diagnose stale, broken, uncommitted and dirty sources; a local file cannot rescue a missing source in a committed snapshot used by another worktree.
- Register a saved result with its catalog entry and owning-issue backlink through a bounded extension of existing transaction ownership; do not assume Issue 103 already covers arbitrary output paths.
- Expose the same project-scoped stable ID/original/state read contract to 086, 091 and 092; UI and analysis-profile execution remain out of scope.
- Plan synthetic A/B, empty/legacy, stale/missing/private-source and separate committed-worktree scenarios without importing actual company data. The referenced data-context/data-manifest pattern is an application example, not a verified universal API.
- The linked spec/plan are prepared for one combined approval. These additions do not start implementation, change backlog state, or alter the parent task's 111 release gate.

## Acceptance Criteria

- A project can initialize both files without overwriting existing content.
- Knowledge sections cover core metrics, analysis criteria, recurring sources, key links, final conclusions, and commonly confused interpretations.
- Artifact entries contain document name, purpose, local path, external link, related issue, reference period, draft/final state, owner, and update date.
- Broken local paths and malformed registry entries are reported by validation without making external links mandatory.
- Sensitive or external-only files can be registered by metadata without being copied into Git.
- Existing memory and decision records are referenced instead of duplicated.
- `product:knowledge` can show the files and recommend the next missing knowledge or registry action.
- `python3 scripts/release_check.py .` passes.

## Verification

- `python3 -m unittest discover -s tests -p 'test_*knowledge*registry*.py' -v`
- `python3 scripts/validate_project_artifacts.py .`
- `python3 scripts/release_check.py .`

## Entry Points

- `commands/product-knowledge.md`
- `scripts/project_knowledge.py`
- `scripts/project_memory.py`
- `templates/workspace/`
- `templates/knowledge/`
- `workspace/`
- `tests/`

## Scope Fence

Do not create a second database or copy external/sensitive source files into Git. Markdown registry files remain canonical and portable.

## Workflow Tasks

- [x] spec draft prepared → `specs/090-project-knowledge-and-artifact-registry/spec.md` (joint approval pending)
- [x] plan draft prepared → `specs/090-project-knowledge-and-artifact-registry/plan.md` (joint approval pending)
- [ ] execute → templates, parser, validation, migration guidance, command updates, and tests
- [ ] review → `specs/090-project-knowledge-and-artifact-registry/review.md`

## Related Issues

- follows_up: `003-knowledge-evidence-layer`, `030-project-memory-layer`, `034-memory-capture-and-sync-workflow`, `043-memory-relationship-capture-prompts`, `085-project-production-records-and-playbooks`
- related: `033-business-document-workflow`, `044-product-dashboard-command`, `092-project-home-dashboard`
- blocks: `091-reproducible-analysis-runs-and-template-pack`, `092-project-home-dashboard`
- blocked_by:

## Reference Implementations

- Backstage repository identity and documentation annotations: `https://backstage.io/docs/features/software-catalog/well-known-annotations/`
- Backstage TechDocs Git-native documentation source: `https://backstage.io/docs/features/techdocs/creating-and-publishing/`
- Architecture Decision Record examples and lifecycle: `https://github.com/joelparkerhenderson/architecture-decision-record`

## Sessions

- 2026-07-16: User prioritized the project wiki and artifact registry as the first project-knowledge improvement.
- 2026-09-02: User approved the existing spec/plan for implementation and independent 086 QA preparation. Implementation, integration, release and actual application remain separate evidence.

## Links

- Roadmap: `workspace/roadmap.md`
- Goal: `workspace/goal.md`
- GitHub: https://github.com/dongwonlee222/moduflow/issues/20
- Spec: [English](../specs/090-project-knowledge-and-artifact-registry/spec.md) / [한국어](../specs/090-project-knowledge-and-artifact-registry/spec.ko.md)
- Plan: [Implementation plan](../specs/090-project-knowledge-and-artifact-registry/plan.md)
- Tasks: [Unchecked implementation tasks](../specs/090-project-knowledge-and-artifact-registry/tasks.md)
- Simulation: [Synthetic scenario matrix](../specs/090-project-knowledge-and-artifact-registry/simulation-matrix.md)
- Planning review: [한국어 검토·통합 인계](../specs/090-project-knowledge-and-artifact-registry/review-handoff.ko.md)
- Implementation authority: [Approval, ownership and lifecycle limitation](../specs/090-project-knowledge-and-artifact-registry/implementation-approval.md)

## Next Command

`product:execute 090-project-knowledge-and-artifact-registry`
