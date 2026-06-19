# Plan: Real Subagent Execution Backend (Issue 028)

Goal: Upgrade ModuFlow worker orchestration from static worker-plan simulation into an optional real subagent execution backend that can dispatch independent work to host-provided coding agents.

Architecture: Update `scripts/project_loop.py` and `scripts/worker_orchestrator.py` to support `host-subagent` as a first-class execution backend.

---

### Task 1: RED Tests

- [ ] Add unit test in `tests/test_project_loop.py` verifying that `"host-subagent"` is recognized as a valid execution backend.
- [ ] Add unit test in `tests/test_worker_orchestration.py` verifying that generated worker plan contains structured `subagent` config blocks for each task.
- [ ] Run tests and verify they fail (RED).

### Task 2: Implement Loop Backend updates

- [ ] In `scripts/project_loop.py`, add `"host-subagent"` to `EXECUTION_BACKENDS`.
- [ ] In `scripts/project_loop.py`, update `recommend_execution_backend` to recommend `"host-subagent"` under appropriate criteria (e.g., code task when host supports subagents).

### Task 3: Implement Worker Plan Mapping

- [ ] In `scripts/worker_orchestrator.py`, update `build_worker_plan` to inject the `subagent` config block for each task, specifying:
  - `TypeName`: `"self"` (inherits workspace & tools)
  - `Role`: maps to task's worker name (e.g. `"implementation-worker"`)
  - `Workspace`: `"share"`
  - `Prompt`: structured instructions with files, objectives, and merge targets.

### Task 4: UI & Execute Command updates

- [ ] Update `commands/product-execute.md` with instructions on how to dispatch tasks to the host subagent.
- [ ] Verify execution outputs when loop backend is set to `host-subagent`.

### Task 5: Verification & Release

- [ ] Run focused tests: `python3 -m unittest tests.test_project_loop tests.test_worker_orchestration -v`.
- [ ] Run full test suite: `python3 -m unittest discover -s tests -v`.
- [ ] Run validation suite: `python3 scripts/validate_moduflow.py .`.
- [ ] Release issue 028.
