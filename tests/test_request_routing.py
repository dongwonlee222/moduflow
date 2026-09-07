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
