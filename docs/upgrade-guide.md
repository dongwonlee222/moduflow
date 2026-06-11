# Upgrade Guide

## Existing Users

Existing commands remain available:

- `product:start`
- `product:status`
- `product:issue`
- `product:spec`
- `product:plan`
- `product:execute`

New layers are opt-in:

- `product:migrate`
- `product:profile`
- `product:knowledge`
- `product:portfolio`
- `product:handoff`

## Existing Projects

1. Run `product:doctor`.
2. Run `product:migrate` in dry-run mode if the project already has its own structure.
3. Run `product:profile --write` to add project metadata.
4. Run `product:knowledge --write` to add evidence folders.
5. Run `product:handoff --write` to add team workflow artifacts.
6. Run `python3 scripts/validate_project_artifacts.py <project-path>`.

## Codex

After changing the plugin package, refresh the personal marketplace entry and cachebuster, then reinstall or update `moduflow@personal`.

## Claude

Use the local plugin source or symlink described in `INSTALL.md`. Reopen the client after changing plugin metadata.
