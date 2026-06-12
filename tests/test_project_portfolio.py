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


class ProjectPortfolioTests(unittest.TestCase):
    def test_portfolio_dry_run_lists_missing_workspace_files_without_writing(self):
        project_portfolio = load_module("project_portfolio", "scripts/project_portfolio.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            plan = project_portfolio.build_portfolio_plan(root)

            self.assertTrue(plan["dry_run"])
            self.assertEqual(
                plan["writes"],
                [
                    "projects.json",
                    "portfolio-dashboard.md",
                    "portfolio-roadmap.md",
                    "weekly-status.md",
                ],
            )
            self.assertFalse((root / "projects.json").exists())

    def test_portfolio_write_preserves_existing_registry(self):
        project_portfolio = load_module("project_portfolio", "scripts/project_portfolio.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry = root / "projects.json"
            registry.write_text('{"projects": []}\n', encoding="utf-8")

            plan = project_portfolio.build_portfolio_plan(root, dry_run=False)
            result = project_portfolio.apply_portfolio_plan(plan)

            self.assertNotIn("projects.json", result["written"])
            self.assertEqual(registry.read_text(encoding="utf-8"), '{"projects": []}\n')
            self.assertTrue((root / "portfolio-dashboard.md").exists())

    def test_collect_project_status_reads_state_and_profile(self):
        project_portfolio = load_module("project_portfolio", "scripts/project_portfolio.py")
        with tempfile.TemporaryDirectory() as tmp:
            portfolio = Path(tmp) / "portfolio"
            project = Path(tmp) / "project-a"
            (project / ".moduflow").mkdir(parents=True)
            (project / "workspace").mkdir()
            (project / ".moduflow" / "state.json").write_text(
                json.dumps(
                    {
                        "phase": "in-progress",
                        "next_command": "product:review 001",
                        "blockers": ["waiting for QA"],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (project / ".moduflow" / "project-profile.md").write_text(
                "# Project Profile\n\n- Owner: Mina\n",
                encoding="utf-8",
            )
            portfolio.mkdir()
            (portfolio / "projects.json").write_text(
                json.dumps(
                    {
                        "projects": [
                            {
                                "id": "project-a",
                                "name": "Project A",
                                "path": str(project),
                                "status": "active",
                            }
                        ]
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            statuses = project_portfolio.collect_project_statuses(portfolio / "projects.json")

            self.assertEqual(statuses[0]["id"], "project-a")
            self.assertEqual(statuses[0]["phase"], "in-progress")
            self.assertEqual(statuses[0]["owner"], "Mina")
            self.assertEqual(statuses[0]["next_command"], "product:review 001")
            self.assertEqual(statuses[0]["blockers"], ["waiting for QA"])

    def test_render_dashboard_includes_project_status_fields(self):
        project_portfolio = load_module("project_portfolio", "scripts/project_portfolio.py")

        dashboard = project_portfolio.render_dashboard(
            [
                {
                    "id": "project-a",
                    "name": "Project A",
                    "owner": "Mina",
                    "phase": "in-progress",
                    "next_command": "product:review 001",
                    "blockers": ["waiting for QA"],
                    "path": "/tmp/project-a",
                    "warnings": [],
                }
            ]
        )

        self.assertIn("| Project A | Mina | in-progress | waiting for QA | product:review 001 |", dashboard)
        self.assertIn("/tmp/project-a", dashboard)


if __name__ == "__main__":
    unittest.main()
