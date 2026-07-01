# Autonomous Execute Review Visual Handoff Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a tested review handoff artifact so implementation completion automatically leads to subagent review, verification, and dashboard-backed issue inspection.

**Architecture:** Add one focused helper, `scripts/project_execution.py`, that reads Git-native issue/spec artifacts and writes `review-handoff.md`. Keep actual host subagent invocation outside the helper; command docs require the main agent to map the handoff to available subagent tools and regenerate the dashboard plus issue drill-down views.

**Tech Stack:** Python standard library, `unittest`, existing ModuFlow Markdown command docs.

---

### Task 1: RED Tests For Handoff Generation

**Files:**
- Create: `tests/test_project_execution.py`
- Create later: `scripts/project_execution.py`

- [ ] Write tests that build a temp issue with `issue.md`, `spec.md`, `tasks.md`, and `status.md`.
- [ ] Assert the handoff contains implementation, QA, PM/spec review, verification, dashboard path, and issue drill-down path.
- [ ] Run `python3 -m unittest tests.test_project_execution -v` and confirm it fails before implementation.

### Task 2: Implement Handoff Helper

**Files:**
- Create: `scripts/project_execution.py`
- Test: `tests/test_project_execution.py`

- [ ] Implement `build_review_handoff(root, issue_id)`.
- [ ] Implement `write_review_handoff(root, issue_id)`.
- [ ] Add CLI flags `--review-handoff --issue-id <issue> --write`.
- [ ] Run focused tests until green.

### Task 3: Wire Command Docs

**Files:**
- Modify: `commands/product-execute.md`
- Modify: `commands/product-review.md`

- [ ] Add handoff generation to `product:execute` completion.
- [ ] Add review subagent + dashboard/issue drill-down gate to `product:review`.

### Task 4: Update Artifacts And Verify

**Files:**
- Modify: `issues/051-autonomous-execute-review-visual-handoff.md`
- Modify: `specs/051-autonomous-execute-review-visual-handoff/status.md`
- Create: `specs/051-autonomous-execute-review-visual-handoff/review-handoff.md`
- Modify: `workspace/dashboard.md`
- Modify: `workspace/roadmap.md`

- [ ] Generate review handoff for Issue 051.
- [ ] Run `python3 -m unittest tests.test_project_execution -v`.
- [ ] Run `python3 scripts/release_check.py .`.

## Self-Review

- Covers all spec requirements.
- Avoids host-specific subagent API coupling.
- Keeps visual handoff explicit via dashboard and issue drill-down commands/paths.

## Next Command

`product:execute 051-autonomous-execute-review-visual-handoff`
