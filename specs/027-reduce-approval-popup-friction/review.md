# Review: Reduce Approval Popup Friction

## Issue

`027-reduce-approval-popup-friction`

## Decision

Pass. Issue 027 is ready to close as complete.

## What Changed

- Added approval surface mapping for routine validation, local writes, Git reads/writes, GitHub/network calls, account checks, and destructive actions.
- Added `validate_moduflow(root)` as an importable validation API while keeping the CLI wrapper.
- Updated `release_check.py` so safe package/project validation uses importable functions instead of shelling out.
- Split `project_doctor.inspect_project()` into default full preflight and local-only `include_preflight=False` mode.
- Added `scripts/project_doctor.py --no-preflight` for approval-sensitive hosts.
- Added `docs/host-adapter-guidance.md` for shell-free validation, local-only checks, full preflight boundaries, and Antigravity adapter expectations.
- Added resume banner guidance so resumed work shows what was already completed, what is happening now, and what comes next.

## Acceptance Review

- Approval-triggering flows are mapped: pass.
- Local-only workflows can complete without GitHub API prompts: pass.
- Routine validation has importable API paths: pass.
- CLI entrypoints remain available for CLI/CI users: pass.
- Documentation explains expected versus avoidable prompts: pass.
- Risky Git/GitHub/account/destructive operations remain explicit: pass.
- Resumed work shows a concise continuity banner: pass.

## Verification

- `python3 -m unittest tests.test_validation_distribution -v` passed.
- `python3 scripts/project_doctor.py . --no-preflight` passed.
- `python3 scripts/project_doctor.py workspace --no-preflight` passed.
- `python3 scripts/validate_project_artifacts.py .` passed.
- `python3 scripts/validate_moduflow.py .` passed.
- `python3 scripts/release_check.py .` passed.

## Residual Risk

- Antigravity-specific APIs are not verified yet. This is intentionally deferred to `028-real-subagent-execution-backend` and `029-antigravity-artifact-sync-connector`.
- `release_check.py` still uses a subprocess boundary for running tests and project doctor. That is acceptable for CI/release behavior; routine status/doctor/review can now use local-only/importable paths.

## Follow-Up

- Start `028-real-subagent-execution-backend`.
- Keep 029 for Antigravity artifact sync after the execution backend direction is clear.
