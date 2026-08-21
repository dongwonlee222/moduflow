---
description: Inspect or resolve explicitly registered projects in a portfolio workspace.
argument-hint: "[portfolio path] [--resolve <request>|--select <project-id>]"
---

# /product:projects

Read the versioned `projects.json` registry and summarize registered project IDs, names, canonical paths, owners, resolution state, and current state.

## Do

1. Read `moduflow.projects.v2` or read-compatible `moduflow.projects.v1` through the shared registry parser.
2. For each explicitly registered project, read `.moduflow/state.json` and its canonical `workflow` path when available.
3. Report invalid registry entries and missing project state as warnings; never choose the first entry on ambiguity.
4. Resolve request text without writing:

```bash
python3 scripts/project_portfolio.py <portfolio-path> --resolve "모두의충전 배너"
```

5. Record a recent project only after an explicit ID selection:

```bash
python3 scripts/project_portfolio.py <portfolio-path> --select modu-charge
```

`--select` writes only `project-selection.json` beside the registry. It does not write to a project repository.

## Next

- `/product:portfolio` to refresh dashboard files
- `/product:status` inside a project for deeper inspection
