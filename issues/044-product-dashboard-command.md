# Issue: `044-product-dashboard-command`

**Status: backlog** — created 2026-06-28. Part of goal `visual-workbench`. Not active until started.

## Goal

Expose the decision-graph dashboard as a **ModuFlow-native command**, not a Claude-only global skill. Anyone who installs ModuFlow should be able to invoke it; it must live in the plugin and ship via GitHub.

## Decision (spine)

A Claude global skill (`~/.claude/skills/`) is wrong here: it exists only in one user's environment and is never distributed. The dashboard belongs in the ModuFlow plugin so it's versioned, shared, and consistent with the `/moduflow` hub.

## Scope

- Add `product:dashboard` (and `/moduflow 그래프` routing) that runs `project_memory.py --dashboard` and reports the `memory/dashboard.html` path.
- When a visualization MCP is available (e.g. Claude client), also render the graph inline in chat; otherwise just generate the file and tell the user to open it. Core behavior must work with no MCP (generate + open).
- Decide `dashboard.html` artifact policy: it is generated and re-dirties on every run → `.gitignore` it and treat the generator as the artifact (recommended), or commit snapshots.
- Optionally ship `open-dashboard.command` as a repo-local convenience (macOS double-click).

## Out of Scope

- Issue graph (→ `045`).
- Interactive authoring/execution (later goal stage).

## Related

- Goal `visual-workbench`
- `042-decision-graph-dashboard` (the generator this exposes)
- `progress-dashboard` skill, `/moduflow` hub (where it routes)
