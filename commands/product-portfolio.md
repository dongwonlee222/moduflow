---
description: Initialize or render a portfolio workspace for multiple ModuFlow projects.
argument-hint: "[portfolio path] [--write|--render]"
---

# /product:portfolio

Create or refresh a central portfolio workspace over multiple project-local ModuFlow workspaces.

## Do

1. Initialize a portfolio workspace:

```bash
python3 scripts/project_portfolio.py <portfolio-path> --write
```

2. Register projects in `projects.json`.
3. Render portfolio dashboard and weekly status:

```bash
python3 scripts/project_portfolio.py <portfolio-path> --render
```

4. The dashboard reads each project's `.moduflow/state.json` and, when present, `workflow/team-state.json`.
5. Preserve project-local Git artifacts as the source of truth.

## Team Columns

Portfolio dashboard rows include:

- Active Work: assigned/active issue owners from `workflow/team-state.json`
- Review: issues waiting for review or approved for release
- Blockers: project-level blockers from `.moduflow/state.json`
- Next Command: the project-local next action

## Next

- `/product:projects` to inspect registered projects
- `/product:weekly` to produce a weekly status view
