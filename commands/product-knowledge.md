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
5. **Capture relationships at write time (043).** When a knowledge artifact becomes a memory entry, list existing ids and link real nodes — `python3 scripts/project_memory.py <project-path> --list-ids` — then set `--issue-id` and any content-verified `--supersedes/--depends-on/--references`. Present options; never auto-link by topic (042's anti-goal).

## Next

- `/product:decision` for decision records
- `/product:evidence` to gather evidence for an issue or spec

## Record Contract (issue 075)

Every knowledge record this command writes carries shared frontmatter so `product:promote` and retention tooling can operate on it:

- `kind`: `knowledge`
- `date`: ISO date
- `summary`: one line
- `retrieval_trigger`: when a future session should re-read this record (semantic cue, required for new records)
- `promoted_to`: issue id, written by `product:promote` only
- `superseded_by`: record id — supersede, never delete or move record files

Write discipline (AI writers create records for free, so creation is NOT the default):

1. Before creating, search existing records of this kind for the same subject.
2. Prefer UPDATE (extend the existing record) or SUPERSEDE (new record + `superseded_by` on the old one) over ADD.
3. NOOP when nothing genuinely new — do not write a file to log activity.
