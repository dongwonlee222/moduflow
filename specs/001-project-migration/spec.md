# Project Migration Spec

## Problem

Existing projects often already have docs, planning folders, reports, issue lists, and research notes. ModuFlow must adopt those projects without overwriting files or forcing an immediate canonical folder structure.

## Users

- Project owners adding ModuFlow to an existing repo.
- Agents diagnosing whether a project is ready for ModuFlow.
- Teams that need a migration plan before changing repository layout.

## Goals

- Detect likely existing project artifact folders.
- Recommend a non-destructive migration mode by default.
- Generate a migration plan that maps existing folders into ModuFlow paths.
- Keep `product:start` safe by making migration a separate explicit step.
- Make `product:doctor` explain migration readiness.

## Non-Goals

- Moving existing files automatically.
- Importing GitHub, Linear, Slack, or Notion data.
- Requiring GitHub CLI authentication.
- Replacing project-specific docs conventions.

## Migration Modes

### Overlay

ModuFlow creates only `.moduflow/` and index/status files while existing folders remain unchanged. This is best when a project is already organized but does not match ModuFlow names.

### Mapped

ModuFlow records existing folder paths in `.moduflow/config.json`, such as `docs/specs` for specs or `planning` for workspace. This is the default recommendation when candidate folders are found.

### Canonical

The project eventually moves into standard `issues/`, `specs/`, `workspace/`, and `knowledge/` paths. This mode requires explicit user approval and is not automated in this issue.

## Requirements

- `project_doctor.py` reports candidate folders for issues, specs, workspace, reports, benchmarks, research, decisions, and data notes.
- `project_doctor.py` recommends `product:migrate --mode mapped` when candidates exist and ModuFlow is not initialized.
- `scripts/project_migrate.py` supports dry-run planning without writing files.
- `scripts/project_migrate.py --write` creates only `.moduflow/config.json`, `.moduflow/state.json`, and missing workspace index files.
- `product:migrate` command documents dry-run first behavior.
- Existing files are never overwritten.

## Acceptance Criteria

- A project with `docs/specs`, `planning`, and `reports` receives candidate mappings in doctor output.
- Dry-run migration prints a JSON plan and creates no files.
- Write mode creates missing ModuFlow metadata and index files without moving existing project documents.
- Validator includes the new command and migration script.

## Risks

- Candidate detection can be too clever. Keep it conservative and transparent.
- Writing config to the wrong Git root would be harmful. Always use detected Git root or the provided path when no Git repo exists.
- Users may confuse migration with canonicalization. Use dry-run and explicit mode names to keep the distinction clear.

## Next Command

`product:plan 001-project-migration`
