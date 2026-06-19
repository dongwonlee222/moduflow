# Release: User-Facing Simple Loop UX

Issue: `020-user-facing-simple-loop-ux`

## Version

`0.2.7+codex.20260618122055`

## Summary

Makes the default ModuFlow plugin surface smaller and more natural: `상태`, `다음`, `이거 해줘`, and `완료` now have explicit routing, safety, and output rules while direct `product:*` commands remain available.

## Included

- `/moduflow` hub now defaults to concise status and shows the long command list only on help requests.
- `product:status` defines a short Korean-first status output contract.
- `product:loop` documents read-only `다음` and explicit mutating `다음 실행` / `product:loop --step` behavior.
- ModuFlow routing skills prioritize simple aliases before exposing internal workflow commands.
- README Codex examples lead with the simple command surface.

## Verification

- `rg -n "상태|다음|이거 해줘|완료" commands README.md` confirmed docs coverage.
- `rg -n "active_issue_id|attempts|needs_decision|다음 실행" commands/product-loop.md` confirmed loop-state and one-step docs coverage.
- `rg -n "이거 해줘|완료|다음 실행|guarded|direct.*product" skills/index/SKILL.md skills/pm-execution-router/SKILL.md` confirmed routing skill coverage.
- `python3 -m unittest discover -s tests -v` passed (46 tests).
- `python3 scripts/validate_project_artifacts.py .` passed.
- `python3 scripts/validate_moduflow.py .` passed.
- `python3 scripts/release_check.py .` passed.

## Rollback

Return command docs and routing skills to the previous 0.2.6 source checkout, then reinstall `moduflow@personal`.

## Post-Release Checks

- Refresh the Codex plugin cachebuster.
- Re-register the personal marketplace entry.
- Start a new Codex thread and confirm `@ModuFlow 상태`, `@ModuFlow 다음`, and `@ModuFlow 완료` route as documented.
