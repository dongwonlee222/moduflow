import importlib
import importlib.util
import json
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest import mock

from scripts import project_knowledge, project_operation
from scripts import project_artifact_registry as registry
from scripts.project_sync import CommandResult, run_command
from tests.knowledge_registry_fixture import ARTIFACT_A, ARTIFACT_B, SyntheticProject, make_entry, registry_text


class RegistrySchemaTests(unittest.TestCase):
    def parse(self, text):
        self.assertIsNotNone(importlib.util.find_spec("scripts.project_artifact_registry"),
                             "Canonical registry parser is required")
        return importlib.import_module("scripts.project_artifact_registry").parse_artifact_registry(text)

    def test_valid_unicode_record_round_trips_without_changing_id(self):
        entry = make_entry(name="합성 자료", summary="모집단 정의")
        parsed = self.parse(registry_text([entry]))
        self.assertTrue(parsed["metadata_valid"], parsed["diagnostics"])
        self.assertEqual(parsed["entries"], [entry])
        module = importlib.import_module("scripts.project_artifact_registry")
        rendered = "---\nschema: moduflow.artifacts.v1\n---\n\n" + module.render_artifact_entry(entry)
        self.assertEqual(self.parse(rendered)["entries"], [entry])

    def test_duplicate_id_never_selects_a_winner(self):
        result = self.parse(registry_text([make_entry(), make_entry(name="Other")]))
        self.assertFalse(result["metadata_valid"])
        self.assertEqual(result["entries"], [])
        self.assertIn("REGISTRY_DUPLICATE_ID", {d["code"] for d in result["diagnostics"]})

    def test_duplicate_id_remains_ambiguous_when_one_record_is_invalid(self):
        result = self.parse(registry_text([make_entry(), make_entry(owner="")]))
        self.assertFalse(result["metadata_valid"])
        self.assertEqual(result["entries"], [])

    def test_duplicate_json_key_and_heading_mismatch_are_invalid(self):
        text = registry_text([make_entry()])
        for invalid in (text.replace('"name":', '"name": "Other", "name":'),
                        text.replace(f"## {ARTIFACT_A}", f"## {ARTIFACT_B}"),
                        text.replace("moduflow.artifacts.v1", "moduflow.artifacts.v9"),
                        text + "```json\n{}\n```\n"):
            with self.subTest(text=invalid[:60]):
                self.assertFalse(self.parse(invalid)["metadata_valid"])

    def test_invalid_metadata_is_rejected_without_echoing_values(self):
        mutations = [
            {"id": "unsafe-private-value"}, {"kind": "unknown"}, {"state": "final"},
            {"owner": ""}, {"read_when": ""}, {"summary": "line\nline"},
            {"summary": "a" * 241}, {"as_of": "2026-02-30"},
            {"updated_at": "yesterday"}, {"review_after": "2026-13-01"},
            {"period": {"start": "2026-09-02", "end": "2026-09-01", "label": "reversed"}},
            {"period": {"start": None, "end": "2026-09-02", "label": "half"}},
            {"state": "approved", "approval_ref": None}, {"issue_ids": ["../private"]},
            {"local_path": "../unsafe-private-value"}, {"local_path": "/unsafe-private-value"},
            {"local_path": ".moduflow/transactions/private"},
            {"external_url": "https://user:unsafe-private-value@example.test"},
            {"external_url": "https://example.test/?token=unsafe-private-value"},
            {"external_url": "javascript:unsafe-private-value"},
            {"private_ref": "/unsafe-private-value"},
        ]
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                result = self.parse(registry_text([make_entry(**mutation)]))
                self.assertFalse(result["metadata_valid"])
                self.assertEqual(result["entries"], [])
                self.assertNotIn("unsafe-private-value", json.dumps(result))
        entry = make_entry()
        del entry["read_when"]
        self.assertFalse(self.parse(registry_text([entry]))["metadata_valid"])

    def test_required_missing_and_optional_unavailable_are_distinct(self):
        missing = make_entry(local_path=None)
        result = self.parse(registry_text([missing]))
        self.assertIn("REQUIRED_LINK_MISSING", {d["code"] for d in result["diagnostics"]})
        optional = make_entry(local_path=None, source_requirement="optional", unavailable_reason="Restricted original")
        self.assertTrue(self.parse(registry_text([optional]))["metadata_valid"])

    def test_supersession_requires_existing_acyclic_target(self):
        first = make_entry(state="superseded", superseded_by=ARTIFACT_B)
        second = make_entry(id=ARTIFACT_B)
        self.assertTrue(self.parse(registry_text([first, second]))["metadata_valid"])
        for entries in ([first], [make_entry(state="superseded", superseded_by=ARTIFACT_A)],
                        [first, make_entry(id=ARTIFACT_B, state="superseded", superseded_by=ARTIFACT_A)]):
            self.assertFalse(self.parse(registry_text(entries))["metadata_valid"])


