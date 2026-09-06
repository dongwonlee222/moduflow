"""Issue 127 — completing an issue must release its execution binding, and the
branch rule must have an answer for work done on the base branch.

Both faults were found on 2026-09-05 in this repository's own
`workspace/loop-state.json`, which still carried issue 111's binding long after
111 was `done`: branch `codex/111-…`, five commits, and an execution backend
still marked `active`. Held separately each is survivable; together they refuse
every subsequent issue on a repository worked on `main`.
"""

import importlib.util
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))


def load_module(name, relative_path):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


project_loop = load_module("project_loop", "scripts/project_loop.py")


# The binding as found on 2026-09-05, verbatim apart from the issue id.
STALE_BINDING = {
    "mode": "git-files",
    "branch": "codex/111-runtime-provenance-and-validation-mode-separation",
    "base_branch": "main",
    "commits": ["a1e5ae6", "aac78e5", "a7ccdca", "517ec64", "b5c3ce3"],
    "pull_request": None,
    "release": None,
    "execution_backend": {
        "type": "codex",
        "status": "active",
        "reason": "User approved inline Issue 111 implementation",
        "session": None,
    },
}


def loop_bytes(binding=None, **extra):
    payload = {
        "schema": "moduflow.loop.v1",
        "issue_id": "111-runtime-provenance-and-validation-mode-separation",
        "phase": "execute",
        "git_binding": binding if binding is not None else dict(STALE_BINDING),
    }
    payload.update(extra)
    return (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def project(loop_input, *, action, target_lifecycle=None, issue_id="111-runtime-provenance-and-validation-mode-separation"):
    rendered = project_loop.render_loop_projection(
        loop_input,
        issue_id=issue_id,
        action=action,
        next_command="product:status",
        blocker=None,
        changed_on="2026-09-06",
        phase="execute",
        target_lifecycle=target_lifecycle,
    )
    return json.loads(rendered.decode("utf-8"))


class CompletionReleasesTheBinding(unittest.TestCase):
    def test_complete_clears_the_branch(self):
        state = project(loop_bytes(), action="complete", target_lifecycle="done")
        self.assertIsNone(state["git_binding"]["branch"])

    def test_complete_clears_the_commits(self):
        state = project(loop_bytes(), action="complete", target_lifecycle="done")
        self.assertEqual(state["git_binding"]["commits"], [])

    def test_complete_deactivates_the_execution_backend(self):
        state = project(loop_bytes(), action="complete", target_lifecycle="done")
        self.assertNotEqual(
            state["git_binding"]["execution_backend"]["status"], "active"
        )

    def test_complete_keeps_the_base_branch(self):
        """base_branch is repository configuration, not per-issue state."""
        state = project(loop_bytes(), action="complete", target_lifecycle="done")
        self.assertEqual(state["git_binding"]["base_branch"], "main")

    def test_complete_clears_the_pull_request_and_release(self):
        """Same class as the branch: per-issue state the next issue would inherit."""
        binding = dict(STALE_BINDING)
        binding["pull_request"] = "https://github.com/example/repo/pull/27"
        binding["release"] = "v0.3.60"
        state = project(loop_bytes(binding), action="complete", target_lifecycle="done")
        self.assertIsNone(state["git_binding"]["pull_request"])
        self.assertIsNone(state["git_binding"]["release"])

    def test_complete_keeps_the_binding_mode(self):
        state = project(loop_bytes(), action="complete", target_lifecycle="done")
        self.assertEqual(state["git_binding"]["mode"], "git-files")

    def test_start_does_not_clear_the_binding(self):
        """The release must be scoped to completion, not applied to every action."""
        state = project(loop_bytes(), action="start", target_lifecycle="active")
        self.assertEqual(
            state["git_binding"]["branch"],
            "codex/111-runtime-provenance-and-validation-mode-separation",
        )
        self.assertEqual(len(state["git_binding"]["commits"]), 5)

    def test_completion_is_idempotent(self):
        once = project(loop_bytes(), action="complete", target_lifecycle="done")
        twice = project(
            (json.dumps(once, ensure_ascii=False, indent=2) + "\n").encode("utf-8"),
            action="complete",
            target_lifecycle="done",
        )
        self.assertEqual(once["git_binding"], twice["git_binding"])


class BranchRuleHandlesBaseBranchWork(unittest.TestCase):
    def test_work_on_the_base_branch_matches(self):
        """`main` can never contain an issue id. Working there is not a mismatch."""
        self.assertTrue(
            project_loop.branch_matches_issue("main", "127-foo", base_branch="main")
        )

    def test_a_wrong_per_issue_branch_still_fails(self):
        """The fix must not be 'accept everything'."""
        self.assertFalse(
            project_loop.branch_matches_issue(
                "codex/999-unrelated", "127-foo", base_branch="main"
            )
        )

    def test_the_matching_per_issue_branch_still_passes(self):
        self.assertTrue(
            project_loop.branch_matches_issue(
                "codex/127-foo", "127-foo", base_branch="main"
            )
        )

    def test_validation_accepts_base_branch_work(self):
        errors = project_loop.validate_git_binding_for_issue(
            {"branch": "main", "base_branch": "main"},
            "127-foo",
        )
        self.assertEqual(errors, [])

    def test_validation_still_rejects_a_foreign_branch(self):
        errors = project_loop.validate_git_binding_for_issue(
            {"branch": "codex/111-other", "base_branch": "main"},
            "127-foo",
        )
        self.assertEqual(len(errors), 1)

    def test_the_rejection_says_what_would_satisfy_it(self):
        """A person reading only the error must know which branches are accepted."""
        errors = project_loop.validate_git_binding_for_issue(
            {"branch": "codex/111-other", "base_branch": "main"},
            "127-foo",
        )
        message = errors[0]
        self.assertIn("codex/127-foo", message, "the accepted per-issue branch")
        self.assertIn("main", message, "the accepted base branch")

    def test_no_base_branch_keeps_the_old_behaviour(self):
        self.assertFalse(project_loop.branch_matches_issue("main", "127-foo"))


if __name__ == "__main__":
    unittest.main()
