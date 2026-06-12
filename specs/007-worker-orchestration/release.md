# Release: Worker Orchestration

Issue: `007-worker-orchestration`

## Version

`0.2.0`

## Summary

Adds explicit worker planning for ModuFlow issue execution.

## Included

- `product:workers` command.
- Worker plan generation from `specs/<issue>/tasks.md`.
- Issue-local `worker-plan.json` and `worker-plan.md` artifacts.
- Parallel eligibility and shared-state risk checks.
- `product:execute` documentation connected to worker plans.
- Release check coverage for worker orchestration tests.

## Verification

- `python3 -m unittest discover -s tests -v`
- `python3 scripts/validate_moduflow.py .`
- `python3 scripts/release_check.py .`
- `python3 scripts/validate_project_artifacts.py .`
- `python3 scripts/portfolio_doctor.py portfolio`

## Rollback

Return to commit `b8d3613` or the previous known-good tag/source checkout, then reinstall `moduflow@personal`.

## Post-Release Checks

- Re-register the personal marketplace entry.
- Refresh the Codex plugin cachebuster.
- Reinstall or update `moduflow@personal`.
- Start a new Codex thread and confirm `@ModuFlow product:status` routes to the updated plugin.
