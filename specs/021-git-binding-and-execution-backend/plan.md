# Git Binding And Execution Backend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bind ModuFlow loop progress to issue-named Git branches, commit/PR/release references, and explicit execution backend recommendations.

**Architecture:** Keep Git as evidence inside `workspace/loop-state.json`; expose small helper functions in `scripts/project_loop.py`; let doctor and project validation read those helpers. Command docs explain backend routing without creating remote automation.

**Tech Stack:** Python standard library, unittest, Markdown/JSON ModuFlow artifacts.

---

### Task 1: Loop Git Binding Helpers

**Files:**
- Modify: `scripts/project_loop.py`
- Test: `tests/test_project_loop.py`

- [x] Write failing tests for issue branch recommendation, git binding normalization, declared branch mismatch, and high-risk backend recommendation.
- [x] Run focused tests and confirm they fail because helpers and fields are missing.
- [x] Implement `recommend_issue_branch`, `branch_matches_issue`, `normalize_git_binding`, `normalize_execution_backend`, `recommend_execution_backend`, and `validate_git_binding_for_issue`.
- [x] Run focused tests and confirm they pass.

### Task 2: Doctor Git Binding Output

**Files:**
- Modify: `scripts/project_doctor.py`

- [x] Add current branch discovery with `git rev-parse --abbrev-ref HEAD`.
- [x] Include declared `git_binding` in doctor output.
- [x] Recommend switching or updating loop state when current branch does not match active issue on non-neutral branches.

### Task 3: Artifact And Command Documentation

**Files:**
- Create: `specs/021-git-binding-and-execution-backend/spec.md`
- Create: `specs/021-git-binding-and-execution-backend/plan.md`
- Create: `specs/021-git-binding-and-execution-backend/tasks.md`
- Create: `specs/021-git-binding-and-execution-backend/release.md`
- Modify: `commands/product-execute.md`
- Modify: `commands/product-loop.md`
- Modify: `templates/workspace/loop-state.json`

- [x] Document branch naming, loop-state binding, backend recommendation, and validation rules.
- [x] Update command docs so `product:execute` recommends/records backend choice.
- [x] Update loop-state template with `git_binding`.

### Task 4: State And Release Readiness

**Files:**
- Modify: `issues/021-git-binding-and-execution-backend.md`
- Modify: `.moduflow/state.json`
- Modify: `workspace/loop-state.json`
- Modify: `workspace/dashboard.md`
- Modify: `workspace/roadmap.md`

- [x] Mark 021 workflow tasks complete after verification.
- [x] Advance active issue cursor to `022-intake-to-goal-graph`.
- [x] Remove duplicate `## Now` heading from roadmap.
- [x] Run full tests and ModuFlow validation gates.
