import contextlib
import importlib.util
import io
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
                        "schema": "moduflow.projects.v1",
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

    def test_collect_project_status_reads_team_workflow_state(self):
        project_portfolio = load_module("project_portfolio", "scripts/project_portfolio.py")
        with tempfile.TemporaryDirectory() as tmp:
            portfolio = Path(tmp) / "portfolio"
            project = Path(tmp) / "project-a"
            (project / ".moduflow").mkdir(parents=True)
            (project / "workflow").mkdir()
            (project / ".moduflow" / "state.json").write_text(
                json.dumps({"phase": "status", "next_command": "product:status"}) + "\n",
                encoding="utf-8",
            )
            (project / "workflow" / "team-state.json").write_text(
                json.dumps(
                    {
                        "schema": "moduflow.team-state.v1",
                        "items": [
                            {
                                "issue_id": "035-team-issue-branch-pr-workflow",
                                "status": "review",
                                "assignee": "Minsu",
                                "reviewer": "Dongwon",
                                "branch": "codex/035-team-issue-branch-pr-workflow",
                                "pr": "https://github.com/example/repo/pull/35",
                                "next_command": "product:review 035-team-issue-branch-pr-workflow",
                            },
                            {
                                "issue_id": "036-portfolio-team-dashboard",
                                "status": "active",
                                "assignee": "Jiyoung",
                                "branch": "codex/036-portfolio-team-dashboard",
                            },
                        ],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            portfolio.mkdir()
            (portfolio / "projects.json").write_text(
                json.dumps(
                    {
                        "schema": "moduflow.projects.v1",
                        "projects": [
                            {
                                "id": "project-a",
                                "name": "Project A",
                                "path": str(project),
                            }
                        ],
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            statuses = project_portfolio.collect_project_statuses(portfolio / "projects.json")

            self.assertEqual(statuses[0]["team"]["active_count"], 1)
            self.assertEqual(statuses[0]["team"]["review_count"], 1)
            self.assertIn("Jiyoung: 036-portfolio-team-dashboard", statuses[0]["team"]["active_text"])
            self.assertIn("Minsu: 035-team-issue-branch-pr-workflow", statuses[0]["team"]["review_text"])

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
                    "team": {
                        "active_text": "Jiyoung: 036-portfolio-team-dashboard",
                        "review_text": "Minsu: 035-team-issue-branch-pr-workflow",
                        "done_text": "none",
                    },
                    "path": "/tmp/project-a",
                    "warnings": [],
                }
            ]
        )

        self.assertIn(
            "| Project A | Mina | in-progress | Jiyoung: 036-portfolio-team-dashboard | Minsu: 035-team-issue-branch-pr-workflow | waiting for QA | product:review 001 |",
            dashboard,
        )
        self.assertIn("/tmp/project-a", dashboard)

    def v2_project(self, project_id, name, root, paths=None, aliases=None):
        return {
            "id": project_id,
            "name": name,
            "root": str(root),
            "aliases": aliases or [project_id, name],
            "paths": paths
            or {
                "issues": "issues",
                "specs": "specs",
                "workspace": "workspace",
                "knowledge": "knowledge",
                "memory": "memory",
                "production_records": "memory/production-records",
                "playbooks": "playbooks",
                "workflow": "workflow",
            },
            "trust_scope": "internal",
            "status": "active",
            "owner": "Owner",
        }

    def write_registry(self, portfolio, projects):
        portfolio.mkdir(parents=True, exist_ok=True)
        path = portfolio / "projects.json"
        path.write_text(
            json.dumps(
                {"schema": "moduflow.projects.v2", "projects": projects},
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )
        return path

    def test_new_portfolio_initialization_emits_projects_v2(self):
        project_portfolio = load_module("project_portfolio", "scripts/project_portfolio.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan = project_portfolio.build_portfolio_plan(root, dry_run=False)

            project_portfolio.apply_portfolio_plan(plan)

            payload = json.loads((root / "projects.json").read_text(encoding="utf-8"))
            self.assertEqual(payload["schema"], "moduflow.projects.v2")
            self.assertEqual(payload["projects"], [])

    def test_existing_v1_registry_is_preserved_and_rendered(self):
        project_portfolio = load_module("project_portfolio", "scripts/project_portfolio.py")
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            portfolio = base / "portfolio"
            project = base / "project"
            (project / ".moduflow").mkdir(parents=True)
            (project / ".moduflow" / "state.json").write_text(
                json.dumps({"phase": "review", "next_command": "product:review 001"}),
                encoding="utf-8",
            )
            portfolio.mkdir()
            registry = portfolio / "projects.json"
            registry.write_text(
                json.dumps(
                    {
                        "schema": "moduflow.projects.v1",
                        "projects": [
                            {
                                "id": "legacy",
                                "name": "Legacy",
                                "path": str(project),
                                "status": "active",
                                "owner": "Mina",
                            }
                        ],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            before = registry.read_bytes()

            statuses = project_portfolio.collect_project_statuses(registry)

            self.assertEqual(statuses[0]["id"], "legacy")
            self.assertEqual(statuses[0]["phase"], "review")
            self.assertEqual(statuses[0]["registry_schema"], "moduflow.projects.v1")
            self.assertEqual(registry.read_bytes(), before)

    def test_v2_status_uses_configured_workflow_and_ignores_default_decoy(self):
        project_portfolio = load_module("project_portfolio", "scripts/project_portfolio.py")
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            portfolio = base / "portfolio"
            project = base / "project"
            (project / ".moduflow").mkdir(parents=True)
            (project / ".moduflow" / "state.json").write_text(
                json.dumps({"phase": "execute", "next_command": "product:status"}),
                encoding="utf-8",
            )
            configured = project / "ops" / "workflow"
            configured.mkdir(parents=True)
            (configured / "team-state.json").write_text(
                json.dumps(
                    {
                        "items": [
                            {
                                "issue_id": "CONFIGURED-001",
                                "status": "active",
                                "assignee": "Mina",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            default = project / "workflow"
            default.mkdir()
            (default / "team-state.json").write_text(
                json.dumps(
                    {
                        "items": [
                            {
                                "issue_id": "DECOY-001",
                                "status": "active",
                                "assignee": "Wrong",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            paths = self.v2_project("project-a", "Project A", project)["paths"]
            paths["workflow"] = "ops/workflow"
            registry = self.write_registry(
                portfolio,
                [self.v2_project("project-a", "Project A", project, paths=paths)],
            )

            statuses = project_portfolio.collect_project_statuses(registry)

            serialized = json.dumps(statuses, ensure_ascii=False)
            self.assertIn("CONFIGURED-001", serialized)
            self.assertNotIn("DECOY-001", serialized)
            self.assertEqual(statuses[0]["resolution_status"], "resolved")

    def test_invalid_registry_returns_warnings_without_project_reads(self):
        project_portfolio = load_module("project_portfolio", "scripts/project_portfolio.py")
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            portfolio = base / "portfolio"
            project = base / "project"
            (project / ".moduflow").mkdir(parents=True)
            (project / ".moduflow" / "state.json").write_text(
                '{"phase": "SECRET-PHASE"}', encoding="utf-8"
            )
            first = self.v2_project("duplicate", "One", project)
            second = self.v2_project("duplicate", "Two", project)
            registry = self.write_registry(portfolio, [first, second])

            statuses = project_portfolio.collect_project_statuses(registry)

            serialized = json.dumps(statuses, ensure_ascii=False)
            self.assertNotIn("SECRET-PHASE", serialized)
            self.assertIn("PROJECT_ID_DUPLICATE", serialized)
            self.assertEqual(statuses[0]["resolution_status"], "unresolved")

    def test_resolve_cli_prints_resolution_without_writing(self):
        project_portfolio = load_module("project_portfolio", "scripts/project_portfolio.py")
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            portfolio = base / "portfolio"
            project_a = base / "a"
            project_b = base / "b"
            project_a.mkdir()
            project_b.mkdir()
            self.write_registry(
                portfolio,
                [
                    self.v2_project("project-a", "Project A", project_a),
                    self.v2_project(
                        "modu-charge",
                        "모두의충전",
                        project_b,
                        aliases=["모두의충전", "모두충전"],
                    ),
                ],
            )
            output = io.StringIO()

            with contextlib.redirect_stdout(output):
                code = project_portfolio.main(
                    [str(portfolio), "--resolve", "모두의충전 배너"]
                )

            payload = json.loads(output.getvalue())
            self.assertEqual(code, 0)
            self.assertEqual(payload["project_id"], "modu-charge")
            self.assertFalse((portfolio / "project-selection.json").exists())
            self.assertFalse((portfolio / "portfolio-dashboard.md").exists())

    def test_select_cli_writes_only_recent_selection(self):
        project_portfolio = load_module("project_portfolio", "scripts/project_portfolio.py")
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            portfolio = base / "portfolio"
            project = base / "project"
            project.mkdir()
            self.write_registry(
                portfolio,
                [self.v2_project("project-a", "Project A", project)],
            )
            before = {path.name for path in portfolio.iterdir()}
            output = io.StringIO()

            with contextlib.redirect_stdout(output):
                code = project_portfolio.main(
                    [str(portfolio), "--select", "project-a"]
                )

            after = {path.name for path in portfolio.iterdir()}
            self.assertEqual(code, 0)
            self.assertEqual(after - before, {"project-selection.json"})
            self.assertEqual(json.loads(output.getvalue())["action"], "written")

    def test_unknown_select_returns_nonzero_without_writing(self):
        project_portfolio = load_module("project_portfolio", "scripts/project_portfolio.py")
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            portfolio = base / "portfolio"
            project = base / "project"
            project.mkdir()
            self.write_registry(
                portfolio,
                [self.v2_project("project-a", "Project A", project)],
            )
            output = io.StringIO()

            with contextlib.redirect_stdout(output):
                code = project_portfolio.main(
                    [str(portfolio), "--select", "missing"]
                )

            self.assertEqual(code, 2)
            self.assertFalse((portfolio / "project-selection.json").exists())
            self.assertEqual(json.loads(output.getvalue())["status"], "error")

    def test_collect_status_projects_archived_read_only_capabilities(self):
        project_portfolio = load_module("project_portfolio", "scripts/project_portfolio.py")
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            portfolio = base / "portfolio"
            project = base / "project"
            (project / ".moduflow").mkdir(parents=True)
            (project / ".moduflow" / "state.json").write_text(
                json.dumps({"phase": "archived", "next_command": "product:doctor"}),
                encoding="utf-8",
            )
            (project / "workflow").mkdir()
            payload = self.v2_project("project-a", "Project A", project)
            payload["status"] = "archived"
            payload["trust_scope"] = "read-only"
            registry = self.write_registry(portfolio, [payload])

            statuses = project_portfolio.collect_project_statuses(registry)

        self.assertEqual(statuses[0]["project_status"], "archived")
        self.assertEqual(statuses[0]["policy_trust_scope"], "read-only")
        self.assertEqual(
            statuses[0]["capabilities"],
            {"read": True, "write": False, "execute": False, "publish": False},
        )
        self.assertEqual(
            statuses[0]["capability_reasons"]["publish"]["reason_code"],
            "PROJECT_OPERATION_DENIED_ARCHIVED",
        )


if __name__ == "__main__":
    unittest.main()
