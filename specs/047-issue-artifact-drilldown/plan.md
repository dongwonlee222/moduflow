# Plan: Issue Artifact Drill-down Panel

Issue: `047-issue-artifact-drilldown`
Spec: `specs/047-issue-artifact-drilldown/spec.md` · Next: `product:execute 047`

## Architecture decision (reverses spec Alternatives #4 — see "Reversal" below)

Render the panel as a **self-contained HTML that loads two pinned CDN render libs client-side** — `marked` (Markdown→HTML) and `mermaid` (diagrams) — with Python doing **only collection + assembly**. Zero new Python dependency.

This is the same shape as the 042/044 dashboard (`render_dashboard_html`): Python emits an HTML skeleton + a JSON blob of data; a pinned CDN lib renders the dynamic part in the browser. It also renders inline when a visualization MCP is present, exactly like `dashboard.html`.

### Reversal of the spec's leaning (documented, not silent)

- Spec **Alternatives #4** rejected client-side `marked.js` to "keep the output a true static file with no runtime fetch."
- That rationale is already void: spec **Goal #4** requires Mermaid diagrams rendered *visually inside the panel*, which forces a client-side Mermaid CDN fetch regardless. So the spec's own anti-pattern (Python `markdown` text **+** CDN Mermaid) pays the dependency cost **and** the fetch cost while achieving neither's benefit.
- The two coherent endpoints are: **(A)** all-CDN (marked + Mermaid, zero Python dep) or **(B)** all-build-time-static (Python `markdown` + `mermaid-cli`/node). (A) reuses the proven 042 path; (B) adds a node dependency heavier than `markdown`.
- **Chosen: (A).** The benchmark evidence conclusion ("no JS library; Python markdown→HTML; Mermaid renders natively on GitHub/Obsidian") conflicts with Goal #4 (render *inside the panel*) — that was a latent contradiction. Resolved in favor of Goal #4. Will note this in the spec Alternatives + the benchmark evidence file.

## CDN pins (mirror the 042 style — explicit version, cdnjs/jsdelivr, no build step)

- `marked` 12.0.2 — `https://cdnjs.cloudflare.com/ajax/libs/marked/12.0.2/marked.min.js` (classic `<script src>`, same load style as Cytoscape 3.30.2 already in the dashboard).
- `mermaid` 11 — pinned ESM `import` from jsdelivr (`mermaid@11.x.x/dist/mermaid.esm.min.mjs`); pin the exact patch at implementation time. ESM differs from the classic Cytoscape `<script src>` — documented in code comment per spec Risk.

## Renderer

New function `render_issue_panel(root, issue_id)` in `scripts/project_memory.py`, alongside `render_dashboard_html`.

1. **Collect** artifacts for the issue, in this fixed order, including only files that exist:
   1. Issue header: `issues/<issue_id>.md` (status, goal, history) — the panel's top card.
   2. `specs/<issue_id>/spec.md`
   3. `specs/<issue_id>/plan.md`
   4. `specs/<issue_id>/tasks.md`
   5. `specs/<issue_id>/status.md`
   6. Then any remaining `specs/<issue_id>/*.md` not above (e.g. `design-brief.md`, `analysis.md`, `prototype.md`, `metrics.md`), sorted — so warranted-but-unlisted artifacts still appear.
   - `issue_id` accepts either the full slug (`047-issue-artifact-drilldown`) or a bare number (`047`); resolve number → folder/file by prefix match.
   - Mermaid diagrams need no separate collection step: they live as ```mermaid fences inside the above Markdown and render in place.
   - Linked `memory/` entries: **deferred** to a later cut (spec lists it "when present"; keep first cut to the issue's own `specs/` + issue file). Noted, not silently dropped.
2. **Assemble** one HTML string from a template: a JSON array `ARTIFACTS = [{name, label, md}]` (raw Markdown text, `json.dumps` escaped) + the two CDN tags. Client JS: for each artifact, `marked.parse(md)` → section; then convert `code.language-mermaid` blocks to `<div class="mermaid">` and call `mermaid.run()` on them.
3. **Graceful degrade**: no `specs/<issue_id>/` folder and no matching issue file → emit a panel that states "no artifacts yet for `<id>`" and links the issue file if it exists; never error.

## CLI + command surface

- Add `--issue <id>` flag to `project_memory.py` `main()` (next to `--dashboard`). Writes `memory/issue-<id>.html`, prints the path (same contract as `--dashboard`).
- Update `commands/product-dashboard.md`: document the `--issue <id>` mode — `python3 scripts/project_memory.py <project-path> --issue <id>` → reports `memory/issue-<id>.html`, renders inline if a viz MCP is present else points to the file. No new command (reuses 044 surface, per spec Goal #2).

## Derived-artifact policy

- `memory/issue-*.html` is derived → add to `.gitignore` next to `memory/dashboard.html`. Generator + command doc are the committed artifacts (mirrors 044).

## Test, review, deploy, rollback gates

- **Test** (`tests/test_project_memory.py`, extend): (a) present — `render_issue_panel(root, "046")` output contains the spec heading text and the pinned `marked`/`mermaid` URLs; (b) absent — a nonexistent issue id degrades to the "no artifacts" panel without raising; (c) number-vs-slug resolution returns the same artifacts.
- **Review**: `python3 scripts/release_check.py` (exit 0) — validate_moduflow, artifacts, lint, security, tests, doctor, doc checks.
- **Manual render check**: open a generated `memory/issue-046.html` in a browser; confirm Markdown renders and the spec's Mermaid flowchart appears as a diagram (release_check does NOT validate render — 046's fence-bug lesson).
- **Deploy**: commit generator + command doc + `.gitignore` + test; push via `github-evmodu` SSH alias.
- **Rollback**: the feature is additive (new function + new flag + gitignored output); revert the commit — no migration, no data change.

## Out of scope (confirmed from spec)

- Issue **graph** (→ 045); all-issues index; interactive editing; producing artifacts (→ 046); linked-memory embedding (deferred sub-cut).
