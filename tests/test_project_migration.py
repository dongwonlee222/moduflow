import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts import project_operation, project_registry


ROOT = Path(__file__).resolve().parents[1]


def load_module(name, relative_path):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


project_doctor = load_module("project_doctor", "scripts/project_doctor.py")


class AdoptionSurvivesACloneTests(unittest.TestCase):
    """Issue 141 — a committed adoption did not survive `git clone`.

    `migrate --write` created `issues`, `specs`, `knowledge`, `memory` and
    `workflow` as **empty directories**. Git does not track those, so the commit
    that looked complete carried none of them, and a clone came back missing
    `issues` and `specs` with `doctor` reporting `initialized: False`.

    **Only a clone can catch this.** Every existing migration test asserts
    against the working tree, where the empty directories are present and
    everything looks right. That is why this class shells out to real git rather
    than checking `path.exists()`.

    `workspace/transactions` already shipped a `.gitkeep` for the same reason —
    the pattern existed and the five directories did not use it.
    """

    def git(self, cwd, *args):
        return subprocess.run(
            ["git", "-c", "user.email=t@t", "-c", "user.name=t", *args],
            cwd=str(cwd), capture_output=True, text=True, check=True,
        )

    def adopt_commit_and_clone(self, tmp):
        """The exact sequence a person follows, ending in a second machine."""
        origin = Path(tmp) / "origin"
        (origin / "src").mkdir(parents=True)
        (origin / "src" / "a.py").write_text("print(1)\n", encoding="utf-8")
        self.git(origin, "init", "-q")
        self.git(origin, "add", "-A")
        self.git(origin, "commit", "-q", "-m", "init")

        migrate = load_module("project_migrate", "scripts/project_migrate.py")
        plan = migrate.build_migration_plan(origin, mode="mapped", dry_run=False)
        migrate.apply_migration_plan(plan)

        self.git(origin, "add", "-A")
        self.git(origin, "commit", "-q", "-m", "adopt moduflow")

        clone = Path(tmp) / "clone"
        subprocess.run(
            ["git", "clone", "-q", str(origin), str(clone)],
            capture_output=True, text=True, check=True,
        )
        return origin, clone

    def test_every_created_directory_survives_the_clone(self):
        with tempfile.TemporaryDirectory() as tmp:
            origin, clone = self.adopt_commit_and_clone(tmp)
            migrate = load_module("project_migrate", "scripts/project_migrate.py")
            missing = [
                name for name in migrate.MINIMAL_PM_DIRECTORIES
                if not (clone / name).is_dir()
            ]
            self.assertEqual(
                missing, [],
                "empty directories are not committed; a clone loses them",
            )

    def test_the_clone_is_still_an_initialized_project(self):
        with tempfile.TemporaryDirectory() as tmp:
            origin, clone = self.adopt_commit_and_clone(tmp)
            doctor = load_module("project_doctor", "scripts/project_doctor.py")
            result = doctor.inspect_project(clone, include_preflight=False)
            self.assertTrue(
                result["moduflow"]["initialized"],
                f"clone reports missing: {result['moduflow']['missing']}",
            )
            self.assertEqual(result["moduflow"]["missing"], [])

    def test_the_working_tree_alone_would_not_have_caught_this(self):
        """Named so nobody replaces the clone with an `exists()` check.

        The origin passes on every assertion the clone fails, which is exactly
        why this bug shipped.
        """
        with tempfile.TemporaryDirectory() as tmp:
            origin, _clone = self.adopt_commit_and_clone(tmp)
            migrate = load_module("project_migrate", "scripts/project_migrate.py")
            for name in migrate.MINIMAL_PM_DIRECTORIES:
                self.assertTrue((origin / name).is_dir())


