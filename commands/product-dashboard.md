---
description: Generate the interactive project view (issue DB + issue graph + memory graph) and report its path.
argument-hint: "[project path]"
---

# /product:dashboard

Render the project as an interactive **project workbench** in one self-contained HTML file:

- **이슈 DB (issue database/list)** — default view; searchable/filterable/sortable issue table with artifact coverage, next command, flags, and linked-memory counts.
- **이슈 그래프 (issue graph)** — nodes = issues, color = status (done / active / backlog / blocked / review / superseded), edges = `supersedes` and scoped related links.
- **지식 그래프 (memory graph)** — decisions / evidence / deliverables with relationship edges (the original 042 graph).

The issue and memory graphs are **cross-linked** via `memory.issue_id`: an issue node click opens its artifact panel (`--issue` below); the info box previews the issue's linked memory (badge `🧠N`, toggleable); a memory node links back to its source issue. A tab **is** the standalone view — open the table or a graph via the `#issue-db` / `#issues` / `#memory` URL hash.

This is a ModuFlow-native command, not a Claude-client-only skill: it ships with the plugin so anyone who installs ModuFlow can invoke it. The canonical artifacts stay the Git-tracked Markdown in `issues/`, `specs/`, and `memory/`; this view is a derived, rebuildable lens over them.

## Do

1. Generate the project view from current issues + memory frontmatter:

```bash
python3 scripts/project_memory.py <project-path> --dashboard
```

2. Report the output path: `memory/dashboard.html`.

3. Surface it for the user:
   - **If a visualization MCP is available** (e.g. the Claude client), also render the view inline in chat so the user sees it without leaving the conversation.
   - **Otherwise**, tell the user to open `memory/dashboard.html` (on macOS, `open-dashboard.command` double-click works). The core behavior must work with **no MCP** — generate the file and point to it.

## Issue drill-down mode (`--issue <id>`)

To inspect **one issue's** planning artifacts (spec, plan, tasks, status, and any warranted design-brief/analysis) in a single L2 panel — the "추후 문제가 생기면 사람이 산출물 확인" surface:

```bash
python3 scripts/project_memory.py <project-path> --issue <id>
```

- `<id>` accepts a bare number (`047`) or the full slug (`047-issue-artifact-drilldown`).
- Reports the output path `memory/issue-<id>.html`; surface it the same way as the dashboard (inline if a viz MCP is present, else point to the file).
- Renders **only artifacts that exist** — never forces empty sections. Markdown renders via pinned `marked`, Mermaid diagrams render visually via pinned `mermaid` (both CDN, zero backend). An issue with no `specs/<id>/` folder degrades to a "no artifacts yet" panel.
- Also appends a **연결된 지식** section listing the issue's `issue_id`-linked memory (omitted when none — the cross-link the issue-graph node click leads into).
- `memory/issue-*.html` is derived/`.gitignore`d, like `dashboard.html`.

## Rules

- `issues/*.md` + `memory/*.md` are the source of truth; `dashboard.html` is a derived view, regenerated on every run. It is `.gitignore`d — the generator (`scripts/project_memory.py`) is the committed artifact, not the snapshot.
- The issue graph reads status + `supersedes` from issue files (text parse, no frontmatter added). The memory graph reads relationships from memory frontmatter (`references`, `supersedes`, `depends_on`, `issue_id`). To enrich either graph, edit the canonical Markdown, not the HTML. Cross-links come from `memory.issue_id` — sparse until `043` lands.
- This shows the **issue DB + issue graph + memory graph** (L1 project view), distinct from `workspace/dashboard.md` (the progress dashboard) and the `progress-dashboard` skill.

## Next

- `/product:memory --search` to inspect a node's underlying record
- `/product:evidence` to review related memory and evidence
