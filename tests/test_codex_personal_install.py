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


class CodexPersonalInstallTests(unittest.TestCase):
    def create_plugin_source(self, root):
        source = root / "source"
        (source / ".codex-plugin").mkdir(parents=True)
        (source / ".codex-plugin" / "plugin.json").write_text(
            json.dumps({"name": "moduflow", "version": "0.2.0+codex.test"}) + "\n",
            encoding="utf-8",
        )
        (source / "skills").mkdir()
        (source / "templates" / "issues").mkdir(parents=True)
        (source / "templates" / "specs").mkdir(parents=True)
        (source / "templates" / "issues" / "issue.md").write_text("issue template\n", encoding="utf-8")
        (source / "templates" / "specs" / "spec.md").write_text("spec template\n", encoding="utf-8")
        for development_dir in ("issues", "specs", "tests", "sessions"):
            (source / development_dir).mkdir()
            (source / development_dir / "development-artifact.md").write_text("dev only\n", encoding="utf-8")
        (source / "README.md").write_text("# ModuFlow\n", encoding="utf-8")
        return source

    def test_install_codex_personal_plugin_populates_marketplace_cache_and_config(self):
        installer = load_module("register_codex_personal_marketplace", "scripts/register_codex_personal_marketplace.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self.create_plugin_source(root)
            home = root / "home"

            result = installer.install_codex_personal_plugin(source, home)

            marketplace = json.loads((home / ".agents" / "plugins" / "marketplace.json").read_text(encoding="utf-8"))
            self.assertEqual(marketplace["plugins"][0]["name"], "moduflow")
            self.assertEqual(marketplace["plugins"][0]["policy"]["installation"], "INSTALLED_BY_DEFAULT")
            self.assertTrue((home / "plugins" / "moduflow").is_symlink())
            self.assertTrue((home / ".codex" / "plugins" / "local" / "moduflow").is_symlink())
            cache = home / ".codex" / "plugins" / "cache" / "personal" / "moduflow" / "0.2.0+codex.test"
            self.assertTrue(cache.is_dir())
            self.assertTrue((cache / "skills").is_dir())
            self.assertTrue((cache / "templates" / "issues" / "issue.md").is_file())
            self.assertTrue((cache / "templates" / "specs" / "spec.md").is_file())
            for development_dir in ("issues", "specs", "tests", "sessions"):
                self.assertFalse((cache / development_dir).exists())
            config = (home / ".codex" / "config.toml").read_text(encoding="utf-8")
            self.assertIn('[plugins."moduflow@personal"]', config)
            self.assertIn("enabled = true", config)
            self.assertEqual(result["plugin"], "moduflow@personal")

    def test_cache_copy_ships_only_runtime_validation_fixtures(self):
        installer = load_module(
            "register_codex_personal_marketplace_distribution",
            "scripts/register_codex_personal_marketplace.py",
        )
        with tempfile.TemporaryDirectory() as tmp:
            cache = installer.copy_plugin_cache(
                ROOT, Path(tmp) / "home", "0.0.0+codex.test"
            )

            expected = {
                "tests/fixtures/issue-schema/BIZ-033.md",
                "tests/fixtures/issue-schema/BIZ-038.md",
                "tests/fixtures/issue-schema/BIZ-039.md",
                "tests/fixtures/issue-schema/BIZ-040.md",
                "tests/fixtures/issue-schema/legacy-markdown.md",
                "tests/fixtures/capability-routing/cases.json",
                "tests/fixtures/spec-kit-selective-validation/cases.json",
                "tests/fixtures/spec-kit-selective-validation/results/clarify.json",
                "tests/fixtures/spec-kit-selective-validation/results/analyze.json",
                "tests/fixtures/spec-kit-selective-validation/results/checklist.json",
                "tests/fixtures/spec-kit-selective-validation/results/converge.json",
            }
            runtime_evidence = {
                "specs/098-speckit-selective-validation-adapter/pilot-report.md",
                "specs/098-speckit-selective-validation-adapter/status.md",
            }
            self.assertTrue((cache / "scripts" / "project_issue_schema.py").is_file())
            self.assertTrue((cache / "scripts" / "sync_spec_kit_templates.py").is_file())
            self.assertTrue((cache / "templates" / "moduflow-capabilities.json").is_file())
            self.assertTrue(all((cache / path).is_file() for path in expected))
            self.assertTrue(all((cache / path).is_file() for path in runtime_evidence))
            self.assertFalse((cache / "tests" / "test_issue_generator.py").exists())
            self.assertEqual(
                {
                    path.relative_to(cache).as_posix()
                    for path in (cache / "tests").rglob("*")
                    if path.is_file()
                },
                expected,
            )

            validator = load_module(
                "validate_moduflow_cached_distribution",
                cache / "scripts" / "validate_moduflow.py",
            )
            validation = validator.validate_moduflow(cache)
            self.assertTrue(validation["valid"], validation["errors"])

    def test_cached_router_uses_cache_registry_with_lightweight_target(self):
        installer = load_module(
            "register_codex_personal_marketplace_routing",
            "scripts/register_codex_personal_marketplace.py",
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cache = installer.copy_plugin_cache(ROOT, root / "home", "0.0.0+codex.test")
            target = root / "target-project"
            target.mkdir()

            completed = subprocess.run(
                [
                    sys.executable,
                    str(cache / "scripts" / "capability_routing.py"),
                    "Analyze conversion",
                    str(target),
                    "--issue-id",
                    "001-conversion",
                    "--available",
                    "data-analytics",
                ],
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["outcome"], "delegate")
            self.assertEqual(payload["stages"][0]["adapter_id"], "data-analytics")


if __name__ == "__main__":
    unittest.main()
