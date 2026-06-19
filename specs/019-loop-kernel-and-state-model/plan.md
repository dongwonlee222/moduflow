# Loop Kernel And State Model Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first durable ModuFlow loop kernel so a plugin-installed user can ask for status or the next step while ModuFlow tracks active goal, active issue, phase, attempts, blocker, and next command in Git files.

**Architecture:** Add one focused loop module, `scripts/project_loop.py`, that owns loading loop state, normalizing v1/v2 schemas, inferring issue phase, choosing the next command, and applying the repeated-step guard. Existing command markdown stays as UX guidance; validators and doctor import the loop module for consistency checks instead of duplicating logic.

**Tech Stack:** Python standard library, Markdown artifacts, JSON state files, `unittest`, existing ModuFlow release check scripts.

---

Issue: `019-loop-kernel-and-state-model`
Owner / decision maker: Dongwon Lee
Current phase: plan drafted
Next command: `product:execute 019-loop-kernel-and-state-model`
Mode: `git-files`

## File Structure

- Create: `scripts/project_loop.py`
  - Responsibility: pure loop-state and next-command logic. No GitHub writes, no package publishing, no destructive operations.
- Create: `tests/test_project_loop.py`
  - Responsibility: unit tests for v1/v2 state loading, phase inference, next-command routing, attempts guard, and one-step state writes.
- Modify: `scripts/validate_project_artifacts.py`
  - Responsibility: validate optional `workspace/loop-state.json`, active issue references, schema compatibility, and next-command consistency.
- Modify: `scripts/project_doctor.py`
  - Responsibility: report loop state health and drift in doctor output.
- Modify: `commands/product-loop.md`
  - Responsibility: document the concrete v2 state fields, simple user aliases, and stop-state behavior.
- Modify: `commands/product-status.md`
  - Responsibility: render active goal/loop state when present without mutating files.
- Modify: `templates/workspace/loop-state.json`
  - Responsibility: seed v2 loop state while staying readable by v1 fallback logic.
- Modify: `templates/moduflow-state.json`
  - Responsibility: include nullable `active_goal` so project state can point to a goal loop.
- Modify: `specs/019-loop-kernel-and-state-model/status.md`
  - Responsibility: record implementation and verification progress.

## Task 1: Add Loop State Loader And Normalizer

**Files:**
- Create: `scripts/project_loop.py`
- Test: `tests/test_project_loop.py`

- [ ] **Step 1: Write failing tests for v1 and v2 loop-state loading**

Add these tests to `tests/test_project_loop.py`:

```python
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_module(name, relative_path):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


project_loop = load_module("project_loop", "scripts/project_loop.py")


class ProjectLoopTests(unittest.TestCase):
    def test_load_loop_state_reads_v1_issue_id_as_active_issue_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "workspace").mkdir()
            (root / "workspace" / "loop-state.json").write_text(
                json.dumps({
                    "schema": "moduflow.loop-state.v1",
                    "goal_id": "goal-a",
                    "issue_id": "019-loop-kernel-and-state-model",
                    "phase": "goal",
                    "mode": "recommend",
                    "next_command": "product:loop",
                    "attempts": 0,
                    "status": "active",
                }) + "\n",
                encoding="utf-8",
            )

            state = project_loop.load_loop_state(root)

            self.assertEqual(state["schema"], "moduflow.loop-state.v2")
            self.assertEqual(state["goal_id"], "goal-a")
            self.assertEqual(state["issue_ids"], ["019-loop-kernel-and-state-model"])
            self.assertEqual(state["active_issue_id"], "019-loop-kernel-and-state-model")
            self.assertEqual(state["attempts"]["count"], 0)

    def test_load_loop_state_reads_v2_issue_ids_and_active_cursor(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "workspace").mkdir()
            (root / "workspace" / "loop-state.json").write_text(
                json.dumps({
                    "schema": "moduflow.loop-state.v2",
                    "goal_id": "goal-a",
                    "issue_ids": ["019-loop-kernel-and-state-model", "020-user-facing-simple-loop-ux"],
                    "active_issue_id": "020-user-facing-simple-loop-ux",
                    "phase": "spec",
                    "mode": "recommend",
                    "next_command": "product:plan 020-user-facing-simple-loop-ux",
                    "attempts": {"command": "product:plan 020-user-facing-simple-loop-ux", "count": 1, "max": 3},
                    "status": "active",
                }) + "\n",
                encoding="utf-8",
            )

            state = project_loop.load_loop_state(root)

            self.assertEqual(state["issue_ids"], ["019-loop-kernel-and-state-model", "020-user-facing-simple-loop-ux"])
            self.assertEqual(state["active_issue_id"], "020-user-facing-simple-loop-ux")
            self.assertEqual(state["attempts"]["max"], 3)
```

