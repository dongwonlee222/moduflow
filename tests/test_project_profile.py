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


project_doctor = load_module("project_doctor", "scripts/project_doctor.py")


class ProjectProfileTests(unittest.TestCase):
    def test_profile_dry_run_lists_missing_profile_files_without_writing(self):
        project_profile = load_module("project_profile", "scripts/project_profile.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            plan = project_profile.build_profile_plan(root)

            self.assertTrue(plan["dry_run"])
            self.assertEqual(
                plan["writes"],
                [
                    ".moduflow/project-profile.md",
                    ".moduflow/environments.json",
                    ".moduflow/integrations.json",
                ],
            )
            self.assertFalse((root / ".moduflow" / "project-profile.md").exists())

    def test_profile_write_creates_missing_files_and_preserves_existing_content(self):
        project_profile = load_module("project_profile", "scripts/project_profile.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile_path = root / ".moduflow" / "project-profile.md"
            profile_path.parent.mkdir()
            profile_path.write_text("# Existing Profile\n", encoding="utf-8")

            plan = project_profile.build_profile_plan(root, dry_run=False)
            result = project_profile.apply_profile_plan(plan)

            self.assertNotIn(".moduflow/project-profile.md", result["written"])
            self.assertEqual(profile_path.read_text(encoding="utf-8"), "# Existing Profile\n")
            self.assertTrue((root / ".moduflow" / "environments.json").exists())
            self.assertTrue((root / ".moduflow" / "integrations.json").exists())

    def test_doctor_reports_profile_missing_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".moduflow").mkdir()
            (root / ".moduflow" / "config.json").write_text("{}\n", encoding="utf-8")
            (root / ".moduflow" / "state.json").write_text("{}\n", encoding="utf-8")
            (root / "issues").mkdir()
            (root / "specs").mkdir()
            (root / "workspace").mkdir()
            for filename in ["inbox.md", "opportunities.md", "roadmap.md", "dashboard.md"]:
                (root / "workspace" / filename).write_text("# Test\n", encoding="utf-8")

            result = project_doctor.inspect_project(root)

            self.assertFalse(result["profile"]["initialized"])
            self.assertEqual(
                result["profile"]["missing"],
                [
                    ".moduflow/project-profile.md",
                    ".moduflow/environments.json",
                    ".moduflow/integrations.json",
                ],
            )
            self.assertIn("product:profile", " ".join(result["recommendation"]))

    def test_doctor_reports_profile_initialized(self):
        project_profile = load_module("project_profile", "scripts/project_profile.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan = project_profile.build_profile_plan(root, dry_run=False)
            project_profile.apply_profile_plan(plan)

            missing = project_doctor.missing_profile_paths(root)

            self.assertEqual(missing, [])

    def test_legacy_remote_is_only_a_confirmation_candidate(self):
        project_profile = load_module("project_profile", "scripts/project_profile.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config_path = root / ".moduflow" / "config.json"
            config_path.parent.mkdir()
            config_path.write_text(
                json.dumps(
                    {
                        "schema": "moduflow.config.v1",
                        "git": {
                            "remote": "https://oauth2:secret@github.com/Owner/Repo.git"
                        },
                    }
                ),
                encoding="utf-8",
            )

            proposal = project_profile.build_repository_identity_proposal(root)

        self.assertTrue(proposal["requires_confirmation"])
        self.assertIsNone(proposal["proposed_identity"])
        self.assertEqual(proposal["legacy_remote_candidate"], "github.com/owner/repo")
        self.assertNotIn("secret", json.dumps(proposal))

    def test_explicit_remote_identity_write_preserves_unrelated_config_and_profile_content(self):
        project_profile = load_module("project_profile", "scripts/project_profile.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config_path = root / ".moduflow" / "config.json"
            config_path.parent.mkdir()
            config_path.write_text(
                json.dumps(
                    {
                        "schema": "moduflow.config.v1",
                        "project_name": "Example",
                        "git": {"required": True, "remote": "https://github.com/Old/Repo"},
                        "paths": {"issues": "custom-issues"},
                    }
                ),
                encoding="utf-8",
            )
            profile_path = root / ".moduflow" / "project-profile.md"
            profile_path.write_text(
                "# Existing Profile\n\n## Private Operating Note\n\nKeep this text.\n",
                encoding="utf-8",
            )
            proposal = project_profile.build_repository_identity_proposal(
                root,
                canonical_repository="git@github.com:Owner/Repo.git",
                provider="github",
                remote_name_hint="upstream",
                base_branch="main",
                lifecycle="active",
            )

            result = project_profile.apply_repository_identity_proposal(root, proposal)

            config = json.loads(config_path.read_text(encoding="utf-8"))
            profile = profile_path.read_text(encoding="utf-8")

        self.assertTrue(result["written"])
        self.assertEqual(config["project_name"], "Example")
        self.assertEqual(config["paths"], {"issues": "custom-issues"})
        self.assertEqual(config["git"]["remote"], "https://github.com/Old/Repo")
        self.assertEqual(
            config["git"]["identity"]["canonical_repository"],
            "github.com/owner/repo",
        )
        self.assertEqual(config["git"]["identity"]["remote_name_hint"], "upstream")
        self.assertIn("Keep this text.", profile)
        self.assertIn("Canonical repository: `github.com/owner/repo`", profile)
        self.assertIn("Base branch: `main`", profile)

    def test_local_only_proposal_omits_remote_identity_fields(self):
        project_profile = load_module("project_profile", "scripts/project_profile.py")
        with tempfile.TemporaryDirectory() as tmp:
            proposal = project_profile.build_repository_identity_proposal(
                tmp,
                local_only=True,
                provider="generic",
                base_branch="main",
                lifecycle="active",
            )

        identity = proposal["proposed_identity"]
        self.assertEqual(identity["mode"], "local_only")
        self.assertNotIn("canonical_repository", identity)
        self.assertNotIn("remote_name_hint", identity)

    def test_repository_projection_update_is_idempotent(self):
        project_profile = load_module("project_profile", "scripts/project_profile.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile_path = root / ".moduflow" / "project-profile.md"
            profile_path.parent.mkdir()
            profile_path.write_text("# Existing\n", encoding="utf-8")
            proposal = project_profile.build_repository_identity_proposal(
                root,
                canonical_repository="github.com/Owner/Repo",
                provider="github",
                remote_name_hint="origin",
                base_branch="main",
                lifecycle="active",
            )

            project_profile.apply_repository_identity_proposal(root, proposal)
            first = profile_path.read_text(encoding="utf-8")
            project_profile.apply_repository_identity_proposal(root, proposal)
            second = profile_path.read_text(encoding="utf-8")

        self.assertEqual(first, second)
        self.assertEqual(first.count("<!-- moduflow:repository-identity:start -->"), 1)

    def test_invalid_repository_lifecycle_is_rejected_before_write(self):
        project_profile = load_module("project_profile", "scripts/project_profile.py")
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                project_profile.build_repository_identity_proposal(
                    tmp,
                    canonical_repository="github.com/Owner/Repo",
                    provider="github",
                    remote_name_hint="origin",
                    base_branch="main",
                    lifecycle="frozen",
                )


if __name__ == "__main__":
    unittest.main()
