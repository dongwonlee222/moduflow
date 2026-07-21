import importlib.util
import json
import tempfile
import unittest
import sys
import io
from contextlib import redirect_stdout
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "project_repository_identity.py"


def load_identity_module():
    if not MODULE_PATH.exists():
        return None
    spec = importlib.util.spec_from_file_location("project_repository_identity", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_config(root, git_config):
    target = Path(root) / ".moduflow" / "config.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps({"schema": "moduflow.config.v1", "git": git_config}),
        encoding="utf-8",
    )


@dataclass
class CommandResult:
    returncode: int
    stdout: str = ""
    stderr: str = ""


def ok(stdout=""):
    return CommandResult(0, stdout, "")


def failed(stderr="command failed"):
    return CommandResult(1, "", stderr)


class FakeRunner:
    def __init__(self, responses):
        self.responses = responses
        self.calls = []

    def __call__(self, args, cwd):
        key = tuple(args)
        self.calls.append((key, str(cwd)))
        return self.responses.get(key, failed(f"unexpected command: {' '.join(args)}"))


def github_provider(
    repository="github.com/owner/repo",
    default_branch="main",
    archived=False,
    fork=False,
):
    def check(canonical_repository, root, runner):
        return {
            "ok": True,
            "repository": repository,
            "default_branch": default_branch,
            "archived": archived,
            "fork": fork,
        }

    return check


def unavailable_provider(canonical_repository, root, runner):
    return {
        "ok": False,
        "reason": "provider_unavailable",
        "detail": "GitHub API is unavailable.",
    }


def reason_codes(result):
    return {reason["code"] for reason in result["reasons"]}


class RepositoryUrlTests(unittest.TestCase):
    def setUp(self):
        self.module = load_identity_module()

    def normalize(self, value, provider):
        self.assertIsNotNone(self.module, "scripts/project_repository_identity.py must exist")
        function = getattr(self.module, "normalize_git_url", None)
        self.assertTrue(callable(function), "normalize_git_url must be implemented")
        return function(value, provider)

    def test_github_url_forms_normalize_to_one_identity(self):
        values = [
            "https://github.com/Owner/Repo.git",
            "ssh://git@github.com/Owner/Repo.git",
            "git@github.com:Owner/Repo.git",
        ]

        normalized = {self.normalize(value, "github") for value in values}

        self.assertEqual(normalized, {"github.com/owner/repo"})

    def test_github_normalization_removes_default_ports_and_trailing_slashes(self):
        self.assertEqual(
            self.normalize("ssh://git@GitHub.com:22/Owner/Repo.git/", "github"),
            "github.com/owner/repo",
        )
        self.assertEqual(
            self.normalize("https://GitHub.com:443/Owner/Repo/", "github"),
            "github.com/owner/repo",
        )

    def test_generic_provider_preserves_repository_path_case(self):
        self.assertEqual(
            self.normalize("ssh://git@Git.Example.com/Team/Repo.git", "generic"),
            "git.example.com/Team/Repo",
        )

    def test_credentials_never_appear_in_normalized_value_or_error(self):
        value = "https://oauth2:secret-token@github.com/Owner/Repo.git"

        normalized = self.normalize(value, "github")

        self.assertEqual(normalized, "github.com/owner/repo")
        self.assertNotIn("oauth2", normalized)
        self.assertNotIn("secret-token", normalized)

    def test_github_rejects_extra_path_components(self):
        self.assertIsNotNone(self.module, "scripts/project_repository_identity.py must exist")
        error_type = getattr(self.module, "IdentityConfigError", None)
        self.assertTrue(isinstance(error_type, type), "IdentityConfigError must be implemented")

        with self.assertRaises(error_type):
            self.normalize("https://github.com/Owner/Repo/extra", "github")

    def test_remote_mode_rejects_local_filesystem_paths(self):
        self.assertIsNotNone(self.module, "scripts/project_repository_identity.py must exist")
        error_type = getattr(self.module, "IdentityConfigError", None)
        self.assertTrue(isinstance(error_type, type), "IdentityConfigError must be implemented")

        for value in ["../repo", "/tmp/repo", "file:///tmp/repo"]:
            with self.subTest(value=value):
                with self.assertRaises(error_type):
                    self.normalize(value, "github")

    def test_github_artifact_url_resolves_repository_through_shared_parser(self):
        self.assertIsNotNone(self.module)
        function = getattr(self.module, "repository_from_github_artifact_url", None)
        self.assertTrue(
            callable(function),
            "repository_from_github_artifact_url must be implemented",
        )

        self.assertEqual(
            function("https://github.com/Owner/Repo/issues/42"),
            "github.com/owner/repo",
        )
        self.assertEqual(
            function("https://github.com/Owner/Repo/pull/7"),
            "github.com/owner/repo",
        )


