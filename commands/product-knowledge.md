---
description: Initialize or inspect the project knowledge evidence layer.
argument-hint: "[project path] [--inspect|--query|--register|--read-sources] [--write]"
---

# /product:knowledge

Create or inspect Git-native evidence folders for decisions, benchmarks, reports, research, data notes, and references.

## Do

1. Run dry-run first:

```bash
python3 scripts/project_knowledge.py <project-path>
```

2. Use `--write` to create missing folders, `knowledge/index.md`, and the curated `workspace/knowledge.md` / `workspace/artifacts.md` pair:

```bash
python3 scripts/project_knowledge.py <project-path> --write
```

3. Preserve existing files.
4. Link artifacts to issue IDs and specs when known.
5. **Capture relationships at write time (043).** When a knowledge artifact becomes a memory entry, list existing ids and link real nodes — `python3 scripts/project_memory.py <project-path> --list-ids` — then set `--issue-id` and any content-verified `--supersedes/--depends-on/--references`. Present options; never auto-link by topic (042's anti-goal).

## Find Materials Without Scanning Originals

The wiki gives short project guidance; the catalog identifies which material to read and why. Search reads metadata only, so unrelated originals and private materials stay unopened.

```bash
python3 scripts/project_knowledge.py <project-path> --inspect
python3 scripts/project_knowledge.py <project-path> --query "population"
python3 scripts/project_knowledge.py <project-path> --read-sources --artifact-id <art-UUIDv4>
```

Use `--shared-ref <commit-or-ref>` for a committed handoff. Keep the returned `snapshot_commit` and use that exact OID for the selected-source read; do not silently switch to a newer HEAD. Dirty, ignored or uncommitted local files never rescue a missing committed source. An external/private locator is a handoff requiring an authorized tool, not permission to fetch it.

Plain CLI roots report an unbound project identity. A host with a resolved registry-v2 context should pass it to the Python facade; never derive a durable project ID from a worktree path. Review `total`, `omitted`, `truncated` and per-entry metadata/availability/freshness/share status instead of treating a short result as the entire project.

## Preview and Register an Issue-Linked Output

Prepare one JSON entry following `moduflow.artifacts.v1` in the workspace template/spec: stable UUID, purpose, read trigger, dates/period, owner, actual issue IDs, approval state and safe original locators. Do not include source bodies, private absolute paths, credentials or signed URLs. Dates and approval evidence must be supplied, not inferred from the filename.

```bash
python3 scripts/project_knowledge.py <project-path> --register <entry.json> --issue-id <actual-issue-id>
python3 scripts/project_knowledge.py <project-path> --register <entry.json> --issue-id <actual-issue-id> --write
```

The first command is read-only preview. Retain the returned `artifact_id` in the entry JSON for apply/retry if it was allocated for you. Use `--amend` only for an explicitly reviewed metadata amendment; this preserves the ID and surrounding prose. The Python plan/apply facade keeps the allocated ID and preview preconditions in one immutable plan.

For a new supported knowledge Markdown output, add `--kind` and `--title` (plus optional `--spec` / `--decision-supported`) to the same registration command. Its `local_path` must equal the selected knowledge kind directory plus `<updated_at>-<title-slug>.md`. New output, registry and owning issue backlink share the existing transaction; lifecycle/state/goal/loop/roadmap/dashboard are not advanced. Standalone legacy `--kind` creation retains its previous write behavior and reports `registered=false`.

Registration requires an existing valid issue and initialized transaction prerequisites, including configured `workspace/transactions/`. Initialize through the project's normal start/migration workflow; do not invent an issue or lifecycle state just to pass registration. Knowledge initialization alone creates the optional metadata files, not a transaction-ready project. It is missing-only and may report partial success; retry creates remaining files without overwriting existing text.

An existing original is linked, never copied, rewritten or uploaded. If registering a separately saved local/external document fails, keep that original and report **saved, unregistered**. A successful local registration does not mean committed/share-ready or approved. Legacy unstructured catalogs are preserved and diagnosed; review and curate them explicitly instead of automatically migrating whole folders or memory bodies.

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
