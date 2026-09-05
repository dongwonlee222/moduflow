# Issue 118: Portfolio-Mode Dashboard

**Status: backlog** — created 2026-09-05.
**Priority: p2**
**Blocked-by: `086-project-aware-production-library-dashboard`**

## Summary

Own the cross-project half of the dashboard that Issue 086 deferred on 2026-09-05: portfolio-mode collection from `projects.json`, the `전체 프로젝트` (All Projects) summary view, the `all` selector state, and the trusted cross-project link resolver that Issue 086's spec requires but that no code provides.

## Source

- Type: approved scope deferral from Issue 086
- Owner / decision maker: Dongwon Lee
- Date: 2026-09-05
- Link: `specs/086-project-aware-production-library-dashboard/spec.md` § "Amendment — 2026-09-05" (Korean: `spec.ko.md` § "개정 — 2026-09-05")

## Opportunity

Issue 086's approved plan turned out to exclude portfolio mode without saying so. `specs/086-project-aware-production-library-dashboard/plan.md:24` states as a global constraint that there is "no page that mixes two projects' records in one payload"; its contract table exposes only single-project entry points (`_collect_production_records(root, ...)`, `_collect_playbooks(root, ...)`, `render_project_view(root, ...)`); and its file map contains no portfolio collector. Yet the same plan's coverage table maps AC3-AC7 to tasks C1/C2, claiming coverage for a summary view that has nothing behind it. The contradiction was found on 2026-09-05 and resolved by deferring the cross-project scope here rather than by weakening the constraint.

Two further inputs made this a separate deliverable rather than a leftover task:

- `workspace/roadmap.md`, "086/092 — lightweight projections": "A hidden tab is not a privacy boundary: do not bundle private records from every project into a single portfolio HTML payload." That governance decision postdates Issue 086's spec and converts the `All Projects` restraint from a rendering rule into a collection-design requirement.
- `specs/086-.../spec.md:240` had explicitly left it to the plan to decide "whether portfolio generation embeds project details eagerly or generates linked per-project detail files". The plan never answered. The amendment settles it as **linked per-project generation**, which is the constraint this issue implements.

Issue 092 is not the right home: `issues/092-project-home-dashboard.md:47` lists "Cross-project detail views without explicit project selection" as out of scope. Issues 004 and 036 are done. Meanwhile the capability is not lost — `scripts/project_portfolio.py:262` `write_dashboard()` already emits a Markdown `portfolio-dashboard.md` portfolio summary, so this issue adds the HTML surface rather than the first portfolio view.

## Scope

### In

- Portfolio-mode collection: read portfolio `projects.json` (`moduflow.projects.v1`) and collect a bounded summary snapshot per explicitly registered project root.
- The `전체 프로젝트` summary view: per-project issue counts by state, production-record counts by lifecycle, playbook candidate / review-due counts, validation-warning counts, blocker and next command.
- The `all` selector state (`selectedProjectId=all`): a distinct summary state that disables project-detail links and project actions until a concrete project is chosen.
- The trusted cross-project link resolver required by `specs/086-.../spec.md:137` (links generated from trusted registered roots, never concatenated from browser input) and by the "Cross-project links" risk at `specs/086-.../spec.md:235`. It does not exist today.
- Per-entry warnings for a registered project that is missing, unreadable or malformed, without aborting the other projects.
- Enforce the settled generation strategy structurally: the portfolio artifact carries counts, attention states and links only, and links out to each project's own generated dashboard. No record body, internal reporting copy, decision text or memory content enters a portfolio payload.
- Decide and document the portfolio HTML output location and the CLI arguments that produce it. Both are undecided today.

### Out

- Anything Issue 086 keeps: the single-project dashboard, its five tabs, the project selector for one project, and `?project=<id>` restoration to one registered project.
- Merged cross-project search, or any view that renders two projects' record bodies together. The privacy boundary is the payload, not the tab.
- Browser-side Git writes, a hosted database, or a runtime server.
- Filesystem discovery of projects. Only explicitly registered portfolio entries are trusted.
- A second registry parser or project resolver. Consume `102-project-registry-and-resolver` and the existing `scripts/project_portfolio.py`.
- Replacing the existing Markdown `portfolio-dashboard.md` output.
- Analysis runs from Issue 091, which belong to Issue 092.

## Acceptance Criteria

