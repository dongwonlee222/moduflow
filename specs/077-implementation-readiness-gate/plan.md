# Implementation Readiness Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a report-only implementation-readiness gate before `product:execute`.

**Architecture:** Extend the existing `scripts/project_execution.py` helper with deterministic readiness analysis and a `--readiness` CLI mode that can write `specs/<issue>/implementation-readiness.json`. Teach `project_loop.py` to read that artifact and route `not_ready` execute-phase issues back to `product:plan`. Keep command and skill docs aligned with the report-only v1 behavior.

**Tech Stack:** Python standard library, unittest, Markdown command docs, ModuFlow Git-native artifacts.

---

## Global Constraints

Constitution v1.0 applies (`workspace/constitution.md`). Plan-specific additions:

- v1 readiness is report-only; do not hard-block all execution.
- Frontend-specific checks must be conditional and can return `not_applicable`.
- The machine-readable artifact path is `specs/<issue>/implementation-readiness.json`.
- Do not add reusable Storybook/MSW/Playwright templates in this issue; that belongs to 078.
- Keep all new behavior deterministic and locally testable.

## Recommended Discipline

| Stream | Discipline / Adapter | Reason |
| --- | --- | --- |
| A — readiness checker | Superpowers TDD + focused unittest | New routing/checker behavior needs RED/GREEN coverage. |
| B — loop routing | Superpowers TDD + ModuFlow PM router | `product:loop` must route severe readiness gaps back to planning. |
| C — command docs | writing-plans + review | Human-facing command guidance must match implemented behavior. |
| D — verification | verification-before-completion | Completion claims need fresh validation and release-check evidence. |

## File Structure

- Modify `scripts/project_execution.py`: add readiness dimensions, plan/spec/status text inspection, result builder, JSON writer, and CLI flags.
- Modify `tests/test_project_execution.py`: cover ready, warning/not-ready, frontend conditional checks, and JSON write behavior.
- Modify `scripts/project_loop.py`: load latest readiness artifact and recommend `product:plan` when an execute-phase issue is `not_ready`.
- Modify `tests/test_project_loop.py`: cover readiness-aware execute routing.
- Modify `commands/product-execute.md`: add readiness preflight before worker dispatch.
- Modify `commands/product-plan.md`: add readiness evidence guidance after the discipline matrix.
- Modify `commands/product-loop.md`: document readiness-aware routing.
- Modify `skills/superpowers-execution-bridge/SKILL.md`: connect readiness to execution discipline.
- Update `issues/077-implementation-readiness-gate.md`, `specs/077-implementation-readiness-gate/tasks.md`, `status.md`, and `workspace/roadmap.md`.

## Interfaces

- `project_execution.build_implementation_readiness(root, issue_id)` returns a dict:

```python
{
    "schema": "moduflow.implementation-readiness.v1",
    "issue_id": issue_id,
    "status": "ready|warning|not_ready",
    "mode": "report-only",
    "checks": [
        {
            "id": "api_contract",
            "state": "pass|warn|fail|not_applicable",
            "severity": "low|medium|high",
            "evidence": "...",
            "gap": "...",
            "recommendation": "..."
        }
    ],
    "next_command": "product:execute <issue>" or "product:plan <issue>"
}
```

- `project_execution.write_implementation_readiness(root, issue_id)` writes `specs/<issue>/implementation-readiness.json`.
- `project_loop.load_implementation_readiness(root, issue_id)` returns the JSON dict or `None`.
- `project_loop.recommend_loop(root)` sets `next_command` to `product:plan <issue>` when phase is `execute` and readiness status is `not_ready`.

### Task 1: Readiness Checker

**Files:**
- Modify: `scripts/project_execution.py`
- Modify: `tests/test_project_execution.py`

- [ ] **Step 1: Write failing tests for readiness states**

Add tests that create temporary issue/spec/plan/status files:

```python
def test_build_implementation_readiness_returns_ready_for_explicit_contracts(self):
    # spec says API-backed UI and permission model are in scope.
    # plan includes API contract, test strategy, Storybook states,
    # MSW fixtures, Playwright smoke matrix, roles, and rollback check.
    # assert status == "ready" and api_contract state == "pass".
```

```python
def test_build_implementation_readiness_reports_not_ready_for_missing_high_severity_contracts(self):
    # spec says API-backed UI with admin roles.
    # plan only says "implement UI".
    # assert status == "not_ready", next_command == "product:plan <issue>",
    # and failed checks include api_contract and test_strategy.
```

```python
def test_build_implementation_readiness_marks_frontend_checks_not_applicable_for_docs_only_work(self):
    # spec and plan describe docs-only command guidance.
    # assert storybook_states, msw_fixtures, and playwright_smoke are not_applicable.
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
python3 -m unittest tests.test_project_execution -v
```

Expected: readiness tests fail because the functions do not exist.

- [ ] **Step 3: Implement readiness builder**

Add deterministic keyword-based checks in `scripts/project_execution.py`.

Minimum behavior:

- Read `issues/<issue>.md`, `specs/<issue>/spec.md`, `plan.md`, `tasks.md`, and `status.md`.
- Detect scope from text:
  - UI/frontend scope: `ui`, `frontend`, `component`, `screen`, `storybook`, `browser`, `playwright`.
  - API scope: `api`, `endpoint`, `request`, `response`, `integration`, `msw`.
  - permission scope: `permission`, `role`, `auth`, `admin`, `access control`.
