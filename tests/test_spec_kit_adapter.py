import importlib.util
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "spec_kit_adapter.py"
ISSUE_ID = "098-speckit-selective-validation-adapter"
APPROVED_VERSION = "0.16.1"
APPROVED_SHA = "684b3d8e05263a7c1948d3d0699ab1cb4f77c3d5"
LIFECYCLE_ACTIONS = (
    "start",
    "begin",
    "pause",
    "stop",
    "resume",
    "continue",
    "finish",
    "complete",
    "close",
)
KOREAN_LIFECYCLE_ACTIONS = (
    "시작",
    "착수",
    "일시정지",
    "멈춰",
    "중지",
    "재개",
    "계속",
    "이어",
    "마무리",
    "끝내",
    "완료",
    "닫아",
    "종료",
)
LIFECYCLE_RESOURCES = ("status", "issue", "goal", "roadmap", "memory")
KOREAN_LIFECYCLE_RESOURCES = ("상태", "이슈", "목표", "로드맵", "메모리", "기억")
GIT_OPERATIONS = (
    "add",
    "stage",
    "stash",
    "fetch",
    "pull",
    "push",
    "merge",
    "rebase",
    "reset",
    "restore",
    "checkout",
    "switch",
    "branch",
    "tag",
    "cherry-pick",
    "revert",
    "clone",
    "commit",
)
KOREAN_GIT_OPERATIONS = (
    "깃 추가",
    "스테이징",
    "스태시",
    "페치",
    "풀",
    "푸시",
    "병합",
    "리베이스",
    "리셋",
    "복원",
    "체크아웃",
    "스위치",
    "브랜치",
    "태그",
    "체리픽",
    "리버트",
    "클론",
    "커밋",
)
KOREAN_INTRINSIC_GIT_OPERATIONS = {
    "스테이징", "스태시", "페치", "푸시", "병합", "리베이스", "리셋",
    "체크아웃", "체리픽", "리버트", "클론", "커밋",
}
ORDINARY_VALIDATION_REQUESTS = (
    ("Spec Kit clarify which acceptance criteria to add", "clarify"),
    ("Spec Kit analyze the stages in the plan", "analyze"),
    ("Spec Kit checklist where to start validation", "checklist"),
    ("Spec Kit converge candidates to restore requirement coverage", "converge"),
    ("스펙킷으로 분석해서 요구사항을 계속 명확히 해줘", "analyze"),
    ("스펙킷으로 체크리스트에 태그 요구사항을 추가해줘", "checklist"),
    ("Spec Kit clarify which changes to add to the requirements", "clarify"),
    ("Spec Kit analyze which stages changed in the spec files", "analyze"),
)
ADJACENT_OWNERSHIP_REQUESTS = (
    "Spec Kit analyze then add files to the index",
    "Spec Kit checklist then stage changed files",
    "Spec Kit clarify then restore files from the working tree",
    "Spec Kit analyze then start work on the issue",
    "Spec Kit checklist because the issue should be started",
    "스펙킷으로 분석한 뒤 이슈를 다시 시작해줘",
    "스펙킷으로 체크리스트 만든 뒤 이슈를 잠시 멈춰줘",
    "Spec Kit converge then switch to the current branch",
    "Spec Kit analyze then tag the modified commit",
    "Spec Kit checklist then branch the repo",
    "Spec Kit clarify then add tracked hunks to the index",
    "Spec Kit analyze then restore staged changes in the working tree",
    "Spec Kit checklist then stage untracked files",
    "Spec Kit checklist then continue work on the roadmap",
    "Spec Kit clarify because the project must be paused",
    "Spec Kit analyze because this work item can be completed",
    "스펙킷으로 분석한 뒤 프로젝트를 이제 재개해줘",
    "스펙킷으로 체크리스트 만든 뒤 로드맵을 바로 완료해줘",
    "스펙킷으로 분석한 뒤 이슈를 계속 이어줘",
)
METAMORPHIC_OWNERSHIP_REQUESTS = (
    "Spec Kit checklist then stage the recently changed files",
    "Spec Kit analyze then add all changed files to the index",
    "Spec Kit clarify then restore selected files from the working tree",
    "Spec Kit checklist because the issue should really be paused",
    "Spec Kit analyze then start working on the issue",
    "스펙킷으로 분석한 뒤 이슈를 잠깐 다시 시작해줘",
    "스펙킷으로 체크리스트 만든 뒤 프로젝트를 먼저 천천히 완료해줘",
    "Spec Kit checklist then stage the very recently modified files",
    "Spec Kit clarify then add every carefully reviewed changed hunk to the index",
    "Spec Kit analyze then restore only those selected archived files from the working tree",
    "Spec Kit checklist because the roadmap should eventually be carefully resumed",
    "Spec Kit analyze then carefully start seriously working on the current issue",
    "스펙킷으로 분석한 뒤 이슈를 아주 잠깐 먼저 멈춰줘",
    "스펙킷으로 체크리스트 만든 뒤 로드맵을 먼저 천천히 다시 재개해줘",
)
DOMAIN_TARGET_POSITIVE_REQUESTS = (
    ("Spec Kit clarify how to add changes to requirements", "clarify"),
    ("Spec Kit analyze which files to add to spec inputs", "analyze"),
    ("Spec Kit converge where to restore changes to requirement coverage", "converge"),
    ("Spec Kit checklist where to start validation for this issue", "checklist"),
    ("Spec Kit analyze which requirements to continue in the issue spec", "analyze"),
    ("스펙킷으로 스테이징된 요구사항 파일을 분석해줘", "analyze"),
)


