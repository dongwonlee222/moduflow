# PR Handoff: 081-gpt-5-6-model-tier-guidance

## Purpose

Make the pull request the visible review surface instead of waiting until all local review work is finished.
Use a Draft PR or a local PR-ready marker early, then attach review, verification, and dashboard evidence to it as work progresses.

## Draft PR

- Branch: `codex/081-gpt-5-6-model-tier-guidance`
- PR: `local:081-gpt-5-6-model-tier-guidance:draft-pr-ready`
- Reviewer: `Dongwon Lee`
- Fallback reason: GitHub Draft PR URL is not recorded yet. This local PR-ready marker preserves review state until GitHub sync creates or mirrors the PR.
- Preferred timing: create a Draft PR after the first meaningful commit, or record a local PR-ready marker when GitHub write access is unavailable.
- Do not merge from this handoff. Merge remains gated by Human approval, required reviews, and Required status checks.
- Commit mode: `local-git-write`

## Commands

```bash
python3 scripts/project_pr.py . --issue-id 081-gpt-5-6-model-tier-guidance --write
```

```bash
python3 scripts/project_workflow.py . --pr-state --issue-id 081-gpt-5-6-model-tier-guidance --pr "local:081-gpt-5-6-model-tier-guidance:draft-pr-ready" --reviewer "Dongwon Lee"
```

- Continue review: `product:review 081-gpt-5-6-model-tier-guidance`
- Refresh PR handoff: `product:pr 081-gpt-5-6-model-tier-guidance`

## PR Body Contract

- Summary: what changed and why.
- Verification: local tests, release checks, CI/status checks, and known gaps.
- Dashboard: `memory/dashboard.html`.
- Issue drill-down: `memory/issue-081-gpt-5-6-model-tier-guidance.html`.
- Korean human-review packet: `specs/081-gpt-5-6-model-tier-guidance/human-review.ko.md`.
- Review findings: implementation, QA, and PM/spec review results.
- Human approval: who reviewed the dashboard, PR diff, and merge readiness.

## Evidence To Mirror

### Verification

Re-run at branch head on 2026-07-25:

| Check | Result |
| --- | --- |
| `python3 -m unittest discover -s tests` | 582 passed, `OK` |
| `python3 scripts/release_check.py .` | `valid: true`, zero errors |
| `python3 scripts/spec_consistency.py . --issue-id 081-gpt-5-6-model-tier-guidance` | 0 errors, 1 info (`tasks.md is missing`) |
| `python3 scripts/project_lifecycle.py . --drift` | `[]` |

Original focused run: `python3 -m unittest tests.test_cognitive_demand_routing -v`
passed.

### Review Findings

No blocking findings.

### Visual Evidence

- Dashboard: `memory/dashboard.html`.
- Issue drill-down: `memory/issue-081-gpt-5-6-model-tier-guidance.html`.

## Approval Record

- Dashboard reviewer: `Dongwon Lee` or assigned reviewer before merge.
- PR diff reviewer: `Dongwon Lee` or assigned reviewer before merge.
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

- Issue bytes: 3378
- Spec bytes: 1609
- Status bytes: 1933
- Review bytes: 2747
