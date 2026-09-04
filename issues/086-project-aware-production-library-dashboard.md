# Issue 086: Project-Aware Production Library Dashboard

**Status: backlog** — created 2026-07-10; spec, design, and prototype completed 2026-07-10. Execution not started.
**Priority: p2**
**Blocked-by: `102-project-registry-and-resolver`**

## Summary

Extend the existing ModuFlow dashboard with a global project selector and project-scoped production library/playbook views, so one selected project consistently controls issues, production knowledge, memory, decisions, roadmap, and status across every dashboard tab.

## Source

- Type: user product direction / approved UX concept
- Link: local Codex session and dashboard visualization, 2026-07-10
- Owner / decision maker: Dongwon Lee
- Date: 2026-07-10

## Opportunity

Production records are only useful when people can see what is registered, search past failures and patterns, and open final artifacts without knowing repository paths. Because every project has different folders and brand knowledge, project selection must be a global dashboard context rather than a filter attached only to the production tab.

## Product Decision

Reuse and extend the existing generated ModuFlow dashboard instead of creating a separate application. A single global project selector controls all tabs. Each selected project's canonical Production Records provide registered artifact links, so the dashboard never crawls arbitrary project folders.

## Scope

### In

- Add a global project selector to the dashboard header using registered ModuFlow projects as its source.
- Apply the selected project root consistently to Issue DB, issue graph, production records, playbooks, memory/knowledge graph, decisions, roadmap, goal, status, and next action.
- Add `Production Records` and `Playbooks` tabs beside the existing issue and knowledge views.
- Production list supports search and filters for deliverable type, channel, audience, lifecycle state, and playbook promotion state.
- A record detail view shows final artifacts, source inputs, decisions, failed attempts, reusable patterns, `Do Not Repeat`, playbook updates, external copy, and internal reporting copy.
- Persist selected project and active tab in the URL so refreshes and shared links reopen the same context.
- Provide an `All Projects` portfolio summary, but require one project selection before opening detailed records or performing project-specific actions.
- Keep the initial dashboard read-oriented and Git-derived; registration/editing remains through ModuFlow natural language or commands.
- Preserve existing project-local dashboard generation for users with only one configured project.

### Out

- Direct browser write-back to Git in v1.
- A hosted central database or mandatory runtime server.
- Cross-project merging of records/playbooks.
- Scanning every arbitrary folder for unregistered assets.
- Replacing existing Issue DB, issue graph, knowledge graph, or drill-down views.

## Acceptance Criteria

- Changing the project selector changes every dashboard tab to the same project, with no mixed-project detail state.
- The project selection survives refresh and can be represented in a shareable URL.
- Production Records lists only the selected project's registered records and opens a complete detail view.
- Playbooks lists only human-approved playbooks for the selected project and links back to source records.
- Projects may keep final assets in different folders or external tools; the dashboard renders their registered metadata and links consistently.
- `All Projects` shows portfolio-level counts/attention states only; a user must choose a project before opening a record or executing an action.
- Existing single-project dashboards work without requiring portfolio setup.
- Responsive visual review covers desktop and mobile without overlapping controls or clipped text.
- Existing dashboard/memory tests and `python3 scripts/release_check.py .` pass.

## Verification

Commands the executing agent runs to self-check before handing off.

- `python3 -m unittest tests.test_project_memory -v`
- `python3 scripts/project_memory.py . --dashboard`
- `python3 scripts/validate_project_artifacts.py .`
- `python3 scripts/release_check.py .`
- Playwright desktop/mobile screenshots of project selection, record list, record detail, and playbook view

## Entry Points

Starting files/components for the executing agent.

- `scripts/project_memory.py`
- `commands/product-dashboard.md`
- `commands/product-portfolio.md`
- `templates/portfolio/`
- `tests/test_project_memory.py`
- `specs/056-dashboard-database-list-view/`
- `specs/047-issue-artifact-drilldown/`

## Scope Fence

Do NOT introduce browser-side Git mutation or an external database in v1. Do not let one tab keep a stale project while another tab uses the current global selection.

## Workflow Tasks

Every artifact-producing step is a tracked task here — never produce a spec, plan, design, prototype, or review off the books. Check the box and link the artifact when done.

- [x] spec → `specs/086-project-aware-production-library-dashboard/spec.md` (+ `spec.ko.md`)
- [x] design → `specs/086-project-aware-production-library-dashboard/design.md` (+ `design.ko.md`)
- [x] prototype → `specs/086-project-aware-production-library-dashboard/prototype.md` + `prototype.html`
- [ ] plan → pending `product:plan 086-project-aware-production-library-dashboard`
- [ ] execute → project selector, production views, URL state, responsive UI, and tests
- [ ] review → pending `product:review 086-project-aware-production-library-dashboard`

## Related Issues

- blocks:
- blocked_by: `102-project-registry-and-resolver`
- duplicates:
- follows_up: `056-dashboard-database-list-view`, `047-issue-artifact-drilldown`
- supersedes:
- related: `004-portfolio-workspace`, `036-portfolio-team-dashboard`, `042-decision-graph-dashboard`, `045-issue-graph-visualization`, `115-playbook-process-and-checklist-extension`

## Playbook Extension Note — 2026-09-03

[Issue 115](115-playbook-process-and-checklist-extension.md) adds two optional elements to `moduflow.playbook.v1`: an external `process_ref` and a numbered, human-owned `Required Checks` checklist. This issue was written before they existed. The playbook tab must render the two new elements read-only, and must not mark, complete or evaluate a checklist item. Reconciled 2026-09-04. `spec.md` gained AC 10a-10c and `design.md` gained the playbook column set, the three-state production record treatment, and the analysis-run scope boundary. The July prototype shows the target visual language but predates Issue 115, so treat this design as the current reference.

## Sessions

- 2026-07-10: User approved a production library/playbook dashboard concept.
- 2026-07-10: User decided the top project selector must control issue, production, knowledge, and status views globally.
- 2026-07-10: User approved preserving the existing ModuFlow UI and opening Production Record details in a dimmed modal.
- 2026-07-10: Corrected Issue 086 from backlog to active so the existing issue graph current-work focus remains functional.
- 2026-07-26: Restored to backlog after the branch artifacts were merged into `main`. Only one issue may be active at a time (`project_lifecycle.py` reports multiple active issues as drift), and `095-commit-issue-resolution-parity` takes priority as p1. Design and prototype artifacts remain in `main`; nothing is lost.

## Links

- Spec: `specs/086-project-aware-production-library-dashboard/spec.md`
- Design: `specs/086-project-aware-production-library-dashboard/design.md`
- Prototype: `specs/086-project-aware-production-library-dashboard/prototype.md`
- Status: `specs/086-project-aware-production-library-dashboard/status.md`
- Sessions: `sessions/086-project-aware-production-library-dashboard/`
- Roadmap: `workspace/roadmap.md`
- GitHub: https://github.com/dongwonlee222/moduflow/issues/27

## Next Command

After Issue 102 is done: `product:plan 086-project-aware-production-library-dashboard`.