- [ ] **Step 2: Run the failing tests**

Run:

```bash
python3 -m unittest tests.test_project_loop.ProjectLoopTests.test_load_loop_state_reads_v1_issue_id_as_active_issue_id tests.test_project_loop.ProjectLoopTests.test_load_loop_state_reads_v2_issue_ids_and_active_cursor -v
```

Expected before implementation: FAIL with `FileNotFoundError` or import error for `scripts/project_loop.py`.

- [ ] **Step 3: Implement minimal loader and normalizer**

Create `scripts/project_loop.py` with:

```python
#!/usr/bin/env python3
import argparse
import json
from datetime import date
from pathlib import Path

LOOP_STATE_SCHEMA = "moduflow.loop-state.v2"
DEFAULT_MAX_ATTEMPTS = 3
VALID_LOOP_STATUSES = {"active", "needs_decision", "blocked", "done"}
PHASE_ORDER = ["issue", "spec", "plan", "execute", "review", "release", "status"]


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def loop_state_path(root):
    return Path(root).resolve() / "workspace" / "loop-state.json"


def normalize_attempts(raw_attempts, next_command="product:loop"):
    if isinstance(raw_attempts, dict):
        return {
            "command": raw_attempts.get("command") or next_command,
            "count": int(raw_attempts.get("count") or 0),
            "max": int(raw_attempts.get("max") or DEFAULT_MAX_ATTEMPTS),
            "last_changed_at": raw_attempts.get("last_changed_at") or date.today().isoformat(),
        }
    return {
        "command": next_command,
        "count": int(raw_attempts or 0),
        "max": DEFAULT_MAX_ATTEMPTS,
        "last_changed_at": date.today().isoformat(),
    }


def normalize_loop_state(raw):
    next_command = raw.get("next_command") or "product:loop"
    issue_ids = raw.get("issue_ids")
    if not isinstance(issue_ids, list) or not issue_ids:
        issue_id = raw.get("issue_id") or raw.get("active_issue_id")
        issue_ids = [issue_id] if issue_id else []
    active_issue_id = raw.get("active_issue_id") or raw.get("issue_id") or (issue_ids[0] if issue_ids else None)
    status = raw.get("status") or "active"
    if status not in VALID_LOOP_STATUSES:
        status = "active"
    return {
        "schema": LOOP_STATE_SCHEMA,
        "loop_id": raw.get("loop_id") or raw.get("goal_id") or "active-loop",
        "goal_id": raw.get("goal_id") or "active-goal",
        "objective": raw.get("objective") or "",
        "issue_ids": issue_ids,
        "active_issue_id": active_issue_id,
        "phase": raw.get("phase") or "goal",
        "mode": raw.get("mode") or "recommend",
        "status": status,
        "next_command": next_command,
        "attempts": normalize_attempts(raw.get("attempts"), next_command),
        "blocker": raw.get("blocker"),
        "last_action": raw.get("last_action") or "",
        "last_verification": raw.get("last_verification"),
        "updated_at": raw.get("updated_at") or raw.get("updated") or date.today().isoformat(),
    }


def load_loop_state(root):
    path = loop_state_path(root)
    if not path.exists():
        return None
    return normalize_loop_state(read_json(path))
```

- [ ] **Step 4: Run tests to verify loader passes**

Run:

```bash
python3 -m unittest tests.test_project_loop.ProjectLoopTests.test_load_loop_state_reads_v1_issue_id_as_active_issue_id tests.test_project_loop.ProjectLoopTests.test_load_loop_state_reads_v2_issue_ids_and_active_cursor -v
```

Expected: both tests PASS.

## Task 2: Infer Phase And Recommend Next Command

**Files:**
- Modify: `scripts/project_loop.py`
- Modify: `tests/test_project_loop.py`

- [ ] **Step 1: Add tests for phase inference from Workflow Tasks**

Add to `ProjectLoopTests`:

