# Issue 105: Schema Migration and Doctor Triage

**Status: backlog** — created 2026-08-19.
**Priority: p0**
**Blocked-by: `102-project-registry-and-resolver`, `103-atomic-lifecycle-state-transaction`**

## Summary

Turn migration and Doctor output into a safe, prioritized recovery workflow that separates current blockers from legacy schema debt and applies only deterministic, reversible fixes.

## Source

- Type: user multi-project orchestration improvement request
- Link: local Codex attachment `pasted-text.txt`, 2026-08-19
- Owner / decision maker: Dongwon Lee
- Current phase: blocked

## Opportunity

Issues 001, 013, 024, 066, and 093 delivered non-destructive project mapping, a real Doctor gate, artifact validation, one legacy status migration, and shared issue-schema diagnostics. They do not yet provide a general migration plan/apply workflow, grouped triage, safe auto-fix classification, recovery points, or idempotent state reconciliation across configured paths.

## Scope

### In

- Group Doctor results into current blockers, active-issue defects, state drift, legacy migration needs, safe auto-fixes, and warnings/recommendations.
- Add concise `--summary` and active-work `--current` views without hiding raw diagnostics.
- Add migration `--plan` and guarded `--apply` semantics with explicit before/after values and recovery evidence.
- Add `doctor --fix-safe` for deterministic fixes only.
- Normalize documented legacy values such as `done`, `active`, `todo`, `transferred`, and `gate_passed` when meaning is unambiguous.
- Use the project resolver for configured artifact paths and Issue 103 transaction behavior for multi-file applies.
- Make repeated migrations idempotent and report `noop`.

### Out

- Guessing ambiguous lifecycle meaning.
- Moving existing folders or overwriting user prose.
- Hiding detailed diagnostics behind the summary.
- Treating optional configuration warnings as current-work blockers.

## Acceptance Criteria

- Doctor shows the actual current blocking cause and recommended repair before listing legacy schema noise.
- `--current` limits attention to active goal/issue and their dependencies while preserving a link to the full report.
- Migration plan lists every path, current value, proposed value, rationale, and reversibility before write.
- A failed apply restores the pre-migration state through Issue 103's transaction.
- Running the same migration twice returns `noop` on the second run.
- Ambiguous legacy values remain unchanged and are classified as human decisions.
- Nested configured issue paths are used consistently.
- Migrated legacy fixtures have no schema or lifecycle drift after apply.

## Verification

- Legacy project fixtures including mixed Markdown/frontmatter schemas and nested issue paths.
- Safe-fix, ambiguous-value, rollback, and double-run idempotence scenarios.
- `python3 scripts/release_check.py .`

## Entry Points

- `scripts/project_doctor.py`
- `scripts/project_migrate.py`
- `scripts/project_issue_schema.py`
- `scripts/project_lifecycle.py`
- `commands/product-doctor.md`
- `commands/product-migrate.md`

## Scope Fence

Do not infer uncertain state, delete legacy files, or make `--fix-safe` repair judgment-dependent findings.

## Workflow Tasks

- [ ] spec → `specs/105-schema-migration-and-doctor-triage/spec.md`
- [ ] plan → `specs/105-schema-migration-and-doctor-triage/plan.md`
- [ ] execute → triage views, migration plan/apply, safe fixes, recovery, and tests
- [ ] review → `specs/105-schema-migration-and-doctor-triage/review.md`

## Related Issues

- blocks:
- blocked_by: `102-project-registry-and-resolver`, `103-atomic-lifecycle-state-transaction`
- duplicates:
- follows_up: `001-project-migration`, `013-project-doctor-gate`, `024-artifact-schema-and-doctor-gates`, `066-legacy-issue-status-migration`, `093-frontmatter-issue-schema-readiness-gate`
- supersedes:
- related: `025-lightweight-project-adoption`

## Links

- Goal: `workspace/goal.md`
- Roadmap: `workspace/roadmap.md`
- Source audit: `specs/102-project-registry-and-resolver/source-audit.md`

## Next Command

After Issues 102 and 103 are done: `product:spec 105-schema-migration-and-doctor-triage`.
