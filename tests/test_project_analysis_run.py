import importlib.util
import unittest
from pathlib import Path

from tests.analysis_run_fixture import OTHER_ID, RUN_ID, runs_file, valid_run

ROOT = Path(__file__).resolve().parents[1]


def load_module(name, relative_path):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


runs = load_module("project_analysis_run", "scripts/project_analysis_run.py")


def codes(findings):
    return sorted({item["code"] for item in findings})


class AnalysisRunSchemaTest(unittest.TestCase):
    def test_valid_run_has_no_diagnostics(self):
        self.assertEqual(runs.validate_run(valid_run()), [])

    def test_every_required_field_is_required(self):
        for name in runs.FIELDS:
            with self.subTest(field=name):
                entry = valid_run()
                del entry[name]
                self.assertIn("RUN_FIELD_MISSING", codes(runs.validate_run(entry)))

    def test_unknown_field_is_reported(self):
        entry = valid_run()
        entry["extra"] = 1
        self.assertIn("RUN_FIELD_UNKNOWN", codes(runs.validate_run(entry)))

    def test_null_values_need_an_explicit_reason(self):
        cases = (
            ("population", {"definition": "A", "comparison": None, "comparison_reason": ""}),
            (
                "measure",
                {
                    "numerator": "n",
                    "denominator": None,
                    "denominator_reason": "",
                    "unit": "u",
                },
            ),
        )
        for field, value in cases:
            with self.subTest(field=field):
                entry = valid_run(**{field: value})
                self.assertIn("RUN_NULL_WITHOUT_REASON", codes(runs.validate_run(entry)))

    def test_malformed_dates_and_windows_are_rejected(self):
        bad_windows = (
            {"start": "2026-9-1", "end": "2026-09-06", "label": "x", "grain": "week"},
            {"start": "2026-09-30", "end": "2026-09-06", "label": "x", "grain": "week"},
            {"start": "2026-08-31", "end": "2026-09-06", "label": "", "grain": "week"},
        )
        for window in bad_windows:
            with self.subTest(window=window):
                entry = valid_run(time_window=window)
                self.assertIn("RUN_FIELD_INVALID", codes(runs.validate_run(entry)))
        self.assertIn(
            "RUN_FIELD_INVALID", codes(runs.validate_run(valid_run(created_at="today")))
        )

    def test_single_line_fields_are_bounded(self):
        entry = valid_run(title="x" * 241)
        self.assertIn("RUN_FIELD_INVALID", codes(runs.validate_run(entry)))
        entry = valid_run(conclusion="line one\nline two")
        self.assertIn("RUN_FIELD_INVALID", codes(runs.validate_run(entry)))

    def test_id_must_be_a_run_uuid4(self):
        self.assertIn("RUN_FIELD_INVALID", codes(runs.validate_run(valid_run(id="run-1"))))


class AnalysisRunCheckTest(unittest.TestCase):
    def test_required_code_checks_cannot_be_absent(self):
        entry = valid_run(checks=[])
        self.assertIn("CHECK_MISSING", codes(runs.validate_run(entry)))

    def test_profitability_requires_denominator_and_cost_checks(self):
        entry = valid_run(claim_class="profitability", caveats=["synthetic"])
        found = codes(runs.validate_run(entry))
        self.assertIn("CHECK_MISSING", found)

    def test_unexplained_non_applicable_is_rejected(self):
        entry = valid_run(
            checks=[
                {
                    "id": "population-defined",
                    "source": "code",
                    "result": "not_applicable",
                    "reason": "",
                    "evidence_ref": None,
                }
            ]
        )
        self.assertIn("CHECK_UNEXPLAINED", codes(runs.validate_run(entry)))

    def test_a_failing_check_blocks_passed_validation(self):
        entry = valid_run(
            validation_state="passed",
            checks=[
                {
                    "id": "population-defined",
                    "source": "code",
                    "result": "fail",
                    "reason": "population not agreed",
                    "evidence_ref": None,
                }
            ],
        )
        self.assertIn("RUN_VALIDATION_CONTRADICTED", codes(runs.validate_run(entry)))

    def test_unknown_cost_cannot_accompany_a_settled_profit_conclusion(self):
        entry = valid_run(
            claim_class="profitability",
            caveats=["synthetic"],
            decision_state="decided",
            costs={
                "applicable": True,
                "items": [{"name": "delivery", "basis": "per order"}],
                "unknown_items": ["settlement fee"],
                "reason": "",
            },
            checks=[
                {
                    "id": name,
                    "source": "code",
                    "result": "pass",
                    "reason": "",
                    "evidence_ref": "docs/evidence.md",
                }
                for name in (
                    "population-defined",
                    "denominator-stated",
                    "cost-applicability-explicit",
                )
            ],
        )
        self.assertIn("COST_UNKNOWN_NOT_ZERO", codes(runs.validate_run(entry)))

    def test_causal_pass_requires_existing_evidence(self):
        entry = valid_run(
            claim_class="causal",
            caveats=["synthetic"],
            checks=[
                {
                    "id": name,
                    "source": "code",
                    "result": "pass",
                    "reason": "",
                    "evidence_ref": None,
                }
                for name in ("population-defined", "denominator-stated")
            ],
        )
        self.assertIn("CHECK_EVIDENCE_MISSING", codes(runs.validate_run(entry)))