```python
    def test_infer_issue_phase_returns_plan_after_spec_checked(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            issue_dir = root / "issues"
            issue_dir.mkdir()
            (issue_dir / "019-loop-kernel-and-state-model.md").write_text(
                """# Issue 019

## Workflow Tasks

- [x] spec → `specs/019-loop-kernel-and-state-model/spec.md`
- [ ] plan → `specs/019-loop-kernel-and-state-model/plan.md`
- [ ] execute → loop kernel/state model implementation
""",
                encoding="utf-8",
            )
            (root / "specs" / "019-loop-kernel-and-state-model").mkdir(parents=True)
            (root / "specs" / "019-loop-kernel-and-state-model" / "spec.md").write_text("# Spec
", encoding="utf-8")

            phase = project_loop.infer_issue_phase(root, "019-loop-kernel-and-state-model")
            command = project_loop.recommend_next_command("019-loop-kernel-and-state-model", phase)

            self.assertEqual(phase, "plan")
            self.assertEqual(command, "product:plan 019-loop-kernel-and-state-model")

    def test_infer_issue_phase_returns_execute_after_plan_checked(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            issue_dir = root / "issues"
            issue_dir.mkdir()
            (issue_dir / "019-loop-kernel-and-state-model.md").write_text(
                """# Issue 019

## Workflow Tasks

- [x] spec → `specs/019-loop-kernel-and-state-model/spec.md`
- [x] plan → `specs/019-loop-kernel-and-state-model/plan.md`
- [ ] execute → loop kernel/state model implementation
- [ ] review → loop state drift and attempts guard tests
""",
                encoding="utf-8",
            )

            phase = project_loop.infer_issue_phase(root, "019-loop-kernel-and-state-model")
            command = project_loop.recommend_next_command("019-loop-kernel-and-state-model", phase)

            self.assertEqual(phase, "execute")
            self.assertEqual(command, "product:execute 019-loop-kernel-and-state-model")
```

- [ ] **Step 2: Run the new tests and observe failure**

Run:

```bash
python3 -m unittest tests.test_project_loop.ProjectLoopTests.test_infer_issue_phase_returns_plan_after_spec_checked tests.test_project_loop.ProjectLoopTests.test_infer_issue_phase_returns_execute_after_plan_checked -v
```

Expected before implementation: FAIL with missing `infer_issue_phase`.

- [ ] **Step 3: Implement phase and command selection**

Add to `scripts/project_loop.py`:

```python

def issue_path(root, issue_id):
    return Path(root).resolve() / "issues" / f"{issue_id}.md"


def workflow_checkbox_state(issue_text, label):
    checked_pattern = f"- [x] {label}"
    unchecked_pattern = f"- [ ] {label}"
    if checked_pattern in issue_text:
        return "done"
    if unchecked_pattern in issue_text:
        return "pending"
    return "missing"


def infer_issue_phase(root, issue_id):
    path = issue_path(root, issue_id)
    if not path.exists():
        return "issue"
    issue_text = path.read_text(encoding="utf-8")
    for phase in ["spec", "plan", "execute", "review", "release"]:
        if workflow_checkbox_state(issue_text, phase) == "pending":
            return phase
    return "status"


def recommend_next_command(issue_id, phase):
    if phase in {"spec", "plan", "execute", "review", "release"}:
        return f"product:{phase} {issue_id}"
    return "product:status"
```

- [ ] **Step 4: Run tests to verify phase routing passes**

Run:

```bash
python3 -m unittest tests.test_project_loop.ProjectLoopTests.test_infer_issue_phase_returns_plan_after_spec_checked tests.test_project_loop.ProjectLoopTests.test_infer_issue_phase_returns_execute_after_plan_checked -v
```

Expected: both tests PASS.

## Task 3: Add Attempts Guard And Stop State

**Files:**
- Modify: `scripts/project_loop.py`
- Modify: `tests/test_project_loop.py`

- [ ] **Step 1: Add tests for repeated next command guard**

Add to `ProjectLoopTests`:

