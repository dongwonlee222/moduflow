# Tasks: Issue Dependency & Priority Model

Issue: `069-issue-dependency-priority-model`
Plan: `specs/069-issue-dependency-priority-model/plan.md`

## Stream A — Lifecycle

- [ ] `_issue_priority` / `_issue_blocked_by` parsers
- [ ] `list_issues` +priority/+blocked_by
- [ ] `ready_issues(root)` + `--ready` CLI
- [ ] Drift: dangling refs + open-issue cycles

## Stream B — MCP

- [ ] `moduflow_ready` tool

## Stream C — Template/docs/dogfood

- [ ] `templates/issues/issue.md` canonical Status line (pre-048 block removed)
- [ ] `commands/product-issue.md` + `commands/product-status.md`
- [ ] Priority backfill on 070-073
- [ ] `scripts/release_check.py` module list

## Stream D — Tests

- [ ] Parser/ready/sort/drift cases per plan
- [ ] 2 MCP cases

## Verification

- [ ] RED → GREEN; full discover; release_check
- [ ] `--ready` smoke on this repo (070/071 before 072/073)

## Next

`product:execute 069-issue-dependency-priority-model`
