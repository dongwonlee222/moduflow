# PR Handoff: 095-commit-issue-resolution-parity

## Purpose

Make the pull request the visible review surface instead of waiting until all local review work is finished.
Use a Draft PR or a local PR-ready marker early, then attach review, verification, and dashboard evidence to it as work progresses.

## Draft PR

- Branch: `codex/095-commit-issue-resolution-parity-fix`
- PR: `local:095-commit-issue-resolution-parity-fix:draft-pr-ready`
- Reviewer: `Reviewer`
- Fallback reason: no GitHub Draft PR is claimed yet. This local marker records
  the corrective handoff until GitHub sync creates a real PR.
- Preferred timing: create a Draft PR after the first meaningful commit, or record a local PR-ready marker when GitHub write access is unavailable.
- Do not merge from this handoff. Merge remains gated by Human approval, required reviews, and Required status checks.
- Commit mode: `local-git-write`

## Commands

```bash
python3 scripts/project_pr.py . --issue-id 095-commit-issue-resolution-parity --write
```

```bash
python3 scripts/project_workflow.py . --pr-state --issue-id 095-commit-issue-resolution-parity --pr "local:095-commit-issue-resolution-parity-fix:draft-pr-ready" --reviewer "Reviewer"
```

- Continue review: `product:review 095-commit-issue-resolution-parity`
- Refresh PR handoff: `product:pr 095-commit-issue-resolution-parity`

## PR Body Contract

- Summary: what changed and why.
- Verification: local tests, release checks, CI/status checks, and known gaps.
- Dashboard: `memory/dashboard.html`.
- Issue drill-down: `memory/issue-095-commit-issue-resolution-parity.html`.
- Korean human-review packet: `specs/095-commit-issue-resolution-parity/human-review.ko.md`.
- Review findings: implementation, QA, and PM/spec review results.
- Human approval: who reviewed the dashboard, PR diff, and merge readiness.

## Evidence To Mirror

### Verification

- Task 1 focused suite: `92/92 PASS`.
- Five-module focused suite: `195/195 PASS`.
- Expected failures: `0`.
- Artifact validation and lifecycle drift are refreshed by F3.
- Full unittest discovery and release check remain F4; this handoff does not
  claim they have passed on the corrective branch.

### Review Findings

- Task 1 independent spec review: pass.
- Task 1 independent quality review: pass after terminated graph-query handling
  was fixed in `881d81d`.
- Task 2 independent spec review: pass.
- Task 2 independent quality review: pass after two Important base-selection
  findings were fixed and re-reviewed in `4f5d14a`.
- Final whole-branch review remains F4.

### Visual Evidence

- Dashboard: `memory/dashboard.html`.
- Issue drill-down: `memory/issue-095-commit-issue-resolution-parity.html`.

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

## Corrective Commit Set

- `f980aef` — approved corrective design and execution plan.
- `21d1290` — fail closed on historical issue discovery.
- `881d81d` — reject failed or terminated graph queries.
- `ef149a8` — apply one global attribution policy.
- `4f5d14a` — fail closed on unusable branch bases.

## Separate Issue 096 Gate

Issue 096 owns the command-safety follow-up: explicit evidence writes,
issue-id path traversal prevention, repo-external symlink rejection, and write
announcements. Do not update the installed plugin until both 095 and 096 are
safe. Issue 096 is not part of this PR diff.

## GitHub Gate Alignment

- PR review can approve, comment, or request changes.
- Required status checks must pass before merge when branch protection is configured.
- Required reviewers or CODEOWNERS remain the merge authority.
- Deployment environments may add a separate approval gate after merge or before release.

## Source Snapshot

- Issue bytes: 5907
- Spec bytes: 7818
- Status bytes: 10909
- Review bytes: 0
