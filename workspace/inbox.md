# ModuFlow Inbox

## 2026-06-11

- [handled] Multi-project users need project-local issue management, environment information, dashboards, knowledge artifacts, decisions, migration support, and portfolio views.

- [handled 2026-09-05] 2026-07-06 (user observation): dashboard issue DB buries the `active` status group mid-page under default sort (created_desc) because group order follows row-encounter order. Active group should always render first (active → review → blocked → backlog → done). Small UI fix in project_memory.py groupedRows/status ordering. Source: user couldn't find active issue 071 in the DB view.

## 2026-09-05

- (user requirement): work continues on a second computer and other people will use ModuFlow too. Cloning and continuing **alone** already works — everything is in git and `INSTALL.md` covers the plugin install. Two problems appear only when two people work at the same time.

- (blocker for concurrent work): `.moduflow/state.json` holds a single global `active_issue`, and it is tracked in git. Every lifecycle transition writes it and `workspace/loop-state.json` — both were transaction targets when issues 086 and 119 were completed on 2026-09-05. Two people working at once each write their own issue id into the same field and conflict on every transition; a mis-resolved conflict silently discards the other person's state. "What I am working on right now" is per-person and does not belong in a shared file. Note before designing anything new: `workflow/team-state.json` (issues 005/035) already carries `owner`, `assignee`, `reviewer`, `branch`, `pr`, `lock_state` and `locked_by` per issue. Whether that lock is actually enforced against a transition was **not** checked — check that first, because if it is, this problem is smaller than it looks.

- (needed once other people join): the GitHub mirror shows 10 of 122 issues, so someone who looks at GitHub before cloning reads this as a ten-issue project. Three issues that were done locally were still open there (#27/086, #23/093, #21/091) and were closed by hand on 2026-09-05 with a comment. They drifted because nothing runs the sync: `commands/product-issue.md` says projection happens only on explicit request, never automatically. And `scripts/project_github_issues.py` only does `gh issue create` / `edit` / `label` — it has **no close path at all**, so completion cannot be mirrored even on request. Deciding when sync runs means changing the "never automatically" rule, which is a human decision.

## Handled

- 2026-09-05: the `active` group ordering fix landed in `groupedRows`
  (`scripts/project_memory.py`). Verified in a browser, not only by markers.
- 2026-09-05: the 2026-06-11 multi-project note is covered by Issues 102
  (registry/resolver), 086 (project-aware dashboard), 004/036 (portfolio
  workspace and summary) and 118 (portfolio-mode dashboard). Entries are
  marked in place rather than removed so the original wording survives.
