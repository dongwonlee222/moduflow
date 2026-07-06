# PR Handoff: 071-spec-code-converge-check

## Purpose

Make the pull request the visible review surface instead of waiting until all local review work is finished.
Use a Draft PR or a local PR-ready marker early, then attach review, verification, and dashboard evidence to it as work progresses.

## Draft PR

- Branch: `codex/071-spec-code-converge-check`
- PR: `local:071-spec-code-converge-check:draft-pr-ready`
- Reviewer: `Reviewer`
- Fallback reason: GitHub Draft PR URL is not recorded yet. This local PR-ready marker preserves review state until GitHub sync creates or mirrors the PR.
- Preferred timing: create a Draft PR after the first meaningful commit, or record a local PR-ready marker when GitHub write access is unavailable.
- Do not merge from this handoff. Merge remains gated by Human approval, required reviews, and Required status checks.
- Commit mode: `local-git-write`

## Commands

```bash
python3 scripts/project_pr.py . --issue-id 071-spec-code-converge-check --write
```

```bash
python3 scripts/project_workflow.py . --pr-state --issue-id 071-spec-code-converge-check --pr "local:071-spec-code-converge-check:draft-pr-ready" --reviewer "Reviewer"
```

- Continue review: `product:review 071-spec-code-converge-check`
- Refresh PR handoff: `product:pr 071-spec-code-converge-check`

## PR Body Contract

- Summary: what changed and why.
- Verification: local tests, release checks, CI/status checks, and known gaps.
- Dashboard: `memory/dashboard.html`.
- Issue drill-down: `memory/issue-071-spec-code-converge-check.html`.
- Korean human-review packet: `specs/071-spec-code-converge-check/human-review.ko.md`.
- Review findings: implementation, QA, and PM/spec review results.
- Human approval: who reviewed the dashboard, PR diff, and merge readiness.

## Evidence To Mirror

### Verification

- Verification evidence has not been recorded yet.

### Review Findings

1. (resolved) Doc workers twice invented CLI flags (`--judge`, `--judge-inline`, `--judgment-file`) not present in the implemented surface — corrected by coordinator both times; the pattern (doc workers extrapolating CLI) is worth a line in worker prompts going forward.
2. (resolved) Plan GC#6 grammar gap for unrequested findings — caught by 071's own converge run; plan amended with dated note.
3. (open, follow-up candidate) Bundle file ordering: tight caps truncate implementing code first, inflating `unverifiable` (8/9 on 075's first run). Evidence collection should prioritize scripts/tests over docs when capping. Not blocking; candidate CV/inbox item for a 071 follow-up.
4. (accepted) Judgment variance risk stands as spec'd — run history in converge.md keeps it visible.

### Visual Evidence

- Dashboard: `memory/dashboard.html`.
- Issue drill-down: `memory/issue-071-spec-code-converge-check.html`.

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

- Issue bytes: 2656
- Spec bytes: 12433
- Status bytes: 2109
- Review bytes: 3124
