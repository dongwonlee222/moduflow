"""Issue 104 step 1: the `moduflow.request-routing.v1` contract and stage 1.

Every test here is RED before `scripts/request_routing.py` exists. The module
resolves a project first and calls nothing else until it has one, so these
fixtures build two registered projects in a tmp dir and assert on which one a
request reaches — and, for the isolation cases, on which one it does not.

Nothing in this file writes to the repository.
"""
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))


def load_module(name, relative_path):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


routing = load_module("request_routing", "scripts/request_routing.py")


# --------------------------------------------------------------------------
# Fixture: two registered projects, one Korean-named, one English-named.
# R5 requires both directions in both languages, so neither is the "default".
# --------------------------------------------------------------------------

def build_registry():
    tmp = Path(tempfile.mkdtemp())
    projects = []
    for pid, name, alias in (
        ("project-a", "Project A", "이벤트"),
        ("modu-charge", "모두의충전", "charge"),
    ):
        root = tmp / pid
        # All seven canonical paths, not a subset: the loader marks a registry
        # invalid when one is missing, and an invalid registry never reaches the
        # alias branch these tests are about.
        subs = (
            "issues", "specs", "workspace", "knowledge", "memory",
            "memory/production-records", "playbooks", "workflow",
        )
        for sub in subs:
            (root / sub).mkdir(parents=True, exist_ok=True)
        (root / "issues" / f"001-{pid}-only.md").write_text(
            f"# Issue 001: {pid} only\n\n"
            f"**Status: backlog** — created 2026-09-07.\n**Priority: p2**\n\n"
            f"## 안 고치면\n\n{pid} 전용 이슈입니다. 다른 프로젝트에 보이면 안 됩니다.\n",
            encoding="utf-8",
        )
        # A finished issue. Overlap is about work someone might still attach to,
        # so a `done` issue is not a candidate — and this file is how that is
        # asserted rather than assumed.
        (root / "issues" / f"002-{pid}-finished.md").write_text(
            f"# Issue 002: {pid} finished\n\n"
            f"**Status: done** — completed 2026-09-07.\n**Priority: p2**\n\n"
            f"## 안 고치면\n\n끝난 일입니다.\n",
            encoding="utf-8",
        )
        projects.append(
            {
                "id": pid,
                "name": name,
                "root": str(root),
                "aliases": [alias],
                "paths": {
                    "issues": "issues",
                    "specs": "specs",
                    "workspace": "workspace",
                    "knowledge": "knowledge",
                    "memory": "memory",
                    "production_records": "memory/production-records",
                    "playbooks": "playbooks",
                    "workflow": "workflow",
                },
                "trust_scope": "internal",
                "status": "active",
                "owner": "Dongwon Lee",
            }
        )
    registry = tmp / "projects.json"
    registry.write_text(
        json.dumps({"schema": "moduflow.projects.v2", "projects": projects}, ensure_ascii=False),
        encoding="utf-8",
    )
    return registry


REQUIRED_FIELDS = (
    "schema",
    "request_id",
    "request",
    "project",
    "stage",
    "status",
    "action",
    "issue",
    "overlap_candidates",
    "capability",
    "execution",
    "question",
    "written",
    "next_command",
)


class ContractTests(unittest.TestCase):
    """R1 — every field present in every result, whatever the status."""

    def setUp(self):
        self.registry = build_registry()

    def test_schema_is_pinned(self):
        self.assertEqual(routing.ROUTING_SCHEMA, "moduflow.request-routing.v1")

    def test_every_field_present_on_a_resolved_request(self):
        result = routing.route_request("이벤트 프로젝트 상태 알려줘", self.registry)
        for field in REQUIRED_FIELDS:
            self.assertIn(field, result, f"{field} missing on an ok result")
        self.assertEqual(result["schema"], "moduflow.request-routing.v1")

    def test_every_field_present_on_an_ambiguous_request(self):
        result = routing.route_request("상태 알려줘", self.registry)
        for field in REQUIRED_FIELDS:
            self.assertIn(field, result, f"{field} missing on an ambiguous result")

    def test_status_is_from_the_closed_set(self):
        for request in ("이벤트 상태", "상태 알려줘", ""):
            result = routing.route_request(request, self.registry)
            self.assertIn(result["status"], {"ok", "ambiguous", "refused", "blocked"})

    def test_stage_is_from_the_closed_set(self):
        result = routing.route_request("이벤트 상태", self.registry)
        self.assertIn(
            result["stage"],
            {"resolve", "overlap", "capability", "execution", "commit"},
        )


