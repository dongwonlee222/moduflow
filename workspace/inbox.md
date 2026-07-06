# ModuFlow Inbox

## 2026-06-11

- Multi-project users need project-local issue management, environment information, dashboards, knowledge artifacts, decisions, migration support, and portfolio views.

- 2026-07-06 (user observation): dashboard issue DB buries the `active` status group mid-page under default sort (created_desc) because group order follows row-encounter order. Active group should always render first (active → review → blocked → backlog → done). Small UI fix in project_memory.py groupedRows/status ordering. Source: user couldn't find active issue 071 in the DB view.
