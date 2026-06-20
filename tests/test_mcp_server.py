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

issue_generator = load_module("issue_generator", "scripts/issue_generator.py")
mcp_server = load_module("mcp_server", "scripts/mcp_server.py")

class MCPServerTests(unittest.TestCase):
    def test_mcp_default_list_tools(self):
        # Default run with empty stdin returns tools lists
        import sys
        from io import StringIO
        
        orig_stdin = sys.stdin
        orig_stdout = sys.stdout
        
        try:
            sys.stdin = StringIO("")
            sys.stdout = StringIO()
            mcp_server.main()
            output = json.loads(sys.stdout.getvalue())
            self.assertIn("tools", output)
            self.assertEqual(len(output["tools"]), 2)
            self.assertEqual(output["tools"][0]["name"], "moduflow_status")
        finally:
            sys.stdin = orig_stdin
            sys.stdout = orig_stdout

    def test_mcp_tools_list_method(self):
        import sys
        from io import StringIO
        
        req = json.dumps({"method": "tools/list", "id": "1"})
        orig_stdin = sys.stdin
        orig_stdout = sys.stdout
        
        try:
            sys.stdin = StringIO(req)
            sys.stdout = StringIO()
            mcp_server.main()
            output = json.loads(sys.stdout.getvalue())
            self.assertEqual(output["id"], "1")
            self.assertIn("tools", output["result"])
        finally:
            sys.stdin = orig_stdin
            sys.stdout = orig_stdout

    def test_mcp_tools_call_status_empty(self):
        import sys
        from io import StringIO
        
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            orig_root = mcp_server.ROOT
            mcp_server.ROOT = tmp_root
            
            req = json.dumps({"method": "tools/call", "params": {"name": "moduflow_status"}, "id": "2"})
            orig_stdin = sys.stdin
            orig_stdout = sys.stdout
            
            try:
                sys.stdin = StringIO(req)
                sys.stdout = StringIO()
                mcp_server.main()
                output = json.loads(sys.stdout.getvalue())
                self.assertEqual(output["id"], "2")
                self.assertIn("No active ModuFlow loop-state.json", output["result"]["content"][0]["text"])
            finally:
                sys.stdin = orig_stdin
                sys.stdout = orig_stdout
                mcp_server.ROOT = orig_root

    def test_mcp_tools_call_decompose_goal(self):
        import sys
        from io import StringIO
        
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            (tmp_root / "issues").mkdir()
            # Update ROOT constant in mcp_server so it writes inside temporary directory
            orig_root = mcp_server.ROOT
            mcp_server.ROOT = tmp_root
            
            req = json.dumps({
                "method": "tools/call",
                "params": {
                    "name": "moduflow_decompose_goal",
                    "arguments": {"goal": "Test Goal Decomposition"}
                },
                "id": "3"
            })
            
            orig_stdin = sys.stdin
            orig_stdout = sys.stdout
            
            try:
                sys.stdin = StringIO(req)
                sys.stdout = StringIO()
                mcp_server.main()
                output = json.loads(sys.stdout.getvalue())
                
                self.assertEqual(output["id"], "3")
                self.assertIn("Successfully decomposed goal", output["result"]["content"][0]["text"])
                
                # Check that 3 issues were created
                issue_files = list((tmp_root / "issues").glob("*.md"))
                self.assertEqual(len(issue_files), 3)
            finally:
                sys.stdin = orig_stdin
                sys.stdout = orig_stdout
                mcp_server.ROOT = orig_root

    def test_multi_language_benchmarking_translation(self):
        # Verify translations in generate_issues_from_goal
        issues = issue_generator.generate_issues_from_goal("Sample Goal", "industry best practices")
        self.assertIn("업계 최고 모범 사례 (Best Practices)", issues[0]["summary"])
        
        issues_rfc = issue_generator.generate_issues_from_goal("Sample Goal", "OAuth2 RFC standards")
        self.assertIn("OAuth2 RFC 보안 표준 스펙", issues_rfc[0]["summary"])
