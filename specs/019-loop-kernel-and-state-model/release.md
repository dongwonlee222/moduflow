# Release: Loop Kernel And State Model

Issue: `019-loop-kernel-and-state-model`

## Version

`0.2.7+codex.20260618122055`

## Summary

Adds the ModuFlow loop kernel and state model so a goal can supervise multiple issues, keep one active cursor, recommend the next command, and stop repeated identical actions before the loop becomes noisy.

## Included

- `workspace/loop-state.json` v2 shape with `loop_id`, `goal_id`, `issue_ids`, `active_issue_id`, `status`, and attempts tracking.
- `scripts/project_loop.py` loader, normalizer, phase inference, loop recommendation, write mode, and repeated-command guard.
- Loop-state validation in `scripts/validate_project_artifacts.py` and loop health checks in `scripts/project_doctor.py`.
- `product:loop` and `product:status` docs updated for the goal-aware loop surface.
- Updated ModuFlow state, dashboard, roadmap, and templates for the 019 loop model.

## Verification

- `python3 -m unittest tests.test_project_loop -v` passed (9 tests).
- `python3 -m unittest tests.test_validation_distribution -v` passed (9 tests).
- `python3 -m unittest discover -s tests -v` passed.
- `python3 scripts/validate_project_artifacts.py .` passed.
- `python3 scripts/validate_moduflow.py .` passed.
- `python3 scripts/release_check.py .` passed.

## Rollback

Return to the previous known-good `0.2.6` source checkout before `scripts/project_loop.py` and `workspace/loop-state.json` v2 were introduced, then reinstall `moduflow@personal`.

## Post-Release Checks

- Re-register the personal marketplace entry.
- Refresh the Codex plugin cachebuster.
- Reinstall or update `moduflow@personal`.
- Start a new Codex thread and confirm `@ModuFlow status` or `@ModuFlow product:status` shows issue 020 as next.
