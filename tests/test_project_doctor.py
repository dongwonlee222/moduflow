import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from scripts import project_doctor


class CheckHookLogTests(unittest.TestCase):
    """Test hook log parsing and filtering."""

    def setUp(self):
        """Create a temporary directory for each test."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.logs_dir = self.root / ".moduflow" / "logs"
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.logs_dir / "hooks.log"

    def tearDown(self):
        """Clean up temporary directory."""
        self.temp_dir.cleanup()

    def test_absent_log_file_returns_empty(self):
        """Absent .moduflow/logs/hooks.log returns empty list (silent)."""
        result = project_doctor.check_hook_log(self.root)
        self.assertEqual(result, [])

    def test_empty_log_file_returns_empty(self):
        """Empty or whitespace-only log file returns empty list."""
        self.log_file.write_text("")
        result = project_doctor.check_hook_log(self.root)
        self.assertEqual(result, [])

        self.log_file.write_text("   \n  \n")
        result = project_doctor.check_hook_log(self.root)
        self.assertEqual(result, [])

    def test_recent_warning_included(self):
        """Recent (within 7 days) warn entries are included."""
        now = datetime.now(timezone.utc)
        recent_ts = (now - timedelta(days=1)).isoformat()

        log_content = f"{recent_ts} session_start warn incomplete git state\n"
        self.log_file.write_text(log_content)

        result = project_doctor.check_hook_log(self.root)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["hook"], "session_start")
        self.assertEqual(result[0]["level"], "warn")
        self.assertEqual(result[0]["message"], "incomplete git state")
        self.assertNotIn("malformed", result[0])

    def test_recent_error_included(self):
        """Recent (within 7 days) error entries are included."""
        now = datetime.now(timezone.utc)
        recent_ts = (now - timedelta(days=2)).isoformat()

        log_content = f"{recent_ts} on_stop error failed to sync\n"
        self.log_file.write_text(log_content)

        result = project_doctor.check_hook_log(self.root)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["hook"], "on_stop")
        self.assertEqual(result[0]["level"], "error")
        self.assertEqual(result[0]["message"], "failed to sync")

    def test_old_entries_excluded(self):
        """Entries older than 7 days are excluded."""
        now = datetime.now(timezone.utc)
        old_ts = (now - timedelta(days=8)).isoformat()
        recent_ts = (now - timedelta(days=1)).isoformat()

        log_content = f"{old_ts} session_start warn old entry\n{recent_ts} on_stop error recent entry\n"
        self.log_file.write_text(log_content)

        result = project_doctor.check_hook_log(self.root)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["message"], "recent entry")

    def test_malformed_line_included_with_note(self):
        """Unparseable lines are included as warnings with malformed flag."""
        log_content = "garbage\ninvalid line format\n"
        self.log_file.write_text(log_content)

        result = project_doctor.check_hook_log(self.root)

        # Both malformed lines should be included
        self.assertEqual(len(result), 2)
        for entry in result:
            self.assertTrue(entry.get("malformed", False))
            self.assertIn("malformed hook log entry", entry["message"])

    def test_unparseable_timestamp_included_with_note(self):
        """Lines with unparseable timestamps are included with a note."""
        log_content = "not-a-timestamp session_start warn something happened\n"
        self.log_file.write_text(log_content)

        result = project_doctor.check_hook_log(self.root)

        self.assertEqual(len(result), 1)
        self.assertTrue(result[0].get("malformed", False))
        self.assertIn("unparseable timestamp", result[0].get("note", ""))
        self.assertEqual(result[0]["hook"], "session_start")
        self.assertEqual(result[0]["message"], "something happened")

    def test_capped_at_20_most_recent(self):
        """More than 20 entries are capped, keeping the 20 most recent."""
        now = datetime.now(timezone.utc)
        log_lines = []

        # Create 30 recent entries
        for i in range(30):
            ts = (now - timedelta(hours=i)).isoformat()
            log_lines.append(f"{ts} hook{i} warn entry {i}\n")

        self.log_file.write_text("".join(log_lines))

        result = project_doctor.check_hook_log(self.root)

        self.assertEqual(len(result), 20)
        # Verify sorted by timestamp descending (most recent first)
        # Most recent should be "entry 0"
        self.assertIn("entry 0", result[0]["message"])

    def test_mixed_recent_and_old_capped_correctly(self):
        """Mixed recent and old entries: filter 7 days first, then cap at 20."""
        now = datetime.now(timezone.utc)
        log_lines = []

        # Add 10 old entries (>7 days)
        for i in range(10):
            ts = (now - timedelta(days=10 + i)).isoformat()
            log_lines.append(f"{ts} hook warn old {i}\n")

        # Add 15 recent entries (<7 days)
        for i in range(15):
            ts = (now - timedelta(hours=i)).isoformat()
            log_lines.append(f"{ts} hook warn recent {i}\n")

        self.log_file.write_text("".join(log_lines))

        result = project_doctor.check_hook_log(self.root)

        # Should have only 15 (all recent, old filtered out)
        self.assertEqual(len(result), 15)
        # All should be recent messages
        for entry in result:
            self.assertIn("recent", entry["message"])

    def test_iso_timestamp_with_z_suffix(self):
        """ISO timestamps with 'Z' suffix (UTC) are parsed correctly."""
        now = datetime.now(timezone.utc)
        ts_with_z = now.isoformat().replace("+00:00", "Z")
        log_content = f"{ts_with_z} session_start warn test\n"
        self.log_file.write_text(log_content)

        result = project_doctor.check_hook_log(self.root)

        # Should parse without error and be included
        self.assertEqual(len(result), 1)

    def test_iso_timestamp_with_microseconds(self):
        """ISO timestamps with microseconds are parsed correctly."""
        ts_with_micro = "2024-01-15T10:30:45.123456+00:00"
        log_content = f"{ts_with_micro} session_start warn test\n"
        self.log_file.write_text(log_content)

        result = project_doctor.check_hook_log(self.root)

        # Old entry, should be filtered out if >7 days, but parsing should work
        # This is a hard-coded old date, so it will be excluded
        self.assertEqual(len(result), 0)

    def test_message_with_spaces_preserved(self):
        """Message content with spaces is preserved correctly."""
        now = datetime.now(timezone.utc)
        ts = now.isoformat()
        msg = "this is a message with multiple spaces and words"
        log_content = f"{ts} hook warn {msg}\n"
        self.log_file.write_text(log_content)

        result = project_doctor.check_hook_log(self.root)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["message"], msg)

    def test_never_crashes_on_read_error(self):
        """check_hook_log never raises exceptions (returns empty on read error)."""
        # Make log dir unreadable (if possible)
        # For this test, we'll just verify it doesn't raise
        self.log_file.write_text("valid entry")

        # This should never raise
        result = project_doctor.check_hook_log(self.root)
        self.assertIsInstance(result, list)

    def test_sorting_most_recent_first(self):
        """Entries are sorted with most recent first."""
        now = datetime.now(timezone.utc)
        log_lines = []

        # Add entries out of order
        ts1 = (now - timedelta(hours=5)).isoformat()
        ts2 = (now - timedelta(hours=2)).isoformat()
        ts3 = (now - timedelta(hours=10)).isoformat()

        log_lines.append(f"{ts1} hook warn first\n")
        log_lines.append(f"{ts2} hook warn second\n")
        log_lines.append(f"{ts3} hook warn third\n")

        self.log_file.write_text("".join(log_lines))

        result = project_doctor.check_hook_log(self.root)

        # Most recent (ts2) should be first
        self.assertIn("second", result[0]["message"])
        self.assertIn("first", result[1]["message"])
        # ts3 is oldest but still within 7 days
        self.assertIn("third", result[2]["message"])

    def test_integration_with_inspect_project(self):
        """Hook log warnings are included in inspect_project result."""
        now = datetime.now(timezone.utc)
        ts = now.isoformat()

        # Create necessary moduflow structure
        (self.root / ".moduflow").mkdir(parents=True, exist_ok=True)
        (self.root / ".moduflow" / "config.json").write_text('{"paths": {}}')
        (self.root / ".moduflow" / "state.json").write_text('{}')

        # Create log entry
        self.log_file.write_text(f"{ts} session_start warn test warning\n")

        # Call inspect_project with preflight disabled (no git needed)
        result = project_doctor.inspect_project(str(self.root), include_preflight=False)

        # Verify hooks section exists and contains the warning
        self.assertIn("hooks", result)
        self.assertEqual(len(result["hooks"]["warnings"]), 1)
        self.assertEqual(result["hooks"]["warnings"][0]["hook"], "session_start")
        self.assertEqual(result["hooks"]["warnings"][0]["level"], "warn")

    def test_recommendation_added_for_hook_warnings(self):
        """A recommendation is added when hook warnings are present."""
        now = datetime.now(timezone.utc)
        ts = now.isoformat()

        # Create necessary moduflow structure
        (self.root / ".moduflow").mkdir(parents=True, exist_ok=True)
        (self.root / ".moduflow" / "config.json").write_text('{"paths": {}}')
        (self.root / ".moduflow" / "state.json").write_text('{}')

        # Create log entries
        self.log_file.write_text(
            f"{ts} hook1 warn test1\n"
            f"{ts} hook2 error test2\n"
        )

        result = project_doctor.inspect_project(str(self.root), include_preflight=False)

        # Find the hook health recommendation
        hook_recs = [r for r in result["recommendation"] if "hook health" in r]
        self.assertEqual(len(hook_recs), 1)
        self.assertIn("2 lifecycle hook event(s)", hook_recs[0])

    def test_no_recommendation_without_warnings(self):
        """No hook recommendation when log is absent or empty."""
        # Create necessary moduflow structure
        (self.root / ".moduflow").mkdir(parents=True, exist_ok=True)
        (self.root / ".moduflow" / "config.json").write_text('{"paths": {}}')
        (self.root / ".moduflow" / "state.json").write_text('{}')

        result = project_doctor.inspect_project(str(self.root), include_preflight=False)

        # Should have no hook health recommendation
        hook_recs = [r for r in result["recommendation"] if "hook health" in r]
        self.assertEqual(len(hook_recs), 0)


class RepositoryIdentityDoctorTests(unittest.TestCase):
    def test_doctor_includes_shared_repository_identity_result_without_reparsing(self):
        expected = {
            "schema": "moduflow.repository-identity.v1",
            "status": "mismatch",
            "expected": {"repository": "github.com/owner/repo", "base_branch": "main"},
            "observed": {"fetch_repositories": ["github.com/other/repo"]},
            "capabilities": {"read": True, "execute": False},
            "reasons": [{"code": "fetch_remote_mismatch", "message": "wrong repository"}],
        }
        calls = []
        original = getattr(project_doctor, "inspect_repository_identity", None)

        def fake_identity(root, runner=None, provider_check=None):
            calls.append((Path(root), runner, provider_check))
            return expected

        project_doctor.inspect_repository_identity = fake_identity
        try:
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                (root / ".moduflow").mkdir()
                (root / ".moduflow" / "config.json").write_text("{}\n", encoding="utf-8")
                (root / ".moduflow" / "state.json").write_text("{}\n", encoding="utf-8")

                result = project_doctor.inspect_project(root, include_preflight=True)
        finally:
            if original is None:
                delattr(project_doctor, "inspect_repository_identity")
            else:
                project_doctor.inspect_repository_identity = original

        self.assertEqual(result["repository_identity"], expected)
        self.assertEqual(len(calls), 1)

    def test_no_preflight_reports_repository_identity_as_skipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".moduflow").mkdir()
            (root / ".moduflow" / "config.json").write_text("{}\n", encoding="utf-8")
            (root / ".moduflow" / "state.json").write_text("{}\n", encoding="utf-8")

            result = project_doctor.inspect_project(root, include_preflight=False)

        self.assertIsNone(result["repository_identity"])
        self.assertIn("repository_identity", result["preflight"]["skipped"])


if __name__ == "__main__":
    unittest.main()
