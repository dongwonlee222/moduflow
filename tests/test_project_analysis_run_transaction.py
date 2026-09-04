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


class PlaybookOriginationTest(unittest.TestCase):
    """E1: a project playbook must be obtainable without hand-authoring one."""

    def _project(self, tmp, *entries):
        project = transaction_project(tmp)
        workspace = project.context["relative_paths"]["workspace"]
        project.write(workspace + "/analysis-runs.md", runs_file(*entries))
        return project

    def _parsed(self, project, plan):
        production = runs._module("project_production")
        return production.parse_playbook(project.root, Path(project.root) / plan["target_path"])

    def test_scaffold_previews_without_writing(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(tmp)
            plan = runs.plan_playbook_scaffold(
                project.root, "monthly-trend", project_context=project.context
            )
            self.assertFalse(plan["exists"])
            self.assertFalse((Path(project.root) / plan["target_path"]).exists())
            self.assertEqual(plan["origin"], "default")

    def test_scaffold_creates_a_parseable_candidate_and_never_overwrites(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(tmp)
            plan = runs.plan_playbook_scaffold(
                project.root, "monthly-trend", project_context=project.context
            )
            result = runs.apply_playbook_plan(
                project.root, plan, project_context=project.context
            )
            self.assertEqual(result["status"], "created")
            playbook = self._parsed(project, plan)
            self.assertEqual(playbook["status"], "candidate")
            self.assertEqual(playbook["approved_by"], "")
            self.assertTrue(playbook["retrieval_trigger"])
            with self.assertRaises(ValueError):
                runs.apply_playbook_plan(
                    project.root, plan, project_context=project.context
                )

    def test_the_read_only_default_is_never_modified(self):
        import tempfile
        source = runs.default_playbook_dir() / "monthly-trend.md"
        before = source.read_bytes()
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(tmp)
            plan = runs.plan_playbook_scaffold(
                project.root, "monthly-trend", project_context=project.context
            )
            runs.apply_playbook_plan(project.root, plan, project_context=project.context)
        self.assertEqual(source.read_bytes(), before)

    def test_unknown_default_name_raises(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(tmp)
            with self.assertRaises(runs.PlaybookUnresolved):
                runs.plan_playbook_scaffold(
                    project.root, "no-such-default", project_context=project.context
                )

    def test_promoting_a_run_produces_a_candidate_that_invents_nothing(self):
        import tempfile
        entry = valid_run()
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(tmp, entry)
            plan = runs.plan_playbook_promotion(
                project.root, RUN_ID, project_context=project.context, today="2026-09-08"
            )
            self.assertEqual(plan["origin"], "run-promotion")
            runs.apply_playbook_plan(project.root, plan, project_context=project.context)
            playbook = self._parsed(project, plan)
            self.assertEqual(playbook["status"], "candidate")
            self.assertEqual(playbook["approved_by"], "")
            self.assertEqual(playbook["approved_at"], "")
            self.assertEqual(playbook["process_ref"]["kind"], "none")
            self.assertIn("아직 승인된 문구가 없습니다", playbook["sections"]["Approved Copy Blocks"])
            self.assertIn(entry["id"], playbook["sections"]["Evidence"])

    def test_a_promoted_playbook_drives_the_next_run(self):
        import tempfile
        entry = valid_run()
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(tmp, entry)
            plan = runs.plan_playbook_promotion(
                project.root, RUN_ID, project_context=project.context, today="2026-09-08"
            )
            runs.apply_playbook_plan(project.root, plan, project_context=project.context)
            resolved = runs.resolve_playbook(
                project.root, plan["name"], project_context=project.context
            )
            self.assertEqual(resolved["source"], "project")
            prefill = runs.prefill_run(resolved["playbook"])
            self.assertEqual(prefill["claim_class"], entry["claim_class"])
            self.assertEqual(prefill["caveats"], entry["caveats"])

    def test_an_unfinished_run_cannot_be_promoted(self):
        import tempfile
        entry = valid_run(run_state="draft")
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(tmp, entry)
            with self.assertRaises(ValueError):
                runs.plan_playbook_promotion(
                    project.root, RUN_ID, project_context=project.context
                )
