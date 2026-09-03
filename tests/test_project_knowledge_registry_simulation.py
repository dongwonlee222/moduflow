"""S01–S14: synthetic-only offline scenarios; no live company data or host install."""
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest import mock

from scripts import project_artifact_registry as registry, project_knowledge, project_operation
from scripts.project_sync import run_command
from tests.knowledge_registry_fixture import (
    ARTIFACT_A, ARTIFACT_B, SyntheticProject, make_entry, registry_text,
    transaction_project, shared_lifecycle_bytes,
)

ARTIFACT_C = "art-33333333-3333-4333-8333-333333333333"
ARTIFACT_D = "art-44444444-4444-4444-8444-444444444444"
TODAY = date(2026, 9, 2)


def codes(result):
    return {item["code"] for item in result["diagnostics"]}


def file_hashes(root):
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob("*") if p.is_file() and ".git" not in p.parts}


class RegistrySimulationTests(unittest.TestCase):
    def read(self, project, **options):
        return registry.read_artifact_registry(project.root, project_context=project.context, today=TODAY, **options)

    def sources(self, project, ids, **options):
        return registry.read_artifact_sources(project.root, ids, project_context=project.context, **options)

    def test_empty_project_initialization_is_non_destructive(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = SyntheticProject(tmp)
            self.assertIn("REGISTRY_NOT_INITIALIZED", codes(self.read(project)))
            plan = project_knowledge.build_knowledge_plan(project.root, project_context=project.context)
            self.assertEqual(file_hashes(project.root), {})
            first = project_knowledge.apply_knowledge_plan(plan)
            self.assertEqual(first["status"], "complete")
            before = file_hashes(project.root)
            second = project_knowledge.apply_knowledge_plan(project_knowledge.build_knowledge_plan(project.root, project_context=project.context))
            self.assertEqual(second["written"], [])
            self.assertEqual(before, file_hashes(project.root))
            self.assertEqual(len(self.read(project)["sections"]), 6)

    def test_legacy_migration_preserves_sources(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = SyntheticProject(tmp)
            for name, body in (("workspace/knowledge.md", "# Legacy wiki\nKeep this."),
                               ("workspace/artifacts.md", "# Old catalog\nUnstructured notes."),
                               ("memory/decisions/legacy.md", "---\nid: original-id\nreferences: [prior-id]\n---\nLegacy source")):
                project.write(name, body)
            before = file_hashes(project.root)
            plan = project_knowledge.build_knowledge_plan(project.root, project_context=project.context)
            self.assertEqual(before, file_hashes(project.root))
            result = project_knowledge.apply_knowledge_plan(plan)
            self.assertIn("workspace/artifacts.md", result["preserved"])
            after = file_hashes(project.root)
            self.assertEqual(before, {p: after[p] for p in before})
            self.assertIn("REGISTRY_SCHEMA_UNSUPPORTED", codes(self.read(project)))

    def test_project_a_b_switch_keeps_metadata_scoped(self):
        with tempfile.TemporaryDirectory() as tmp:
            a = SyntheticProject(Path(tmp) / "a").seed()
            b = SyntheticProject(Path(tmp) / "b", project_id="synthetic-b", nested=True).seed([
                make_entry(owner="Synthetic B", issue_ids=["002-synthetic-b"], local_path="product/knowledge/references/b.md")])
            a.write("knowledge/references/population.md", "SYNTHETIC_A_SOURCE")
            b.write("product/knowledge/references/b.md", "SYNTHETIC_B_PRIVATE_MARKER")
            b.write("workspace/artifacts.md", "POISON_DEFAULT_CATALOG")
            for project, other in ((a, b), (b, a)):
                result = self.read(project, query="population")
                self.assertEqual(result["project_id"], project.context["project_id"])
                self.assertEqual(result["entries"][0]["id"], ARTIFACT_A)
                self.assertNotIn(other.context["project_id"], repr(result))
                self.assertNotIn("SYNTHETIC_B_PRIVATE_MARKER", repr(result))
                self.assertNotIn("POISON_DEFAULT_CATALOG", repr(result))
            self.assertEqual(self.sources(b, [ARTIFACT_A])["sources"][0]["content"], "SYNTHETIC_B_PRIVATE_MARKER")

    def test_required_link_missing_and_local_broken_differ(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = SyntheticProject(tmp).seed([make_entry(local_path=None), make_entry(id=ARTIFACT_B)])
            (project.root / "knowledge/references/population.md").unlink()
            result = self.read(project)
            self.assertTrue({"REQUIRED_LINK_MISSING", "LOCAL_LINK_BROKEN"} <= codes(result))
            self.assertEqual(result["entries"][0]["id"], ARTIFACT_B)
            self.assertIsNone(result["entries"][0]["external_url"])
            self.assertFalse(result["entries"][0]["metadata_valid"])

    def test_optional_private_absence_is_metadata_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = SyntheticProject(tmp).seed([
                make_entry(local_path=None, private_ref="private:synthetic", source_requirement="optional"),
                make_entry(id=ARTIFACT_B, local_path=None, source_requirement="optional", unavailable_reason="No original retained")])
            oid = project.commit()
            result = self.read(project, view="shared", ref=oid)
            self.assertTrue(result["metadata_valid"])
            for entry in result["entries"]:
                self.assertEqual(entry["source_availability"], "unavailable")
                self.assertEqual(entry["share_status"], "metadata_only")
                self.assertTrue(all(d["severity"] == "info" for d in entry["diagnostics"]))
            self.assertTrue(all(t["operation"] != "source-content" for t in result["read_trace"]))

    def test_required_private_and_external_are_not_assumed_accessible(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = SyntheticProject(tmp).seed([
                make_entry(local_path=None, private_ref="private:required"),
                make_entry(id=ARTIFACT_B, local_path=None, external_url="https://example.test/source"),
                make_entry(id=ARTIFACT_C, external_url="https://example.test/source")])
            oid = project.commit()
            result = self.sources(project, [ARTIFACT_A, ARTIFACT_B, ARTIFACT_C], view="shared", ref=oid)
            entries = {e["id"]: e for e in result["entries"]}
            self.assertEqual(entries[ARTIFACT_A]["share_status"], "metadata_only")
            self.assertEqual(entries[ARTIFACT_B]["source_availability"], "unchecked")
            self.assertEqual(entries[ARTIFACT_C]["share_status"], "ready")
            self.assertTrue(all(s["content"] is None for s in result["sources"][:2]))
            self.assertIn("POPULATION_A", result["sources"][2]["content"])

    def test_staleness_and_supersession_preserve_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            entries = [make_entry(state="approved", approval_ref="knowledge/decisions/approval.md", review_after="2026-09-01"),
                       make_entry(id=ARTIFACT_B, review_after="2026-09-02"),
                       make_entry(id=ARTIFACT_C, state="superseded", superseded_by=ARTIFACT_B, review_after=None)]
            project = SyntheticProject(tmp).seed(entries)
            project.write("knowledge/decisions/approval.md", "Synthetic approval evidence")
            result = self.read(project)
            self.assertEqual([(e["state"], e["freshness"]) for e in result["entries"]],
                             [("approved", "stale"), ("draft", "current"), ("superseded", "unknown")])
            old_path = project.root / entries[0]["local_path"]
            renamed = project.root / "knowledge/references/renamed.md"
            old_path.rename(renamed)
            updated = make_entry(**{**entries[0], "local_path": "knowledge/references/renamed.md"})
            catalog = project.root / "workspace/artifacts.md"
            catalog.write_text(registry.render_registration(catalog.read_text(), updated, amend=True))
            self.assertEqual(self.read(project, artifact_ids=[ARTIFACT_A])["entries"][0]["id"], ARTIFACT_A)
            self.assertIn("POPULATION_A", self.sources(project, [ARTIFACT_A])["sources"][0]["content"])
            cycle = registry.parse_artifact_registry(registry_text([
                make_entry(state="superseded", superseded_by=ARTIFACT_B),
                make_entry(id=ARTIFACT_B, state="superseded", superseded_by=ARTIFACT_A)]))
            self.assertIn("REGISTRY_SUPERSESSION_INVALID", codes(cycle))

    def test_fresh_reader_opens_only_selected_original(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = SyntheticProject(tmp).seed([make_entry(), make_entry(id=ARTIFACT_B, name="Other report",
                kind="report", summary="Unrelated", read_when="For another decision", local_path="knowledge/reports/other.md")])
            actual_reads = []
            original = registry._local_file
            def spy(root, relative, *, content=False):
                if content:
                    actual_reads.append(relative)
                return original(root, relative, content=content)
            with mock.patch.object(registry, "_local_file", side_effect=spy):
                result = self.read(project, query="population")
                self.assertEqual(actual_reads, ["workspace/knowledge.md", "workspace/artifacts.md"])
                self.assertTrue(result["entries"][0]["match_reasons"])
                actual_reads.clear()
                selected = self.sources(project, [ARTIFACT_A])
            self.assertEqual(actual_reads, ["workspace/knowledge.md", "workspace/artifacts.md", "knowledge/references/population.md"])
            self.assertNotIn("knowledge/reports/other.md", repr(selected["read_trace"]))
            print("S08 read_trace=" + json.dumps(selected["read_trace"], sort_keys=True))

    def test_committed_worktree_resume_ignores_author_only_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            author = SyntheticProject(Path(tmp) / "author").seed()
            first = author.commit()
            reader_path = Path(tmp) / "reader"
            author.git("worktree", "add", "--detach", str(reader_path), first)
            reader = SyntheticProject(reader_path)
            selected = self.sources(reader, [ARTIFACT_A], view="shared", ref=first)
            self.assertEqual(selected["snapshot_commit"], first)
            self.assertIn("POPULATION_A", selected["sources"][0]["content"])
            author.write("knowledge/reports/author-only.md", "AUTHOR_ONLY_MARKER")
            author.write("workspace/artifacts.md", registry_text([make_entry(), make_entry(id=ARTIFACT_B, local_path="knowledge/reports/author-only.md")]))
            author.git("add", "workspace/artifacts.md")
            author.git("commit", "-qm", "catalog without original")
            second = author.git("rev-parse", "HEAD")
            calls = []
            def runner(args, cwd, timeout=None):
                calls.append(args)
                return run_command(args, cwd, timeout=timeout)
            missing = self.sources(reader, [ARTIFACT_B], view="shared", ref=second, runner=runner)
            self.assertIn("LOCAL_LINK_BROKEN", codes(missing))
            self.assertIsNone(missing["sources"][0]["content"])
            self.assertNotIn("AUTHOR_ONLY_MARKER", repr(missing))
            self.assertTrue(all(args[3] == second for args in calls if args[1] == "ls-tree"))
            self.assertEqual(reader.git("rev-parse", "HEAD"), first)
            print("S09 snapshots=" + json.dumps({"original": first, "later_catalog": second, "reader_checkout": first}))

    def test_dirty_staged_ignored_and_missing_evidence_do_not_rescue(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = SyntheticProject(tmp).seed()
            project.commit()
            entries = [make_entry(), make_entry(id=ARTIFACT_B, local_path="knowledge/references/staged.md"),
                       make_entry(id=ARTIFACT_C, local_path="knowledge/references/ignored.md"),
                       make_entry(id=ARTIFACT_D, state="approved", approval_ref="knowledge/decisions/approval.md", issue_ids=["002-missing-issue"])]
            project.write("workspace/artifacts.md", registry_text(entries))
            project.write(".gitignore", "knowledge/references/ignored.md\n")
            project.git("add", "workspace/artifacts.md", ".gitignore")
            project.git("commit", "-qm", "metadata with unavailable originals")
            oid = project.git("rev-parse", "HEAD")
            project.write("knowledge/references/population.md", "DIRTY_MARKER")
            project.write("knowledge/references/staged.md", "STAGED_MARKER")
            project.git("add", "knowledge/references/staged.md")
            project.write("knowledge/references/ignored.md", "IGNORED_MARKER")
            project.write("knowledge/decisions/approval.md", "Uncommitted approval")
            project.write("issues/002-missing-issue.md", "Uncommitted issue")
            result = self.sources(project, [ARTIFACT_A, ARTIFACT_B, ARTIFACT_C, ARTIFACT_D], view="shared", ref=oid)
            self.assertTrue({"SOURCE_DIRTY", "SOURCE_UNCOMMITTED", "REGISTRY_ISSUE_LINK_MISSING", "REGISTRY_APPROVAL_LINK_MISSING"} <= codes(result))
            self.assertIn("POPULATION_A", result["sources"][0]["content"])
            self.assertTrue(all(s["content"] is None for s in result["sources"][1:]))
            self.assertNotIn("DIRTY_MARKER", repr(result))
            self.assertNotIn("STAGED_MARKER", repr(result))
            self.assertNotIn("IGNORED_MARKER", repr(result))

    def test_registration_failure_and_retry_are_atomic(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = transaction_project(tmp)
            before = shared_lifecycle_bytes(project)
            entry = make_entry(kind="report", local_path="knowledge/reports/2026-09-02-synthetic-report.md")
            engine = registry._transaction_module()
            original = engine.validate_project_artifacts.validate_project
            def invalidate_canonical(root, **kwargs):
                result = original(root, **kwargs)
                if Path(root).resolve() == project.root.resolve():
                    result.update(valid=False, errors=["Synthetic post-apply validation failure"])
                return result
            def create():
                return project_knowledge.create_knowledge_artifact(project.root, "report", "Synthetic report",
                    issue_id="001-synthetic-a", project_context=project.context, registry_entry=entry)
            with mock.patch.object(engine.validate_project_artifacts, "validate_project", side_effect=invalidate_canonical):
                failed = create()
            self.assertEqual(failed["status"], "rolled_back", failed)
            self.assertFalse((project.root / entry["local_path"]).exists())
            self.assertEqual(before, shared_lifecycle_bytes(project))
            self.assertEqual(create()["status"], "applied")
            self.assertEqual(create()["status"], "noop")
            self.assertEqual((project.root / "issues/001-synthetic-a.md").read_text().count("#" + ARTIFACT_A), 1)
            self.assertEqual(before, shared_lifecycle_bytes(project))

    def test_denial_and_initialization_failure_are_truthful(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = SyntheticProject(tmp)
            plan = project_knowledge.build_knowledge_plan(project.root, project_context=project.context)
            original = project_knowledge.write_text_if_missing
            def fail_catalog(path, content):
                if path.name == "artifacts.md":
                    raise OSError("Synthetic init failure")
                return original(path, content)
            with mock.patch.object(project_knowledge, "write_text_if_missing", side_effect=fail_catalog):
                result = project_knowledge.apply_knowledge_plan(plan)
            self.assertEqual(result["status"], "partial")
            self.assertIn("workspace/knowledge.md", result["written"])
            before = file_hashes(project.root)
            project_knowledge.apply_knowledge_plan(project_knowledge.build_knowledge_plan(project.root, project_context=project.context))
            self.assertEqual(before, {p: file_hashes(project.root)[p] for p in before})
            with self.assertRaises(ValueError):
                registry.plan_artifact_registration(project.root, make_entry(), issue_id="001-synthetic-a", project_context=project.context)
            self.assertFalse((project.root / ".moduflow").exists())
            project.context.update(project_operation.compute_project_policy("archived", "internal"))
            self.assertTrue(self.read(project)["metadata_valid"])
            with self.assertRaises(project_operation.ProjectOperationDenied):
                project_knowledge.apply_knowledge_plan(plan, project_context=project.context)
            self.assertFalse((project.root / ".moduflow").exists())

    def test_limits_identity_and_consumer_references_are_explicit(self):
        with tempfile.TemporaryDirectory() as tmp:
            a = SyntheticProject(Path(tmp) / "a").seed([
                make_entry(id=f"art-{i:08x}-1111-4111-8111-111111111111") for i in range(25)])
            b = SyntheticProject(Path(tmp) / "b", project_id="synthetic-b").seed()
            a.write("workspace/knowledge.md", "# Knowledge\n\n## Long guide\n" + "x" * 5000 + "\n")
            result = self.read(a)
            self.assertEqual((result["total"], result["returned"], result["omitted"]), (25, 20, 5))
            self.assertTrue(result["truncated"] and result["home_truncated"])
            self.assertTrue(result["omitted_sections"])
            with self.assertRaises(ValueError):
                registry.read_artifact_registry(a.root, project_context=b.context, artifact_ids=[ARTIFACT_A])
            a.context["project_id"] = None
            self.assertEqual(self.read(a)["identity_status"], "unbound")
            self.assertIn("REGISTRY_ID_NOT_FOUND", codes(self.read(a, artifact_ids=[ARTIFACT_D])))

    def test_unsafe_paths_and_git_failures_never_fallback(self):
        for overrides in ({"local_path": "../SYNTHETIC_PRIVATE"}, {"local_path": "/SYNTHETIC_PRIVATE/file"},
                          {"external_url": "https://user:SYNTHETIC_PRIVATE@example.test/x"},
                          {"external_url": "https://example.test/x?token=SYNTHETIC_PRIVATE"}):
            parsed = registry.parse_artifact_registry(registry_text([make_entry(**overrides)]))
            self.assertFalse(parsed["metadata_valid"])
            self.assertNotIn("SYNTHETIC_PRIVATE", repr(parsed))
        with tempfile.TemporaryDirectory() as tmp:
            project = SyntheticProject(Path(tmp) / "project").seed()
            outside = Path(tmp) / "outside.md"
            outside.write_text("SYNTHETIC_PRIVATE_MARKER")
            source = project.root / "knowledge/references/population.md"
            source.unlink()
            source.symlink_to(outside)
            self.assertIn("UNSAFE_SOURCE_LINK", codes(self.sources(project, [ARTIFACT_A])))
            first = project.commit()
            self.assertIn("UNSAFE_SOURCE_LINK", codes(self.sources(project, [ARTIFACT_A], view="shared", ref=first)))
            project.git("update-index", "--add", "--cacheinfo", f"160000,{first},vendor/reference")
            project.write("workspace/artifacts.md", registry_text([make_entry(local_path="vendor/reference")]))
            project.git("add", "workspace/artifacts.md")
            project.git("commit", "-qm", "synthetic gitlink")
            self.assertIn("UNSAFE_SOURCE_LINK", codes(self.sources(project, [ARTIFACT_A], view="shared")))
            bad = self.read(project, view="shared", ref="$(not-a-command)")
            self.assertIn("GIT_SNAPSHOT_UNAVAILABLE", codes(bad))
            def fail_git(*args, **kwargs):
                raise OSError("SYNTHETIC_PRIVATE_ERROR")
            failed = self.read(project, view="shared", runner=fail_git)
            self.assertIn("GIT_SNAPSHOT_UNAVAILABLE", codes(failed))
            self.assertNotIn("SYNTHETIC_PRIVATE", repr(failed))

    def test_packaged_cli_initializes_and_reads_without_source_checkout(self):
        from tests.runtime_provenance_fixture import make_distribution
        with tempfile.TemporaryDirectory() as tmp:
            package = make_distribution(Path(tmp) / "package")
            project = SyntheticProject(Path(tmp) / "target")
            command = [sys.executable, str(package / "scripts/project_knowledge.py"), str(project.root)]
            init = subprocess.run([*command, "--write"], cwd=tmp, capture_output=True, text=True)
            self.assertEqual(init.returncode, 0, init.stderr)
            project.seed()
            inspected = subprocess.run([*command, "--inspect"], cwd=tmp, capture_output=True, text=True)
            self.assertEqual(inspected.returncode, 0, inspected.stderr)
            self.assertEqual(json.loads(inspected.stdout)["schema"], "moduflow.artifact-registry-read.v1")
            selected = subprocess.run([*command, "--read-sources", "--artifact-id", ARTIFACT_A], cwd=tmp, capture_output=True, text=True)
            self.assertEqual(selected.returncode, 0, selected.stderr)
            self.assertIn("POPULATION_A", json.loads(selected.stdout)["sources"][0]["content"])


if __name__ == "__main__":
    unittest.main()
