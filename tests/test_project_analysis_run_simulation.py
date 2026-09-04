"""Issue 091 offline simulation matrix: end-to-end scenarios S01-S12/S02b.

Every contract exercised here is already implemented in scripts/project_analysis_run.py
(and the production modules it delegates to) and already unit-tested in
tests/test_project_analysis_run.py and tests/test_project_analysis_run_transaction.py.
This module only assembles those contracts into the scenarios named in
specs/091-reproducible-analysis-runs-and-template-pack/simulation-matrix.md.

Fixture boundary (binding, see the matrix's "Fixture Boundary" section):
  - Everything lives under tempfile.TemporaryDirectory(); the active repository,
    the default checkout and other worktrees are never touched.
  - Synthetic playbooks below carry invented deliverable types, check ids and
    copy blocks only; no company rule text, metric definition, cost amount or
    currency value appears anywhere in this file.
  - Fixed evaluation date is 2026-09-07; a follow-up due_on of 2026-09-06 is
    due and 2026-10-07 is not.
  - All subprocess access flows through an injected runner (mocked here); no
    network, no real external connectors, no installed external skill.
"""

import hashlib
import importlib.util
import re
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts import project_operation as operation
from scripts import project_migrate as migrate

from tests.analysis_run_fixture import OTHER_ID, RUN_ID, runs_file, valid_run
from tests.knowledge_registry_fixture import transaction_project
from tests.test_project_production import VALID_RECORD

ROOT = Path(__file__).resolve().parents[1]


def load_module(name, relative_path):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


runs = load_module("project_analysis_run", "scripts/project_analysis_run.py")

EVAL_DATE = "2026-09-07"
DUE_FOLLOW_UP = "2026-09-06"
NOT_DUE_FOLLOW_UP = "2026-10-07"


def codes(findings):
    return sorted({item["code"] for item in findings})


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def playbook_text(id_, title, canary):
    """A minimal, valid moduflow.playbook.v1 with invented content only."""
    return (
        "---\n"
        "schema: moduflow.playbook.v1\n"
        f"id: {id_}\n"
        "kind: playbook\n"
        f"title: {title}\n"
        "applies_to_types: [analysis]\n"
        "applies_to_channels: [report]\n"
        "audiences: [internal]\n"
        f"retrieval_trigger: synthetic trigger for {id_}\n"
        "process_ref_kind: none\n"
        "process_ref:\n"
        "process_ref_version:\n"
        "process_ref_missing:\n"
        "  - process_ref: synthetic fixture has no external process\n"
        "version: 1.0\n"
        "status: candidate\n"
        "source_records: []\n"
        "review_after: 2027-01-01\n"
        "superseded_by: []\n"
        "created: 2026-09-07\n"
        "updated: 2026-09-07\n"
        "---\n"
        "\n"
        "## Required Checks\n"
        "\n"
        "- CHK001 [auto] section:Summary\n"
        f"- CHK002 [review] {canary} synthetic review item\n"
        "\n"
        "## Reusable Patterns\n"
        "\n"
        "- 기본 주장 종류: exploratory\n"
        f"- {canary} synthetic pattern line\n"
        "\n"
        "## Do Not Repeat\n"
        "\n"
        f"- {canary} synthetic caveat line\n"
        "\n"
        "## Approved Copy Blocks\n"
        "\n"
        f"- {canary} synthetic approved copy block\n"
        "\n"
        "## Approved Structures\n"
        "\n"
        f"- {canary} synthetic structure reference\n"
        "\n"
        "## Evidence\n"
        "\n"
        "- synthetic\n"
        "\n"
        "## Revision History\n"
        "\n"
        "- 2026-09-07 synthetic fixture created\n"
    )


def profitability_checks(evidence="docs/synthetic-evidence.md"):
    return [
        {"id": name, "source": "code", "result": "pass", "reason": "", "evidence_ref": evidence}
        for name in runs.CODE_CHECKS["profitability"]
    ]


def causal_checks(evidence="docs/synthetic-evidence.md"):
    return [
        {"id": name, "source": "code", "result": "pass", "reason": "", "evidence_ref": evidence}
        for name in runs.CODE_CHECKS["causal"]
    ]


def _project(tmp, *entries):
    """A fully scaffolded synthetic project with its run file pre-seeded."""
    project = transaction_project(tmp)
    workspace = project.context["relative_paths"]["workspace"]
    project.write(workspace + "/analysis-runs.md", runs_file(*entries))
    return project


