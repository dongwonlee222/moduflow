# Issue: `041-decision-graph-native-mermaid-rendering`

**Status: superseded-by-042** — created 2026-06-27, superseded 2026-06-28. The static-Mermaid hardening here was absorbed into `042-decision-graph-dashboard`, which renders an interactive Cytoscape dashboard instead. The edge-extraction logic this issue scoped now lives in `_collect_graph` (`scripts/project_memory.py`). The Mermaid `--graph` output still works and carries the same supersedes/depends_on edge conventions.

## Goal

Improve the intuitiveness of ModuFlow's chat-only visualization by hardening issue-037's decision-graph Mermaid output so it renders natively in GitHub and Obsidian — a zero-code win that reuses an external renderer without adding a web stack.

## Decision (spine)

External visualization splits into two mechanisms that must be handled differently:

- **skill-vendorable** (Mermaid, visualization MCP/skill): can be vendored via `source-adapter-policy` (`vendor/`/`overlays/`/`adapters/`).
- **code-dependency** (React Flow, Rete, Rivet — JS libraries): NOT skill artifacts, NOT `source-adapter-policy` targets. They enter only as npm dependencies of a separate dashboard app.

→ ModuFlow path is **Mermaid-first**, consistent with its Git-native, lightweight, zero-render-cost philosophy. Full landscape and star counts: see `docs/dashboard-visualization-research.md`.

## Scope

- Emit decision-graph as fenced ` ```mermaid ` blocks in `.ai-os`/`memory/index.md` (or `decisions-index.md`) so GitHub and Obsidian render it inline with no extra tooling.
- Carry over the 037 edge conventions (supersedes solid / depends_on dashed) into the rendered output.
- Verify the rendered graph displays correctly in both GitHub Markdown preview and Obsidian.

## Out of Scope (revisit only when chat-only viz is proven the real bottleneck)

- Interactive React Flow / web dashboard (separate deliverable, code-dependency — not this issue).
- Visualization MCP/skill adapter vendoring (the step-2 option; track separately if pursued).

## Workflow Tasks

- [ ] spec -> define native-render output format and acceptance (GitHub + Obsidian)
- [ ] plan -> implementation plan for Mermaid emission in index files
- [ ] execute -> code changes in `scripts/project_memory.py` graph output
- [ ] review -> verify render in GitHub preview and Obsidian
- [ ] release -> confirm and document

## Related Issues

- `037-delegation-level-gate-and-memory-context-graph` (Foundation — produces the Mermaid graph this hardens)
- `036-portfolio-team-dashboard` (Related — broader dashboard surface)

## Related Artifacts

- `docs/dashboard-visualization-research.md` (node-based visual programming landscape + decision rationale)
