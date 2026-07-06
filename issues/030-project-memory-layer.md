# Issue 030: Project Memory Layer

**Status: backlog** — half-implemented prototype (`Phase: prototype`, 5 of 10 workflow tasks unchecked); much of the memory scope later landed via 034/040/043, so re-scope before picking up. Status line added 2026-07-06 (issue 066 follow-up: files whose specs-link line matched the migration's `Status:` grep were skipped).

## Summary

Expand ModuFlow from issue-centric PM tracking into project-level long-term memory management for deliverables, decisions, evidence, operating context, and reusable project memory.

## Source

- Type: user feedback / product direction
- Link: conversation, 2026-06-24
- Date: 2026-06-24

## Lifecycle

- Phase: prototype
- Created: 2026-06-24
- Started: 2026-06-24
- Target End:
- Completed:
- Last Updated: 2026-06-24

## Opportunity

ModuFlow currently keeps strong Git-native issue, spec, plan, task, and status artifacts, but project memory is still too shallow. The existing `knowledge/` layer initializes folders for decisions, reports, research, data notes, references, and benchmarks, yet it does not act like a searchable project memory system. The user-facing name should be **memory**, not knowledge.

Each project needs a durable memory layer that starts from generated deliverables and grows into a full record of why the project moved the way it did: decisions, evidence, reports, meeting notes, operational learnings, source links, handoffs, release notes, and reusable context for future agents.

## Scope

### In

- Define project-local long-term memory as a first-class ModuFlow artifact model.
- Define `memory/` as the preferred project-local folder name; support migration from existing `knowledge/` without overwriting user files.
- Extend passive knowledge folders into a searchable project memory registry.
- Track deliverables as memory entries, not only as issue task links.
- Add decision records with clear decision, rationale, evidence, alternatives, owner, and reversal conditions.
- Add memory entry types for deliverables, decisions, research, reports, data notes, references, meetings, handoffs, releases, and operational notes.
- Define a `write / search / get` style project-memory contract inspired by `personal-memory`, while preserving Git-native Markdown files as the source of truth.
- Link memories bidirectionally with issues, specs, roadmap items, releases, and project profile metadata.
- Guarantee project portability: a project copied, zipped, cloned, or moved to another machine keeps its memory because memory files live inside the project repo.
- Treat any external memory index, vector index, MCP server, or host database as a rebuildable cache/adapter, never as the source of truth.
- Use relative project-local links by default so memory entries survive path changes.
- Provide migration guidance from existing `knowledge/` artifacts and scattered project documents.

### Out

- Replacing issues, specs, or roadmap artifacts.
- Importing personal/private memory into company project repos automatically.
- Blind ingestion of external documents without user approval.
- Requiring vector search, database infrastructure, or hosted memory services in v1.
- Making every chat message a memory entry.
- Storing project memory only in an external service that would break when the project is moved.

## Acceptance Criteria

- A spec defines the project memory model, entry schema, folder/index strategy, and relationship to issues/specs/roadmap.
- Project deliverables can be registered and later found without knowing the original issue number.
- Decision records include rationale, supporting evidence, alternatives, owner, confidence, and reversal conditions.
- `product:evidence` or a new project-memory command can search project memories by query, type, issue, spec, roadmap item, or tag.
- Doctor validates that project memory is initialized and that registered memory links point to existing files.
- A project remains self-contained when moved: `.moduflow/`, `workspace/`, `issues/`, `specs/`, and `memory/` are sufficient to recover current state and project memory.
- External indexes can be deleted and rebuilt from project-local memory files.
- Existing `knowledge/` projects can migrate without losing files or overwriting user artifacts.

## Workflow Tasks

Every artifact-producing step is a tracked task here - never produce a spec/plan/design/review off the books. Check the box and link the artifact when done.

- [ ] spec -> `specs/030-project-memory-layer/spec.md`
- [ ] plan -> `specs/030-project-memory-layer/plan.md`
- [ ] execute -> PR / commits
- [ ] review -> review notes
- [x] compare ModuFlow `knowledge/` with `personal-memory` contracts
- [x] define project memory entry schema and registry/index format
- [x] define project portability and external-index cache rules
- [x] define commands for write/search/get-style project memory flows
- [x] add doctor and validation gates for memory links
- [ ] add migration path from existing knowledge artifacts

## Prototype Shipped

- Added `scripts/project_memory.py` for portable project memory init/write/search/get.
- Added `commands/product-memory.md`.
- Added `templates/memory/entry.md`.
- Added `memory/` to lightweight project migration plans.
- Added `memory` readiness to project doctor and project artifact validation.
- Added `tests/test_project_memory.py`.
- Initialized this ModuFlow repo's own `memory/` folder and recorded `memory/decisions/2026-06-24-use-portable-project-memory.md`.

## Verification

- `python3 -m unittest tests.test_project_memory -v` passed.
- `python3 -m unittest tests.test_project_memory tests.test_project_migration tests.test_validation_distribution -v` passed.
- `python3 -m unittest discover -s tests -v` passed (81 tests).
- `python3 scripts/validate_project_artifacts.py .` passed.
- `python3 scripts/validate_moduflow.py .` passed.
- `python3 scripts/release_check.py .` passed.

## Related Issues

- blocks:
- blocked_by:
- duplicates:
- follows_up: `003-knowledge-evidence-layer`, `011-workflow-task-tracking`, `024-artifact-schema-and-doctor-gates`
- supersedes:
- related: `029-antigravity-artifact-sync-connector`

## Sessions

- 2026-06-24: User clarified that each project needs long-term memory management from deliverables through project artifacts, decisions, and durable context; current ModuFlow feels like it only manages issues.

## Links

- Personal memory reference: `/Users/dongwon.lee/workhub/projects/personal-memory`
- Spec: `specs/030-project-memory-layer/spec.md`
- Status: `specs/030-project-memory-layer/status.md`
- Sessions: `sessions/030-project-memory-layer/`
- Roadmap: `workspace/roadmap.md`

## Next Command

`/product:spec 030-project-memory-layer`
