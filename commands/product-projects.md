---
description: Inspect or resolve explicitly registered projects in a portfolio workspace.
argument-hint: "[portfolio path] [--resolve <request>|--select <project-id>]"
---

# /product:projects

Read the versioned `projects.json` registry and summarize registered project IDs, names, canonical paths, owners, resolution state, and current state.

## Do

1. Read `moduflow.projects.v2` or read-compatible `moduflow.projects.v1` through the shared registry parser.
2. For each explicitly registered project, read `.moduflow/state.json` and its canonical `workflow` path when available, then show `project_status`, normalized policy trust, capabilities, and denial reasons separately from resolution status.
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

Portfolio initialization, render, and selection use the portfolio-control context. The selected project's policy does not grant or deny those portfolio-owned writes. Conversely, a portfolio authorization decision cannot be reused for a target-project mutation because the canonical roots must match.

When policy denies a CLI mutation, print the stable `moduflow.project-operation-authorization.v1` JSON and return non-zero. Keep archived and read-only targets visible for diagnostic reads.

## Next

- `/product:portfolio` to refresh dashboard files
- `/product:status` inside a project for deeper inspection
