# Issue: `044-product-dashboard-command`

**Status: done** — created 2026-06-28, completed 2026-06-28. Part of goal `visual-workbench`.

## Outcome

Shipped `product:dashboard` as a ModuFlow-native command:
- `commands/product-dashboard.md` — runs `project_memory.py --dashboard`, reports `memory/dashboard.html`, renders inline when a visualization MCP is present, else points to the file (works with zero MCP).
- Routing in both `commands/moduflow.md` (`그래프`/`graph` alias) and `skills/index/SKILL.md` (Command Map + Short Alias Map + natural-language example + trigger keyword), so bot/at-mention routing reaches it too.
- Artifact policy decided: `memory/dashboard.html` is `.gitignore`d (derived, rebuildable); the generator is the committed artifact. Aligned with the Git-canonical-memory decision.
- `open-dashboard.command` already shipped (042) as the macOS double-click convenience.

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
