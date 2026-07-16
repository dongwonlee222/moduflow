# Issue 090: Project Knowledge and Artifact Registry

**Status: backlog** — created 2026-07-16.
**Priority: p1**

## Summary

Make `workspace/knowledge.md` a structured project wiki and add `workspace/artifacts.md` as the canonical registry for reports, local files, Google Sheets, related issues, periods, and draft/final state.

## Source

- Type: user product direction
- Link: local Codex session, 2026-07-16
- Owner / decision maker: Dongwon Lee
- Current phase: backlog

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

- [ ] spec → `specs/090-project-knowledge-and-artifact-registry/spec.md`
- [ ] plan → `specs/090-project-knowledge-and-artifact-registry/plan.md`
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

## Links

- Roadmap: `workspace/roadmap.md`
- Goal: `workspace/goal.md`
- GitHub: https://github.com/dongwonlee222/moduflow/issues/20

## Next Command

`product:spec 090-project-knowledge-and-artifact-registry`
