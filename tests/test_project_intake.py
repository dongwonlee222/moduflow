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


project_intake = load_module("project_intake", "scripts/project_intake.py")


class ProjectIntakeTests(unittest.TestCase):
    def test_classify_request_detects_dev_work(self):
        result = project_intake.classify_request("로그인 버그 고쳐줘")

        self.assertEqual(result["primary"], "dev")
        self.assertGreater(result["scores"]["dev"], 0)

    def test_classify_request_detects_business_work(self):
        result = project_intake.classify_request("새 사업계획서 린 캔버스 만들어줘")

        self.assertEqual(result["primary"], "business")

    def test_find_related_issues_returns_overlap_without_duplicate_creation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "issues").mkdir()
            (root / "issues" / "042-login-bug-fix.md").write_text(
                "# Issue 042: Login Bug Fix\n\n## Summary\n\nFix login error and session bug.\n",
                encoding="utf-8",
            )

            related = project_intake.find_related_issues(root, "로그인 버그 고쳐줘")

            self.assertEqual(related[0]["issue_id"], "042-login-bug-fix")
            self.assertIn(related[0]["relationship"], {"duplicate_candidate", "related"})

    def test_route_intake_attaches_small_related_request_to_active_issue(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "workspace").mkdir()
            (root / "issues").mkdir()
            (root / "workspace" / "loop-state.json").write_text(
                json.dumps({
                    "schema": "moduflow.loop-state.v2",
                    "goal_id": "goal-auth",
                    "issue_ids": ["042-login-bug-fix"],
                    "active_issue_id": "042-login-bug-fix",
                    "phase": "execute",
                    "status": "active",
                    "next_command": "product:execute 042-login-bug-fix",
                }) + "\n",
                encoding="utf-8",
            )
            (root / "issues" / "042-login-bug-fix.md").write_text(
                "# Issue 042: Login Bug Fix\n\n## Summary\n\nFix login error and session bug.\n",
                encoding="utf-8",
            )

            routed = project_intake.route_intake(root, "로그인 버그 고쳐줘")

            self.assertEqual(routed["schema"], "moduflow.intake-routing.v1")
            self.assertEqual(routed["recommended_action"], "attach_active_issue")
            self.assertEqual(routed["active_issue"], "042-login-bug-fix")
            self.assertEqual(routed["next_command"], "product:execute 042-login-bug-fix")

    def test_route_intake_splits_large_request_into_goal_graph_candidates(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "workspace").mkdir()
            (root / "issues").mkdir()

            routed = project_intake.route_intake(
                root,
                "사업계획서 만들고 랜딩 디자인하고 결제 기능 구현해줘",
            )

            self.assertEqual(routed["recommended_action"], "create_goal_with_issues")
            self.assertGreaterEqual(len(routed["issue_candidates"]), 3)
            self.assertEqual(routed["next_command"], "product:goal")

    def test_write_intake_appends_inbox_record(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "workspace").mkdir()
            (root / "issues").mkdir()

            routed = project_intake.route_intake(root, "주간 리포트 만들어줘", write=True)
            inbox = (root / "workspace" / "inbox.md").read_text(encoding="utf-8")

            self.assertIn("moduflow.intake-routing.v1", inbox)
            self.assertIn("주간 리포트 만들어줘", inbox)
            self.assertEqual(routed["recommended_action"], "create_issue")

    def test_issue_candidate_title_uses_original_request_tokens(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "issues").mkdir()

            candidate = project_intake.split_issue_candidates(root, "로그인 버그 고쳐줘")[0]

            self.assertEqual(candidate["title"], "로그인 버그 고쳐줘")
            self.assertNotIn("auth", candidate["title"])


if __name__ == "__main__":
    unittest.main()
