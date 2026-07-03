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

    def test_create_memory_entry_supports_depends_on_and_references(self):
        project_memory = load_module("project_memory", "scripts/project_memory.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project_memory.apply_memory_plan(project_memory.build_memory_plan(root, dry_run=False))

            result = project_memory.create_memory_entry(
                root,
                kind="decision",
                title="Caching Strategy",
                depends_on=["decision-git-canonical-memory"],
                references=["specs/034-memory-capture-and-sync-workflow/spec.md"],
            )

            entry_path = root / result["path"]
            text = entry_path.read_text(encoding="utf-8")
            metadata, _ = project_memory.parse_frontmatter(text)

            self.assertEqual(project_memory.parse_list_value(metadata.get("depends_on", "[]")), ["decision-git-canonical-memory"])
            self.assertEqual(project_memory.parse_list_value(metadata.get("references", "[]")), ["specs/034-memory-capture-and-sync-workflow/spec.md"])

    def test_generate_memory_graph_renders_mermaid(self):
        project_memory = load_module("project_memory", "scripts/project_memory.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project_memory.apply_memory_plan(project_memory.build_memory_plan(root, dry_run=False))

            # Create node 1
            project_memory.create_memory_entry(
                root,
                kind="decision",
                title="Git Memory Base",
                summary="Base decision",
            )
            # Create node 2 with relationship to node 1
            # The slugify name of Git Memory Base will be YYYY-MM-DD-git-memory-base
            today = project_memory.date.today().isoformat()
            base_node_id = f"{today}-git-memory-base"

            project_memory.create_memory_entry(
                root,
                kind="decision",
                title="SQLite Cache",
                summary="Cache decision",
                depends_on=[base_node_id],
            )

            graph = project_memory.generate_memory_graph(root)

            self.assertIn("flowchart TD", graph)
            self.assertIn("classDef decision fill:#e1f5fe,stroke:#0288d1,stroke-width:2px;", graph)
            self.assertIn("depends_on", graph)
            self.assertIn("sqlite_cache", graph.lower())
            self.assertIn("sqlite_cache", graph.lower())
            self.assertIn("git_memory_base", graph.lower())

    def test_parse_frontmatter_reads_yaml_block_list(self):
        project_memory = load_module("project_memory", "scripts/project_memory.py")
        text = (
            "---\n"
            "id: x\n"
            "references:\n"
            '  - "memory/evidence/a.md"\n'
            '  - "memory/evidence/b.md"\n'
            "---\n"
            "body\n"
        )
        metadata, _ = project_memory.parse_frontmatter(text)
        self.assertEqual(
            project_memory.parse_list_value(metadata.get("references", "[]")),
            ["memory/evidence/a.md", "memory/evidence/b.md"],
        )

    def test_normalize_target_drops_urls_and_strips_path(self):
        project_memory = load_module("project_memory", "scripts/project_memory.py")
        self.assertIsNone(project_memory._normalize_target("https://example.com/x"))
        self.assertIsNone(project_memory._normalize_target("http://example.com"))
        self.assertEqual(
            project_memory._normalize_target("memory/evidence/2026-06-27-x.md"),
            "2026-06-27-x",
        )
        self.assertEqual(project_memory._normalize_target("plain-id"), "plain-id")

    def test_render_dashboard_html_embeds_graph(self):
        project_memory = load_module("project_memory", "scripts/project_memory.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project_memory.apply_memory_plan(project_memory.build_memory_plan(root, dry_run=False))
            project_memory.create_memory_entry(root, kind="decision", title="Base D", summary="b")
            today = project_memory.date.today().isoformat()
            base = f"{today}-base-d"
            project_memory.create_memory_entry(
                root, kind="decision", title="Next D", summary="n", depends_on=[base]
            )
            html = project_memory.render_dashboard_html(root)
            self.assertIn("cytoscape.min.js", html)
            self.assertIn("const ELEMENTS =", html)
            self.assertIn(base, html)
            self.assertIn('"rel": "depends_on"', html)
            self.assertIn('edge[rel="references"]', html)

    def test_reject_memory_candidate(self):
        project_memory = load_module("project_memory", "scripts/project_memory.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project_memory.apply_memory_plan(project_memory.build_memory_plan(root, dry_run=False))

            candidate = project_memory.create_memory_candidate(
                root,
                kind="decision",
                title="Discardable Choice",
                summary="Temporary decision to reject."
            )
            candidate_path = root / candidate["path"]
            self.assertTrue(candidate_path.exists())

            # Reject
            reject_result = project_memory.reject_memory_candidate(root, candidate["id"])
            self.assertIsNotNone(reject_result)
            self.assertEqual(reject_result["status"], "rejected")
            self.assertFalse(candidate_path.exists())

    def test_capture_to_memory_candidate(self):
        project_memory = load_module("project_memory", "scripts/project_memory.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project_memory.apply_memory_plan(project_memory.build_memory_plan(root, dry_run=False))

            # Create dummy external file
            external_file = root / "dummy_doc.md"
            external_file.write_text("""---
title: External Benchmark Findings
tags: [external, benchmarking]
summary: Benchmark results from external system.
evidence: External performance metrics were verified.
---
# Benchmark Notes
More detail contents here.
""", encoding="utf-8")

            # Capture
            candidate = project_memory.capture_to_memory_candidate(
                root,
                kind="evidence",
                source_file=external_file,
            )
            self.assertIsNotNone(candidate)
            candidate_path = root / candidate["path"]
            self.assertTrue(candidate_path.exists())

            text = candidate_path.read_text(encoding="utf-8")
            metadata, _ = project_memory.parse_frontmatter(text)
            self.assertEqual(metadata.get("title"), "External Benchmark Findings")
            self.assertEqual(metadata.get("kind"), "evidence")
            self.assertEqual(metadata.get("status"), "candidate")
            self.assertIn("benchmarking", project_memory.parse_list_value(metadata.get("tags", "[]")))

    def test_list_memory_candidates_stale_pruning(self):
        project_memory = load_module("project_memory", "scripts/project_memory.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project_memory.apply_memory_plan(project_memory.build_memory_plan(root, dry_run=False))

            # Candidate 1: Fresh
            fresh_candidate = project_memory.create_memory_candidate(
                root, kind="decision", title="Fresh Choice", summary="Fresh"
            )
            fresh_path = root / fresh_candidate["path"]

            # Candidate 2: Stale (Older than 14 days)
            stale_candidate = project_memory.create_memory_candidate(
                root, kind="decision", title="Stale Choice", summary="Stale"
            )
            stale_path = root / stale_candidate["path"]

            # Set mtime back 15 days
            import os
            import time
            back_15_days = time.time() - (15 * 24 * 3600)
            os.utime(stale_path, (back_15_days, back_15_days))

            # Listing should prune stale and only keep fresh
            candidates = project_memory.list_memory_candidates(root)
            self.assertEqual(len(candidates), 1)
            self.assertEqual(candidates[0]["id"], fresh_candidate["id"])
            self.assertFalse(stale_path.exists())
            self.assertTrue(fresh_path.exists())

    def test_workflow_release_auto_capture(self):
        project_workflow = load_module("project_workflow", "scripts/project_workflow.py")
        project_memory = load_module("project_memory", "scripts/project_memory.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project_memory.apply_memory_plan(project_memory.build_memory_plan(root, dry_run=False))
            project_workflow.apply_workflow_plan(project_workflow.build_workflow_plan(root, dry_run=False))

            # Record a release record
            result = project_workflow.create_workflow_record(
                root,
                issue_id="040-test-auto",
                state="released",
                owner="Tester",
                next_command="product:status"
            )

            # Verification of candidate generated automatically
            candidates = project_memory.list_memory_candidates(root)
            self.assertEqual(len(candidates), 1)
            self.assertIn("040-test-auto", candidates[0]["id"])
            self.assertEqual(candidates[0]["kind"], "decision")


    def test_issue_panel_renders_existing_artifacts_only(self):
        project_memory = load_module("project_memory", "scripts/project_memory.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "issues").mkdir()
            (root / "specs" / "046-foo").mkdir(parents=True)
            (root / "issues" / "046-foo.md").write_text("# Issue 046\nStatus: done\n", encoding="utf-8")
            (root / "specs" / "046-foo" / "spec.md").write_text(
                "# Spec heading\n\n```mermaid\nflowchart TD\n A-->B\n```\n", encoding="utf-8")
            # plan.md absent on purpose — must not be stubbed.

            html = project_memory.render_issue_panel(root, "046-foo")

            self.assertIn("Spec heading", html)
            self.assertIn("# Issue 046", html)
            self.assertIn("cdnjs.cloudflare.com/ajax/libs/marked/12.0.2", html)
            self.assertIn("mermaid@11.4.1", html)
            self.assertNotIn('"label": "Plan"', html)

    def test_issue_panel_resolves_bare_number_same_as_slug(self):
        project_memory = load_module("project_memory", "scripts/project_memory.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "specs" / "047-bar").mkdir(parents=True)
            (root / "specs" / "047-bar" / "spec.md").write_text("# Bar spec\n", encoding="utf-8")

            slug_num, arts_num = project_memory._collect_issue_artifacts(root, "047")
            slug_full, arts_full = project_memory._collect_issue_artifacts(root, "047-bar")

            self.assertEqual(slug_num, "047-bar")
            self.assertEqual(slug_num, slug_full)
            self.assertEqual([a["name"] for a in arts_num], [a["name"] for a in arts_full])

    def test_issue_panel_degrades_when_no_artifacts(self):
        project_memory = load_module("project_memory", "scripts/project_memory.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            html = project_memory.render_issue_panel(root, "099-nope")

            self.assertIn("No artifacts yet", html)
            self.assertIn("099-nope", html)

    def test_collect_issue_graph_parses_status_and_supersedes(self):
        project_memory = load_module("project_memory", "scripts/project_memory.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "issues").mkdir()
            (root / "issues" / "041-old.md").write_text(
                "# Issue: `041-old`\n\n**Status: superseded-by-042** — created.\n", encoding="utf-8")
            (root / "issues" / "042-new.md").write_text(
                "# Issue: `042-new`\n\n**Status: done** — created. Supersedes `041-old`.\n", encoding="utf-8")
            (root / "issues" / "043-todo.md").write_text(
                "# Issue: `043-todo`\n\n**Status: backlog** — created.\n", encoding="utf-8")

            nodes, edges = project_memory._collect_issue_graph(root)

            self.assertEqual(nodes["041-old"]["status"], "superseded")
            self.assertEqual(nodes["042-new"]["status"], "done")
            self.assertEqual(nodes["043-todo"]["status"], "backlog")
            # both the prose and the superseded-by line resolve to ONE deduped edge
            self.assertEqual(edges, [("042-new", "041-old", "supersedes")])

    def test_issue_linked_memory_maps_and_tolerates_empty(self):
        project_memory = load_module("project_memory", "scripts/project_memory.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project_memory.apply_memory_plan(project_memory.build_memory_plan(root, dry_run=False))
            project_memory.create_memory_entry(
                root, kind="evidence", title="Bench", summary="b", issue_id="046-foo")

            mapping = project_memory._issue_linked_memory(root)

            self.assertIn("046-foo", mapping)
            self.assertEqual(mapping["046-foo"][0]["kind"], "evidence")
            self.assertEqual(mapping.get("999-none", []), [])

    def test_issue_elements_group_issues_into_goal_boxes(self):
        project_memory = load_module("project_memory", "scripts/project_memory.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "issues").mkdir()
            (root / "issues" / "045-a.md").write_text(
                "# Issue: `045-a`\n\n**Status: active** — Part of goal `visual-workbench`.\n", encoding="utf-8")
            (root / "issues" / "010-b.md").write_text(
                "# Issue: `010-b`\n\n**Status: done** — no goal marker here.\n", encoding="utf-8")

            elements, n, _ = project_memory._issue_elements(root)

            goal_boxes = {e["data"]["label"] for e in elements if e["data"].get("isgoal")}
            self.assertIn("visual-workbench", goal_boxes)
            self.assertIn("(기타)", goal_boxes)
            child = next(e for e in elements if e["data"].get("id") == "045-a")
            self.assertEqual(child["data"]["parent"], "goal:visual-workbench")
            self.assertIn("position", child)
            self.assertEqual(n, 2)

    def test_collect_issue_table_includes_artifacts_flags_and_memory(self):
        project_memory = load_module("project_memory", "scripts/project_memory.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "issues").mkdir()
            (root / "specs" / "056-dashboard").mkdir(parents=True)
            (root / "issues" / "056-dashboard.md").write_text(
                "# Issue: `056-dashboard`\n\n"
                "**Status: active** — Part of goal `visual-workbench`.\n\n"
                "## Next Command\n\n"
                "`/product:execute 056-dashboard`\n",
                encoding="utf-8",
            )
            (root / "issues" / "057-review.md").write_text(
                "# Issue: `057-review`\n\n"
                "**Status: backlog** — created.\n\n",
                encoding="utf-8",
            )
            (root / "specs" / "056-dashboard" / "spec.md").write_text("# Spec\n", encoding="utf-8")
            (root / "specs" / "056-dashboard" / "spec.ko.md").write_text("# 명세\n", encoding="utf-8")
            (root / "specs" / "056-dashboard" / "plan.md").write_text("# Plan\n", encoding="utf-8")
            project_memory.apply_memory_plan(project_memory.build_memory_plan(root, dry_run=False))
            project_memory.create_memory_entry(
                root, kind="decision", title="Dash choice", summary="s", issue_id="056-dashboard")

            rows = project_memory._collect_issue_table(root)
            by_id = {row["id"]: row for row in rows}

            self.assertEqual([row["id"] for row in rows], ["056-dashboard", "057-review"])
            self.assertEqual(by_id["056-dashboard"]["number"], 56)
            self.assertEqual(by_id["056-dashboard"]["status"], "active")
            self.assertEqual(by_id["056-dashboard"]["goal"], "visual-workbench")
            self.assertEqual(by_id["056-dashboard"]["next_command"], "/product:execute 056-dashboard")
            self.assertEqual(by_id["056-dashboard"]["href"], "issue-056-dashboard.html")
            self.assertTrue(by_id["056-dashboard"]["artifact_coverage"]["spec"])
            self.assertTrue(by_id["056-dashboard"]["artifact_coverage"]["spec_ko"])
            self.assertTrue(by_id["056-dashboard"]["artifact_coverage"]["plan"])
            self.assertEqual(by_id["056-dashboard"]["linked_memory_count"], 1)
            self.assertIn("no_review", by_id["056-dashboard"]["attention_flags"])
            self.assertIn("missing_spec", by_id["057-review"]["attention_flags"])
            self.assertIn("no_next", by_id["057-review"]["attention_flags"])

    def test_render_project_view_has_issue_db_tab_and_controls(self):
        project_memory = load_module("project_memory", "scripts/project_memory.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "issues").mkdir()
            (root / "issues" / "042-new.md").write_text(
                "# Issue: `042-new`\n\n**Status: done** — created.\n", encoding="utf-8")
            project_memory.apply_memory_plan(project_memory.build_memory_plan(root, dry_run=False))

            html = project_memory.render_project_view(root)

            self.assertIn('id="issue-db"', html)
            self.assertIn('id="cy-issues"', html)
            self.assertIn('id="cy-memory"', html)
            self.assertIn("이슈 DB", html)
            self.assertIn("이슈 그래프", html)
            self.assertIn("지식 그래프", html)
            self.assertIn("const ISSUE_ROWS =", html)
            self.assertIn("const ISSUE_ELEMENTS =", html)
            self.assertIn('id="issue-search"', html)
            self.assertIn('data-view="missing"', html)
            self.assertIn('id="issue-sort"', html)
            self.assertIn("issue-042-new.html", html)

    def test_issue_panel_includes_linked_memory_section_only_when_present(self):
        project_memory = load_module("project_memory", "scripts/project_memory.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "issues").mkdir()
            (root / "specs" / "046-foo").mkdir(parents=True)
            (root / "issues" / "046-foo.md").write_text("# Issue 046\n", encoding="utf-8")
            (root / "specs" / "046-foo" / "spec.md").write_text("# Spec\n", encoding="utf-8")
            project_memory.apply_memory_plan(project_memory.build_memory_plan(root, dry_run=False))

            html_absent = project_memory.render_issue_panel(root, "046-foo")
            self.assertEqual("[]", _linked_blob(html_absent))

            project_memory.create_memory_entry(
                root, kind="decision", title="Why foo", summary="s", issue_id="046-foo")
            html_present = project_memory.render_issue_panel(root, "046-foo")
            self.assertIn("Why foo", _linked_blob(html_present))
            self.assertIn("연결된 지식", html_present)


    def test_ko_sidecar_attached_and_not_listed_separately(self):
        project_memory = load_module("project_memory", "scripts/project_memory.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "specs" / "049-b").mkdir(parents=True)
            (root / "specs" / "049-b" / "spec.md").write_text("# Spec EN\n", encoding="utf-8")
            (root / "specs" / "049-b" / "spec.ko.md").write_text("# 명세 한글\n", encoding="utf-8")
            (root / "specs" / "049-b" / "plan.md").write_text("# Plan EN\n", encoding="utf-8")  # no sidecar

            _slug, arts = project_memory._collect_issue_artifacts(root, "049-b")
            names = [a["name"] for a in arts]
            spec = next(a for a in arts if a["name"] == "spec.md")
            plan = next(a for a in arts if a["name"] == "plan.md")

            self.assertNotIn("spec.ko.md", names)        # sidecar is not its own artifact
            self.assertEqual(spec["ko"], "# 명세 한글\n")  # attached to its EN artifact
            self.assertIsNone(plan["ko"])                 # no sidecar → null (EN fallback)

    def test_issue_panel_toggle_only_when_sidecar_exists(self):
        project_memory = load_module("project_memory", "scripts/project_memory.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "specs" / "049-b").mkdir(parents=True)
            (root / "specs" / "049-b" / "spec.md").write_text("# Spec\n", encoding="utf-8")

            without = project_memory.render_issue_panel(root, "049-b")
            self.assertIn('"ko": null', without)              # ko slot present, empty
            self.assertNotIn("한글 본문 내용", without)        # no Korean sidecar payload

            (root / "specs" / "049-b" / "spec.ko.md").write_text("# 한글 본문 내용\n", encoding="utf-8")
            with_ko = project_memory.render_issue_panel(root, "049-b")
            self.assertIn("한글 본문 내용", with_ko)          # Korean payload present → client offers toggle

    def test_list_memory_ids_returns_all_and_filters_by_kind(self):
        project_memory = load_module("project_memory", "scripts/project_memory.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project_memory.apply_memory_plan(project_memory.build_memory_plan(root, dry_run=False))
            project_memory.create_memory_entry(root, kind="decision", title="Dee", summary="d")
            project_memory.create_memory_entry(root, kind="evidence", title="Eee", summary="e")

            all_ids = project_memory.list_memory_ids(root)
            decisions = project_memory.list_memory_ids(root, kind="decision")

            self.assertEqual({e["kind"] for e in all_ids}, {"decision", "evidence"})
            self.assertTrue(all("id" in e and "title" in e for e in all_ids))
            self.assertEqual([e["kind"] for e in decisions], ["decision"])

    def test_isolated_memory_entries_flags_only_unlinked(self):
        project_memory = load_module("project_memory", "scripts/project_memory.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project_memory.apply_memory_plan(project_memory.build_memory_plan(root, dry_run=False))
            project_memory.create_memory_entry(root, kind="note", title="Lonely", summary="x")
            project_memory.create_memory_entry(
                root, kind="decision", title="Linked", summary="y", issue_id="045-foo")
            base = f"{project_memory.date.today().isoformat()}-lonely"

            isolated = project_memory.isolated_memory_entries(root)
            ids = [e["id"] for e in isolated]

            self.assertIn(base, ids)
            self.assertNotIn(f"{project_memory.date.today().isoformat()}-linked", ids)

    def test_doctor_surfaces_isolated_as_soft_hint_without_failing(self):
        project_memory = load_module("project_memory", "scripts/project_memory.py")
        project_doctor = load_module("project_doctor", "scripts/project_doctor.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project_memory.apply_memory_plan(project_memory.build_memory_plan(root, dry_run=False))
            project_memory.create_memory_entry(root, kind="note", title="Lonely", summary="x")

            result = project_doctor.inspect_project(root, include_preflight=False)

            self.assertGreaterEqual(len(result["memory"]["isolated"]), 1)
            self.assertTrue(any("isolated" in r for r in result["recommendation"]))
            # the hint must never be an error gate — exit code keys are unaffected
            self.assertIn("initialized", result["memory"])


def _linked_blob(html):
    import re
    m = re.search(r"const LINKED = (\[.*?\]);", html, re.S)
    return m.group(1).replace("<\\/", "</") if m else ""


if __name__ == "__main__":
    unittest.main()
