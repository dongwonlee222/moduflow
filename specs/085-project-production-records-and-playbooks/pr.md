# PR Handoff: 085-project-production-records-and-playbooks

## Purpose

Make the pull request the visible review surface instead of waiting until all local review work is finished.
Use a Draft PR or a local PR-ready marker early, then attach review, verification, and dashboard evidence to it as work progresses.

## Draft PR

- Branch: `codex/085-project-production-records-and-playbooks`
- PR: `https://github.com/dongwonlee222/moduflow/pull/17`
- Reviewer: `Dongwon Lee`
- Fallback reason: GitHub Draft PR URL is available or expected to be supplied by the workflow.
- Preferred timing: create a Draft PR after the first meaningful commit, or record a local PR-ready marker when GitHub write access is unavailable.
- Do not merge from this handoff. Merge remains gated by Human approval, required reviews, and Required status checks.
- Commit mode: `local-git-write`

## Commands

```bash
python3 scripts/project_pr.py . --issue-id 085-project-production-records-and-playbooks --write
```

```bash
python3 scripts/project_workflow.py . --pr-state --issue-id 085-project-production-records-and-playbooks --pr "https://github.com/dongwonlee222/moduflow/pull/17" --reviewer "Dongwon Lee"
```

- Continue review: `product:review 085-project-production-records-and-playbooks`
- Refresh PR handoff: `product:pr 085-project-production-records-and-playbooks`

## PR Body Contract

- Summary: what changed and why.
- Verification: local tests, release checks, CI/status checks, and known gaps.
- Dashboard: `memory/dashboard.html`.
- Issue drill-down: `memory/issue-085-project-production-records-and-playbooks.html`.
- Korean human-review packet: `specs/085-project-production-records-and-playbooks/human-review.ko.md`.
- Review findings: implementation, QA, and PM/spec review results.
- Human approval: who reviewed the dashboard, PR diff, and merge readiness.

## Evidence To Mirror

### Verification

- Focused production suite: 24 passed.
- Full repository suite: 483 passed.
- Spec consistency: 0 findings.
- Package, project, release, lint, and security gates: passed.
- GitHub CI `test`: success; PR is mergeable.
- Constitution: v1.0 checked — no violations.
- Converge: 13 unverifiable due numbered-AC parser limitation; no blocking findings.
- Visual evidence: `memory/dashboard.html`, `memory/issue-085-project-production-records-and-playbooks.html`.
- Reference improvements: none found.

### Review Findings

1. **High — same-day/title ID collision blocked distinct records.** Resolved by preserving the simple base ID for the first record and deterministically adding source context when a different capture key collides. Added a regression test proving both records are created without overwrite.
2. **Medium — CLI usage errors raised `SystemExit(2)` instead of returning `2`.** Resolved with a returning argument parser and a focused direct-`main(argv)` test.
3. **Medium — missing `--issue-id` and `--source-context` returned mutation failure `1`.** Resolved by classifying the missing source as a usage error and returning `2`.

### Visual Evidence

- Dashboard: `memory/dashboard.html`.
- Issue drill-down: `memory/issue-085-project-production-records-and-playbooks.html`.

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

- Issue bytes: 6104
- Spec bytes: 17131
- Status bytes: 1732
- Review bytes: 3465
