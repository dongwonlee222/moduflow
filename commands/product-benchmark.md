---
description: Create a benchmark or competitive/reference analysis artifact.
argument-hint: "<title> [--issue-id id] [--spec path]"
user-invocable: false
---

# /product:benchmark

Capture competitor, reference product, UX, pricing, or operational benchmarks.

## Script

```bash
python3 scripts/project_knowledge.py . --kind benchmark --title "Checkout onboarding benchmark" --issue-id 003-checkout
```

## Next

- `/moduflow decision` if the benchmark supports a choice
- `/moduflow design` if the benchmark affects UX