class Stage1Tests(unittest.TestCase):
    """R2 — resolve before reading, and one question when ambiguous."""

    def setUp(self):
        self.registry = build_registry()

    def test_an_alias_resolves_to_its_project(self):
        result = routing.route_request("이벤트 프로젝트 상태", self.registry)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["project"], "project-a")

    def test_a_korean_name_resolves_to_its_project(self):
        result = routing.route_request("모두의충전 상태 알려줘", self.registry)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["project"], "modu-charge")

    def test_ambiguous_asks_exactly_one_question(self):
        result = routing.route_request("상태 알려줘", self.registry)
        self.assertEqual(result["status"], "ambiguous")
        self.assertIsNotNone(result["question"])
        self.assertIsInstance(result["question"], str)
        # One question. Not a list, and not two sentences joined by a newline.
        self.assertNotIn("\n", result["question"].strip())

    def test_ambiguous_has_no_project_and_writes_nothing(self):
        result = routing.route_request("상태 알려줘", self.registry)
        self.assertIsNone(result["project"])
        self.assertEqual(result["written"], [])

    def test_question_is_null_when_not_ambiguous(self):
        result = routing.route_request("이벤트 상태", self.registry)
        self.assertIsNone(result["question"])

    def test_written_is_empty_for_every_non_ok_status(self):
        for request in ("상태 알려줘", ""):
            result = routing.route_request(request, self.registry)
            if result["status"] != "ok":
                self.assertEqual(result["written"], [], request)

    def test_stage_1_stops_at_resolve_when_it_cannot_resolve(self):
        result = routing.route_request("상태 알려줘", self.registry)
        self.assertEqual(result["stage"], "resolve")

    def test_an_unresolvable_request_calls_no_capability(self):
        """R2 — zero capability calls on ambiguity, asserted by mock not by tree."""
        calls = []
        original = routing.capability_routing.route_request
        routing.capability_routing.route_request = lambda *a, **k: calls.append(a)
        try:
            routing.route_request("상태 알려줘", self.registry)
        finally:
            routing.capability_routing.route_request = original
        self.assertEqual(calls, [])


class Stage2OverlapTests(unittest.TestCase):
    """R3 — surface the resolved project's open issues; judge none of them.

    Measured 2026-09-07 over 147 issues and 10,731 pairs: no mechanical rule
    separates same-work pairs from unrelated ones, and five of seven confirmed
    pairs score 0.00 on title similarity. So the stage returns candidates, the
    reader names the overlap, and `test_no_score_rank_or_verdict` is the test
    that fails if a threshold is ever put back.
    """

    def setUp(self):
        self.registry = build_registry()

    def test_candidates_are_the_resolved_projects_open_issues(self):
        result = routing.route_request("이벤트 이슈 보여줘", self.registry)
        ids = [c["issue"] for c in result["overlap_candidates"]]
        self.assertEqual(ids, ["001-project-a-only"])

    def test_candidate_carries_the_blocked_without_this_line(self):
        result = routing.route_request("이벤트 이슈 보여줘", self.registry)
        candidate = result["overlap_candidates"][0]
        self.assertIn("project-a 전용 이슈입니다", candidate["blocked_without_this"])
        self.assertEqual(candidate["title"], "project-a only")

    def test_no_score_rank_or_verdict(self):
        """The measurement ruled these out. This test is why they stay out."""
        result = routing.route_request("이벤트 이슈 보여줘", self.registry)
        for candidate in result["overlap_candidates"]:
            for banned in ("score", "similarity", "rank", "confidence", "match"):
                self.assertNotIn(banned, candidate, f"{banned} is a threshold by another name")
        self.assertIsNone(result["action"])
        self.assertIsNone(result["issue"])

    def test_done_issues_are_not_candidates(self):
        result = routing.route_request("이벤트 이슈 보여줘", self.registry)
        done = [c for c in result["overlap_candidates"] if c["issue"].startswith("002")]
        self.assertEqual(done, [])

    def test_stage_2_writes_nothing(self):
        result = routing.route_request("이벤트 이슈 보여줘", self.registry)
        self.assertEqual(result["written"], [])

    def test_attaching_to_a_candidate_sets_action_and_issue(self):
        result = routing.route_request(
            "이벤트 이슈 고쳐줘", self.registry, chosen_issue="001-project-a-only"
        )
        self.assertEqual(result["action"], "attach")
        self.assertEqual(result["issue"], "001-project-a-only")

    def test_attaching_to_another_projects_issue_is_refused(self):
        """R5's sharpest edge — the caller names an id that is not in scope."""
        result = routing.route_request(
            "이벤트 이슈 고쳐줘", self.registry, chosen_issue="001-modu-charge-only"
        )
        self.assertEqual(result["status"], "refused")
        self.assertEqual(result["stage"], "overlap")
        self.assertIsNone(result["issue"])
        self.assertEqual(result["written"], [])