class AnalysisRunStateTest(unittest.TestCase):
    def test_approval_requires_linked_evidence(self):
        entry = valid_run(approval_state="approved")
        self.assertIn("RUN_APPROVAL_EVIDENCE_MISSING", codes(runs.validate_run(entry)))

    def test_unassigned_run_cannot_be_approved(self):
        entry = valid_run(
            issue_id="unassigned",
            approval_state="approved",
            approval_ref="docs/approval.md",
        )
        self.assertIn("RUN_UNASSIGNED_NOT_FINAL", codes(runs.validate_run(entry)))

    def test_waiting_on_maturity_needs_immaturity_or_a_condition(self):
        entry = valid_run(decision_state="waiting_on_maturity")
        self.assertIn("RUN_FIELD_INVALID", codes(runs.validate_run(entry)))
        ok = valid_run(
            decision_state="waiting_on_maturity",
            follow_up={"due_on": "2026-10-07", "condition": "one more closed week", "scheduled": False},
        )
        self.assertEqual(runs.validate_run(ok), [])

    def test_follow_up_can_never_be_scheduled(self):
        entry = valid_run(
            decision_state="waiting_on_maturity",
            follow_up={"due_on": "2026-10-07", "condition": "recheck", "scheduled": True},
        )
        self.assertIn("FOLLOW_UP_NOT_SCHEDULABLE", codes(runs.validate_run(entry)))

    def test_due_follow_up_is_a_read_time_diagnostic_only(self):
        entry = valid_run(
            decision_state="waiting_on_maturity",
            follow_up={"due_on": "2026-09-06", "condition": "recheck", "scheduled": False},
        )
        found = codes(runs.validate_run(entry, today="2026-09-07"))
        self.assertIn("FOLLOW_UP_DUE", found)
        self.assertIn("FOLLOW_UP_INTENT_ONLY", found)
        self.assertEqual(runs.validate_run(entry), [])


class AnalysisRunAmendmentTest(unittest.TestCase):
    def _amend(self, **changes):
        before = valid_run()
        after = valid_run(**changes)
        return before, after

    def test_state_amendment_needs_one_history_entry(self):
        before, after = self._amend(run_state="draft")
        self.assertIn("RUN_AMENDMENT_FORBIDDEN", codes(runs.check_amendment(before, after)))
        after["state_history"] = [
            {
                "field": "run_state",
                "from": "completed",
                "to": "draft",
                "reason": "reopened for a correction",
                "evidence_ref": None,
                "recorded_at": "2026-09-08",
            }
        ]
        self.assertEqual(runs.check_amendment(before, after), [])

    def test_forbidden_field_amendment_is_rejected(self):
        before, after = self._amend(conclusion="A different conclusion entirely.")
        self.assertIn("RUN_AMENDMENT_FORBIDDEN", codes(runs.check_amendment(before, after)))

    def test_history_entries_are_immutable(self):
        before = valid_run(
            state_history=[
                {
                    "field": "run_state",
                    "from": "draft",
                    "to": "completed",
                    "reason": "finished",
                    "evidence_ref": None,
                    "recorded_at": "2026-09-07",
                }
            ]
        )
        after = valid_run(
            state_history=[
                {
                    "field": "run_state",
                    "from": "draft",
                    "to": "completed",
                    "reason": "edited afterwards",
                    "evidence_ref": None,
                    "recorded_at": "2026-09-07",
                }
            ]
        )
        self.assertIn("RUN_AMENDMENT_FORBIDDEN", codes(runs.check_amendment(before, after)))

    def test_history_must_agree_with_the_current_value(self):
        entry = valid_run(
            state_history=[
                {
                    "field": "run_state",
                    "from": "completed",
                    "to": "draft",
                    "reason": "reopened",
                    "evidence_ref": None,
                    "recorded_at": "2026-09-08",
                }
            ]
        )
        self.assertIn("RUN_AMENDMENT_FORBIDDEN", codes(runs.validate_run(entry)))

    def test_issue_id_promotes_only_out_of_unassigned(self):
        before = valid_run(issue_id="unassigned")
        after = valid_run(
            issue_id="001-synthetic-a",
            state_history=[
                {
                    "field": "issue_id",
                    "from": "unassigned",
                    "to": "001-synthetic-a",
                    "reason": "attached to its owning issue",
                    "evidence_ref": None,
                    "recorded_at": "2026-09-08",
                }
            ],
        )
        self.assertEqual(runs.check_amendment(before, after), [])
        second = valid_run(
            issue_id="002-synthetic-b",
            state_history=after["state_history"]
            + [
                {
                    "field": "issue_id",
                    "from": "001-synthetic-a",
                    "to": "002-synthetic-b",
                    "reason": "moved again",
                    "evidence_ref": None,
                    "recorded_at": "2026-09-09",
                }
            ],
        )
        self.assertIn("RUN_AMENDMENT_FORBIDDEN", codes(runs.check_amendment(after, second)))


