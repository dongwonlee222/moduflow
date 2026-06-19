# Spec: Real Subagent Execution Backend (Issue 028)

## Issue

`028-real-subagent-execution-backend`

## Owner

Dongwon Lee

## Phase

spec

## Problem

ModuFlow currently orchestrates tasks through a static `worker_orchestrator.py` which outputs JSON plans and recommends manual task execution or simulates workers. This does not take advantage of advanced execution hosts like Antigravity, which can launch actual parallel coding agents using `invoke_subagent` to do work concurrently.

## Goals

- Introduce `host-subagent` as a first-class execution backend in `scripts/project_loop.py` and `scripts/worker_orchestrator.py`.
- Map worker plan tasks to structured subagent configs compatible with Antigravity's `invoke_subagent` (specifying `TypeName`, `Role`, `Workspace`, and `Prompt`).
- Provide an adapter/guidance in the execution phase showing the agent exactly how to invoke subagents for ready tasks.
- Maintain compatibility with existing manual and `codex` backends when `invoke_subagent` is not available.

## Design

### 1. Loop State & Backend Configuration
In `scripts/project_loop.py`, `EXECUTION_BACKENDS` is updated to include `"host-subagent"`:
```python
EXECUTION_BACKENDS = {"codex", "claude-code", "copilot-cloud-agent", "openhands", "manual", "host-subagent"}
```

In `git_binding.execution_backend`, if the active environment supports subagents (detected via presence of the `invoke_subagent` tool or explicitly configured), the backend type will be recommended as `"host-subagent"`.

### 2. Worker Plan Mapping
In `scripts/worker_orchestrator.py`, each task in the worker plan will generate a `subagent` config block:
```json
"subagent": {
  "TypeName": "self",
  "Role": "ModuFlow worker-name",
  "Workspace": "share",
  "Prompt": "Implement task: ... expected files: ..."
}
```

- **Workspace Mode**: Defaults to `"share"` (shares the underlying repo directory using git worktree style) to match ModuFlow's existing worktree isolation design, or `"branch"` for isolated clones.
- **Prompt Structure**: Formatted with clear task objectives, dependencies, and file scopes.

### 3. Execution Integration
When `/product:execute` is run and `execution_backend` is `"host-subagent"`, the command output will render a structured instruction card:

```text
╭─ 🚀 ModuFlow Subagent Dispatch ────────────────────────╮
│ Task: T01 (implementation-worker)                       │
│ Type: self                                             │
│ Workspace: share                                        │
│ Command: Please call invoke_subagent for T01           │
╰────────────────────────────────────────────────────────╯
```
This signals the host agent to make the tool call for the ready tasks.

## Acceptance Criteria

- `host-subagent` is recognized as a valid execution backend.
- ModuFlow generates structured `subagent` metadata for tasks in `worker-plan.json`.
- All tests pass cleanly, verifying that the new backend type is supported and schema validated.