class S01InitializationSimulation(unittest.TestCase):
    """S01: run-file initialization is non-destructive.

    There is no dedicated "init" entry point on scripts/project_analysis_run.py's
    public API; workspace/analysis-runs.md is a missing-only workspace template
    (templates/workspace/analysis-runs.md, tracked in scripts/validate_moduflow.py's
    inventory) written through the already-tested missing-only writer
    scripts/project_migrate.write_text_if_missing. "Preview" below is therefore the
    read-only facade (read_analysis_runs, which never writes) and "apply" is that
    missing-only writer, exercised twice to prove idempotence.
    """

    def test_run_file_initialization_is_non_destructive(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = transaction_project(tmp)
            workspace = project.context["relative_paths"]["workspace"]
            target = Path(project.root) / workspace / "analysis-runs.md"
            self.assertFalse(target.exists())

            other_files = {
                name: (Path(project.root) / workspace / name).read_bytes()
                for name in ("dashboard.md", "roadmap.md", "loop-state.json")
            }
            state_before = (Path(project.root) / ".moduflow" / "state.json").read_bytes()

            # Preview: read-only, creates nothing.
            envelope = runs.read_analysis_runs(project.root, project_context=project.context)
            self.assertEqual(codes(envelope["diagnostics"]), ["RUNS_NOT_INITIALIZED"])
            self.assertFalse(target.exists())

            template = (ROOT / "templates" / "workspace" / "analysis-runs.md").read_text(
                encoding="utf-8"
            )

            # Apply: missing-only init creates the run file with the right schema.
            created = migrate.write_text_if_missing(target, template)
            self.assertTrue(created)
            self.assertTrue(target.exists())
            parsed = runs.parse_analysis_runs(target.read_text(encoding="utf-8"))
            self.assertEqual(parsed["schema"], runs.SCHEMA)
            self.assertTrue(parsed["metadata_valid"])
            self.assertEqual(parsed["entries"], [])
            first_hash = sha256(target)

            # Apply again: missing-only means the second apply changes zero bytes.
            created_again = migrate.write_text_if_missing(target, template)
            self.assertFalse(created_again)
            self.assertEqual(sha256(target), first_hash)

            # Existing files are untouched by any of the above.
            for name, before in other_files.items():
                self.assertEqual((Path(project.root) / workspace / name).read_bytes(), before)
            self.assertEqual(
                (Path(project.root) / ".moduflow" / "state.json").read_bytes(), state_before
            )


class S02AppendOnlyHistorySimulation(unittest.TestCase):
    def test_append_only_history_explains_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            run1 = valid_run()
            project = _project(tmp, run1)
            workspace = project.context["relative_paths"]["workspace"]
            runs_path = Path(project.root) / workspace / "analysis-runs.md"

            run2 = valid_run(
                id=OTHER_ID,
                title="Synthetic A weekly usage, week 36 corrected",
                conclusion="Corrected: synthetic A usage was flat, not rising, in week 36.",
                supersedes=RUN_ID,
                change_reason="the original run misread the aggregation window",
            )
            plan2 = runs.plan_analysis_run_append(
                project.root, run2, project_context=project.context
            )
            result2 = runs.apply_analysis_run_append(
                project.root, plan2, project_context=project.context
            )
            self.assertEqual(result2["status"], "applied", result2)
            after_run2_hash = sha256(runs_path)

            parsed = runs.parse_analysis_runs(runs_path.read_text(encoding="utf-8"))
            stored1 = next(e for e in parsed["entries"] if e["id"] == RUN_ID)
            stored2 = next(e for e in parsed["entries"] if e["id"] == OTHER_ID)
            # Run 1's analysis fields are unchanged.
            self.assertEqual(stored1, run1)
            # Run 2 names its predecessor and the reason for superseding it.
            self.assertEqual(stored2["supersedes"], RUN_ID)
            self.assertEqual(
                stored2["change_reason"], "the original run misread the aggregation window"
            )

            # An in-place edit of run 1's analysis fields returns RUN_AMENDMENT_FORBIDDEN.
            edited_run1 = valid_run(conclusion="Silently rewritten conclusion.")
            self.assertIn(
                "RUN_AMENDMENT_FORBIDDEN", codes(runs.check_amendment(run1, edited_run1))
            )
            with self.assertRaises(Exception) as ctx:
                runs.plan_analysis_run_append(
                    project.root, edited_run1, project_context=project.context, amend=True
                )
            self.assertEqual(
                getattr(ctx.exception, "code", None), "PLAN_RUN_AMENDMENT_FORBIDDEN"
            )
            self.assertEqual(sha256(runs_path), after_run2_hash)

            # A no-op append (identical replay of run 1) is byte-identical.
            plan_replay = runs.plan_analysis_run_append(
                project.root, run1, project_context=project.context
            )
            result_replay = runs.apply_analysis_run_append(
                project.root, plan_replay, project_context=project.context
            )
            self.assertIn(result_replay["status"], ("applied", "noop"))
            self.assertEqual(sha256(runs_path), after_run2_hash)


class S02bStateAmendmentSimulation(unittest.TestCase):
    def test_state_amendment_appends_history(self):
        run0 = valid_run(
            decision_state="waiting_on_maturity",
            maturity={
                "status": "immature",
                "observation_until": "2026-10-01",
                "reason": "the observation window is still open",
            },
        )
        self.assertEqual(runs.validate_run(run0), [])

        run1 = valid_run(
            **{**{k: v for k, v in run0.items() if k not in ("validation_state", "state_history")}},
            validation_state="passed",
            state_history=[
                {
                    "field": "validation_state",
                    "from": "unvalidated",
                    "to": "passed",
                    "reason": "synthetic validation evidence reviewed",
                    "evidence_ref": "docs/synthetic-validation-evidence.md",
                    "recorded_at": "2026-09-08",
                }
            ],
        )
        self.assertEqual(runs.check_amendment(run0, run1), [])
        self.assertEqual(len(run1["state_history"]), 1)

        # Both approval_state and approval_ref changed, so both amendable fields
        # need their own history entry (check_amendment requires one entry per
        # changed amendable field, not one entry per amendment "event").
        run2 = valid_run(
            **{**{k: v for k, v in run1.items() if k not in ("approval_state", "approval_ref", "state_history")}},
            approval_state="approved",
            approval_ref="docs/synthetic-approval.md",
            state_history=run1["state_history"]
            + [
                {
                    "field": "approval_state",
                    "from": "unapproved",
                    "to": "approved",
                    "reason": "synthetic approval evidence reviewed",
                    "evidence_ref": "docs/synthetic-approval-evidence.md",
                    "recorded_at": "2026-09-09",
                },
                {
                    "field": "approval_ref",
                    "from": None,
                    "to": "docs/synthetic-approval.md",
                    "reason": "recording the approval evidence location",
                    "evidence_ref": None,
                    "recorded_at": "2026-09-09",
                },
            ],
        )
        self.assertEqual(runs.check_amendment(run1, run2), [])
        self.assertEqual(len(run2["state_history"]), 3)

        run3 = valid_run(
            **{**{k: v for k, v in run2.items() if k not in ("decision_state", "state_history")}},
            decision_state="decided",
            state_history=run2["state_history"]
            + [
                {
                    "field": "decision_state",
                    "from": "waiting_on_maturity",
                    "to": "decided",
                    "reason": "the maturity condition was later satisfied",
                    "evidence_ref": None,
                    "recorded_at": "2026-09-10",
                }
            ],
        )
        self.assertEqual(runs.check_amendment(run2, run3), [])
        self.assertEqual(len(run3["state_history"]), 4)

        # No analysis field changed across the whole chain.
        for field in ("conclusion", "measure", "population", "claim_class", "time_window"):
            self.assertEqual(run0[field], run3[field])

        # Editing an existing history entry is forbidden.
        edited_history = list(run3["state_history"])
        edited_history[0] = {**edited_history[0], "reason": "a rewritten reason"}
        tampered_edit = {**run3, "state_history": edited_history}
        self.assertIn(
            "RUN_AMENDMENT_FORBIDDEN", codes(runs.check_amendment(run2, tampered_edit))
        )

        # Dropping a history entry is forbidden.
        dropped_history = [
            item for index, item in enumerate(run3["state_history"]) if index != 2
        ]
        tampered_drop = {**run3, "state_history": dropped_history}
        self.assertIn(
            "RUN_AMENDMENT_FORBIDDEN", codes(runs.check_amendment(run2, tampered_drop))
        )

        # A history entry that disagrees with the field it claims to set is forbidden.
        desync_history = list(run2["state_history"]) + [
            {
                "field": "decision_state",
                "from": "waiting_on_maturity",
                "to": "decided",
                "reason": "history says decided",
                "evidence_ref": None,
                "recorded_at": "2026-09-10",
            }
        ]
        tampered_desync = {**run2, "decision_state": "waiting_on_maturity", "state_history": desync_history}
        self.assertIn(
            "RUN_AMENDMENT_FORBIDDEN", codes(runs.validate_run(tampered_desync))
        )


class S03PlaybookResolutionSimulation(unittest.TestCase):
    def test_playbook_resolution_prefers_project(self):
        default_monthly = runs.default_playbook_dir() / "monthly-trend.md"
        default_policy = runs.default_playbook_dir() / "policy-impact.md"
        before_monthly = default_monthly.read_bytes()
        before_policy = default_policy.read_bytes()

        with tempfile.TemporaryDirectory() as tmp:
            root_a = Path(tmp) / "a"
            root_b = Path(tmp) / "b"
            root_a.mkdir()
            root_b.mkdir()
            project_a = transaction_project(root_a)
            project_b = transaction_project(root_b, nested=True)
            project_b.context["project_id"] = "synthetic-b"

            project_a.write(
                project_a.context["relative_paths"]["playbooks"] + "/pb-monthly-trend.md",
                playbook_text("pb-monthly-trend", "Synthetic A monthly cadence review", "CANARY-CADENCE-A-091"),
            )
            project_a.write(
                project_a.context["relative_paths"]["playbooks"] + "/pb-team-canary-review.md",
                playbook_text("pb-team-canary-review", "Synthetic A canary-only playbook", "CANARY-ONLY-A-091"),
            )
            project_b.write(
                project_b.context["relative_paths"]["playbooks"] + "/pb-monthly-trend.md",
                playbook_text("pb-monthly-trend", "Synthetic B monthly cadence review", "CANARY-CADENCE-B-091"),
            )

            # Same name in the default pack and in both projects: project wins.
            resolved_a = runs.resolve_playbook(
                project_a.root, "monthly-trend", project_context=project_a.context
            )
            self.assertEqual(resolved_a["source"], "project")
            self.assertIn("overrides the default", resolved_a["reason"])
            self.assertIn(
                "CANARY-CADENCE-A-091", resolved_a["playbook"]["sections"]["Do Not Repeat"]
            )

            resolved_b = runs.resolve_playbook(
                project_b.root, "monthly-trend", project_context=project_b.context
            )
            self.assertEqual(resolved_b["source"], "project")
            self.assertIn(
                "CANARY-CADENCE-B-091", resolved_b["playbook"]["sections"]["Do Not Repeat"]
            )
            self.assertNotEqual(
                resolved_a["playbook"]["sections"]["Do Not Repeat"],
                resolved_b["playbook"]["sections"]["Do Not Repeat"],
            )

            # A project-only name resolves from the project.
            project_only = runs.resolve_playbook(
                project_a.root, "team-canary-review", project_context=project_a.context
            )
            self.assertEqual(project_only["source"], "project")

            # A default-only name resolves from the default pack.
            default_only = runs.resolve_playbook(
                project_a.root, "policy-impact", project_context=project_a.context
            )
            self.assertEqual(default_only["source"], "default")
            self.assertIn("using the read-only default", default_only["reason"])

            # A name in neither raises without any silent fallback.
            with self.assertRaises(runs.PlaybookUnresolved):
                runs.resolve_playbook(
                    project_a.root, "no-such-playbook-091", project_context=project_a.context
                )

            # A run sharing the same UUID in both projects proves (project_id, run_id) scoping:
            # resolving RUN_ID is bound to (root, project_context), not globally ambiguous.
            project_a.write(
                project_a.context["relative_paths"]["workspace"] + "/analysis-runs.md",
                runs_file(
                    valid_run(
                        title="Synthetic A run sharing an id with B",
                        conclusion="CANARY-A-SCOPE-091 synthetic conclusion.",
                    )
                ),
            )
            project_b.write(
                project_b.context["relative_paths"]["workspace"] + "/analysis-runs.md",
                runs_file(
                    valid_run(
                        title="Synthetic B run sharing an id with A",
                        conclusion="CANARY-B-SCOPE-091 synthetic conclusion.",
                    )
                ),
            )
            envelope_a = runs.read_analysis_runs(project_a.root, project_context=project_a.context)
            envelope_b = runs.read_analysis_runs(project_b.root, project_context=project_b.context)
            self.assertEqual(envelope_a["entries"][0]["id"], RUN_ID)
            self.assertEqual(envelope_b["entries"][0]["id"], RUN_ID)
            self.assertNotEqual(
                envelope_a["entries"][0]["conclusion"], envelope_b["entries"][0]["conclusion"]
            )

        # Defaults are never edited in place.
        self.assertEqual(default_monthly.read_bytes(), before_monthly)
        self.assertEqual(default_policy.read_bytes(), before_policy)


class S04SecondRunNeedsOnlyWindowSimulation(unittest.TestCase):
    """S04: the decisive scenario for the issue's purpose.

    NOTE on scope: scripts/project_analysis_run.prefill_run is the only implemented
    R7 prefill mechanism. Its returned fields are playbook_ref, claim_class,
    required_code_checks, playbook_check_ids, auto_check_ids, caveats, structure_ref
    and process_ref. It does not derive measure.unit (the spec, spec.md:273/330,
    describes measure.unit as part of prefill, but the shipped prefill_run has no
    such field). Per this task's instruction to write tests against the delivered
    contract rather than change production code, this test asserts every field
    prefill_run actually derives (claim class, required code checks / checks
    skeleton, caveats, structure reference, pinned playbook_ref) is identical
    across two independent prefill_run calls against the same resolved playbook,
    and that only the caller-supplied time_window differs between the two runs.
    measure.unit is not separately asserted as playbook-derived, since no code
    path derives it; it is not skipped either, since the rest of the scenario is
    fully exercisable without a production change.
    """

    def test_second_run_needs_only_the_window(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = transaction_project(tmp)
            project.write(
                project.context["relative_paths"]["playbooks"] + "/pb-weekly-cadence-091.md",
                playbook_text(
                    "pb-weekly-cadence-091", "Synthetic weekly cadence playbook", "CANARY-WEEKLY-091"
                ),
            )
            resolved = runs.resolve_playbook(
                project.root, "weekly-cadence-091", project_context=project.context
            )
            self.assertEqual(resolved["source"], "project")
            playbook = resolved["playbook"]

            prefill1 = runs.prefill_run(playbook)
            run1 = valid_run(
                playbook_ref=prefill1["playbook_ref"],
                claim_class=prefill1["claim_class"],
                caveats=prefill1["caveats"],
                time_window={
                    "start": "2026-08-31",
                    "end": "2026-09-06",
                    "label": "week 36",
                    "grain": "week",
                },
                checks=[
                    {"id": cid, "source": "code", "result": "pass", "reason": "", "evidence_ref": None}
                    for cid in prefill1["required_code_checks"]
                ],
            )
            self.assertEqual(runs.validate_run(run1), [])

            # The second run supplies only the new time window.
            prefill2 = runs.prefill_run(playbook)
            self.assertEqual(prefill2, prefill1)  # nothing about the playbook restated differently

            run2 = valid_run(
                id=OTHER_ID,
                playbook_ref=prefill2["playbook_ref"],
                claim_class=prefill2["claim_class"],
                caveats=prefill2["caveats"],
                time_window={
                    "start": "2026-09-07",
                    "end": "2026-09-13",
                    "label": "week 37",
                    "grain": "week",
                },
                checks=[
                    {"id": cid, "source": "code", "result": "pass", "reason": "", "evidence_ref": None}
                    for cid in prefill2["required_code_checks"]
                ],
            )
            self.assertEqual(runs.validate_run(run2), [])

            # Claim class, checks skeleton, caveats and the pinned playbook came from the
            # playbook on both runs without being restated.
            self.assertEqual(run1["playbook_ref"], run2["playbook_ref"])
            self.assertEqual(run1["claim_class"], run2["claim_class"])
            self.assertEqual(run1["caveats"], run2["caveats"])
            self.assertEqual(
                sorted(c["id"] for c in run1["checks"]), sorted(c["id"] for c in run2["checks"])
            )
            # Only the caller-supplied window changed.
            self.assertNotEqual(run1["time_window"], run2["time_window"])


class S05CodeChecksSimulation(unittest.TestCase):
    def test_code_checks_cannot_be_skipped(self):
        absent = valid_run(checks=[])
        self.assertIn("CHECK_MISSING", codes(runs.validate_run(absent)))

        present_passing = valid_run(
            checks=[
                {"id": "population-defined", "source": "code", "result": "pass", "reason": "", "evidence_ref": None}
            ]
        )
        self.assertEqual(runs.validate_run(present_passing), [])

        na_with_reason = valid_run(
            checks=[
                {
                    "id": "population-defined",
                    "source": "code",
                    "result": "not_applicable",
                    "reason": "synthetic: population is fixed by design in this fixture",
                    "evidence_ref": None,
                }
            ]
        )
        self.assertEqual(runs.validate_run(na_with_reason), [])

        na_without_reason = valid_run(
            checks=[
                {"id": "population-defined", "source": "code", "result": "not_applicable", "reason": "", "evidence_ref": None}
            ]
        )
        self.assertIn("CHECK_UNEXPLAINED", codes(runs.validate_run(na_without_reason)))

        profit_missing_one = valid_run(
            claim_class="profitability",
            caveats=["synthetic"],
            checks=[
                {"id": "population-defined", "source": "code", "result": "pass", "reason": "", "evidence_ref": "docs/e.md"}
            ],
        )
        self.assertIn("CHECK_MISSING", codes(runs.validate_run(profit_missing_one)))

        profit_all_present = valid_run(
            claim_class="profitability", caveats=["synthetic"], checks=profitability_checks()
        )
        self.assertEqual(runs.validate_run(profit_all_present), [])

        causal_pass_no_evidence = valid_run(
            claim_class="causal",
            caveats=["synthetic"],
            checks=[
                {"id": name, "source": "code", "result": "pass", "reason": "", "evidence_ref": None}
                for name in runs.CODE_CHECKS["causal"]
            ],
        )
        self.assertIn("CHECK_EVIDENCE_MISSING", codes(runs.validate_run(causal_pass_no_evidence)))

        causal_pass_with_evidence = valid_run(
            claim_class="causal", caveats=["synthetic"], checks=causal_checks()
        )
        self.assertEqual(runs.validate_run(causal_pass_with_evidence), [])

        any_failure_blocks_passed = valid_run(
            validation_state="passed",
            checks=[
                {
                    "id": "population-defined",
                    "source": "code",
                    "result": "fail",
                    "reason": "synthetic failure reason",
                    "evidence_ref": None,
                }
            ],
        )
        self.assertIn(
            "RUN_VALIDATION_CONTRADICTED", codes(runs.validate_run(any_failure_blocks_passed))
        )


class S06UnknownCostSimulation(unittest.TestCase):
    def test_unknown_cost_is_never_zero(self):
        unresolved = valid_run(
            claim_class="profitability",
            caveats=["synthetic"],
            decision_state="decided",
            costs={
                "applicable": True,
                "items": [{"name": "synthetic delivery", "basis": "per synthetic order"}],
                "unknown_items": ["synthetic settlement fee", "synthetic refund adjustment"],
                "reason": "",
            },
            checks=profitability_checks(),
        )
        self.assertIn("COST_UNKNOWN_NOT_ZERO", codes(runs.validate_run(unresolved)))
        # An unknown cost item is a name, never a numeric value defaulted to 0.
        self.assertTrue(all(isinstance(item, str) for item in unresolved["costs"]["unknown_items"]))
        self.assertEqual(
            set(unresolved["costs"]), {"applicable", "items", "unknown_items", "reason"}
        )  # the schema carries no total/amount field an unknown could be defaulted into

        resolved = valid_run(
            claim_class="profitability",
            caveats=["synthetic"],
            decision_state="decided",
            costs={
                "applicable": True,
                "items": [{"name": "synthetic delivery", "basis": "per synthetic order"}],
                "unknown_items": [],
                "reason": "",
            },
            checks=profitability_checks(),
        )
        self.assertEqual(runs.validate_run(resolved), [])

        not_applicable = valid_run(
            claim_class="profitability",
            caveats=["synthetic"],
            decision_state="decided",
            costs={
                "applicable": False,
                "items": [],
                "unknown_items": [],
                "reason": "synthetic: cost is not applicable to this question",
            },
            checks=profitability_checks(),
        )
        self.assertEqual(runs.validate_run(not_applicable), [])


class S07OneClaimPerRunSimulation(unittest.TestCase):
    def test_one_claim_per_run(self):
        combined = valid_run(claim_class="exploratory+profitability")
        findings = runs.validate_run(combined)
        self.assertTrue(
            any(f["code"] == "RUN_FIELD_INVALID" and f["field"] == "claim_class" for f in findings)
        )

        trend = valid_run(
            id=RUN_ID,
            claim_class="exploratory",
            conclusion="Synthetic A usage trended upward across the window.",
            decision_refs=[OTHER_ID],
        )
        margin = valid_run(
            id=OTHER_ID,
            claim_class="profitability",
            caveats=["synthetic"],
            conclusion="Synthetic A per-order margin held steady across the window.",
            costs={
                "applicable": True,
                "items": [{"name": "synthetic delivery", "basis": "per synthetic order"}],
                "unknown_items": [],
                "reason": "",
            },
            checks=profitability_checks(),
            decision_refs=[RUN_ID],
        )
        self.assertEqual(runs.validate_run(trend), [])
        self.assertEqual(runs.validate_run(margin), [])
        self.assertIn(OTHER_ID, trend["decision_refs"])
        self.assertIn(RUN_ID, margin["decision_refs"])
        # The author's prose is exactly what was authored, never rewritten.
        self.assertEqual(
            trend["conclusion"], "Synthetic A usage trended upward across the window."
        )
        self.assertEqual(
            margin["conclusion"], "Synthetic A per-order margin held steady across the window."
        )


class S08FourStatesIndependenceSimulation(unittest.TestCase):
    def test_four_states_stay_independent(self):
        # No state implies another: an unfinished run can carry a passed validation.
        draft_but_validated = valid_run(run_state="draft", validation_state="passed")
        self.assertEqual(runs.validate_run(draft_but_validated), [])

        # Approval without existing evidence is rejected.
        no_evidence = valid_run(approval_state="approved")
        self.assertIn("RUN_APPROVAL_EVIDENCE_MISSING", codes(runs.validate_run(no_evidence)))

        # No writer invents approval_ref: round-tripping a caller-supplied ref through
        # render/parse returns exactly that value, never a placeholder.
        approved = valid_run(approval_state="approved", approval_ref="docs/synthetic-approval.md")
        self.assertEqual(runs.validate_run(approved), [])
        rendered = runs.render_run_entry(approved)
        reparsed = runs.parse_analysis_runs(
            "---\nschema: moduflow.analysis-runs.v1\n---\n\n" + rendered
        )
        self.assertEqual(reparsed["entries"][0]["approval_ref"], "docs/synthetic-approval.md")

        # waiting_on_maturity requires immature maturity or a follow-up condition.
        bare_waiting = valid_run(decision_state="waiting_on_maturity")
        self.assertIn("RUN_FIELD_INVALID", codes(runs.validate_run(bare_waiting)))

        immature_waiting = valid_run(
            decision_state="waiting_on_maturity",
            maturity={
                "status": "immature",
                "observation_until": "2026-10-01",
                "reason": "the observation window is still open",
            },
        )
        self.assertEqual(runs.validate_run(immature_waiting), [])

        conditioned_waiting = valid_run(
            decision_state="waiting_on_maturity",
            follow_up={
                "due_on": NOT_DUE_FOLLOW_UP,
                "condition": "one more closed week of synthetic data",
                "scheduled": False,
            },
        )
        self.assertEqual(runs.validate_run(conditioned_waiting), [])

        # No read collapses two states: all four fields stay individually addressable.
        with tempfile.TemporaryDirectory() as tmp:
            entry = valid_run(
                run_state="draft",
                validation_state="passed",
                approval_state="approved",
                approval_ref="docs/synthetic-approval.md",
                decision_state="waiting_on_maturity",
                maturity={
                    "status": "immature",
                    "observation_until": "2026-10-01",
                    "reason": "the observation window is still open",
                },
            )
            project = _project(tmp, entry)
            envelope = runs.read_analysis_runs(project.root, project_context=project.context)
            got = envelope["entries"][0]
            self.assertEqual(got["run_state"], "draft")
            self.assertEqual(got["validation_state"], "passed")
            self.assertEqual(got["approval_state"], "approved")
            self.assertEqual(got["decision_state"], "waiting_on_maturity")


class S09UnassignedHoldingStateSimulation(unittest.TestCase):
    def test_unassigned_run_is_a_holding_state(self):
        unassigned_complete = valid_run(issue_id="unassigned")
        self.assertEqual(runs.validate_run(unassigned_complete), [])

        unassigned_validated = valid_run(issue_id="unassigned", validation_state="passed")
        self.assertEqual(runs.validate_run(unassigned_validated), [])

        # Approval / final-result on an unassigned run is refused.
        unassigned_approval_attempt = valid_run(
            issue_id="unassigned", approval_state="approved", approval_ref="docs/synthetic-approval.md"
        )
        self.assertIn(
            "RUN_UNASSIGNED_NOT_FINAL", codes(runs.validate_run(unassigned_approval_attempt))
        )

        with tempfile.TemporaryDirectory() as tmp:
            project = _project(tmp, valid_run(issue_id="unassigned"))
            workspace = project.context["relative_paths"]["workspace"]
            issues = project.context["relative_paths"]["issues"]
            project.write(
                issues + "/002-synthetic-b.md",
                "# Issue: `002-synthetic-b`\n\n**Status: backlog** — created 2026-09-07.\n"
                "**Priority: p2**\n\n## Notes\n\nSynthetic promotion target.\n",
            )

            promoted = valid_run(
                issue_id="002-synthetic-b",
                state_history=[
                    {
                        "field": "issue_id",
                        "from": "unassigned",
                        "to": "002-synthetic-b",
                        "reason": "promoted to its owning issue",
                        "evidence_ref": None,
                        "recorded_at": "2026-09-08",
                    }
                ],
            )
            plan = runs.plan_analysis_run_append(
                project.root, promoted, project_context=project.context, amend=True
            )
            result = runs.apply_analysis_run_append(
                project.root, plan, project_context=project.context
            )
            self.assertEqual(result["status"], "applied", result)

            # Promotion appends one history entry and one backlink.
            issue_text = (Path(project.root) / issues / "002-synthetic-b.md").read_text(
                encoding="utf-8"
            )
            backlinks = [line for line in issue_text.splitlines() if RUN_ID in line]
            self.assertEqual(len(backlinks), 1, backlinks)
            parsed = runs.parse_analysis_runs(
                (Path(project.root) / workspace / "analysis-runs.md").read_text(encoding="utf-8")
            )
            self.assertEqual(len(parsed["entries"][0]["state_history"]), 1)

            # A second promotion is rejected.
            second_promotion = valid_run(
                issue_id="003-synthetic-c",
                state_history=promoted["state_history"]
                + [
                    {
                        "field": "issue_id",
                        "from": "002-synthetic-b",
                        "to": "003-synthetic-c",
                        "reason": "moved again",
                        "evidence_ref": None,
                        "recorded_at": "2026-09-09",
                    }
                ],
            )
            with self.assertRaises(Exception):
                runs.plan_analysis_run_append(
                    project.root, second_promotion, project_context=project.context, amend=True
                )

        # An unbound-identity context emits no cross-project reference.
        with tempfile.TemporaryDirectory() as tmp2:
            root = Path(tmp2)
            (root / "workspace").mkdir()
            (root / "playbooks").mkdir()
            entry = valid_run(
                sources=[
                    {
                        "project_id": "synthetic-b",
                        "artifact_id": "art-11111111-1111-4111-8111-111111111111",
                        "snapshot_commit": "b" * 40,
                        "locator": "knowledge/references/population.md",
                        "recorded_state": "draft",
                        "tab_or_range": "sheet1!A1:D200",
                        "extracted_at": "2026-09-07",
                        "content_hash": None,
                    }
                ]
            )
            (root / "workspace" / "analysis-runs.md").write_text(
                runs_file(entry), encoding="utf-8"
            )
            found = runs.resolve_run_sources(tmp2, RUN_ID)
            self.assertIn("SOURCE_IDENTITY_UNVERIFIED", codes(found["diagnostics"]))
            self.assertEqual(found["sources"], [])


class S10ImmatureFollowUpSimulation(unittest.TestCase):
    def test_immature_window_and_follow_up_are_not_a_schedule(self):
        due_entry = valid_run(
            maturity={
                "status": "immature",
                "observation_until": NOT_DUE_FOLLOW_UP,
                "reason": "the policy change was observed only days ago",
            },
            decision_state="waiting_on_maturity",
            follow_up={
                "due_on": DUE_FOLLOW_UP,
                "condition": "recheck after one more closed week",
                "scheduled": False,
            },
        )
        self.assertEqual(codes(runs.validate_run(due_entry)), [])
        maturity_findings = {f["code"]: f for f in runs.validate_run(due_entry)}
        self.assertEqual(maturity_findings, {})

        due_at_eval_date = runs.validate_run(due_entry, today=EVAL_DATE)
        self.assertIn("FOLLOW_UP_DUE", codes(due_at_eval_date))
        self.assertIn("FOLLOW_UP_INTENT_ONLY", codes(due_at_eval_date))
        severities = {f["code"]: f["severity"] for f in due_at_eval_date}
        self.assertEqual(severities["FOLLOW_UP_DUE"], "warning")
        self.assertEqual(severities["FOLLOW_UP_INTENT_ONLY"], "info")

        not_due_entry = valid_run(
            maturity={
                "status": "immature",
                "observation_until": NOT_DUE_FOLLOW_UP,
                "reason": "the policy change was observed only days ago",
            },
            decision_state="waiting_on_maturity",
            follow_up={
                "due_on": NOT_DUE_FOLLOW_UP,
                "condition": "recheck after one more closed week",
                "scheduled": False,
            },
        )
        not_due_findings = runs.validate_run(not_due_entry, today=EVAL_DATE)
        self.assertNotIn("FOLLOW_UP_DUE", codes(not_due_findings))
        self.assertIn("FOLLOW_UP_INTENT_ONLY", codes(not_due_findings))  # read-time only, still informational

        # scheduled: true is never accepted.
        scheduled_attempt = valid_run(
            decision_state="waiting_on_maturity",
            follow_up={"due_on": NOT_DUE_FOLLOW_UP, "condition": "recheck", "scheduled": True},
        )
        self.assertIn(
            "FOLLOW_UP_NOT_SCHEDULABLE", codes(runs.validate_run(scheduled_attempt))
        )

        # No timer, job, queue or re-run is created and no state changes: reading a
        # due follow-up (repeatedly, through the full project facade) leaves every
        # byte and every filesystem entry exactly as it was.
        with tempfile.TemporaryDirectory() as tmp:
            project = _project(tmp, due_entry)
            workspace = project.context["relative_paths"]["workspace"]
            runs_path = Path(project.root) / workspace / "analysis-runs.md"
            before_hash = sha256(runs_path)
            before_listing = sorted(
                str(p.relative_to(project.root)) for p in Path(project.root).rglob("*")
            )

            envelope = runs.read_analysis_runs(
                project.root, project_context=project.context, today=EVAL_DATE
            )
            self.assertIn("FOLLOW_UP_DUE", codes(envelope["entries"][0]["diagnostics"]))
            envelope_again = runs.read_analysis_runs(
                project.root, project_context=project.context, today=EVAL_DATE
            )
            self.assertEqual(envelope, envelope_again)  # a second read changes nothing either

            self.assertEqual(sha256(runs_path), before_hash)
            after_listing = sorted(
                str(p.relative_to(project.root)) for p in Path(project.root).rglob("*")
            )
            self.assertEqual(before_listing, after_listing)  # no scheduler/job/queue artifact appeared


class S11PinnedSourcesSimulation(unittest.TestCase):
    ART = "art-11111111-1111-4111-8111-111111111111"
    UNKNOWN_ART = "art-99999999-9999-4999-8999-999999999999"
    COMMIT = "a" * 40

    def _source(self, **overrides):
        source = {
            "project_id": "",
            "artifact_id": self.ART,
            "snapshot_commit": self.COMMIT,
            "locator": "knowledge/references/population.md",
            "recorded_state": "draft",
            "tab_or_range": "sheet1!A1:D200",
            "extracted_at": "2026-09-07",
            "content_hash": None,
        }
        source.update(overrides)
        return source

    def _patched(self, **kwargs):
        registry = runs._module("project_artifact_registry")
        return mock.patch.object(registry, "read_artifact_registry", **kwargs)

    def test_pinned_sources_reopen_without_substitution(self):
        # Renamed-but-same-id: matching is by id, and reopens at the stored OID.
        with tempfile.TemporaryDirectory() as tmp:
            project = _project(tmp, valid_run(sources=[self._source()]))
            payload = {
                "return_value": {
                    "entries": [{"id": self.ART, "state": "draft", "name": "Renamed synthetic population"}],
                    "diagnostics": [],
                }
            }
            with self._patched(**payload) as patched:
                found = runs.resolve_run_sources(project.root, RUN_ID, project_context=project.context)
            self.assertEqual(len(found["sources"]), 1)
            self.assertEqual(found["sources"][0]["artifact_id"], self.ART)
            self.assertEqual(found["sources"][0]["snapshot_commit"], self.COMMIT)
            self.assertEqual(patched.call_args.kwargs["ref"], self.COMMIT)
            self.assertEqual(patched.call_args.kwargs["view"], "shared")

        # Superseded: an explicit warning, still readable, never substituted.
        with tempfile.TemporaryDirectory() as tmp:
            project = _project(tmp, valid_run(sources=[self._source()]))
            payload = {"return_value": {"entries": [{"id": self.ART, "state": "superseded"}], "diagnostics": []}}
            with self._patched(**payload):
                found = runs.resolve_run_sources(project.root, RUN_ID, project_context=project.context)
            self.assertIn("SOURCE_SUPERSEDED", codes(found["diagnostics"]))
            self.assertEqual(found["sources"][0]["artifact_id"], self.ART)
            self.assertEqual(found["sources"][0]["current_state"], "superseded")

        # Unknown id: explicit diagnostic, no similarly-titled substitution.
        with tempfile.TemporaryDirectory() as tmp:
            project = _project(tmp, valid_run(sources=[self._source()]))
            payload = {"return_value": {"entries": [{"id": self.UNKNOWN_ART, "state": "draft"}], "diagnostics": []}}
            with self._patched(**payload):
                found = runs.resolve_run_sources(project.root, RUN_ID, project_context=project.context)
            self.assertIn("SOURCE_ARTIFACT_UNKNOWN", codes(found["diagnostics"]))
            self.assertEqual(found["sources"], [])

        # A's artifact pinned under B's context: explicit mismatch, no snapshot switch.
        with tempfile.TemporaryDirectory() as tmp:
            project = _project(tmp, valid_run(sources=[self._source(project_id="synthetic-b")]))
            self.assertEqual(project.context["project_id"], "synthetic-a")
            payload = {"return_value": {"entries": [{"id": self.ART, "state": "draft"}], "diagnostics": []}}
            with self._patched(**payload):
                found = runs.resolve_run_sources(project.root, RUN_ID, project_context=project.context)
            self.assertIn("SOURCE_PROJECT_MISMATCH", codes(found["diagnostics"]))
            self.assertEqual(found["sources"], [])

        # An optional, absent private source on one run does not block an unrelated run.
        with tempfile.TemporaryDirectory() as tmp:
            healthy = valid_run(sources=[self._source()])
            broken = valid_run(id=OTHER_ID, sources=[self._source(artifact_id=self.UNKNOWN_ART)])
            project = _project(tmp, healthy, broken)

            with self._patched(return_value={"entries": [], "diagnostics": []}):
                found_broken = runs.resolve_run_sources(
                    project.root, OTHER_ID, project_context=project.context
                )
            self.assertIn("SOURCE_ARTIFACT_UNKNOWN", codes(found_broken["diagnostics"]))

            with self._patched(return_value={"entries": [{"id": self.ART, "state": "draft"}], "diagnostics": []}):
                found_ok = runs.resolve_run_sources(project.root, RUN_ID, project_context=project.context)
            self.assertEqual(found_ok["diagnostics"], [])
            self.assertEqual(len(found_ok["sources"]), 1)

        # An injected Git failure never falls back to local bytes.
        with tempfile.TemporaryDirectory() as tmp:
            project = _project(tmp, valid_run(sources=[self._source()]))
            local_path = Path(project.root) / "knowledge" / "references" / "population.md"
            local_path.parent.mkdir(parents=True, exist_ok=True)
            local_path.write_text("SYNTHETIC LOCAL BYTES; MUST NOT BE READ AS A FALLBACK\n", encoding="utf-8")
            with self._patched(side_effect=ValueError("GIT_SNAPSHOT_UNAVAILABLE")):
                found = runs.resolve_run_sources(project.root, RUN_ID, project_context=project.context)
            self.assertIn("GIT_SNAPSHOT_UNAVAILABLE", codes(found["diagnostics"]))
            self.assertEqual(found["sources"], [])


class S12DocumentFormConsistencySimulation(unittest.TestCase):
    def test_document_form_stays_consistent_across_cadences(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = transaction_project(tmp)
            project.write(
                project.context["relative_paths"]["playbooks"] + "/pb-cadence-091.md",
                playbook_text("pb-cadence-091", "Synthetic cadence playbook", "CANARY-CADENCE-091"),
            )
            resolved = runs.resolve_playbook(project.root, "cadence-091", project_context=project.context)
            playbook = resolved["playbook"]

            weekly_prefill = runs.prefill_run(playbook)
            weekly = valid_run(
                playbook_ref=weekly_prefill["playbook_ref"],
                claim_class=weekly_prefill["claim_class"],
                caveats=weekly_prefill["caveats"],
                checks=[
                    {"id": cid, "source": "code", "result": "pass", "reason": "", "evidence_ref": None}
                    for cid in weekly_prefill["required_code_checks"]
                ],
            )
            off_cycle_prefill = runs.prefill_run(playbook)
            off_cycle = valid_run(
                id=OTHER_ID,
                playbook_ref=off_cycle_prefill["playbook_ref"],
                claim_class=off_cycle_prefill["claim_class"],
                caveats=off_cycle_prefill["caveats"],
                time_window={
                    "start": "2026-09-14",
                    "end": "2026-09-20",
                    "label": "off-cycle check",
                    "grain": "week",
                },
                checks=[
                    {"id": cid, "source": "code", "result": "pass", "reason": "", "evidence_ref": None}
                    for cid in off_cycle_prefill["required_code_checks"]
                ],
            )
            self.assertEqual(runs.validate_run(weekly), [])
            self.assertEqual(runs.validate_run(off_cycle), [])
            self.assertEqual(weekly["playbook_ref"], off_cycle["playbook_ref"])
            self.assertEqual(weekly["caveats"], off_cycle["caveats"])

            matching_text = re.sub(
                r"^playbook_refs:.*$", "playbook_refs: [pb-cadence-091]", VALID_RECORD, flags=re.M
            )
            matching_relative = "memory/production-records/2026-09-07-synthetic-cadence.md"
            (Path(project.root) / matching_relative).parent.mkdir(parents=True, exist_ok=True)
            (Path(project.root) / matching_relative).write_text(matching_text, encoding="utf-8")
            matching_entry = {**weekly, "production_record_ref": matching_relative}
            self.assertEqual(runs.check_playbook_binding(project.root, matching_entry), [])

            divergent_text = re.sub(
                r"^playbook_refs:.*$", "playbook_refs: [pb-something-else]", VALID_RECORD, flags=re.M
            )
            divergent_relative = "memory/production-records/2026-09-07-synthetic-divergent.md"
            (Path(project.root) / divergent_relative).parent.mkdir(parents=True, exist_ok=True)
            (Path(project.root) / divergent_relative).write_text(divergent_text, encoding="utf-8")
            divergent_entry = {**weekly, "production_record_ref": divergent_relative}
            self.assertIn(
                "PLAYBOOK_MISMATCH", codes(runs.check_playbook_binding(project.root, divergent_entry))
            )

        with tempfile.TemporaryDirectory() as tmp2:
            many = [
                valid_run(id=f"run-44444444-4444-4444-8444-{index:012d}") for index in range(25)
            ]
            project = _project(tmp2, *many)
            envelope = runs.read_analysis_runs(project.root, project_context=project.context, limit=20)
            self.assertEqual(envelope["total"], 25)
            self.assertEqual(envelope["returned"], 20)
            self.assertEqual(envelope["omitted"], 5)
            self.assertTrue(envelope["truncated"])

        with tempfile.TemporaryDirectory() as tmp3:
            project = transaction_project(tmp3)
            project.context.update(operation.compute_project_policy("archived", "internal"))
            plan = runs.plan_playbook_scaffold(
                project.root, "monthly-trend", project_context=project.context
            )
            target = Path(project.root) / plan["target_path"]
            staged = target.with_name(target.name + ".staged")
            with self.assertRaises(operation.ProjectOperationDenied) as ctx:
                runs.apply_playbook_plan(project.root, plan, project_context=project.context)
            self.assertEqual(ctx.exception.decision["reason_code"], "PROJECT_OPERATION_DENIED_ARCHIVED")
            self.assertFalse(target.exists())
            self.assertFalse(staged.exists())

        with tempfile.TemporaryDirectory() as tmp4:
            project = transaction_project(tmp4)
            registry_module = runs._module("project_artifact_registry")
            with mock.patch.multiple(
                registry_module,
                plan_artifact_registration=mock.DEFAULT,
                apply_artifact_registration=mock.DEFAULT,
            ) as patched:
                patched["apply_artifact_registration"].return_value = {"status": "conflict"}
                result = runs.register_run_output(
                    project.root,
                    {"id": "art-11111111-1111-4111-8111-111111111111"},
                    issue_id="001-synthetic-a",
                    project_context=project.context,
                )
            self.assertEqual(result["status"], "unregistered")


if __name__ == "__main__":
    unittest.main()
