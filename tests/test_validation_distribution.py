import ast
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_module(name, relative_path):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ValidationDistributionTests(unittest.TestCase):
    def create_minimal_project(self, root):
        (root / ".moduflow").mkdir()
        (root / ".moduflow" / "config.json").write_text(
            json.dumps({"schema": "moduflow.config.v1", "paths": {}}) + "\n",
            encoding="utf-8",
        )
        (root / ".moduflow" / "state.json").write_text(
            json.dumps({"schema": "moduflow.state.v1", "phase": "ready", "next_command": "product:status"}) + "\n",
            encoding="utf-8",
        )
        for directory in ["issues", "specs", "knowledge/decisions", "knowledge/benchmarks", "knowledge/reports", "knowledge/research", "knowledge/data-notes", "knowledge/references"]:
            (root / directory).mkdir(parents=True, exist_ok=True)
        (root / "knowledge" / "index.md").write_text("# Knowledge\n", encoding="utf-8")
        (root / "workspace").mkdir()
        for filename in ["inbox.md", "opportunities.md", "roadmap.md", "dashboard.md"]:
            (root / "workspace" / filename).write_text("# Workspace\n", encoding="utf-8")
        for filename in ["project-profile.md", "environments.json", "integrations.json"]:
            content = "{}\n" if filename.endswith(".json") else "# Profile\n"
            (root / ".moduflow" / filename).write_text(content, encoding="utf-8")
        (root / "workflow").mkdir()
        for filename in ["review-gates.md", "approval-policy.md", "release-policy.md", "handoff.md", "risks.md"]:
            (root / "workflow" / filename).write_text("# Workflow\n", encoding="utf-8")

    def test_validate_project_artifacts_passes_for_valid_project(self):
        validator = load_module("validate_project_artifacts", "scripts/validate_project_artifacts.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.create_minimal_project(root)

            result = validator.validate_project(root)

            self.assertTrue(result["valid"])
            self.assertEqual(result["errors"], [])

    def test_validate_project_uses_nested_context_and_ignores_decoy_defaults(self):
        validator = load_module("validate_project_nested", "scripts/validate_project_artifacts.py")
        project_registry = load_module("project_registry_nested", "scripts/project_registry.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.create_minimal_project(root)
            nested = {
                "issues": "product/issues",
                "specs": "delivery/specs",
                "workspace": "ops/workspace",
                "knowledge": "project-knowledge",
                "memory": "project-memory",
                "production_records": "records/production",
                "playbooks": "shared/playbooks",
                "workflow": "team/workflow",
            }
            for role in ("issues", "specs", "workspace", "knowledge", "workflow"):
                source = root / role
                target = root / nested[role]
                target.parent.mkdir(parents=True, exist_ok=True)
                source.rename(target)
            (root / nested["memory"]).mkdir(parents=True)
            (root / ".moduflow" / "config.json").write_text(
                json.dumps({"schema": "moduflow.config.v1", "paths": nested}) + "\n",
                encoding="utf-8",
            )
            decoy = root / "workflow" / "team-state.json"
            decoy.parent.mkdir()
            decoy.write_text('{"schema":"broken","items":{}}\n', encoding="utf-8")
            context = project_registry.project_context_for_root(root)

            result = validator.validate_project(root, project_context=context)

            self.assertTrue(result["valid"], result["errors"])
            self.assertEqual(decoy.read_text(encoding="utf-8"), '{"schema":"broken","items":{}}\n')

    def test_validate_project_artifacts_warns_on_issue_missing_status_line(self):
        validator = load_module("validate_project_artifacts", "scripts/validate_project_artifacts.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.create_minimal_project(root)
            (root / "issues" / "001-with-status.md").write_text(
                "# Issue 001\n\n**Status: done** — shipped.\n", encoding="utf-8"
            )
            (root / "issues" / "002-legacy.md").write_text(
                "# Issue 002\n\n## Links\n\n- Status: `specs/002/status.md`\n", encoding="utf-8"
            )

            result = validator.validate_project(root)

            self.assertTrue(result["valid"])
            matching = [w for w in result["warnings"] if "002-legacy.md" in w and "**Status:" in w]
            self.assertEqual(len(matching), 1)
            self.assertFalse(any("001-with-status.md" in w for w in result["warnings"]))

    def test_unreadable_issue_fails_closed_without_validator_or_doctor_traceback(self):
        validator = load_module("validate_project_unreadable", "scripts/validate_project_artifacts.py")
        project_doctor = load_module("project_doctor_unreadable", "scripts/project_doctor.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.create_minimal_project(root)
            (root / "issues" / "BIZ-UNREADABLE.md").write_bytes(
                b"\xff\xfe\x00\x80"
            )

            validation = validator.validate_project(root)
            doctor = project_doctor.inspect_project(
                root, include_preflight=False
            )
            validator_proc = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "validate_project_artifacts.py"),
                    str(root),
                ],
                capture_output=True,
                text=True,
            )
            validator_payload = json.loads(validator_proc.stdout)

        self.assertFalse(validation["valid"])
        self.assertEqual(validator_proc.returncode, 1)
        self.assertFalse(validator_payload["valid"])
        self.assertTrue(
            any(
                "ISSUE_SOURCE_UNREADABLE" in error
                for error in validation["errors"]
            )
        )
        self.assertIn(
            "ISSUE_SOURCE_UNREADABLE",
            validation["issue_schema"]["codes"],
        )
        self.assertGreaterEqual(doctor["issue_schema"]["errors"], 1)
        self.assertIn(
            "ISSUE_SOURCE_UNREADABLE",
            doctor["issue_schema"]["codes"],
        )

    def test_external_issue_and_artifact_symlinks_keep_validator_and_doctor_json(self):
        validator = load_module(
            "validate_project_external_symlink",
            "scripts/validate_project_artifacts.py",
        )
        project_doctor = load_module(
            "project_doctor_external_symlink",
            "scripts/project_doctor.py",
        )
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "project"
            root.mkdir()
            self.create_minimal_project(root)
            outside_issue = base / "DO-NOT-EXPOSE-ISSUE-SECRET.md"
            outside_issue.write_text(
                "# DO-NOT-EXPOSE-ISSUE-CONTENT\n",
                encoding="utf-8",
            )
            (root / "issues" / "BIZ-SOURCE-LINK.md").symlink_to(outside_issue)
            (root / "issues" / "BIZ-ARTIFACT-LINK.md").write_text(
                """---
schema_version: 0.1.0
issue_id: BIZ-ARTIFACT-LINK
canonical_state: active
status: in_progress
priority: p2
definition_readiness: ready
gate_state: passed
depends_on: []
next_command: product:execute BIZ-ARTIFACT-LINK
---
# Artifact link

**Status: active**
""",
                encoding="utf-8",
            )
            outside_specs = base / "DO-NOT-EXPOSE-SPECS-SECRET"
            outside_specs.mkdir()
            (outside_specs / "spec.md").write_text(
                "# DO-NOT-EXPOSE-SPEC-CONTENT\n",
                encoding="utf-8",
            )
            (root / "specs" / "BIZ-ARTIFACT-LINK").symlink_to(
                outside_specs,
                target_is_directory=True,
            )

            validation = validator.validate_project(root)
            doctor = project_doctor.inspect_project(
                root,
                include_preflight=False,
            )
            validator_proc = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "validate_project_artifacts.py"),
                    str(root),
                ],
                capture_output=True,
                text=True,
            )
            doctor_proc = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "project_doctor.py"),
                    str(root),
                    "--no-preflight",
                ],
                capture_output=True,
                text=True,
            )
            validator_payload = json.loads(validator_proc.stdout)
            doctor_payload = json.loads(doctor_proc.stdout)
            serialized = json.dumps(
                {
                    "validation": validation,
                    "doctor": doctor,
                    "validator_cli": validator_payload,
                    "doctor_cli": doctor_payload,
                },
                ensure_ascii=False,
            )

        self.assertEqual(validator_proc.returncode, 1)
        self.assertEqual(doctor_proc.returncode, 1)
        self.assertFalse(validation["valid"])
        self.assertIn(
            "ISSUE_SOURCE_OUTSIDE_ROOT",
            validation["issue_schema"]["codes"],
        )
        self.assertIn(
            "ISSUE_ARTIFACT_OUTSIDE_ROOT",
            validation["issue_schema"]["codes"],
        )
        self.assertEqual(
            validation["issue_schema"],
            doctor["issue_schema"],
        )
        self.assertNotIn("DO-NOT-EXPOSE-ISSUE-CONTENT", serialized)
        self.assertNotIn("DO-NOT-EXPOSE-SPEC-CONTENT", serialized)

    def test_external_issues_root_symlink_fails_validator_and_doctor_closed(self):
        validator = load_module(
            "validate_project_external_issues_root",
            "scripts/validate_project_artifacts.py",
        )
        project_doctor = load_module(
            "project_doctor_external_issues_root",
            "scripts/project_doctor.py",
        )
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "project"
            root.mkdir()
            self.create_minimal_project(root)
            outside_issues = base / "DO-NOT-EXPOSE-ISSUES-ROOT"
            outside_issues.mkdir()
            (outside_issues / "BIZ-SECRET.md").write_text(
                "# DO-NOT-EXPOSE-ROOT-CONTENT\n",
                encoding="utf-8",
            )
            (root / "issues").rmdir()
            (root / "issues").symlink_to(
                outside_issues,
                target_is_directory=True,
            )

            validation = validator.validate_project(root)
            doctor = project_doctor.inspect_project(
                root,
                include_preflight=False,
            )
            validator_proc = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "validate_project_artifacts.py"),
                    str(root),
                ],
                capture_output=True,
                text=True,
            )
            doctor_proc = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "project_doctor.py"),
                    str(root),
                    "--no-preflight",
                ],
                capture_output=True,
                text=True,
            )
            serialized = json.dumps(
                {
                    "validation": validation,
                    "doctor": doctor,
                    "validator_cli": json.loads(validator_proc.stdout),
                    "doctor_cli": json.loads(doctor_proc.stdout),
                },
                ensure_ascii=False,
            )

        self.assertEqual(validator_proc.returncode, 1)
        self.assertEqual(doctor_proc.returncode, 1)
        self.assertIn(
            "ISSUE_SOURCE_OUTSIDE_ROOT",
            validation["issue_schema"]["codes"],
        )
        self.assertEqual(validation["issue_schema"], doctor["issue_schema"])
        self.assertNotIn("DO-NOT-EXPOSE-ROOT-CONTENT", serialized)

    def test_validate_project_surfaces_sorted_actionable_issue_schema_diagnostics_once(self):
        validator = load_module("validate_project_artifacts", "scripts/validate_project_artifacts.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.create_minimal_project(root)
            (root / "issues" / "BIZ-PROJECTION.md").write_text(
                """---
schema_version: 0.1.0
issue_id: BIZ-PROJECTION
canonical_state: backlog
status: backlog
priority: p2
definition_readiness: ready
gate_state: passed
depends_on: []
next_command: product:doctor
---
# Projection mismatch

**Status: done** — created 2026-07-24.
""",
                encoding="utf-8",
            )
            (root / "issues" / "BIZ-ADVISORY.md").write_text(
                """---
issue_id: BIZ-ADVISORY
definition_readiness: ready
gate_state: passed
---
# Advisory issue

**Status: backlog** — created 2026-07-24.
""",
                encoding="utf-8",
            )

            result = validator.validate_project(root)

            self.assertFalse(result["valid"])
            projection_errors = [
                error
                for error in result["errors"]
                if "ISSUE_STATE_PROJECTION_MISMATCH" in error
            ]
            self.assertEqual(len(projection_errors), 1)
            self.assertIn("issues/BIZ-PROJECTION.md", projection_errors[0])
            self.assertIn("Markdown Status must project", projection_errors[0])
            self.assertIn("Recommendation:", projection_errors[0])
            self.assertTrue(
                any(
                    "ISSUE_FRONTMATTER_UNVERSIONED" in warning
                    and "issues/BIZ-ADVISORY.md" in warning
                    and "Recommendation:" in warning
                    for warning in result["warnings"]
                )
            )
            self.assertEqual(len(result["errors"]), len(set(result["errors"])))
            self.assertEqual(len(result["warnings"]), len(set(result["warnings"])))
            self.assertGreaterEqual(result["issue_schema"]["errors"], 1)
            self.assertGreaterEqual(result["issue_schema"]["warnings"], 1)
            self.assertEqual(
                result["issue_schema"]["codes"],
                sorted(result["issue_schema"]["codes"]),
            )

    def test_validate_project_evaluates_issue_schema_once(self):
        validator = load_module("validate_project_artifacts_once", "scripts/validate_project_artifacts.py")
        schema = validator.load_project_issue_schema()
        original_evaluate = schema.evaluate_project
        calls = []

        def counting_evaluate(root):
            calls.append(Path(root))
            return original_evaluate(root)

        schema.evaluate_project = counting_evaluate
        validator.load_project_issue_schema = lambda: schema
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.create_minimal_project(root)

            validator.validate_project(root)

        self.assertEqual(calls, [root.resolve()])

    def test_validate_project_preserves_context_aware_dependency_severity(self):
        validator = load_module("validate_project_dependency_severity", "scripts/validate_project_artifacts.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.create_minimal_project(root)

            def write_issue(issue_id, lifecycle, dependencies, next_command):
                status = "in_progress" if lifecycle == "active" else "backlog"
                (root / "issues" / f"{issue_id}.md").write_text(
                    f"""---
schema_version: 0.1.0
issue_id: {issue_id}
canonical_state: {lifecycle}
status: {status}
priority: p2
definition_readiness: ready
gate_state: passed
depends_on: [{", ".join(dependencies)}]
next_command: {next_command}
---
# Dependency severity fixture

**Status: {lifecycle}** — created 2026-07-24.
""",
                    encoding="utf-8",
                )

            write_issue("BIZ-BLOCKER", "backlog", (), "product:status")
            write_issue(
                "BIZ-WAITING",
                "backlog",
                ("BIZ-BLOCKER",),
                "product:status",
            )
            write_issue(
                "BIZ-ACTIVE",
                "active",
                ("BIZ-BLOCKER",),
                "product:status",
            )
            state_path = root / ".moduflow" / "state.json"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            state["active_issue"] = "BIZ-ACTIVE"
            state_path.write_text(json.dumps(state) + "\n", encoding="utf-8")
            (root / "workspace" / "dashboard.md").write_text(
                "# Dashboard\n\n## Active Issue\n\n- `BIZ-ACTIVE`\n",
                encoding="utf-8",
            )

            result = validator.validate_project(root)

        warning_matches = [
            message
            for message in result["warnings"]
            if "ISSUE_DEPENDENCY_UNMET" in message
            and "BIZ-WAITING.md" in message
        ]
        error_matches = [
            message
            for message in result["errors"]
            if "ISSUE_DEPENDENCY_UNMET" in message
            and "BIZ-ACTIVE.md" in message
        ]
        self.assertEqual(len(warning_matches), 1)
        self.assertEqual(len(error_matches), 1)
        self.assertFalse(
            any(
                "ISSUE_DEPENDENCY_UNMET" in message
                and "BIZ-WAITING.md" in message
                for message in result["errors"]
            )
        )

    def test_validate_project_artifacts_reports_invalid_state_json(self):
        validator = load_module("validate_project_artifacts", "scripts/validate_project_artifacts.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.create_minimal_project(root)
            (root / ".moduflow" / "state.json").write_text("{bad json", encoding="utf-8")

            result = validator.validate_project(root)

            self.assertFalse(result["valid"])
            self.assertTrue(any(".moduflow/state.json" in error for error in result["errors"]))

    def test_validate_moduflow_exposes_importable_api(self):
        validator = load_module("validate_moduflow", "scripts/validate_moduflow.py")

        result = validator.validate_moduflow(ROOT)

        self.assertEqual(result["schema"], "moduflow.package-validation.v1")
        self.assertTrue(result["valid"])
        self.assertEqual(result["errors"], [])
        self.assertGreater(result["checked_files"], 0)

    def test_validate_moduflow_requires_frontend_qa_templates(self):
        validator = load_module("validate_moduflow", "scripts/validate_moduflow.py")

        expected = {
            "templates/frontend-qa/README.md",
            "templates/frontend-qa/api-contract-mapping.md",
            "templates/frontend-qa/storybook-required-states.md",
            "templates/frontend-qa/msw-fixture-catalog.md",
            "templates/frontend-qa/playwright-smoke-matrix.md",
            "templates/frontend-qa/qa-evidence-checklist.md",
        }

        self.assertTrue(expected.issubset(set(validator.REQUIRED_FILES)))

    def test_validate_moduflow_requires_reference_improvement_surface(self):
        validator = load_module("validate_moduflow", "scripts/validate_moduflow.py")

        expected = {
            "templates/workspace/reference-improvements.md",
            "scripts/project_reference_backlog.py",
        }

        self.assertTrue(expected.issubset(set(validator.REQUIRED_FILES)))

    def test_validate_moduflow_requires_production_knowledge_surface(self):
        validator = load_module("validate_moduflow_production", "scripts/validate_moduflow.py")
        expected = {
            "commands/product-production.md",
            "scripts/project_production.py",
            "templates/production/record.md",
            "templates/production/playbook.md",
        }
        self.assertTrue(expected.issubset(set(validator.REQUIRED_FILES)))

    def test_validate_moduflow_ships_issue_schema_and_local_fixtures(self):
        validator = load_module(
            "validate_moduflow_issue_schema", "scripts/validate_moduflow.py"
        )
        expected = {
            "scripts/project_issue_schema.py",
            "tests/fixtures/issue-schema/BIZ-033.md",
            "tests/fixtures/issue-schema/BIZ-038.md",
            "tests/fixtures/issue-schema/BIZ-039.md",
            "tests/fixtures/issue-schema/BIZ-040.md",
            "tests/fixtures/issue-schema/legacy-markdown.md",
        }

        self.assertTrue(expected.issubset(set(validator.REQUIRED_FILES)))
        self.assertTrue(all((ROOT / path).is_file() for path in expected))

    def test_distribution_ships_project_registry_contract_and_release_suite(self):
        validator = load_module(
            "validate_moduflow_project_registry", "scripts/validate_moduflow.py"
        )
        expected = {
            "scripts/project_registry.py",
            "scripts/canonical_path_guard.py",
            "config/canonical-path-literals.json",
            "tests/test_project_registry.py",
            "tests/test_canonical_path_guard.py",
            "tests/fixtures/project-registry/projects-v1.json",
            "tests/fixtures/project-registry/projects-v2.json",
            "tests/fixtures/project-registry/projects-v2-alias-collision.json",
            "templates/portfolio/projects.json",
            "commands/product-projects.md",
            "commands/product-portfolio.md",
        }

        self.assertTrue(expected.issubset(set(validator.REQUIRED_FILES)))
        self.assertTrue(all((ROOT / path).is_file() for path in expected))
        release_source = (ROOT / "scripts" / "release_check.py").read_text(
            encoding="utf-8"
        )
        self.assertIn('"tests.test_project_registry"', release_source)
        self.assertIn('"tests.test_canonical_path_guard"', release_source)
        self.assertIn('"canonical_path_guard"', release_source)

    def test_distribution_ships_project_operation_policy_and_audit(self):
        validator = load_module(
            "validate_moduflow_project_operation", "scripts/validate_moduflow.py"
        )
        packaged = {
            "scripts/project_operation.py",
            "scripts/project_operation_audit.py",
            "config/project-operation-entrypoints.json",
        }
        source_only = {
            "tests/test_project_operation.py",
            "tests/test_project_operation_audit.py",
            "tests/project_operation_fixture.py",
        }

        self.assertTrue(packaged.issubset(set(validator.REQUIRED_FILES)))
        self.assertTrue(source_only.issubset(set(validator.REQUIRED_FILES)))
        self.assertTrue(source_only.issubset(set(validator.SOURCE_ONLY_REQUIRED_FILES)))
        self.assertTrue(all((ROOT / path).is_file() for path in packaged | source_only))

    def test_issue_consumers_import_shared_schema_without_duplicate_parsers(self):
        forbidden_definitions = {
            "parse_issue_frontmatter",
            "issue_status",
            "issue_blocked_by",
        }
        for relative_path in [
            "scripts/project_lifecycle.py",
            "scripts/mcp_server.py",
            "scripts/project_memory.py",
        ]:
            with self.subTest(consumer=relative_path):
                tree = ast.parse(
                    (ROOT / relative_path).read_text(encoding="utf-8"),
                    filename=relative_path,
                )
                imported_modules = {
                    node.module
                    for node in ast.walk(tree)
                    if isinstance(node, ast.ImportFrom)
                }
                definitions = {
                    node.name
                    for node in ast.walk(tree)
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                }

                self.assertTrue(
                    {
                        "scripts.project_issue_schema",
                        "project_issue_schema",
                    }
                    & imported_modules
                )
                self.assertTrue(forbidden_definitions.isdisjoint(definitions))

    def test_validate_moduflow_requires_review_intake_surface(self):
        validator = load_module(
            "validate_moduflow_review", "scripts/validate_moduflow.py"
        )
        required = {
            "scripts/review_intake.py",
            "scripts/project_review.py",
            "adapters/github-review.yaml",
            "adapters/security-review.yaml",
            "overlays/review-policy.yaml",
            "templates/reviews/review-intake.json",
            "templates/reviews/review-summary.ko.md",
            "templates/reviews/review-candidates.md",
        }

        self.assertTrue(required.issubset(set(validator.REQUIRED_FILES)))

    def test_validate_moduflow_requires_capability_routing_surface(self):
        validator = load_module(
            "validate_moduflow_capability_routing", "scripts/validate_moduflow.py"
        )
        required = {
            "adapters/capability-routing.json",
            "scripts/capability_routing.py",
            "scripts/capability_routing_simulation.py",
            "tests/fixtures/capability-routing/cases.json",
        }

        self.assertTrue(required.issubset(set(validator.REQUIRED_FILES)))

        moduflow = (ROOT / "commands" / "moduflow.md").read_text(encoding="utf-8")
        index = (ROOT / "skills" / "index" / "SKILL.md").read_text(encoding="utf-8")
        router = (
            ROOT / "skills" / "pm-execution-router" / "SKILL.md"
        ).read_text(encoding="utf-8")

        self.assertIn("capability_routing.py", moduflow)
        self.assertIn("bundled", moduflow.lower())
        self.assertIn("--available", moduflow)
        self.assertIn("--completed-artifact", moduflow)
        for outcome in ("none", "delegate", "sequence", "clarify"):
            self.assertIn(f"`{outcome}`", moduflow)
        self.assertIn("at most one specialist", moduflow)
        self.assertIn("permission", index.lower())
        self.assertIn("availability", index.lower())
        self.assertIn("permission", router.lower())
        self.assertIn("availability", router.lower())
        self.assertIn("fail-closed", router.lower())

    def test_validate_moduflow_requires_spec_kit_selective_surface(self):
        validator = load_module(
            "validate_moduflow_spec_kit_selective", "scripts/validate_moduflow.py"
        )
        packaged_paths = {
            "skills/spec-kit-validation-bridge/SKILL.md",
            "overlays/spec-kit/selective-validation-policy.md",
            "adapters/spec-kit.yaml",
            "adapters/capability-routing.json",
            "commands/moduflow.md",
            "skills/index/SKILL.md",
            "skills/pm-execution-router/SKILL.md",
            "scripts/spec_kit_adapter.py",
            "scripts/spec_kit_pilot.py",
            "scripts/sync_spec_kit_templates.py",
            "templates/moduflow-capabilities.json",
            "vendor/spec-kit/0.16.1/manifest.json",
            "vendor/spec-kit/0.16.1/commands/clarify.md",
            "vendor/spec-kit/0.16.1/commands/analyze.md",
            "vendor/spec-kit/0.16.1/commands/checklist.md",
            "vendor/spec-kit/0.16.1/commands/converge.md",
            "tests/fixtures/spec-kit-selective-validation/cases.json",
            "tests/fixtures/spec-kit-selective-validation/results/clarify.json",
            "tests/fixtures/spec-kit-selective-validation/results/analyze.json",
            "tests/fixtures/spec-kit-selective-validation/results/checklist.json",
            "tests/fixtures/spec-kit-selective-validation/results/converge.json",
            "specs/098-speckit-selective-validation-adapter/pilot-report.md",
            "specs/098-speckit-selective-validation-adapter/status.md",
        }

        missing = sorted(path for path in packaged_paths if not (ROOT / path).is_file())

        self.assertEqual(missing, [])
        self.assertTrue(packaged_paths.issubset(set(validator.REQUIRED_FILES)))

    def test_review_upstreams_and_policy_are_registered(self):
        vendor = json.loads((ROOT / "vendor.lock.json").read_text(encoding="utf-8"))
        source_ids = {source["id"] for source in vendor["sources"]}
        github_adapter = (ROOT / "adapters" / "github-review.yaml").read_text(
            encoding="utf-8"
        )
        security_adapter = (
            ROOT / "adapters" / "security-review.yaml"
        ).read_text(encoding="utf-8")
        superpowers_adapter = (
            ROOT / "adapters" / "superpowers.yaml"
        ).read_text(encoding="utf-8")
        policy = (ROOT / "overlays" / "review-policy.yaml").read_text(
            encoding="utf-8"
        )

        self.assertIn("codex-github", source_ids)
        self.assertIn("thread-aware GraphQL", github_adapter)
        self.assertIn("none by default", github_adapter)
        self.assertIn("CodeQL alert intake", security_adapter)
        self.assertIn("SARIF result intake", security_adapter)
        self.assertIn("receiving code review", superpowers_adapter)
        for reason_code in [
            "sensitive_path",
            "elevated_severity",
            "no_risk_evidence_missing",
            "high_risk_reject_requires_human",
            "target_commit_mismatch",
        ]:
            self.assertIn(reason_code, policy)

    def test_product_review_and_index_route_intake_without_remote_write(self):
        command = (ROOT / "commands" / "product-review.md").read_text(
            encoding="utf-8"
        )
        index = (ROOT / "skills" / "index" / "SKILL.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("product:review --intake", command)
        self.assertIn("Router AI", command)
        self.assertIn("Verifier", command)
        self.assertIn("never reply, resolve, publish, implement", command)
        self.assertIn("외부 코드리뷰 접수", index)
        self.assertIn("product:review --intake", index)

    def test_validate_moduflow_importable_api_reports_missing_files(self):
        validator = load_module("validate_moduflow", "scripts/validate_moduflow.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            result = validator.validate_moduflow(root)

            self.assertFalse(result["valid"])
            self.assertTrue(any("Missing required files" in error for error in result["errors"]))

    def test_validate_project_artifacts_allows_lightweight_project(self):
        validator = load_module("validate_project_artifacts", "scripts/validate_project_artifacts.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".moduflow").mkdir()
            (root / ".moduflow" / "config.json").write_text(
                json.dumps({"schema": "moduflow.config.v1", "paths": {}}) + "\n",
                encoding="utf-8",
            )
            (root / ".moduflow" / "state.json").write_text(
                json.dumps({"schema": "moduflow.state.v1", "phase": "ready", "next_command": "product:status"}) + "\n",
                encoding="utf-8",
            )
            for directory in ["issues", "specs"]:
                (root / directory).mkdir()
            (root / "workspace").mkdir()
            for filename in ["inbox.md", "opportunities.md", "roadmap.md", "dashboard.md"]:
                (root / "workspace" / filename).write_text("# Workspace\n", encoding="utf-8")

            result = validator.validate_project(root)

            self.assertTrue(result["valid"])
            self.assertEqual(result["errors"], [])
            self.assertTrue(any("Optional project capability not initialized" in warning for warning in result["warnings"]))

    def test_validate_project_artifacts_respects_configured_paths(self):
        validator = load_module("validate_project_artifacts", "scripts/validate_project_artifacts.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".moduflow").mkdir()
            (root / ".moduflow" / "config.json").write_text(
                json.dumps(
                    {
                        "schema": "moduflow.config.v1",
                        "paths": {
                            "issues": "projects/modu-charge/issues",
                            "specs": "specs",
                            "workspace": "workspace",
                        },
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (root / ".moduflow" / "state.json").write_text(
                json.dumps({"schema": "moduflow.state.v1", "phase": "ready", "next_command": "product:status"}) + "\n",
                encoding="utf-8",
            )
            (root / "projects" / "modu-charge" / "issues").mkdir(parents=True)
            (root / "specs").mkdir()
            (root / "workspace").mkdir()
            for filename in ["inbox.md", "opportunities.md", "roadmap.md", "dashboard.md"]:
                (root / "workspace" / filename).write_text("# Workspace\n", encoding="utf-8")

            result = validator.validate_project(root)

            self.assertTrue(result["valid"])
            self.assertEqual(result["errors"], [])

    def test_validator_evaluates_issues_from_configured_safe_paths(self):
        validator = load_module("validate_project_custom_issue_path", "scripts/validate_project_artifacts.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.create_minimal_project(root)
            custom_issues = root / "projects" / "billing" / "issues"
            custom_specs = root / "projects" / "billing" / "specs"
            custom_issues.mkdir(parents=True)
            custom_specs.mkdir(parents=True)
            config_path = root / ".moduflow" / "config.json"
            config = json.loads(config_path.read_text(encoding="utf-8"))
            config["paths"].update(
                {
                    "issues": "projects/billing/issues",
                    "specs": "projects/billing/specs",
                }
            )
            config_path.write_text(json.dumps(config) + "\n", encoding="utf-8")
            (custom_issues / "BIZ-CUSTOM.md").write_text(
                """---
schema_version: 9.9.9
issue_id: BIZ-CUSTOM
---
# Unsupported custom issue

**Status: backlog** — created 2026-07-25.
""",
                encoding="utf-8",
            )

            result = validator.validate_project(root)

        self.assertFalse(result["valid"])
        self.assertIn("ISSUE_SCHEMA_UNSUPPORTED", result["issue_schema"]["codes"])
        diagnostic = next(
            item
            for item in result["issue_schema"]["diagnostics"]
            if item["code"] == "ISSUE_SCHEMA_UNSUPPORTED"
        )
        self.assertEqual(
            diagnostic["source_path"],
            "projects/billing/issues/BIZ-CUSTOM.md",
        )

    def test_validator_rejects_configured_issue_path_outside_project(self):
        validator = load_module("validate_project_traversal", "scripts/validate_project_artifacts.py")
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "project"
            root.mkdir()
            self.create_minimal_project(root)
            (root / "issues").rmdir()
            outside_issues = base / "outside" / "issues"
            outside_issues.mkdir(parents=True)
            (outside_issues / "BIZ-OUTSIDE.md").write_text(
                "# Outside\n\n**Status: backlog** — created.\n",
                encoding="utf-8",
            )
            config_path = root / ".moduflow" / "config.json"
            config = json.loads(config_path.read_text(encoding="utf-8"))
            config["paths"]["issues"] = "../../outside/issues"
            config_path.write_text(json.dumps(config) + "\n", encoding="utf-8")

            result = validator.validate_project(root)

        self.assertFalse(result["valid"])
        self.assertTrue(
            any(
                "Missing required project artifact: issues" in error
                for error in result["errors"]
            )
        )
        self.assertIn(
            "ISSUE_SOURCE_OUTSIDE_ROOT",
            result["issue_schema"]["codes"],
        )
        self.assertTrue(
            any(
                diagnostic["field"] == "issues_root"
                for diagnostic in result["issue_schema"]["diagnostics"]
            )
        )

    def test_validate_project_artifacts_reports_loop_state_missing_active_issue(self):
        validator = load_module("validate_project_artifacts", "scripts/validate_project_artifacts.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.create_minimal_project(root)
            (root / "workspace" / "loop-state.json").write_text(
                json.dumps(
                    {
                        "schema": "moduflow.loop-state.v2",
                        "goal_id": "goal-a",
                        "issue_ids": ["missing-issue"],
                        "active_issue_id": "missing-issue",
                        "next_command": "product:spec missing-issue",
                        "status": "active",
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            result = validator.validate_project(root)

            self.assertFalse(result["valid"])
            self.assertTrue(
                any("active_issue_id missing-issue" in error for error in result["errors"])
            )


    def write_loop_project(self, root, issue_id="024-artifact-schema-and-doctor-gates", next_command=None):
        self.create_minimal_project(root)
        next_command = next_command or f"product:spec {issue_id}"
        # 048: the lifecycle gate keys off .moduflow/state.json, not loop-state.json.
        state_path = root / ".moduflow" / "state.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        state["active_issue"] = issue_id
        state["next_command"] = next_command
        state_path.write_text(json.dumps(state) + "\n", encoding="utf-8")
        (root / "issues" / f"{issue_id}.md").write_text(
            f"""# Issue 024: Artifact Schema And Doctor Gates

## Lifecycle

- Phase: proposed

## Workflow Tasks

- [ ] spec → `specs/{issue_id}/spec.md`
- [ ] plan → `specs/{issue_id}/plan.md`
- [ ] execute → schema validator + doctor gates
- [ ] review → fixture-based drift/missing-link tests

## Next Command

`{next_command}`
""",
            encoding="utf-8",
        )
        (root / "workspace" / "loop-state.json").write_text(
            json.dumps(
                {
                    "schema": "moduflow.loop-state.v2",
                    "goal_id": "goal-loop",
                    "issue_ids": [issue_id],
                    "active_issue_id": issue_id,
                    "phase": "spec",
                    "next_command": next_command,
                    "status": "active",
                }
            )
            + "\n",
            encoding="utf-8",
        )
        (root / "workspace" / "dashboard.md").write_text(
            f"# Dashboard\n\n## Active Issue\n\n- `{issue_id}`\n\n## Next Command\n\n`{next_command}`\n",
            encoding="utf-8",
        )
        (root / "workspace" / "roadmap.md").write_text(
            f"# Roadmap\n\n## Now\n\n### `{issue_id}`\n\n- Next command: `{next_command}`\n",
            encoding="utf-8",
        )

    def test_validate_project_artifacts_reports_missing_linked_spec_file(self):
        validator = load_module("validate_project_artifacts", "scripts/validate_project_artifacts.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            issue_id = "024-artifact-schema-and-doctor-gates"
            self.write_loop_project(root, issue_id)

            result = validator.validate_project(root)

            self.assertFalse(result["valid"])
            self.assertTrue(
                any(f"issues/{issue_id}.md: linked artifact missing: specs/{issue_id}/spec.md" in error for error in result["errors"])
            )

    def test_validate_project_artifacts_reports_dashboard_active_issue_drift(self):
        validator = load_module("validate_project_artifacts", "scripts/validate_project_artifacts.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            issue_id = "024-artifact-schema-and-doctor-gates"
            self.write_loop_project(root, issue_id)
            (root / "specs" / issue_id).mkdir(parents=True)
            (root / "specs" / issue_id / "spec.md").write_text("# Spec\n", encoding="utf-8")
            (root / "workspace" / "dashboard.md").write_text("# Dashboard\n\n- `023-worker-routing-and-isolation`\n", encoding="utf-8")

            result = validator.validate_project(root)

            self.assertFalse(result["valid"])
            self.assertTrue(
                any("workspace/dashboard.md: missing active_issue_id 024-artifact-schema-and-doctor-gates" in error for error in result["errors"])
            )

    def test_validate_project_artifacts_reports_team_workflow_drift(self):
        validator = load_module("validate_project_artifacts", "scripts/validate_project_artifacts.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            issue_id = "035-team-issue-branch-pr-workflow"
            self.write_loop_project(root, issue_id, next_command=f"product:execute {issue_id}")
            issue_text = (root / "issues" / f"{issue_id}.md").read_text(encoding="utf-8")
            (root / "issues" / f"{issue_id}.md").write_text(
                issue_text.replace("- [ ] spec", "- [x] spec").replace("- [ ] plan", "- [x] plan"),
                encoding="utf-8",
            )
            (root / "specs" / issue_id).mkdir(parents=True)
            (root / "specs" / issue_id / "spec.md").write_text("# Spec\n", encoding="utf-8")
            (root / "specs" / issue_id / "plan.md").write_text("# Plan\n", encoding="utf-8")
            (root / "workflow" / "team-state.json").write_text(
                json.dumps({
                    "schema": "moduflow.team-state.v1",
                    "items": [
                        {
                            "issue_id": issue_id,
                            "status": "review",
                            "assignee": "Minsu",
                            "branch": "codex/035-team-issue-branch-pr-workflow",
                        }
                    ],
                }) + "\n",
                encoding="utf-8",
            )

            result = validator.validate_project(root)

            self.assertFalse(result["valid"])
            self.assertTrue(
                any("review state requires reviewer and pr" in error for error in result["errors"])
            )

    # Retired in 048: loop-state.json next_command/phase coupling is no longer a
    # lifecycle gate (loop-state is dormant; the gate keys off .moduflow/state.json).

    def test_project_doctor_surfaces_schema_gate_errors(self):
        project_doctor = load_module("project_doctor", "scripts/project_doctor.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            issue_id = "024-artifact-schema-and-doctor-gates"
            self.write_loop_project(root, issue_id, next_command=f"product:plan {issue_id}")

            result = project_doctor.inspect_project(root)

            self.assertTrue(
                any("schema gate failed" in recommendation for recommendation in result["recommendation"])
            )
            self.assertTrue(result["schema_gates"]["errors"])

    def test_project_doctor_can_skip_git_and_github_preflight(self):
        project_doctor = load_module("project_doctor", "scripts/project_doctor.py")
        shell_calls = []
        original_run = project_doctor.run

        def tracking_run(args, cwd):
            shell_calls.append(args)
            return original_run(args, cwd)

        project_doctor.run = tracking_run
        try:
            result = project_doctor.inspect_project(ROOT, include_preflight=False)
        finally:
            project_doctor.run = original_run

        self.assertFalse(result["preflight"]["enabled"])
        self.assertIn("git", result["preflight"]["skipped"])
        self.assertIn("github_cli", result["preflight"]["skipped"])
        self.assertFalse(any(args and args[0] in {"git", "gh"} for args in shell_calls))
        self.assertIn("moduflow", result)
        self.assertIn("schema_gates", result)

    def test_project_doctor_preflight_enabled_by_default(self):
        project_doctor = load_module("project_doctor", "scripts/project_doctor.py")

        result = project_doctor.inspect_project(ROOT)

        self.assertTrue(result["preflight"]["enabled"])

    def test_project_doctor_local_only_detects_project_root_from_subdirectory(self):
        project_doctor = load_module("project_doctor", "scripts/project_doctor.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.create_minimal_project(root)
            subdir = root / "workspace"

            result = project_doctor.inspect_project(subdir, include_preflight=False)

            self.assertEqual(result["project_root"], str(root.resolve()))
            self.assertTrue(result["moduflow"]["initialized"])


    def test_portfolio_doctor_warns_for_missing_project_path(self):
        portfolio_doctor = load_module("portfolio_doctor", "scripts/portfolio_doctor.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            missing_project = root / "missing"
            (root / "projects.json").write_text(
                json.dumps({"projects": [{"id": "missing", "name": "Missing", "path": str(missing_project)}]}) + "\n",
                encoding="utf-8",
            )

            result = portfolio_doctor.inspect_portfolio(root)

            self.assertFalse(result["valid"])
            self.assertTrue(any("missing" in warning for warning in result["warnings"]))

    def test_project_doctor_exit_zero_for_initialized_repo(self):
        # The ModuFlow repo itself is initialized (missing == []), so the gate passes.
        proc = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "project_doctor.py"), str(ROOT)],
            capture_output=True,
        )
        self.assertEqual(proc.returncode, 0)

    def test_project_doctor_exit_nonzero_for_uninitialized(self):
        # An empty (non-ModuFlow, non-git) directory must fail the gate, not silently pass.
        with tempfile.TemporaryDirectory() as tmp:
            proc = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "project_doctor.py"), tmp],
                capture_output=True,
            )
            self.assertEqual(proc.returncode, 1)

    def test_project_doctor_cli_exits_nonzero_for_hard_issue_schema_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.create_minimal_project(root)
            (root / "issues" / "BIZ-HARD.md").write_text(
                """---
schema_version: 9.9.9
issue_id: BIZ-HARD
---
# Unsupported

**Status: backlog** — created 2026-07-25.
""",
                encoding="utf-8",
            )

            proc = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "project_doctor.py"),
                    str(root),
                    "--no-preflight",
                ],
                capture_output=True,
                text=True,
            )

        payload = json.loads(proc.stdout)
        self.assertEqual(proc.returncode, 1)
        self.assertFalse(payload["schema_gates"]["valid"])
        self.assertIn("ISSUE_SCHEMA_UNSUPPORTED", payload["issue_schema"]["codes"])

    def test_project_doctor_cli_keeps_warning_only_issue_schema_at_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.create_minimal_project(root)
            (root / "issues" / "BIZ-ADVISORY.md").write_text(
                """---
issue_id: BIZ-ADVISORY
---
# Advisory

**Status: backlog** — created 2026-07-25.
""",
                encoding="utf-8",
            )

            proc = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "project_doctor.py"),
                    str(root),
                    "--no-preflight",
                ],
                capture_output=True,
                text=True,
            )

        payload = json.loads(proc.stdout)
        self.assertEqual(proc.returncode, 0)
        self.assertTrue(payload["schema_gates"]["valid"])
        self.assertEqual(payload["issue_schema"]["errors"], 0)
        self.assertGreaterEqual(payload["issue_schema"]["warnings"], 1)

    def test_release_check_succeeds_for_current_repo(self):
        release_check = load_module("release_check", "scripts/release_check.py")

        result = release_check.run_release_check(ROOT)

        self.assertTrue(result["valid"])
        self.assertEqual(result["errors"], [])
        self.assertIn("validate_moduflow", result["checks"])
        self.assertIn("spec_kit_pilot_provenance", result["checks"])
        self.assertTrue(result["checks"]["spec_kit_pilot_provenance"]["ok"])

    def test_release_check_uses_importable_validation_for_safe_checks(self):
        release_check = load_module("release_check", "scripts/release_check.py")
        original_run_command = release_check.run_command
        shell_calls = []

        def tracking_run_command(args, cwd):
            shell_calls.append(args)
            return original_run_command(args, cwd)

        release_check.run_command = tracking_run_command
        try:
            result = release_check.run_release_check(ROOT)
        finally:
            release_check.run_command = original_run_command

        self.assertTrue(result["valid"])
        self.assertFalse(
            any(args[:2] == ["python3", "scripts/validate_moduflow.py"] for args in shell_calls)
        )
        self.assertFalse(
            any(args[:2] == ["python3", "scripts/validate_project_artifacts.py"] for args in shell_calls)
        )
        self.assertTrue(any(args[:3] == ["python3", "-m", "unittest"] for args in shell_calls))

    def test_project_doctor_detects_dogfooding_mode(self):
        project_doctor = load_module("project_doctor", "scripts/project_doctor.py")
        result = project_doctor.inspect_project(ROOT)
        self.assertEqual(result["mode"], "dogfooding")

    def test_project_doctor_detects_lightweight_mode(self):
        project_doctor = load_module("project_doctor", "scripts/project_doctor.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            # Initialize minimal project (lightweight)
            (root / ".moduflow").mkdir(parents=True, exist_ok=True)
            (root / ".moduflow" / "config.json").write_text("{}", encoding="utf-8")
            (root / ".moduflow" / "state.json").write_text("{}", encoding="utf-8")
            (root / "workspace").mkdir(parents=True, exist_ok=True)
            (root / "workspace" / "inbox.md").write_text("", encoding="utf-8")
            (root / "workspace" / "opportunities.md").write_text("", encoding="utf-8")
            (root / "workspace" / "roadmap.md").write_text("", encoding="utf-8")
            (root / "workspace" / "dashboard.md").write_text("", encoding="utf-8")
            (root / "issues").mkdir(parents=True, exist_ok=True)
            (root / "specs").mkdir(parents=True, exist_ok=True)
            
            result = project_doctor.inspect_project(root)
            self.assertEqual(result["mode"], "lightweight")

    def test_project_doctor_detects_heavy_mode(self):
        project_doctor = load_module("project_doctor", "scripts/project_doctor.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            # Initialize minimal project
            (root / ".moduflow").mkdir(parents=True, exist_ok=True)
            (root / ".moduflow" / "config.json").write_text("{}", encoding="utf-8")
            (root / ".moduflow" / "state.json").write_text("{}", encoding="utf-8")
            (root / "workspace").mkdir(parents=True, exist_ok=True)
            (root / "workspace" / "inbox.md").write_text("", encoding="utf-8")
            (root / "workspace" / "opportunities.md").write_text("", encoding="utf-8")
            (root / "workspace" / "roadmap.md").write_text("", encoding="utf-8")
            (root / "workspace" / "dashboard.md").write_text("", encoding="utf-8")
            (root / "issues").mkdir(parents=True, exist_ok=True)
            (root / "specs").mkdir(parents=True, exist_ok=True)
            # Add legacy tooling dir
            (root / "commands").mkdir(parents=True, exist_ok=True)
            (root / "commands" / "dummy.md").write_text("dummy", encoding="utf-8")
            
            result = project_doctor.inspect_project(root)
            self.assertEqual(result["mode"], "heavy")

    def test_project_doctor_keeps_raw_mode_and_adds_user_guidance(self):
        project_doctor = load_module("project_doctor", "scripts/project_doctor.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".moduflow").mkdir(parents=True, exist_ok=True)
            (root / ".moduflow" / "config.json").write_text("{}", encoding="utf-8")
            (root / ".moduflow" / "state.json").write_text("{}", encoding="utf-8")
            (root / "workspace").mkdir(parents=True, exist_ok=True)
            for filename in ["inbox.md", "opportunities.md", "roadmap.md", "dashboard.md"]:
                (root / "workspace" / filename).write_text("", encoding="utf-8")
            (root / "issues").mkdir(parents=True, exist_ok=True)
            (root / "specs").mkdir(parents=True, exist_ok=True)

            result = project_doctor.inspect_project(root)

            self.assertEqual(result["mode"], "lightweight")
            self.assertEqual(
                result["mode_guidance"]["message"],
                "프로젝트 설정이 가볍고 정상입니다.",
            )
            self.assertIn("commands", result["mode_guidance"]["details"])
            self.assertNotEqual(result["mode_guidance"]["label"], "lightweight")

    def test_release_check_fails_on_syntax_and_security_violations(self):
        release_check = load_module("release_check", "scripts/release_check.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for relative in ["docs", "scripts"]:
                (root / relative).mkdir()
            (root / "docs" / "release-checklist.md").write_text("# Checklist\n", encoding="utf-8")
            (root / "docs" / "upgrade-guide.md").write_text("# Upgrade\n", encoding="utf-8")

            # Create a file with credential leakage
            leak_file = root / "scripts" / "secrets.py"
            leak_file.write_text("API_KEY = \"my-secret-key-123456\"\n", encoding="utf-8")

            # Mock get_modified_python_files to return the leak file
            orig_get_modified = release_check.get_modified_python_files
            try:
                release_check.get_modified_python_files = (
                    lambda r, *a, **k: {"files": [leak_file], "errors": []}
                )
                result = release_check.run_release_check(root)
            finally:
                release_check.get_modified_python_files = orig_get_modified

            self.assertFalse(result["valid"])
            self.assertFalse(result["checks"]["security_check"]["ok"])

            # Test a syntax error
            leak_file.write_text("this is a syntax error !!!\n", encoding="utf-8")

            orig_get_modified = release_check.get_modified_python_files
            try:
                release_check.get_modified_python_files = (
                    lambda r, *a, **k: {"files": [leak_file], "errors": []}
                )
                result = release_check.run_release_check(root)
            finally:
                release_check.get_modified_python_files = orig_get_modified

            self.assertFalse(result["valid"])
            self.assertFalse(result["checks"]["lint_check"]["ok"])


if __name__ == "__main__":
    unittest.main()
