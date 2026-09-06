"""Issue 112 Streams A and B: the execution-routing gates.

Ported from the measured prototype in
`specs/112-execution-planner-and-backend-boundary/evidence/`, which ran against
all 55 specs on 2026-09-05. The corpus cases below are the fixtures spec §13
requires; the synthetic ones use tmp dirs so nothing in the repository is
touched. The gates never write, so no test needs to clean up after them.
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

FIXTURES = ROOT / "tests/fixtures/execution-routing"


def load_module(name, relative_path):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


routing = load_module("execution_routing", "scripts/execution_routing.py")


def write_tasks(body):
    tmp = Path(tempfile.mkdtemp())
    path = tmp / "tasks.md"
    path.write_text(body, encoding="utf-8")
    return path


def route(body):
    path = write_tasks(body)
    return routing.build_routing(routing.scan_tasks(path), path.parent)


def kinds(result):
    return sorted(gap["kind"] for gap in result["gaps"])


class ScanParity(unittest.TestCase):
    """The scan adds a section and an id; it must not otherwise drift."""

    def test_scan_matches_the_shipped_parser_on_every_spec(self):
        parse_tasks = load_module("worker_orchestrator_parity", "scripts/worker_orchestrator.py").parse_tasks
        checked = 0
        for tasks_path in sorted(ROOT.glob("specs/*/tasks.md")):
            try:
                shipped = parse_tasks(tasks_path)
            except ValueError:
                continue
            scanned = routing.scan_tasks(tasks_path)
            self.assertEqual(
                [(task["text"], task["status"]) for task in shipped],
                [(task["text"], task["status"]) for task in scanned],
                f"scan diverged from parse_tasks on {tasks_path}",
            )
            checked += 1
        self.assertGreater(checked, 40, "expected to compare against the real corpus")


class Gate1SemanticFilter(unittest.TestCase):
    def test_a_completed_task_is_not_executable_work(self):
        path = write_tasks("- [x] Add the thing [files: a.py]\n- [ ] Do the other [files: b.py]\n")
        kept = routing.gate1_executable(routing.scan_tasks(path))
        self.assertEqual([task["id"] for task in kept], ["T02"])

    def test_a_deferred_task_is_not_executable_even_when_it_declares_files(self):
        path = write_tasks("- [ ] [deferred → 118-other] Implementation: x [files: scripts/a.py]\n")
        self.assertEqual(routing.gate1_executable(routing.scan_tasks(path)), [])

    def test_the_required_gates_section_never_becomes_work(self):
        path = write_tasks(
            "## Ready\n- [ ] Build the parser [files: scripts/p.py]\n"
            "## Required Gates\n- [ ] All acceptance criteria have evidence [files: x.md]\n"
        )
        kept = routing.gate1_executable(routing.scan_tasks(path))
        self.assertEqual([task["text"] for task in kept], ["Build the parser"])

    def test_verification_and_converge_findings_sections_never_become_work(self):
        path = write_tasks(
            "## Stream A\n- [ ] Write the adapter [files: scripts/a.py]\n"
            "## Verification\n- [ ] RED to GREEN on tests.test_a\n"
            "## Converge Findings (auto)\n- [ ] CV-1 [high] emits wrong ref\n"
        )
        kept = routing.gate1_executable(routing.scan_tasks(path))
        self.assertEqual([task["text"] for task in kept], ["Write the adapter"])

    def test_a_task_under_no_heading_still_survives(self):
        """141 of the corpus checkboxes live under no heading at all."""
        path = write_tasks("- [ ] Implement metadata routing [files: scripts/w.py]\n")
        self.assertEqual(len(routing.gate1_executable(routing.scan_tasks(path))), 1)

    def test_a_stream_prefix_does_not_hide_a_gate_section(self):
        path = write_tasks("## Stream D — Verification\n- [ ] Run the unittest suite\n")
        self.assertEqual(routing.gate1_executable(routing.scan_tasks(path)), [])

    def test_writing_tests_is_implementation_even_inside_a_verification_stream(self):
        """Measured: substring matching on `verification` deleted four genuine
        test-writing tasks under `Stream 3 — Tests + verification (gate)`."""
        path = write_tasks(
            "## Stream 3 — Tests + verification (gate)\n"
            "- [ ] Extend tests/test_project_memory.py [files: tests/test_project_memory.py]\n"
        )
        kept = routing.gate1_executable(routing.scan_tasks(path))
        self.assertEqual(len(kept), 1, "test-writing work was wrongly excluded")

    def test_an_h1_title_that_mentions_verification_is_not_a_gate_section(self):
        path = write_tasks("# Tasks: Verification And Distribution\n- [ ] Ship it [files: a.py]\n")
        self.assertEqual(len(routing.gate1_executable(routing.scan_tasks(path))), 1)

    def test_an_empty_checkbox_is_not_a_task(self):
        path = write_tasks("## Done\n- [ ]\n- [ ] Real work [files: a.py]\n")
        kept = routing.gate1_executable(routing.scan_tasks(path))
        self.assertEqual([task["text"] for task in kept], ["Real work"])


class TaskIdentity(unittest.TestCase):
    """Ids are positional in the source. Filtering must not renumber them."""

    def test_dropping_a_middle_task_does_not_renumber_the_survivors(self):
        path = write_tasks(
            "- [ ] First [files: a.py]\n"
            "- [x] Middle already done [files: b.py]\n"
            "- [ ] Third [files: c.py] [depends: T01]\n"
        )
        kept = routing.gate1_executable(routing.scan_tasks(path))
        self.assertEqual([task["id"] for task in kept], ["T01", "T03"])
        self.assertEqual(kept[1]["dependencies"], ["T01"])

    def test_a_dependency_on_a_completed_task_is_satisfied(self):
        """Matches shipped `dispatchable_now` (spec §5). The opposite rule would
        make a spec degrade from plannable to refused as its work progresses."""
        result = route(
            "- [x] Groundwork [files: a.py]\n"
            "- [ ] Builds on it [files: b.py] [depends: T01]\n"
        )
        self.assertEqual(result["status"], "ok", result["gaps"])

    def test_a_dependency_on_an_unknown_id_is_a_dangling_dependency(self):
        result = route("- [ ] Builds on nothing [files: b.py] [depends: T09]\n")
        self.assertEqual(result["status"], "needs_plan")
        self.assertEqual(kinds(result), ["dangling_dependency"])
        self.assertIn("T09", result["gaps"][0]["message"])

    def test_a_dependency_on_a_task_deferred_elsewhere_names_the_issue_it_moved_to(self):
        result = route(
            "- [ ] [deferred → 118-other] Moved away [files: a.py]\n"
            "- [ ] Waits on the moved one [files: b.py] [depends: T01]\n"
        )
        self.assertEqual(result["status"], "needs_plan")
        self.assertEqual(kinds(result), ["dangling_dependency"])
        self.assertIn("118-other", result["gaps"][0]["message"])

    def test_the_positive_control_survives_its_predecessor_being_completed(self):
        """029 carries `[depends: T01]` with T01 open today. Checking T01 off
        must not flip the spec from ok to needs_plan (criterion 4)."""
        source = (ROOT / "specs/029-antigravity-artifact-sync-connector/tasks.md").read_text(
            encoding="utf-8"
        )
        progressed = source.replace(
            "- [ ] Implementation: write scripts/antigravity_sync.py",
            "- [x] Implementation: write scripts/antigravity_sync.py",
            1,
        )
        self.assertNotEqual(source, progressed, "fixture no longer matches 029")
        self.assertEqual(route(progressed)["status"], "ok", route(progressed)["gaps"])


class Gate2Boundaries(unittest.TestCase):
    def test_a_task_without_a_boundary_refuses_the_whole_plan(self):
        result = route("- [ ] Commit and push.\n")
        self.assertEqual(result["status"], "needs_plan")
        self.assertEqual(kinds(result), ["no_boundary"])

    def test_a_glob_counts_as_a_boundary(self):
        self.assertEqual(route("- [ ] Keep CLI wrappers compatible [globs: scripts/*]\n")["status"], "ok")

    def test_gate_one_passes_commit_and_push_but_gate_two_rejects_it(self):
        """The two gates compose; neither alone catches this line."""
        scanned = routing.scan_tasks(write_tasks("- [ ] Commit and push.\n"))
        self.assertEqual(len(routing.gate1_executable(scanned)), 1)
        self.assertEqual(routing.build_routing(scanned, ROOT)["status"], "needs_plan")

    def test_one_gap_refuses_every_other_usable_task_with_it(self):
        result = route(
            "- [ ] Usable work [files: scripts/a.py]\n"
            "- [ ] Commit and push.\n"
        )
        self.assertEqual(result["status"], "needs_plan")
        self.assertEqual([gap["task_id"] for gap in result["gaps"]], ["T02"])
        self.assertEqual(result["tasks"], [])
        self.assertEqual(result["written"], [])
        self.assertEqual(result["next_command"], "product:plan")

    def test_a_refused_plan_leaves_no_worker_plan_file_behind(self):
        path = write_tasks("- [ ] Commit and push.\n")
        result = routing.build_routing(routing.scan_tasks(path), path.parent)
        self.assertEqual(result["status"], "needs_plan")
        self.assertEqual(sorted(p.name for p in path.parent.glob("worker-plan.*")), [])

    def test_a_gap_is_addressed_to_the_task_that_caused_it(self):
        result = route("- [ ] Commit and push.\n")
        gap = result["gaps"][0]
        self.assertEqual(gap["task_id"], "T01")
        self.assertIn("T01", gap["message"])

    def test_nothing_executable_is_not_applicable_rather_than_needs_plan(self):
        """A finished spec and an unauthored one are different events (§6.2)."""
        result = route("- [x] All finished [files: a.py]\n")
        self.assertEqual(result["status"], "not_applicable")
        self.assertEqual(result["gaps"], [])
        self.assertEqual(result["next_command"], "product:status")


class UnreadableNotation(unittest.TestCase):
    """Criterion 7: a boundary the parser cannot read is not a missing one."""

    def test_the_pipe_form_is_reported_as_unreadable_notation(self):
        result = routing.build_routing(
            routing.scan_tasks(FIXTURES / "pipe-notation-tasks.md"), ROOT
        )
        self.assertEqual(result["status"], "needs_plan")
        self.assertEqual(kinds(result), ["unreadable_notation"] * 3)

    def test_the_pipe_form_gap_says_the_boundary_was_written_but_not_read(self):
        result = routing.build_routing(
            routing.scan_tasks(FIXTURES / "pipe-notation-tasks.md"), ROOT
        )
        message = result["gaps"][0]["message"]
        self.assertIn("| Files:", message)
        self.assertNotIn("declares no file or glob boundary", message)

    def test_a_task_that_wrote_nothing_at_all_is_no_boundary_not_unreadable(self):
        result = route("- [ ] Commit and push.\n")
        self.assertEqual(kinds(result), ["no_boundary"])

    def test_a_pipe_form_dependency_beside_a_readable_boundary_is_not_a_gap(self):
        """The pipe form is detected to name the boundary gap, never parsed. A
        `| Depends: A1` yields no dependency, so there is nothing to dangle;
        reading it here would bless a second notation the parser does not own."""
        result = route("- [ ] **A1** Do the work [files: scripts/a.py] | Depends: A9\n")
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["gaps"], [])

    def test_the_fixture_keeps_the_authored_form_specs_103_109_110_use(self):
        body = (FIXTURES / "pipe-notation-tasks.md").read_text(encoding="utf-8")
        self.assertIn("| Files: scripts/", body)
        self.assertIn("| Depends: A1", body)
        self.assertNotIn("[files:", body)


class Gate3Routing(unittest.TestCase):
    def test_a_single_task_routes_inline(self):
        self.assertEqual(route("- [ ] One change [files: a.py]\n")["backend"], "inline")

    def test_inline_is_a_success_result_not_a_fallback(self):
        """§6.3: sequential single-file work is done directly by design."""
        result = route("- [ ] One change [files: a.py]\n")
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["gaps"], [])
        self.assertEqual(len(result["tasks"]), 1)
        self.assertEqual(result["next_command"], "product:execute (inline)")

    def test_two_tasks_declaring_the_same_file_route_inline(self):
        result = route(
            "- [ ] Part one [files: scripts/a.py]\n- [ ] Part two [files: scripts/a.py]\n"
        )
        self.assertEqual(result["backend"], "inline")

    def test_shared_state_forces_inline(self):
        result = route(
            "- [ ] Change the shared registry [files: scripts/r.py]\n"
            "- [ ] Unrelated edit [files: scripts/z.py]\n"
        )
        self.assertEqual(result["backend"], "inline")

    def test_a_glob_that_covers_another_task_file_routes_inline(self):
        """Measured on specs/027: `scripts/*` and four named `scripts/` files
        were compared as raw strings and sent to two parallel workers."""
        result = route(
            "- [ ] Normalize the validators [files: scripts/validate_a.py, scripts/doctor.py]\n"
            "- [ ] Keep CLI wrappers compatible [globs: scripts/*]\n"
        )
        self.assertEqual(result["backend"], "inline", result["routing_reason"])
        self.assertIn("scripts/*", result["routing_reason"])

    def test_two_globs_over_different_trees_stay_parallel(self):
        result = route("- [ ] Scripts work [globs: scripts/*]\n- [ ] Docs work [globs: docs/*]\n")
        self.assertEqual(result["backend"], "superpowers-sdd")

    def test_disjoint_independent_tasks_route_to_superpowers_sdd(self):
        result = route(
            "- [ ] Build parser [files: scripts/p.py]\n"
            "- [ ] Build renderer [files: scripts/r2.py]\n"
        )
        self.assertEqual(result["backend"], "superpowers-sdd")
        self.assertEqual(result["status"], "ok")


class ResultContract(unittest.TestCase):
    """Spec §7, asserted on one result of each status."""

    def results(self):
        return {
            "ok": route("- [ ] a [files: x.py]\n"),
            "needs_plan": route("- [ ] Commit and push.\n"),
            "not_applicable": route("- [x] Done [files: x.py]\n"),
        }

    def test_every_result_names_the_versioned_schema(self):
        for status, result in self.results().items():
            self.assertEqual(result["schema"], "moduflow.execution-routing.v1", status)

    def test_every_status_carries_a_routing_reason(self):
        for status, result in self.results().items():
            self.assertTrue(result["routing_reason"].strip(), status)

    def test_no_result_ever_claims_that_moduflow_dispatched_the_work(self):
        for status, result in self.results().items():
            self.assertIs(result["dispatched"], False, status)
            self.assertIsNone(result["executed_by"], status)

    def test_project_root_is_repository_relative_never_absolute(self):
        for status, result in self.results().items():
            self.assertFalse(Path(result["project_root"]).is_absolute(), status)

    def test_only_a_refusal_carries_gaps_and_only_ok_carries_tasks(self):
        results = self.results()
        self.assertEqual(results["ok"]["gaps"], [])
        self.assertEqual(results["not_applicable"]["gaps"], [])
        self.assertTrue(results["needs_plan"]["gaps"])
        self.assertTrue(results["ok"]["tasks"])
        self.assertEqual(results["needs_plan"]["tasks"], [])
        self.assertEqual(results["not_applicable"]["tasks"], [])

    def test_a_refusal_declares_that_nothing_was_written(self):
        for status, result in self.results().items():
            self.assertEqual(result["written"], [], status)

    def test_a_backend_is_named_only_when_the_plan_is_usable(self):
        results = self.results()
        self.assertEqual(results["ok"]["backend"], "inline")
        self.assertIsNone(results["needs_plan"]["backend"])
        self.assertIsNone(results["not_applicable"]["backend"])

    def test_the_whole_result_survives_json(self):
        for status, result in self.results().items():
            self.assertEqual(json.loads(json.dumps(result))["status"], status)


class RealCorpus(unittest.TestCase):
    """Spec §13's required fixtures, read from the checkout itself."""

    def route_spec(self, issue_dir):
        path = ROOT / "specs" / issue_dir / "tasks.md"
        return routing.build_routing(routing.scan_tasks(path), ROOT)

    def test_001_project_migration_is_refused_and_writes_nothing(self):
        result = self.route_spec("001-project-migration")
        self.assertEqual(result["status"], "needs_plan")
        self.assertEqual(result["written"], [])

    def test_023_worker_routing_is_finished_rather_than_broken(self):
        """All six tasks are done. That is not_applicable, not needs_plan."""
        self.assertEqual(self.route_spec("023-worker-routing-and-isolation")["status"], "not_applicable")

    def test_029_is_the_positive_control_and_must_produce_a_usable_plan(self):
        result = self.route_spec("029-antigravity-artifact-sync-connector")
        self.assertEqual(result["status"], "ok", f"positive control rejected: {result['gaps']}")
        self.assertTrue(result["tasks"])
        for task in result["tasks"]:
            self.assertTrue(
                task["expected_files"] or task["expected_globs"],
                "a task reached the plan without a boundary",
            )

    def test_a_deferred_task_carrying_a_boundary_never_becomes_work(self):
        """086 returns not_applicable, so asserting over `tasks` would assert
        over an empty list. Gate 1 is where the deferral is decided."""
        scanned = routing.scan_tasks(
            ROOT / "specs/086-project-aware-production-library-dashboard/tasks.md"
        )
        deferred = [
            task["id"]
            for task in scanned
            if task["status"] == "deferred"
            and (task["expected_files"] or task["expected_globs"])
        ]
        self.assertTrue(deferred, "086 no longer carries a deferred task with a boundary")
        survivors = {task["id"] for task in routing.gate1_executable(scanned)}
        self.assertEqual(survivors & set(deferred), set())

    def test_issue_112_routes_ok_against_its_own_tasks_file(self):
        """The dogfood check `tasks.md:45` requires: gate sections dropped,
        `Stream E — Integration and verification` kept, and T12's five
        dependencies still resolving after the drop.

        Asserted as properties, not as the literal twelve. An earlier version
        pinned the exact list `T01..T12`, which meant checking off finished
        work broke the test — so the file could not say what had actually been
        done. That is the state-disagrees-with-itself defect issues 125, 126
        and 127 all traced back to, reproduced inside its own dogfood.
        """
        result = self.route_spec("112-execution-planner-and-backend-boundary")
        self.assertEqual(result["status"], "ok", result["gaps"])
        self.assertEqual(result["backend"], "inline", result["routing_reason"])

        survivors = {task["id"] for task in result["tasks"]}
        self.assertTrue(survivors, "every task checked off would be not_applicable")

        # The five `## Required Gates` lines carry no `[files:]`, so if Gate 1
        # let them through Gate 2 would refuse the whole plan. Status ok is
        # only reachable when they are dropped.
        gate_ids = {task["id"] for task in routing.scan_tasks(
            ROOT / "specs/112-execution-planner-and-backend-boundary/tasks.md"
        ) if task["section"].strip().lower() == "required gates"}
        self.assertTrue(gate_ids, "the fixture must still carry a gate section")
        self.assertFalse(survivors & gate_ids, "gate lines must not survive Gate 1")

        # T12 depends on T03, T07, T08, T10 and T11. Zero gaps above already
        # proves they all resolve — including any that resolve by being done
        # rather than by surviving, which is the rule spec section 5 settled.
        self.assertEqual(result["gaps"], [])

    def test_no_spec_in_the_corpus_crashes_the_gates(self):
        for tasks_path in sorted(ROOT.glob("specs/*/tasks.md")):
            result = routing.build_routing(routing.scan_tasks(tasks_path), ROOT)
            self.assertIn(result["status"], {"ok", "needs_plan", "not_applicable"})


if __name__ == "__main__":
    unittest.main()
