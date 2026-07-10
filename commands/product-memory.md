---
description: Initialize, write, search, or retrieve portable project memory.
argument-hint: "[project path] [--write|--kind|--search|--get]"
---

# /product:memory

Manage repo-local project memory for deliverables, decisions, evidence, meetings, releases, notes, and references.

For recurring production outputs that must preserve artifacts, decisions, failed attempts, reusable patterns, external copy, internal reporting copy, and human-approved playbooks, use `/product:production`. This command remains the generic long-term memory path.

## PM-Friendly Flow

1. Initialize memory:

```bash
python3 scripts/project_memory.py <project-path> --write
```

2. **Capture relationships at write time (043).** Before creating an entry, list existing ids so you link to *real* nodes — never free-type ids, never auto-link by topic:

```bash
python3 scripts/project_memory.py <project-path> --list-ids          # all entries (id/kind/title)
python3 scripts/project_memory.py <project-path> --list-ids --kind decision   # filter by kind
```

Then, when writing, pass the relationships you can **content-verify** plus the `issue_id`:

```bash
python3 scripts/project_memory.py <project-path> --candidate --kind decision --title "Use Git canonical memory" --issue-id 034-memory-capture-and-sync-workflow --spec specs/034-memory-capture-and-sync-workflow/spec.md --summary "Keep memory canonical in Git-tracked Markdown." --source-event decision-detected --source-artifacts specs/034-memory-capture-and-sync-workflow/spec.md --supersedes 2026-06-24-use-portable-project-memory --references 2026-06-25-some-evidence --tags memory,team,pm
```

- Always set `--issue-id` when the entry came from an issue — this is what fills the issue↔memory cross-links the 045 project view shows.
- Pass `--supersedes` / `--depends-on` / `--references` only for links you can justify from the content. **Present options, never auto-link** (042's anti-goal). Relationships survive `--approve` unchanged.
- `product:doctor` surfaces "isolated" entries (no links, no issue_id) as an informational hint — a nudge to link, never a hard failure.

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

## Record Contract (issue 075)

Every memory record this command writes carries shared frontmatter so `product:promote` and retention tooling can operate on it:

- `kind`: `memory`
- `date`: ISO date
- `summary`: one line
- `retrieval_trigger`: when a future session should re-read this record (semantic cue, required for new records)
- `promoted_to`: issue id, written by `product:promote` only
- `superseded_by`: record id — supersede, never delete or move record files

Write discipline (AI writers create records for free, so creation is NOT the default):

1. Before creating, search existing records of this kind for the same subject.
2. Prefer UPDATE (extend the existing record) or SUPERSEDE (new record + `superseded_by` on the old one) over ADD.
3. NOOP when nothing genuinely new — do not write a file to log activity.
