import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_module(name, relative_path):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


project_promote = load_module("project_promote", "scripts/project_promote.py")


DECISION_RECORD = """---
id: 2026-07-06-use-widget-cache
kind: decision
title: Use Widget Cache
source_artifacts: [scripts/widget.py, commands/product-widget.md]
supersedes: []
superseded_by: []
date: 2026-07-06
summary: Cache widget lookups to cut latency.
retrieval_trigger: when widget latency or cache invalidation comes up
rationale: Uncached lookups dominate p95 latency; a repo-local cache is the cheapest fix.
reversal_conditions: If cache staleness causes correctness bugs, drop the cache.
---

# Use Widget Cache

## Summary

Cache widget lookups to cut latency.
"""


def make_project(tmp, existing_issues=("001-old-thing.md", "007-newer-thing.md")):
    root = Path(tmp)
    (root / "issues").mkdir(parents=True, exist_ok=True)
    for name in existing_issues:
        (root / "issues" / name).write_text(f"# Issue: `{name[:-3]}`\n", encoding="utf-8")
    template_dst = root / "templates" / "issues" / "issue.md"
    template_dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ROOT / "templates" / "issues" / "issue.md", template_dst)
    (root / "memory" / "decisions").mkdir(parents=True, exist_ok=True)
    return root


def write_record(root, text=DECISION_RECORD, name="2026-07-06-use-widget-cache.md"):
    path = root / "memory" / "decisions" / name
    path.write_text(text, encoding="utf-8")
    return path


