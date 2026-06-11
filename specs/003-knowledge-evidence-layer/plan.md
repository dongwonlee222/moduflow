# Knowledge Evidence Layer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Git-native knowledge artifacts for decisions, benchmarks, reports, research, data notes, and references.

**Architecture:** Add a small Python script that plans/creates missing knowledge structure and individual artifacts. Extend doctor for readiness checks, add Markdown command docs, and keep templates in `templates/knowledge/`.

**Tech Stack:** Python standard library, Markdown, JSON, unittest.

---

## File Structure

- Create `scripts/project_knowledge.py`: dry-run/write initialization and artifact creation.
- Modify `scripts/project_doctor.py`: knowledge missing checks.
- Create `tests/test_project_knowledge.py`: TDD coverage.
- Create `templates/knowledge/*.md`: artifact templates.
- Create `commands/product-knowledge.md`, `product-decision.md`, `product-research.md`, `product-benchmark.md`, `product-report.md`, and `product-evidence.md`.
- Modify `README.md`, `skills/index/SKILL.md`, `skills/pm-execution-router/SKILL.md`, and `scripts/validate_moduflow.py`.

### Task 1: Knowledge Tests

- [ ] Write failing tests for dry-run initialization, write mode, artifact creation, and doctor reporting.
- [ ] Run `python3 -m unittest tests.test_project_knowledge -v` and confirm missing module/function failures.

### Task 2: Knowledge Script

- [ ] Implement `build_knowledge_plan()`, `apply_knowledge_plan()`, and `create_knowledge_artifact()`.
- [ ] Re-run tests and confirm pass.

### Task 3: Doctor Integration

- [ ] Add `missing_knowledge_paths()` and `knowledge` status to doctor output.
- [ ] Re-run tests and confirm pass.

### Task 4: Commands And Templates

- [ ] Add command docs and templates.
- [ ] Update README, skills, and validator.
- [ ] Run validator.

### Task 5: Verification

- [ ] Run all tests.
- [ ] Run knowledge dry-run/write against a temporary project.
- [ ] Initialize ModuFlow repo knowledge layer with `--write`.
- [ ] Update status evidence.
- [ ] Commit and push.

## Self-Review

- Spec coverage: initialization, artifact creation, doctor checks, command docs, templates, and validation are covered.
- Placeholder scan: no TBD or TODO placeholders.
- Type consistency: script plans are JSON-serializable dictionaries.
