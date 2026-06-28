# Issue: `043-memory-relationship-capture-prompts`

**Status: done** — created 2026-06-28, started 2026-06-28, done 2026-06-28. Part of goal `visual-workbench`, Axis B (data quality). Makes recording the `issue_id`/relationship cross-links that `045` surfaced easy and habitual at write time.

## Outcome

Relationship capture is now **guided, not inferred** — no new schema (the fields already existed), just the affordances to use them:

- **`--list-ids`** flag (`project_memory.py`, `list_memory_ids`) — lists existing memory `id`/`kind`/`title` (optional `--kind`) as link candidates, so authors link to *real* nodes. Reuses `search_memory_entries(query="")`.
- **Command-doc guidance** (`product-memory.md`, `product-knowledge.md`) — a "capture relationships at write time" step: list ids → pass content-verified `--supersedes/--depends-on/--references` + `--issue-id`. States plainly: present options, never auto-link (042's anti-goal). Verified relationships survive `--approve`.
- **`project_doctor` soft hint** (`isolated_memory_entries`) — surfaces entries with no relationships and no `issue_id` as an informational nudge; **never an error** (exit 0 preserved, release_check safe).

Tests: 32 pass (list-ids all/filter, isolated flagging, doctor hint without failing). `release_check` exit 0. No auto-inference anywhere.

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
