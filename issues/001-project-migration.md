# Issue 001: Project Migration

**Status: done** — `scripts/project_migrate.py` shipped in the 0.1.x era; status.md shows all verification passed. Status line added 2026-07-06 (issue 066 follow-up: files whose specs-link line matched the migration's `Status:` grep were skipped).

## Summary

Add a safe migration workflow for projects that already have their own folder structures, documents, issues, reports, and planning artifacts.

## Source

- Type: product direction
- Link: user conversation
- Date: 2026-06-11

## Opportunity

Users may already manage projects with different structures. ModuFlow should not overwrite or force canonical folders before it understands the existing project.

## Scope

### In

- Add `product:migrate` command definition.
- Define migration modes: `overlay`, `mapped`, and `canonical`.
- Add migration plan template.
- Extend project doctor output to identify candidate folders.
- Preserve existing files by default.

### Out

- Automatic destructive file moves.
- Mandatory GitHub issue migration.

## Acceptance Criteria

- A user can run a migration planning flow before adding ModuFlow files.
- Existing project folders can be mapped through `.moduflow/config.json`.
- The recommended default mode is non-destructive.
- Doctor output clearly recommends next steps.

## Links

- Spec: `specs/001-project-migration/spec.md`
- Status: `specs/001-project-migration/status.md`
- Roadmap: `workspace/roadmap.md`

## Next Command

`product:spec 001-project-migration`
