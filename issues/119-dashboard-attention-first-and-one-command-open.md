# Issue 119: Dashboard Attention-First Ordering and One-Command Open

**Status: backlog** — created 2026-09-05.
**Priority: p3**

## Summary

Two inbox items about actually using the dashboard: the issue DB buried the `active` status group mid-page, and generating the dashboard printed a path the user then had to go find.

## Source

- Type: user observation recorded in `workspace/inbox.md`
- Owner / decision maker: Dongwon Lee
- Date: 2026-07-06 (ordering), 2026-09-05 (opening)
- Link: `workspace/inbox.md`

## Opportunity

`groupedRows` in `scripts/project_memory.py` built status groups in row-encounter order. Under the default `created_desc` sort that means the newest issue's status leads, so a single new backlog issue pushed the `active` group below a screenful of `done` ones. The reporter could not find their own active issue 071 in the DB view. Recorded 2026-07-06 and still true on 2026-09-05.

Separately, `--dashboard` writes `memory/dashboard.html` and prints the path. `open-dashboard.command` exists but only works as a Finder double-click, so an agent or a terminal user generating the page has no way to open it in the same step. Generating a view nobody looks at is the step that gets skipped.

Both are small, user-reported, and verifiable by looking at the page.

## Scope

### In

- Fixed status group order in the issue DB: `active → review → blocked → backlog → done → superseded`, independent of the row sort.
- An unknown status keeps its encounter order after the known ones — never dropped, never promoted.
- Grouping by goal is untouched; only the status axis has a meaningful order.
- `--open` on `scripts/project_memory.py` to hand the generated page to the OS viewer after writing it.
- `--open` is best effort: a failure prints the reason and still exits 0, because the page was generated either way.
- Document both in `commands/product-dashboard.md`, and mark the handled inbox entries in place.

### Out

- Changing the row sort, the default view, or any filter.
- A new dashboard surface, tab, or layout.
- Replacing `open-dashboard.command`.
- Auto-opening on every `--dashboard` run. Opening a window is a side effect and stays opt-in.
- Portfolio or cross-project ordering, which belongs to `118-portfolio-mode-dashboard`.

## Acceptance Criteria

- With rows in an arbitrary order, the issue DB renders attention states first in the fixed sequence above.
- A status outside that sequence still renders, positioned after the known groups.
- Grouping by goal produces the same output as before this change.
- `--dashboard --open` writes the file and opens it; without `--open` behavior is unchanged.
- `--open` on a host with no opener prints why and exits 0.
- `python3 scripts/release_check.py .` passes.

## Verification

- `python3 -m unittest tests.test_dashboard_production_views tests.test_project_memory`
- `python3 scripts/release_check.py .`
- Browser check of the ordering against a probe row set, because marker assertions on generated JS cannot see behavior. This is the lesson from the dead-script defect found the same day (`specs/086-project-aware-production-library-dashboard/status.md`).

## Entry Points

- `scripts/project_memory.py`
- `commands/product-dashboard.md`
- `tests/test_dashboard_production_views.py`
- `workspace/inbox.md`

## Scope Fence

Do not restyle the issue DB, add a status, or change what counts as active. This issue changes the order groups are emitted in and adds one CLI flag.

## Workflow Tasks

- [x] execute → group ordering, `--open`, tests, docs, inbox marking

Executed directly from the inbox without a spec or plan: two contained changes to one file, both user-reported and verifiable by looking at the page. Recorded here rather than left as an unlinked commit.

## Related Issues

- blocks:
- blocked_by:
- duplicates:
- follows_up: `086-project-aware-production-library-dashboard`
- supersedes:
- related: `092-project-home-dashboard`, `118-portfolio-mode-dashboard`

## Links

- Inbox: `workspace/inbox.md`
- Goal: `workspace/goal.md`
- Roadmap: `workspace/roadmap.md`

## Next Command

`product:issue 119-dashboard-attention-first-and-one-command-open --transition complete`
