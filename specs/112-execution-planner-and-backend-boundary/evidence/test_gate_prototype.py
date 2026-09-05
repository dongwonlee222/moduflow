"""Failing-first tests for the Issue 112 execution-routing gates.

Runs against the real ModuFlow checkout; no fixtures are copied into the repo
and nothing in the repo is written. Synthetic cases use tmp dirs.

Positive control: specs/029-antigravity-artifact-sync-connector has open tasks
that carry real [files:] boundaries and a [depends: T01]. If the gates reject
that one too, the filter is too aggressive and the design is wrong.
"""
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(REPO))

import gate_prototype as gp
from scripts.worker_orchestrator import parse_tasks as real_parse_tasks


def write_tasks(body):
    tmp = Path(tempfile.mkdtemp())
    (tmp / "tasks.md").write_text(body, encoding="utf-8")
    return tmp / "tasks.md"


class ScanParity(unittest.TestCase):
    """The prototype scan must not drift from the shipped parser."""

    def test_scan_matches_real_parse_tasks_on_every_spec(self):
        checked = 0
        for tasks_path in sorted(REPO.glob("specs/*/tasks.md")):
            try:
                real = real_parse_tasks(tasks_path)
            except ValueError:
                continue
            mine = gp.scan_tasks(tasks_path)
            self.assertEqual(
                [(t["text"], t["status"]) for t in real],
                [(t["text"], t["status"]) for t in mine],
                f"scan diverged from parse_tasks on {tasks_path}",
            )
            checked += 1
        self.assertGreater(checked, 40, "expected to compare against the real corpus")


class Gate1SemanticFilter(unittest.TestCase):
    def test_completed_tasks_are_not_executable(self):
        path = write_tasks("- [x] Add the thing [files: a.py]\n- [ ] Do the other [files: b.py]\n")
        kept = gp.gate1_executable(gp.scan_tasks(path))
        self.assertEqual([t["id"] for t in kept], ["T02"])

    def test_deferred_task_is_not_executable_even_with_files(self):
        path = write_tasks("- [ ] [deferred → 118-other] Implementation: x [files: scripts/a.py]\n")
        self.assertEqual(gp.gate1_executable(gp.scan_tasks(path)), [])

    def test_required_gates_section_is_excluded(self):
        path = write_tasks(
            "## Ready\n- [ ] Build the parser [files: scripts/p.py]\n"
            "## Required Gates\n- [ ] All acceptance criteria have evidence [files: x.md]\n"
        )
        kept = gp.gate1_executable(gp.scan_tasks(path))
        self.assertEqual([t["text"] for t in kept], ["Build the parser"])

    def test_verification_and_converge_sections_are_excluded(self):
        path = write_tasks(
            "## Stream A\n- [ ] Write the adapter [files: scripts/a.py]\n"
            "## Verification\n- [ ] RED to GREEN on tests.test_a\n"
            "## Converge Findings (auto)\n- [ ] CV-1 [high] emits wrong ref\n"
        )
        kept = gp.gate1_executable(gp.scan_tasks(path))
        self.assertEqual([t["text"] for t in kept], ["Write the adapter"])

    def test_unsectioned_tasks_still_pass(self):
        """141 of the corpus checkboxes live under no heading; they must survive."""
        path = write_tasks("- [ ] Implement metadata routing [files: scripts/w.py]\n")
        self.assertEqual(len(gp.gate1_executable(gp.scan_tasks(path))), 1)

    def test_stream_prefixed_gate_section_is_still_excluded(self):
        path = write_tasks("## Stream D — Verification\n- [ ] Run the unittest suite\n")
        self.assertEqual(gp.gate1_executable(gp.scan_tasks(path)), [])

    def test_writing_tests_is_implementation_even_in_a_verification_stream(self):
        """Regression: substring matching on 'verification' swallowed 4 real
        test-writing tasks under 'Stream 3 — Tests + verification (gate)'."""
        path = write_tasks(
            "## Stream 3 — Tests + verification (gate)\n"
            "- [ ] Extend tests/test_project_memory.py [files: tests/test_project_memory.py]\n"
        )
        kept = gp.gate1_executable(gp.scan_tasks(path))
        self.assertEqual(len(kept), 1, "test-writing work was wrongly excluded")

    def test_h1_title_is_not_treated_as_a_gate_section(self):
        path = write_tasks("# Tasks: Verification And Distribution\n- [ ] Ship it [files: a.py]\n")
        self.assertEqual(len(gp.gate1_executable(gp.scan_tasks(path))), 1)

    def test_empty_checkbox_is_ignored(self):
        path = write_tasks("## Done\n- [ ]\n- [ ] Real work [files: a.py]\n")
        kept = gp.gate1_executable(gp.scan_tasks(path))
        self.assertEqual([t["text"] for t in kept], ["Real work"])


