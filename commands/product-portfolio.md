---
description: Initialize or render a portfolio workspace for multiple ModuFlow projects.
argument-hint: "[portfolio path] [--write|--render|--resolve <request>|--select <project-id>]"
---

# /product:portfolio

Create or refresh a central portfolio workspace over multiple project-local ModuFlow workspaces.

## Do

1. Initialize a portfolio workspace:

```bash
python3 scripts/project_portfolio.py <portfolio-path> --write
```

2. Register projects in `moduflow.projects.v2` with an ID, name, aliases, canonical root, all eight relative canonical paths, trust scope, status, and owner. Existing `moduflow.projects.v1` files remain read-only compatible and receive migration guidance.
3. Render portfolio dashboard and weekly status:

```bash
python3 scripts/project_portfolio.py <portfolio-path> --render
```

4. The dashboard reads each project's `.moduflow/state.json` and canonical `workflow/team-state.json` only after registry validation.
5. Preserve project-local Git artifacts as the source of truth.

## Resolution

- `--resolve <request>` applies explicit ID/CWD/alias/active/recent precedence and performs no write.
- `--select <project-id>` atomically writes only `project-selection.json` after registry membership validation.
- `ambiguous` and `unresolved` results expose only safe candidate identity and never read candidate project content.

## Team Columns

Portfolio dashboard rows include:

- Active Work: assigned/active issue owners from `workflow/team-state.json`
- Review: issues waiting for review or approved for release
- Blockers: project-level blockers from `.moduflow/state.json`
- Next Command: the project-local next action

## Next

- `/product:projects` to inspect registered projects
- `/product:weekly` to produce a weekly status view
