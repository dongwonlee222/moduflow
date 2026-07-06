# Release: Korean Human Review Packet

Issue: `057-korean-human-review-packet`
Date: 2026-07-03
Release status: released locally; GitHub PR creation deferred by `gh` preflight

## Summary

Issue 057 is released in the Git-native workflow after human approval.

This release standardizes the Korean human-review packet as the first review surface for PR, review, and release gates. Korean-speaking reviewers can now approve or hold work without searching through English-only canonical artifacts.

## Scope Released

- Korean human-review packet generation via `scripts/project_pr.py`.
- Release gate documentation in `commands/product-release.md`.
- Release checklist wording in `human-review.ko.md`.
- Test coverage for the release command contract and Korean packet release checklist.
- 057 review artifact, PR handoff, and Korean human-review packet.
- Dashboard/roadmap/team-state updates showing 057 as review-approved and released.

## Release Evidence

- Branch: `codex/057-korean-human-review-packet`
- Base branch: `codex/056-dashboard-db-list-view-spec`
- Local PR-ready marker: `local:057-korean-human-review-packet:pr-ready`
- Human approval record: `workflow/records/2026-07-03-057-korean-human-review-packet-approved.md`
- Korean review packet: `specs/057-korean-human-review-packet/human-review.ko.md`
- PR handoff: `specs/057-korean-human-review-packet/pr.md`

GitHub Draft PR creation remains deferred when local `gh` preflight is unavailable. The GitHub API commit is the remote sync path for this Codex environment.

## Verification

- `python3 -m unittest discover -s tests` passed, 176 tests.
- `python3 scripts/validate_project_artifacts.py .` passed.
- `python3 scripts/validate_moduflow.py .` passed.
- `python3 scripts/release_check.py .` passed.

## Human Review

- Approver: Dongwon.
- Approval date: 2026-07-03.
- Review surface:
  - `specs/057-korean-human-review-packet/human-review.ko.md`
  - `specs/057-korean-human-review-packet/pr.md`
  - `memory/dashboard.html#issue-db`
  - `memory/issue-057-korean-human-review-packet.html`

## Rollback

If this release needs to be reverted before merge to `main`, abandon or reset the feature branch.

If it has already been merged, revert the release commit or the 057 branch range, then run:

```bash
python3 scripts/release_check.py .
```

## Post-Release Follow-Ups

- Apply the Korean packet convention to future PR/review/release flows by default.
- Consider a future dashboard affordance for "검토 패킷 열기" directly from the DB row.

## Next

`product:status`