class RepositoryConfigTests(unittest.TestCase):
    def setUp(self):
        self.module = load_identity_module()

    def load(self, root):
        self.assertIsNotNone(self.module, "scripts/project_repository_identity.py must exist")
        function = getattr(self.module, "load_repository_identity", None)
        self.assertTrue(callable(function), "load_repository_identity must be implemented")
        return function(root)

    def test_loads_valid_remote_identity_without_using_legacy_remote_as_truth(self):
        with tempfile.TemporaryDirectory() as tmp:
            write_config(
                tmp,
                {
                    "remote": "https://github.com/wrong/legacy",
                    "identity": {
                        "mode": "remote",
                        "provider": "github",
                        "canonical_repository": "github.com/Owner/Repo",
                        "remote_name_hint": "upstream",
                        "base_branch": "main",
                        "lifecycle": "active",
                    },
                },
            )

            result = self.load(tmp)

        self.assertTrue(result["configured"])
        self.assertEqual(result["identity"]["canonical_repository"], "github.com/owner/repo")
        self.assertEqual(result["identity"]["remote_name_hint"], "upstream")
        self.assertEqual(result["reasons"], [])

    def test_legacy_remote_without_identity_is_unconfigured(self):
        with tempfile.TemporaryDirectory() as tmp:
            write_config(tmp, {"remote": "https://github.com/Owner/Repo"})

            result = self.load(tmp)

        self.assertFalse(result["configured"])
        self.assertIsNone(result["identity"])
        self.assertEqual(result["reasons"][0]["code"], "canonical_identity_missing")

    def test_local_only_requires_base_branch_and_lifecycle_but_no_remote(self):
        with tempfile.TemporaryDirectory() as tmp:
            write_config(
                tmp,
                {
                    "identity": {
                        "mode": "local_only",
                        "provider": "generic",
                        "base_branch": "main",
                        "lifecycle": "active",
                    }
                },
            )

            result = self.load(tmp)

        self.assertTrue(result["configured"])
        self.assertEqual(result["identity"]["mode"], "local_only")
        self.assertNotIn("canonical_repository", result["identity"])
        self.assertNotIn("remote_name_hint", result["identity"])

    def test_invalid_enum_returns_explicit_configuration_reason(self):
        with tempfile.TemporaryDirectory() as tmp:
            write_config(
                tmp,
                {
                    "identity": {
                        "mode": "remote",
                        "provider": "github",
                        "canonical_repository": "github.com/Owner/Repo",
                        "remote_name_hint": "origin",
                        "base_branch": "main",
                        "lifecycle": "frozen",
                    }
                },
            )

            result = self.load(tmp)

        self.assertFalse(result["configured"])
        self.assertEqual(result["reasons"][0]["code"], "canonical_identity_invalid")
        self.assertIn("lifecycle", result["reasons"][0]["message"])

    def test_missing_config_is_unconfigured_not_an_exception(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.load(tmp)

        self.assertFalse(result["configured"])
        self.assertEqual(result["reasons"][0]["code"], "canonical_identity_missing")


class RepositoryInspectionTests(unittest.TestCase):
    def setUp(self):
        self.module = load_identity_module()
        self.assertIsNotNone(self.module)
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.root = Path(self.temp_dir.name)
        write_config(
            self.root,
            {
                "identity": {
                    "mode": "remote",
                    "provider": "github",
                    "canonical_repository": "github.com/Owner/Repo",
                    "remote_name_hint": "origin",
                    "base_branch": "main",
                    "lifecycle": "active",
                }
            },
        )

    def inspect(self, responses, provider_check=None):
        function = getattr(self.module, "inspect_repository_identity", None)
        self.assertTrue(callable(function), "inspect_repository_identity must be implemented")
        return function(
            self.root,
            runner=FakeRunner(responses),
            provider_check=provider_check,
        )

    def matching_responses(self):
        return {
            ("git", "rev-parse", "--show-toplevel"): ok(f"{self.root}\n"),
            ("git", "remote", "get-url", "--all", "origin"): ok(
                "https://github.com/Owner/Repo.git\n"
            ),
            ("git", "remote", "get-url", "--push", "--all", "origin"): ok(
                "git@github.com:owner/repo.git\n"
            ),
            ("git", "rev-parse", "--abbrev-ref", "HEAD"): ok("codex/088-identity\n"),
            ("git", "show-ref", "--verify", "--quiet", "refs/remotes/origin/main"): ok(),
        }

    def test_match_reports_all_evidence_and_capabilities(self):
        result = self.inspect(self.matching_responses(), github_provider())

        self.assertEqual(result["schema"], "moduflow.repository-identity.v1")
        self.assertEqual(result["status"], "match")
        self.assertEqual(
            result["observed"]["fetch_repositories"],
            ["github.com/owner/repo"],
        )
        self.assertEqual(
            result["observed"]["push_repositories"],
            ["github.com/owner/repo"],
        )
        self.assertEqual(result["observed"]["current_branch"], "codex/088-identity")
        self.assertEqual(result["observed"]["base_ref"], "refs/remotes/origin/main")
        self.assertTrue(all(result["capabilities"].values()))

    def test_origin_name_cannot_hide_wrong_fetch_repository(self):
        responses = self.matching_responses()
        responses[("git", "remote", "get-url", "--all", "origin")] = ok(
            "git@github.com:other/repo.git\n"
        )

        result = self.inspect(responses, github_provider())

        self.assertEqual(result["status"], "mismatch")
        self.assertIn("fetch_remote_mismatch", reason_codes(result))
        self.assertFalse(result["capabilities"]["execute"])
        self.assertFalse(result["capabilities"]["commit"])

    def test_accidental_parent_git_root_blocks_execution_and_writes(self):
        responses = self.matching_responses()
        responses[("git", "rev-parse", "--show-toplevel")] = ok(
            f"{self.root.parent}\n"
        )

        result = self.inspect(responses, github_provider())

        self.assertEqual(result["status"], "mismatch")
        self.assertIn("git_root_mismatch", reason_codes(result))
        self.assertFalse(result["capabilities"]["execute"])
        self.assertFalse(result["capabilities"]["commit"])
        self.assertFalse(result["capabilities"]["push"])
        self.assertFalse(result["capabilities"]["github_write"])
        self.assertFalse(result["capabilities"]["release"])

    def test_different_push_repository_blocks_commit_push_and_github_but_not_execute(self):
        responses = self.matching_responses()
        responses[("git", "remote", "get-url", "--push", "--all", "origin")] = ok(
            "git@github.com:other/repo.git\n"
        )

        result = self.inspect(responses, github_provider())

        self.assertIn("push_remote_mismatch", reason_codes(result))
        self.assertTrue(result["capabilities"]["execute"])
        self.assertFalse(result["capabilities"]["commit"])
        self.assertFalse(result["capabilities"]["push"])
        self.assertFalse(result["capabilities"]["github_write"])
        self.assertFalse(result["capabilities"]["release"])

    def test_missing_base_ref_blocks_all_write_capabilities(self):
        responses = self.matching_responses()
        responses[("git", "show-ref", "--verify", "--quiet", "refs/remotes/origin/main")] = failed()
        responses[("git", "show-ref", "--verify", "--quiet", "refs/heads/main")] = failed()

        result = self.inspect(responses, github_provider())

        self.assertIn("base_branch_missing", reason_codes(result))
        self.assertTrue(result["capabilities"]["read"])
        for capability in ["execute", "commit", "push", "github_write", "release"]:
            self.assertFalse(result["capabilities"][capability])

    def test_provider_unavailable_preserves_local_capabilities_but_blocks_github(self):
        result = self.inspect(self.matching_responses(), unavailable_provider)

        self.assertEqual(result["status"], "unverifiable")
        self.assertIn("provider_unavailable", reason_codes(result))
        self.assertTrue(result["capabilities"]["execute"])
        self.assertTrue(result["capabilities"]["commit"])
        self.assertTrue(result["capabilities"]["push"])
        self.assertFalse(result["capabilities"]["github_write"])
        self.assertFalse(result["capabilities"]["release"])

    def test_provider_default_branch_mismatch_only_blocks_provider_writes(self):
        result = self.inspect(
            self.matching_responses(),
            github_provider(default_branch="trunk"),
        )

        self.assertEqual(result["status"], "mismatch")
        self.assertIn("provider_default_branch_mismatch", reason_codes(result))
        self.assertTrue(result["capabilities"]["push"])
        self.assertFalse(result["capabilities"]["github_write"])
        self.assertFalse(result["capabilities"]["release"])

    def test_provider_fork_is_a_deterministic_mismatch(self):
        result = self.inspect(self.matching_responses(), github_provider(fork=True))

        self.assertEqual(result["status"], "mismatch")
        self.assertIn("provider_repository_is_fork", reason_codes(result))
        self.assertFalse(result["capabilities"]["github_write"])
        self.assertFalse(result["capabilities"]["release"])

    def test_multiple_fetch_or_push_urls_are_all_reported_and_checked(self):
        responses = self.matching_responses()
        responses[("git", "remote", "get-url", "--all", "origin")] = ok(
            "https://github.com/Owner/Repo.git\ngit@github.com:other/repo.git\n"
        )
        responses[("git", "remote", "get-url", "--push", "--all", "origin")] = ok(
            "git@github.com:owner/repo.git\ngit@github.com:other/repo.git\n"
        )

        result = self.inspect(responses, github_provider())

        self.assertEqual(len(result["observed"]["fetch_repositories"]), 2)
        self.assertEqual(len(result["observed"]["push_repositories"]), 2)
        self.assertIn("fetch_remote_mismatch", reason_codes(result))
        self.assertIn("push_remote_mismatch", reason_codes(result))

    def test_stale_pr_handoff_link_blocks_github_and_release_capabilities(self):
        spec_dir = self.root / "specs" / "088-test"
        spec_dir.mkdir(parents=True)
        (spec_dir / "pr.md").write_text(
            "# PR\n\nGitHub PR: https://github.com/other/repo/pull/9\n",
            encoding="utf-8",
        )

        result = self.inspect(self.matching_responses(), github_provider())

        self.assertIn("artifact_write_repository_mismatch", reason_codes(result))
        self.assertTrue(result["capabilities"]["push"])
        self.assertFalse(result["capabilities"]["github_write"])
        self.assertFalse(result["capabilities"]["release"])


class RepositoryPolicyTests(unittest.TestCase):
    def setUp(self):
        self.module = load_identity_module()
        self.assertIsNotNone(self.module)
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.root = Path(self.temp_dir.name)

    def inspect(self, git_identity, responses):
        write_config(self.root, {"identity": git_identity})
        function = getattr(self.module, "inspect_repository_identity", None)
        self.assertTrue(callable(function), "inspect_repository_identity must be implemented")
        return function(self.root, runner=FakeRunner(responses))

    def decide(self, result, operation):
        function = getattr(self.module, "operation_decision", None)
        self.assertTrue(callable(function), "operation_decision must be implemented")
        return function(result, operation)

    def local_responses(self):
        return {
            ("git", "rev-parse", "--show-toplevel"): ok(f"{self.root}\n"),
            ("git", "rev-parse", "--abbrev-ref", "HEAD"): ok("feature/local\n"),
            ("git", "show-ref", "--verify", "--quiet", "refs/heads/main"): ok(),
        }

    def test_local_only_allows_local_execute_and_commit_but_never_remote_writes(self):
        result = self.inspect(
            {
                "mode": "local_only",
                "provider": "generic",
                "base_branch": "main",
                "lifecycle": "active",
            },
            self.local_responses(),
        )

        self.assertEqual(result["status"], "local_only")
        self.assertTrue(self.decide(result, "execute")["allowed"])
        self.assertTrue(self.decide(result, "commit")["allowed"])
        self.assertFalse(self.decide(result, "push")["allowed"])
        self.assertFalse(self.decide(result, "github_issue")["allowed"])
        self.assertFalse(self.decide(result, "release")["allowed"])

    def test_generic_remote_never_advertises_github_or_release_capabilities(self):
        result = self.inspect(
            {
                "mode": "remote",
                "provider": "generic",
                "canonical_repository": "git.example.com/Team/Repo",
                "remote_name_hint": "origin",
                "base_branch": "main",
                "lifecycle": "active",
            },
            {
                ("git", "rev-parse", "--show-toplevel"): ok(f"{self.root}\n"),
                ("git", "rev-parse", "--abbrev-ref", "HEAD"): ok("feature/generic\n"),
                ("git", "show-ref", "--verify", "--quiet", "refs/remotes/origin/main"): ok(),
                ("git", "remote", "get-url", "--all", "origin"): ok(
                    "ssh://git@git.example.com/Team/Repo.git\n"
                ),
                ("git", "remote", "get-url", "--push", "--all", "origin"): ok(
                    "ssh://git@git.example.com/Team/Repo.git\n"
                ),
            },
        )

        self.assertTrue(result["capabilities"]["execute"])
        self.assertTrue(result["capabilities"]["commit"])
        self.assertTrue(result["capabilities"]["push"])
        self.assertFalse(result["capabilities"]["github_write"])
        self.assertFalse(result["capabilities"]["release"])
        self.assertFalse(self.decide(result, "pr")["allowed"])
        self.assertFalse(self.decide(result, "release")["allowed"])

    def test_read_only_and_archived_lifecycles_allow_only_read(self):
        for lifecycle, expected_status, expected_reason in [
            ("read_only", "read_only", "repository_read_only"),
            ("archived", "archived", "repository_archived"),
        ]:
            with self.subTest(lifecycle=lifecycle):
                result = self.inspect(
                    {
                        "mode": "local_only",
                        "provider": "generic",
                        "base_branch": "main",
                        "lifecycle": lifecycle,
                    },
                    self.local_responses(),
                )
                self.assertEqual(result["status"], expected_status)
                self.assertIn(expected_reason, reason_codes(result))
                self.assertTrue(self.decide(result, "doctor")["allowed"])
                self.assertFalse(self.decide(result, "execute")["allowed"])
                self.assertFalse(self.decide(result, "commit")["allowed"])

    def test_unconfigured_identity_blocks_writes_but_allows_doctor(self):
        write_config(self.root, {"remote": "https://github.com/Owner/Repo"})
        function = getattr(self.module, "inspect_repository_identity", None)
        self.assertTrue(callable(function), "inspect_repository_identity must be implemented")
        result = function(self.root, runner=FakeRunner({}))

        self.assertEqual(result["status"], "unconfigured")
        self.assertTrue(self.decide(result, "status")["allowed"])
        self.assertFalse(self.decide(result, "execute")["allowed"])
        self.assertFalse(self.decide(result, "push")["allowed"])

    def test_unknown_operation_is_explicitly_blocked(self):
        result = {
            "schema": "moduflow.repository-identity.v1",
            "capabilities": {"read": True},
            "reasons": [],
        }

        decision = self.decide(result, "delete_repository")

        self.assertFalse(decision["allowed"])
        self.assertEqual(decision["reasons"][0]["code"], "unsupported_operation")


class RepositoryCliTests(unittest.TestCase):
    def test_cli_returns_three_for_denied_write_operation(self):
        module = load_identity_module()
        self.assertIsNotNone(module)
        main = getattr(module, "main", None)
        self.assertTrue(callable(main), "main must expose the identity operation CLI")
        identity = {
            "schema": "moduflow.repository-identity.v1",
            "status": "mismatch",
            "capabilities": {"read": True, "execute": False},
            "reasons": [{"code": "fetch_remote_mismatch", "message": "wrong repository"}],
        }
        original_inspect = module.inspect_repository_identity
        original_argv = sys.argv
        module.inspect_repository_identity = lambda root: identity
        sys.argv = [
            "project_repository_identity.py",
            ".",
            "--operation",
            "execute",
        ]
        try:
            with redirect_stdout(io.StringIO()) as output:
                result = main()
        finally:
            module.inspect_repository_identity = original_inspect
            sys.argv = original_argv

        self.assertEqual(result, 3)
        self.assertIn('"allowed": false', output.getvalue())


if __name__ == "__main__":
    unittest.main()