```python
    def test_attempts_guard_sets_needs_decision_after_repeated_command(self):
        state = {
            "schema": "moduflow.loop-state.v2",
            "goal_id": "goal-a",
            "issue_ids": ["019-loop-kernel-and-state-model"],
            "active_issue_id": "019-loop-kernel-and-state-model",
            "phase": "plan",
            "status": "active",
            "next_command": "product:plan 019-loop-kernel-and-state-model",
            "attempts": {"command": "product:plan 019-loop-kernel-and-state-model", "count": 3, "max": 3},
        }

        updated = project_loop.apply_attempts_guard(state, "product:plan 019-loop-kernel-and-state-model")

        self.assertEqual(updated["status"], "needs_decision")
        self.assertEqual(updated["blocker"], "Repeated next command exceeded max attempts: product:plan 019-loop-kernel-and-state-model")

    def test_attempts_guard_resets_count_for_new_command(self):
        state = {
            "schema": "moduflow.loop-state.v2",
            "goal_id": "goal-a",
            "issue_ids": ["019-loop-kernel-and-state-model"],
            "active_issue_id": "019-loop-kernel-and-state-model",
            "status": "active",
            "next_command": "product:spec 019-loop-kernel-and-state-model",
            "attempts": {"command": "product:spec 019-loop-kernel-and-state-model", "count": 2, "max": 3},
        }

        updated = project_loop.apply_attempts_guard(state, "product:plan 019-loop-kernel-and-state-model")

        self.assertEqual(updated["status"], "active")
        self.assertEqual(updated["attempts"]["count"], 1)
        self.assertEqual(updated["attempts"]["command"], "product:plan 019-loop-kernel-and-state-model")
```

- [ ] **Step 2: Run the new tests and observe failure**

Run:

```bash
python3 -m unittest tests.test_project_loop.ProjectLoopTests.test_attempts_guard_sets_needs_decision_after_repeated_command tests.test_project_loop.ProjectLoopTests.test_attempts_guard_resets_count_for_new_command -v
```

Expected before implementation: FAIL with missing `apply_attempts_guard`.

- [ ] **Step 3: Implement attempts guard**

Add to `scripts/project_loop.py`:

```python

def apply_attempts_guard(state, recommended_command):
    updated = dict(state)
    attempts = normalize_attempts(updated.get("attempts"), updated.get("next_command") or recommended_command)
    if attempts["command"] == recommended_command:
        attempts["count"] += 1
    else:
        attempts = normalize_attempts({"command": recommended_command, "count": 1, "max": attempts["max"]}, recommended_command)
    updated["attempts"] = attempts
    updated["next_command"] = recommended_command
    if attempts["count"] >= attempts["max"]:
        updated["status"] = "needs_decision"
        updated["blocker"] = f"Repeated next command exceeded max attempts: {recommended_command}"
    else:
        updated["status"] = updated.get("status") or "active"
        updated["blocker"] = updated.get("blocker")
    updated["updated_at"] = date.today().isoformat()
    return updated
```

- [ ] **Step 4: Run attempts guard tests**

Run:

```bash
python3 -m unittest tests.test_project_loop.ProjectLoopTests.test_attempts_guard_sets_needs_decision_after_repeated_command tests.test_project_loop.ProjectLoopTests.test_attempts_guard_resets_count_for_new_command -v
```

Expected: both tests PASS.

## Task 4: Add Recommendation Summary And One-Step State Write

**Files:**
- Modify: `scripts/project_loop.py`
- Modify: `tests/test_project_loop.py`

- [ ] **Step 1: Add tests for recommendation and write mode**

Add to `ProjectLoopTests`:

```python
    def test_recommend_loop_reports_active_issue_phase_and_command(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "workspace").mkdir()
            (root / "workspace" / "loop-state.json").write_text(
                json.dumps({
                    "schema": "moduflow.loop-state.v2",
                    "goal_id": "goal-a",
                    "issue_ids": ["019-loop-kernel-and-state-model"],
                    "active_issue_id": "019-loop-kernel-and-state-model",
                    "status": "active",
                    "next_command": "product:spec 019-loop-kernel-and-state-model",
                    "attempts": {"command": "product:spec 019-loop-kernel-and-state-model", "count": 1, "max": 3},
                }) + "\n",
                encoding="utf-8",
            )
            (root / "issues").mkdir()
            (root / "issues" / "019-loop-kernel-and-state-model.md").write_text(
                """# Issue 019

## Workflow Tasks

- [x] spec → `specs/019-loop-kernel-and-state-model/spec.md`
- [ ] plan → `specs/019-loop-kernel-and-state-model/plan.md`
""",
                encoding="utf-8",
            )

            result = project_loop.recommend_loop(root)

            self.assertEqual(result["active_issue_id"], "019-loop-kernel-and-state-model")
            self.assertEqual(result["phase"], "plan")
            self.assertEqual(result["next_command"], "product:plan 019-loop-kernel-and-state-model")
            self.assertEqual(result["status"], "active")

    def test_write_loop_state_persists_v2_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state = project_loop.normalize_loop_state({
                "goal_id": "goal-a",
                "issue_ids": ["019-loop-kernel-and-state-model"],
                "active_issue_id": "019-loop-kernel-and-state-model",
                "next_command": "product:plan 019-loop-kernel-and-state-model",
            })

            project_loop.write_loop_state(root, state)
            saved = json.loads((root / "workspace" / "loop-state.json").read_text(encoding="utf-8"))

            self.assertEqual(saved["schema"], "moduflow.loop-state.v2")
            self.assertEqual(saved["active_issue_id"], "019-loop-kernel-and-state-model")
```

