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

    def test_route_intake_marks_clear_request_as_fast_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "workspace").mkdir()
            (root / "issues").mkdir()

            routed = project_intake.route_intake(root, "README 설치법 추가 이슈 만들어줘")

            self.assertEqual(routed["recommended_action"], "create_issue")
            self.assertEqual(routed["shaping_path"], "fast")
            self.assertEqual(routed["question_count"], 0)
            self.assertEqual(routed["suggested_questions"], [])
            self.assertEqual(routed["durable_context"], "issue")

    def test_route_intake_marks_ambiguous_request_as_short_shaping(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "workspace").mkdir()
            (root / "issues").mkdir()

            routed = project_intake.route_intake(root, "모두플로 인기가 없는 이유 개선해줘")

            self.assertEqual(routed["recommended_action"], "shape_then_issue")
            self.assertEqual(routed["shaping_path"], "short")
            self.assertGreaterEqual(routed["question_count"], 1)
            self.assertLessEqual(routed["question_count"], 3)
            self.assertEqual(routed["durable_context"], "opportunity")

    def test_route_intake_marks_strategy_request_as_panel_shaping(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "workspace").mkdir()
            (root / "issues").mkdir()

            routed = project_intake.route_intake(
                root,
                "모두플로 제품 방향과 포지셔닝을 다시 잡고 로드맵까지 정리해줘",
            )

            self.assertEqual(routed["recommended_action"], "panel_shape")
            self.assertEqual(routed["shaping_path"], "panel")
            self.assertLessEqual(routed["question_count"], 3)
            self.assertEqual(routed["next_command"], "product:opportunity")

    def test_route_intake_keeps_clear_improvement_requests_fast(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "workspace").mkdir()
            (root / "issues").mkdir()

            examples = [
                "README 문구 개선 이슈 만들어줘",
                "로그인 버그 수정하고 테스트 추가해줘",
                "경쟁사 조사해서 벤치마크 문서 만들어줘",
                "대시보드 지표가 왜 떨어졌는지 분석해줘",
                "결제 API 구현 계획 이슈 만들어줘",
            ]

            for request in examples:
                with self.subTest(request=request):
                    routed = project_intake.route_intake(root, request)

                    self.assertEqual(routed["recommended_action"], "create_issue")
                    self.assertEqual(routed["shaping_path"], "fast")
                    self.assertEqual(routed["question_count"], 0)

    def test_route_intake_shapes_product_context_questions(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "workspace").mkdir()
            (root / "issues").mkdir()

            examples = [
                ("사용자들이 모두플로를 안 쓰는 이유 찾아줘", "shape_then_issue", "short"),
                ("모두플로 온보딩 개선 방향 잡아줘", "panel_shape", "panel"),
                ("AI 작업 루프 제품 전략 다시 정리해줘", "panel_shape", "panel"),
            ]

            for request, action, path in examples:
                with self.subTest(request=request):
                    routed = project_intake.route_intake(root, request)

                    self.assertEqual(routed["recommended_action"], action)
                    self.assertEqual(routed["shaping_path"], path)
                    self.assertGreaterEqual(routed["question_count"], 1)
                    self.assertLessEqual(routed["question_count"], 3)

    def test_route_intake_question_cap_is_three_across_shaping_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "workspace").mkdir()
            (root / "issues").mkdir()

            requests = [
                "모두플로 인기가 없는 이유 개선해줘",
                "모두플로 제품 방향과 포지셔닝을 다시 잡고 로드맵까지 정리해줘",
                "사용자들이 모두플로를 안 쓰는 이유 찾아줘",
            ]

            for request in requests:
                with self.subTest(request=request):
                    routed = project_intake.route_intake(root, request)

                    self.assertLessEqual(routed["question_count"], 3)
                    self.assertEqual(len(routed["suggested_questions"]), routed["question_count"])

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