def add_capability_registry(registry_path, project_id, *, valid=True):
    """Give one fixture project an adapter registry. `valid=False` corrupts it."""
    payload = json.loads(Path(registry_path).read_text(encoding="utf-8"))
    root = Path(
        next(p["root"] for p in payload["projects"] if p["id"] == project_id)
    )
    (root / "adapters").mkdir(exist_ok=True)
    # Every field 097's validator requires, and the three global lists non-empty.
    # A short fixture that omits one is rejected as a corrupt registry, which
    # makes the "no adapters" case and the "broken adapters" case look alike —
    # exactly the distinction these tests are here to hold apart.
    (root / "adapters" / "documents.yaml").write_text("id: documents\n", encoding="utf-8")
    body = {
        "schema": "moduflow.capability-registry.v1",
        "lifecycle_triggers": ["이슈", "issue"],
        "sequence_markers": ["다음", "next"],
        "external_write_triggers": ["게시", "publish"],
        "capabilities": [
            {
                "id": "documents",
                "adapter_path": "adapters/documents.yaml",
                "purpose": "document drafting",
                "triggers": ["문서", "document"],
                "explicit_triggers": ["문서 작성"],
                "exclusions": [],
                "default_available": True,
                "permission": "write-local",
                "output_artifact": "specs/{issue_id}/document.md",
                "setup_recommendation": "문서 어댑터를 설치하세요.",
            }
        ],
    }
    if not valid:
        body["schema"] = "moduflow.not-a-registry.v9"
    (root / "adapters" / "capability-routing.json").write_text(
        json.dumps(body, ensure_ascii=False), encoding="utf-8"
    )
    return root


def add_tasks_file(registry_path, project_id, issue_id, body):
    payload = json.loads(Path(registry_path).read_text(encoding="utf-8"))
    root = Path(
        next(p["root"] for p in payload["projects"] if p["id"] == project_id)
    )
    spec_dir = root / "specs" / issue_id
    spec_dir.mkdir(parents=True, exist_ok=True)
    (spec_dir / "tasks.md").write_text(body, encoding="utf-8")
    return spec_dir / "tasks.md"


class Stage3CapabilityTests(unittest.TestCase):
    """R4 — consume `capability_routing`, never re-derive it."""

    def setUp(self):
        self.registry = build_registry()

    def test_no_registry_is_outcome_none_not_a_refusal(self):
        """A project with no adapters routes nothing. That is normal.

        Reading it as a refusal would refuse every request ModuFlow handles
        itself, which is most of them.
        """
        result = routing.route_request("이벤트 상태 알려줘", self.registry)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["capability"]["outcome"], "none")

    def test_a_corrupt_registry_blocks_rather_than_reading_as_none(self):
        """A missing registry and a broken one are different facts."""
        add_capability_registry(self.registry, "project-a", valid=False)
        result = routing.route_request("이벤트 문서 작성해줘", self.registry)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["stage"], "capability")
        self.assertEqual(result["written"], [])

    def test_the_097_result_is_carried_verbatim(self):
        add_capability_registry(self.registry, "project-a")
        result = routing.route_request("이벤트 문서 작성해줘", self.registry)
        self.assertEqual(
            result["capability"]["schema"], "moduflow.capability-routing.v1"
        )
        # Not reinterpreted: the keys 097 emits are the keys that arrive.
        for field in ("outcome", "stages", "current_stage", "sequence_state"):
            self.assertIn(field, result["capability"])


