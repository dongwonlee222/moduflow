# Issue 127: Recurring Data Update Playbook Routing

**Status: done** — created 2026-09-07; started 2026-09-07; done 2026-09-07.
**Priority: p2**
**Blocked-by:**

## Summary

Route recurring data updates and weekly report input procedures to `product:production`, so projects can preserve source windows, actual-versus-forecast decisions, human approval, exact write targets, inactive channels, and verification evidence as production records and playbooks.

## Source

- Type: direct user request from a Modu Charge campaign-report update
- Owner / decision maker: Dongwon Lee
- Request: `이것도 플레이북으로 모두플로! 모두플로 버전 업데이트 하면서`
- Date: 2026-09-07

## Problem

`product:production` already owns recurring deliverables and playbooks, but its routing examples name creative and communication outputs only. A weekly campaign report can therefore be treated as an isolated analysis or a one-off Sheet edit even when its reusable value is the operating procedure: source selection, same-weekday comparison, forecast labeling, approval, bounded write, and post-write validation.

## Outcome

- `product:production` and the PM router explicitly include recurring data updates.
- Korean requests for a data-update or weekly-report-input playbook route to `product:production`.
- The command documents the minimum evidence for data updates and provides a `campaign-report-data-update` example.
- Modu Charge applies the contract through `playbooks/weekly-campaign-report-data-update.md` and its linked production record; company data and metric values remain outside this plugin.
- Plugin source and Codex manifests advance from 0.3.65 to 0.3.66.

## Scope

### In

- Extend existing routing and command documentation.
- Add a regression test for English and Korean routing terms and the data-update example.
- Bump the patch version and refresh the Codex personal installation.

### Out

- Add a scheduler, database connector, spreadsheet writer, or calculation engine.
- Copy Modu Charge production data or project-specific formulas into ModuFlow.
- Change the production-record or playbook schemas.

## Acceptance Criteria

- `반복 데이터 업데이트` and `데이터 업데이트 플레이북` resolve to `product:production` in the skill surfaces.
- The production command requires source/comparison window, actual or forecast state, approval, exact write target, inactive channels, and verification evidence.
- The command shows a `campaign-report-data-update` record example.
- Focused tests and the full release check pass.
- Source and installed Codex package report version 0.3.66.

## Verification

- RED: `python3 -m unittest tests.test_production_data_update_routing -v` failed 2/2 before routing text existed.
- GREEN: the same focused suite passed 2/2 after the minimal routing and command changes.
- Regression: `python3 -m unittest tests.test_production_data_update_routing tests.test_project_production -v` passed 49/49.
- Final verification: `python3 scripts/release_check.py .` returned `valid: true` with all release checks passing.

## Workflow Tasks

- [x] execute → `skills/index/SKILL.md`, `skills/pm-execution-router/SKILL.md`, `commands/product-production.md`, `README.md`, `tests/test_production_data_update_routing.py`
- [x] review → focused TDD evidence and full release gate

## Related Issues

- follows_up: `085-project-production-records-and-playbooks`, `091-reproducible-analysis-runs-and-template-pack`
- related: `115-playbook-process-and-checklist-extension`

## Links

- Project application: `/Users/dongwon.lee/workhub/company/projects/modu-charge/playbooks/weekly-campaign-report-data-update.md`
- Project issue: `/Users/dongwon.lee/workhub/company/projects/modu-charge/projects/modu-charge/issues/MODU-013.md`

## Next Command

`product:status`
