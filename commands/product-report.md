---
description: Create a report artifact tied to an issue, spec, roadmap, or release.
argument-hint: "<title> [--issue-id id] [--spec path]"
---

# /product:report

Capture project reports, market reports, operating summaries, or stakeholder-ready evidence.

Read the executing ModuFlow package's `docs/output-format.md`. Start the report with **왜 필요한지 → 해결해야 할 문제 → 기대 효과**, then evidence/results and next actions. Fill the generated artifact from actual project evidence; expected benefits are not measured results.

## Script

```bash
python3 scripts/project_knowledge.py . --kind report --title "June product report" --issue-id 003-growth
```

## Next

- `/product:update` for stakeholder communication
- `/product:roadmap` when priority changes