class PromoteDecisionEndToEndTests(unittest.TestCase):
    def test_promote_decision_record_creates_issue_and_backlinks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = make_project(tmp)
            record = write_record(root)
            original = record.read_text(encoding="utf-8")

            plan = project_promote.build_promotion_plan(root, record, today="2026-07-06")
            self.assertTrue(plan["ok"], plan["errors"])
            result = project_promote.apply_promotion_plan(plan)

            issue_path = Path(result["issue_path"])
            self.assertEqual(issue_path.name, "008-use-widget-cache.md")
            issue_text = issue_path.read_text(encoding="utf-8")

            # Prefilled from the record.
            self.assertIn("# Issue 008-use-widget-cache: Use Widget Cache", issue_text)
            self.assertIn("Cache widget lookups to cut latency.", issue_text)
            self.assertIn("**Status: backlog**", issue_text)
            self.assertIn("**Priority: p2**", issue_text)
            self.assertIn("- Type: promoted record", issue_text)
            self.assertIn("- Link: `memory/decisions/2026-07-06-use-widget-cache.md`", issue_text)
            self.assertIn("- Promoted-from: `2026-07-06-use-widget-cache`", issue_text)

            # The three AI-first sections are present and populated/TODO-marked.
            self.assertIn("## Verification", issue_text)
            self.assertIn("## Entry Points", issue_text)
            self.assertIn("## Scope Fence", issue_text)
            self.assertIn("TODO(blocking-execution)", issue_text)  # verification underivable
            self.assertIn("`scripts/widget.py`", issue_text)  # entry points from source_artifacts
            self.assertIn("rationale", issue_text.lower())  # scope fence seeded from rationale
            self.assertNotIn("{{", issue_text)  # no unfilled placeholders

            # Record gained promoted_to after superseded_by; rest byte-identical.
            updated = record.read_text(encoding="utf-8")
            self.assertIn("superseded_by: []\npromoted_to: 008-use-widget-cache\n", updated)
            self.assertEqual(updated.replace("promoted_to: 008-use-widget-cache\n", "", 1), original)

    def test_id_auto_increment_uses_max_existing_number(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = make_project(tmp, existing_issues=("003-a.md", "042-b.md", "017-c.md"))
            record = write_record(root)
            plan = project_promote.build_promotion_plan(root, record, today="2026-07-06")
            self.assertTrue(plan["ok"])
            self.assertEqual(plan["issue_id"], "043-use-widget-cache")

    def test_explicit_issue_id_number_is_padded_and_slugged(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = make_project(tmp)
            record = write_record(root)
            plan = project_promote.build_promotion_plan(root, record, issue_id="90", today="2026-07-06")
            self.assertTrue(plan["ok"])
            self.assertEqual(plan["issue_id"], "090-use-widget-cache")


class PromoteRefusalTests(unittest.TestCase):
    def test_already_promoted_record_is_refused_without_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = make_project(tmp)
            text = DECISION_RECORD.replace(
                "superseded_by: []\n", "superseded_by: []\npromoted_to: 099-existing\n"
            )
            record = write_record(root, text=text)
            plan = project_promote.build_promotion_plan(root, record, today="2026-07-06")
            self.assertFalse(plan["ok"])
            self.assertTrue(any("already promoted" in e for e in plan["errors"]))
            self.assertEqual(record.read_text(encoding="utf-8"), text)
            self.assertEqual(sorted(p.name for p in (root / "issues").glob("*.md")),
                             ["001-old-thing.md", "007-newer-thing.md"])

    def test_missing_frontmatter_is_refused_with_reason(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = make_project(tmp)
            record = write_record(root, text="# Bare Note\n\nNo fences here.\n")
            plan = project_promote.build_promotion_plan(root, record, today="2026-07-06")
            self.assertFalse(plan["ok"])
            self.assertTrue(any("no YAML frontmatter" in e for e in plan["errors"]))

    def test_existing_issue_file_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = make_project(tmp)
            record = write_record(root)
            (root / "issues" / "008-use-widget-cache.md").write_text("# taken\n", encoding="utf-8")
            # Auto-increment would skip past the clash, so pin the id.
            plan = project_promote.build_promotion_plan(root, record, issue_id="008", today="2026-07-06")
            self.assertFalse(plan["ok"])
            self.assertTrue(any("already exists" in e for e in plan["errors"]))

    def test_apply_refuses_failed_plan(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = make_project(tmp)
            record = write_record(root, text="no frontmatter\n")
            plan = project_promote.build_promotion_plan(root, record, today="2026-07-06")
            with self.assertRaises(ValueError):
                project_promote.apply_promotion_plan(plan)


class PromoteDryRunTests(unittest.TestCase):
    def test_dry_run_cli_prints_plan_json_and_writes_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = make_project(tmp)
            record = write_record(root)
            before = record.read_text(encoding="utf-8")

            import contextlib
            import io
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                code = project_promote.main([str(root), "--record", str(record)])

            self.assertEqual(code, 0)
            plan = json.loads(out.getvalue())
            self.assertTrue(plan["dry_run"])
            self.assertEqual(plan["issue_id"], "008-use-widget-cache")
            self.assertNotIn("issue_content", plan)
            self.assertFalse((root / "issues" / "008-use-widget-cache.md").exists())
            self.assertEqual(record.read_text(encoding="utf-8"), before)

    def test_dry_run_cli_reports_missing_frontmatter_refusal(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = make_project(tmp)
            record = write_record(root, text="just prose\n")

            import contextlib
            import io
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                code = project_promote.main([str(root), "--record", str(record)])

            self.assertEqual(code, 1)
            plan = json.loads(out.getvalue())
            self.assertFalse(plan["ok"])
            self.assertTrue(any("no YAML frontmatter" in e for e in plan["errors"]))
            self.assertEqual(record.read_text(encoding="utf-8"), "just prose\n")


class PromoteOtherKindsTests(unittest.TestCase):
    """Kinds only differ in the frontmatter `kind` value — shared helper."""

    def _promote_kind(self, kind):
        with tempfile.TemporaryDirectory() as tmp:
            root = make_project(tmp)
            text = (
                "---\n"
                f"id: 2026-07-06-{kind}-sample\n"
                f"kind: {kind}\n"
                f"title: Sample {kind.capitalize()} Record\n"
                "date: 2026-07-06\n"
                f"summary: A {kind} record worth promoting.\n"
                "retrieval_trigger: when this subject reappears\n"
                "---\n"
                "\n"
                f"# Sample {kind.capitalize()} Record\n"
            )
            record = write_record(root, text=text, name=f"2026-07-06-{kind}-sample.md")
            plan = project_promote.build_promotion_plan(root, record, today="2026-07-06")
            self.assertTrue(plan["ok"], plan["errors"])
            self.assertEqual(plan["kind"], kind)
            project_promote.apply_promotion_plan(plan)

            issue_text = Path(plan["issue_path"]).read_text(encoding="utf-8")
            self.assertIn(f"A {kind} record worth promoting.", issue_text)
            self.assertIn("- Promoted-from: `2026-07-06-" + kind + "-sample`", issue_text)
            # No derivable fields → all three AI sections carry the TODO marker.
            self.assertEqual(issue_text.count("TODO(blocking-execution)"), 6)

            updated = record.read_text(encoding="utf-8")
            self.assertIn(f"promoted_to: {plan['issue_id']}\n", updated)
            # promoted_to sits at the end of the frontmatter (no superseded_by).
            self.assertIn(f"retrieval_trigger: when this subject reappears\npromoted_to: {plan['issue_id']}\n---\n", updated)

    def test_promote_inbox_record(self):
        self._promote_kind("inbox")

    def test_promote_memory_record(self):
        self._promote_kind("memory")

    def test_promote_knowledge_record(self):
        self._promote_kind("knowledge")


if __name__ == "__main__":
    unittest.main()
