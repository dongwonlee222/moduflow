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

    def test_release_check_succeeds_for_current_repo(self):
        release_check = load_module("release_check", "scripts/release_check.py")

        result = release_check.run_release_check(ROOT)

        self.assertTrue(result["valid"])
        self.assertEqual(result["errors"], [])
        self.assertIn("validate_moduflow", result["checks"])


if __name__ == "__main__":
    unittest.main()
