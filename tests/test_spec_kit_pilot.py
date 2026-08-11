import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "spec_kit_pilot.py"
FIXTURES = ROOT / "tests" / "fixtures" / "spec-kit-selective-validation" / "cases.json"
ISSUE_ID = "098-speckit-selective-validation-adapter"
FUNCTIONS = ("clarify", "analyze", "checklist", "converge")
LIFECYCLE_ACTIONS = (
    "start", "begin", "pause", "stop", "resume", "continue", "finish", "complete", "close"
)
KOREAN_LIFECYCLE_ACTIONS = (
    "시작", "착수", "일시정지", "멈춰", "중지", "재개", "계속", "이어", "마무리", "끝내", "완료", "닫아", "종료"
)
LIFECYCLE_RESOURCES = ("status", "issue", "goal", "roadmap", "memory")
KOREAN_LIFECYCLE_RESOURCES = ("상태", "이슈", "목표", "로드맵", "메모리", "기억")
GIT_OPERATIONS = (
    "add", "stage", "stash", "fetch", "pull", "push", "merge", "rebase", "reset",
    "restore", "checkout", "switch", "branch", "tag", "cherry-pick", "revert", "clone", "commit",
)
KOREAN_GIT_OPERATIONS = (
    "깃 추가", "스테이징", "스태시", "페치", "풀", "푸시", "병합", "리베이스", "리셋",
    "복원", "체크아웃", "스위치", "브랜치", "태그", "체리픽", "리버트", "클론", "커밋",
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
INPUTS = {
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


def load_module():
    spec = importlib.util.spec_from_file_location("spec_kit_pilot", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def independent_input_hash(function):
    records = []
    for relative in INPUTS[function]:
        content = (ROOT / relative).read_bytes()
        records.append({"path": relative, "sha256": hashlib.sha256(content).hexdigest()})
    canonical = json.dumps(
        records,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(canonical).hexdigest()


def independent_loaded_context_chars(function):
    paths = [
        ROOT / "overlays" / "spec-kit" / "selective-validation-policy.md",
        ROOT / "vendor" / "spec-kit" / "0.16.1" / "commands" / f"{function}.md",
        *(ROOT / relative for relative in INPUTS[function]),
    ]
    return sum(len(path.read_text(encoding="utf-8")) for path in paths)


class SpecKitPilotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pilot = load_module()

    def canonical_cases(self):
        return json.loads(json.dumps(self.pilot.load_cases(FIXTURES)["cases"]))

    def evaluate_cases(self, cases, result_base=FIXTURES.parent):
        return self.pilot.evaluate_cases(
            cases,
            result_base=result_base,
            package_root=ROOT,
        )

    def case(self, cases, case_id):
        return next(case for case in cases if case["id"] == case_id)

    def copy_fixtures(self, root):
        destination = root / "tests" / "fixtures" / "spec-kit-selective-validation"
        destination.parent.mkdir(parents=True)
        shutil.copytree(FIXTURES.parent, destination)
        return destination / "cases.json"

    def run_cli(self, root, fixtures, *extra):
        return subprocess.run(
            [sys.executable, str(SCRIPT), str(root), "--fixtures", str(fixtures), *extra],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_fixture_matrix_is_request_driven_without_self_declared_safety(self):
        cases = self.canonical_cases()
        self.assertEqual(len(cases), 13)
        self.assertEqual(
            {case["function"] for case in cases if case["class"] == "success"},
            set(FUNCTIONS),
        )
        for case in cases:
            self.assertRegex(case["id"], r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
            self.assertTrue(case["request"].strip())
            self.assertIn(case["expected_outcome"], {"ready", "disabled", "unavailable", "unsupported"})
            for untrusted in (
                "passed",
                "boundary_violation",
                "unauthorized_write",
                "fanout",
                "false_execution_claim",
                "output_artifact",
            ):
                self.assertNotIn(untrusted, case)

    def test_real_router_and_adapter_derive_every_case_outcome(self):
        report = self.evaluate_cases(self.canonical_cases())

        self.assertEqual(report["passed_cases"], 13)
        self.assertTrue(report["passed"])
        for case in report["cases"]:
            self.assertTrue(case["passed"], case)
            self.assertFalse(case["artifact_created"], case)
            if case["class"] == "success":
                self.assertEqual(case["route_outcome"], "delegate")
                self.assertEqual(case["adapter_outcome"], "ready")
                self.assertEqual(case["selected_function"], case["function"])
                self.assertEqual(case["fanout"], 1)
            elif case["class"] in {"disabled", "unavailable"}:
                self.assertEqual(case["adapter_outcome"], case["expected_outcome"])
                self.assertEqual(case["fanout"], 0)
            else:
                self.assertIsNone(case["selected_function"])
                self.assertEqual(case["adapter_outcome"], "unsupported")
                self.assertEqual(case["fanout"], 0)

    def test_declared_pass_or_boundary_booleans_are_rejected_not_trusted(self):
        cases = self.canonical_cases()
        cases[0]["passed"] = True
        cases[0]["boundary_violation"] = False

        with self.assertRaisesRegex(self.pilot.PilotError, "unknown_case_field"):
            self.evaluate_cases(cases)

    def test_wrong_expected_outcome_is_observed_as_failure(self):
        cases = self.canonical_cases()
        self.case(cases, "disabled-analyze")["expected_outcome"] = "ready"

        report = self.evaluate_cases(cases)

        observed = self.case(report["cases"], "disabled-analyze")
        self.assertFalse(observed["passed"])
        self.assertFalse(report["passed"])

    def test_ownership_request_cannot_hide_a_real_boundary_violation(self):
        cases = self.canonical_cases()
        ownership = self.case(cases, "ownership-git")
        ownership["request"] = "Spec Kit analyze the requirements"

        report = self.evaluate_cases(cases)

        self.assertFalse(self.case(report["cases"], "ownership-git")["passed"])
        self.assertEqual(report["metrics"]["boundary_violations"], 1)
        self.assertFalse(report["passed"])

    def test_pilot_real_path_rejects_every_canonical_lifecycle_and_git_alias(self):
        adapter = self.pilot.spec_kit_adapter
        self.assertEqual(set(adapter.LIFECYCLE_ACTION_ALIASES), set(LIFECYCLE_ACTIONS))
        self.assertEqual(
            set(adapter.KOREAN_LIFECYCLE_ACTION_ALIASES),
            set(KOREAN_LIFECYCLE_ACTIONS),
        )
        self.assertEqual(set(adapter.GIT_OPERATION_ALIASES), set(GIT_OPERATIONS))
        self.assertEqual(
            set(adapter.KOREAN_GIT_OPERATION_ALIASES), set(KOREAN_GIT_OPERATIONS)
        )
        registry = self.pilot.capability_routing.load_registry(ROOT)
        probes = [
            *(("lifecycle", f"Spec Kit analyze then {alias} the issue") for alias in LIFECYCLE_ACTIONS),
            *(("lifecycle", f"Spec Kit checklist then update {resource}") for resource in LIFECYCLE_RESOURCES),
            *(("lifecycle", f"스펙킷으로 분석한 다음 이슈를 {alias}") for alias in KOREAN_LIFECYCLE_ACTIONS),
            *(
                ("lifecycle", f"스펙킷으로 체크리스트 만든 뒤 {resource}를 수정해줘")
                for resource in KOREAN_LIFECYCLE_RESOURCES
            ),
            *(("git", f"Spec Kit converge then {operation} repository changes") for operation in GIT_OPERATIONS),
            *(
                (
                    "git",
                    (
                        f"스펙킷으로 분석한 뒤 {operation}해줘"
                        if operation in KOREAN_INTRINSIC_GIT_OPERATIONS
                        else f"스펙킷으로 명확화한 뒤 저장소에 {operation}해줘"
                    ),
                )
                for operation in KOREAN_GIT_OPERATIONS
            ),
        ]
        for boundary, request in probes:
            with self.subTest(request=request):
                observed = self.pilot._execute_case(
                    {
                        "id": "ownership-probe",
                        "class": "ownership",
                        "function": None,
                        "boundary": boundary,
                        "request": request,
                        "expected_outcome": "unsupported",
                        "result_file": None,
                    },
                    ROOT,
                    registry,
                    FIXTURES.parent,
                )
                self.assertTrue(observed["passed"], observed)
                self.assertIsNone(observed["selected_function"])
                self.assertEqual(observed["adapter_outcome"], "unsupported")
                self.assertFalse(observed["artifact_created"])

        report = self.evaluate_cases(self.canonical_cases())
        self.assertEqual(report["ownership_probes"]["total"], len(probes))
        self.assertEqual(report["ownership_probes"]["passed"], len(probes))
        self.assertEqual(report["ownership_probes"]["failed"], [])

    def test_pilot_real_path_accepts_context_free_validation_words(self):
        registry = self.pilot.capability_routing.load_registry(ROOT)

        for index, (request, expected_function) in enumerate(
            ORDINARY_VALIDATION_REQUESTS, start=1
        ):
            with self.subTest(request=request):
                observed = self.pilot._execute_case(
                    {
                        "id": f"positive-probe-{index}",
                        "class": "success",
                        "function": expected_function,
                        "boundary": None,
                        "request": request,
                        "expected_outcome": "ready",
                        "result_file": f"results/{expected_function}.json",
                    },
                    ROOT,
                    registry,
                    FIXTURES.parent,
                )
                self.assertTrue(observed["passed"], observed)
                self.assertEqual(observed["selected_function"], expected_function)
                self.assertEqual(observed["route_outcome"], "delegate")
                self.assertEqual(observed["adapter_outcome"], "ready")
                self.assertEqual(observed["fanout"], 1)
                self.assertFalse(observed["artifact_created"])

        report = self.evaluate_cases(self.canonical_cases())
        self.assertEqual(report["positive_probes"]["total"], 14)
        self.assertEqual(report["positive_probes"]["passed"], 14)
        self.assertEqual(report["positive_probes"]["failed"], [])

    def test_pilot_executes_intrinsic_korean_git_negative_without_context(self):
        registry = self.pilot.capability_routing.load_registry(ROOT)
        request = "스펙킷으로 분석한 뒤 스테이징해줘"

        self.assertIn(
            request,
            {case["request"] for case in self.pilot._ownership_probe_cases()},
        )
        observed = self.pilot._execute_case(
            {
                "id": "ownership-intrinsic-korean-git-probe",
                "class": "ownership",
                "function": None,
                "boundary": "git",
                "request": request,
                "expected_outcome": "unsupported",
                "result_file": None,
            },
            ROOT,
            registry,
            FIXTURES.parent,
        )
        self.assertTrue(observed["passed"], observed)
        self.assertIsNone(observed["selected_function"])
        self.assertEqual(observed["adapter_outcome"], "unsupported")
        self.assertFalse(observed["artifact_created"])

    def test_pilot_executes_table_driven_adjacent_ownership_phrases(self):
        registry = self.pilot.capability_routing.load_registry(ROOT)

        for index, request in enumerate(ADJACENT_OWNERSHIP_REQUESTS, start=1):
            with self.subTest(request=request):
                observed = self.pilot._execute_case(
                    {
                        "id": f"ownership-adjacent-probe-{index}",
                        "class": "ownership",
                        "function": None,
                        "boundary": (
                            "lifecycle"
                            if "issue" in request
                            or "roadmap" in request
                            or "project" in request
                            or "work item" in request
                            or "이슈" in request
                            or "로드맵" in request
                            or "프로젝트" in request
                            else "git"
                        ),
                        "request": request,
                        "expected_outcome": "unsupported",
                        "result_file": None,
                    },
                    ROOT,
                    registry,
                    FIXTURES.parent,
                )
                self.assertTrue(observed["passed"], observed)
                self.assertIsNone(observed["selected_function"])
                self.assertEqual(observed["adapter_outcome"], "unsupported")
                self.assertFalse(observed["artifact_created"])

        report = self.evaluate_cases(self.canonical_cases())
        self.assertEqual(report["adjacent_ownership_probes"]["total"], 19)
        self.assertEqual(report["adjacent_ownership_probes"]["passed"], 19)
        self.assertEqual(report["adjacent_ownership_probes"]["failed"], [])

    def test_pilot_executes_metamorphic_ownership_and_domain_target_probes(self):
        registry = self.pilot.capability_routing.load_registry(ROOT)
        for index, request in enumerate(METAMORPHIC_OWNERSHIP_REQUESTS, start=1):
            with self.subTest(kind="ownership", request=request):
                observed = self.pilot._execute_case(
                    {
                        "id": f"ownership-metamorphic-probe-{index}",
                        "class": "ownership",
                        "function": None,
                        "boundary": "lifecycle" if any(
                            word in request
                            for word in ("issue", "roadmap", "project", "이슈", "로드맵", "프로젝트")
                        ) else "git",
                        "request": request,
                        "expected_outcome": "unsupported",
                        "result_file": None,
                    },
                    ROOT,
                    registry,
                    FIXTURES.parent,
                )
                self.assertTrue(observed["passed"], observed)
        for index, (request, function) in enumerate(DOMAIN_TARGET_POSITIVE_REQUESTS, start=1):
            with self.subTest(kind="domain", request=request):
                observed = self.pilot._execute_case(
                    {
                        "id": f"positive-domain-probe-{index}",
                        "class": "success",
                        "function": function,
                        "boundary": None,
                        "request": request,
                        "expected_outcome": "ready",
                        "result_file": f"results/{function}.json",
                    },
                    ROOT,
                    registry,
                    FIXTURES.parent,
                )
                self.assertTrue(observed["passed"], observed)

        report = self.evaluate_cases(self.canonical_cases())
        self.assertEqual(report["metamorphic_ownership_probes"], {
            "total": 14, "passed": 14, "failed": []
        })
        self.assertEqual(report["positive_probes"], {
            "total": 14, "passed": 14, "failed": []
        })

    def test_pilot_executes_strong_clause_role_metamorphics(self):
        registry = self.pilot.capability_routing.load_registry(ROOT)
        negatives, positives = semantic_role_requests()
        for index, request in enumerate(negatives, start=1):
            with self.subTest(kind="ownership", request=request):
                boundary = "lifecycle" if any(
                    word in request
                    for word in ("issue", "paused", "이슈", "멈춰")
                ) else "git"
                observed = self.pilot._execute_case(
                    {
                        "id": f"ownership-role-probe-{index}",
                        "class": "ownership",
                        "function": None,
                        "boundary": boundary,
                        "request": request,
                        "expected_outcome": "unsupported",
                        "result_file": None,
                    },
                    ROOT,
                    registry,
                    FIXTURES.parent,
                )
                self.assertTrue(observed["passed"], observed)
        for index, (request, function) in enumerate(positives, start=1):
            with self.subTest(kind="advisory", request=request):
                observed = self.pilot._execute_case(
                    {
                        "id": f"positive-role-probe-{index}",
                        "class": "success",
                        "function": function,
                        "boundary": None,
                        "request": request,
                        "expected_outcome": "ready",
                        "result_file": f"results/{function}.json",
                    },
                    ROOT,
                    registry,
                    FIXTURES.parent,
                )
                self.assertTrue(observed["passed"], observed)

    def test_success_snapshots_use_derived_input_hash_context_and_synthetic_latency(self):
        report = self.evaluate_cases(self.canonical_cases())

        for function in FUNCTIONS:
            case = self.case(report["cases"], f"success-{function}")
            result = json.loads((FIXTURES.parent / case["result_file"]).read_text(encoding="utf-8"))
            self.assertEqual(result["input_hash"], independent_input_hash(function))
            self.assertEqual(
                result["loaded_context_chars"],
                independent_loaded_context_chars(function),
            )
            self.assertEqual(result["elapsed_ms"], 0)

    def test_tampered_snapshot_cost_or_input_identity_is_rejected(self):
        for field, value in (("input_hash", "sha256:" + "0" * 64), ("loaded_context_chars", 1)):
            with self.subTest(field=field):
                with tempfile.TemporaryDirectory() as tmp:
                    fixtures = self.copy_fixtures(Path(tmp))
                    result_path = fixtures.parent / "results" / "analyze.json"
                    result = json.loads(result_path.read_text(encoding="utf-8"))
                    result[field] = value
                    result["run_id"] = self.pilot.spec_kit_adapter._result_hash(result)
                    result_path.write_text(json.dumps(result), encoding="utf-8")
                    cases = self.pilot.load_cases(fixtures)["cases"]
                    with self.assertRaisesRegex(self.pilot.PilotError, "invalid_result_snapshot"):
                        self.evaluate_cases(cases, result_base=fixtures.parent)

    def test_case_ids_outside_safe_markdown_identifier_are_rejected(self):
        for unsafe in ("Upper-Case", "bad|cell", "line\nbreak", "../escape", "html<script>"):
            with self.subTest(case_id=unsafe):
                cases = self.canonical_cases()
                cases[0]["id"] = unsafe
                with self.assertRaisesRegex(self.pilot.PilotError, "invalid_case"):
                    self.evaluate_cases(cases)

    def test_markdown_table_cells_escape_pipes_controls_and_html(self):
        report = self.evaluate_cases(self.canonical_cases())
        report["cases"][0]["function"] = "analyze|x\n<script>"

        rendered = self.pilot.render_report(report)

        self.assertIn(r"analyze\|x &lt;script&gt;", rendered)
        self.assertNotIn("| analyze|x", rendered)
        self.assertNotIn("<script>", rendered)

    def test_matrix_coverage_and_snapshot_provenance_remain_fail_closed(self):
        cases = self.canonical_cases()
        with self.assertRaisesRegex(self.pilot.PilotError, "invalid_matrix"):
            self.evaluate_cases(cases[:-1])

        cases = self.canonical_cases()
        self.case(cases, "success-clarify")["result_file"] = "results/does-not-exist.json"
        with self.assertRaisesRegex(self.pilot.PilotError, "unsafe_result_path"):
            self.evaluate_cases(cases)

    def test_metric_denominators_use_reviewed_findings_and_derived_costs(self):
        report = self.evaluate_cases(self.canonical_cases())
        total_chars = sum(independent_loaded_context_chars(function) for function in FUNCTIONS)

        self.assertEqual(report["metrics"]["actionable_value"], 4)
        self.assertEqual(report["metrics"]["false_positive_rate"], 0.1429)
        self.assertEqual(report["metrics"]["native_overlap_rate"], 0.2857)
        self.assertEqual(report["metrics"]["elapsed_ms"], 0)
        self.assertEqual(report["metrics"]["loaded_context_chars"], total_chars)
        self.assertEqual(report["metrics"]["estimated_loaded_tokens"], (total_chars + 3) // 4)
        for metric in (
            "boundary_violations",
            "unauthorized_writes",
            "unwanted_fanout",
            "false_execution_claims",
        ):
            self.assertEqual(report["metrics"][metric], 0)

    def test_report_is_sorted_and_labels_latency_as_synthetic(self):
        cases = self.canonical_cases()
        report = self.evaluate_cases(list(reversed(cases)))
        rendered = self.pilot.render_report(report)

        self.assertEqual(
            [case["id"] for case in report["cases"]],
            sorted(case["id"] for case in cases),
        )
        self.assertIn("Human decision: pending", rendered)
        self.assertIn("Wider/default activation: prohibited", rendered)
        self.assertIn("Synthetic fixture latency", rendered)
        self.assertIn("real router and adapter", rendered)

    def test_default_cli_is_dry_run_and_write_is_repeat_byte_stable(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fixtures = self.copy_fixtures(root)
            target = root / "specs" / ISSUE_ID / "pilot-report.md"

            dry_run = self.run_cli(root, fixtures)
            self.assertEqual(dry_run.returncode, 0, dry_run.stderr)
            self.assertFalse(target.exists())
            self.assertTrue(json.loads(dry_run.stdout)["passed"])

            first = self.run_cli(root, fixtures, "--write")
            self.assertEqual(first.returncode, 0, first.stderr)
            first_bytes = target.read_bytes()
            second = self.run_cli(root, fixtures, "--write")
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertEqual(target.read_bytes(), first_bytes)

    def test_failed_observation_exits_nonzero_without_replacing_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fixtures = self.copy_fixtures(root)
            payload = json.loads(fixtures.read_text(encoding="utf-8"))
            payload["cases"][0]["expected_outcome"] = "ready"
            fixtures.write_text(json.dumps(payload), encoding="utf-8")
            target = root / "specs" / ISSUE_ID / "pilot-report.md"
            target.parent.mkdir(parents=True)
            target.write_bytes(b"preserve-me\n")

            result = self.run_cli(root, fixtures, "--write")

            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(target.read_bytes(), b"preserve-me\n")

    def test_cli_parse_and_utf8_errors_use_common_json_envelope_without_traceback(self):
        missing = subprocess.run(
            [sys.executable, str(SCRIPT), "."],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(missing.returncode, 2)
        self.assertEqual(missing.stderr, "")
        self.assertEqual(
            json.loads(missing.stdout)["schema"], "moduflow.spec-kit-error.v1"
        )

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fixtures = self.copy_fixtures(root)
            fixtures.write_bytes(b"\xff")
            bad_cases = self.run_cli(root, fixtures)
            self.assertEqual(bad_cases.returncode, 2)
            self.assertEqual(bad_cases.stderr, "")
            self.assertEqual(
                json.loads(bad_cases.stdout)["schema"], "moduflow.spec-kit-error.v1"
            )

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fixtures = self.copy_fixtures(root)
            (fixtures.parent / "results" / "analyze.json").write_bytes(b"\xff")
            bad_result = self.run_cli(root, fixtures)
            self.assertEqual(bad_result.returncode, 2)
            self.assertEqual(bad_result.stderr, "")
            self.assertEqual(
                json.loads(bad_result.stdout)["schema"], "moduflow.spec-kit-error.v1"
            )

    def test_direct_write_reexecutes_cases_before_replacing_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "specs" / ISSUE_ID / "pilot-report.md"
            target.parent.mkdir(parents=True)
            target.write_bytes(b"preserve-me\n")
            report = self.evaluate_cases(self.canonical_cases())
            report["cases"][0]["expected_outcome"] = "ready"

            with self.assertRaisesRegex(self.pilot.PilotError, "invalid_report"):
                self.pilot.write_report(
                    root,
                    report,
                    result_base=FIXTURES.parent,
                    package_root=ROOT,
                )
            self.assertEqual(target.read_bytes(), b"preserve-me\n")

    def test_symlinked_output_ancestor_is_rejected_without_external_write(self):
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as outside:
            root = Path(tmp)
            fixtures = self.copy_fixtures(root)
            (root / "specs").symlink_to(Path(outside), target_is_directory=True)

            result = self.run_cli(root, fixtures, "--write")

            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(list(Path(outside).iterdir()), [])


if __name__ == "__main__":
    unittest.main()
