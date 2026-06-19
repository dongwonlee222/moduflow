# Release: Git Binding And Execution Backend

Issue: `021-git-binding-and-execution-backend`

## Version

`0.2.8+codex.20260618140719`

## Summary

Binds ModuFlow loop progress to Git evidence: issue-named branches, commit/PR/release references, and explicit execution backend recommendations.

## Included

- `workspace/loop-state.json` supports normalized `git_binding` metadata.
- Default branch recommendation is `codex/<issue-id>`.
- Validation catches declared branch/active issue mismatch.
- Doctor reports current branch and declared Git binding.
- `product:execute` now explains backend recommendation and recording behavior.
- Loop-state template includes Git binding defaults.

## Verification

- Focused issue 021 loop tests passed.
- `python3 -m unittest discover -s tests -v` passed (50 tests).
- `python3 scripts/validate_project_artifacts.py .` passed.
- `python3 scripts/validate_moduflow.py .` passed.
- `python3 scripts/release_check.py .` passed.

## Rollback

Return `scripts/project_loop.py`, `scripts/project_doctor.py`, command docs, and loop-state template to the previous 0.2.7 source checkout, then reinstall `moduflow@personal`.
