---
description: Initialize, write, search, or retrieve portable project memory.
argument-hint: "[project path] [--write|--kind|--search|--get]"
---

# /product:memory

Manage repo-local project memory for deliverables, decisions, evidence, meetings, releases, notes, and references.

## PM-Friendly Flow

1. Initialize memory:

```bash
python3 scripts/project_memory.py <project-path> --write
```

2. Create a reviewable candidate when a workflow produces a durable decision, deliverable, evidence summary, release note, or failed approach:

```bash
python3 scripts/project_memory.py <project-path> --candidate --kind decision --title "Use Git canonical memory" --issue-id 034-memory-capture-and-sync-workflow --spec specs/034-memory-capture-and-sync-workflow/spec.md --summary "Keep memory canonical in Git-tracked Markdown." --source-event decision-detected --source-artifacts specs/034-memory-capture-and-sync-workflow/spec.md --tags memory,team,pm
```

3. Review candidates:

```bash
python3 scripts/project_memory.py <project-path> --list-candidates
```

4. Approve a candidate:

```bash
python3 scripts/project_memory.py <project-path> --approve 2026-06-26-use-git-canonical-memory
```

5. Search with source links and match reasons:

```bash
python3 scripts/project_memory.py <project-path> --search "canonical memory"
```

6. Get mirror/export guidance:

```bash
python3 scripts/project_memory.py <project-path> --export-guidance google-drive
```

## Rules

- `memory/` is the source of truth.
- External indexes, MCP servers, vector stores, and databases are rebuildable caches/adapters.
- Prefer relative project-local links so projects remain portable when copied, cloned, or zipped.
- Do not import private personal memory into a project automatically.
- In team mode, shared memory should be approved through Git branch/PR review before merge.
- RAG, LangGraph, MCP servers, Basic Memory, projectmem, mem0, Supermemory, Google Drive, and Obsidian are adapters or mirrors, not the source of truth.
- PMs can approve memory candidates through natural language; implementation hosts may translate that approval into the CLI calls above.

## Next

- `/product:evidence` to review related memory and evidence
- `/product:decision` when a memory entry supports a decision
