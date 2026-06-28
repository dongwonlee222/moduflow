# Plan: Project View — Issue Graph + Memory Graph (cross-linked)

Issue: `045-issue-graph-visualization`
Spec: `specs/045-issue-graph-visualization/spec.md` · Next: `product:execute 045`

## CLI / file structure decision

- **Keep `render_dashboard_html(root)` untouched** — 042's `test_render_dashboard_html_embeds_graph` calls it directly and pins `cytoscape.min.js` / `const ELEMENTS =` / `depends_on`. Preserving it keeps that test green and lets the project view reuse the memory-graph elements.
- **New `render_project_view(root)`** builds the two-tab HTML, embedding **both** the memory-graph elements (via the same `_collect_graph`) and the issue-graph elements (new `_collect_issue_graph`).
- **`--dashboard` evolves to emit the project view** at the same path `memory/dashboard.html` (filename unchanged, so 044's command + `.gitignore` entry still hold; internals become two-tab). The standalone memory graph remains reachable as the 지식 tab (`#memory`).
- Update `commands/product-dashboard.md`: dashboard.html is now the two-tab **project view** (issue + memory), `--issue <id>` unchanged.

## Collectors

- `_collect_issue_graph(root)` — scan `issues/*.md`:
  - `id` = filename stem (`045-issue-graph-visualization`); short label = id + H1 title (truncate).
  - `status` from the `**Status:** <word>` line → bucket: `done` / `active` / `backlog` / `superseded` (anything `superseded*` / `superseded-by-NNN`). Color per bucket.
  - `supersedes` edges: from `superseded-by-NNN` (this → NNN, reversed to NNN supersedes this) **and** `Supersedes \`NNN\`` prose (this supersedes NNN). Emit one `supersedes` edge per resolved pair; skip targets that aren't real issue files.
  - **No `## Related Issues` prose edges in this cut** (noisy) — leave a `# TODO(045): scoped related edges` marker, don't parse them yet.
  - Return `nodes` (id→{title,status}) + `edges` ([(src,tgt,'supersedes')]).
- `_issue_linked_memory(root)` — read `memory/*.md` frontmatter `issue_id` (reuse existing frontmatter parse); return `{issue_id: [{id,title,kind}]}`. Sparse is fine (5/8). Used for badge count, click preview, and the 047 panel section.

## Renderer — two-tab project view

`PROJECT_VIEW_TEMPLATE`: one self-contained HTML, Korean UI.
- Two pinned `cytoscape` containers (`#cy-issues`, `#cy-memory`), one visible at a time.
- Tab bar `[이슈 그래프] [지식 그래프]` + badge toggle `🧠 배지 표시`. Default tab = issues. On load, honor URL hash `#issues`/`#memory`; update hash on tab switch (bookmarkable).
- Issue nodes colored by status (done/active/backlog/superseded); reuse the 042 edge styling. Memory tab embeds the existing `_collect_graph` elements with the 042 styling (visual parity with the standalone dashboard).
- **Layer 1 badge**: issue node label shows `🧠N` when linked-memory count > 0; toggle hides/shows it (re-render label). Omit when 0.
- **Layer 2 preview**: `cy.on('tap','node')` on the issue graph → info box lists linked memory with kind icons (💡decision 📎evidence 📦deliverable) in Korean; each entry is a link that switches to the 지식 tab and selects that memory node. Issue node also shows a `상세 열기` link → `issue-<id>.html`.
- Memory node tap (지식 tab) → info box; if the entry has `issue_id`, show `출처 이슈: <id>` linking to the issue tab + that node.
- Help text in Korean, matching 042 ("노드를 클릭하면…").

## 047 panel — un-defer linked memory (cross-link layer 3)

- Extend `_collect_issue_artifacts` (or `render_issue_panel`) to append a **"연결된 지식"** section listing `_issue_linked_memory(root)[slug]` entries (title + path link + kind icon). Omit the section when none (selective, consistent with 047). This is the deferred cut from 047, now in scope.

## Tasks / gates

- **Test** (`tests/test_project_memory.py`): (a) `_collect_issue_graph` parses status buckets + a `supersedes` edge from the real-style status line; (b) `_issue_linked_memory` maps `issue_id`→entries and tolerates the empty/missing case; (c) `render_project_view` contains both `#cy-issues` and `#cy-memory` and the Korean tab labels; (d) 047 panel includes the "연결된 지식" section when a linked memory exists, omits it otherwise.
- **Run** `python3 -m unittest tests.test_project_memory` → all pass (incl. the untouched 042 test).
- **Manual render**: generate `memory/dashboard.html`, open → tab switch works, issue graph colored, node click shows preview + opens 047 panel; **and** confirm the 047 panel's marked+mermaid render visually (spec AC #7; the still-open browser file, or visualize MCP).
- **Review**: `python3 scripts/release_check.py` exit 0.
- **Deploy**: commit (collectors + renderer + 047 section + command doc + tests + spec/plan/tasks) + push via `github-evmodu`.
- **Rollback**: additive (new functions + evolved `--dashboard` output); revert commit — no data/schema change. `render_dashboard_html` preserved as fallback generator.

## Out of scope (confirmed)

- `## Related Issues` dense edges (later, scoped/toggleable); issue-file frontmatter (024); interactive editing; translating artifact bodies.
