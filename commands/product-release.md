---
description: Prepare release, deploy, rollback, and post-release checks.
argument-hint: "<issue id>"
---

# /product:release

Prepare release.

## Do

1. Confirm merged PR, version, deploy target, rollback path, and post-release checks.
2. Confirm `specs/<issue>/human-review.ko.md` exists and was used as the first human approval surface.
3. Confirm human approval evidence is recorded before release. The evidence must identify who reviewed the dashboard, issue detail, PR diff or local change scope, verification result, and release readiness.
4. Hold release if the Korean packet is missing, stale, or does not include verification, hold criteria, and approval checklist.
5. Run `scripts/release_check.py .` before publishing a plugin/package update.
6. Save to `specs/<issue>/release.md`.
7. Update roadmap and status.

## Korean Human Review Gate

Release can proceed only after a Korean-speaking reviewer can start from `human-review.ko.md` and make an approve/hold decision without searching through English-only artifacts.

The release note should link:

- `specs/<issue>/human-review.ko.md`
- `specs/<issue>/pr.md`
- `memory/dashboard.html#issue-db`
- `memory/issue-<issue>.html`

If GitHub PR creation is unavailable, record the local PR-ready marker and keep the Korean packet current. Do not treat the local marker as merge or release approval.

## Next

- `/product:update` for stakeholder communication
- `/product:analyze` for post-release metric readout
