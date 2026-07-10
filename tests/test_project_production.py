import importlib.util
import json
import re
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_module(name, relative_path):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


production = load_module("project_production", "scripts/project_production.py")


VALID_RECORD = """---
schema: moduflow.production-record.v1
id: 2026-07-10-summer-banner
kind: production_record
title: Summer banner
issue_id: 123-summer-event
deliverable_type: banner
channel: home-popup
audiences: [customer, internal]
variant: mobile
lifecycle: published
owner: marketing
created: 2026-07-10
updated: 2026-07-10
playbook_refs: [banner-mobile]
retrieval_trigger: when creating a mobile banner
---

## Artifacts

- [Final](marketing/banner-final.png) — final · customer

## Source Inputs

- Event brief

## Decisions

- Use a black card layout for text stability.

## Failed Attempts

- Small Korean text inside the phone image broke.

## Reusable Patterns

- Keep customer copy outside generated imagery.

## Do Not Repeat

- Do not generate final Korean text as pixels.

## Playbook Updates

- banner-mobile — candidate

## External Copy

Charge now to receive the event benefit.

## Internal Reporting Copy

This variant tests mobile conversion.
"""


VALID_PLAYBOOK = """---
schema: moduflow.playbook.v1
id: banner-mobile
kind: playbook
title: Mobile banner playbook
applies_to_types: [banner, home-popup]
applies_to_channels: [home-popup]
audiences: [customer]
version: 1.0
status: approved
approved_by: Dongwon Lee
approved_at: 2026-07-10
source_records: [2026-07-10-summer-banner]
review_after: 2026-10-10
superseded_by: []
created: 2026-07-10
updated: 2026-07-10
---

## Reusable Patterns

- Use a black card layout.

## Do Not Repeat

- Do not render small Korean text in generated images.

## Approved Copy Blocks

- Charge now to receive the event benefit.

## Approved Structures

- Benefit, condition, call to action.

## Evidence

- 2026-07-10-summer-banner

## Revision History

- 2026-07-10 approved by Dongwon Lee.
"""


PRESS_RECORD = VALID_RECORD.replace(
    "id: 2026-07-10-summer-banner", "id: 2026-07-10-partnership-press-release"
).replace("title: Summer banner", "title: Partnership press release").replace(
    "issue_id: 123-summer-event", "issue_id: 124-partnership"
).replace("deliverable_type: banner", "deliverable_type: press-release").replace(
    "channel: home-popup", "channel: media"
).replace("audiences: [customer, internal]", "audiences: [journalist, internal]").replace(
    "variant: mobile", "variant: distribution"
).replace("playbook_refs: [banner-mobile]", "playbook_refs: []").replace(
    "retrieval_trigger: when creating a mobile banner",
    "retrieval_trigger: when drafting an external press release",
).replace("marketing/banner-final.png", "documents/press-release-final.md").replace(
    "- banner-mobile — candidate", ""
).replace("Small Korean text inside the phone image broke.", "Advertising tone weakened news value.")


def write_project(root, humans=None):
    (root / "memory" / "production-records").mkdir(parents=True)
    (root / "playbooks").mkdir(parents=True)
    if humans is not None:
        config = root / ".moduflow" / "humans.json"
        config.parent.mkdir(parents=True)
        config.write_text(json.dumps({"humans": humans}), encoding="utf-8")


def write_record(root, content=VALID_RECORD):
    record_id = re.search(r"^id:\s*(.+)$", content, re.MULTILINE).group(1)
    path = root / "memory" / "production-records" / f"{record_id}.md"
    path.write_text(content, encoding="utf-8")
    return path


def write_playbook(root, content=VALID_PLAYBOOK):
    path = root / "playbooks" / "banner-mobile.md"
    path.write_text(content, encoding="utf-8")
    return path


def write_issue(root, issue_id):
    path = root / "issues" / f"{issue_id}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"# Issue {issue_id}\n\n**Status: done** — completed.\n", encoding="utf-8")
    return path


