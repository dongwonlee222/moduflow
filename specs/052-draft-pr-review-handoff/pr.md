# PR Handoff: 052-draft-pr-review-handoff

## Purpose

Make the pull request the visible review surface instead of waiting until all local review work is finished.
Use a Draft PR or a local PR-ready marker early, then attach review, verification, and dashboard evidence to it as work progresses.

## Draft PR

- Branch: `codex/052-draft-pr-review-handoff`
- PR: `local:052-draft-pr-ready`
- Reviewer: `Dongwon`
- Fallback reason: GitHub Draft PR URL is not recorded yet. This local PR-ready marker preserves review state until GitHub sync creates or mirrors the PR.
- Preferred timing: create a Draft PR after the first meaningful commit, or record a local PR-ready marker when GitHub write access is unavailable.
- Do not merge from this handoff. Merge remains gated by Human approval, required reviews, and Required status checks.

## Commands

```bash
python3 scripts/project_pr.py . --issue-id 052-draft-pr-review-handoff --write
```

```bash
python3 scripts/project_workflow.py . --pr-state --issue-id 052-draft-pr-review-handoff --pr "local:052-draft-pr-ready" --reviewer "Dongwon"
```

- Continue review: `product:review 052-draft-pr-review-handoff`
- Refresh PR handoff: `product:pr 052-draft-pr-review-handoff`

## PR Body Contract

- Summary: what changed and why.
- Verification: local tests, release checks, CI/status checks, and known gaps.
- Dashboard: `memory/dashboard.html`.
- Issue drill-down: `memory/issue-052-draft-pr-review-handoff.html`.
- Review findings: implementation, QA, and PM/spec review results.
- Human approval: who reviewed the dashboard, PR diff, and merge readiness.

## Evidence To Mirror

### Verification

- `python3 -m unittest tests.test_project_pr -v` passed.
- `python3 scripts/project_pr.py . --issue-id 052-draft-pr-review-handoff --write` generated `specs/052-draft-pr-review-handoff/pr.md`.
- `python3 scripts/project_memory.py . --dashboard` generated `memory/dashboard.html`.
- `python3 scripts/project_memory.py . --issue 052-draft-pr-review-handoff` generated `memory/issue-052-draft-pr-review-handoff.html`.
- `python3 scripts/project_lifecycle.py . --drift` returned `[]`.
- `python3 scripts/release_check.py .` passed.

### Review Findings

- The flow now distinguishes PR creation from merge approval. `product:pr` can create or record an early Draft PR / PR-ready marker, while merge remains controlled by human approval and GitHub checks.
- `product:review` now has an explicit PR evidence gate, so dashboard and review evidence do not stay local-only.
- `product:execute` now explains when early PR state should be created, without forcing GitHub writes in local-only mode.
- PM/spec review found that local PR-ready fallback must explain why no GitHub Draft PR URL is present. Fixed by adding a fallback reason to `pr.md`.
- PM/spec review found that `product:pr` still sounded like a late-only PR step. Fixed by changing the command description and making early PR state a pre-review requirement.
- QA/release review found that `pr.md` contained a contract but not actual evidence. Fixed by embedding verification, review, visual evidence, and approval record sections.
- QA/release review found that release_check evidence was missing from status/dashboard artifacts. Fixed in `status.md` and `workspace/dashboard.md`.

### Visual Evidence

- `memory/dashboard.html`
- `memory/issue-052-draft-pr-review-handoff.html`

## Approval Record

- Dashboard reviewer: `Dongwon` or assigned reviewer before merge.
- PR diff reviewer: `Dongwon` or assigned reviewer before merge.
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

- Issue bytes: 2868
- Spec bytes: 2319
- Status bytes: 1425
- Review bytes: 1652
