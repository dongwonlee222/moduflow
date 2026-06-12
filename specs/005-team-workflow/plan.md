# Team Workflow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add team workflow artifacts for states, roles, review gates, approval policy, risks, and handoff.

**Architecture:** Add a focused Python script that initializes workflow policy files and appends or creates workflow records. Extend doctor for readiness checks, add command docs, and keep templates in `templates/workflow/`.

**Tech Stack:** Python standard library, Markdown, unittest.

---

## File Structure

- Create `scripts/project_workflow.py`: workflow initialization and record creation.
- Modify `scripts/project_doctor.py`: workflow missing checks.
- Create `tests/test_project_workflow.py`: TDD coverage.
- Create `templates/workflow/*.md`: workflow templates.
- Create `commands/product-handoff.md` and `commands/product-risks.md`.
- Modify `README.md`, `skills/index/SKILL.md`, `skills/pm-execution-router/SKILL.md`, and `scripts/validate_moduflow.py`.

### Task 1: Workflow Tests

- [ ] Write failing tests for dry-run initialization, write mode, no overwrite, record creation, and doctor reporting.
- [ ] Run `python3 -m unittest tests.test_project_workflow -v` and confirm missing module/function failures.

### Task 2: Workflow Script

- [ ] Implement `build_workflow_plan()`, `apply_workflow_plan()`, and `create_workflow_record()`.
- [ ] Re-run tests and confirm pass.

### Task 3: Doctor Integration

- [ ] Add `missing_workflow_paths()` and `workflow` status to doctor output.
- [ ] Re-run tests and confirm pass.

### Task 4: Commands And Templates

- [ ] Add command docs and workflow templates.
- [ ] Update README, skills, and validator.
- [ ] Run validator.

### Task 5: Verification

- [ ] Run all tests.
- [ ] Run workflow dry-run/write against a temporary project.
- [ ] Initialize ModuFlow repo workflow structure with `--write`.
- [ ] Update status evidence.
- [ ] Commit and push.

## Self-Review

- Spec coverage: states, roles, workflow files, record creation, doctor checks, commands, templates, and validator are covered.
- Placeholder scan: no TBD or TODO placeholders.
- Type consistency: script APIs use JSON-serializable dicts and string fields.