class AnalysisRunFileTest(unittest.TestCase):
    def test_round_trip_is_stable(self):
        entry = valid_run()
        rendered = runs.render_run_entry(entry)
        parsed = runs.parse_analysis_runs(
            "---\nschema: moduflow.analysis-runs.v1\n---\n\n" + rendered
        )
        self.assertEqual(parsed["entries"], [entry])
        self.assertTrue(parsed["metadata_valid"])

    def test_prose_outside_records_is_ignored_not_lost(self):
        text = runs_file(valid_run()).replace(
            "---\n\n", "---\n\nHuman notes about this project's runs.\n\n", 1
        )
        parsed = runs.parse_analysis_runs(text)
        self.assertEqual(len(parsed["entries"]), 1)

    def test_duplicate_ids_are_rejected(self):
        text = runs_file(valid_run(), valid_run())
        self.assertIn("RUN_ID_DUPLICATE", codes(runs.parse_analysis_runs(text)["diagnostics"]))

    def test_heading_and_object_id_must_agree(self):
        text = runs_file(valid_run()).replace(f"## {RUN_ID}", f"## {OTHER_ID}")
        self.assertIn("RUN_ID_MISMATCH", codes(runs.parse_analysis_runs(text)["diagnostics"]))

    def test_unsupported_schema_and_broken_blocks_are_reported(self):
        self.assertIn(
            "RUNS_SCHEMA_UNSUPPORTED", codes(runs.parse_analysis_runs("# not a run file")["diagnostics"])
        )
        text = runs_file(valid_run()).replace("```json", "```", 1)
        self.assertIn("RUN_BLOCK_INVALID", codes(runs.parse_analysis_runs(text)["diagnostics"]))

    def test_duplicate_json_keys_are_rejected(self):
        text = runs_file(valid_run()).replace(
            '"title":', '"created_at": "2026-09-07",\n  "title":', 1
        )
        self.assertIn("RUN_BLOCK_INVALID", codes(runs.parse_analysis_runs(text)["diagnostics"]))

    def test_rendering_an_invalid_record_raises(self):
        with self.assertRaises(ValueError):
            runs.render_run_entry(valid_run(id="run-1"))


if __name__ == "__main__":
    unittest.main()


