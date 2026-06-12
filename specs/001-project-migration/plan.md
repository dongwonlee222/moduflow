# Project Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a safe, non-destructive migration planning flow for existing projects.

**Architecture:** Extend `project_doctor.py` with conservative candidate detection and add `project_migrate.py` for dry-run/write migration plans. Keep commands and skills as Markdown routing definitions, while scripts provide machine-checkable behavior.

**Tech Stack:** Python standard library, Markdown command docs, JSON ModuFlow config/state files, Git-backed artifacts.

---

## File Structure

- Modify `scripts/project_doctor.py`: report candidate folders and migration recommendations.
- Create `scripts/project_migrate.py`: generate dry-run plans and optional metadata/index files.
- Create `tests/test_project_migration.py`: unit tests for candidate detection and dry-run/write behavior.
- Create `commands/product-migrate.md`: user-facing migration command.
- Modify `skills/index/SKILL.md`: route `product:migrate`.
- Modify `skills/pm-execution-router/SKILL.md`: route existing-project adoption to migration.
- Modify `README.md`: list `product:migrate`.
- Modify `scripts/validate_moduflow.py`: require migration command/script.
- Update `specs/001-project-migration/status.md`: record verification.

### Task 1: Doctor Candidate Detection

- [ ] Write failing tests for folder candidate detection.
- [ ] Run `python3 -m unittest tests.test_project_migration -v` and confirm the missing function failure.
- [ ] Add `discover_candidate_paths()` and include candidates in doctor JSON.
- [ ] Re-run the unit test and confirm pass.

### Task 2: Migration Planner Script

- [ ] Write failing tests for dry-run and write mode.
- [ ] Run `python3 -m unittest tests.test_project_migration -v` and confirm `project_migrate.py` import failure.
- [ ] Implement `build_migration_plan()` and `apply_migration_plan()`.
- [ ] Re-run the unit test and confirm pass.

### Task 3: Command And Router Docs

- [ ] Add `commands/product-migrate.md`.
- [ ] Update index/router skills and README command list.
- [ ] Update validator required files.
- [ ] Run `python3 scripts/validate_moduflow.py .`.

### Task 4: End-To-End Verification

- [ ] Run `python3 scripts/project_doctor.py .`.
- [ ] Create a temporary existing-project sample with `docs/specs`, `planning`, and `reports`.
- [ ] Run migration dry-run and confirm no files are written.
- [ ] Run migration write mode and confirm only ModuFlow metadata/index files are written.
- [ ] Update status with test evidence.

## Self-Review

- Spec coverage: candidate detection, dry-run, write mode, command docs, validator, and status evidence are covered.
- Placeholder scan: no TODO or TBD placeholders.
- Type consistency: script functions use `Path`, dictionaries, and JSON-serializable values consistently.
