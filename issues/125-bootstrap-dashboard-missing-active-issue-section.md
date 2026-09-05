# Issue 125: Bootstrap Dashboard Missing Active Issue Section

**Status: review** — created 2026-09-05; fix implemented the same day, awaiting review.
**Priority: p1**

## 요약

새 프로젝트를 만드는 두 경로(`product:start`·`product:migrate`)가 만드는 `workspace/dashboard.md`에 `## Active Issue` 섹션이 없습니다. 종료 훅의 투영 함수는 그 섹션이 없으면 `ValueError`를 던집니다. 그래서 새 어댑터는 **세션이 끝날 때마다** 트레이스백을 봅니다.

## Summary

`project_lifecycle.render_dashboard_projection` raises
`ValueError: dashboard requires an Active Issue section` when the dashboard has
no `## Active Issue` heading. Both bootstrap paths write a dashboard without one,
so every session end fails for a newly created or newly migrated project.

## Source

- Type: bug reported through `workspace/inbox.md`, 2026-09-05
- Owner / decision maker: Dongwon Lee
- Reported scope: `product:migrate` only. Verified while fixing that
  `product:start` has the same defect, so this issue covers both.

## Opportunity

```python
# scripts/project_lifecycle.py:155
pattern = re.compile(r"^##\s+Active Issue\s*$.*?(?=^##\s|\Z)", re.M | re.S)
if not pattern.search(text):
    raise ValueError("dashboard requires an Active Issue section")
```

Measured against the projection on 2026-09-05:

| Dashboard source | Result |
| --- | --- |
| `templates/workspace/dashboard.md` (`product:start`) | **ValueError** |
| `project_migrate.WORKSPACE_FILES["dashboard.md"]` (`product:migrate`) | **ValueError** |
| this repository's own hand-grown `workspace/dashboard.md` | passes |

Only a dashboard that grew by hand satisfies the projection. Every dashboard the
product generates fails it.

Two details worth keeping from the report:

- A new adopter hits **two different errors in sequence** — before an issue
  exists the failure is `ISSUE_RECONCILE_OWNER_UNAVAILABLE`, and after creating
  one it becomes this ValueError. Neither names the actual fix.
- The report asked whether `render_roadmap_projection` has the same mismatch.
  **It does not.** When its managed block is absent it appends
  (`project_lifecycle.py:213`) rather than raising. That asymmetry between two
  sibling projections is the underlying inconsistency, and is worth a decision
  even though the dashboard side is now fixed.

Still open from the same report and **not** fixed here:

- `hooks/on_stop.py:189` logs `detail[:300]`, keeping the head of a traceback.
  A Python traceback carries its exception type at the end, so the cap hides the
  very line that identifies the failure — which is how this bug stayed
  unidentified. Lines 249 and 265 share the pattern.

## Scope

### In

- `## Active Issue` in both bootstrap dashboards, matching the text the
  projection itself writes for the no-active-issue case.
- A guard test covering every bootstrap dashboard template, including any added
  later.

### Out

- Changing `render_dashboard_projection` to append instead of raise. Making the
  projection lenient would hide the next template that ships without the section.
- The roadmap/dashboard asymmetry noted above. It needs a decision, not a patch.
- The `detail[:300]` log truncation. Same report, different file, different fix.

## Acceptance Criteria

- `templates/workspace/dashboard.md` survives the projection. **Met.**
- `project_migrate.WORKSPACE_FILES["dashboard.md"]` survives it. **Met.**
- Any `dashboard.md` under `templates/` survives it, so a third bootstrap path
  added later is covered. **Met.**
- The projection still rejects a dashboard with no section — the guard must not
  be satisfied by weakening the check. **Met.**
- Projection output is stable on a second pass. **Met.**

## Verification

`tests/test_bootstrap_dashboard_projection.py` — 5 tests, RED before the fix
(4 failing) and GREEN after. Full suite and `release_check` re-run before merge.

## Entry Points

- `templates/workspace/dashboard.md`
- `scripts/project_migrate.py` — `WORKSPACE_FILES`
- `scripts/project_lifecycle.py:136` — `render_dashboard_projection`
- `tests/test_bootstrap_dashboard_projection.py`

## Scope Fence

Fix the templates, not the projection. The ValueError is doing its job.

## Workflow Tasks

- [x] execute → both templates plus the guard test
- [ ] review → `specs/125-bootstrap-dashboard-missing-active-issue-section/review.md`

No spec or plan: a two-template fix with a guard test is below the threshold
where a spec adds anything, per the S-grade bugfix exception.

## Related Issues

- related: `124-inbox-entries-cannot-be-promoted` (this bug sat in the inbox
  because there was no path out of it), `096-read-shaped-commands-that-write`

## Next Command

`product:review 125-bootstrap-dashboard-missing-active-issue-section`
