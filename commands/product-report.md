---
description: Create a report artifact tied to an issue, spec, roadmap, or release.
argument-hint: "<title> [--issue-id id] [--spec path]"
---

# /product:report

Capture project reports, market reports, operating summaries, or stakeholder-ready evidence.

## Script

```bash
python3 scripts/project_knowledge.py . --kind report --title "June product report" --issue-id 003-growth
```

## Next

- `/product:update` for stakeholder communication
- `/product:roadmap` when priority changes
