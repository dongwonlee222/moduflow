import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_module(name, relative_path):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ProjectMemoryTests(unittest.TestCase):
    def test_memory_dry_run_lists_missing_portable_structure_without_writing(self):
        project_memory = load_module("project_memory", "scripts/project_memory.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            plan = project_memory.build_memory_plan(root)

            self.assertTrue(plan["dry_run"])
            self.assertIn("memory/index.md", plan["writes"])
            self.assertIn("memory/decisions", plan["writes"])
            self.assertIn("memory/deliverables", plan["writes"])
            self.assertFalse((root / "memory" / "index.md").exists())

    def test_memory_write_creates_structure_and_preserves_existing_files(self):
        project_memory = load_module("project_memory", "scripts/project_memory.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            index = root / "memory" / "index.md"
            index.parent.mkdir()
            index.write_text("# Existing Memory\n", encoding="utf-8")

            plan = project_memory.build_memory_plan(root, dry_run=False)
            result = project_memory.apply_memory_plan(plan)

            self.assertNotIn("memory/index.md", result["written"])
            self.assertEqual(index.read_text(encoding="utf-8"), "# Existing Memory\n")
            self.assertTrue((root / "memory" / "decisions").is_dir())
            self.assertTrue((root / "memory" / "deliverables").is_dir())

    def test_memory_write_creates_candidate_directory(self):
        project_memory = load_module("project_memory", "scripts/project_memory.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            plan = project_memory.build_memory_plan(root, dry_run=False)
            result = project_memory.apply_memory_plan(plan)

            self.assertIn("memory/.candidates", result["written"])
            self.assertTrue((root / "memory" / ".candidates").is_dir())

    def test_create_memory_entry_records_decision_fields_and_relative_links(self):
        project_memory = load_module("project_memory", "scripts/project_memory.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            entry = project_memory.create_memory_entry(
                root,
                kind="decision",
                title="Use repo-local memory",
                issue_id="030-project-memory-layer",
                spec_path="specs/030-project-memory-layer/spec.md",
                summary="Keep project memory portable inside the repo.",
                rationale="Projects must remain independent when copied or cloned.",
                evidence="External memory indexes can be rebuilt from Markdown files.",
                alternatives="External-only DB memory",
                owner="Dongwon Lee",
                reversal_conditions="Search scale requires an external index.",
                tags=["memory", "portability"],
            )

            entry_path = root / entry["path"]
            content = entry_path.read_text(encoding="utf-8")
            self.assertEqual(entry["kind"], "decision")
            self.assertTrue(entry["path"].startswith("memory/decisions/"))
            self.assertIn("issue_id: 030-project-memory-layer", content)
            self.assertIn("spec: specs/030-project-memory-layer/spec.md", content)
            self.assertIn("rationale: Projects must remain independent", content)
            self.assertIn("tags: [memory, portability]", content)
            self.assertNotIn(str(root), content)

    def test_create_memory_entry_records_source_and_review_fields(self):
        project_memory = load_module("project_memory", "scripts/project_memory.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "specs" / "034-memory-capture-and-sync-workflow").mkdir(parents=True)
            (root / "specs" / "034-memory-capture-and-sync-workflow" / "spec.md").write_text(
                "# Spec\n", encoding="utf-8"
            )

            entry = project_memory.create_memory_entry(
                root,
                kind="decision",
                title="Use Git canonical memory",
                issue_id="034-memory-capture-and-sync-workflow",
                spec_path="specs/034-memory-capture-and-sync-workflow/spec.md",
                summary="Keep memory canonical in Git-tracked Markdown.",
                source_event="decision-approved",
                source_artifacts=["specs/034-memory-capture-and-sync-workflow/spec.md"],
                review_after="2026-07-26",
                supersedes=["2026-06-24-use-portable-project-memory"],
                storage_policy="team",
                mirror_targets=["google-drive", "obsidian"],
                tags=["memory", "team"],
            )

            content = (root / entry["path"]).read_text(encoding="utf-8")
            self.assertIn("source_event: decision-approved", content)
            self.assertIn("source_artifacts: [specs/034-memory-capture-and-sync-workflow/spec.md]", content)
            self.assertIn("review_after: 2026-07-26", content)
            self.assertIn("supersedes: [2026-06-24-use-portable-project-memory]", content)
            self.assertIn("storage_policy: team", content)
            self.assertIn("mirror_targets: [google-drive, obsidian]", content)

    def test_create_memory_candidate_writes_reviewable_candidate(self):
        project_memory = load_module("project_memory", "scripts/project_memory.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            candidate = project_memory.create_memory_candidate(
                root,
                kind="decision",
                title="Use Git canonical memory",
                issue_id="034-memory-capture-and-sync-workflow",
                summary="Keep memory canonical in Git-tracked Markdown.",
                source_event="decision-detected",
                source_artifacts=["specs/034-memory-capture-and-sync-workflow/spec.md"],
                tags=["memory", "team"],
            )

            candidate_path = root / candidate["path"]
            content = candidate_path.read_text(encoding="utf-8")
            self.assertEqual(candidate["status"], "candidate")
            self.assertTrue(candidate["path"].startswith("memory/.candidates/"))
            self.assertIn("status: candidate", content)
            self.assertIn("kind: decision", content)
            self.assertIn("source_event: decision-detected", content)

    def test_list_and_approve_memory_candidate_moves_to_kind_folder(self):
        project_memory = load_module("project_memory", "scripts/project_memory.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidate = project_memory.create_memory_candidate(
                root,
                kind="decision",
                title="Use Git canonical memory",
                summary="Keep memory canonical in Git-tracked Markdown.",
                tags=["memory"],
            )

            candidates = project_memory.list_memory_candidates(root)
            approved = project_memory.approve_memory_candidate(root, candidate["id"])

            self.assertEqual([item["id"] for item in candidates], [candidate["id"]])
            self.assertTrue(approved["path"].startswith("memory/decisions/"))
            self.assertFalse((root / candidate["path"]).exists())
            self.assertTrue((root / approved["path"]).exists())
            self.assertIn("status: approved", (root / approved["path"]).read_text(encoding="utf-8"))

    def test_search_and_get_memory_entries_use_project_local_files(self):
        project_memory = load_module("project_memory", "scripts/project_memory.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            created = project_memory.create_memory_entry(
                root,
                kind="deliverable",
                title="Project memory spec",
                summary="Defines portable project memory.",
                tags=["memory"],
            )

            hits = project_memory.search_memory_entries(root, "portable", kind="deliverable")
            fetched = project_memory.get_memory_entry(root, created["id"])

            self.assertEqual([hit["id"] for hit in hits], [created["id"]])
            self.assertEqual(fetched["id"], created["id"])
            self.assertEqual(fetched["path"], created["path"])
            self.assertIn("Defines portable project memory.", fetched["content"])

    def test_search_memory_entries_returns_match_reasons_and_source_artifacts(self):
        project_memory = load_module("project_memory", "scripts/project_memory.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project_memory.create_memory_entry(
                root,
                kind="decision",
                title="Use Git canonical memory",
                issue_id="034-memory-capture-and-sync-workflow",
                summary="Keep memory canonical in Git-tracked Markdown.",
                source_artifacts=["specs/034-memory-capture-and-sync-workflow/spec.md"],
                tags=["memory", "team"],
            )

            hits = project_memory.search_memory_entries(root, "canonical memory", tag="team")

            self.assertEqual(len(hits), 1)
            self.assertIn("query: canonical", hits[0]["match_reasons"])
            self.assertIn("query: memory", hits[0]["match_reasons"])
            self.assertIn("tag: team", hits[0]["match_reasons"])
            self.assertEqual(
                hits[0]["source_artifacts"],
                ["specs/034-memory-capture-and-sync-workflow/spec.md"],
            )

    def test_memory_export_guidance_keeps_markdown_canonical(self):
        project_memory = load_module("project_memory", "scripts/project_memory.py")

        guidance = project_memory.memory_export_guidance("google-drive")

        self.assertEqual(guidance["target"], "google-drive")
        self.assertEqual(guidance["canonical"], "memory/")
        self.assertIn("mirror", guidance["mode"])
        self.assertIn("Do not treat Google Drive as the source of truth.", guidance["warnings"])

    def test_doctor_reports_memory_missing_and_initialized(self):
        project_doctor = load_module("project_doctor", "scripts/project_doctor.py")
        project_memory = load_module("project_memory", "scripts/project_memory.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            missing = project_doctor.missing_memory_paths(root)
            self.assertIn("memory/index.md", missing)

            project_memory.apply_memory_plan(project_memory.build_memory_plan(root, dry_run=False))

            self.assertEqual(project_doctor.missing_memory_paths(root), [])

    def test_project_validation_reports_broken_memory_source_artifact(self):
        validate_project_artifacts = load_module(
            "validate_project_artifacts", "scripts/validate_project_artifacts.py"
        )
        project_memory = load_module("project_memory", "scripts/project_memory.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".moduflow").mkdir()
            (root / ".moduflow" / "config.json").write_text(
                '{"schema":"moduflow.config.v1","paths":{}}', encoding="utf-8"
            )
            (root / ".moduflow" / "state.json").write_text(
                '{"schema":"moduflow.state.v1","phase":"status","next_command":"product:status"}',
                encoding="utf-8",
            )
            for relative in ["issues", "specs", "workspace"]:
                (root / relative).mkdir()
            for relative in ["inbox.md", "opportunities.md", "roadmap.md", "dashboard.md"]:
                (root / "workspace" / relative).write_text("# Test\n", encoding="utf-8")
            project_memory.apply_memory_plan(project_memory.build_memory_plan(root, dry_run=False))
            project_memory.create_memory_entry(
                root,
                kind="decision",
                title="Broken source",
                source_artifacts=["specs/missing/spec.md"],
            )

            result = validate_project_artifacts.validate_project(root)

            self.assertFalse(result["valid"])
            self.assertIn("memory/decisions/", "\n".join(result["errors"]))
            self.assertIn("broken source_artifacts link: specs/missing/spec.md", "\n".join(result["errors"]))


if __name__ == "__main__":
    unittest.main()