class Stage4ExecutionTests(unittest.TestCase):
    """R4 — consume 112's `build_routing` unchanged."""

    def setUp(self):
        self.registry = build_registry()

    def test_no_chosen_issue_means_nothing_to_execute(self):
        result = routing.route_request("이벤트 상태 알려줘", self.registry)
        self.assertEqual(result["status"], "ok")
        self.assertIsNone(result["execution"])

    def test_ready_tasks_route_and_the_112_result_is_carried_verbatim(self):
        add_tasks_file(
            self.registry,
            "project-a",
            "001-project-a-only",
            "# Tasks\n\n## Implementation\n\n"
            "- [ ] T01 Edit the parser [files: scripts/parser.py]\n",
        )
        result = routing.route_request(
            "이벤트 고쳐줘", self.registry, chosen_issue="001-project-a-only"
        )
        self.assertEqual(
            result["execution"]["schema"], "moduflow.execution-routing.v1"
        )
        self.assertEqual(result["execution"]["project_root"], ".")
        self.assertFalse(result["execution"]["dispatched"])

    def test_needs_plan_blocks_with_written_empty(self):
        add_tasks_file(
            self.registry,
            "project-a",
            "001-project-a-only",
            "# Tasks\n\n## Implementation\n\n- [ ] T01 어떻게든 해줘\n",
        )
        result = routing.route_request(
            "이벤트 고쳐줘", self.registry, chosen_issue="001-project-a-only"
        )
        # Asserted, not guarded on. Written as `if status == "needs_plan":` this
        # passes for free the day the fixture stops producing one, and the test
        # then proves nothing while still going green.
        self.assertEqual(result["execution"]["status"], "needs_plan")
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["stage"], "execution")
        self.assertEqual(result["written"], [])

    def test_execution_never_claims_it_dispatched(self):
        add_tasks_file(
            self.registry,
            "project-a",
            "001-project-a-only",
            "# Tasks\n\n## Implementation\n\n"
            "- [ ] T01 Edit the parser [files: scripts/parser.py]\n",
        )
        result = routing.route_request(
            "이벤트 고쳐줘", self.registry, chosen_issue="001-project-a-only"
        )
        self.assertFalse(result["execution"]["dispatched"])
        self.assertIsNone(result["execution"]["executed_by"])
        self.assertEqual(result["written"], [])


class Stage5CommitTests(unittest.TestCase):
    """R6 — the only stage that writes, and only when told to.

    **These do not re-test 103's rollback.** Issue 103 owns proving that a
    transaction leaves no half-written state, and it has its own suite for it.
    What this module owns is narrower and is what is asserted here: stage 5
    calls the existing transition rather than building its own, it does not
    write unless the caller asked, and when the transaction refuses, the
    pipeline stops with `written: []` instead of reporting success.
    """

    def setUp(self):
        self.registry = build_registry()
        add_tasks_file(
            self.registry,
            "project-a",
            "001-project-a-only",
            "# Tasks\n\n## Implementation\n\n"
            "- [ ] T01 Edit the parser [files: scripts/parser.py]\n",
        )

    def test_a_routing_call_does_not_write_by_default(self):
        calls = []
        original = routing.project_lifecycle.transition_lifecycle
        routing.project_lifecycle.transition_lifecycle = lambda *a, **k: calls.append(a)
        try:
            result = routing.route_request(
                "이벤트 고쳐줘", self.registry, chosen_issue="001-project-a-only"
            )
        finally:
            routing.project_lifecycle.transition_lifecycle = original
        self.assertEqual(calls, [], "asking what a request routes to must not transact")
        self.assertEqual(result["written"], [])
        self.assertEqual(result["status"], "ok")

    def test_commit_true_calls_the_existing_transition_not_a_new_intent(self):
        """R4's rule one layer down: consume `transition_lifecycle`, do not
        rebuild `LifecycleIntent` here."""
        seen = {}

        def fake(root, issue_id, action, **kwargs):
            seen.update(
                {"root": root, "issue_id": issue_id, "action": action, **kwargs}
            )
            return {"schema": "moduflow.lifecycle-transaction.v1", "status": "complete"}

        original = routing.project_lifecycle.transition_lifecycle
        routing.project_lifecycle.transition_lifecycle = fake
        try:
            result = routing.route_request(
                "이벤트 고쳐줘",
                self.registry,
                chosen_issue="001-project-a-only",
                commit=True,
            )
        finally:
            routing.project_lifecycle.transition_lifecycle = original

        self.assertEqual(seen["issue_id"], "001-project-a-only")
        self.assertEqual(seen["action"], "start")
        self.assertEqual(seen["source_event"], "request-routing")
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["stage"], "commit")
        self.assertTrue(result["written"])

    def test_a_refused_transaction_blocks_with_written_empty(self):
        def fake(*args, **kwargs):
            raise RuntimeError("PROJECTED_VALIDATION_FAILED")

        original = routing.project_lifecycle.transition_lifecycle
        routing.project_lifecycle.transition_lifecycle = fake
        try:
            result = routing.route_request(
                "이벤트 고쳐줘",
                self.registry,
                chosen_issue="001-project-a-only",
                commit=True,
            )
        finally:
            routing.project_lifecycle.transition_lifecycle = original

        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["stage"], "commit")
        self.assertEqual(result["written"], [])
        self.assertIn("PROJECTED_VALIDATION_FAILED", result["next_command"])

    def test_nothing_to_commit_when_no_issue_was_chosen(self):
        calls = []
        original = routing.project_lifecycle.transition_lifecycle
        routing.project_lifecycle.transition_lifecycle = lambda *a, **k: calls.append(a)
        try:
            result = routing.route_request(
                "이벤트 상태 알려줘", self.registry, commit=True
            )
        finally:
            routing.project_lifecycle.transition_lifecycle = original
        self.assertEqual(calls, [])
        self.assertEqual(result["written"], [])
        self.assertEqual(result["status"], "ok")


