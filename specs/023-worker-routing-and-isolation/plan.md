# Worker Routing And Isolation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make worker plans deterministic and safe by routing ambiguous tasks predictably and using file/dependency isolation before recommending parallel execution.

**Architecture:** Extend the existing `scripts/worker_orchestrator.py` planner rather than adding a second planner. Keep `tasks.md` as the source input, parse small inline metadata, and emit enriched Markdown/JSON worker plans.

**Tech Stack:** Python standard library, Markdown task files, JSON worker plans, `unittest`.

---

### Task 1: Failing Routing And Isolation Tests

**Files:**
- Modify: `tests/test_worker_orchestration.py`

- [x] Add tests proving `acceptance verification` routes to `qa-reviewer`.
- [x] Add tests proving duplicate `[files: ...]` metadata forces sequential mode.
- [x] Add tests proving disjoint file plans include worktree isolation and merge order.
- [x] Add tests proving worker files without routing rules are reported.
- [x] Run `python3 -m unittest tests.test_worker_orchestration -v` and confirm RED.

### Task 2: Worker Planner Implementation

**Files:**
- Modify: `scripts/worker_orchestrator.py`

- [x] Parse inline task metadata for `files`, `globs`, `depends`, and `shared_state`.
- [x] Add explicit prefix routing for `PM:`, `QA:`, `Implementation:`, `Release:`, `Design:`, `Data:`, `Spec:`, and `Roadmap:`.
- [x] Prioritize QA routing for acceptance verification while preserving PM acceptance-criteria routing.
- [x] Add file-overlap risk detection.
- [x] Add worker inventory and dead-worker detection.
- [x] Add per-task isolation worktree names and dependency-aware merge order.
- [x] Run focused worker tests and confirm GREEN.

### Task 3: Docs And Release Artifacts

**Files:**
- Modify: `commands/product-workers.md`
- Modify: `commands/product-execute.md`
- Modify: `README.md`
- Create: `specs/023-worker-routing-and-isolation/status.md`
- Create: `specs/023-worker-routing-and-isolation/release.md`

- [x] Document task metadata syntax.
- [x] Document sequential fallback behavior.
- [x] Generate `worker-plan.json` and `worker-plan.md` for issue 023.

### Task 4: Verification And Version

**Files:**
- Modify: `.claude-plugin/plugin.json`
- Modify: `.codex-plugin/plugin.json`
- Modify: `.moduflow/state.json`
- Modify: `workspace/loop-state.json`
- Modify: `workspace/dashboard.md`
- Modify: `workspace/roadmap.md`

- [x] Run focused worker tests.
- [x] Run full unit tests.
- [x] Run project artifact validation.
- [x] Run plugin validation.
- [x] Run release check.
- [x] Bump plugin version and register the local Codex marketplace cache.
