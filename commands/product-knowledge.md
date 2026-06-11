---
description: Initialize or inspect the project knowledge evidence layer.
argument-hint: "[project path] [--write]"
---

# /product:knowledge

Create or inspect Git-native evidence folders for decisions, benchmarks, reports, research, data notes, and references.

## Do

1. Run dry-run first:

```bash
python3 scripts/project_knowledge.py <project-path>
```

2. Use `--write` to create missing folders and `knowledge/index.md` only:

```bash
python3 scripts/project_knowledge.py <project-path> --write
```

3. Preserve existing files.
4. Link artifacts to issue IDs and specs when known.

## Next

- `/product:decision` for decision records
- `/product:evidence` to gather evidence for an issue or spec
