# Issue 006: Validation And Distribution

**Status: done** — `validate_project_artifacts.py`/`release_check.py` shipped and gate every release; status.md shows all verification passed. Status line added 2026-07-06 (issue 066 follow-up: files whose specs-link line matched the migration's `Status:` grep were skipped).

## Summary

Strengthen validation, install, migration, and release tooling so ModuFlow can be safely used by multiple people across projects.

## Source

- Type: product direction
- Link: user conversation
- Date: 2026-06-11

## Opportunity

A shared plugin needs predictable installation, validation, upgrade, and rollback behavior.

## Scope

### In

- Add schema validation for config, state, issue, spec, and knowledge artifacts.
- Add migration and portfolio doctor scripts.
- Document install/update paths for Codex and Claude.
- Add release checklist for plugin publishing.

### Out

- Remote package registry automation.
- Hosted SaaS control plane.

## Acceptance Criteria

- The plugin validates its own package and project workspaces.
- Users can verify a project before and after migration.
- Release notes explain install and upgrade steps.

## Links

- Spec: `specs/006-validation-and-distribution/spec.md`
- Status: `specs/006-validation-and-distribution/status.md`
- Roadmap: `workspace/roadmap.md`

## Next Command

`product:spec 006-validation-and-distribution`
