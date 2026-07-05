import json
import tempfile
import unittest
from pathlib import Path

from scripts import project_doctor


class InstalledPluginStalenessTests(unittest.TestCase):
    def setUp(self):
        self._project_tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._project_tmp.cleanup)
        self.project_root = Path(self._project_tmp.name)

        self._home_tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._home_tmp.cleanup)
        self.home = Path(self._home_tmp.name)

        plugin_dir = self.project_root / ".claude-plugin"
        plugin_dir.mkdir(parents=True, exist_ok=True)
        (plugin_dir / "plugin.json").write_text(
            json.dumps({"name": "moduflow", "version": "0.3.4"}), encoding="utf-8"
        )

    def _write_installed_plugins(self, entries):
        claude_plugins_dir = self.home / ".claude" / "plugins"
        claude_plugins_dir.mkdir(parents=True, exist_ok=True)
        (claude_plugins_dir / "installed_plugins.json").write_text(
            json.dumps({"version": 2, "plugins": {"moduflow@moduflow": entries}}),
            encoding="utf-8",
        )

    def _write_codex_cache_dir(self, dirname):
        cache_dir = self.home / ".codex" / "plugins" / "cache" / "personal" / "moduflow" / dirname
        cache_dir.mkdir(parents=True, exist_ok=True)

    def test_stale_claude_install_reports_warning(self):
        self._write_installed_plugins([{"version": "0.2.6"}])

        result = project_doctor.installed_plugin_staleness(self.project_root, home=self.home)

        self.assertTrue(result["checked"])
        self.assertEqual(len(result["stale"]), 1)
        entry = result["stale"][0]
        self.assertEqual(entry["host"], "claude-code")
        self.assertEqual(entry["installed"], "0.2.6")
        self.assertTrue(
            any("claude plugin marketplace update moduflow" in rec for rec in result["recommendations"])
        )

    def test_current_claude_install_is_clean(self):
        self._write_installed_plugins([{"version": "0.3.4"}])

        result = project_doctor.installed_plugin_staleness(self.project_root, home=self.home)

        self.assertTrue(result["checked"])
        self.assertEqual(result["stale"], [])
        self.assertEqual(result["recommendations"], [])

    def test_no_install_present_is_silent(self):
        result = project_doctor.installed_plugin_staleness(self.project_root, home=self.home)

        self.assertTrue(result["checked"])
        self.assertEqual(result["stale"], [])

    def test_stale_codex_cache_reports_warning(self):
        self._write_codex_cache_dir("0.2.15+codex.123")

        result = project_doctor.installed_plugin_staleness(self.project_root, home=self.home)

        self.assertTrue(result["checked"])
        self.assertEqual(len(result["stale"]), 1)
        entry = result["stale"][0]
        self.assertEqual(entry["host"], "codex")
        self.assertTrue(
            any("register_codex_personal_marketplace.py" in rec for rec in result["recommendations"])
        )

    def test_current_codex_cache_is_clean(self):
        self._write_codex_cache_dir("0.3.4+codex.123")

        result = project_doctor.installed_plugin_staleness(self.project_root, home=self.home)

        self.assertTrue(result["checked"])
        self.assertEqual(result["stale"], [])

    def test_other_plugin_manifest_skips_check(self):
        # A repo for a different plugin must not trigger moduflow comparisons
        # (review finding: name field was ignored, causing spurious warnings).
        (self.project_root / ".claude-plugin" / "plugin.json").write_text(
            json.dumps({"name": "some-other-plugin", "version": "0.2.6"}), encoding="utf-8"
        )
        self._write_installed_plugins([{"version": "9.9.9"}])

        result = project_doctor.installed_plugin_staleness(self.project_root, home=self.home)

        self.assertFalse(result["checked"])
        self.assertEqual(result["stale"], [])

    def test_newest_codex_dir_uses_numeric_order(self):
        # Review finding: lexicographic sort showed 0.3.9 as newer than 0.3.10.
        self._write_codex_cache_dir("0.3.9+codex.1")
        self._write_codex_cache_dir("0.3.10+codex.1")

        result = project_doctor.installed_plugin_staleness(self.project_root, home=self.home)

        self.assertEqual(len(result["stale"]), 1)
        self.assertEqual(result["stale"][0]["installed"], "0.3.10+codex.1")

    def test_missing_repo_manifest_skips_check(self):
        empty_project_tmp = tempfile.TemporaryDirectory()
        self.addCleanup(empty_project_tmp.cleanup)
        empty_project_root = Path(empty_project_tmp.name)

        result = project_doctor.installed_plugin_staleness(empty_project_root, home=self.home)

        self.assertFalse(result["checked"])
        self.assertEqual(result["stale"], [])


if __name__ == "__main__":
    unittest.main()
