import json
import tempfile
import unittest
from pathlib import Path

from scripts import vendor_freshness
from scripts.project_sync import CommandResult


class FakeRunner:
    def __init__(self, responses):
        self.responses = responses

    def __call__(self, args, cwd):
        key = tuple(args)
        if key not in self.responses:
            return CommandResult(1, "", f"unexpected command: {' '.join(args)}")
        value = self.responses[key]
        if isinstance(value, CommandResult):
            return value
        return CommandResult(0, value, "")


def _commit_json(sha, date):
    return json.dumps({"sha": sha, "commit": {"committer": {"date": date}}})


LOCK_DATA = {
    "version": 1,
    "sources": [
        {
            "id": "never-synced",
            "url": "https://github.com/acme/never-synced",
            "type": "github",
            "pin": "main",
        },
        {
            "id": "up-to-date",
            "url": "https://github.com/acme/up-to-date",
            "type": "github",
            "pin": "main",
            "last_synced": {"sha": "aaa111", "date": "2026-06-01T00:00:00Z"},
        },
        {
            "id": "stale",
            "url": "https://github.com/acme/stale",
            "type": "github",
            "pin": "main",
            "last_synced": {"sha": "old000", "date": "2026-05-01T00:00:00Z"},
        },
        {
            "id": "unreachable",
            "url": "https://github.com/acme/unreachable",
            "type": "github",
            "pin": "main",
        },
        {
            "id": "codex-local",
            "url": "local:codex-plugin/product-design",
            "type": "local-plugin",
            "pin": "0.1.44",
        },
    ],
}


def _write_lock(tmp_dir):
    path = Path(tmp_dir) / "vendor.lock.json"
    path.write_text(json.dumps(LOCK_DATA), encoding="utf-8")
    return path


class VendorFreshnessTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.lock_path = _write_lock(self._tmp.name)

    def _runner(self):
        return FakeRunner(
            {
                ("gh", "api", "repos/acme/never-synced/commits/main"): _commit_json("new111", "2026-07-01T00:00:00Z"),
                ("gh", "api", "repos/acme/up-to-date/commits/main"): _commit_json("aaa111", "2026-06-01T00:00:00Z"),
                ("gh", "api", "repos/acme/stale/commits/main"): _commit_json("new222", "2026-07-02T00:00:00Z"),
                ("gh", "api", "repos/acme/unreachable/commits/main"): CommandResult(
                    1, "", "gh: HTTP 404 (Not Found)"
                ),
            }
        )

    def test_never_synced_source_is_drifted(self):
        path = self.lock_path
        results = vendor_freshness.check_vendor_freshness(path, runner=self._runner())
        result = next(r for r in results if r["id"] == "never-synced")
        self.assertTrue(result["drifted"])
        self.assertIsNone(result["last_synced_sha"])
        self.assertEqual(result["latest_sha"], "new111")

    def test_matching_sha_is_not_drifted(self):
        path = self.lock_path
        results = vendor_freshness.check_vendor_freshness(path, runner=self._runner())
        result = next(r for r in results if r["id"] == "up-to-date")
        self.assertFalse(result["drifted"])

    def test_differing_sha_is_drifted(self):
        path = self.lock_path
        results = vendor_freshness.check_vendor_freshness(path, runner=self._runner())
        result = next(r for r in results if r["id"] == "stale")
        self.assertTrue(result["drifted"])
        self.assertEqual(result["last_synced_sha"], "old000")
        self.assertEqual(result["latest_sha"], "new222")

    def test_api_failure_sets_error_without_raising(self):
        path = self.lock_path
        results = vendor_freshness.check_vendor_freshness(path, runner=self._runner())
        result = next(r for r in results if r["id"] == "unreachable")
        self.assertIsNotNone(result["error"])
        self.assertIn("404", result["error"])
        # Other sources still got checked despite this one failing.
        ids = {r["id"] for r in results}
        self.assertIn("never-synced", ids)

    def test_local_plugin_sources_are_skipped(self):
        path = self.lock_path
        results = vendor_freshness.check_vendor_freshness(path, runner=self._runner())
        ids = {r["id"] for r in results}
        self.assertNotIn("codex-local", ids)

    def test_sync_writes_last_synced_back_to_lock_file(self):
        path = self.lock_path
        results = vendor_freshness.check_vendor_freshness(path, runner=self._runner())
        vendor_freshness.sync_last_synced(path, results)

        updated = json.loads(path.read_text(encoding="utf-8"))
        by_id = {s["id"]: s for s in updated["sources"]}
        self.assertEqual(by_id["never-synced"]["last_synced"]["sha"], "new111")
        self.assertEqual(by_id["stale"]["last_synced"]["sha"], "new222")
        # A source whose check errored keeps its prior last_synced untouched.
        self.assertNotIn("last_synced", by_id["unreachable"])


if __name__ == "__main__":
    unittest.main()
