# ModuFlow Inbox

## 2026-06-11

- [handled] Multi-project users need project-local issue management, environment information, dashboards, knowledge artifacts, decisions, migration support, and portfolio views.

- [handled 2026-09-05] 2026-07-06 (user observation): dashboard issue DB buries the `active` status group mid-page under default sort (created_desc) because group order follows row-encounter order. Active group should always render first (active → review → blocked → backlog → done). Small UI fix in project_memory.py groupedRows/status ordering. Source: user couldn't find active issue 071 in the DB view.

## Handled

- 2026-09-05: the `active` group ordering fix landed in `groupedRows`
  (`scripts/project_memory.py`). Verified in a browser, not only by markers.
- 2026-09-05: the 2026-06-11 multi-project note is covered by Issues 102
  (registry/resolver), 086 (project-aware dashboard), 004/036 (portfolio
  workspace and summary) and 118 (portfolio-mode dashboard). Entries are
  marked in place rather than removed so the original wording survives.
