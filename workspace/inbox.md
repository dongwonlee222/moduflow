# ModuFlow Inbox

## 2026-06-11

- [handled] Multi-project users need project-local issue management, environment information, dashboards, knowledge artifacts, decisions, migration support, and portfolio views.

- [handled 2026-09-05] 2026-07-06 (user observation): dashboard issue DB buries the `active` status group mid-page under default sort (created_desc) because group order follows row-encounter order. Active group should always render first (active → review → blocked → backlog → done). Small UI fix in project_memory.py groupedRows/status ordering. Source: user couldn't find active issue 071 in the DB view.

## 2026-09-05

- (user requirement): work continues on a second computer and other people will use ModuFlow too. Cloning and continuing **alone** already works — everything is in git and `INSTALL.md` covers the plugin install. Two problems appear only when two people work at the same time.

- (blocker for concurrent work): `.moduflow/state.json` holds a single global `active_issue`, and it is tracked in git. Every lifecycle transition writes it and `workspace/loop-state.json` — both were transaction targets when issues 086 and 119 were completed on 2026-09-05. Two people working at once each write their own issue id into the same field and conflict on every transition; a mis-resolved conflict silently discards the other person's state. "What I am working on right now" is per-person and does not belong in a shared file. Note before designing anything new: `workflow/team-state.json` (issues 005/035) already carries `owner`, `assignee`, `reviewer`, `branch`, `pr`, `lock_state` and `locked_by` per issue. Whether that lock is actually enforced against a transition was **not** checked — check that first, because if it is, this problem is smaller than it looks.

- **Missing primitive: numeric ledger + retraction propagation.** Source: real-world audit of a grant-application project (33 docs, 187 measurements, deadline-driven) run on 2026-09-05. ModuFlow tracks *"is the task done"*; that project needed *"is the sentence I wrote still true"*. Issue state moves forward (todo→doing→done); evidence moves backward — when a server-cost assumption (600k KRW/mo) was replaced by a measurement (80k KRW/mo, ledger id M173), the already-`done` break-even figure (4,706 users) silently went stale in **four** documents, and a retracted metric survived in one doc after being removed from another. 14 instances of the same class in one audit.

  What is missing (verified against this repo on 2026-09-05):
  1. **No artifact to hold a measured value.** Artifacts are issue/spec/plan/decision/knowledge/memory. `knowledge/data-notes/` is a document folder, not a record schema for `{id, value, grade A/B/C/D, source, measured_at}`.
  2. **No citation edge.** `linkage_check.py` links commits↔issues only. There is no way to record "document X's break-even cites M173".
  3. **No reverse query.** `product:evidence` does forward search/summary (issue → evidence). It cannot answer "if M173 changes, what breaks".
  4. **No invalidation state.** Issues have open/closed. A *value* needs `retracted|superseded` + reason + replacement (e.g. 28% retracted by M109, replaced with 0.93x/4.2x).
  5. **`product:converge` is code-only.** Its shape is already right — AC/GC ↔ evidence bundle ↔ independent judge, non-blocking, re-runnable forever. But `project_converge.py` collects git commits as the only evidence source.

  Proposal: do not build a new tool. Widen converge's two slots — AC/GC → *claims*, commit evidence → *numeric ledger*. A working reference implementation already exists by hand in that project (M1~M187 with values, grades, and sources), which is ahead of the current evidence layer.

  `retrieval_trigger`: re-read when working on evidence/knowledge layer, converge scope, or any request about tracking whether written claims remain valid.
  Suggested routing: `product:opportunity` (product shaping) — this is not obvious implementation work yet.

- (needed once other people join): the GitHub mirror shows 10 of 122 issues, so someone who looks at GitHub before cloning reads this as a ten-issue project. Three issues that were done locally were still open there (#27/086, #23/093, #21/091) and were closed by hand on 2026-09-05 with a comment. They drifted because nothing runs the sync: `commands/product-issue.md` says projection happens only on explicit request, never automatically. And `scripts/project_github_issues.py` only does `gh issue create` / `edit` / `label` — it has **no close path at all**, so completion cannot be mirrored even on request. Deciding when sync runs means changing the "never automatically" rule, which is a human decision.

## Handled

- 2026-09-05: the `active` group ordering fix landed in `groupedRows`
  (`scripts/project_memory.py`). Verified in a browser, not only by markers.
- 2026-09-05: the 2026-06-11 multi-project note is covered by Issues 102
  (registry/resolver), 086 (project-aware dashboard), 004/036 (portfolio
  workspace and summary) and 118 (portfolio-mode dashboard). Entries are
  marked in place rather than removed so the original wording survives.
