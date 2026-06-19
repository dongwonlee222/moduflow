# Release 022: Intake To Goal Graph

## Summary

Released deterministic intake routing for loose ModuFlow requests. Users can say `이거 해줘: ...`; ModuFlow can classify the request, check for related issues, attach to active work, generate issue candidates, or append a safe inbox record.

## Version

- Target base version: `0.2.9`
- Codex cachebuster version: `0.2.9+codex.20260618153227`

## Verification

- `python3 -m unittest tests.test_project_intake -v` passed.
- `python3 -m unittest discover -s tests -v` passed (57 tests).
- `python3 scripts/validate_project_artifacts.py .` passed.
- `python3 scripts/validate_moduflow.py .` passed (116 required files).
- `python3 scripts/release_check.py .` passed.

## Next

`product:spec 023-worker-routing-and-isolation`
