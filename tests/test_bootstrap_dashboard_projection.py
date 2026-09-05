"""Every bootstrap path must write a dashboard the stop hook can project.

Reported via workspace/inbox.md 2026-09-05: `product:migrate --mode overlay`
wrote `workspace/dashboard.md` containing only `# Dashboard`, and the stop hook
then raised `ValueError: dashboard requires an Active Issue section` on every
session end. Verified while fixing it that `product:start`'s canonical template
has the same defect, so the guard covers both entry points rather than the one
that was reported.
"""
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts import project_lifecycle, project_migrate  # noqa: E402


def _project(dashboard_bytes):
    """Run the projection the stop hook runs, with no active issue."""
    return project_lifecycle.render_dashboard_projection(
        dashboard_bytes,
        active_issue=None,
        phase=None,
        source_path=None,
    )


class BootstrapDashboardProjectionTests(unittest.TestCase):
    def test_product_start_template_survives_the_projection(self):
        template = (REPO_ROOT / "templates/workspace/dashboard.md").read_bytes()
        _project(template)

    def test_product_migrate_template_survives_the_projection(self):
        template = project_migrate.WORKSPACE_FILES["dashboard.md"].encode("utf-8")
        _project(template)

    def test_every_workspace_template_named_dashboard_survives(self):
        """Catches a third bootstrap path added later without this guard."""
        for path in sorted((REPO_ROOT / "templates").rglob("dashboard.md")):
            with self.subTest(template=str(path.relative_to(REPO_ROOT))):
                _project(path.read_bytes())

    def test_projection_still_rejects_a_dashboard_with_no_section(self):
        """The guard must not be satisfied by weakening the projection."""
        with self.assertRaises(ValueError):
            _project(b"# Dashboard\n\nnothing here\n")

    def test_projected_bootstrap_dashboard_is_stable_on_a_second_pass(self):
        once = _project((REPO_ROOT / "templates/workspace/dashboard.md").read_bytes())
        self.assertEqual(once, _project(once))


if __name__ == "__main__":
    unittest.main(verbosity=2)
