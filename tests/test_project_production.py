import importlib.util
import json
import re
import tempfile
import unittest
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from scripts import project_operation, project_registry


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


def write_transaction_project(root, issue_ids, *, nested=False):
    paths = {
        "issues": "product/issues" if nested else "issues",
        "specs": "product/specs" if nested else "specs",
        "workspace": "product/workspace" if nested else "workspace",
        "knowledge": "product/knowledge" if nested else "knowledge",
        "memory": "product/memory" if nested else "memory",
        "production_records": (
            "product/records" if nested else "memory/production-records"
        ),
        "playbooks": "product/playbooks" if nested else "playbooks",
        "workflow": "product/workflow" if nested else "workflow",
    }
    moduflow = root / ".moduflow"
    moduflow.mkdir()
    (moduflow / "config.json").write_text(
        json.dumps({"schema": "moduflow.config.v1", "paths": paths}) + "\n",
        encoding="utf-8",
    )
    (moduflow / "state.json").write_text(
        json.dumps(
            {
                "schema": "moduflow.state.v1",
                "active_issue": "",
                "phase": "select",
                "active_goal": "",
                "next_command": "product:status",
                "blockers": [],
                "updated_at": "2029-12-31",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    for relative in paths.values():
        (root / relative).mkdir(parents=True, exist_ok=True)
    for issue_id in issue_ids:
        (root / paths["issues"] / f"{issue_id}.md").write_text(
            f"# Issue: `{issue_id}`\n\n"
            "**Status: backlog** — created 2029-12-01.\n"
            "**Priority: p2**\n"
            "**Blocked-by: none**\n\n"
            "## Notes\n\nPreserve issue prose.\n",
            encoding="utf-8",
        )
    workspace = root / paths["workspace"]
    (workspace / "dashboard.md").write_text(
        "# Dashboard\n\n## Active Issue\n\n- None active.\n\n"
        "## Notes\n\nPreserve dashboard prose.\n",
        encoding="utf-8",
    )
    (workspace / "loop-state.json").write_text(
        json.dumps(
            {
                "schema": "moduflow.loop-state.v2",
                "goal_id": "goal-103",
                "issue_ids": [],
                "active_issue_id": None,
                "status": "active",
                "next_command": "product:status",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (workspace / "transactions").mkdir()
    if nested:
        for relative, payload in (
            ("issues/POISON.md", b"POISON DEFAULT ISSUE\n"),
            ("workspace/dashboard.md", b"POISON DEFAULT DASHBOARD\n"),
            ("workspace/loop-state.json", b"{broken-default\n"),
            ("memory/production-records/poison.md", b"POISON DEFAULT RECORD\n"),
        ):
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(payload)
    return project_registry.project_context_for_root(root)


def transaction_clock():
    values = [date(2030, 1, 2)]
    start = datetime(2030, 1, 2, 3, 4, 5, tzinfo=timezone.utc)
    values.extend(start + timedelta(seconds=index) for index in range(120))
    iterator = iter(values)
    return lambda: next(iterator)


def transaction_validation_result():
    return {
        "schema": "moduflow.project-validation.v1",
        "project_root": "PRIVATE OMITTED",
        "valid": True,
        "errors": [],
        "warnings": [],
        "issue_schema": {
            "errors": 0,
            "warnings": 0,
            "codes": [],
            "diagnostics": [],
        },
        "lifecycle_drift": [],
    }


class ProjectProductionParserTests(unittest.TestCase):
    def test_parse_record_normalizes_metadata_sections_and_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_project(root)
            path = write_record(root)

            record = production.parse_production_record(root, path)

            self.assertEqual(record["version"], "")
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

    def test_parse_and_render_version_metadata_without_migrating_legacy_records(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_project(root)
            versioned = VALID_RECORD.replace(
                "issue_id: 123-summer-event\n",
                "issue_id: 123-summer-event\nversion: 1.2.3\n",
            )
            record = production.parse_production_record(
                root,
                write_record(root, versioned),
            )

            rendered = production._record_content(
                "record-103",
                "Versioned record",
                "BIZ-103",
                "",
                "document",
                "internal",
                ["team"],
                "draft",
                "when preparing release notes",
                "dongwon",
                "default",
                "2026-09-01",
                version="2.0.0",
            )
            legacy = production._record_content(
                "record-legacy",
                "Legacy record",
                "BIZ-103",
                "",
                "document",
                "internal",
                ["team"],
                "draft",
                "when preparing release notes",
                "dongwon",
                "default",
                "2026-09-01",
            )

            self.assertEqual(record["version"], "1.2.3")
            self.assertEqual(rendered.count("\nversion: 2.0.0\n"), 1)
            self.assertNotIn("\nversion:", legacy)

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
    def test_create_record_routes_exact_versioned_intent_and_maps_result(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            transaction_result = {
                "schema": "moduflow.lifecycle-transaction.v1",
                "status": "applied",
            }
            apply = mock.Mock(return_value=transaction_result)
            boundary = SimpleNamespace(
                LifecycleIntent=lambda **values: SimpleNamespace(**values),
                apply_lifecycle_transaction=apply,
            )
            context = project_registry.project_context_for_root(root)
            injector = lambda _stage: None

            with mock.patch.object(
                production,
                "_load_lifecycle_transaction_module",
                return_value=boundary,
                create=True,
            ):
                result = production.create_production_record(
                    root,
                    title="Release notes",
                    issue_id="BIZ-103",
                    version="1.2.3",
                    deliverable_type="document",
                    channel="internal",
                    audiences=["team"],
                    lifecycle="draft",
                    retrieval_trigger="when preparing releases",
                    owner="dongwon",
                    variant="default",
                    created="2030-01-02",
                    actor="dongwon",
                    source_event="request:C2c",
                    idempotency_key="a" * 64,
                    expected_issue_sha256="b" * 64,
                    project_context=context,
                    clock="clock",
                    fault_injector=injector,
                )

            intent = apply.call_args.args[1]
            self.assertEqual(intent.issue_id, "BIZ-103")
            self.assertEqual(intent.action, "production-version")
            self.assertEqual(intent.actor, "dongwon")
            self.assertEqual(intent.source_event, "request:C2c")
            self.assertEqual(intent.idempotency_key, "a" * 64)
            self.assertEqual(intent.expected_issue_sha256, "b" * 64)
            self.assertEqual(intent.production_change["version"], "1.2.3")
            self.assertEqual(
                intent.production_change["record_id"],
                "2030-01-02-release-notes",
            )
            self.assertIn("version: 1.2.3", intent.production_change["content"])
            apply.assert_called_once_with(
                root.resolve(),
                intent,
                project_context=context,
                clock="clock",
                fault_injector=injector,
            )
            self.assertEqual(result["action"], "created")
            self.assertEqual(result["id"], "2030-01-02-release-notes")
            self.assertEqual(
                result["path"],
                "memory/production-records/2030-01-02-release-notes.md",
            )
            self.assertIs(result["transaction"], transaction_result)
            self.assertFalse((root / "memory").exists())

    def test_create_record_rejects_invalid_version_or_issue_before_engine(self):
        invalid = (
            {"issue_id": "BIZ-103", "version": ""},
            {"issue_id": "BIZ-103", "version": "v1"},
            {"issue_id": "", "version": "1.2.3"},
        )
        for values in invalid:
            with self.subTest(values=values), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                with mock.patch.object(
                    production,
                    "_load_lifecycle_transaction_module",
                    create=True,
                ) as load:
                    with self.assertRaises(ValueError):
                        production.create_production_record(
                            root,
                            title="Release notes",
                            deliverable_type="document",
                            channel="internal",
                            audiences=["team"],
                            lifecycle="draft",
                            retrieval_trigger="when preparing releases",
                            **values,
                        )
                load.assert_not_called()
                self.assertFalse((root / "memory").exists())

    def test_create_record_maps_transaction_terminal_statuses(self):
        for status, action in (
            ("applied", "created"),
            ("noop", "noop"),
            ("conflict", "update_required"),
            ("denied", "denied"),
            ("recovery_required", "recovery_required"),
        ):
            with self.subTest(status=status), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                transaction_result = {
                    "schema": "moduflow.lifecycle-transaction.v1",
                    "status": status,
                }
                boundary = SimpleNamespace(
                    LifecycleIntent=lambda **values: SimpleNamespace(**values),
                    apply_lifecycle_transaction=mock.Mock(
                        return_value=transaction_result
                    ),
                )
                with mock.patch.object(
                    production,
                    "_load_lifecycle_transaction_module",
                    return_value=boundary,
                    create=True,
                ):
                    result = production.create_production_record(
                        root,
                        title="Release notes",
                        issue_id="BIZ-103",
                        version="1.2.3",
                        deliverable_type="document",
                        channel="internal",
                        audiences=["team"],
                        lifecycle="draft",
                        retrieval_trigger="when preparing releases",
                        created="2030-01-02",
                    )

                self.assertEqual(result["action"], action)
                self.assertIs(result["transaction"], transaction_result)

    def test_archived_project_denies_all_production_mutators_before_reads_or_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            context = project_registry.project_context_for_root(root)
            context.update(project_operation.compute_project_policy("archived", "internal"))

            with self.assertRaisesRegex(Exception, "Archived projects are read-only"):
                production.apply_production_plan(
                    {
                        "project_root": str(root),
                        "directories": ["memory/production-records", "playbooks"],
                    },
                    project_context=context,
                )
            with self.assertRaisesRegex(Exception, "Archived projects are read-only"):
                production.create_production_record(
                    root,
                    title="Denied",
                    deliverable_type="document",
                    channel="internal",
                    audiences=["team"],
                    lifecycle="draft",
                    retrieval_trigger="manual",
                    source_context="test",
                    project_context=context,
                )
            with mock.patch.object(
                production,
                "_configured_human_values",
                side_effect=AssertionError("project read before authorization"),
            ) as humans:
                with self.assertRaisesRegex(Exception, "Archived projects are read-only"):
                    production.decide_playbook_update(
                        root,
                        record_id="record",
                        playbook_id="playbook",
                        decision="approve",
                        approved_by="human",
                        reason="test",
                        decided_at="2026-08-21",
                        project_context=context,
                    )

            humans.assert_not_called()
            self.assertFalse((root / "memory").exists())
            self.assertFalse((root / "playbooks").exists())

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
            write_transaction_project(root, ["123-summer-event"])
            boundary = production._load_lifecycle_transaction_module()
            values = {
                "title": "Summer banner",
                "issue_id": "123-summer-event",
                "version": "1.2.3",
                "deliverable_type": "banner",
                "channel": "home-popup",
                "audiences": ["customer"],
                "lifecycle": "draft",
                "retrieval_trigger": "when creating mobile banners",
                "variant": "mobile",
                "created": "2030-01-02",
            }
            with mock.patch.object(
                boundary.validate_project_artifacts,
                "validate_project",
                return_value=transaction_validation_result(),
            ):
                first = production.create_production_record(
                    root, clock=transaction_clock(), **values
                )
            path = root / first["path"]

            with mock.patch.object(
                boundary.validate_project_artifacts,
                "validate_project",
                return_value=transaction_validation_result(),
            ):
                same = production.create_production_record(
                    root, clock=transaction_clock(), **values
                )
            self.assertEqual(same["action"], "noop")

            changed_values = {
                **values,
                "retrieval_trigger": "when creating changed mobile banners",
            }
            with mock.patch.object(
                boundary.validate_project_artifacts,
                "validate_project",
                return_value=transaction_validation_result(),
            ):
                changed = production.create_production_record(
                    root, clock=transaction_clock(), **changed_values
                )

            self.assertEqual(changed["action"], "update_required")
            self.assertNotIn(
                "changed mobile banners",
                path.read_text(encoding="utf-8"),
            )

    def test_same_day_and_title_with_different_issue_never_overwrites(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_transaction_project(
                root,
                ["123-summer-event", "124-partner-event"],
            )
            boundary = production._load_lifecycle_transaction_module()
            common = {
                "title": "Summer banner",
                "version": "1.2.3",
                "deliverable_type": "banner",
                "channel": "home-popup",
                "audiences": ["customer"],
                "lifecycle": "draft",
                "created": "2030-01-02",
            }
            with mock.patch.object(
                boundary.validate_project_artifacts,
                "validate_project",
                return_value=transaction_validation_result(),
            ):
                first = production.create_production_record(
                    root,
                    issue_id="123-summer-event",
                    retrieval_trigger="when creating banners",
                    clock=transaction_clock(),
                    **common,
                )
            before = (root / first["path"]).read_bytes()
            with mock.patch.object(
                boundary.validate_project_artifacts,
                "validate_project",
                return_value=transaction_validation_result(),
            ):
                second = production.create_production_record(
                    root,
                    issue_id="124-partner-event",
                    retrieval_trigger="when creating partner banners",
                    clock=transaction_clock(),
                    **common,
                )

            self.assertEqual(first["action"], "created")
            self.assertEqual(second["action"], "update_required")
            self.assertEqual(first["path"], second["path"])
            self.assertEqual((root / first["path"]).read_bytes(), before)
            self.assertEqual(len(production.list_production_records(root)), 1)

    def test_capture_requires_issue_and_explicit_semantic_version(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "issue_id is required"):
                production.create_production_record(
                    Path(tmp),
                    title="Banner",
                    deliverable_type="banner",
                    channel="home-popup",
                    audiences=["customer"],
                    lifecycle="draft",
                    retrieval_trigger="when creating banners",
                    source_context="brief-only-is-not-an-owner",
                )


class ProjectProductionCliTests(unittest.TestCase):
    def test_cli_init_and_new_record_emit_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_transaction_project(root, ["123-summer-event"])
            self.assertEqual(production.main([str(root), "--init"]), 0)
            boundary = production._load_lifecycle_transaction_module()
            with mock.patch.object(
                boundary.validate_project_artifacts,
                "validate_project",
                return_value=transaction_validation_result(),
            ):
                self.assertEqual(
                    production.main(
                        [
                            str(root),
                            "--new-record",
                            "--title",
                            "Summer banner",
                            "--issue-id",
                            "123-summer-event",
                            "--version",
                            "1.2.3",
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

    def test_cli_new_record_returns_nonzero_for_transaction_conflict(self):
        args = [
            "/project",
            "--new-record",
            "--title",
            "Summer banner",
            "--issue-id",
            "123-summer-event",
            "--version",
            "1.2.3",
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
        result = {
            "action": "update_required",
            "transaction": {"status": "conflict"},
        }
        with mock.patch.object(
            production,
            "create_production_record",
            return_value=result,
        ) as create:
            self.assertEqual(production.main(args), 1)

        self.assertEqual(create.call_args.kwargs["version"], "1.2.3")

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
    def test_validation_rejects_duplicate_versioned_semantic_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_project(root)
            write_issue(root, "123-summer-event")
            (root / "marketing").mkdir()
            (root / "marketing/banner-final.png").write_bytes(b"image")

            def versioned(record_id, title):
                return (
                    VALID_RECORD.replace(
                        "id: 2026-07-10-summer-banner",
                        f"id: {record_id}",
                    )
                    .replace("title: Summer banner", f"title: {title}")
                    .replace(
                        "issue_id: 123-summer-event\n",
                        "issue_id: 123-summer-event\nversion: 1.2.3\n",
                    )
                    .replace("playbook_refs: [banner-mobile]", "playbook_refs: []")
                    .replace("- banner-mobile — candidate", "")
                )

            write_record(root, versioned("record-one", "First title"))
            write_record(root, versioned("record-two", "Second title"))

            result = production.validate_production_project(root)
            version_errors = [
                error
                for error in result["errors"]
                if "duplicate production version identity" in error
            ]

            self.assertEqual(len(version_errors), 1)
            self.assertIn("record-one.md", version_errors[0])
            self.assertIn("record-two.md", version_errors[0])

    def test_validation_excludes_legacy_and_distinct_version_identities(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_project(root)
            write_issue(root, "123-summer-event")
            (root / "marketing").mkdir()
            (root / "marketing/banner-final.png").write_bytes(b"image")

            records = (
                VALID_RECORD.replace(
                    "id: 2026-07-10-summer-banner", "id: legacy-one"
                ).replace("title: Summer banner", "title: Legacy one"),
                VALID_RECORD.replace(
                    "id: 2026-07-10-summer-banner", "id: legacy-two"
                ).replace("title: Summer banner", "title: Legacy two"),
                VALID_RECORD.replace(
                    "id: 2026-07-10-summer-banner", "id: version-mobile"
                ).replace(
                    "issue_id: 123-summer-event\n",
                    "issue_id: 123-summer-event\nversion: 1.2.3\n",
                ),
                VALID_RECORD.replace(
                    "id: 2026-07-10-summer-banner", "id: version-desktop"
                )
                .replace(
                    "issue_id: 123-summer-event\n",
                    "issue_id: 123-summer-event\nversion: 1.2.3\n",
                )
                .replace("variant: mobile", "variant: desktop"),
            )
            for content in records:
                write_record(
                    root,
                    content.replace(
                        "playbook_refs: [banner-mobile]", "playbook_refs: []"
                    ).replace("- banner-mobile — candidate", ""),
                )

            result = production.validate_production_project(root)

            self.assertFalse(
                any(
                    "duplicate production version identity" in error
                    for error in result["errors"]
                )
            )

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


class ProjectProductionCanonicalPathTests(unittest.TestCase):
    def test_search_validation_and_create_use_only_configured_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_transaction_project(
                root,
                ["CONFIGURED-001", "CONFIGURED-002"],
                nested=True,
            )
            configured_records = root / "product" / "records"
            configured_content = (
                VALID_RECORD.replace(
                    "id: 2026-07-10-summer-banner",
                    "id: configured-banner",
                )
                .replace("issue_id: 123-summer-event", "issue_id: CONFIGURED-001")
                .replace("playbook_refs: [banner-mobile]", "playbook_refs: []")
                .replace("- banner-mobile — candidate", "")
                .replace(
                    "- [Final](marketing/banner-final.png) — final · customer",
                    "- [Final](product/banner-final.png) — final · customer",
                )
            )
            (configured_records / "configured-banner.md").write_text(
                configured_content, encoding="utf-8"
            )
            (root / "product" / "banner-final.png").write_bytes(b"image")
            poison_paths = (
                root / "issues/POISON.md",
                root / "workspace/dashboard.md",
                root / "workspace/loop-state.json",
                root / "memory/production-records/poison.md",
            )
            poison_before = {path: path.read_bytes() for path in poison_paths}

            result = production.search_production(root, "banner")
            validation = production.validate_production_project(root)
            boundary = production._load_lifecycle_transaction_module()
            with mock.patch.object(
                boundary.validate_project_artifacts,
                "validate_project",
                return_value=transaction_validation_result(),
            ):
                created = production.create_production_record(
                    root,
                    title="Configured follow-up",
                    issue_id="CONFIGURED-002",
                    version="1.2.3",
                    source_context="campaign brief",
                    deliverable_type="banner",
                    channel="home-popup",
                    audiences=["customer"],
                    lifecycle="draft",
                    retrieval_trigger="when creating configured follow-ups",
                    created="2030-01-02",
                    clock=transaction_clock(),
                )

            self.assertEqual(
                [item["id"] for item in result["items"]], ["configured-banner"]
            )
            self.assertNotIn("decoy-banner", json.dumps(result))
            self.assertFalse(
                any("dangling issue" in error for error in validation["errors"])
            )
            self.assertTrue(created["path"].startswith("product/records/"))
            self.assertTrue((root / created["path"]).exists())
            self.assertEqual(created["transaction"]["status"], "applied")
            self.assertEqual(
                {target["role"] for target in created["transaction"]["targets"]},
                {
                    "issue",
                    "state",
                    "loop",
                    "dashboard",
                    "production-record",
                    "evidence",
                },
            )
            self.assertTrue(
                list((root / "product/workspace/transactions").glob("*.json"))
            )
            self.assertEqual(
                {path: path.read_bytes() for path in poison_paths},
                poison_before,
            )


if __name__ == "__main__":
    unittest.main()
