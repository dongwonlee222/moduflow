# PR Handoff: 056-dashboard-database-list-view

## Purpose

Make the pull request the visible review surface instead of waiting until all local review work is finished.
Use a Draft PR or a local PR-ready marker early, then attach review, verification, and dashboard evidence to it as work progresses.

## Draft PR

- Branch: `codex/056-dashboard-db-list-view-spec`
- PR: `local:056-dashboard-db-list-view-spec:review-ready`
- Reviewer: `Reviewer`
- Fallback reason: GitHub Draft PR URL is not recorded yet. This local PR-ready marker preserves review state until GitHub sync creates or mirrors the PR.
- Preferred timing: create a Draft PR after the first meaningful commit, or record a local PR-ready marker when GitHub write access is unavailable.
- Do not merge from this handoff. Merge remains gated by Human approval, required reviews, and Required status checks.

## Commands

```bash
python3 scripts/project_pr.py . --issue-id 056-dashboard-database-list-view --branch codex/056-dashboard-db-list-view-spec --pr local:056-dashboard-db-list-view-spec:review-ready --reviewer Reviewer --write
```

```bash
python3 scripts/project_workflow.py . --pr-state --issue-id 056-dashboard-database-list-view --pr "local:056-dashboard-db-list-view-spec:review-ready" --reviewer "Reviewer" --branch codex/056-dashboard-db-list-view-spec
```

- Continue: `product:pr 056-dashboard-database-list-view`
- Refresh PR handoff: `product:pr 056-dashboard-database-list-view`

## PR Body Contract

- Summary: what changed and why.
- Verification: local tests, release checks, CI/status checks, and known gaps.
- Dashboard: `memory/dashboard.html`.
- Issue drill-down: `memory/issue-056-dashboard-database-list-view.html`.
- Review findings: implementation, QA, and PM/spec review results.
- Human approval: who reviewed the dashboard, PR diff, and merge readiness.

## Evidence To Mirror

### Verification

- `python3 -m unittest tests.test_project_memory`
- `python3 -m unittest discover -s tests`
- `python3 scripts/project_memory.py . --dashboard`
- `python3 -m py_compile scripts/project_memory.py`
- generated HTML contains `이슈 DB`, `ISSUE_ROWS`, search controls, missing filter, and 056 issue row link
- generated dashboard script parses with Node `new Function`
- `python3 scripts/validate_project_artifacts.py .`
- `python3 scripts/validate_moduflow.py .`
- `python3 scripts/release_check.py .`

### Review Findings

- Review passed; no blocking or important findings.
- Review artifact: `specs/056-dashboard-database-list-view/review.md`.
- Known limitation: browser automation could not run because the local Playwright browser binary was missing and installed Chrome exited under sandbox constraints. Generated dashboard and issue drill-down were opened locally for human visual review.

### Visual Evidence

- Dashboard: `memory/dashboard.html`.
- Issue drill-down: `memory/issue-056-dashboard-database-list-view.html`.

## Approval Record

- Dashboard reviewer: `Reviewer` or assigned reviewer before merge.
- PR diff reviewer: `Reviewer` or assigned reviewer before merge.
- Merge approver: human approval required; not granted by this handoff.
- Deployment approver: required only when a protected deployment environment is configured.

## Human Checkpoints

- Spec/plan approval before implementation starts.
- Dashboard and issue drill-down inspection after review.
- GitHub PR diff, conversation, and status checks before approval.
- Merge and deployment approval through protected branch or environment gates.

## GitHub Gate Alignment

- PR review can approve, comment, or request changes.
- Required status checks must pass before merge when branch protection is configured.
- Required reviewers or CODEOWNERS remain the merge authority.
- Deployment environments may add a separate approval gate after merge or before release.

## Source Snapshot

- Issue bytes: 5419
- Spec bytes: 8506
- Status bytes: 1670
- Review bytes: 3274