class IdentityPreservation(unittest.TestCase):
    """T-ids are positional in the source. Filtering must not renumber them."""

    def test_dropping_a_middle_task_does_not_renumber_survivors(self):
        path = write_tasks(
            "- [ ] First [files: a.py]\n"
            "- [x] Middle already done [files: b.py]\n"
            "- [ ] Third [files: c.py] [depends: T01]\n"
        )
        kept = gp.gate1_executable(gp.scan_tasks(path))
        self.assertEqual([t["id"] for t in kept], ["T01", "T03"])
        self.assertEqual(kept[1]["dependencies"], ["T01"])

    def test_dependency_on_a_completed_task_is_satisfied(self):
        """Matches shipped dispatchable_now (w_o.py:246): a dep is met when the
        predecessor is done. Treating it as a gap would contradict ba1269a and
        make any spec degrade to needs_plan as its work progresses."""
        path = write_tasks(
            "- [x] Groundwork [files: a.py]\n"
            "- [ ] Builds on it [files: b.py] [depends: T01]\n"
        )
        result = gp.build_routing(gp.scan_tasks(path), REPO)
        self.assertEqual(result["status"], "ok", result.get("gaps"))

    def test_dependency_on_an_unknown_id_is_a_gap(self):
        path = write_tasks("- [ ] Builds on nothing [files: b.py] [depends: T09]\n")
        result = gp.build_routing(gp.scan_tasks(path), REPO)
        self.assertEqual(result["status"], "needs_plan")
        self.assertTrue(any("T09" in g for g in result["gaps"]))

    def test_dependency_on_a_deferred_task_is_a_gap(self):
        path = write_tasks(
            "- [ ] [deferred → 118-other] Moved away [files: a.py]\n"
            "- [ ] Waits on the moved one [files: b.py] [depends: T01]\n"
        )
        result = gp.build_routing(gp.scan_tasks(path), REPO)
        self.assertEqual(result["status"], "needs_plan")
        self.assertTrue(any("T01" in g for g in result["gaps"]))

    def test_positive_control_survives_its_predecessor_being_completed(self):
        """029 has [depends: T01] with T01 open today. Checking T01 off must not
        flip the spec from ok to needs_plan."""
        source = (REPO / "specs/029-antigravity-artifact-sync-connector/tasks.md").read_text(
            encoding="utf-8"
        )
        progressed = source.replace(
            "- [ ] Implementation: write scripts/antigravity_sync.py",
            "- [x] Implementation: write scripts/antigravity_sync.py",
            1,
        )
        self.assertNotEqual(source, progressed, "fixture no longer matches 029")
        result = gp.build_routing(gp.scan_tasks(write_tasks(progressed)), REPO)
        self.assertEqual(result["status"], "ok", result.get("gaps"))


class Gate2Boundaries(unittest.TestCase):
    def test_task_without_file_boundary_blocks_the_plan(self):
        path = write_tasks("- [ ] Commit and push.\n")
        result = gp.build_routing(gp.scan_tasks(path), REPO)
        self.assertEqual(result["status"], "needs_plan")

    def test_glob_counts_as_a_boundary(self):
        path = write_tasks("- [ ] Keep CLI wrappers compatible [globs: scripts/*]\n")
        result = gp.build_routing(gp.scan_tasks(path), REPO)
        self.assertEqual(result["status"], "ok")

    def test_gate1_passes_commit_and_push_but_gate2_rejects_it(self):
        """The two gates compose; neither alone catches this line."""
        path = write_tasks("- [ ] Commit and push.\n")
        scanned = gp.scan_tasks(path)
        self.assertEqual(len(gp.gate1_executable(scanned)), 1)
        self.assertEqual(gp.build_routing(scanned, REPO)["status"], "needs_plan")

    def test_nothing_executable_is_not_applicable_not_needs_plan(self):
        path = write_tasks("- [x] All finished [files: a.py]\n")
        self.assertEqual(gp.build_routing(gp.scan_tasks(path), REPO)["status"], "not_applicable")


