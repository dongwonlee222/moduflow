import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_module(name, relative_path):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ValidationDistributionTests(unittest.TestCase):
    def create_minimal_project(self, root):
        (root / ".moduflow").mkdir()
        (root / ".moduflow" / "config.json").write_text(
            json.dumps({"schema": "moduflow.config.v1", "paths": {}}) + "\n",
            encoding="utf-8",
        )
        (root / ".moduflow" / "state.json").write_text(
            json.dumps({"schema": "moduflow.state.v1", "phase": "ready", "next_command": "product:status"}) + "\n",
            encoding="utf-8",
        )
        for directory in ["issues", "specs", "knowledge/decisions", "knowledge/benchmarks", "knowledge/reports", "knowledge/research", "knowledge/data-notes", "knowledge/references"]:
            (root / directory).mkdir(parents=True, exist_ok=True)
        (root / "knowledge" / "index.md").write_text("# Knowledge\n", encoding="utf-8")
        (root / "workspace").mkdir()
        for filename in ["inbox.md", "opportunities.md", "roadmap.md", "dashboard.md"]:
            (root / "workspace" / filename).write_text("# Workspace\n", encoding="utf-8")
        for filename in ["project-profile.md", "environments.json", "integrations.json"]:
            content = "{}\n" if filename.endswith(".json") else "# Profile\n"
            (root / ".moduflow" / filename).write_text(content, encoding="utf-8")
        (root / "workflow").mkdir()
        for filename in ["review-gates.md", "approval-policy.md", "release-policy.md", "handoff.md", "risks.md"]:
            (root / "workflow" / filename).write_text("# Workflow\n", encoding="utf-8")

    def test_validate_project_artifacts_passes_for_valid_project(self):
        validator = load_module("validate_project_artifacts", "scripts/validate_project_artifacts.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.create_minimal_project(root)

            result = validator.validate_project(root)

            self.assertTrue(result["valid"])
            self.assertEqual(result["errors"], [])

    def test_validate_project_artifacts_reports_invalid_state_json(self):
        validator = load_module("validate_project_artifacts", "scripts/validate_project_artifacts.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.create_minimal_project(root)
            (root / ".moduflow" / "state.json").write_text("{bad json", encoding="utf-8")

            result = validator.validate_project(root)

            self.assertFalse(result["valid"])
            self.assertTrue(any(".moduflow/state.json" in error for error in result["errors"]))

    def test_validate_project_artifacts_allows_lightweight_project(self):
        validator = load_module("validate_project_artifacts", "scripts/validate_project_artifacts.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".moduflow").mkdir()
            (root / ".moduflow" / "config.json").write_text(
                json.dumps({"schema": "moduflow.config.v1", "paths": {}}) + "\n",
                encoding="utf-8",
            )
            (root / ".moduflow" / "state.json").write_text(
                json.dumps({"schema": "moduflow.state.v1", "phase": "ready", "next_command": "product:status"}) + "\n",
                encoding="utf-8",
            )
            for directory in ["issues", "specs"]:
                (root / directory).mkdir()
            (root / "workspace").mkdir()
            for filename in ["inbox.md", "opportunities.md", "roadmap.md", "dashboard.md"]:
                (root / "workspace" / filename).write_text("# Workspace\n", encoding="utf-8")

            result = validator.validate_project(root)

            self.assertTrue(result["valid"])
            self.assertEqual(result["errors"], [])
            self.assertTrue(any("Optional project capability not initialized" in warning for warning in result["warnings"]))

    def test_validate_project_artifacts_respects_configured_paths(self):
        validator = load_module("validate_project_artifacts", "scripts/validate_project_artifacts.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".moduflow").mkdir()
            (root / ".moduflow" / "config.json").write_text(
                json.dumps(
                    {
                        "schema": "moduflow.config.v1",
                        "paths": {
                            "issues": "projects/modu-charge/issues",
                            "specs": "specs",
                            "workspace": "workspace",
                        },
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (root / ".moduflow" / "state.json").write_text(
                json.dumps({"schema": "moduflow.state.v1", "phase": "ready", "next_command": "product:status"}) + "\n",
                encoding="utf-8",
            )
            (root / "projects" / "modu-charge" / "issues").mkdir(parents=True)
            (root / "specs").mkdir()
            (root / "workspace").mkdir()
            for filename in ["inbox.md", "opportunities.md", "roadmap.md", "dashboard.md"]:
                (root / "workspace" / filename).write_text("# Workspace\n", encoding="utf-8")

            result = validator.validate_project(root)

            self.assertTrue(result["valid"])
            self.assertEqual(result["errors"], [])

    def test_validate_project_artifacts_reports_loop_state_missing_active_issue(self):
        validator = load_module("validate_project_artifacts", "scripts/validate_project_artifacts.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.create_minimal_project(root)
            (root / "workspace" / "loop-state.json").write_text(
                json.dumps(
                    {
                        "schema": "moduflow.loop-state.v2",
                        "goal_id": "goal-a",
                        "issue_ids": ["missing-issue"],
                        "active_issue_id": "missing-issue",
                        "next_command": "product:spec missing-issue",
                        "status": "active",
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            result = validator.validate_project(root)

            self.assertFalse(result["valid"])
            self.assertTrue(
                any("active_issue_id missing-issue" in error for error in result["errors"])
            )


    def write_loop_project(self, root, issue_id="024-artifact-schema-and-doctor-gates", next_command=None):
        self.create_minimal_project(root)
        next_command = next_command or f"product:spec {issue_id}"
        (root / "issues" / f"{issue_id}.md").write_text(
            f"""# Issue 024: Artifact Schema And Doctor Gates

## Lifecycle

- Phase: proposed

## Workflow Tasks

- [ ] spec → `specs/{issue_id}/spec.md`
- [ ] plan → `specs/{issue_id}/plan.md`
- [ ] execute → schema validator + doctor gates
- [ ] review → fixture-based drift/missing-link tests

## Next Command

`{next_command}`
""",
            encoding="utf-8",
        )
        (root / "workspace" / "loop-state.json").write_text(
            json.dumps(
                {
                    "schema": "moduflow.loop-state.v2",
                    "goal_id": "goal-loop",
                    "issue_ids": [issue_id],
                    "active_issue_id": issue_id,
                    "phase": "spec",
                    "next_command": next_command,
                    "status": "active",
                }
            )
            + "\n",
            encoding="utf-8",
        )
        (root / "workspace" / "dashboard.md").write_text(
            f"# Dashboard\n\n## Active Issue\n\n- `{issue_id}`\n\n## Next Command\n\n`{next_command}`\n",
            encoding="utf-8",
        )
        (root / "workspace" / "roadmap.md").write_text(
            f"# Roadmap\n\n## Now\n\n### `{issue_id}`\n\n- Next command: `{next_command}`\n",
            encoding="utf-8",
        )

    def test_validate_project_artifacts_reports_missing_linked_spec_file(self):
        validator = load_module("validate_project_artifacts", "scripts/validate_project_artifacts.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            issue_id = "024-artifact-schema-and-doctor-gates"
            self.write_loop_project(root, issue_id)

            result = validator.validate_project(root)

            self.assertFalse(result["valid"])
            self.assertTrue(
                any(f"issues/{issue_id}.md: linked artifact missing: specs/{issue_id}/spec.md" in error for error in result["errors"])
            )

    def test_validate_project_artifacts_reports_dashboard_active_issue_drift(self):
        validator = load_module("validate_project_artifacts", "scripts/validate_project_artifacts.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            issue_id = "024-artifact-schema-and-doctor-gates"
            self.write_loop_project(root, issue_id)
            (root / "specs" / issue_id).mkdir(parents=True)
            (root / "specs" / issue_id / "spec.md").write_text("# Spec\n", encoding="utf-8")
            (root / "workspace" / "dashboard.md").write_text("# Dashboard\n\n- `023-worker-routing-and-isolation`\n", encoding="utf-8")

            result = validator.validate_project(root)

            self.assertFalse(result["valid"])
            self.assertTrue(
                any("workspace/dashboard.md: missing active_issue_id 024-artifact-schema-and-doctor-gates" in error for error in result["errors"])
            )

    def test_validate_project_artifacts_reports_invalid_next_command_for_phase(self):
        validator = load_module("validate_project_artifacts", "scripts/validate_project_artifacts.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            issue_id = "024-artifact-schema-and-doctor-gates"
            self.write_loop_project(root, issue_id, next_command=f"product:plan {issue_id}")
            (root / "specs" / issue_id).mkdir(parents=True)
            (root / "specs" / issue_id / "spec.md").write_text("# Spec\n", encoding="utf-8")

            result = validator.validate_project(root)

            self.assertFalse(result["valid"])
            self.assertTrue(
                any(f"workspace/loop-state.json: next_command product:plan {issue_id} should be product:spec {issue_id}" in error for error in result["errors"])
            )

    def test_project_doctor_surfaces_schema_gate_errors(self):
        project_doctor = load_module("project_doctor", "scripts/project_doctor.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            issue_id = "024-artifact-schema-and-doctor-gates"
            self.write_loop_project(root, issue_id, next_command=f"product:plan {issue_id}")

            result = project_doctor.inspect_project(root)

            self.assertTrue(
                any("schema gate failed" in recommendation for recommendation in result["recommendation"])
            )
            self.assertTrue(result["schema_gates"]["errors"])


    def test_portfolio_doctor_warns_for_missing_project_path(self):
        portfolio_doctor = load_module("portfolio_doctor", "scripts/portfolio_doctor.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            missing_project = root / "missing"
            (root / "projects.json").write_text(
                json.dumps({"projects": [{"id": "missing", "name": "Missing", "path": str(missing_project)}]}) + "\n",
                encoding="utf-8",
            )

            result = portfolio_doctor.inspect_portfolio(root)

            self.assertFalse(result["valid"])
            self.assertTrue(any("missing" in warning for warning in result["warnings"]))

    def test_project_doctor_exit_zero_for_initialized_repo(self):
        # The ModuFlow repo itself is initialized (missing == []), so the gate passes.
        proc = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "project_doctor.py"), str(ROOT)],
            capture_output=True,
        )
        self.assertEqual(proc.returncode, 0)

    def test_project_doctor_exit_nonzero_for_uninitialized(self):
        # An empty (non-ModuFlow, non-git) directory must fail the gate, not silently pass.
        with tempfile.TemporaryDirectory() as tmp:
            proc = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "project_doctor.py"), tmp],
                capture_output=True,
            )
            self.assertEqual(proc.returncode, 1)

    def test_release_check_succeeds_for_current_repo(self):
        release_check = load_module("release_check", "scripts/release_check.py")

        result = release_check.run_release_check(ROOT)

        self.assertTrue(result["valid"])
        self.assertEqual(result["errors"], [])
        self.assertIn("validate_moduflow", result["checks"])

    def test_project_doctor_detects_dogfooding_mode(self):
        project_doctor = load_module("project_doctor", "scripts/project_doctor.py")
        result = project_doctor.inspect_project(ROOT)
        self.assertEqual(result["mode"], "dogfooding")

    def test_project_doctor_detects_lightweight_mode(self):
        project_doctor = load_module("project_doctor", "scripts/project_doctor.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            # Initialize minimal project (lightweight)
            (root / ".moduflow").mkdir(parents=True, exist_ok=True)
            (root / ".moduflow" / "config.json").write_text("{}", encoding="utf-8")
            (root / ".moduflow" / "state.json").write_text("{}", encoding="utf-8")
            (root / "workspace").mkdir(parents=True, exist_ok=True)
            (root / "workspace" / "inbox.md").write_text("", encoding="utf-8")
            (root / "workspace" / "opportunities.md").write_text("", encoding="utf-8")
            (root / "workspace" / "roadmap.md").write_text("", encoding="utf-8")
            (root / "workspace" / "dashboard.md").write_text("", encoding="utf-8")
            (root / "issues").mkdir(parents=True, exist_ok=True)
            (root / "specs").mkdir(parents=True, exist_ok=True)
            
            result = project_doctor.inspect_project(root)
            self.assertEqual(result["mode"], "lightweight")

    def test_project_doctor_detects_heavy_mode(self):
        project_doctor = load_module("project_doctor", "scripts/project_doctor.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            # Initialize minimal project
            (root / ".moduflow").mkdir(parents=True, exist_ok=True)
            (root / ".moduflow" / "config.json").write_text("{}", encoding="utf-8")
            (root / ".moduflow" / "state.json").write_text("{}", encoding="utf-8")
            (root / "workspace").mkdir(parents=True, exist_ok=True)
            (root / "workspace" / "inbox.md").write_text("", encoding="utf-8")
            (root / "workspace" / "opportunities.md").write_text("", encoding="utf-8")
            (root / "workspace" / "roadmap.md").write_text("", encoding="utf-8")
            (root / "workspace" / "dashboard.md").write_text("", encoding="utf-8")
            (root / "issues").mkdir(parents=True, exist_ok=True)
            (root / "specs").mkdir(parents=True, exist_ok=True)
            # Add legacy tooling dir
            (root / "commands").mkdir(parents=True, exist_ok=True)
            (root / "commands" / "dummy.md").write_text("dummy", encoding="utf-8")
            
            result = project_doctor.inspect_project(root)
            self.assertEqual(result["mode"], "heavy")

    def test_project_doctor_keeps_raw_mode_and_adds_user_guidance(self):
        project_doctor = load_module("project_doctor", "scripts/project_doctor.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".moduflow").mkdir(parents=True, exist_ok=True)
            (root / ".moduflow" / "config.json").write_text("{}", encoding="utf-8")
            (root / ".moduflow" / "state.json").write_text("{}", encoding="utf-8")
            (root / "workspace").mkdir(parents=True, exist_ok=True)
            for filename in ["inbox.md", "opportunities.md", "roadmap.md", "dashboard.md"]:
                (root / "workspace" / filename).write_text("", encoding="utf-8")
            (root / "issues").mkdir(parents=True, exist_ok=True)
            (root / "specs").mkdir(parents=True, exist_ok=True)

            result = project_doctor.inspect_project(root)

            self.assertEqual(result["mode"], "lightweight")
            self.assertEqual(
                result["mode_guidance"]["message"],
                "프로젝트 설정이 가볍고 정상입니다.",
            )
            self.assertIn("commands", result["mode_guidance"]["details"])
            self.assertNotEqual(result["mode_guidance"]["label"], "lightweight")


if __name__ == "__main__":
    unittest.main()
