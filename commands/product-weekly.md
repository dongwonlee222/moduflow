---
description: Generate a weekly portfolio status summary.
argument-hint: "[portfolio path]"
---

# /product:weekly

Generate `weekly-status.md` from registered project state.

Read the executing ModuFlow package's `docs/output-format.md`. For each substantive work summary, explain **왜 필요한지 → 해결해야 할 문제 → 기대 효과** before implementation and verification; keep portfolio summaries concise and project evidence separate.

## Do

1. Read `projects.json`.
2. Collect phase, blockers, owner, and next command from each project.
3. Write a concise weekly status view in the portfolio workspace.
4. Keep detailed project state in each project repo.

## Next

- `/product:update` for stakeholder-ready communication
- `/product:roadmap` if priorities changed