- [ ] **Step 2: Run the new tests and observe failure**

Run:

```bash
python3 -m unittest tests.test_project_loop.ProjectLoopTests.test_recommend_loop_reports_active_issue_phase_and_command tests.test_project_loop.ProjectLoopTests.test_write_loop_state_persists_v2_state -v
```

Expected before implementation: FAIL with missing `recommend_loop` or `write_loop_state`.

- [ ] **Step 3: Implement recommendation and write functions**

Add to `scripts/project_loop.py`:

```python

def default_loop_state(root):
    return normalize_loop_state({
        "goal_id": "active-goal",
        "issue_ids": [],
        "active_issue_id": None,
        "phase": "goal",
        "mode": "recommend",
        "status": "needs_decision",
        "next_command": "product:goal",
        "blocker": "No loop-state.json found",
    })


def recommend_loop(root):
    state = load_loop_state(root) or default_loop_state(root)
    active_issue_id = state.get("active_issue_id")
    if not active_issue_id:
        state["status"] = "needs_decision"
        state["blocker"] = "No active issue selected"
        state["next_command"] = "product:goal"
        return state
    phase = infer_issue_phase(root, active_issue_id)
    command = recommend_next_command(active_issue_id, phase)
    state["phase"] = phase
    state = apply_attempts_guard(state, command)
    return state


def write_loop_state(root, state):
    path = loop_state_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(normalize_loop_state(state), ensure_ascii=False, indent=2) + "
", encoding="utf-8")
    return path
```

- [ ] **Step 4: Run recommendation/write tests**

Run:

```bash
python3 -m unittest tests.test_project_loop.ProjectLoopTests.test_recommend_loop_reports_active_issue_phase_and_command tests.test_project_loop.ProjectLoopTests.test_write_loop_state_persists_v2_state -v
```

Expected: both tests PASS.

## Task 5: Connect CLI, Validator, And Doctor Gates

**Files:**
- Modify: `scripts/project_loop.py`
- Modify: `scripts/validate_project_artifacts.py`
- Modify: `scripts/project_doctor.py`
- Modify: `tests/test_project_loop.py`
- Modify: `tests/test_validation_distribution.py`

- [ ] **Step 1: Add CLI and validation tests**

Add to `tests/test_project_loop.py`:

```python
    def test_validate_loop_state_reports_missing_active_issue_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "workspace").mkdir()
            (root / "workspace" / "loop-state.json").write_text(
                json.dumps({
                    "schema": "moduflow.loop-state.v2",
                    "goal_id": "goal-a",
                    "issue_ids": ["missing-issue"],
                    "active_issue_id": "missing-issue",
                    "next_command": "product:spec missing-issue",
                    "status": "active",
                }) + "\n",
                encoding="utf-8",
            )

            errors = project_loop.validate_loop_state(root)

            self.assertIn("workspace/loop-state.json: active_issue_id missing-issue has no matching issue file", errors)
```

Add to `tests/test_validation_distribution.py`:

```python
    def test_validate_project_artifacts_reports_loop_state_missing_active_issue(self):
        validator = load_module("validate_project_artifacts", "scripts/validate_project_artifacts.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.create_minimal_project(root)
            (root / "workspace" / "loop-state.json").write_text(
                json.dumps({
                    "schema": "moduflow.loop-state.v2",
                    "goal_id": "goal-a",
                    "issue_ids": ["missing-issue"],
                    "active_issue_id": "missing-issue",
                    "next_command": "product:spec missing-issue",
                    "status": "active",
                }) + "\n",
                encoding="utf-8",
            )

            result = validator.validate_project(root)

            self.assertFalse(result["valid"])
            self.assertTrue(any("active_issue_id missing-issue" in error for error in result["errors"]))
```

