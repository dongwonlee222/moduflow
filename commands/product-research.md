---
description: Create a research note tied to an issue, spec, user problem, or opportunity.
argument-hint: "<title> [--issue-id id] [--spec path]"
user-invocable: false
---

# /product:research

Capture user, market, or problem research as durable evidence.

## Script

```bash
python3 scripts/project_knowledge.py . --kind research --title "Activation interview notes" --issue-id 003-activation
```

## Next

- `/moduflow spec` to update requirements
- `/moduflow evidence` to summarize supporting material
