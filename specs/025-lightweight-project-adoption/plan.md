# Plan: Lightweight Project Adoption Implementation Plan

Goal: Reduce ModuFlow's footprint in target projects by making commands, scripts, skills, and templates central plugin assets, leaving only durable state and PM artifacts locally.

Architecture: Update `scripts/project_doctor.py`, `scripts/project_migrate.py`, and `scripts/project_intake.py` to support and validate "lightweight mode" vs "dogfooding mode".

Tech Stack: Python standard library, Markdown artifacts, JSON loop state, `unittest`.

---

### Task 1: RED Tests

- [ ] Add unit test in `tests/test_project_profile.py` or `tests/test_validation_distribution.py` verifying that `project_doctor` detects and reports `lightweight` mode.
- [ ] Add unit test verifying that `project_doctor` passes cleanly in lightweight mode without `commands/`, `skills/`, `scripts/`, and `templates/` directories.
- [ ] Add unit test verifying that `project_doctor` still reports errors if required PM files (e.g., `.moduflow/state.json` or `workspace/dashboard.md`) are missing in lightweight mode.
- [ ] Run tests and verify they fail (RED).

### Task 2: Doctor and Migration Updates

- [ ] Modify `scripts/project_doctor.py` to detect `dogfooding` mode vs `lightweight` mode (e.g., by checking if `scripts/validate_moduflow.py` and `vendor.lock.json` exist in the target root).
- [ ] In `project_doctor.py`, skip checking/warning for `commands/`, `skills/`, `scripts/`, and `templates/` folders when in `lightweight` mode.
- [ ] Report the detected mode (`dogfooding` or `lightweight`) in the doctor's JSON output.
- [ ] Modify `scripts/project_migrate.py` and `scripts/project_intake.py` to only copy or initialize the lightweight layout (skip copying `commands/`, `skills/`, `scripts/`, and `templates/`).

### Task 3: Validation and Release

- [ ] Run focused tests: `python3 -m unittest tests.test_validation_distribution -v`.
- [ ] Run full test suite: `python3 -m unittest discover -s tests -v`.
- [ ] Validate project artifacts and moduflow: `python3 scripts/validate_moduflow.py .`
- [ ] Bump version to `0.2.12` and refresh Codex marketplace cache.
