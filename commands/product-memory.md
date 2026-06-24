---
description: Initialize, write, search, or retrieve portable project memory.
argument-hint: "[project path] [--write|--kind|--search|--get]"
---

# /product:memory

Manage repo-local project memory for deliverables, decisions, evidence, meetings, releases, notes, and references.

## Do

1. Run dry-run first:

```bash
python3 scripts/project_memory.py <project-path>
```

2. Use `--write` to create missing portable memory folders and `memory/index.md` only:

```bash
python3 scripts/project_memory.py <project-path> --write
```

3. Create memory entries with project-local relative links:

```bash
python3 scripts/project_memory.py <project-path> --kind decision --title "Use repo-local memory" --issue-id 030-project-memory-layer --spec specs/030-project-memory-layer/spec.md --summary "Keep memory portable inside the repo."
```

4. Search or get entries:

```bash
python3 scripts/project_memory.py <project-path> --search "portable memory"
python3 scripts/project_memory.py <project-path> --get 2026-06-24-use-repo-local-memory
```

## Rules

- `memory/` is the source of truth.
- External indexes, MCP servers, vector stores, and databases are rebuildable caches/adapters.
- Prefer relative project-local links so projects remain portable when copied, cloned, or zipped.
- Do not import private personal memory into a project automatically.

## Next

- `/product:evidence` to review related memory and evidence
- `/product:decision` when a memory entry supports a decision
