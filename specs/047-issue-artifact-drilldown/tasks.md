# Tasks: Issue Artifact Drill-down Panel

Issue: `047-issue-artifact-drilldown`
Plan: `specs/047-issue-artifact-drilldown/plan.md`

## Stream 1 — Renderer (core)

- [ ] T1. Add `ISSUE_PANEL_TEMPLATE` (HTML skeleton + pinned `marked` `<script>` + `mermaid` ESM import + client JS that `marked.parse`es each artifact and runs `mermaid` on `language-mermaid` blocks).
- [ ] T2. Add `_collect_issue_artifacts(root, issue_id)` — resolve number↔slug, gather `issues/<id>.md` + `specs/<id>/{spec,plan,tasks,status}.md` + remaining `specs/<id>/*.md` (sorted), return ordered `[{name,label,md}]` of existing files only.
- [ ] T3. Add `render_issue_panel(root, issue_id)` — assemble template with `json.dumps(artifacts)`; graceful "no artifacts" panel when nothing found.

## Stream 2 — CLI + command surface

- [ ] T4. Add `--issue <id>` flag in `main()`; write `memory/issue-<id>.html`, print path (mirror `--dashboard`).
- [ ] T5. Update `commands/product-dashboard.md` to document the `--issue <id>` mode.
- [ ] T6. Add `memory/issue-*.html` to `.gitignore`.

## Stream 3 — Tests + verification (gate)

- [ ] T7. Extend `tests/test_project_memory.py`: present (046) contains spec heading + pinned CDN URLs; absent degrades gracefully; number-vs-slug parity.
- [ ] T8. Run `python3 -m unittest tests.test_project_memory` → all pass.
- [ ] T9. Generate `memory/issue-046.html`, open in browser → Markdown + Mermaid render visually (manual; release_check doesn't cover render).
- [ ] T10. `python3 scripts/release_check.py` → exit 0.

## Stream 4 — Close-out

- [ ] T11. Update spec Alternatives #4 + benchmark evidence with the reversal note.
- [ ] T12. Commit (generator + command + .gitignore + test + spec/plan/tasks) + push via `github-evmodu`; mark issue 047 done; resync state.json + dashboard.md.
