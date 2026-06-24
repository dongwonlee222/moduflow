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

    def test_doctor_reports_memory_missing_and_initialized(self):
        project_doctor = load_module("project_doctor", "scripts/project_doctor.py")
        project_memory = load_module("project_memory", "scripts/project_memory.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            missing = project_doctor.missing_memory_paths(root)
            self.assertIn("memory/index.md", missing)

            project_memory.apply_memory_plan(project_memory.build_memory_plan(root, dry_run=False))

            self.assertEqual(project_doctor.missing_memory_paths(root), [])


if __name__ == "__main__":
    unittest.main()
