---
description: Create a decision record tied to an issue, spec, or roadmap choice.
argument-hint: "<title> [--issue-id id] [--spec path]"
---

# /product:decision

Record why a product or technical decision was made.

## Script

```bash
python3 scripts/project_knowledge.py . --kind decision --title "Payment priority" --issue-id 003-payment --spec specs/003-payment/spec.md --decision-supported "Prioritize card onboarding"
```

## Required Fields

- issue ID when applicable
- spec path when applicable
- decision supported
- evidence
- caveats
- next action

## Next

- `/product:evidence` to review supporting material
- `/product:roadmap` when priority changes
