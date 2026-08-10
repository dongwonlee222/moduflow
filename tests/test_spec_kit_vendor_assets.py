import copy
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ADAPTER_PATH = ROOT / "scripts" / "spec_kit_adapter.py"
SYNC_PATH = ROOT / "scripts" / "sync_spec_kit_templates.py"
APPROVED_SHA = "684b3d8e05263a7c1948d3d0699ab1cb4f77c3d5"
EXPECTED = {
    "clarify": "9fce9b3dfe037b67f52486df112f89377ff6c0c598698131cde65cec610b5bba",
    "analyze": "79f5334bce9b249d4c1a5e6949dee3f3532db89a0a97f3d2eb55c1a1c2fe06f6",
    "checklist": "0a862264b9b358138d6049590d42b392ee4dadb69d32811d460620f077924d4e",
    "converge": "aafba511dea42334373c7ffb9f58e2fb6d82889ea94ec86c1367dbb6a531ca36",
}


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SpecKitVendorAssetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ska = load_module(ADAPTER_PATH, "spec_kit_adapter_vendor_test")

    def test_manifest_allows_exactly_four_verified_templates(self):
        manifest = self.ska.load_manifest(ROOT)

        self.assertEqual(set(manifest["functions"]), set(EXPECTED))
        self.assertEqual(
            {record["function"]: record["actual_sha256"]
             for record in self.ska.verify_assets(ROOT, manifest)},
            EXPECTED,
        )

    def test_manifest_rejects_an_extra_template_before_it_can_be_loaded(self):
        manifest = self.ska.load_manifest(ROOT)
        manifest["functions"]["implement"] = copy.deepcopy(manifest["functions"]["analyze"])

        with self.assertRaisesRegex(self.ska.SpecKitAdapterError, "invalid_manifest"):
            self.ska.verify_assets(ROOT, manifest)

    def test_manifest_rejects_a_template_path_that_escapes_commands(self):
        manifest = self.ska.load_manifest(ROOT)
        manifest["functions"]["analyze"]["template"] = "../outside.md"

        with self.assertRaisesRegex(self.ska.SpecKitAdapterError, "unsafe_path"):
            self.ska.verify_assets(ROOT, manifest)

    def test_manifest_rejects_a_symlinked_template_path(self):
        with tempfile.TemporaryDirectory() as directory:
            package = Path(directory)
            manifest_path = package / "vendor/spec-kit/0.16.1/manifest.json"
            command_path = manifest_path.parent / "commands"
            command_path.mkdir(parents=True)
            source_manifest = self.ska.load_manifest(ROOT)
            manifest_path.write_text(json.dumps(source_manifest), encoding="utf-8")
            outside = package / "outside.md"
            outside.write_bytes((ROOT / "vendor/spec-kit/0.16.1/commands/analyze.md").read_bytes())
            (command_path / "analyze.md").symlink_to(outside)
            for function in ("clarify", "checklist", "converge"):
                (command_path / f"{function}.md").write_bytes(
                    (ROOT / f"vendor/spec-kit/0.16.1/commands/{function}.md").read_bytes()
                )

            with self.assertRaisesRegex(self.ska.SpecKitAdapterError, "unsafe_path"):
                self.ska.verify_assets(package, self.ska.load_manifest(package))

    def test_one_byte_template_drift_makes_a_handoff_unavailable_without_a_template(self):
        with tempfile.TemporaryDirectory() as directory:
            package = Path(directory)
            source = ROOT / "vendor/spec-kit/0.16.1"
            destination = package / "vendor/spec-kit/0.16.1"
            (destination / "commands").mkdir(parents=True)
            (destination / "manifest.json").write_bytes((source / "manifest.json").read_bytes())
            for function in EXPECTED:
                content = (source / "commands" / f"{function}.md").read_bytes()
                (destination / "commands" / f"{function}.md").write_bytes(content)
            drifted = destination / "commands/analyze.md"
            drifted.write_bytes(drifted.read_bytes() + b"x")
            project = package / "project"
            config_path = project / ".moduflow/capabilities.json"
            config_path.parent.mkdir(parents=True)
            config_path.write_text(json.dumps({
                "schema": "moduflow.capabilities.v1",
                "capabilities": {"spec-kit": {
                    "enabled": True,
                    "source_version": "0.16.1",
                    "source_sha": APPROVED_SHA,
                    "functions": ["analyze"],
                }},
            }), encoding="utf-8")

            result = self.ska.build_handoff(
                package, project, "098-speckit-selective-validation-adapter", "analyze", True
            )

        self.assertEqual(result["outcome"], "unavailable")
        self.assertIsNone(result["source"]["template"])

    def test_manifest_rejects_wrong_source_sha(self):
        manifest = self.ska.load_manifest(ROOT)
        manifest["source"]["sha"] = "0" * 40

        with self.assertRaisesRegex(self.ska.SpecKitAdapterError, "unapproved_source"):
            self.ska.verify_assets(ROOT, manifest)


class SpecKitTemplateSyncTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sync = load_module(SYNC_PATH, "sync_spec_kit_templates_test")
        cls.snapshot = {
            function: (ROOT / f"vendor/spec-kit/0.16.1/commands/{function}.md").read_bytes()
            for function in EXPECTED
        }

    def downloader(self, url):
        function = url.rsplit("/", 1)[-1].removesuffix(".md")
        return self.snapshot[function]

    def test_dry_run_verifies_all_templates_without_writing_destinations(self):
        with tempfile.TemporaryDirectory() as directory:
            package = Path(directory)
            records = self.sync.sync_templates(package, self.downloader, write=False)

            self.assertEqual({record["function"] for record in records}, set(EXPECTED))
            self.assertFalse((package / "vendor/spec-kit/0.16.1/commands").exists())

    def test_explicit_write_installs_only_the_verified_four_templates(self):
        with tempfile.TemporaryDirectory() as directory:
            package = Path(directory)
            self.sync.sync_templates(package, self.downloader, write=True)
            commands = package / "vendor/spec-kit/0.16.1/commands"

            self.assertEqual({path.name for path in commands.iterdir()}, {
                "clarify.md", "analyze.md", "checklist.md", "converge.md",
            })
            self.assertEqual(
                hashlib.sha256((commands / "converge.md").read_bytes()).hexdigest(),
                EXPECTED["converge"],
            )

    def test_network_failure_creates_no_partial_destination(self):
        def failed_downloader(url):
            raise OSError("network unreachable")

        with tempfile.TemporaryDirectory() as directory:
            package = Path(directory)
            with self.assertRaisesRegex(self.sync.SpecKitSyncError, "download_failed"):
                self.sync.sync_templates(package, failed_downloader, write=True)
            self.assertFalse((package / "vendor/spec-kit/0.16.1/commands").exists())

    def test_hash_failure_creates_no_partial_destination(self):
        def drifted_downloader(url):
            return self.downloader(url) + b"x"

        with tempfile.TemporaryDirectory() as directory:
            package = Path(directory)
            with self.assertRaisesRegex(self.sync.SpecKitSyncError, "hash_mismatch"):
                self.sync.sync_templates(package, drifted_downloader, write=True)
            self.assertFalse((package / "vendor/spec-kit/0.16.1/commands").exists())
