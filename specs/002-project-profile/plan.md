# Project Profile Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add safe project profile metadata generation and doctor validation.

**Architecture:** Add focused templates under `templates/profile/`, a Python script that creates missing files only, and doctor support that reports profile readiness. Keep profile data in Git-safe metadata files and explicitly exclude secrets.

**Tech Stack:** Python standard library, JSON, Markdown, unittest, ModuFlow command docs.

---

## File Structure

- Create `templates/profile/project-profile.md`: project context and ownership template.
- Create `templates/profile/environments.json`: dev/staging/prod metadata template.
- Create `templates/profile/integrations.json`: GitHub/docs/chat/analytics integration metadata template.
- Create `scripts/project_profile.py`: dry-run/write profile file creation.
- Modify `scripts/project_doctor.py`: profile missing checks.
- Create `tests/test_project_profile.py`: TDD coverage.
- Create `commands/product-profile.md`: user-facing command.
- Modify `templates/moduflow-config.json`: profile path support.
- Modify `scripts/validate_moduflow.py`: required files.
- Modify `README.md`, `skills/index/SKILL.md`, `skills/pm-execution-router/SKILL.md`.

### Task 1: Profile Tests

- [ ] Write failing tests for dry-run, write mode, no overwrite, and doctor profile reporting.
- [ ] Run `python3 -m unittest tests.test_project_profile -v` and confirm missing module/function failures.

### Task 2: Profile Script

- [ ] Implement `build_profile_plan()` and `apply_profile_plan()`.
- [ ] Re-run profile tests and confirm pass.

### Task 3: Doctor Integration

- [ ] Add profile missing checks to `project_doctor.py`.
- [ ] Re-run profile tests and confirm pass.

### Task 4: Command And Templates

- [ ] Add profile templates and command docs.
- [ ] Update README, skills, config template, and validator.
- [ ] Run validator and doctor.

### Task 5: Verification

- [ ] Run all unittest files.
- [ ] Run profile dry-run/write against a temporary project.
- [ ] Update status evidence.
- [ ] Commit and push.

## Self-Review

- Spec coverage: profile artifacts, dry-run, no overwrite, doctor reporting, sensitive data rules, and validator are covered.
- Placeholder scan: no TBD or TODO placeholders.
- Type consistency: scripts use JSON-serializable dict plans and `Path` internally.
