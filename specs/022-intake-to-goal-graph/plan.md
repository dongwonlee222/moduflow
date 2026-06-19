# Intake To Goal Graph Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Route loose user requests into active issue attachments, new issue candidates, or goal-linked issue graphs.

**Architecture:** Add a focused Python standard-library router in `scripts/project_intake.py`. Keep routing deterministic and reviewable, with safe writes limited to `workspace/inbox.md`.

**Tech Stack:** Python standard library, unittest, Markdown/JSON ModuFlow artifacts.

---

### Task 1: Intake Router Tests

**Files:**
- Create: `tests/test_project_intake.py`

- [x] Write failing tests for dev/business classification.
- [x] Write failing tests for Korean request to English issue related matching.
- [x] Write failing tests for active issue attachment.
- [x] Write failing tests for large request splitting.
- [x] Write failing tests for inbox write mode.
- [x] Run focused tests and confirm they fail because `scripts/project_intake.py` is missing.

### Task 2: Deterministic Router

**Files:**
- Create: `scripts/project_intake.py`

- [x] Implement `classify_request`.
- [x] Implement tokenization and bilingual aliases.
- [x] Implement `find_related_issues`.
- [x] Implement `split_issue_candidates`.
- [x] Implement `route_intake`.
- [x] Implement `--write` inbox append mode.
- [x] Run focused tests and confirm they pass.

### Task 3: Command And Skill Documentation

**Files:**
- Modify: `commands/moduflow.md`
- Modify: `commands/product-loop.md`
- Modify: `commands/product-inbox.md`
- Modify: `skills/index/SKILL.md`
- Modify: `skills/pm-execution-router/SKILL.md`

- [x] Document that `이거 해줘` uses the intake router semantics.
- [x] Document that large requests become goal plus issue candidates.
- [x] Document inbox JSON routing records.

### Task 4: State And Release Readiness

**Files:**
- Modify: `issues/022-intake-to-goal-graph.md`
- Create: `specs/022-intake-to-goal-graph/tasks.md`
- Create: `specs/022-intake-to-goal-graph/status.md`
- Create: `specs/022-intake-to-goal-graph/release.md`
- Modify: `.moduflow/state.json`
- Modify: `workspace/loop-state.json`
- Modify: `workspace/dashboard.md`
- Modify: `workspace/roadmap.md`

- [x] Mark 022 workflow tasks complete after verification.
- [x] Advance active issue cursor to `023-worker-routing-and-isolation`.
- [x] Run full tests and ModuFlow validation gates.
