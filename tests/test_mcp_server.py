import importlib.util
import json
import tempfile
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_module(name, relative_path):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


mcp_server = load_module("mcp_server", "scripts/mcp_server.py")


def scaffold(root):
    (root / "issues").mkdir()
    (root / "issues" / "001-alpha.md").write_text(
        "# Issue: `001-alpha`\n\n**Status: done** — created 2026-07-01.\n",
        encoding="utf-8",
    )
    (root / "issues" / "002-beta.md").write_text(
        "# Issue: `002-beta`\n\n"
        "**Status: active** — created 2026-07-02.\n\n"
        "## Outcome\n\n"
        "Beta does the thing.\n\n"
        "## Links\n\n"
        "- GitHub: https://github.com/o/r/issues/5\n\n"
        "## Next Command\n\n"
        "`product:status`\n",
        encoding="utf-8",
    )
    (root / "issues" / "003-gamma.md").write_text(
        "# Issue: `003-gamma`\n\n**Status: backlog** — created 2026-07-03.\n",
        encoding="utf-8",
    )
    (root / ".moduflow").mkdir()
    (root / ".moduflow" / "state.json").write_text(
        json.dumps(
            {
                "schema": "moduflow.state.v1",
                "phase": "spec",
                "active_goal": "g",
                "active_issue": "002-beta",
                "last_command": "product:status",
                "next_command": "product:plan",
                "blockers": [],
                "updated_at": "2026-07-05",
            }
        )
        + "\n",
        encoding="utf-8",
    )


class MCPServerTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        scaffold(self.root)

    def test_initialize_returns_protocol_and_server_info(self):
        req = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
        resp = mcp_server.handle_request(req, self.root)
        self.assertEqual(resp["id"], 1)
        self.assertEqual(resp["jsonrpc"], "2.0")
        result = resp["result"]
        self.assertIn("protocolVersion", result)
        self.assertEqual(result["serverInfo"]["name"], "moduflow")
        self.assertIn("tools", result["capabilities"])

    def test_notifications_initialized_returns_none(self):
        req = {"jsonrpc": "2.0", "method": "notifications/initialized"}
        resp = mcp_server.handle_request(req, self.root)
        self.assertIsNone(resp)

    def test_tools_list_returns_four_tools_with_schema(self):
        req = {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}
        resp = mcp_server.handle_request(req, self.root)
        tools = resp["result"]["tools"]
        self.assertEqual(len(tools), 4)
        for tool in tools:
            self.assertIn("name", tool)
            self.assertIn("description", tool)
            self.assertIn("inputSchema", tool)

    def test_moduflow_issues_no_filter_returns_all_sorted(self):
        req = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {"name": "moduflow_issues", "arguments": {}},
        }
        resp = mcp_server.handle_request(req, self.root)
        payload = json.loads(resp["result"]["content"][0]["text"])
        self.assertEqual(payload["schema"], "moduflow.mcp.v1")
        ids = [item["id"] for item in payload["issues"]]
        self.assertEqual(ids, ["001-alpha", "002-beta", "003-gamma"])

    def test_moduflow_issues_status_filter(self):
        req = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {"name": "moduflow_issues", "arguments": {"status": "backlog"}},
        }
        resp = mcp_server.handle_request(req, self.root)
        payload = json.loads(resp["result"]["content"][0]["text"])
        ids = [item["id"] for item in payload["issues"]]
        self.assertEqual(ids, ["003-gamma"])

    def test_moduflow_issue_get_known_id(self):
        req = {
            "jsonrpc": "2.0",
            "id": 5,
            "method": "tools/call",
            "params": {"name": "moduflow_issue_get", "arguments": {"id": "002-beta"}},
        }
        resp = mcp_server.handle_request(req, self.root)
        payload = json.loads(resp["result"]["content"][0]["text"])
        self.assertEqual(payload["status"], "active")
        self.assertEqual(payload["github"], "https://github.com/o/r/issues/5")
        self.assertIn("Beta does the thing.", payload["outcome"])

    def test_moduflow_issue_get_unknown_id_returns_error_payload_not_exception(self):
        req = {
            "jsonrpc": "2.0",
            "id": 6,
            "method": "tools/call",
            "params": {"name": "moduflow_issue_get", "arguments": {"id": "999-nope"}},
        }
        resp = mcp_server.handle_request(req, self.root)
        payload = json.loads(resp["result"]["content"][0]["text"])
        self.assertIn("error", payload)
        self.assertNotIn("error", resp)

    def test_moduflow_issue_get_missing_id_arg_is_json_rpc_error(self):
        req = {
            "jsonrpc": "2.0",
            "id": 7,
            "method": "tools/call",
            "params": {"name": "moduflow_issue_get", "arguments": {}},
        }
        resp = mcp_server.handle_request(req, self.root)
        self.assertEqual(resp["error"]["code"], -32602)

    def test_moduflow_status_reflects_state_and_issue_counts(self):
        req = {
            "jsonrpc": "2.0",
            "id": 8,
            "method": "tools/call",
            "params": {"name": "moduflow_status", "arguments": {}},
        }
        resp = mcp_server.handle_request(req, self.root)
        payload = json.loads(resp["result"]["content"][0]["text"])
        self.assertEqual(payload["active_issue"], "002-beta")
        self.assertEqual(payload["issue_counts"], {"done": 1, "active": 1, "backlog": 1})
        # Review finding: state.json's own schema key clobbered the tool
        # contract version — the payload must carry both, disambiguated.
        self.assertEqual(payload["schema"], "moduflow.mcp.v1")
        self.assertEqual(payload["state_schema"], "moduflow.state.v1")

    def test_issue_get_rejects_absolute_path_traversal(self):
        outside = Path(self._tmp.name) / "secret.md"
        outside.write_text("# Issue: secret\n\n## Outcome\n\ntop secret\n", encoding="utf-8")
        req = {
            "jsonrpc": "2.0",
            "id": 80,
            "method": "tools/call",
            "params": {"name": "moduflow_issue_get", "arguments": {"id": str(outside.with_suffix(""))}},
        }
        resp = mcp_server.handle_request(req, self.root)
        payload = json.loads(resp["result"]["content"][0]["text"])
        self.assertIn("error", payload)
        self.assertNotIn("top secret", resp["result"]["content"][0]["text"])

    def test_issue_get_rejects_relative_path_traversal(self):
        outside = Path(self._tmp.name) / "leak.md"
        outside.write_text("# Issue: leak\n\n## Outcome\n\nleaked\n", encoding="utf-8")
        req = {
            "jsonrpc": "2.0",
            "id": 81,
            "method": "tools/call",
            "params": {"name": "moduflow_issue_get", "arguments": {"id": "../leak"}},
        }
        resp = mcp_server.handle_request(req, self.root)
        payload = json.loads(resp["result"]["content"][0]["text"])
        self.assertIn("error", payload)
        self.assertNotIn("leaked", resp["result"]["content"][0]["text"])

    def test_non_object_json_line_is_invalid_request_not_crash(self):
        for raw in ("null", "[1,2,3]", "42"):
            with self.subTest(raw=raw):
                resp = mcp_server._handle_line(raw, self.root)
                self.assertEqual(resp["error"]["code"], -32600)

    def test_tool_internal_error_becomes_minus_32603_and_loop_survives(self):
        # A directory named *.md used to crash list_issues and kill the loop.
        (self.root / "issues" / "broken.md").mkdir()
        req_line = json.dumps({
            "jsonrpc": "2.0",
            "id": 82,
            "method": "tools/call",
            "params": {"name": "moduflow_issues", "arguments": {}},
        })
        resp = mcp_server._handle_line(req_line, self.root)
        # Hardened list_issues skips the directory, so this now succeeds —
        # and a follow-up request still works (loop-survival contract).
        self.assertNotIn("error", resp)
        follow_up = mcp_server._handle_line(
            json.dumps({"jsonrpc": "2.0", "id": 83, "method": "ping"}), self.root
        )
        self.assertEqual(follow_up["result"], {})

    def test_handle_line_catches_handler_exceptions_as_internal_error(self):
        # Force an exception inside handle_request via an unreadable state file.
        (self.root / ".moduflow" / "state.json").unlink()
        (self.root / ".moduflow" / "state.json").mkdir()  # a dir named state.json
        req_line = json.dumps({
            "jsonrpc": "2.0",
            "id": 84,
            "method": "tools/call",
            "params": {"name": "moduflow_status", "arguments": {}},
        })
        resp = mcp_server._handle_line(req_line, self.root)
        # Either the tool's own guard returns an error payload, or the
        # top-level guard returns -32603 — both are non-crash outcomes.
        if "error" in resp:
            self.assertEqual(resp["error"]["code"], -32603)
        else:
            payload = json.loads(resp["result"]["content"][0]["text"])
            self.assertIn("error", payload)

    def test_unknown_method_is_json_rpc_error(self):
        req = {"jsonrpc": "2.0", "id": 9, "method": "not/a/method"}
        resp = mcp_server.handle_request(req, self.root)
        self.assertEqual(resp["error"]["code"], -32601)

    def test_unknown_tool_name_is_json_rpc_error(self):
        req = {
            "jsonrpc": "2.0",
            "id": 10,
            "method": "tools/call",
            "params": {"name": "moduflow_nonexistent", "arguments": {}},
        }
        resp = mcp_server.handle_request(req, self.root)
        self.assertEqual(resp["error"]["code"], -32602)

    def test_ping(self):
        req = {"jsonrpc": "2.0", "id": 11, "method": "ping"}
        resp = mcp_server.handle_request(req, self.root)
        self.assertEqual(resp["id"], 11)
        self.assertEqual(resp["result"], {})

    def test_malformed_json_line_returns_parse_error(self):
        resp = mcp_server._handle_line("{not valid json", self.root)
        self.assertEqual(resp["error"]["code"], -32700)
        self.assertEqual(resp["id"], None)

    def test_valid_line_delegates_to_handle_request(self):
        line = json.dumps({"jsonrpc": "2.0", "id": 12, "method": "ping"})
        resp = mcp_server._handle_line(line, self.root)
        self.assertEqual(resp["id"], 12)

    def test_list_issues_unit(self):
        lc = load_module("project_lifecycle", "scripts/project_lifecycle.py")
        items = lc.list_issues(self.root)
        self.assertEqual(len(items), 3)
        by_id = {item["id"]: item for item in items}
        self.assertEqual(by_id["001-alpha"]["status"], "done")
        self.assertEqual(by_id["002-beta"]["status"], "active")
        self.assertEqual(by_id["003-gamma"]["status"], "backlog")
        self.assertEqual(by_id["001-alpha"]["title"], "001-alpha")

    def test_doctor_tool_is_exception_safe(self):
        req = {
            "jsonrpc": "2.0",
            "id": 13,
            "method": "tools/call",
            "params": {"name": "moduflow_doctor", "arguments": {}},
        }
        resp = mcp_server.handle_request(req, self.root)
        self.assertIsNotNone(resp)
        payload = json.loads(resp["result"]["content"][0]["text"])
        self.assertEqual(payload["schema"], "moduflow.mcp.v1")
        # Fixture lacks full moduflow footprint — accept either a projected
        # summary or an error payload, but it must not have raised.
        self.assertTrue("initialized" in payload or "error" in payload)


if __name__ == "__main__":
    unittest.main()
