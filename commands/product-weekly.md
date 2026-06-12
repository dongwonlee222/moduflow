---
description: Generate a weekly portfolio status summary.
argument-hint: "[portfolio path]"
---

# /product:weekly

Generate `weekly-status.md` from registered project state.

## Do

1. Read `projects.json`.
2. Collect phase, blockers, owner, and next command from each project.
3. Write a concise weekly status view in the portfolio workspace.
4. Keep detailed project state in each project repo.

## Next

- `/product:update` for stakeholder-ready communication
- `/product:roadmap` if priorities changed