def semantic_role_requests():
    negatives = [
        "Spec Kit checklist then stage, please, changed files",
        "Spec Kit checklist because the issue should, really, be paused",
        "스펙킷으로 분석한 뒤 이슈를, 잠깐, 먼저 멈춰줘",
        "Spec Kit analyze then stage files while preserving requirements",
        "Spec Kit clarify then add tracked files and update requirements",
    ]
    positives = [
        ("Spec Kit checklist which issue to start validation with", "checklist"),
        ("Spec Kit checklist issue to begin validation with", "checklist"),
        ("스펙킷으로 이슈별 시작 검증 기준을 체크리스트해줘", "checklist"),
        ("Spec Kit analyze committed requirements", "analyze"),
    ]
    for punctuation in (", {modifier},", " ({modifier}) ", " -- {modifier} -- "):
        for modifier in ("politely", "very carefully", "without any unnecessary delay"):
            insertion = punctuation.format(modifier=modifier)
            negatives.append(f"Spec Kit checklist then stage{insertion}changed files")
            negatives.append(
                f"Spec Kit checklist because the issue should{insertion}be paused"
            )
            positives.append(
                (f"Spec Kit checklist which issue to start{insertion}validation with", "checklist")
            )
    for modifier in (", 잠깐, 먼저 ", " (조심스럽게) 아주 잠깐 ", " 우선 천천히 "):
        negatives.append(f"스펙킷으로 분석한 뒤 이슈를{modifier}멈춰줘")
        positives.append(
            (f"스펙킷으로 이슈별 시작{modifier}검증 기준을 체크리스트해줘", "checklist")
        )
    return tuple(negatives), tuple(positives)