- Check evidence in plan/status/spec text for each dimension.
- Return `fail` high severity for missing API contract or test strategy when relevant.
- Return `warn` medium severity for missing frontend QA evidence when frontend/API-backed browser scope is relevant.
- Return `not_applicable` when the dimension is not in scope.
- Set overall status:
  - any high `fail` -> `not_ready`
  - any `warn` or medium `fail` -> `warning`
  - otherwise -> `ready`

- [ ] **Step 4: Run tests to verify pass**

Run:

```bash
python3 -m unittest tests.test_project_execution -v
```

Expected: all `ProjectExecutionHandoffTests` pass.

### Task 2: Readiness CLI And Artifact Write

**Files:**
- Modify: `scripts/project_execution.py`
- Modify: `tests/test_project_execution.py`

- [ ] **Step 1: Write failing write/CLI tests**

Add a test:

```python
def test_write_implementation_readiness_creates_json_artifact(self):
    # create minimal ready temp issue artifacts
    # call project_execution.write_implementation_readiness(root, issue_id)
    # assert path == specs/<issue>/implementation-readiness.json
    # assert JSON schema == moduflow.implementation-readiness.v1
```

- [ ] **Step 2: Implement writer and CLI flags**

Extend `main()` so:

```bash
python3 scripts/project_execution.py . --issue-id 077-implementation-readiness-gate --readiness
```

prints JSON, and:

```bash
python3 scripts/project_execution.py . --issue-id 077-implementation-readiness-gate --readiness --write
```

writes `implementation-readiness.json` and prints its path.

Keep existing `--review-handoff --write` behavior unchanged.

- [ ] **Step 3: Run targeted tests**

Run:

```bash
python3 -m unittest tests.test_project_execution -v
```

Expected: pass.

### Task 3: Loop Routing

**Files:**
- Modify: `scripts/project_loop.py`
- Modify: `tests/test_project_loop.py`

- [ ] **Step 1: Write failing loop routing test**

Add a test that creates:

- issue with spec and plan checked, execute pending
- `specs/<issue>/implementation-readiness.json` with `status: "not_ready"`
- loop state pointing to that issue

Assert:

```python
self.assertEqual(result["phase"], "plan")
self.assertEqual(result["next_command"], f"product:plan {issue_id}")
self.assertEqual(result["status"], "needs_decision")
self.assertIn("Implementation readiness is not_ready", result["blocker"])
```

- [ ] **Step 2: Implement readiness-aware routing**

In `project_loop.py`:

- Add `implementation_readiness_path(root, issue_id)`.
- Add `load_implementation_readiness(root, issue_id)`.
- In `recommend_loop`, after inferring `phase`, if phase is `execute` and readiness status is `not_ready`, set:
  - `phase`: `plan`
  - `status`: `needs_decision`
  - `blocker`: `Implementation readiness is not_ready; return to product:plan before execution.`
  - `next_command`: `product:plan <issue>`

- [ ] **Step 3: Run loop tests**

Run:

```bash
python3 -m unittest tests.test_project_loop -v
```

Expected: pass.

### Task 4: Command And Skill Guidance

**Files:**
- Modify: `commands/product-execute.md`
- Modify: `commands/product-plan.md`
- Modify: `commands/product-loop.md`
- Modify: `skills/superpowers-execution-bridge/SKILL.md`

- [ ] **Step 1: Update `product:execute`**

Add readiness preflight before worker-plan generation:

```bash
python3 scripts/project_execution.py . --issue-id <id> --readiness --write
```

State that `not_ready` recommends `product:plan <id>` and requires explicit user approval to continue in v1.

- [ ] **Step 2: Update `product:plan`**

After the `Recommended Discipline` guidance, add a short `Implementation Readiness Inputs` note requiring plans to state applicable contracts or explicit not-applicable reasons.

- [ ] **Step 3: Update `product:loop`**

Document that execute-phase issues with `implementation-readiness.json` status `not_ready` route back to `product:plan`.

- [ ] **Step 4: Update Superpowers bridge**

Add a short section explaining that readiness is the execution handoff check and remains report-only in v1.

### Task 5: Dogfood 077 And Verify

**Files:**
- Create: `specs/077-implementation-readiness-gate/implementation-readiness.json`
- Modify: `specs/077-implementation-readiness-gate/tasks.md`
- Modify: `specs/077-implementation-readiness-gate/status.md`
- Modify: `issues/077-implementation-readiness-gate.md`
- Modify: `workspace/roadmap.md`

- [ ] **Step 1: Generate readiness for 077**

Run:

```bash
python3 scripts/project_execution.py . --issue-id 077-implementation-readiness-gate --readiness --write
```

Expected: `implementation-readiness.json` exists. For this issue, API/frontend permission checks may be `not_applicable`; test strategy and release/rollback verification should pass or warn based on the plan.

- [ ] **Step 2: Run consistency and validation**

Run:

```bash
python3 scripts/spec_consistency.py . --issue-id 077-implementation-readiness-gate
python3 scripts/validate_moduflow.py .
python3 scripts/validate_project_artifacts.py .
python3 scripts/release_check.py .
```

Expected: no errors. Warn/info findings are acceptable only if recorded in `status.md`.

- [ ] **Step 3: Update status and issue checklist**

Mark plan and execute tasks as appropriate after implementation, record verification commands, and set next command to `product:review 077-implementation-readiness-gate`.

