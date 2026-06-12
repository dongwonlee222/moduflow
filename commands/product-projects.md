---
description: Inspect registered projects in a portfolio workspace.
argument-hint: "[portfolio path]"
---

# /product:projects

Read `projects.json` and summarize registered project IDs, names, paths, owners, and current state.

## Do

1. Read `projects.json`.
2. For each project, read `.moduflow/state.json` when available.
3. Report missing project state as warnings.
4. Do not write to project repos.

## Next

- `/product:portfolio` to refresh dashboard files
- `/product:status` inside a project for deeper inspection