class ProjectProductionParserTests(unittest.TestCase):
    def test_parse_record_normalizes_metadata_sections_and_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_project(root)
            path = write_record(root)

            record = production.parse_production_record(root, path)

            self.assertEqual(record["deliverable_type"], "banner")
            self.assertEqual(record["audiences"], ["customer", "internal"])
            self.assertEqual(record["variant"], "mobile")
            self.assertEqual(record["artifacts"][0]["target"], "marketing/banner-final.png")
            self.assertEqual(record["playbook_updates"], [
                {"playbook_id": "banner-mobile", "state": "candidate"}
            ])
            self.assertNotEqual(
                record["sections"]["External Copy"],
                record["sections"]["Internal Reporting Copy"],
            )

    def test_parse_record_requires_nine_sections_in_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_project(root)
            path = write_record(root, VALID_RECORD.replace("## Failed Attempts\n", ""))

            with self.assertRaisesRegex(ValueError, "missing section: Failed Attempts"):
                production.parse_production_record(root, path)

            path = write_record(
                root,
                VALID_RECORD.replace(
                    "## Source Inputs\n\n- Event brief\n\n## Decisions\n\n- Use a black card layout for text stability.",
                    "## Decisions\n\n- Use a black card layout for text stability.\n\n## Source Inputs\n\n- Event brief",
                ),
            )
            with self.assertRaisesRegex(ValueError, "out of order"):
                production.parse_production_record(root, path)

    def test_parse_playbook_normalizes_approval_and_sources(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_project(root)
            playbook = production.parse_playbook(root, write_playbook(root))

            self.assertEqual(playbook["status"], "approved")
            self.assertEqual(playbook["deliverable_types"], ["banner", "home-popup"])
            self.assertEqual(playbook["channels"], ["home-popup"])
            self.assertEqual(playbook["version"], "1.0")
            self.assertEqual(playbook["approved_by"], "Dongwon Lee")
            self.assertEqual(playbook["source_records"], ["2026-07-10-summer-banner"])
            self.assertIn("Approved Copy Blocks", playbook["sections"])

    def test_list_functions_are_path_sorted_and_project_local(self):
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            first_root = Path(first)
            second_root = Path(second)
            write_project(first_root)
            write_project(second_root)
            write_record(first_root)
            write_playbook(first_root)

            self.assertEqual(
                [item["id"] for item in production.list_production_records(first_root)],
                ["2026-07-10-summer-banner"],
            )
            self.assertEqual(
                [item["id"] for item in production.list_playbooks(first_root)],
                ["banner-mobile"],
            )
            self.assertEqual(production.list_production_records(second_root), [])
            self.assertEqual(production.list_playbooks(second_root), [])


class ProjectProductionMutationTests(unittest.TestCase):
    def test_init_creates_only_missing_production_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            existing = root / "marketing" / "keep.txt"
            existing.parent.mkdir(parents=True)
            existing.write_text("keep", encoding="utf-8")

            result = production.apply_production_plan(
                production.build_production_plan(root, dry_run=False)
            )

            self.assertTrue((root / "memory" / "production-records").is_dir())
            self.assertTrue((root / "playbooks").is_dir())
            self.assertEqual(existing.read_text(encoding="utf-8"), "keep")
            self.assertNotIn("marketing/keep.txt", result["written"])

    def test_same_capture_key_returns_noop_then_update_required_without_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first = production.create_production_record(
                root,
                title="Summer banner",
                issue_id="123-summer-event",
                deliverable_type="banner",
                channel="home-popup",
                audiences=["customer"],
                lifecycle="draft",
                retrieval_trigger="when creating mobile banners",
                variant="mobile",
            )
            path = root / first["path"]

            same = production.create_production_record(
                root,
                title="Summer banner",
                issue_id="123-summer-event",
                deliverable_type="banner",
                channel="home-popup",
                audiences=["customer"],
                lifecycle="draft",
                retrieval_trigger="when creating mobile banners",
                variant="mobile",
            )
            self.assertEqual(same["action"], "noop")

            path.write_text(path.read_text(encoding="utf-8") + "\nHuman note\n", encoding="utf-8")
            changed = production.create_production_record(
                root,
                title="Summer banner",
                issue_id="123-summer-event",
                deliverable_type="banner",
                channel="home-popup",
                audiences=["customer"],
                lifecycle="draft",
                retrieval_trigger="when creating mobile banners",
                variant="mobile",
            )

            self.assertEqual(changed["action"], "update_required")
            self.assertIn("Human note", path.read_text(encoding="utf-8"))

    def test_same_day_and_title_with_different_source_gets_distinct_record(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first = production.create_production_record(
                root,
                title="Summer banner",
                issue_id="123-summer-event",
                deliverable_type="banner",
                channel="home-popup",
                audiences=["customer"],
                lifecycle="draft",
                retrieval_trigger="when creating banners",
            )
            second = production.create_production_record(
                root,
                title="Summer banner",
                issue_id="124-partner-event",
                deliverable_type="banner",
                channel="home-popup",
                audiences=["customer"],
                lifecycle="draft",
                retrieval_trigger="when creating partner banners",
            )

            self.assertEqual(first["action"], "created")
            self.assertEqual(second["action"], "created")
            self.assertNotEqual(first["path"], second["path"])
            self.assertEqual(len(production.list_production_records(root)), 2)

    def test_capture_requires_issue_or_source_context(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "issue_id or source_context"):
                production.create_production_record(
                    Path(tmp),
                    title="Banner",
                    deliverable_type="banner",
                    channel="home-popup",
                    audiences=["customer"],
                    lifecycle="draft",
                    retrieval_trigger="when creating banners",
                )


class ProjectProductionCliTests(unittest.TestCase):
    def test_cli_init_and_new_record_emit_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertEqual(production.main([str(root), "--init"]), 0)
            self.assertEqual(
                production.main(
                    [
                        str(root),
                        "--new-record",
                        "--title",
                        "Summer banner",
                        "--issue-id",
                        "123-summer-event",
                        "--type",
                        "banner",
                        "--channel",
                        "home-popup",
                        "--audience",
                        "customer",
                        "--lifecycle",
                        "draft",
                        "--retrieval-trigger",
                        "when creating banners",
                    ]
                ),
                0,
            )
            self.assertEqual(len(production.list_production_records(root)), 1)

    def test_cli_search_retrieve_and_validate_operations(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_project(root)
            write_issue(root, "123-summer-event")
            (root / "marketing").mkdir()
            (root / "marketing" / "banner-final.png").write_bytes(b"image")
            write_record(root, VALID_RECORD.replace("playbook_refs: [banner-mobile]", "playbook_refs: []").replace(
                "- banner-mobile — candidate", ""
            ))

            self.assertEqual(production.main([str(root), "--search", "small Korean text"]), 0)
            self.assertEqual(
                production.main(
                    [
                        str(root),
                        "--retrieve",
                        "--type",
                        "banner",
                        "--channel",
                        "home-popup",
                        "--audience",
                        "customer",
                    ]
                ),
                0,
            )
            self.assertEqual(production.main([str(root), "--validate"]), 0)

    def test_cli_usage_errors_return_two_without_system_exit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertEqual(production.main([]), 2)
            self.assertEqual(
                production.main(
                    [
                        str(root),
                        "--new-record",
                        "--title",
                        "Banner",
                        "--type",
                        "banner",
                        "--channel",
                        "home-popup",
                        "--audience",
                        "customer",
                        "--lifecycle",
                        "draft",
                        "--retrieval-trigger",
                        "when creating banners",
                    ]
                ),
                2,
            )


class ProjectProductionApprovalTests(unittest.TestCase):
    def test_approve_requires_exact_configured_human_and_source_record(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_project(root, humans=[{"name": "Dongwon Lee", "email": "webn77@gmail.com"}])
            write_record(root)
            candidate = VALID_PLAYBOOK.replace("status: approved", "status: candidate").replace(
                "approved_by: Dongwon Lee", "approved_by:"
            ).replace("approved_at: 2026-07-10", "approved_at:")
            write_playbook(root, candidate)

            with self.assertRaisesRegex(ValueError, "configured human"):
                production.decide_playbook_update(
                    root,
                    record_id="2026-07-10-summer-banner",
                    playbook_id="banner-mobile",
                    decision="approve",
                    approved_by="agent",
                    reason="looks good",
                    decided_at="2026-07-10",
                )

            result = production.decide_playbook_update(
                root,
                record_id="2026-07-10-summer-banner",
                playbook_id="banner-mobile",
                decision="approve",
                approved_by="Dongwon Lee",
                reason="validated on mobile",
                decided_at="2026-07-10",
            )
            self.assertEqual(result["status"], "approved")
            self.assertEqual(
                production.decide_playbook_update(
                    root,
                    record_id="2026-07-10-summer-banner",
                    playbook_id="banner-mobile",
                    decision="approve",
                    approved_by="Dongwon Lee",
                    reason="validated on mobile",
                    decided_at="2026-07-10",
                )["action"],
                "noop",
            )

    def test_reject_and_defer_append_audit_without_deleting_candidate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_project(root, humans=[{"name": "Dongwon Lee", "email": "webn77@gmail.com"}])
            record_path = write_record(root)
            candidate = VALID_PLAYBOOK.replace("status: approved", "status: candidate").replace(
                "approved_by: Dongwon Lee", "approved_by:"
            ).replace("approved_at: 2026-07-10", "approved_at:")
            playbook_path = write_playbook(root, candidate)

            for decision in ("reject", "defer"):
                result = production.decide_playbook_update(
                    root,
                    record_id="2026-07-10-summer-banner",
                    playbook_id="banner-mobile",
                    decision=decision,
                    approved_by="Dongwon Lee",
                    reason=f"{decision} for evidence",
                    decided_at="2026-07-10",
                )
                self.assertEqual(result["status"], "candidate")

            self.assertTrue(playbook_path.exists())
            self.assertIn("status: candidate", playbook_path.read_text(encoding="utf-8"))
            audit = record_path.read_text(encoding="utf-8")
            self.assertIn("banner-mobile — rejected", audit)
            self.assertIn("banner-mobile — deferred", audit)

    def test_approval_fails_without_human_configuration(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_project(root)
            write_record(root)
            write_playbook(root)
            with self.assertRaisesRegex(ValueError, "configured human"):
                production.decide_playbook_update(
                    root,
                    record_id="2026-07-10-summer-banner",
                    playbook_id="banner-mobile",
                    decision="approve",
                    approved_by="Dongwon Lee",
                    reason="approve",
                    decided_at="2026-07-10",
                )


class ProjectProductionSearchTests(unittest.TestCase):
    def test_search_filters_failures_patterns_and_audience_with_explicit_cap(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_project(root)
            write_record(root)
            write_record(root, PRESS_RECORD)

            result = production.search_production(
                root,
                "small Korean text",
                deliverable_type="banner",
                audience="customer",
                limit=1,
            )

            self.assertEqual(result["items"][0]["deliverable_type"], "banner")
            self.assertEqual(result["total_matches"], 1)
            self.assertFalse(result["truncated"])

    def test_search_reports_truncation_and_rejects_invalid_limit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_project(root)
            write_record(root)
            write_record(root, PRESS_RECORD)

            result = production.search_production(root, "copy", limit=1)
            self.assertEqual(result["total_matches"], 2)
            self.assertEqual(result["items"][0]["id"], "2026-07-10-partnership-press-release")
            self.assertTrue(result["truncated"])
            self.assertEqual(result["dropped_count"], 1)
            with self.assertRaisesRegex(ValueError, "positive"):
                production.search_production(root, "copy", limit=0)

    def test_retrieval_never_reads_sibling_project(self):
        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp)
            project_a, project_b = parent / "a", parent / "b"
            write_project(project_a)
            write_project(project_b)
            write_record(project_a)
            write_record(project_b, PRESS_RECORD)

            result = production.retrieve_production_context(
                project_a,
                deliverable_type="press-release",
                channel="media",
                audiences=["journalist"],
                limit=5,
            )
            self.assertEqual(result["items"], [])

    def test_retrieval_prioritizes_approved_playbook_over_record(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_project(root)
            write_record(root)
            write_playbook(root)

            result = production.retrieve_production_context(
                root,
                deliverable_type="banner",
                channel="home-popup",
                audiences=["customer"],
                limit=5,
            )
            self.assertEqual(result["items"][0]["kind"], "playbook")
            self.assertTrue(result["items"][0]["authoritative"])
            self.assertFalse(result["items"][1]["authoritative"])


class ProjectProductionValidationTests(unittest.TestCase):
    def test_validation_errors_on_missing_artifact_and_invalid_approval(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_project(root, humans=[{"name": "Dongwon Lee", "email": "webn77@gmail.com"}])
            write_issue(root, "123-summer-event")
            write_record(root, VALID_RECORD.replace("marketing/banner-final.png", "marketing/missing.png"))
            write_playbook(root, VALID_PLAYBOOK.replace("approved_by: Dongwon Lee", "approved_by: agent"))

            result = production.validate_production_project(root)

            self.assertTrue(any("missing artifact" in error for error in result["errors"]))
            self.assertTrue(any("approved_by" in error for error in result["errors"]))

    def test_validation_accepts_https_without_network_and_warns_absolute_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_project(root)
            write_issue(root, "123-summer-event")
            content = VALID_RECORD.replace(
                "- [Final](marketing/banner-final.png) — final · customer",
                "- [Remote](https://example.com/banner.png) — final · customer\n"
                "- [Local](/Users/example/banner.png) — source · internal",
            ).replace("playbook_refs: [banner-mobile]", "playbook_refs: []").replace(
                "- banner-mobile — candidate", ""
            )
            write_record(root, content)

            result = production.validate_production_project(root)

            self.assertFalse(any("https://" in error for error in result["errors"]))
            self.assertTrue(any("absolute artifact" in warning for warning in result["warnings"]))

    def test_validation_accepts_review_lifecycle_and_optional_owner(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_project(root)
            write_issue(root, "123-summer-event")
            (root / "marketing").mkdir()
            (root / "marketing" / "banner-final.png").write_bytes(b"image")
            content = VALID_RECORD.replace("lifecycle: published", "lifecycle: review").replace(
                "owner: marketing\n", ""
            ).replace("playbook_refs: [banner-mobile]", "playbook_refs: []").replace(
                "- banner-mobile — candidate", ""
            )
            record = production.parse_production_record(root, write_record(root, content))
            result = production.validate_production_project(root)

            self.assertEqual(record["owner"], "")
            self.assertFalse(any("invalid lifecycle" in error for error in result["errors"]))

    def test_validation_warns_when_playbook_review_date_is_stale(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_project(root, humans=[{"name": "Dongwon Lee", "email": "webn77@gmail.com"}])
            write_issue(root, "123-summer-event")
            (root / "marketing").mkdir()
            (root / "marketing" / "banner-final.png").write_bytes(b"image")
            write_record(root)
            write_playbook(root, VALID_PLAYBOOK.replace("review_after: 2026-10-10", "review_after: 2026-01-01"))

            result = production.validate_production_project(root)
            self.assertTrue(any("review_after is stale" in warning for warning in result["warnings"]))

    def test_project_validator_merges_production_errors(self):
        validator = load_module("validate_project_artifacts_for_production", "scripts/validate_project_artifacts.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".moduflow").mkdir()
            (root / ".moduflow" / "config.json").write_text(
                json.dumps({"schema": "moduflow.config.v1", "paths": {}}), encoding="utf-8"
            )
            (root / ".moduflow" / "state.json").write_text(
                json.dumps(
                    {
                        "schema": "moduflow.state.v1",
                        "phase": "ready",
                        "active_issue": "",
                        "next_command": "product:status",
                    }
                ),
                encoding="utf-8",
            )
            for directory in ("issues", "specs", "workspace"):
                (root / directory).mkdir()
            for name in ("inbox.md", "opportunities.md", "roadmap.md", "dashboard.md"):
                (root / "workspace" / name).write_text("# Workspace\n", encoding="utf-8")
            write_project(root)
            write_issue(root, "123-summer-event")
            write_record(root, VALID_RECORD.replace("marketing/banner-final.png", "marketing/missing.png").replace(
                "playbook_refs: [banner-mobile]", "playbook_refs: []"
            ).replace("- banner-mobile — candidate", ""))

            result = validator.validate_project(root)
            self.assertFalse(result["valid"])
            self.assertTrue(any("missing artifact" in error for error in result["errors"]))


class ProjectProductionDogfoodTests(unittest.TestCase):
    def test_dogfood_project_validates_searches_and_retrieves(self):
        root = ROOT / "tests" / "fixtures" / "production-project"

        validation = production.validate_production_project(root)
        search = production.search_production(root, "small Korean text", limit=20)
        context = production.retrieve_production_context(
            root,
            deliverable_type="banner",
            channel="home-popup",
            audiences=["customer"],
            limit=5,
        )

        self.assertEqual(validation["errors"], [])
        self.assertEqual(len(search["items"]), 1)
        self.assertEqual(context["items"][0]["kind"], "playbook")
        self.assertTrue(context["items"][0]["authoritative"])


if __name__ == "__main__":
    unittest.main()
