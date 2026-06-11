---
description: Plan or apply a non-destructive ModuFlow migration for an existing project.
argument-hint: "[project path] [--mode overlay|mapped|canonical] [--write]"
---

# /product:migrate

Adopt an existing project without moving or overwriting its current files.

## Do

1. Run `product:doctor` or `scripts/project_doctor.py <project-path>` first.
2. Detect likely existing folders for issues, specs, workspace, reports, benchmarks, research, decisions, and data notes.
3. Default to dry-run mode and print a migration plan.
4. Use `--write` only to create missing `.moduflow` metadata and workspace index files.
5. Never move, rename, delete, or overwrite existing project files.

## Modes

- `overlay`: add ModuFlow metadata and index files while leaving existing structure untouched.
- `mapped`: record existing folders in `.moduflow/config.json`; this is the recommended default when candidates exist.
- `canonical`: planning-only mode for teams that may later move into standard `issues/`, `specs/`, `workspace/`, and `knowledge/` paths.

## Script

```bash
python3 scripts/project_migrate.py <project-path> --mode mapped
python3 scripts/project_migrate.py <project-path> --mode mapped --write
```

## Output

- Project root
- Candidate folder mappings
- Proposed `.moduflow/config.json`
- Files that would be written
- Whether this is a dry run

## Next

- `/product:status` after write mode
- `/product:start` for new projects with no existing structure
- `/product:profile` when project profile support is available