class RegistryInitializationTests(unittest.TestCase):
    def test_initialization_creates_both_workspace_files_and_preserves_existing(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = SyntheticProject(tmp, nested=True)
            old = project.write("product/knowledge/index.md", "# Existing\n")
            plan = project_knowledge.build_knowledge_plan(tmp, project_context=project.context)
            self.assertIn("product/workspace/artifacts.md", plan["writes"])
            self.assertFalse((Path(tmp) / "product/workspace").exists())
            result = project_knowledge.apply_knowledge_plan(plan, project_context=project.context)
            self.assertIn("product/workspace/artifacts.md", result["written"])
            self.assertEqual(old.read_text(), "# Existing\n")
            wiki = (Path(tmp) / "product/workspace/knowledge.md").read_text()
            for heading in ("Core Metrics", "Analysis Criteria", "Recurring Sources", "Key Links", "Final Conclusions", "Interpretation Caveats"):
                self.assertIn("## " + heading, wiki)
            before = {p: p.read_bytes() for p in Path(tmp).rglob("*.md")}
            result = project_knowledge.apply_knowledge_plan(plan, project_context=project.context)
            self.assertEqual(result["written"], [])
            self.assertEqual(before, {p: p.read_bytes() for p in Path(tmp).rglob("*.md")})

    def test_partial_failure_reports_written_and_retry_only_fills_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            plan = project_knowledge.build_knowledge_plan(tmp)
            original = project_knowledge.write_text_if_missing
            def fail_catalog(path, content):
                if path.name == "artifacts.md":
                    raise OSError("private failure detail")
                return original(path, content)
            with mock.patch.object(project_knowledge, "write_text_if_missing", side_effect=fail_catalog):
                result = project_knowledge.apply_knowledge_plan(plan)
            self.assertEqual(result["status"], "partial")
            self.assertIn("workspace/knowledge.md", result["written"])
            self.assertNotIn("private failure detail", repr(result))
            result = project_knowledge.apply_knowledge_plan(plan)
            self.assertEqual(result["written"], ["workspace/artifacts.md"])

    def test_legacy_workspace_bytes_preserved_and_archived_denies_before_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = SyntheticProject(tmp)
            old = project.write("workspace/artifacts.md", "# Legacy manual catalog\n")
            plan = project_knowledge.build_knowledge_plan(tmp)
            project_knowledge.apply_knowledge_plan(plan)
            self.assertEqual(old.read_text(), "# Legacy manual catalog\n")
            project.context.update(project_operation.compute_project_policy("archived", "internal"))
            with self.assertRaises(Exception):
                project_knowledge.apply_knowledge_plan(plan, project_context=project.context)

    def test_plan_retains_archived_policy_when_apply_omits_context(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = SyntheticProject(tmp)
            project.context.update(project_operation.compute_project_policy("archived", "internal"))
            plan = project_knowledge.build_knowledge_plan(tmp, project_context=project.context)
            with self.assertRaises(Exception):
                project_knowledge.apply_knowledge_plan(plan)
            self.assertEqual(list(Path(tmp).iterdir()), [])


class RegistryReadTests(unittest.TestCase):
    def read(self, project, **kwargs):
        self.assertTrue(callable(getattr(registry, "read_artifact_registry", None)), "Read facade required")
        return registry.read_artifact_registry(project.root, project_context=project.context, **kwargs)

    def test_home_search_reads_only_metadata_in_selected_nested_project(self):
        with tempfile.TemporaryDirectory() as tmp:
            a = SyntheticProject(Path(tmp) / "a").seed()
            b = SyntheticProject(Path(tmp) / "b", "synthetic-b", nested=True).seed([
                make_entry(summary="B_PRIVATE_CANARY", local_path="product/knowledge/b.md")])
            a.write("knowledge/other.md", "UNSELECTED_SECRET")
            real_read = Path.read_text
            def guarded(path, *args, **kwargs):
                if path.name not in ("knowledge.md", "artifacts.md"):
                    raise AssertionError("Home read a source body")
                return real_read(path, *args, **kwargs)
            with mock.patch.object(Path, "read_text", guarded):
                result = self.read(a, query="population", today=date(2026, 9, 2))
            self.assertEqual(result["project_id"], "synthetic-a")
            self.assertEqual(result["returned"], 1)
            self.assertNotIn("B_PRIVATE_CANARY", repr(result))
            self.assertEqual({r["operation"] for r in result["read_trace"]}, {"metadata-content", "link-stat"})
            selected = registry.read_artifact_sources(a.root, [ARTIFACT_A], project_context=a.context)
            self.assertEqual(selected["sources"][0]["content"], "# Synthetic source\nPOPULATION_A\n")
            self.assertNotIn("UNSELECTED_SECRET", repr(selected))
            result_b = self.read(b)
            self.assertEqual(result_b["entries"][0]["local_path"], "product/knowledge/b.md")

    def test_optional_private_external_and_staleness_axes_are_independent(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = SyntheticProject(tmp).seed([make_entry(local_path=None, private_ref="restricted:a",
                source_requirement="optional", review_after="2026-09-01")])
            result = self.read(project, today=date(2026, 9, 2))
            entry = result["entries"][0]
            self.assertTrue(entry["metadata_valid"])
            self.assertEqual(entry["state"], "draft")
            self.assertEqual(entry["freshness"], "stale")
            self.assertEqual(entry["source_availability"], "unavailable")
            self.assertIn("OPTIONAL_SOURCE_UNAVAILABLE", {d["code"] for d in entry["diagnostics"]})
            project.seed([make_entry(local_path=None, external_url="https://example.test/source", review_after=None)])
            entry = self.read(project)["entries"][0]
            self.assertEqual(entry["source_availability"], "unchecked")
            self.assertEqual(entry["freshness"], "unknown")

    def test_broken_local_and_missing_issue_are_not_source_ready(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = SyntheticProject(tmp).seed()
            (Path(tmp) / "knowledge/references/population.md").unlink()
            (Path(tmp) / "issues/001-synthetic-a.md").unlink()
            result = self.read(project)
            codes = {d["code"] for d in result["diagnostics"]}
            self.assertIn("LOCAL_LINK_BROKEN", codes)
            self.assertIn("REGISTRY_ISSUE_LINK_MISSING", codes)

    def test_shared_snapshot_reads_committed_bytes_and_marks_dirty(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = SyntheticProject(tmp).seed()
            oid = project.commit()
            project.write("knowledge/references/population.md", "DIRTY_BODY")
            project.write("workspace/knowledge.md", "DIRTY_WIKI")
            result = self.read(project, view="shared", ref=oid)
            self.assertEqual(result["snapshot_commit"], oid)
            self.assertNotIn("DIRTY_WIKI", repr(result))
            self.assertIn("SOURCE_DIRTY", {d["code"] for d in result["diagnostics"]})
            selected = registry.read_artifact_sources(project.root, [ARTIFACT_A], project_context=project.context,
                                                      view="shared", ref=oid)
            self.assertEqual(selected["sources"][0]["content"], "# Synthetic source\nPOPULATION_A\n")
            self.assertEqual(selected["snapshot_commit"], oid)

    def test_shared_snapshot_never_falls_back_to_uncommitted_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = SyntheticProject(tmp).seed()
            source = Path(tmp) / "knowledge/references/population.md"
            source.unlink()
            oid = project.commit()
            source.write_text("AUTHOR_ONLY")
            result = self.read(project, view="shared", ref=oid)
            self.assertEqual(result["entries"][0]["share_status"], "blocked")
            self.assertIn("SOURCE_UNCOMMITTED", {d["code"] for d in result["diagnostics"]})
            selected = registry.read_artifact_sources(project.root, [ARTIFACT_A], project_context=project.context,
                                                      view="shared", ref=oid)
            self.assertNotIn("AUTHOR_ONLY", repr(selected))

    def test_unavailable_git_and_unknown_ids_return_explicit_diagnostics(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = SyntheticProject(tmp).seed()
            failed_runner = lambda *args, **kwargs: CommandResult(128, "", "PRIVATE_GIT_ERROR")
            result = self.read(project, view="shared", runner=failed_runner)
            self.assertEqual(result["entries"], [])
            self.assertIn("GIT_SNAPSHOT_UNAVAILABLE", repr(result))
            self.assertNotIn("PRIVATE_GIT_ERROR", repr(result))
            result = self.read(project, artifact_ids=[ARTIFACT_B])
            self.assertEqual(result["entries"], [])
            self.assertIn("REGISTRY_ID_NOT_FOUND", repr(result))

    def test_limits_unbound_identity_and_long_wiki_are_visible(self):
        with tempfile.TemporaryDirectory() as tmp:
            entries = [make_entry(id=f"art-{i:08x}-1111-4111-8111-111111111111") for i in range(25)]
            project = SyntheticProject(tmp).seed(entries)
            project.write("workspace/knowledge.md", "# Wiki\n\n## Long\n" + "x" * 4100)
            project.context.pop("project_id")
            result = self.read(project)
            self.assertEqual((result["total"], result["returned"], result["omitted"]), (25, 20, 5))
            self.assertTrue(result["truncated"])
            self.assertIsNone(result["project_id"])
            self.assertEqual(result["identity_status"], "unbound")
            self.assertTrue(result["home_truncated"])

    def test_unsafe_symlink_and_denied_context_are_not_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = SyntheticProject(Path(tmp) / "a").seed()
            secret = Path(tmp) / "outside.md"
            secret.write_text("OUTSIDE_SECRET")
            target = project.root / "knowledge/references/population.md"
            target.unlink()
            target.symlink_to(secret)
            result = self.read(project)
            self.assertIn("UNSAFE_SOURCE_LINK", repr(result))
            selected = registry.read_artifact_sources(project.root, [ARTIFACT_A], project_context=project.context)
            self.assertNotIn("OUTSIDE_SECRET", repr(selected))
            denied = dict(project.context, status="unresolved")
            with self.assertRaises(ValueError):
                registry.read_artifact_registry(project.root, project_context=denied)


class RegistryReviewRegressionTests(unittest.TestCase):
    def test_existing_business_issue_ids_are_accepted_and_resolved(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = SyntheticProject(tmp).seed([make_entry(issue_ids=["BIZ-103"])])
            result = registry.read_artifact_registry(project.root, project_context=project.context)
            self.assertTrue(result["metadata_valid"], result)
            self.assertEqual(result["entries"][0]["issue_ids"], ["BIZ-103"])

    def test_orphan_json_and_incomplete_heading_are_not_empty_valid_catalogs(self):
        for body in ("```json\n{}\n```\n", "## " + ARTIFACT_A):
            parsed = registry.parse_artifact_registry("---\nschema: moduflow.artifacts.v1\n---\n\n" + body)
            self.assertFalse(parsed["metadata_valid"], body)

    def test_human_prose_headings_outside_record_sections_are_preserved(self):
        catalog = registry_text([make_entry()]) + "\n## Human notes\n\nKeep these notes.\n"
        self.assertTrue(registry.parse_artifact_registry(catalog)["metadata_valid"])
        rendered = registry.render_registration(catalog, make_entry(summary="Revised"), amend=True)
        self.assertIn("## Human notes\n\nKeep these notes.", rendered)

    def test_approved_records_require_issue_and_drafts_cannot_claim_approval_evidence(self):
        for entry in (make_entry(state="approved", approval_ref="knowledge/approval.md", issue_ids=[]),
                      make_entry(approval_ref="knowledge/approval.md")):
            self.assertFalse(registry.parse_artifact_registry(registry_text([entry]))["metadata_valid"])

    def test_token_fragment_is_rejected_without_echoing_the_token(self):
        parsed = registry.parse_artifact_registry(registry_text([
            make_entry(external_url="https://example.test/x#access_token=PRIVATE_TOKEN")]))
        self.assertFalse(parsed["metadata_valid"])
        self.assertNotIn("PRIVATE_TOKEN", repr(parsed))

    def test_diagnostics_identify_safe_registry_or_source_location(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = SyntheticProject(tmp).seed()
            (project.root / "knowledge/references/population.md").unlink()
            result = registry.read_artifact_registry(project.root, project_context=project.context)
            broken = next(d for d in result["diagnostics"] if d["code"] == "LOCAL_LINK_BROKEN")
            self.assertEqual(broken.get("location"), "knowledge/references/population.md")
            project.write("workspace/artifacts.md", "legacy text")
            invalid = registry.read_artifact_registry(project.root, project_context=project.context)
            self.assertEqual(invalid["diagnostics"][0].get("location"), "workspace/artifacts.md")


if __name__ == "__main__":
    unittest.main()
