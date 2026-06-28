---
description: Generate the interactive decision-graph dashboard from project memory and report its path.
argument-hint: "[project path]"
---

# /product:dashboard

Render the project's memory artifacts (decisions, evidence, deliverables) as an interactive **decision graph** — nodes plus relationship edges — in a self-contained HTML file.

This is a ModuFlow-native command, not a Claude-client-only skill: it ships with the plugin so anyone who installs ModuFlow can invoke it. The canonical artifacts stay the Git-tracked Markdown in `memory/`; this dashboard is a derived, rebuildable lens over them.

## Do

1. Generate the dashboard from current memory frontmatter:

```bash
python3 scripts/project_memory.py <project-path> --dashboard
```

2. Report the output path: `memory/dashboard.html`.

3. Surface it for the user:
   - **If a visualization MCP is available** (e.g. the Claude client), also render the graph inline in chat so the user sees it without leaving the conversation.
   - **Otherwise**, tell the user to open `memory/dashboard.html` (on macOS, `open-dashboard.command` double-click works). The core behavior must work with **no MCP** — generate the file and point to it.

## Rules

- `memory/*.md` is the source of truth; `dashboard.html` is a derived view, regenerated on every run. It is `.gitignore`d — the generator (`scripts/project_memory.py`) is the committed artifact, not the snapshot.
- The graph reads relationships from memory frontmatter (`references`, `supersedes`, `evidence`, `source_artifacts`). To enrich the graph, add those fields to memory records, not to the HTML.
- This shows the **decision/memory graph**, distinct from `workspace/dashboard.md` (the progress dashboard) and the `progress-dashboard` skill.

## Next

- `/product:memory --search` to inspect a node's underlying record
- `/product:evidence` to review related memory and evidence