class HubWiringTests(unittest.TestCase):
    """T10 — a bare sentence reaches this module, and no command file appears.

    The spec's reason for fixing the stage order is that
    `project_registry.resolve_project` already exists and *nothing forces a
    caller through it first*. The hub was one of those callers: it went straight
    to `capability_routing.py`, which is stage 3, skipping resolve and overlap.
    """

    HUB = ROOT / "commands" / "moduflow.md"

    def test_no_new_command_file(self):
        """41 before this issue. A router is not a command."""
        names = sorted(p.name for p in (ROOT / "commands").glob("*.md"))
        self.assertEqual(len(names), 41, names)
        self.assertNotIn("product-request.md", names)
        self.assertNotIn("product-route.md", names)

    def test_the_hub_routes_a_sentence_through_request_routing(self):
        text = self.HUB.read_text(encoding="utf-8")
        self.assertIn("scripts/request_routing.py", text)

    def test_the_hub_no_longer_calls_stage_3_directly(self):
        """Calling `capability_routing.py` from the hub is the skip this fixes."""
        text = self.HUB.read_text(encoding="utf-8")
        self.assertNotIn("scripts/capability_routing.py", text)

    def test_the_hub_states_that_a_sentence_does_not_write(self):
        text = self.HUB.read_text(encoding="utf-8")
        self.assertIn("--commit", text)


class FiveSourceScenarioTests(unittest.TestCase):
    """T11 — the five scenarios the spec's Verification Strategy names.

    Existing-campaign revision, new-project deliverable, ambiguous project,
    unavailable capability, state-write failure. Each asserts the whole result,
    not one field, because the point of the contract is that a reader gets the
    same shape whatever happened.
    """

    def setUp(self):
        self.registry = build_registry()
        add_tasks_file(
            self.registry,
            "project-a",
            "001-project-a-only",
            "# Tasks\n\n## Implementation\n\n"
            "- [ ] T01 Edit the parser [files: scripts/parser.py]\n",
        )

    def test_1_existing_work_revision_attaches(self):
        """"그 이슈 마저 해줘" — the work exists, so attach rather than file again."""
        result = routing.route_request(
            "이벤트 001 이슈 마저 해줘",
            self.registry,
            chosen_issue="001-project-a-only",
        )
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["action"], "attach")
        self.assertEqual(result["issue"], "001-project-a-only")
        self.assertEqual(result["written"], [])

    def test_2_new_deliverable_writes_no_issue_file(self):
        """Nothing is chosen, so the pipeline proposes and files nothing."""
        before = sorted(
            p.name
            for p in (
                Path(
                    json.loads(Path(self.registry).read_text())["projects"][0]["root"]
                )
                / "issues"
            ).glob("*.md")
        )
        result = routing.route_request("이벤트 새로운 보고서 만들어줘", self.registry)
        after = sorted(
            p.name
            for p in (
                Path(
                    json.loads(Path(self.registry).read_text())["projects"][0]["root"]
                )
                / "issues"
            ).glob("*.md")
        )
        self.assertEqual(before, after, "stage 2 must never write an issue file")
        self.assertIsNone(result["issue"])
        self.assertEqual(result["written"], [])

    def test_3_ambiguous_project_asks_one_question_and_stops(self):
        result = routing.route_request("상태 알려줘", self.registry)
        self.assertEqual(result["status"], "ambiguous")
        self.assertEqual(result["stage"], "resolve")
        self.assertNotIn("\n", result["question"].strip())
        self.assertEqual(result["overlap_candidates"], [])
        self.assertIsNone(result["capability"])
        self.assertEqual(result["written"], [])

    def test_4_unavailable_capability_reports_and_does_not_pretend(self):
        result = routing.route_request("이벤트 상태 알려줘", self.registry)
        self.assertEqual(result["capability"]["outcome"], "none")
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["written"], [])

    def test_5_state_write_failure_stops_with_written_empty(self):
        def fake(*args, **kwargs):
            raise RuntimeError("POST_APPLY_VALIDATION_FAILED")

        original = routing.project_lifecycle.transition_lifecycle
        routing.project_lifecycle.transition_lifecycle = fake
        try:
            result = routing.route_request(
                "이벤트 001 이슈 시작해줘",
                self.registry,
                chosen_issue="001-project-a-only",
                commit=True,
            )
        finally:
            routing.project_lifecycle.transition_lifecycle = original
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["stage"], "commit")
        self.assertEqual(result["written"], [])
        # Every contract field still present on the worst path.
        self.assertEqual(sorted(result), sorted(REQUIRED_FIELDS))