- Portfolio mode reads `moduflow.projects.v1` and renders every valid registered project, plus a visible per-entry warning for every invalid one, without aborting the render. (Issue 086 AC2, deferred here.)
- `전체 프로젝트` renders summary counts and attention states only, and requires a concrete project before any record detail or project action. (Issue 086 AC7, deferred here.)
- No portfolio payload contains a production-record body, internal reporting copy, a full decision, or memory content for any project. This is asserted by inspecting the generated payload, not by trusting a view.
- Selecting a project row leaves the `all` state and enters that project's concrete context.
- All generated links resolve through one resolver seeded from registered roots, with fixtures for project-relative, project-dashboard and external-URL cases. No link is built by string-concatenating browser input.
- The single-project dashboard Issue 086 delivers is unchanged by this work, proven by generated-output equivalence before and after.
- The portfolio HTML output location and CLI arguments are documented in `commands/product-portfolio.md` or `commands/product-dashboard.md`, whichever this issue's spec selects.
- `python3 scripts/release_check.py .` passes.

## Verification

- `python3 -m unittest tests.test_project_memory tests.test_dashboard_production_views -v`
- `python3 -m unittest discover -s tests -v`
- `python3 scripts/validate_project_artifacts.py .`
- `python3 scripts/release_check.py .`
- Playwright desktop/mobile screenshots of the `전체 프로젝트` summary and of a row selection entering a concrete project

## Entry Points

- `scripts/project_memory.py`
- `scripts/project_portfolio.py`
- `scripts/project_registry.py`
- `commands/product-portfolio.md`
- `commands/product-dashboard.md`
- `tests/test_project_memory.py`
- `specs/086-project-aware-production-library-dashboard/spec.md` § "Amendment — 2026-09-05"

## Known Hazards

Carried over on 2026-09-05 from inspection of the current renderer. A naive portfolio implementation will hit all three.

- **The two Cytoscape instances are constructed once at page load.** `scripts/project_memory.py` builds `cyIssues` (~line 1632) and `cyMemory` (~line 1651) at load time from `ISSUE_ELEMENTS` / `MEMORY_ELEMENTS`, and `activeNodes` is computed once from `cyIssues` immediately afterwards (~line 1679) and closed over by the later focus/animate code (~lines 2040-2042). Switching projects therefore cannot simply re-point a data variable: either the elements are replaced and `activeNodes` recomputed, or the instances are rebuilt. This is the single most likely place for a project switch to silently keep the previous project's graph.
- **Per-issue drilldown files collide across projects.** `--dashboard` writes `issue-<id>.html` (and `mem-<id>.html`) into each project's own `memory/` directory (~lines 2677-2686). Two projects both having an issue `001` produce the same filename. A portfolio artifact that links to drilldowns must resolve them per project root, and must not flatten them into one output directory.
- **Portfolio HTML output location and CLI arguments are undecided.** `write_dashboard()` in `scripts/project_portfolio.py` writes Markdown to the portfolio root; `project_memory.py --dashboard` writes HTML into a project's `memory/`. Neither is obviously right for a portfolio HTML file, and this issue's spec must choose rather than inherit.

## Scope Fence

Do not weaken Issue 086's payload constraint to make this easier. If a portfolio view needs a project's detail, it links to that project's own generated dashboard; it does not embed the detail. Do not add a second registry parser, a second project resolver, or a second production/playbook parser.

## Workflow Tasks

- [ ] spec → `specs/118-portfolio-mode-dashboard/spec.md` (+ `spec.ko.md`)
- [ ] design → `specs/118-portfolio-mode-dashboard/design.md`
- [ ] plan → `specs/118-portfolio-mode-dashboard/plan.md` + `tasks.md` with declared file boundaries
- [ ] execute → portfolio collection, summary view, `all` state, link resolver, and tests
- [ ] review → `specs/118-portfolio-mode-dashboard/review.md`

## Related Issues

- blocks:
- blocked_by: `086-project-aware-production-library-dashboard`
- duplicates:
- follows_up: `004-portfolio-workspace`, `036-portfolio-team-dashboard`
- supersedes:
- related: `092-project-home-dashboard`, `102-project-registry-and-resolver`, `085-project-production-records-and-playbooks`, `115-playbook-process-and-checklist-extension`

## Links

- Deferred from: `issues/086-project-aware-production-library-dashboard.md`
- Amendment: `specs/086-project-aware-production-library-dashboard/spec.md` § "Amendment — 2026-09-05"
- Goal: `workspace/goal.md`
- Roadmap: `workspace/roadmap.md`

## Next Command

After Issue 086 is done: `product:spec 118-portfolio-mode-dashboard`.
