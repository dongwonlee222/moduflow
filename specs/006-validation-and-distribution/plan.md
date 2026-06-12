# Validation And Distribution Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add validation and release tooling for shared ModuFlow plugin use.

**Architecture:** Add focused Python scripts for project artifact validation, portfolio validation, and release checks. Keep each script JSON-producing and testable, then document release/upgrade steps.

**Tech Stack:** Python standard library, unittest, JSON, Markdown.

---

## File Structure

- Create `scripts/validate_project_artifacts.py`: validate project-local ModuFlow artifacts.
- Create `scripts/portfolio_doctor.py`: validate portfolio registry and project references.
- Create `scripts/release_check.py`: run package/project/test/doc checks.
- Create `tests/test_validation_distribution.py`: TDD coverage.
- Create `docs/release-checklist.md` and `docs/upgrade-guide.md`.
- Modify `commands/product-doctor.md`, `commands/product-release.md`, `commands/product-sync.md`, `README.md`, and `scripts/validate_moduflow.py`.

### Task 1: Validation Tests

- [ ] Write failing tests for project artifact validation, portfolio warnings, and release check success.
- [ ] Run `python3 -m unittest tests.test_validation_distribution -v` and confirm missing module failures.

### Task 2: Project Artifact Validator

- [ ] Implement `validate_project()`.
- [ ] Re-run tests and confirm project validation cases pass.

### Task 3: Portfolio Doctor

- [ ] Implement `inspect_portfolio()`.
- [ ] Re-run tests and confirm portfolio warning cases pass.

### Task 4: Release Check

- [ ] Implement `run_release_check()`.
- [ ] Re-run tests and confirm release check cases pass.

### Task 5: Docs And Command Updates

- [ ] Add release checklist and upgrade guide.
- [ ] Update command docs and package validator.
- [ ] Run all tests and validators.
- [ ] Update status evidence.
- [ ] Commit and push.

## Self-Review

- Spec coverage: project validation, portfolio validation, release check, docs, and validator requirements are covered.
- Placeholder scan: no TBD or TODO placeholders.
- Type consistency: scripts expose JSON-serializable result dictionaries.