def load_module(testcase):
    testcase.assertTrue(MODULE_PATH.exists(), "scripts/spec_kit_adapter.py must exist")
    spec = importlib.util.spec_from_file_location("spec_kit_adapter", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def opted_in_config(functions=("clarify", "analyze", "checklist", "converge")):
    return {
        "schema": "moduflow.capabilities.v1",
        "capabilities": {
            "spec-kit": {
                "enabled": True,
                "source_version": APPROVED_VERSION,
                "source_sha": APPROVED_SHA,
                "functions": list(functions),
            }
        },
    }


def write_canonical_inputs(project, issue_id=ISSUE_ID):
    inputs = {
        Path("issues") / f"{issue_id}.md": "# Canonical issue\n",
        Path("specs") / issue_id / "spec.md": "# Canonical spec\n",
        Path("specs") / issue_id / "plan.md": "# Canonical plan\n",
        Path("specs") / issue_id / "tasks.md": "# Canonical tasks\n",
        Path("workspace") / "constitution.md": "# Canonical constitution\n",
    }
    for relative, content in inputs.items():
        path = project / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    return inputs


class SpecKitConfigTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ska = load_module(cls)

    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.project = Path(self.tempdir.name)
        write_canonical_inputs(self.project)

    def tearDown(self):
        self.tempdir.cleanup()

    def write_config(self, payload):
        path = self.project / ".moduflow" / "capabilities.json"
        path.parent.mkdir()
        path.write_text(json.dumps(payload), encoding="utf-8")

    def test_missing_config_is_disabled_without_creating_a_file(self):
        result = self.ska.build_handoff(
            ROOT, self.project, ISSUE_ID, "analyze", host_available=True
        )

        self.assertEqual(result["outcome"], "disabled")
        self.assertFalse((self.project / ".moduflow" / "capabilities.json").exists())

    def test_explicit_korean_request_selects_one_function(self):
        self.assertEqual(
            self.ska.select_function("스펙킷으로 요구사항 체크리스트 만들어줘"),
            "checklist",
        )
        self.assertEqual(
            self.ska.select_function("스펙킷으로 남은 작업을 수렴해줘"), "converge"
        )

    def test_multiple_functions_do_not_fan_out(self):
        with self.assertRaisesRegex(self.ska.SpecKitAdapterError, "ambiguous_function"):
            self.ska.select_function("스펙킷으로 분석하고 체크리스트도 만들어줘")

    def test_ownership_language_blocks_function_selection_before_template_handoff(self):
        self.write_config(opted_in_config())
        requests = (
            "스펙킷으로 코드를 분석해줘",
            "Spec Kit analyze the Git changes",
            "스펙킷으로 PR 리뷰를 분석해줘",
            "Spec Kit checklist for the deployment",
            "스펙킷으로 릴리즈 요구사항을 명확화해줘",
            "Spec Kit analyze this then mark issue done",
            "Spec Kit checklist then update the roadmap",
            "Spec Kit clarify then change the current goal",
            "Spec Kit analyze then save this to memory",
            "Spec Kit analyze then merge and push the branch",
            "Spec Kit checklist then pull and rebase",
            "Spec Kit converge then tag and cherry-pick",
            "Spec Kit clarify then reset and checkout the branch",
            "스펙킷으로 분석한 다음 이슈를 완료해줘",
            "스펙킷으로 체크리스트 만든 뒤 로드맵을 업데이트해줘",
            "스펙킷으로 명확화한 뒤 목표와 메모리를 수정해줘",
            "스펙킷으로 분석한 다음 브랜치를 병합하고 푸시해줘",
            "스펙킷으로 수렴한 뒤 리베이스하고 태그해줘",
        )

        for request in requests:
            with self.subTest(request=request):
                self.assertIsNone(self.ska.select_function(request))
                handoff = self.ska.build_handoff(
                    ROOT, self.project, ISSUE_ID, request, host_available=True
                )
                self.assertEqual(handoff["outcome"], "unsupported")
                self.assertIsNone(handoff["function"])
                self.assertIsNone(handoff["source"]["template"])

    def test_complete_canonical_lifecycle_and_git_aliases_fail_closed(self):
        self.write_config(opted_in_config())
        lifecycle_inflections = {
            "start": ("start", "started", "starting"),
            "begin": ("begin", "began", "beginning"),
            "pause": ("pause", "paused", "pausing"),
            "stop": ("stop", "stopped", "stopping"),
            "resume": ("resume", "resumed", "resuming"),
            "continue": ("continue", "continued", "continuing"),
            "finish": ("finish", "finished", "finishing"),
            "complete": ("complete", "completed", "completing"),
            "close": ("close", "closed", "closing"),
        }
        git_inflections = {
            "add": ("add", "added", "adding"),
            "stage": ("stage", "staged", "staging"),
            "stash": ("stash", "stashed", "stashing"),
            "fetch": ("fetch", "fetched", "fetching"),
            "pull": ("pull", "pulled", "pulling"),
            "push": ("push", "pushed", "pushing"),
            "merge": ("merge", "merged", "merging"),
            "rebase": ("rebase", "rebased", "rebasing"),
            "reset": ("reset", "resetting", "resets"),
            "restore": ("restore", "restored", "restoring"),
            "checkout": ("checkout", "checked out", "checking out"),
            "switch": ("switch", "switched", "switching"),
            "branch": ("branch", "branched", "branching"),
            "tag": ("tag", "tagged", "tagging"),
            "cherry-pick": ("cherry-pick", "cherry-picked", "cherry-picking"),
            "revert": ("revert", "reverted", "reverting"),
            "clone": ("clone", "cloned", "cloning"),
            "commit": ("commit", "committed", "committing"),
        }
        requests = []
        for aliases in lifecycle_inflections.values():
            requests.extend(f"Spec Kit analyze then {alias} the issue" for alias in aliases)
        requests.extend(
            f"Spec Kit checklist then update the {resource}"
            for resource in LIFECYCLE_RESOURCES
        )
        requests.extend(
            f"스펙킷으로 분석한 다음 이슈를 {alias}"
            for alias in KOREAN_LIFECYCLE_ACTIONS
        )
        requests.extend(
            f"스펙킷으로 체크리스트 만든 뒤 {resource}를 수정해줘"
            for resource in KOREAN_LIFECYCLE_RESOURCES
        )
        for aliases in git_inflections.values():
            requests.extend(
                f"Spec Kit converge then {alias} repository changes" for alias in aliases
            )
        requests.extend(
            (
                f"스펙킷으로 분석한 뒤 {operation}해줘"
                if operation in KOREAN_INTRINSIC_GIT_OPERATIONS
                else f"스펙킷으로 명확화한 뒤 저장소에 {operation}해줘"
            )
            for operation in KOREAN_GIT_OPERATIONS
        )

        self.assertEqual(set(lifecycle_inflections), set(LIFECYCLE_ACTIONS))
        self.assertEqual(set(git_inflections), set(GIT_OPERATIONS))
        for request in requests:
            with self.subTest(request=request):
                self.assertIsNone(self.ska.select_function(request))
                handoff = self.ska.build_handoff(
                    ROOT, self.project, ISSUE_ID, request, host_available=True
                )
                self.assertEqual(handoff["outcome"], "unsupported")
                self.assertIsNone(handoff["source"]["template"])
        self.assertFalse((self.project / "specs" / ISSUE_ID / "validation.md").exists())

    def test_ordinary_validation_words_require_ownership_context_before_blocking(self):
        self.write_config(opted_in_config())

        for request, expected_function in ORDINARY_VALIDATION_REQUESTS:
            with self.subTest(request=request):
                self.assertEqual(self.ska.select_function(request), expected_function)
                handoff = self.ska.build_handoff(
                    ROOT, self.project, ISSUE_ID, request, host_available=True
                )
                self.assertEqual(handoff["outcome"], "ready")
                self.assertEqual(handoff["function"], expected_function)
                self.assertEqual(
                    handoff["source"]["template"],
                    f"vendor/spec-kit/0.16.1/commands/{expected_function}.md",
                )
        self.assertFalse((self.project / "specs" / ISSUE_ID / "validation.md").exists())

    def test_intrinsic_korean_git_action_blocks_without_repository_context(self):
        self.write_config(opted_in_config())
        request = "스펙킷으로 분석한 뒤 스테이징해줘"

        self.assertIsNone(self.ska.select_function(request))
        handoff = self.ska.build_handoff(
            ROOT, self.project, ISSUE_ID, request, host_available=True
        )
        self.assertEqual(handoff["outcome"], "unsupported")
        self.assertIsNone(handoff["function"])
        self.assertIsNone(handoff["source"]["template"])
        self.assertFalse((self.project / "specs" / ISSUE_ID / "validation.md").exists())

    def test_adjacent_git_and_lifecycle_phrase_families_fail_closed(self):
        self.write_config(opted_in_config())

        for request in ADJACENT_OWNERSHIP_REQUESTS:
            with self.subTest(request=request):
                self.assertIsNone(self.ska.select_function(request))
                handoff = self.ska.build_handoff(
                    ROOT, self.project, ISSUE_ID, request, host_available=True
                )
                self.assertEqual(handoff["outcome"], "unsupported")
                self.assertIsNone(handoff["function"])
                self.assertIsNone(handoff["source"]["template"])
        self.assertFalse((self.project / "specs" / ISSUE_ID / "validation.md").exists())

    def test_clause_token_ownership_handles_arbitrary_insertions_and_domain_overrides(self):
        self.write_config(opted_in_config())
        for request in METAMORPHIC_OWNERSHIP_REQUESTS:
            with self.subTest(kind="ownership", request=request):
                self.assertIsNone(self.ska.select_function(request))
                handoff = self.ska.build_handoff(
                    ROOT, self.project, ISSUE_ID, request, host_available=True
                )
                self.assertEqual(handoff["outcome"], "unsupported")
                self.assertIsNone(handoff["source"]["template"])
        for request, function in DOMAIN_TARGET_POSITIVE_REQUESTS:
            with self.subTest(kind="domain", request=request):
                self.assertEqual(self.ska.select_function(request), function)
                handoff = self.ska.build_handoff(
                    ROOT, self.project, ISSUE_ID, request, host_available=True
                )
                self.assertEqual(handoff["outcome"], "ready")
                self.assertEqual(handoff["function"], function)
        self.assertFalse((self.project / "specs" / ISSUE_ID / "validation.md").exists())

    def test_strong_clause_roles_bind_each_verb_to_its_nearest_target(self):
        self.write_config(opted_in_config())
        negatives, positives = semantic_role_requests()
        for request in negatives:
            with self.subTest(kind="ownership", request=request):
                self.assertIsNone(self.ska.select_function(request))
                handoff = self.ska.build_handoff(
                    ROOT, self.project, ISSUE_ID, request, host_available=True
                )
                self.assertEqual(handoff["outcome"], "unsupported")
                self.assertIsNone(handoff["source"]["template"])
        for request, function in positives:
            with self.subTest(kind="advisory", request=request):
                self.assertEqual(self.ska.select_function(request), function)
                handoff = self.ska.build_handoff(
                    ROOT, self.project, ISSUE_ID, request, host_available=True
                )
                self.assertEqual(handoff["outcome"], "ready")
                self.assertEqual(handoff["function"], function)
        self.assertFalse((self.project / "specs" / ISSUE_ID / "validation.md").exists())

    def test_valid_opt_in_with_verified_assets_returns_one_ready_template(self):
        self.write_config(opted_in_config(("analyze",)))

        result = self.ska.build_handoff(
            ROOT, self.project, ISSUE_ID, "analyze", host_available=True
        )

        self.assertEqual(result["outcome"], "ready")
        self.assertEqual(result["function"], "analyze")
        self.assertEqual(
            result["source"]["template"],
            "vendor/spec-kit/0.16.1/commands/analyze.md",
        )
        self.assertEqual(
            result["source"]["template_sha256"],
            "79f5334bce9b249d4c1a5e6949dee3f3532db89a0a97f3d2eb55c1a1c2fe06f6",
        )
        self.assertEqual(result["permission"], "read")
        self.assertEqual(
            result["inputs"],
            [
                f"specs/{ISSUE_ID}/spec.md",
                f"specs/{ISSUE_ID}/plan.md",
                f"specs/{ISSUE_ID}/tasks.md",
                "workspace/constitution.md",
            ],
        )
        self.assertRegex(result["input_hash"], r"^sha256:[0-9a-f]{64}$")
        self.assertIsNone(result["fallback"])

    def test_each_function_requires_its_exact_canonical_regular_inputs(self):
        required = {
            "clarify": [f"issues/{ISSUE_ID}.md", f"specs/{ISSUE_ID}/spec.md"],
            "analyze": [
                f"specs/{ISSUE_ID}/spec.md",
                f"specs/{ISSUE_ID}/plan.md",
                f"specs/{ISSUE_ID}/tasks.md",
                "workspace/constitution.md",
            ],
            "checklist": [f"issues/{ISSUE_ID}.md", f"specs/{ISSUE_ID}/spec.md"],
            "converge": [
                f"specs/{ISSUE_ID}/spec.md",
                f"specs/{ISSUE_ID}/plan.md",
                f"specs/{ISSUE_ID}/tasks.md",
                "workspace/constitution.md",
            ],
        }
        self.write_config(opted_in_config())

        for function, paths in required.items():
            ready = self.ska.build_handoff(
                ROOT, self.project, ISSUE_ID, function, host_available=True
            )
            self.assertEqual(ready["outcome"], "ready")
            self.assertEqual(ready["inputs"], paths)
            for relative in paths:
                with self.subTest(function=function, missing=relative):
                    path = self.project / relative
                    original = path.read_bytes()
                    path.unlink()
                    handoff = self.ska.build_handoff(
                        ROOT, self.project, ISSUE_ID, function, host_available=True
                    )
                    self.assertNotEqual(handoff["outcome"], "ready")
                    self.assertIsNone(handoff["source"]["template"])
                    self.assertIn("prerequisite", handoff["fallback"].lower())
                    path.write_bytes(original)

    def test_input_hash_is_derived_from_canonical_paths_and_bytes(self):
        self.write_config(opted_in_config(("analyze",)))
        before = self.ska.build_handoff(
            ROOT, self.project, ISSUE_ID, "analyze", host_available=True
        )

        (self.project / "specs" / ISSUE_ID / "plan.md").write_text(
            "# Changed canonical plan\n", encoding="utf-8"
        )
        after = self.ska.build_handoff(
            ROOT, self.project, ISSUE_ID, "analyze", host_available=True
        )

        self.assertNotEqual(before["input_hash"], after["input_hash"])
        self.assertEqual(before["inputs"], after["inputs"])

    def test_internal_config_and_input_symlinks_fail_closed(self):
        with tempfile.TemporaryDirectory() as outside:
            outside = Path(outside)
            outside_config = outside / "capabilities.json"
            outside_config.write_text(json.dumps(opted_in_config()), encoding="utf-8")
            config_dir = self.project / ".moduflow"
            config_dir.symlink_to(outside, target_is_directory=True)

            handoff = self.ska.build_handoff(
                ROOT, self.project, ISSUE_ID, "analyze", host_available=True
            )
            self.assertEqual(handoff["outcome"], "blocked")
            self.assertIsNone(handoff["source"]["template"])
            self.assertEqual(
                outside_config.read_text(encoding="utf-8"),
                json.dumps(opted_in_config()),
            )

            config_dir.unlink()
            config_dir.mkdir()
            config = config_dir / "capabilities.json"
            config.write_text(json.dumps(opted_in_config()), encoding="utf-8")
            canonical_input = self.project / "specs" / ISSUE_ID / "plan.md"
            canonical_input.unlink()
            outside_input = outside / "plan.md"
            outside_input.write_text("outside plan\n", encoding="utf-8")
            canonical_input.symlink_to(outside_input)
            handoff = self.ska.build_handoff(
                ROOT, self.project, ISSUE_ID, "analyze", host_available=True
            )
            self.assertNotEqual(handoff["outcome"], "ready")
            self.assertIsNone(handoff["source"]["template"])
            self.assertEqual(outside_input.read_text(encoding="utf-8"), "outside plan\n")

    def test_missing_and_symlinked_inputs_use_exact_prerequisite_fallback_without_target(self):
        self.write_config(opted_in_config(("analyze",)))
        expected = (
            "Required canonical prerequisite inputs are unavailable; use the documented "
            "native prerequisite fallback."
        )
        plan = self.project / "specs" / ISSUE_ID / "plan.md"
        original = plan.read_bytes()
        plan.unlink()

        missing = self.ska.build_handoff(
            ROOT, self.project, ISSUE_ID, "Spec Kit analyze the requirements", True
        )
        self.assertEqual(missing["outcome"], "unavailable")
        self.assertEqual(missing["fallback"], expected)
        self.assertIsNone(missing["output_artifact"])
        self.assertIsNone(missing["source"]["template"])

        with tempfile.TemporaryDirectory() as outside:
            outside_plan = Path(outside) / "plan.md"
            outside_plan.write_bytes(original)
            plan.symlink_to(outside_plan)
            symlinked = self.ska.build_handoff(
                ROOT, self.project, ISSUE_ID, "Spec Kit analyze the requirements", True
            )
            self.assertEqual(symlinked["outcome"], "unavailable")
            self.assertEqual(symlinked["fallback"], expected)
            self.assertIsNone(symlinked["output_artifact"])
            self.assertIsNone(symlinked["source"]["template"])

        config = self.project / ".moduflow" / "capabilities.json"
        config.unlink()
        with tempfile.TemporaryDirectory() as outside:
            outside_config = Path(outside) / "capabilities.json"
            outside_config.write_text(json.dumps(opted_in_config()), encoding="utf-8")
            config.symlink_to(outside_config)
            contained = self.ska.build_handoff(
                ROOT, self.project, ISSUE_ID, "Spec Kit analyze the requirements", True
            )
            self.assertEqual(contained["outcome"], "blocked")
            self.assertNotEqual(contained["fallback"], expected)

    def test_unknown_config_field_is_blocked_without_exposing_a_template(self):
        payload = opted_in_config()
        payload["capabilities"]["spec-kit"]["unexpected"] = True
        self.write_config(payload)

        result = self.ska.build_handoff(
            ROOT, self.project, ISSUE_ID, "analyze", host_available=True
        )

        self.assertEqual(result["outcome"], "blocked")
        self.assertEqual(result["source"]["template"], None)
        self.assertTrue(result["fallback"])

    def test_output_path_escape_returns_a_blocked_handoff(self):
        with tempfile.TemporaryDirectory() as outside:
            shutil.rmtree(self.project / "specs")
            (self.project / "specs").symlink_to(outside, target_is_directory=True)

            result = self.ska.build_handoff(
                ROOT, self.project, ISSUE_ID, "analyze", host_available=True
            )

        self.assertEqual(result["outcome"], "blocked")
        self.assertEqual(result["output_artifact"], None)
        self.assertEqual(result["source"]["template"], None)
        self.assertEqual(result["source"]["template_sha256"], None)
        self.assertTrue(result["fallback"])

    def test_handoff_has_only_the_public_contract_keys(self):
        result = self.ska.build_handoff(
            ROOT, self.project, ISSUE_ID, "not a spec kit request", host_available=True
        )

        self.assertEqual(result["outcome"], "unsupported")
        self.assertEqual(
            set(result),
            {
                "schema",
                "outcome",
                "function",
                "issue_id",
                "source",
                "permission",
                "inputs",
                "output_artifact",
                "limitations",
                "fallback",
                "input_hash",
            },
        )


class SpecKitPersistenceTests(unittest.TestCase):
    """Result records must stay advisory and append-only on real project bytes."""

    @classmethod
    def setUpClass(cls):
        cls.ska = load_module(cls)

    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.project = Path(self.tempdir.name)
        path = self.project / ".moduflow" / "capabilities.json"
        path.parent.mkdir()
        path.write_text(json.dumps(opted_in_config()), encoding="utf-8")
        write_canonical_inputs(self.project)

    def tearDown(self):
        self.tempdir.cleanup()

    def ready_handoff(self, function):
        return self.ska.build_handoff(ROOT, self.project, ISSUE_ID, function, host_available=True)

    def valid_result(self, handoff, findings=None):
        findings = ["Requirements are internally consistent."] if findings is None else findings
        result = {
            "schema": "moduflow.spec-kit-result.v1",
            "run_id": "sha256:" + "0" * 64,
            "input_hash": handoff["input_hash"],
            "issue_id": ISSUE_ID,
            "function": handoff["function"],
            "source_version": APPROVED_VERSION,
            "source_sha": APPROVED_SHA,
            "template_sha256": handoff["source"]["template_sha256"],
            "permission": "read",
            "findings": findings,
            "limitations": ["Advisory only."],
            "native_overlap": ["native requirements analysis"],
            "elapsed_ms": 17,
            "loaded_context_chars": 250,
            "user_decision": "Review the advisory findings.",
            "next_command": "moduflow review --issue 098",
        }
        canonical = json.dumps(
            {
                "source_sha": result["source_sha"],
                "template_sha256": result["template_sha256"],
                "function": result["function"],
                "issue_id": result["issue_id"],
                "input_hash": result["input_hash"],
                "findings": result["findings"],
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        result["run_id"] = "sha256:" + hashlib.sha256(canonical).hexdigest()
        return result

    def test_duplicate_accepted_result_is_byte_stable(self):
        """Removing marker de-duplication would append duplicate validation evidence."""
        handoff = self.ready_handoff("analyze")
        result = self.valid_result(handoff)

        first = self.ska.persist_validation(
            ROOT,
            self.project,
            ISSUE_ID,
            "Spec Kit analyze the requirements",
            result,
            host_available=True,
            write=True,
        )
        before = first["path"].read_bytes()
        second = self.ska.persist_validation(
            ROOT,
            self.project,
            ISSUE_ID,
            "Spec Kit analyze the requirements",
            result,
            host_available=True,
            write=True,
        )

        self.assertFalse(second["changed"])
        self.assertEqual(second["path"].read_bytes(), before)

    def test_result_cannot_claim_write_or_unknown_execution_fields(self):
        """Relaxing advisory result validation would admit host mutation claims."""
        handoff = self.ready_handoff("converge")
        result = self.valid_result(handoff)
        result["permission"] = "write-local"

        with self.assertRaisesRegex(self.ska.SpecKitAdapterError, "permission_mismatch"):
            self.ska.validate_host_result(result, handoff)

        result = self.valid_result(handoff)
        result["executed_commands"] = ["git commit"]
        with self.assertRaisesRegex(self.ska.SpecKitAdapterError, "unknown_result_field"):
            self.ska.validate_host_result(result, handoff)
        self.assertFalse((self.project / "specs" / ISSUE_ID / "validation.md").exists())

    def test_result_rejects_malformed_identity_and_deterministic_hash_drift(self):
        """Skipping strict identity or run-ID checks would persist untraceable evidence."""
        handoff = self.ready_handoff("analyze")
        result = self.valid_result(handoff)
        result["issue_id"] = "../outside"
        with self.assertRaisesRegex(self.ska.SpecKitAdapterError, "unsafe_issue_id"):
            self.ska.validate_result_shape(result)

        result = self.valid_result(handoff)
        result["function"] = "implement"
        with self.assertRaisesRegex(self.ska.SpecKitAdapterError, "function_mismatch"):
            self.ska.validate_result_shape(result)

        result = self.valid_result(handoff)
        result["template_sha256"] = "0" * 64
        with self.assertRaisesRegex(self.ska.SpecKitAdapterError, "template_mismatch"):
            self.ska.validate_result_shape(result)

        result = self.valid_result(handoff)
        result["run_id"] = "sha256:" + "f" * 64
        with self.assertRaisesRegex(self.ska.SpecKitAdapterError, "run_id_mismatch"):
            self.ska.validate_result_shape(result)

        result = self.valid_result(handoff)
        result["elapsed_ms"] = -1
        with self.assertRaisesRegex(self.ska.SpecKitAdapterError, "invalid_result"):
            self.ska.validate_result_shape(result)

    def test_host_result_must_match_ready_handoff_source_and_output(self):
        """Ignoring handoff provenance would let a result cross issue or template boundaries."""
        handoff = self.ready_handoff("checklist")
        result = self.valid_result(handoff)
        result["source_sha"] = "0" * 40
        with self.assertRaisesRegex(self.ska.SpecKitAdapterError, "source_mismatch"):
            self.ska.validate_host_result(result, handoff)

        blocked = dict(handoff)
        blocked["outcome"] = "blocked"
        with self.assertRaisesRegex(self.ska.SpecKitAdapterError, "handoff_not_ready"):
            self.ska.validate_host_result(self.valid_result(handoff), blocked)

        bad_output = dict(handoff)
        bad_output["output_artifact"] = "specs/other/validation.md"
        with self.assertRaisesRegex(self.ska.SpecKitAdapterError, "output_mismatch"):
            self.ska.validate_host_result(self.valid_result(handoff), bad_output)
        self.assertFalse((self.project / "specs" / ISSUE_ID / "validation.md").exists())

    def test_clarify_allows_only_one_question_finding(self):
        """Dropping clarify's cardinality boundary would turn one request into a question fan-out."""
        handoff = self.ready_handoff("clarify")
        result = self.valid_result(handoff, ["Question one?", "Question two?"])

        with self.assertRaisesRegex(self.ska.SpecKitAdapterError, "clarify_findings_limit"):
            self.ska.validate_host_result(result, handoff)

    def test_converge_candidates_remain_advisory_without_task_or_code_mutation(self):
        """Adding mutation fields to convergence candidates would violate the advisory boundary."""
        handoff = self.ready_handoff("converge")
        result = self.valid_result(handoff, [{"kind": "remaining-work", "candidate": "Add test."}])

        validated = self.ska.validate_host_result(result, handoff)
        persisted = self.ska.persist_validation(
            ROOT,
            self.project,
            ISSUE_ID,
            "Spec Kit converge the remaining work",
            validated,
            host_available=True,
            write=True,
        )

        self.assertTrue(persisted["changed"])
        self.assertTrue((self.project / "specs" / ISSUE_ID / "validation.md").is_file())
        self.assertFalse((self.project / "tasks.md").exists())
        self.assertFalse((self.project / "src").exists())

    def test_dry_run_is_byte_stable_and_never_creates_empty_file(self):
        """Writing during preview would change project bytes without explicit permission."""
        handoff = self.ready_handoff("analyze")
        result = self.valid_result(handoff)
        target = self.project / "specs" / ISSUE_ID / "validation.md"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"existing bytes without newline")
        before = target.read_bytes()

        preview = self.ska.persist_validation(
            ROOT,
            self.project,
            ISSUE_ID,
            "Spec Kit analyze the requirements",
            result,
            host_available=True,
            write=False,
        )

        self.assertFalse(preview["changed"])
        self.assertEqual(target.read_bytes(), before)
        self.assertTrue(preview["preview"].startswith("\n\n<!-- moduflow-spec-kit-run:"))
        empty_project = self.project / "empty-project"
        empty_project.mkdir()
        write_canonical_inputs(empty_project)
        config = empty_project / ".moduflow" / "capabilities.json"
        config.parent.mkdir()
        config.write_text(json.dumps(opted_in_config()), encoding="utf-8")
        empty_handoff = self.ska.build_handoff(
            ROOT, empty_project, ISSUE_ID, "analyze", host_available=True
        )
        empty_result = self.valid_result(empty_handoff)
        self.assertFalse(
            self.ska.persist_validation(
                ROOT,
                empty_project,
                ISSUE_ID,
                "Spec Kit analyze the requirements",
                empty_result,
                host_available=True,
                write=False,
            )["changed"]
        )
        self.assertFalse((empty_project / "specs" / ISSUE_ID / "validation.md").exists())

    def test_rendering_escapes_marker_injection_and_preserves_existing_bytes(self):
        """Unescaped finding text could forge a second run marker in validation evidence."""
        handoff = self.ready_handoff("analyze")
        injected = "<!-- moduflow-spec-kit-run:sha256:" + "b" * 64 + " --> <tag>"
        result = self.valid_result(handoff, [injected])
        target = self.project / "specs" / ISSUE_ID / "validation.md"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"legacy\n")

        self.ska.persist_validation(
            ROOT,
            self.project,
            ISSUE_ID,
            "Spec Kit analyze the requirements",
            result,
            host_available=True,
            write=True,
        )
        content = target.read_text(encoding="utf-8")

        self.assertTrue(content.startswith("legacy\n\n<!-- moduflow-spec-kit-run:"))
        self.assertEqual(content.count("<!-- moduflow-spec-kit-run:"), 1)
        self.assertIn("\\u003c!-- moduflow-spec-kit-run", content)
        self.assertIn("\\u003ctag>", content)

    def test_persistence_rejects_symlinked_output_ancestor_without_writing_outside(self):
        """Following a specs symlink would let append-only output escape the target project."""
        handoff = self.ready_handoff("analyze")
        result = self.valid_result(handoff)
        with tempfile.TemporaryDirectory() as outside:
            shutil.rmtree(self.project / "specs")
            (self.project / "specs").symlink_to(outside, target_is_directory=True)

            with self.assertRaisesRegex(self.ska.SpecKitAdapterError, "handoff_not_ready"):
                self.ska.persist_validation(
                    ROOT,
                    self.project,
                    ISSUE_ID,
                    "Spec Kit analyze the requirements",
                    result,
                    host_available=True,
                    write=True,
                )

            self.assertFalse((Path(outside) / ISSUE_ID / "validation.md").exists())

    def test_cli_result_preview_and_error_are_stable_json_without_traceback(self):
        """A CLI that writes by default or leaks tracebacks breaks safe host integration."""
        handoff = self.ready_handoff("analyze")
        result = self.valid_result(handoff)
        command = [
            sys.executable,
            str(MODULE_PATH),
            str(self.project),
            "--issue-id",
            ISSUE_ID,
            "--accept-result",
            json.dumps(result),
            "--request",
            "Spec Kit analyze the requirements",
            "--host-available",
        ]

        preview = subprocess.run(command, capture_output=True, text=True, check=False)
        preview_payload = json.loads(preview.stdout)
        self.assertEqual(preview.returncode, 0)
        self.assertTrue(preview_payload["ok"])
        self.assertFalse(preview_payload["result"]["changed"])
        self.assertFalse((self.project / "specs" / ISSUE_ID / "validation.md").exists())

        bad_command = list(command)
        bad_command[bad_command.index("--accept-result") + 1] = "not-json"
        bad = subprocess.run(bad_command, capture_output=True, text=True, check=False)
        self.assertNotEqual(bad.returncode, 0)
        bad_payload = json.loads(bad.stdout)
        self.assertFalse(bad_payload["ok"])
        self.assertEqual(bad_payload["schema"], "moduflow.spec-kit-error.v1")
        self.assertNotIn("Traceback", bad.stderr)

        missing_issue = subprocess.run(
            [sys.executable, str(MODULE_PATH), str(self.project), "--accept-result", json.dumps(result)],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertNotEqual(missing_issue.returncode, 0)
        self.assertEqual(
            json.loads(missing_issue.stdout)["schema"], "moduflow.spec-kit-error.v1"
        )

    def test_cli_handoff_mode_is_read_only_and_accept_result_remains_proof_bound(self):
        command = [
            sys.executable,
            str(MODULE_PATH),
            str(self.project),
            "--issue-id",
            ISSUE_ID,
            "--request",
            "Spec Kit analyze the requirements",
            "--host-available",
        ]
        ready = subprocess.run(command, capture_output=True, text=True, check=False)
        self.assertEqual(ready.returncode, 0, ready.stderr)
        self.assertEqual(json.loads(ready.stdout)["schema"], "moduflow.spec-kit-handoff.v1")
        self.assertEqual(json.loads(ready.stdout)["outcome"], "ready")
        self.assertEqual(ready.stderr, "")
        self.assertFalse((self.project / "specs" / ISSUE_ID / "validation.md").exists())

        unavailable = subprocess.run(
            command[:-1], capture_output=True, text=True, check=False
        )
        self.assertEqual(unavailable.returncode, 0, unavailable.stderr)
        self.assertEqual(json.loads(unavailable.stdout)["outcome"], "unavailable")

        illegal_write = subprocess.run(
            command + ["--write"], capture_output=True, text=True, check=False
        )
        self.assertEqual(illegal_write.returncode, 2)
        self.assertEqual(
            json.loads(illegal_write.stdout)["schema"], "moduflow.spec-kit-error.v1"
        )
        self.assertEqual(illegal_write.stderr, "")

    def test_cli_missing_accept_result_value_is_json_error(self):
        """Leaving argparse's missing-option branch intact would emit usage text to stderr."""
        result = subprocess.run(
            [sys.executable, str(MODULE_PATH), str(self.project), "--accept-result"],
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stdout)["schema"], "moduflow.spec-kit-error.v1")
        self.assertEqual(result.stderr, "")

    def test_persistence_rebuilds_current_handoff_and_rejects_stale_or_disabled_state(self):
        handoff = self.ready_handoff("analyze")
        result = self.valid_result(handoff)
        (self.project / "specs" / ISSUE_ID / "plan.md").write_text(
            "changed after host result\n", encoding="utf-8"
        )

        with self.assertRaisesRegex(self.ska.SpecKitAdapterError, "input_mismatch"):
            self.ska.persist_validation(
                ROOT,
                self.project,
                ISSUE_ID,
                "Spec Kit analyze the requirements",
                result,
                host_available=True,
                write=True,
            )
        self.assertFalse((self.project / "specs" / ISSUE_ID / "validation.md").exists())

        (self.project / "specs" / ISSUE_ID / "plan.md").write_text(
            "# Canonical plan\n", encoding="utf-8"
        )
        config = self.project / ".moduflow" / "capabilities.json"
        payload = opted_in_config()
        payload["capabilities"]["spec-kit"]["enabled"] = False
        config.write_text(json.dumps(payload), encoding="utf-8")
        with self.assertRaisesRegex(self.ska.SpecKitAdapterError, "handoff_not_ready"):
            self.ska.persist_validation(
                ROOT,
                self.project,
                ISSUE_ID,
                "Spec Kit analyze the requirements",
                result,
                host_available=True,
                write=True,
            )
        self.assertFalse((self.project / "specs" / ISSUE_ID / "validation.md").exists())

    def test_persistence_rechecks_current_asset_bytes_and_validation_leaf(self):
        handoff = self.ready_handoff("analyze")
        result = self.valid_result(handoff)
        with tempfile.TemporaryDirectory() as package_tmp:
            package = Path(package_tmp)
            source = ROOT / "vendor" / "spec-kit" / APPROVED_VERSION
            destination = package / "vendor" / "spec-kit" / APPROVED_VERSION
            destination.parent.mkdir(parents=True)
            shutil.copytree(source, destination)
            (destination / "commands" / "analyze.md").write_text(
                "drifted asset\n", encoding="utf-8"
            )

            with self.assertRaisesRegex(self.ska.SpecKitAdapterError, "handoff_not_ready"):
                self.ska.persist_validation(
                    package,
                    self.project,
                    ISSUE_ID,
                    "Spec Kit analyze the requirements",
                    result,
                    host_available=True,
                    write=True,
                )
        self.assertFalse((self.project / "specs" / ISSUE_ID / "validation.md").exists())

        with tempfile.TemporaryDirectory() as outside:
            outside_file = Path(outside) / "validation.md"
            outside_file.write_bytes(b"outside-bytes\n")
            target = self.project / "specs" / ISSUE_ID / "validation.md"
            target.symlink_to(outside_file)
            with self.assertRaisesRegex(self.ska.SpecKitAdapterError, "handoff_not_ready"):
                self.ska.persist_validation(
                    ROOT,
                    self.project,
                    ISSUE_ID,
                    "Spec Kit analyze the requirements",
                    result,
                    host_available=True,
                    write=True,
                )
            self.assertEqual(outside_file.read_bytes(), b"outside-bytes\n")

    def test_concurrent_duplicate_writers_append_exactly_one_marker(self):
        handoff = self.ready_handoff("analyze")
        result = self.valid_result(handoff)
        barrier = threading.Barrier(2)

        def write_once():
            barrier.wait()
            return self.ska.persist_validation(
                ROOT,
                self.project,
                ISSUE_ID,
                "Spec Kit analyze the requirements",
                result,
                host_available=True,
                write=True,
            )

        with ThreadPoolExecutor(max_workers=2) as pool:
            outcomes = list(pool.map(lambda _: write_once(), range(2)))

        target = self.project / "specs" / ISSUE_ID / "validation.md"
        marker = f"<!-- moduflow-spec-kit-run:{result['run_id']} -->"
        self.assertEqual(sorted(outcome["changed"] for outcome in outcomes), [False, True])
        self.assertEqual(target.read_text(encoding="utf-8").count(marker), 1)

    def test_cli_requires_current_request_host_and_inputs_before_preview_or_write(self):
        handoff = self.ready_handoff("analyze")
        result = self.valid_result(handoff)
        base = [
            sys.executable,
            str(MODULE_PATH),
            str(self.project),
            "--issue-id",
            ISSUE_ID,
            "--accept-result",
            json.dumps(result),
        ]
        for missing in ("request", "host"):
            command = base + (["--host-available"] if missing == "request" else ["--request", "Spec Kit analyze the requirements"])
            with self.subTest(missing=missing):
                completed = subprocess.run(command, capture_output=True, text=True, check=False)
                self.assertEqual(completed.returncode, 2)
                self.assertEqual(
                    json.loads(completed.stdout)["schema"],
                    "moduflow.spec-kit-error.v1",
                )
                self.assertNotIn("Traceback", completed.stderr)
                self.assertFalse((self.project / "specs" / ISSUE_ID / "validation.md").exists())

        (self.project / "specs" / ISSUE_ID / "tasks.md").unlink()
        completed = subprocess.run(
            base + ["--request", "Spec Kit analyze the requirements", "--host-available", "--write"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 2)
        self.assertEqual(json.loads(completed.stdout)["schema"], "moduflow.spec-kit-error.v1")
        self.assertNotIn("Traceback", completed.stderr)
        self.assertFalse((self.project / "specs" / ISSUE_ID / "validation.md").exists())

    def test_configure_errors_and_symlink_targets_are_structured_and_no_follow(self):
        invalid = subprocess.run(
            [
                sys.executable,
                str(MODULE_PATH),
                str(self.project),
                "--configure",
                "--functions",
                "analyze,implement",
                "--write",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(invalid.returncode, 2)
        self.assertEqual(json.loads(invalid.stdout)["schema"], "moduflow.spec-kit-error.v1")
        self.assertNotIn("Traceback", invalid.stderr)

        with tempfile.TemporaryDirectory() as outside:
            outside = Path(outside)
            outside_config = outside / "capabilities.json"
            outside_config.write_bytes(b"outside-bytes\n")
            target = self.project / ".moduflow" / "capabilities.json"
            target.unlink()
            target.symlink_to(outside_config)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(MODULE_PATH),
                    str(self.project),
                    "--configure",
                    "--functions",
                    "analyze",
                    "--write",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 2)
            self.assertEqual(json.loads(completed.stdout)["schema"], "moduflow.spec-kit-error.v1")
            self.assertNotIn("Traceback", completed.stderr)
            self.assertEqual(outside_config.read_bytes(), b"outside-bytes\n")

    def test_cli_invalid_utf8_config_stays_on_structured_error_boundary(self):
        handoff = self.ready_handoff("analyze")
        result = self.valid_result(handoff)
        (self.project / ".moduflow" / "capabilities.json").write_bytes(b"\xff")

        completed = subprocess.run(
            [
                sys.executable,
                str(MODULE_PATH),
                str(self.project),
                "--issue-id",
                ISSUE_ID,
                "--accept-result",
                json.dumps(result),
                "--request",
                "Spec Kit analyze the requirements",
                "--host-available",
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 2)
        self.assertEqual(json.loads(completed.stdout)["schema"], "moduflow.spec-kit-error.v1")
        self.assertNotIn("Traceback", completed.stderr)
        self.assertFalse((self.project / "specs" / ISSUE_ID / "validation.md").exists())

    def test_cli_missing_project_root_is_json_error(self):
        """Leaving argparse's missing-positional branch intact would emit usage text to stderr."""
        result = subprocess.run(
            [sys.executable, str(MODULE_PATH), "--accept-result", "{}"],
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stdout)["schema"], "moduflow.spec-kit-error.v1")
        self.assertEqual(result.stderr, "")

    def test_cli_unknown_option_is_json_error(self):
        """Leaving argparse's unknown-option branch intact would emit usage text to stderr."""
        result = subprocess.run(
            [sys.executable, str(MODULE_PATH), str(self.project), "--not-an-option"],
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stdout)["schema"], "moduflow.spec-kit-error.v1")
        self.assertEqual(result.stderr, "")
