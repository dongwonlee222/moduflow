import json
import tempfile
import unittest
from pathlib import Path

from scripts import version_bump


class ClassifyBumpTests(unittest.TestCase):
    def test_feat_is_minor(self):
        self.assertEqual(version_bump.classify_bump("feat: implement issue 059 — auto fetch in repo sync"), "minor")

    def test_fix_is_patch(self):
        self.assertEqual(version_bump.classify_bump("fix: correct issue 029 stale status"), "patch")

    def test_scoped_feat_is_minor(self):
        self.assertEqual(version_bump.classify_bump("feat(053): implement vendor freshness gate"), "minor")

    def test_bang_is_major(self):
        self.assertEqual(version_bump.classify_bump("feat!: remove legacy loop-state gate"), "major")

    def test_breaking_change_footer_is_major(self):
        message = "fix: change state schema\n\nBREAKING CHANGE: state.json field renamed"
        self.assertEqual(version_bump.classify_bump(message), "major")

    def test_docs_is_none(self):
        self.assertEqual(version_bump.classify_bump("docs: release issue 034 memory workflow"), "none")

    def test_chore_is_none(self):
        self.assertEqual(version_bump.classify_bump("chore: register backlog issues 053-055"), "none")

    def test_unrecognized_prefix_is_none(self):
        self.assertEqual(
            version_bump.classify_bump("merge: bring in issues 056/057/058 from codex/058-..."), "none"
        )


class BumpVersionTests(unittest.TestCase):
    def test_minor_bump_resets_patch(self):
        self.assertEqual(version_bump.bump_version("0.2.15", "minor"), "0.3.0")

    def test_patch_bump_increments_patch(self):
        self.assertEqual(version_bump.bump_version("0.2.15", "patch"), "0.2.16")

    def test_major_bump_resets_minor_and_patch(self):
        self.assertEqual(version_bump.bump_version("0.2.15", "major"), "1.0.0")

    def test_none_bump_is_unchanged(self):
        self.assertEqual(version_bump.bump_version("0.2.15", "none"), "0.2.15")


class ApplyBumpTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.plugin_json_path = Path(self._tmp.name) / "plugin.json"
        self.plugin_json_path.write_text(json.dumps({"name": "moduflow", "version": "0.2.15"}), encoding="utf-8")

    def test_feat_message_bumps_and_writes_file(self):
        new_version = version_bump.apply_bump(self.plugin_json_path, "feat: implement issue 063")
        self.assertEqual(new_version, "0.3.0")
        updated = json.loads(self.plugin_json_path.read_text(encoding="utf-8"))
        self.assertEqual(updated["version"], "0.3.0")

    def test_docs_message_leaves_file_untouched(self):
        before = self.plugin_json_path.read_text(encoding="utf-8")
        new_version = version_bump.apply_bump(self.plugin_json_path, "docs: update readme")
        self.assertEqual(new_version, "0.2.15")
        after = self.plugin_json_path.read_text(encoding="utf-8")
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