class ProjectMigrationTests(unittest.TestCase):
    def test_archived_project_denies_migration_before_moduflow_creation(self):
        project_migrate = load_module("project_migrate_denied", "scripts/project_migrate.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            context = project_registry.project_context_for_root(root)
            context.update(project_operation.compute_project_policy("archived", "internal"))
            plan = project_migrate.build_migration_plan(root, dry_run=False)

            with self.assertRaisesRegex(Exception, "Archived projects are read-only"):
                project_migrate.apply_migration_plan(plan, project_context=context)

            self.assertFalse((root / ".moduflow").exists())

    def test_doctor_discovers_existing_project_artifact_candidates(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs" / "specs").mkdir(parents=True)
            (root / "planning").mkdir()
            (root / "reports").mkdir()
            (root / "research").mkdir()

            candidates = project_doctor.discover_candidate_paths(root)

            self.assertEqual(candidates["specs"], ["docs/specs"])
            self.assertEqual(candidates["workspace"], ["planning"])
            self.assertEqual(candidates["reports"], ["reports"])
            self.assertEqual(candidates["research"], ["research"])

    def test_doctor_recommends_mapped_migration_when_candidates_exist(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs" / "specs").mkdir(parents=True)
            (root / "planning").mkdir()

            result = project_doctor.inspect_project(root)

            self.assertFalse(result["moduflow"]["initialized"])
            self.assertEqual(result["migration"]["recommended_mode"], "mapped")
            self.assertIn("product:migrate --mode mapped", " ".join(result["recommendation"]))

    def test_doctor_respects_configured_project_paths(self):
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
            (root / ".moduflow" / "state.json").write_text("{}\n", encoding="utf-8")
            (root / "projects" / "modu-charge" / "issues").mkdir(parents=True)
            (root / "specs").mkdir()
            (root / "workspace").mkdir()
            for filename in ["inbox.md", "opportunities.md", "roadmap.md", "dashboard.md"]:
                (root / "workspace" / filename).write_text("# Workspace\n", encoding="utf-8")

            result = project_doctor.inspect_project(root)

            self.assertTrue(result["moduflow"]["initialized"])
            self.assertEqual(result["moduflow"]["missing"], [])

    def test_migration_dry_run_builds_plan_without_writing_files(self):
        project_migrate = load_module("project_migrate", "scripts/project_migrate.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs" / "specs").mkdir(parents=True)
            (root / "planning").mkdir()

            plan = project_migrate.build_migration_plan(root, mode="mapped")

            self.assertTrue(plan["dry_run"])
            self.assertEqual(plan["mode"], "mapped")
            self.assertEqual(plan["config"]["paths"]["specs"], "docs/specs")
            self.assertEqual(plan["config"]["paths"]["workspace"], "planning")
            self.assertFalse((root / ".moduflow" / "config.json").exists())

    def test_migration_write_creates_metadata_without_overwriting_existing_files(self):
        project_migrate = load_module("project_migrate", "scripts/project_migrate.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs" / "specs").mkdir(parents=True)
            (root / "planning").mkdir()
            existing_dashboard = root / "planning" / "dashboard.md"
            existing_dashboard.write_text("# Existing Dashboard\n", encoding="utf-8")

            plan = project_migrate.build_migration_plan(root, mode="mapped", dry_run=False)
            project_migrate.apply_migration_plan(plan)

            config = json.loads((root / ".moduflow" / "config.json").read_text(encoding="utf-8"))
            self.assertEqual(config["paths"]["specs"], "docs/specs")
            self.assertEqual(config["paths"]["workspace"], "planning")
            self.assertEqual(existing_dashboard.read_text(encoding="utf-8"), "# Existing Dashboard\n")
            self.assertTrue((root / ".moduflow" / "state.json").exists())

    def test_migration_write_creates_minimal_pm_structure_without_tooling_dirs(self):
        project_migrate = load_module("project_migrate", "scripts/project_migrate.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            plan = project_migrate.build_migration_plan(root, mode="overlay", dry_run=False)
            result = project_migrate.apply_migration_plan(plan)

            for relative in [
                ".moduflow/config.json",
                ".moduflow/state.json",
                "issues",
                "specs",
                "knowledge",
                "workflow",
                "workspace/inbox.md",
                "workspace/opportunities.md",
                "workspace/roadmap.md",
                "workspace/dashboard.md",
                "workspace/loop-state.json",
                "workspace/goal.md",
                "workspace/transactions/.gitkeep",
            ]:
                self.assertTrue((root / relative).exists(), relative)
                self.assertIn(relative, result["written"])

            for tooling_dir in ["commands", "scripts", "skills", "templates", "workers", "adapters", "vendor"]:
                self.assertFalse((root / tooling_dir).exists(), tooling_dir)

    def test_migration_plan_lists_only_missing_files_as_writes(self):
        project_migrate = load_module("project_migrate", "scripts/project_migrate.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".moduflow").mkdir()
            (root / ".moduflow" / "config.json").write_text("{}\n", encoding="utf-8")
            (root / ".moduflow" / "state.json").write_text("{}\n", encoding="utf-8")
            (root / "workspace").mkdir()
            (root / "workspace" / "dashboard.md").write_text("# Existing\n", encoding="utf-8")

            plan = project_migrate.build_migration_plan(root, mode="overlay")

            self.assertNotIn(".moduflow/config.json", plan["writes"])
            self.assertNotIn(".moduflow/state.json", plan["writes"])
            self.assertNotIn("workspace/dashboard.md", plan["writes"])
            self.assertIn("workspace/inbox.md", plan["writes"])
            self.assertIn("workspace/transactions/.gitkeep", plan["writes"])

    def test_overlay_migration_preserves_existing_configured_workspace(self):
        project_migrate = load_module("project_migrate", "scripts/project_migrate.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".moduflow").mkdir()
            (root / ".moduflow" / "config.json").write_text(
                json.dumps(
                    {
                        "schema": "moduflow.config.v1",
                        "paths": {
                            "issues": "product/issues",
                            "specs": "product/specs",
                            "workspace": "product/workspace",
                        },
                    }
                ),
                encoding="utf-8",
            )

            plan = project_migrate.build_migration_plan(root, mode="overlay")

            self.assertEqual(plan["config"]["paths"]["issues"], "product/issues")
            self.assertEqual(plan["config"]["paths"]["specs"], "product/specs")
            self.assertEqual(
                plan["config"]["paths"]["workspace"], "product/workspace"
            )
            self.assertIn("product/workspace/inbox.md", plan["writes"])
            self.assertIn(
                "product/workspace/transactions/.gitkeep", plan["writes"]
            )
            self.assertNotIn("workspace/inbox.md", plan["writes"])


if __name__ == "__main__":
    unittest.main()