- [ ] **Step 2: Run the new validation tests and observe failure**

Run:

```bash
python3 -m unittest tests.test_project_loop.ProjectLoopTests.test_validate_loop_state_reports_missing_active_issue_file tests.test_validation_distribution.ValidationDistributionTests.test_validate_project_artifacts_reports_loop_state_missing_active_issue -v
```

Expected before implementation: FAIL with missing `validate_loop_state` or missing validator integration.

- [ ] **Step 3: Implement loop validation and CLI**

Add to `scripts/project_loop.py`:

```python

def validate_loop_state(root):
    state = load_loop_state(root)
    if not state:
        return []
    errors = []
    active_issue_id = state.get("active_issue_id")
    if active_issue_id and not issue_path(root, active_issue_id).exists():
        errors.append(f"workspace/loop-state.json: active_issue_id {active_issue_id} has no matching issue file")
    for issue_id in state.get("issue_ids", []):
        if not issue_path(root, issue_id).exists():
            errors.append(f"workspace/loop-state.json: issue_id {issue_id} has no matching issue file")
    if state.get("status") not in VALID_LOOP_STATUSES:
        errors.append(f"workspace/loop-state.json: unsupported status {state.get('status')}")
    return errors


def main():
    parser = argparse.ArgumentParser(description="Inspect or advance ModuFlow loop state.")
    parser.add_argument("project_path", nargs="?", default=".")
    parser.add_argument("--step", action="store_true", help="Persist one safe recommendation to workspace/loop-state.json.")
    args = parser.parse_args()
    result = recommend_loop(args.project_path)
    if args.step:
        write_loop_state(args.project_path, result)
    print(json.dumps({"schema": "moduflow.loop-recommendation.v1", **result}, ensure_ascii=False, indent=2))
    return 0 if result.get("status") != "blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())
```

Modify `scripts/validate_project_artifacts.py` by adding an import helper near the top:

```python
import importlib.util


def load_project_loop():
    path = Path(__file__).resolve().parent / "project_loop.py"
    spec = importlib.util.spec_from_file_location("project_loop", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
```

Then, inside `validate_project`, after state validation:

```python
    project_loop = load_project_loop()
    errors.extend(project_loop.validate_loop_state(root))
```

Modify `scripts/project_doctor.py` by adding the same import helper and include this field in `inspect_project` result:

```python
        "loop": {
            "initialized": (project_root / "workspace" / "loop-state.json").exists(),
            "errors": load_project_loop().validate_loop_state(project_root),
        },
```

If loop errors exist, append recommendation:

```python
    loop_errors = result["loop"]["errors"]
    if loop_errors:
        result["recommendation"].append("Run product:loop or product:doctor after fixing loop-state references.")
```

- [ ] **Step 4: Run validation tests**

Run:

```bash
python3 -m unittest tests.test_project_loop.ProjectLoopTests.test_validate_loop_state_reports_missing_active_issue_file tests.test_validation_distribution.ValidationDistributionTests.test_validate_project_artifacts_reports_loop_state_missing_active_issue -v
```

Expected: both tests PASS.

## Task 6: Update Command Docs And Templates

**Files:**
- Modify: `commands/product-loop.md`
- Modify: `commands/product-status.md`
- Modify: `templates/workspace/loop-state.json`
- Modify: `templates/moduflow-state.json`

- [ ] **Step 1: Update loop-state template to v2**

Replace `templates/workspace/loop-state.json` with:

```json
{
  "schema": "moduflow.loop-state.v2",
  "loop_id": "{{loop_id}}",
  "goal_id": "{{goal_id}}",
  "objective": "{{objective}}",
  "issue_ids": ["{{issue_id}}"],
  "active_issue_id": "{{issue_id}}",
  "phase": "goal",
  "mode": "recommend",
  "status": "active",
  "next_command": "product:loop",
  "attempts": {
    "command": "product:loop",
    "count": 0,
    "max": 3,
    "last_changed_at": "{{updated_date}}"
  },
  "blocker": null,
  "last_action": "",
  "last_verification": null,
  "updated_at": "{{updated_date}}"
}
```

- [ ] **Step 2: Update project state template**

Add nullable `active_goal` to `templates/moduflow-state.json`:

