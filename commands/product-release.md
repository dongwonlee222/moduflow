---
description: Prepare release, deploy, rollback, and post-release checks.
argument-hint: "<issue id>"
---

# /product:release

Prepare release.

## Do

1. Confirm merged PR, version, deploy target, rollback path, and post-release checks.
2. Run `scripts/release_check.py .` before publishing a plugin/package update.
3. Save to `specs/<issue>/release.md`.
4. Update roadmap and status.

## Next

- `/product:update` for stakeholder communication
- `/product:analyze` for post-release metric readout
