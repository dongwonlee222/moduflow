# Issue: `043-memory-relationship-capture-prompts`

**Status: backlog** — created 2026-06-28. Not active; `active_issue` remains 042. Activate later with `product:issue 043 start`.

## Goal

Grow the decision graph reliably by capturing memory relationships **at write time**, instead of backfilling guessed edges later. This is the principled way to make the 042 dashboard richer.

## Decision (spine)

The graph is only as good as the `supersedes`/`depends_on`/`references` in frontmatter. Relationships must be **content-verified**, so the right moment to capture them is when the author writes or approves a memory entry — not as an after-the-fact guess. Guessed edges (e.g. "same issue, similar topic") pollute trust: later you can't tell a real rationale link from a hunch. 042 deliberately refused to auto-infer edges; this issue makes the *real* edges easy to record.

## Scope

- `create_memory_entry` / candidate capture / `product-knowledge`: prompt for `supersedes` / `depends_on` / `references` at entry time.
- Suggest existing memory ids as options (author links to real nodes, not free-typed strings that won't match).
- `doctor`/validation: optionally surface isolated nodes as a soft hint (not an error) so gaps are visible without forcing fake links.

## Out of Scope

- Auto-inferring relationships from content — the exact thing 042 refused to do.
- `fcose` layout swap (separate small follow-up).
- Portfolio-level multi-project dashboard (separate).

## Related Issues

- `042-decision-graph-dashboard` (the dashboard this feeds)
- `034-memory-capture-and-sync-workflow` (candidate capture / approval path)
- `030-project-memory-layer` (memory write path)

## Backlog Notes (sibling follow-ups, not this issue)

- `fcose` Cytoscape layout for cleaner disconnected-node spread (CDN one-liner).
- Portfolio dashboard: apply the same graph across multiple project memories.
