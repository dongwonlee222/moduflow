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

4. Preserve project-local Git artifacts as the source of truth.

## Next

- `/product:projects` to inspect registered projects
- `/product:weekly` to produce a weekly status view
