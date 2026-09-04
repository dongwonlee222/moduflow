import importlib.util
import unittest
from pathlib import Path

from tests.analysis_run_fixture import RUN_ID, runs_file, valid_run
from tests.knowledge_registry_fixture import transaction_project

ROOT = Path(__file__).resolve().parents[1]


def load_module(name, relative_path):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


runs = load_module("project_analysis_run", "scripts/project_analysis_run.py")


class AnalysisRunTransactionTest(unittest.TestCase):
    def _project(self, tmp, *entries):
        project = transaction_project(tmp)
        workspace = project.context["relative_paths"]["workspace"]
        project.write(workspace + "/analysis-runs.md", runs_file(*entries))
        return project

    def _bytes(self, project, relative):
        return (Path(project.root) / relative).read_bytes()

    def _projection_hashes(self, project):
        workspace = project.context["relative_paths"]["workspace"]
        return {
            name: self._bytes(project, name)
            for name in (
                ".moduflow/state.json",
                workspace + "/loop-state.json",
                workspace + "/dashboard.md",
            )
        }

    def test_preview_writes_nothing(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(tmp)
            workspace = project.context["relative_paths"]["workspace"]
            before = self._bytes(project, workspace + "/analysis-runs.md")
            plan = runs.plan_analysis_run_append(
                project.root, valid_run(), project_context=project.context
            )
            self.assertEqual(plan.action, "analysis-run-append")
            self.assertEqual(
                self._bytes(project, workspace + "/analysis-runs.md"), before
            )

    def test_append_writes_only_the_run_file_and_one_backlink(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(tmp)
            workspace = project.context["relative_paths"]["workspace"]
            issues = project.context["relative_paths"]["issues"]
            projections = self._projection_hashes(project)

            entry = valid_run()
            plan = runs.plan_analysis_run_append(
                project.root, entry, project_context=project.context
            )
            result = runs.apply_analysis_run_append(
                project.root, plan, project_context=project.context
            )
            self.assertEqual(result["status"], "applied", result)

            text = (Path(project.root) / workspace / "analysis-runs.md").read_text(
                encoding="utf-8"
            )
            self.assertIn(f"## {RUN_ID}", text)
            issue = (
                Path(project.root) / issues / "001-synthetic-a.md"
            ).read_text(encoding="utf-8")
            self.assertIn("## Analysis Runs", issue)
            backlinks = [line for line in issue.splitlines() if RUN_ID in line]
            self.assertEqual(len(backlinks), 1, backlinks)
            self.assertEqual(self._projection_hashes(project), projections)

    def test_retry_is_byte_identical(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(tmp)
            workspace = project.context["relative_paths"]["workspace"]
            entry = valid_run()
            plan = runs.plan_analysis_run_append(
                project.root, entry, project_context=project.context
            )
            runs.apply_analysis_run_append(
                project.root, plan, project_context=project.context
            )
            after = self._bytes(project, workspace + "/analysis-runs.md")
            retry = runs.apply_analysis_run_append(
                project.root, plan, project_context=project.context
            )
            self.assertIn(retry["status"], ("applied", "noop"))
            self.assertEqual(
                self._bytes(project, workspace + "/analysis-runs.md"), after
            )

    def test_identical_reappend_is_a_noop_and_a_different_one_is_refused(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            entry = valid_run()
            project = self._project(tmp, entry)
            workspace = project.context["relative_paths"]["workspace"]
            before = self._bytes(project, workspace + "/analysis-runs.md")

            plan = runs.plan_analysis_run_append(
                project.root, entry, project_context=project.context
            )
            runs.apply_analysis_run_append(
                project.root, plan, project_context=project.context
            )
            self.assertEqual(
                self._bytes(project, workspace + "/analysis-runs.md"), before
            )

            collision = valid_run(title="A different run reusing the same id")
            with self.assertRaises(Exception):
                runs.plan_analysis_run_append(
                    project.root, collision, project_context=project.context
                )

    def test_amending_a_forbidden_field_is_refused(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            entry = valid_run()
            project = self._project(tmp, entry)
            changed = valid_run(conclusion="A different conclusion entirely.")
            with self.assertRaises(Exception):
                runs.plan_analysis_run_append(
                    project.root, changed, project_context=project.context, amend=True
                )

    def test_state_amendment_replaces_only_that_record(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            entry = valid_run()
            project = self._project(tmp, entry)
            workspace = project.context["relative_paths"]["workspace"]
            amended = valid_run(
                run_state="draft",
                state_history=[
                    {
                        "field": "run_state",
                        "from": "completed",
                        "to": "draft",
                        "reason": "reopened for a correction",
                        "evidence_ref": None,
                        "recorded_at": "2026-09-08",
                    }
                ],
            )
            plan = runs.plan_analysis_run_append(
                project.root, amended, project_context=project.context, amend=True
            )
            runs.apply_analysis_run_append(
                project.root, plan, project_context=project.context
            )
            parsed = runs.parse_analysis_runs(
                (Path(project.root) / workspace / "analysis-runs.md").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(len(parsed["entries"]), 1)
            self.assertEqual(parsed["entries"][0]["run_state"], "draft")
            self.assertEqual(len(parsed["entries"][0]["state_history"]), 1)

    def test_an_invalid_run_never_reaches_a_write(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(tmp)
            workspace = project.context["relative_paths"]["workspace"]
            before = self._bytes(project, workspace + "/analysis-runs.md")
            with self.assertRaises(Exception):
                runs.plan_analysis_run_append(
                    project.root,
                    valid_run(approval_state="approved"),
                    project_context=project.context,
                )
            self.assertEqual(
                self._bytes(project, workspace + "/analysis-runs.md"), before
            )


if __name__ == "__main__":
    unittest.main()
