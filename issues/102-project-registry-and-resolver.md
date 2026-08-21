# Issue 102: Project Registry and Resolver

**Status: done** — created, approved, implemented, reviewed, and verified 2026-08-19.
**Priority: p0**
**Blocked-by:**

## Summary

Add a versioned, explicit multi-project registry and one deterministic resolver so every ModuFlow command uses the same project identity and canonical artifact paths before reading or writing project data.

## Source

- Type: user multi-project orchestration improvement request
- Link: local Codex attachment `pasted-text.txt`, 2026-08-19
- Owner / decision maker: Dongwon Lee
- Current phase: done; registry, resolver, compatibility, consumer convergence, and release verification complete

## Opportunity

ModuFlow already has project profiles, a portfolio `projects.json`, project-aware dashboard concepts, and safe configured-path support in the normalized issue-schema/lifecycle layer. The missing boundary is one project resolver plus convergence of the remaining consumers that still assume `<project-root>/issues/` or `<project-root>/workspace/`. Those consumers can report an empty project or update a different view when a registered project uses nested canonical paths.

## Scope

### In

- Define `moduflow.projects.v2` with project ID, aliases, root, canonical issue/spec/workspace/memory/playbook paths, and trust scope.
- Resolve project context in a fixed order: explicit ID, current directory, registered name/alias, active issue project, last explicit selection, then unresolved.
- Use only explicitly registered projects; do not scan arbitrary sibling directories.
- Return `resolved`, `ambiguous`, or `unresolved` with evidence and one clarification prompt when needed.
- Provide one canonical path API for intake, lifecycle, issue schema, doctor, production, dashboard, and migration consumers.
- Preserve a read-compatible migration path from `moduflow.projects.v1` and project-local profile/config metadata.

### Out

- Executing natural-language work after project resolution; Issue 104 owns that orchestration.
- Atomic state writes; Issue 103 owns transaction behavior.
- Dashboard project-selector UI; Issue 086 owns that UI.
- Moving existing project folders or discovering unregistered projects.

## Acceptance Criteria

- Two registered projects may use different issue paths, and every migrated consumer reads only the selected project's configured path.
- An explicit project ID always wins over working-directory and alias signals.
- Multiple matching aliases return `ambiguous`; no project file is changed before the user answers one question.
- An unregistered sibling project is never inspected as a resolution candidate.
- Canonical paths are normalized, contained within the registered root unless explicitly allowed by schema, and reported with their resolution source.
- `projects.v1` registries remain readable and receive deterministic v2 migration guidance rather than silent rewriting.
- Project A/B isolation fixtures cover issue, memory, playbook, doctor, and dashboard consumers.
- Existing Issue 093 configured-path and containment behavior is reused and remains green; no second issue parser/path normalizer is introduced.
- Git Markdown/JSON remains canonical; no central database is introduced.

## Verification

- Registry v1/v2 parser and migration fixtures.
- Project A/B alias, cwd, ambiguity, and unregistered-sibling fixtures.
- Nested issue-path contract tests across lifecycle, doctor, intake, production, and dashboard consumers.
- `python3 scripts/validate_project_artifacts.py .`
- `python3 scripts/release_check.py .`

## Entry Points

- `portfolio/projects.json`
- `scripts/project_portfolio.py`
- `scripts/project_profile.py`
- `scripts/project_intake.py`
- `scripts/project_lifecycle.py`
- `scripts/project_issue_schema.py`
- `scripts/project_doctor.py`
- `scripts/project_production.py`
- `.moduflow/config.json`

## Scope Fence

Do not crawl arbitrary folders, move user artifacts, add browser-side writes, or create a second canonical project database.

## Workflow Tasks

- [x] spec → `specs/102-project-registry-and-resolver/spec.md` + `spec.ko.md` (approved 2026-08-19)
- [x] source audit → `specs/102-project-registry-and-resolver/source-audit.md` (current-source evidence; no implementation)
- [x] plan → `specs/102-project-registry-and-resolver/plan.md` + `plan.ko.md` + `tasks.md`
- [x] execute → registry v2, resolver, consumer adoption, migration guidance, and tests
- [x] review → `specs/102-project-registry-and-resolver/review.md`

## Related Issues

- blocks: `109-canonical-project-context-consumer-convergence`, `110-project-operation-capability-enforcement`, `104-project-aware-natural-language-request-orchestrator`, `105-schema-migration-and-doctor-triage`, `107-shared-approved-playbook-layer`
- blocked_by:
- duplicates:
- follows_up: `002-project-profile`, `004-portfolio-workspace`, `025-lightweight-project-adoption`
- supersedes:
- related: `086-project-aware-production-library-dashboard`, `093-frontmatter-issue-schema-readiness-gate`, `111-runtime-provenance-and-validation-mode-separation`

## Links

- Goal: `workspace/goal.md`
- Spec: `specs/102-project-registry-and-resolver/spec.md`
- Korean spec: `specs/102-project-registry-and-resolver/spec.ko.md`
- Source audit: `specs/102-project-registry-and-resolver/source-audit.md`
- Korean source audit: `specs/102-project-registry-and-resolver/source-audit.ko.md`
- Plan: `specs/102-project-registry-and-resolver/plan.md`
- Korean plan summary: `specs/102-project-registry-and-resolver/plan.ko.md`
- Tasks: `specs/102-project-registry-and-resolver/tasks.md`
- Post-release validation: `workspace/reviews/2026-08-21-issue-102-post-release-validation.md`
- Roadmap: `workspace/roadmap.md`

## Next Command

`product:status 102-project-registry-and-resolver`.
