# PR Handoff: 074-sync-fetch-sandbox-handling

## Purpose

Make the pull request the visible review surface instead of waiting until all local review work is finished.
Use a Draft PR or a local PR-ready marker early, then attach review, verification, and dashboard evidence to it as work progresses.

## Draft PR

- Branch: `codex/074-sync-fetch-sandbox-handling`
- PR: `local:074-sync-fetch-sandbox-handling:draft-pr-ready`
- Reviewer: `Reviewer`
- Fallback reason: GitHub Draft PR URL is not recorded yet. This local PR-ready marker preserves review state until GitHub sync creates or mirrors the PR.
- Preferred timing: create a Draft PR after the first meaningful commit, or record a local PR-ready marker when GitHub write access is unavailable.
- Do not merge from this handoff. Merge remains gated by Human approval, required reviews, and Required status checks.
- Commit mode: `local-git-write`

## Commands

```bash
python3 scripts/project_pr.py . --issue-id 074-sync-fetch-sandbox-handling --write
```

```bash
python3 scripts/project_workflow.py . --pr-state --issue-id 074-sync-fetch-sandbox-handling --pr "local:074-sync-fetch-sandbox-handling:draft-pr-ready" --reviewer "Reviewer"
```

- Continue review: `product:review 074-sync-fetch-sandbox-handling`
- Refresh PR handoff: `product:pr 074-sync-fetch-sandbox-handling`

## PR Body Contract

- Summary: what changed and why.
- Verification: local tests, release checks, CI/status checks, and known gaps.
- Dashboard: `memory/dashboard.html`.
- Issue drill-down: `memory/issue-074-sync-fetch-sandbox-handling.html`.
- Korean human-review packet: `specs/074-sync-fetch-sandbox-handling/human-review.ko.md`.
- Review findings: implementation, QA, and PM/spec review results.
- Human approval: who reviewed the dashboard, PR diff, and merge readiness.

## Evidence To Mirror

### Verification

- `python3 scripts/project_sync.py . --no-fetch` reported local refs without the blocked internal fetch warning.
- `python3 -m unittest tests.test_project_sync -v` passed.
- `python3 scripts/release_check.py .` passed.
- `python3 scripts/validate_project_artifacts.py .` passed.

### Review Findings

- Spec compliance: pass. The hotfix adds an explicit `--no-fetch` path while preserving default automatic fetch behavior.
- Quality: pass. The new behavior is small, parameterized, and covered by a focused regression test. Existing fetch failure and timeout behavior remains covered.
- Risk: low. The default code path remains auto-fetch; `--no-fetch` is opt-in for approval-sensitive hosts after a top-level `git fetch`.

### Visual Evidence

- Dashboard: `memory/dashboard.html`.
- Issue drill-down: `memory/issue-074-sync-fetch-sandbox-handling.html`.

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

- Issue bytes: 2838
- Spec bytes: 0
- Status bytes: 1712
- Review bytes: 1199