class Gate3Routing(unittest.TestCase):
    def test_single_task_routes_inline(self):
        path = write_tasks("- [ ] One change [files: a.py]\n")
        result = gp.build_routing(gp.scan_tasks(path), REPO)
        self.assertEqual(result["backend"], "inline")

    def test_overlapping_files_route_inline(self):
        path = write_tasks(
            "- [ ] Part one [files: scripts/a.py]\n- [ ] Part two [files: scripts/a.py]\n"
        )
        self.assertEqual(gp.build_routing(gp.scan_tasks(path), REPO)["backend"], "inline")

    def test_shared_state_routes_inline(self):
        path = write_tasks(
            "- [ ] Change the shared registry [files: scripts/r.py]\n"
            "- [ ] Unrelated edit [files: scripts/z.py]\n"
        )
        self.assertEqual(gp.build_routing(gp.scan_tasks(path), REPO)["backend"], "inline")

    def test_disjoint_independent_tasks_route_to_superpowers_sdd(self):
        path = write_tasks(
            "- [ ] Build parser [files: scripts/p.py]\n"
            "- [ ] Build renderer [files: scripts/r2.py]\n"
        )
        self.assertEqual(
            gp.build_routing(gp.scan_tasks(path), REPO)["backend"], "superpowers-sdd"
        )

    def test_a_glob_that_covers_another_task_file_routes_inline(self):
        """Regression: specs/027 sent `scripts/*` and four named scripts/ files
        to two parallel workers because overlap was compared as raw strings."""
        path = write_tasks(
            "- [ ] Normalize the validators [files: scripts/validate_a.py, scripts/doctor.py]\n"
            "- [ ] Keep CLI wrappers compatible [globs: scripts/*]\n"
        )
        result = gp.build_routing(gp.scan_tasks(path), REPO)
        self.assertEqual(result["backend"], "inline", result["routing_reason"])

    def test_two_globs_over_different_trees_stay_parallel(self):
        path = write_tasks(
            "- [ ] Scripts work [globs: scripts/*]\n- [ ] Docs work [globs: docs/*]\n"
        )
        self.assertEqual(
            gp.build_routing(gp.scan_tasks(path), REPO)["backend"], "superpowers-sdd"
        )

    def test_every_result_carries_a_routing_reason(self):
        for body in ("- [ ] a [files: x.py]\n", "- [ ] a [files: x.py]\n- [ ] b [files: y.py]\n"):
            result = gp.build_routing(gp.scan_tasks(write_tasks(body)), REPO)
            self.assertTrue(result["routing_reason"])


class TruthfulnessAndPaths(unittest.TestCase):
    def test_result_never_claims_dispatch(self):
        path = write_tasks("- [ ] a [files: x.py]\n- [ ] b [files: y.py]\n")
        result = gp.build_routing(gp.scan_tasks(path), REPO)
        self.assertFalse(result["dispatched"])
        self.assertIsNone(result["executed_by"])

    def test_project_root_is_relative_not_absolute(self):
        path = write_tasks("- [ ] a [files: x.py]\n")
        result = gp.build_routing(gp.scan_tasks(path), REPO)
        self.assertFalse(Path(result["project_root"]).is_absolute())

    def test_refusal_declares_that_nothing_was_written(self):
        path = write_tasks("- [ ] Commit and push.\n")
        result = gp.build_routing(gp.scan_tasks(path), REPO)
        self.assertEqual(result["written"], [])
        self.assertEqual(result["next_command"], "product:plan")


class RealCorpus(unittest.TestCase):
    def test_001_project_migration_yields_needs_plan(self):
        path = REPO / "specs/001-project-migration/tasks.md"
        result = gp.build_routing(gp.scan_tasks(path), REPO)
        self.assertEqual(result["status"], "needs_plan")
        self.assertEqual(result["written"], [])

    def test_023_worker_routing_is_finished_not_broken(self):
        """All six tasks are done. That is not_applicable, not needs_plan."""
        path = REPO / "specs/023-worker-routing-and-isolation/tasks.md"
        self.assertEqual(gp.build_routing(gp.scan_tasks(path), REPO)["status"], "not_applicable")

    def test_029_is_the_positive_control_and_must_produce_a_usable_plan(self):
        path = REPO / "specs/029-antigravity-artifact-sync-connector/tasks.md"
        result = gp.build_routing(gp.scan_tasks(path), REPO)
        self.assertEqual(result["status"], "ok", f"positive control rejected: {result.get('gaps')}")
        self.assertTrue(result["tasks"])
        for task in result["tasks"]:
            self.assertTrue(
                task["expected_files"] or task["expected_globs"],
                "a task reached the plan without a boundary",
            )

    def test_086_deferred_task_never_becomes_work(self):
        path = REPO / "specs/086-project-aware-production-library-dashboard/tasks.md"
        result = gp.build_routing(gp.scan_tasks(path), REPO)
        for task in result.get("tasks", []):
            self.assertIsNone(task["deferred_to"])

    def test_no_spec_in_the_corpus_crashes_the_gates(self):
        for tasks_path in sorted(REPO.glob("specs/*/tasks.md")):
            result = gp.build_routing(gp.scan_tasks(tasks_path), REPO)
            self.assertIn(result["status"], {"ok", "needs_plan", "not_applicable"})


if __name__ == "__main__":
    unittest.main(verbosity=2)
