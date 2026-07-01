# Draft PR Review Handoff Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Draft PR / PR-ready state the early human review surface while keeping review evidence and dashboard paths synchronized.

**Architecture:** Add `scripts/project_pr.py` as a focused PR handoff generator. Keep GitHub writes outside the helper; command docs decide whether to create a Draft PR or record a local marker. `product:review` refreshes the same PR handoff after verification.

**Tech Stack:** Python standard library, `unittest`, existing ModuFlow Markdown command docs.

---

### Task 1: RED Tests For PR Handoff

**Files:**
- Create: `tests/test_project_pr.py`
- Create later: `scripts/project_pr.py`

- [x] Write tests that build a temp issue/spec/status set.
- [x] Assert the handoff includes Draft PR, branch, PR marker, reviewer, review commands, dashboard paths, required status checks, and human approval.
- [x] Run `python3 -m unittest tests.test_project_pr -v` and confirm it fails before implementation.

### Task 2: Implement PR Handoff Helper

**Files:**
- Create: `scripts/project_pr.py`
- Test: `tests/test_project_pr.py`

- [x] Implement `build_pr_handoff(root, issue_id, branch, pr, reviewer)`.
- [x] Implement `write_pr_handoff(root, issue_id, branch, pr, reviewer)`.
- [x] Add CLI flags `--issue-id`, `--branch`, `--pr`, `--reviewer`, and `--write`.
- [x] Run focused tests until green.

### Task 3: Wire Command Docs

**Files:**
- Modify: `commands/product-execute.md`
- Modify: `commands/product-review.md`
- Modify: `commands/product-pr.md`

- [x] Add early Draft PR / PR-ready guidance to `product:execute`.
- [x] Add PR evidence refresh gate to `product:review`.
- [x] Make `product:pr` generate/refresh `specs/<issue>/pr.md`.

### Task 4: Update Artifacts And Verify

**Files:**
- Create: `issues/052-draft-pr-review-handoff.md`
- Create: `specs/052-draft-pr-review-handoff/status.md`
- Create: `specs/052-draft-pr-review-handoff/pr.md`
- Create: `specs/052-draft-pr-review-handoff/review.md`
- Modify: `workspace/dashboard.md`
- Modify: `workspace/roadmap.md`

- [x] Generate PR handoff for Issue 052.
- [x] Run `python3 -m unittest tests.test_project_pr -v`.
- [x] Run `python3 scripts/release_check.py .`.

## Self-Review

- Covers all spec requirements.
- Keeps GitHub writes optional and human-gated.
- Makes PR timing explicit without implying merge approval.

## Next Command

`product:status`