class AnalysisRunReadTest(unittest.TestCase):
    def _project(self, tmp, *entries):
        import tempfile as _t
        root = Path(tmp)
        (root / "workspace").mkdir(parents=True, exist_ok=True)
        (root / "playbooks").mkdir(parents=True, exist_ok=True)
        (root / "workspace" / "analysis-runs.md").write_text(
            runs_file(*entries), encoding="utf-8"
        )
        return root

    def test_uninitialized_project_reports_it(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "workspace").mkdir()
            envelope = runs.read_analysis_runs(tmp)
            self.assertEqual(codes(envelope["diagnostics"]), ["RUNS_NOT_INITIALIZED"])
            self.assertEqual(envelope["entries"], [])

    def test_envelope_reports_its_bounds(self):
        import tempfile
        many = []
        for index in range(25):
            suffix = f"{index:012d}"
            many.append(valid_run(id=f"run-22222222-2222-4222-8222-{suffix}"))
        with tempfile.TemporaryDirectory() as tmp:
            self._project(tmp, *many)
            envelope = runs.read_analysis_runs(tmp, limit=20)
            self.assertEqual(envelope["total"], 25)
            self.assertEqual(envelope["returned"], 20)
            self.assertEqual(envelope["omitted"], 5)
            self.assertTrue(envelope["truncated"])
            self.assertEqual(envelope["schema"], runs.READ_SCHEMA)

    def test_states_stay_separate_in_the_envelope(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            self._project(tmp, valid_run())
            entry = runs.read_analysis_runs(tmp)["entries"][0]
            for field in (
                "run_state",
                "validation_state",
                "approval_state",
                "decision_state",
            ):
                self.assertIn(field, entry)
            self.assertEqual(entry["run_state"], "completed")
            self.assertEqual(entry["validation_state"], "unvalidated")
            self.assertTrue(entry["run_anchor"].endswith(RUN_ID))

    def test_query_and_issue_filters_report_reasons(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            self._project(tmp, valid_run())
            hit = runs.read_analysis_runs(tmp, query="weekly usage")
            self.assertEqual(hit["returned"], 1)
            self.assertIn("title", hit["entries"][0]["match_reasons"])
            miss = runs.read_analysis_runs(tmp, query="정책 영향")
            self.assertEqual(miss["returned"], 0)
            other = runs.read_analysis_runs(tmp, issue_id="999-nope")
            self.assertEqual(other["returned"], 0)

    def test_unknown_requested_id_is_explicit(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            self._project(tmp, valid_run())
            envelope = runs.read_analysis_runs(tmp, run_ids=[OTHER_ID])
            self.assertIn("RUN_ID_UNKNOWN", codes(envelope["diagnostics"]))
            self.assertEqual(envelope["returned"], 0)

    def test_invalid_view_and_limit_are_rejected(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            self._project(tmp, valid_run())
            with self.assertRaises(ValueError):
                runs.read_analysis_runs(tmp, view="anything")
            with self.assertRaises(ValueError):
                runs.read_analysis_runs(tmp, limit=0)

    def test_shared_view_needs_a_runner_and_uses_the_resolved_oid(self):
        import tempfile
        from types import SimpleNamespace

        calls = []

        def runner(args, cwd, timeout=None):
            calls.append(args)
            if args[1] == "rev-parse":
                return SimpleNamespace(returncode=0, stdout="a" * 40 + "\n", stderr="")
            return SimpleNamespace(returncode=0, stdout=runs_file(valid_run()), stderr="")

        with tempfile.TemporaryDirectory() as tmp:
            self._project(tmp, valid_run())
            with self.assertRaises(ValueError):
                runs.read_analysis_runs(tmp, view="shared")
            envelope = runs.read_analysis_runs(tmp, view="shared", runner=runner)
            self.assertEqual(envelope["snapshot_commit"], "a" * 40)
            self.assertEqual(envelope["returned"], 1)
            self.assertTrue(any("show" in call for call in calls))


class AnalysisPlaybookResolutionTest(unittest.TestCase):
    def test_unresolvable_name_raises_without_falling_back(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "playbooks").mkdir()
            with self.assertRaises(runs.PlaybookUnresolved):
                runs.resolve_playbook(tmp, "no-such-playbook")

    def test_prefill_reads_the_playbook_not_the_run(self):
        playbook = {
            "id": "pb-weekly-usage",
            "version": "1.0",
            "deliverable_type": "analysis",
            "process_ref": None,
            "required_checks": [
                {"id": "CHK001", "kind": "auto", "text": "section:본문", "rule": {"form": "section", "value": "본문"}, "retired": False},
                {"id": "CHK002", "kind": "review", "text": "확인", "rule": None, "retired": False},
                {"id": "CHK003", "kind": "review", "text": "옛 규칙", "rule": None, "retired": True},
            ],
            "sections": {
                "Reusable Patterns": "- 기본 주장 종류: exploratory\n- 기간을 명시합니다.",
                "Do Not Repeat": "- 단정적 표현을 쓰지 않습니다.",
                "Approved Structures": "- 배경, 결과, 다음 행동.",
            },
        }
        prefill = runs.prefill_run(playbook)
        self.assertEqual(prefill["claim_class"], "exploratory")
        self.assertEqual(prefill["required_code_checks"], ["population-defined"])
        self.assertEqual(prefill["playbook_check_ids"], ["CHK001", "CHK002"])
        self.assertEqual(prefill["auto_check_ids"], ["CHK001"])
        self.assertEqual(prefill["caveats"], ["단정적 표현을 쓰지 않습니다."])
        self.assertEqual(prefill["playbook_ref"]["playbook_id"], "pb-weekly-usage")