```json
{
  "schema": "moduflow.state.v1",
  "phase": "initialized",
  "active_goal": null,
  "active_issue": null,
  "last_command": "product:start",
  "next_command": "product:status",
  "blockers": [],
  "updated_at": "{{updated_at}}"
}
```

- [ ] **Step 3: Update `commands/product-loop.md`**

Add a short concrete schema section under `## State Updates`:

```markdown
Minimum loop-state v2 fields:

- `goal_id`: durable goal identifier
- `issue_ids`: ordered issue graph for the active goal
- `active_issue_id`: one issue cursor
- `phase`: current workflow phase inferred from artifacts
- `next_command`: next safe ModuFlow command
- `attempts.command/count/max`: repeated-step guard
- `status`: `active`, `needs_decision`, `blocked`, or `done`

Simple user aliases should route here: `상태`, `다음`, `이거 해줘`, `완료`.
```

- [ ] **Step 4: Update `commands/product-status.md`**

Add this to the read list and output guidance:

```markdown
When `workspace/loop-state.json` exists, show active goal, active issue cursor, loop status, attempts, and next command before older dashboard text. Do not expose raw JSON unless the user asks for diagnostics.
```

## Task 7: Full Verification And Artifact Updates

**Files:**
- Modify: `issues/019-loop-kernel-and-state-model.md`
- Modify: `specs/019-loop-kernel-and-state-model/status.md`
- Modify: `specs/019-loop-kernel-and-state-model/tasks.md`
- Modify: `.moduflow/state.json`
- Modify: `workspace/loop-state.json`
- Modify: `workspace/dashboard.md`
- Modify: `workspace/roadmap.md`

- [ ] **Step 1: Run focused tests**

Run:

```bash
python3 -m unittest tests.test_project_loop -v
```

Expected: all `ProjectLoopTests` PASS.

- [ ] **Step 2: Run validation distribution tests**

Run:

```bash
python3 -m unittest tests.test_validation_distribution -v
```

Expected: all validation distribution tests PASS.

- [ ] **Step 3: Run full test suite**

Run:

```bash
python3 -m unittest discover -s tests -v
```

Expected: all tests PASS.

- [ ] **Step 4: Run package validation**

Run:

```bash
python3 scripts/validate_project_artifacts.py .
python3 scripts/validate_moduflow.py .
python3 scripts/release_check.py .
```

Expected: all commands exit 0; release check returns `"valid": true`.

- [ ] **Step 5: Update workflow artifacts**

Apply these exact artifact states after verification passes:

- `issues/019-loop-kernel-and-state-model.md`: mark execute checked only after implementation and tests pass.
- `specs/019-loop-kernel-and-state-model/status.md`: record implementation files and verification commands.
- `workspace/loop-state.json`: set `phase` to `review`, `last_action` to `loop kernel implemented`, and `next_command` to `product:review 019-loop-kernel-and-state-model`.
- `.moduflow/state.json`: set `phase` to `implemented`, `active_issue` to `019-loop-kernel-and-state-model`, and `next_command` to `product:review 019-loop-kernel-and-state-model`.
- `workspace/dashboard.md`: show 019 as active issue and `product:review 019-loop-kernel-and-state-model` as next command.

## Self-Review

Spec coverage:

- Goal 1:N Issue and active issue cursor: Task 1 and Task 4.
- Existing v1 loop-state compatibility: Task 1.
- Next command recommendation from artifacts: Task 2 and Task 4.
- Repeated action guard: Task 3.
- Doctor/validation drift detection: Task 5.
- Plugin-installed `git-files` mode: Task 6 and Task 7.
- Simple user surface: Task 6 keeps this in command docs while issue 020 owns the fuller UX work.

Placeholder scan:

- No placeholder or vague edge-case instructions remain.

Type consistency:

- `active_issue_id`, `issue_ids`, `attempts.command`, `attempts.count`, `attempts.max`, `next_command`, and `status` are consistent across tests, implementation snippets, templates, and docs.

## Verification

Plan artifact verification:

- `python3 scripts/validate_project_artifacts.py .`
- `python3 scripts/validate_moduflow.py .`
- `python3 scripts/release_check.py .`

## Rollback

Remove `scripts/project_loop.py`, `tests/test_project_loop.py`, loop-state validator/doctor integrations, and v2 template/doc changes. Restore `workspace/loop-state.json` to the previous v1 shape only if downstream projects cannot read v2; otherwise keep v2 because loader remains backward compatible.

## Next Command

`product:execute 019-loop-kernel-and-state-model`
