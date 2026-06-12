# Portfolio Workspace Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a central portfolio workspace for summarizing multiple ModuFlow projects.

**Architecture:** Add a Python script that initializes a portfolio workspace, reads a JSON project registry, collects project-local state/profile data, and renders Markdown dashboard/weekly summaries. Keep writes limited to the portfolio workspace.

**Tech Stack:** Python standard library, JSON, Markdown, unittest.

---

## File Structure

- Create `scripts/project_portfolio.py`: workspace initialization, registry loading, status collection, dashboard rendering.
- Create `tests/test_project_portfolio.py`: TDD coverage.
- Create `templates/portfolio/projects.json`, `portfolio-dashboard.md`, `portfolio-roadmap.md`, and `weekly-status.md`.
- Create `commands/product-portfolio.md`, `product-projects.md`, and `product-weekly.md`.
- Modify `README.md`, `skills/index/SKILL.md`, `skills/pm-execution-router/SKILL.md`, `scripts/validate_moduflow.py`.

### Task 1: Portfolio Tests

- [ ] Write failing tests for workspace dry-run/write, project status collection, and dashboard rendering.
- [ ] Run `python3 -m unittest tests.test_project_portfolio -v` and confirm missing module failure.

### Task 2: Portfolio Script

- [ ] Implement workspace plan/write helpers.
- [ ] Implement registry loading and project status collection.
- [ ] Implement dashboard rendering.
- [ ] Re-run tests and confirm pass.

### Task 3: Commands And Templates

- [ ] Add command docs and templates.
- [ ] Update README, skills, and validator.
- [ ] Run validator.

### Task 4: Verification

- [ ] Run all tests.
- [ ] Run portfolio dry-run/write against a temporary workspace.
- [ ] Create ModuFlow repo portfolio sample.
- [ ] Update status evidence.
- [ ] Commit and push.

## Self-Review

- Spec coverage: registry, status collection, dashboard rendering, commands, templates, validation, and no-overwrite behavior are covered.
- Placeholder scan: no TBD or TODO placeholders.
- Type consistency: script APIs use dict plans and JSON-serializable data.