class OrderingTests(unittest.TestCase):
    """The spec names silent reordering as this issue's characteristic failure.

    An outcome test passes when the stages run backwards and happen to agree, so
    these assert the call sequence itself.
    """

    def setUp(self):
        self.registry = build_registry()

    def test_stages_run_in_order(self):
        seen = []
        originals = {}
        for name in ("stage_resolve", "stage_overlap", "stage_capability",
                     "stage_execution", "stage_commit"):
            originals[name] = getattr(routing, name)

        def wrap(name, fn):
            def wrapped(*args, **kwargs):
                seen.append(name)
                return fn(*args, **kwargs)
            return wrapped

        for name, fn in originals.items():
            setattr(routing, name, wrap(name, fn))
        try:
            routing.route_request("이벤트 상태", self.registry)
        finally:
            for name, fn in originals.items():
                setattr(routing, name, fn)

        # The exact list, not "is it sorted" — a run that skipped three stages
        # is also sorted, and skipping is the failure this test exists for.
        self.assertEqual(
            seen,
            [
                "stage_resolve",
                "stage_overlap",
                "stage_capability",
                "stage_execution",
                "stage_commit",
            ],
        )

    def test_a_stage_refuses_without_its_predecessor(self):
        """Order is enforced by structure: a later stage fails on a missing field."""
        with self.assertRaises(routing.StageOrderError):
            routing.stage_capability({"stage": "resolve", "project": None})


class IsolationTests(unittest.TestCase):
    """R5 — a leak that only shows in one language is still a leak.

    These had no teeth at step 1: stages 2-5 read nothing, so no result could
    carry another project's content whatever the code did. **They have teeth
    now.** Stage 2 opens `issues/` and each fixture project holds an issue whose
    body names its own project id, so a result that reached across shows it.
    """

    def setUp(self):
        self.registry = build_registry()

    def test_project_a_never_surfaces_project_b(self):
        result = routing.route_request("이벤트 프로젝트 이슈 보여줘", self.registry)
        self.assertEqual(result["project"], "project-a")
        self.assertNotIn("modu-charge", json.dumps(result, ensure_ascii=False))

    def test_project_b_never_surfaces_project_a(self):
        result = routing.route_request("모두의충전 이슈 보여줘", self.registry)
        self.assertEqual(result["project"], "modu-charge")
        self.assertNotIn("project-a", json.dumps(result, ensure_ascii=False))

    def test_result_carries_no_internal_carry_fields(self):
        """The stages pass state to each other through `_`-prefixed keys.

        `_resolution` holds the resolver's own view — candidates, absolute
        roots, trust scope. Returning it would hand a caller more than the
        contract lists, and R1 is a closed field set. This asserts the strip,
        which is the mechanism the two tests above will depend on once stage 2
        actually reads issue files.
        """
        result = routing.route_request("이벤트 상태", self.registry)
        leaked = [key for key in result if key.startswith("_")]
        self.assertEqual(leaked, [])
        self.assertEqual(sorted(result), sorted(REQUIRED_FIELDS))


if __name__ == "__main__":
    unittest.main()
