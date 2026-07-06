import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from scripts import project_converge

ISSUE = "071-spec-code-converge-check"
LOG_ARGS = tuple(project_converge.GIT_LOG_ARGS)


class FakeRunner:
    def __init__(self, responses):
        self.responses = responses
        self.calls = []

    def __call__(self, args, cwd, timeout=None):
        self.calls.append(tuple(args))
        key = tuple(args)
        if key not in self.responses:
            return project_converge.CommandResult(
                1, "", f"unexpected command: {' '.join(args)}"
            )
        value = self.responses[key]
        if isinstance(value, BaseException):
            raise value
        if isinstance(value, project_converge.CommandResult):
            return value
        return project_converge.CommandResult(0, value, "")


def log_record(sha, subject, parents, body):
    return f"{sha}\x00{subject}\x00{parents}\x00{body}\x01\n"


TRAILER_BODY = f"feat: converge engine\n\nIssue: {ISSUE}\n"


def make_project(spec_body=None, plan_body=None, issue_id=ISSUE):
    """Create a tmpdir project with specs/<id>/{spec.md,plan.md}. Returns the
    root Path; caller owns cleanup via addCleanup."""
    root = Path(tempfile.mkdtemp())
    spec_dir = root / "specs" / issue_id
    spec_dir.mkdir(parents=True)
    if spec_body is None:
        spec_body = (
            "# Spec\n\n## Acceptance Criteria\n\n"
            "- [ ] checkbox criterion one\n"
            "- prose bullet criterion two\n\n"
            "## Non-Goals\n\n- nope\n"
        )
    (spec_dir / "spec.md").write_text(spec_body, encoding="utf-8")
    if plan_body is not None:
        (spec_dir / "plan.md").write_text(plan_body, encoding="utf-8")
    return root


class ResolveCommitsTests(unittest.TestCase):
    def test_trailer_resolution(self):
        runner = FakeRunner(
            {LOG_ARGS: log_record("sha1", "feat: converge engine", "p1", TRAILER_BODY)}
        )

        result = project_converge.resolve_commits(runner, Path("."), ISSUE)

        self.assertEqual(result["errors"], [])
        self.assertEqual(len(result["commits"]), 1)
        commit = result["commits"][0]
        self.assertEqual(commit["sha"], "sha1")
        self.assertEqual(commit["subject"], "feat: converge engine")
        self.assertEqual(commit["source"], "trailer")
        self.assertFalse(commit["is_merge"])

    def test_merge_subject_resolution(self):
        runner = FakeRunner(
            {
                LOG_ARGS: log_record(
                    "mrg1",
                    f"Merge branch 'codex/{ISSUE}'",
                    "p1 p2",
                    f"Merge branch 'codex/{ISSUE}'\n",
                )
            }
        )

        result = project_converge.resolve_commits(runner, Path("."), ISSUE)

        self.assertEqual(result["errors"], [])
        self.assertEqual(len(result["commits"]), 1)
        commit = result["commits"][0]
        self.assertEqual(commit["source"], "merge-subject")
        self.assertTrue(commit["is_merge"])

    def test_merge_subject_with_branch_suffix_resolves(self):
        # Work branches carry suffixes: codex/<id>-<suffix>.
        runner = FakeRunner(
            {
                LOG_ARGS: log_record(
                    "mrg2",
                    f"Merge branch 'codex/{ISSUE}-engine'",
                    "p1 p2",
                    "merge\n",
                )
            }
        )

        result = project_converge.resolve_commits(runner, Path("."), ISSUE)

        self.assertEqual([c["sha"] for c in result["commits"]], ["mrg2"])

    def test_trailer_wins_when_both_sources_match(self):
        # A merge commit whose subject mentions the branch AND whose body
        # carries the trailer is recorded once with source 'trailer'.
        runner = FakeRunner(
            {
                LOG_ARGS: log_record(
                    "mrg3",
                    f"Merge branch 'codex/{ISSUE}'",
                    "p1 p2",
                    f"Merge branch 'codex/{ISSUE}'\n\nIssue: {ISSUE}\n",
                )
            }
        )

        result = project_converge.resolve_commits(runner, Path("."), ISSUE)

        self.assertEqual(len(result["commits"]), 1)
        self.assertEqual(result["commits"][0]["source"], "trailer")

    def test_non_merge_subject_mention_is_not_resolved(self):
        # Subject mentioning the branch on a regular commit is not evidence.
        runner = FakeRunner(
            {
                LOG_ARGS: log_record(
                    "sha9", f"docs: notes about codex/{ISSUE}", "p1", "docs\n"
                )
            }
        )

        result = project_converge.resolve_commits(runner, Path("."), ISSUE)

        self.assertEqual(result["commits"], [])
        self.assertEqual(result["errors"], [])

    def test_unrelated_issue_trailer_is_not_resolved(self):
        runner = FakeRunner(
            {
                LOG_ARGS: log_record(
                    "sha8", "fix: other", "p1", "fix\n\nIssue: 070-spec-consistency-analyze\n"
                )
            }
        )

        result = project_converge.resolve_commits(runner, Path("."), ISSUE)

        self.assertEqual(result["commits"], [])

    def test_git_log_failure_surfaces_error(self):
        runner = FakeRunner(
            {
                LOG_ARGS: project_converge.CommandResult(
                    128, "", "fatal: not a git repository"
                )
            }
        )

        result = project_converge.resolve_commits(runner, Path("."), ISSUE)

        self.assertEqual(result["commits"], [])
        self.assertEqual(len(result["errors"]), 1)
        self.assertIn("not a git repository", result["errors"][0])

    def test_multiline_bodies_do_not_bleed_across_records(self):
        stdout = log_record(
            "sha1", "feat: engine", "p1", TRAILER_BODY
        ) + log_record("sha2", "chore: unrelated", "p0", "chore\n\nno trailer here\n")
        runner = FakeRunner({LOG_ARGS: stdout})

        result = project_converge.resolve_commits(runner, Path("."), ISSUE)

        self.assertEqual([c["sha"] for c in result["commits"]], ["sha1"])


class ParseAcceptanceCriteriaTests(unittest.TestCase):
    def test_checkbox_and_prose_bullets_both_parse(self):
        text = (
            "# Spec\n\n## Acceptance Criteria\n\n"
            "- [ ] first checkbox\n"
            "- [x] done checkbox\n"
            "- plain prose bullet\n\n"
            "## Non-Goals\n\n- other\n"
        )

        entries, notes = project_converge.parse_acceptance_criteria(text)

        self.assertEqual(notes, [])
        self.assertEqual(
            [(e["id"], e["text"], e["parseable"]) for e in entries],
            [
                ("AC#1", "first checkbox", True),
                ("AC#2", "done checkbox", True),
                ("AC#3", "plain prose bullet", True),
            ],
        )

    def test_unparseable_line_kept_with_parseable_false(self):
        text = "## Acceptance Criteria\n\nSome free prose that is not a bullet.\n- real bullet\n"

        entries, notes = project_converge.parse_acceptance_criteria(text)

        self.assertEqual(notes, [])
        self.assertFalse(entries[0]["parseable"])
        self.assertEqual(entries[0]["text"], "Some free prose that is not a bullet.")
        self.assertTrue(entries[1]["parseable"])

    def test_wrapped_bullet_continuation_joins_previous_entry(self):
        text = "## Acceptance Criteria\n\n- [ ] a long criterion\n  that wraps onto a second line\n"

        entries, notes = project_converge.parse_acceptance_criteria(text)

        self.assertEqual(len(entries), 1)
        self.assertEqual(
            entries[0]["text"], "a long criterion that wraps onto a second line"
        )

    def test_missing_section_is_empty_with_note(self):
        entries, notes = project_converge.parse_acceptance_criteria("# Spec\n\n## Goals\n- g\n")

        self.assertEqual(entries, [])
        self.assertEqual(len(notes), 1)
        self.assertIn("not found", notes[0])

    def test_empty_section_is_empty_with_note(self):
        entries, notes = project_converge.parse_acceptance_criteria(
            "## Acceptance Criteria\n\n## Non-Goals\n- x\n"
        )

        self.assertEqual(entries, [])
        self.assertIn("empty", notes[0])


class ParseGlobalConstraintsTests(unittest.TestCase):
    def test_numbered_items_parse_with_gc_ids(self):
        text = (
            "## Global Constraints\n\nBinding on every task:\n\n"
            "1. **First**: rule one.\n"
            "2. Second rule.\n\n"
            "## Interfaces\n\n- stuff\n"
        )

        entries = project_converge.parse_global_constraints(text)

        self.assertEqual(
            [(e["id"], e["text"]) for e in entries],
            [("GC#1", "**First**: rule one."), ("GC#2", "Second rule.")],
        )

    def test_absent_section_is_empty_list_not_error(self):
        self.assertEqual(
            project_converge.parse_global_constraints("# Plan\n\n## Work Streams\n"), []
        )


class CollectFilesTests(unittest.TestCase):
    def _project_with_files(self, names_and_contents):
        root = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: __import__("shutil").rmtree(root))
        for name, content in names_and_contents.items():
            (root / name).write_text(content, encoding="utf-8")
        return root

    def test_union_of_touched_paths_reads_current_content(self):
        root = self._project_with_files({"a.md": "alpha", "b.md": "beta"})
        runner = FakeRunner(
            {
                ("git", "show", "--name-only", "--format=", "sha1"): "a.md\nb.md\n",
                ("git", "show", "--name-only", "--format=", "sha2"): "b.md\n",
            }
        )

        result = project_converge.collect_files(runner, root, ["sha1", "sha2"])

        self.assertEqual(result["errors"], [])
        self.assertFalse(result["truncated"])
        self.assertEqual(
            [(f["path"], f["content"]) for f in result["files"]],
            [("a.md", "alpha"), ("b.md", "beta")],
        )

    def test_deleted_file_recorded_as_missing(self):
        root = self._project_with_files({"kept.md": "still here"})
        runner = FakeRunner(
            {
                ("git", "show", "--name-only", "--format=", "sha1"): (
                    "kept.md\ndeleted.md\n"
                )
            }
        )

        result = project_converge.collect_files(runner, root, ["sha1"])

        by_path = {f["path"]: f for f in result["files"]}
        self.assertTrue(by_path["deleted.md"]["missing"])
        self.assertIsNone(by_path["deleted.md"]["content"])
        self.assertNotIn("missing", by_path["kept.md"])
        self.assertFalse(result["truncated"])

    def test_max_files_cap_sets_truncated_flags(self):
        root = self._project_with_files({"a.md": "a", "b.md": "b", "c.md": "c"})
        runner = FakeRunner(
            {("git", "show", "--name-only", "--format=", "sha1"): "a.md\nb.md\nc.md\n"}
        )

        result = project_converge.collect_files(runner, root, ["sha1"], max_files=2)

        self.assertTrue(result["truncated"])
        contents = [(f["path"], f["content"], f["truncated"]) for f in result["files"]]
        self.assertEqual(
            contents,
            [("a.md", "a", False), ("b.md", "b", False), ("c.md", None, True)],
        )

    def test_max_bytes_cap_sets_truncated_flags(self):
        root = self._project_with_files({"a.md": "x" * 10, "b.md": "y" * 10})
        runner = FakeRunner(
            {("git", "show", "--name-only", "--format=", "sha1"): "a.md\nb.md\n"}
        )

        result = project_converge.collect_files(runner, root, ["sha1"], max_bytes=15)

        self.assertTrue(result["truncated"])
        by_path = {f["path"]: f for f in result["files"]}
        self.assertEqual(by_path["a.md"]["content"], "x" * 10)
        self.assertIsNone(by_path["b.md"]["content"])
        self.assertTrue(by_path["b.md"]["truncated"])

    def test_git_show_failure_surfaces_error(self):
        root = self._project_with_files({})
        runner = FakeRunner(
            {
                ("git", "show", "--name-only", "--format=", "bad"): (
                    project_converge.CommandResult(128, "", "fatal: bad object bad")
                )
            }
        )

        result = project_converge.collect_files(runner, root, ["bad"])

        self.assertEqual(result["files"], [])
        self.assertEqual(len(result["errors"]), 1)
        self.assertIn("bad object", result["errors"][0])


class CollectEvidenceTests(unittest.TestCase):
    def _project(self, **kwargs):
        root = make_project(**kwargs)
        self.addCleanup(lambda: __import__("shutil").rmtree(root))
        return root

    def test_full_evidence_shape(self):
        root = self._project(
            plan_body="# Plan\n\n## Global Constraints\n\n1. Rule one.\n2. Rule two.\n"
        )
        (root / "scripts").mkdir()
        (root / "scripts" / "x.py").write_text("print('x')\n", encoding="utf-8")
        runner = FakeRunner(
            {
                LOG_ARGS: log_record("sha1", "feat: engine", "p1", TRAILER_BODY)
                + log_record(
                    "mrg1",
                    f"Merge branch 'codex/{ISSUE}'",
                    "p1 p2",
                    "merge\n",
                ),
                ("git", "show", "--name-only", "--format=", "sha1"): "scripts/x.py\n",
            }
        )

        evidence, ok = project_converge.collect_evidence(
            root, ISSUE, "2026-07-06", runner=runner
        )

        self.assertTrue(ok)
        self.assertEqual(
            list(evidence.keys()),
            [
                "schema",
                "issue_id",
                "generated",
                "commits",
                "files",
                "acceptance_criteria",
                "global_constraints",
                "truncated",
                "no_evidence",
                "errors",
            ],
        )
        self.assertEqual(evidence["schema"], "moduflow.converge-evidence.v1")
        self.assertEqual(evidence["generated"], "2026-07-06")
        self.assertEqual(
            [(c["sha"], c["source"]) for c in evidence["commits"]],
            [("sha1", "trailer"), ("mrg1", "merge-subject")],
        )
        # commits carry exactly the schema keys — no is_merge leak.
        self.assertEqual(set(evidence["commits"][0]), {"sha", "subject", "source"})
        self.assertEqual(evidence["files"][0]["path"], "scripts/x.py")
        self.assertEqual(evidence["files"][0]["content"], "print('x')\n")
        self.assertEqual(len(evidence["acceptance_criteria"]), 2)
        self.assertEqual(
            [gc["id"] for gc in evidence["global_constraints"]], ["GC#1", "GC#2"]
        )
        self.assertFalse(evidence["truncated"])
        self.assertFalse(evidence["no_evidence"])
        self.assertEqual(evidence["errors"], [])
        # Merge commits never feed file collection.
        self.assertNotIn(("git", "show", "--name-only", "--format=", "mrg1"), runner.calls)

    def test_no_commits_is_no_evidence_and_ok(self):
        root = self._project()
        runner = FakeRunner({LOG_ARGS: ""})

        evidence, ok = project_converge.collect_evidence(
            root, ISSUE, "2026-07-06", runner=runner
        )

        self.assertTrue(ok)
        self.assertTrue(evidence["no_evidence"])
        self.assertEqual(evidence["commits"], [])
        self.assertEqual(evidence["files"], [])
        self.assertEqual(evidence["errors"], [])

    def test_git_log_failure_is_error_and_not_ok(self):
        root = self._project()
        runner = FakeRunner(
            {LOG_ARGS: project_converge.CommandResult(128, "", "fatal: broken repo")}
        )

        evidence, ok = project_converge.collect_evidence(
            root, ISSUE, "2026-07-06", runner=runner
        )

        self.assertFalse(ok)
        self.assertEqual(len(evidence["errors"]), 1)
        self.assertIn("broken repo", evidence["errors"][0])
        # no_evidence reflects the empty commit list but the run still fails.
        self.assertTrue(evidence["no_evidence"])

    def test_missing_spec_file_is_not_ok(self):
        root = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: __import__("shutil").rmtree(root))
        runner = FakeRunner({LOG_ARGS: ""})

        evidence, ok = project_converge.collect_evidence(
            root, ISSUE, "2026-07-06", runner=runner
        )

        self.assertFalse(ok)
        self.assertTrue(any("spec file missing" in e for e in evidence["errors"]))
        self.assertEqual(evidence["acceptance_criteria"], [])

    def test_missing_ac_section_noted_but_still_ok(self):
        root = self._project(spec_body="# Spec\n\n## Goals\n\n- g\n")
        runner = FakeRunner({LOG_ARGS: ""})

        evidence, ok = project_converge.collect_evidence(
            root, ISSUE, "2026-07-06", runner=runner
        )

        self.assertTrue(ok)
        self.assertEqual(evidence["acceptance_criteria"], [])
        self.assertTrue(any("Acceptance Criteria" in e for e in evidence["errors"]))

    def test_missing_plan_is_empty_constraints_not_error(self):
        root = self._project(plan_body=None)
        runner = FakeRunner({LOG_ARGS: ""})

        evidence, ok = project_converge.collect_evidence(
            root, ISSUE, "2026-07-06", runner=runner
        )

        self.assertTrue(ok)
        self.assertEqual(evidence["global_constraints"], [])


class MainTests(unittest.TestCase):
    def _project(self, **kwargs):
        root = make_project(**kwargs)
        self.addCleanup(lambda: __import__("shutil").rmtree(root))
        return root

    def _run_main(self, argv, runner):
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            code = project_converge.main(argv, runner=runner)
        return code, stdout.getvalue()

    def test_no_evidence_exits_zero_and_writes_file(self):
        root = self._project()
        runner = FakeRunner({LOG_ARGS: ""})

        code, out = self._run_main(
            [str(root), "--issue-id", ISSUE, "--evidence", "--json", "--date", "2026-07-06"],
            runner,
        )

        self.assertEqual(code, 0)
        printed = json.loads(out)
        self.assertTrue(printed["no_evidence"])
        written = json.loads(
            (root / "specs" / ISSUE / "converge-evidence.json").read_text(encoding="utf-8")
        )
        self.assertEqual(written, printed)

    def test_git_failure_exits_nonzero_in_json_mode(self):
        root = self._project()
        runner = FakeRunner(
            {LOG_ARGS: project_converge.CommandResult(128, "", "fatal: broken repo")}
        )

        code, out = self._run_main(
            [str(root), "--issue-id", ISSUE, "--evidence", "--json", "--date", "2026-07-06"],
            runner,
        )

        self.assertEqual(code, 1)
        self.assertIn("broken repo", json.loads(out)["errors"][0])

    def test_git_failure_exits_nonzero_in_human_mode_too(self):
        # GC4: identical exit behavior in both output modes.
        root = self._project()
        runner = FakeRunner(
            {LOG_ARGS: project_converge.CommandResult(128, "", "fatal: broken repo")}
        )

        code, out = self._run_main(
            [str(root), "--issue-id", ISSUE, "--evidence", "--date", "2026-07-06"], runner
        )

        self.assertEqual(code, 1)
        self.assertIn("broken repo", out)

    def test_human_mode_summary_and_exit_zero(self):
        root = self._project()
        runner = FakeRunner(
            {
                LOG_ARGS: log_record("sha1", "feat: engine", "p1", TRAILER_BODY),
                ("git", "show", "--name-only", "--format=", "sha1"): "",
            }
        )

        code, out = self._run_main(
            [str(root), "--issue-id", ISSUE, "--evidence", "--date", "2026-07-06"], runner
        )

        self.assertEqual(code, 0)
        self.assertIn("commits: 1", out)
        self.assertIn("no_evidence: false", out)
        self.assertIn("converge-evidence.json", out)

    def test_caps_flow_through_cli_flags(self):
        root = self._project()
        (root / "a.md").write_text("aaaa", encoding="utf-8")
        (root / "b.md").write_text("bbbb", encoding="utf-8")
        runner = FakeRunner(
            {
                LOG_ARGS: log_record("sha1", "feat: engine", "p1", TRAILER_BODY),
                ("git", "show", "--name-only", "--format=", "sha1"): "a.md\nb.md\n",
            }
        )

        code, out = self._run_main(
            [
                str(root),
                "--issue-id",
                ISSUE,
                "--evidence",
                "--json",
                "--date",
                "2026-07-06",
                "--max-files",
                "1",
            ],
            runner,
        )

        self.assertEqual(code, 0)
        printed = json.loads(out)
        self.assertTrue(printed["truncated"])
        self.assertEqual(
            [(f["path"], f["truncated"]) for f in printed["files"]],
            [("a.md", False), ("b.md", True)],
        )

    def test_missing_spec_dir_exits_nonzero(self):
        root = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: __import__("shutil").rmtree(root))
        runner = FakeRunner({LOG_ARGS: ""})

        code, out = self._run_main(
            [str(root), "--issue-id", ISSUE, "--evidence", "--json", "--date", "2026-07-06"],
            runner,
        )

        self.assertEqual(code, 1)
        errors = json.loads(out)["errors"]
        self.assertTrue(any("spec file missing" in e for e in errors))
        self.assertTrue(any("cannot write evidence" in e for e in errors))


def verdict_entry(ac_id, verdict, severity="", evidence_quote="", note=""):
    return {
        "ac_id": ac_id,
        "verdict": verdict,
        "severity": severity,
        "evidence_quote": evidence_quote,
        "note": note,
    }


def make_judgment(verdicts=None, unrequested=None, bundle_gaps=None):
    return {
        "schema": "moduflow.converge-judgment.v1",
        "verdicts": verdicts if verdicts is not None else [],
        "unrequested": unrequested if unrequested is not None else [],
        "bundle_gaps": bundle_gaps if bundle_gaps is not None else [],
    }


def mixed_judgment():
    """1 converged, 1 medium missing, 1 high missing, 1 low unverifiable,
    plus 1 high unrequested and a bundle gap."""
    return make_judgment(
        verdicts=[
            verdict_entry("AC#1", "converged", "", "quoted evidence", "ok"),
            verdict_entry("AC#2", "missing", "medium", "", "no report writer"),
            verdict_entry("AC#3", "missing", "high", "", "no converge.md writer"),
            verdict_entry("AC#4", "unverifiable", "low", "", "cannot run from bundle"),
        ],
        unrequested=[
            {"behavior": "adds retry loop", "file": "scripts/retry.py", "severity": "high"}
        ],
        bundle_gaps=["tests dir truncated"],
    )


class ApplyJudgmentTests(unittest.TestCase):
    DATE = "2026-07-06"

    def _project(self, **kwargs):
        root = make_project(**kwargs)
        self.addCleanup(lambda: __import__("shutil").rmtree(root))
        return root

    def _write_judgment(self, root, judgment, name="judgment.json"):
        path = root / name
        path.write_text(json.dumps(judgment, ensure_ascii=False), encoding="utf-8")
        return path

    def _run(self, root, judgment_path, extra=(), date=DATE):
        argv = [
            str(root),
            "--issue-id",
            ISSUE,
            "--apply-judgment",
            str(judgment_path),
            "--date",
            date,
            *extra,
        ]
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            code = project_converge.main(argv, runner=FakeRunner({}))
        return code, stdout.getvalue()

    def _tasks_path(self, root):
        return root / "specs" / ISSUE / "tasks.md"

    def _converge_path(self, root):
        return root / "specs" / ISSUE / "converge.md"

    # -- happy path: converge.md section + ordered, grammar-exact CV lines --

    def test_valid_judgment_writes_report_and_cv_lines_in_order(self):
        root = self._project()
        judgment_path = self._write_judgment(root, mixed_judgment())

        code, out = self._run(root, judgment_path)

        self.assertEqual(code, 0)
        report = self._converge_path(root).read_text(encoding="utf-8")
        self.assertTrue(report.startswith(f"# Converge: {ISSUE}\n"))
        self.assertIn(f"## Converge Run {self.DATE}\n", report)
        self.assertIn("| AC | Verdict | Severity | Note |", report)
        self.assertIn("| AC#3 | missing | high | no converge.md writer |", report)
        self.assertIn("| AC#4 | unverifiable | low | cannot run from bundle |", report)
        self.assertIn("- [high] adds retry loop — scripts/retry.py", report)
        self.assertIn("- tests dir truncated", report)
        self.assertIn(
            "Summary: 4 AC: 1 converged, 2 missing, 1 unverifiable; 1 unrequested",
            report,
        )
        # tasks.md: high before medium (GC7), exact GC6 grammar, section
        # created once at file end.
        tasks = self._tasks_path(root).read_text(encoding="utf-8")
        self.assertEqual(
            tasks,
            "## Converge Findings (auto)\n"
            "\n"
            f"- [ ] CV-1 [high] missing: no converge.md writer — AC#3, from converge {self.DATE}\n"
            f"- [ ] CV-2 [high] adds retry loop — unrequested:scripts/retry.py, from converge {self.DATE}\n"
            f"- [ ] CV-3 [medium] missing: no report writer — AC#2, from converge {self.DATE}\n",
        )

    # -- idempotency: rerun dedups tasks.md, converge.md accumulates --

    def test_second_apply_dedups_tasks_but_adds_report_section(self):
        root = self._project()
        judgment_path = self._write_judgment(root, mixed_judgment())
        first_code, _ = self._run(root, judgment_path)
        self.assertEqual(first_code, 0)
        tasks_before = self._tasks_path(root).read_bytes()

        code, out = self._run(root, judgment_path)

        self.assertEqual(code, 0)
        # GC3/GC6: byte-for-byte identical tasks.md on rerun.
        self.assertEqual(self._tasks_path(root).read_bytes(), tasks_before)
        report = self._converge_path(root).read_text(encoding="utf-8")
        self.assertIn(f"## Converge Run {self.DATE}\n", report)
        self.assertIn(f"## Converge Run {self.DATE} (run 2)\n", report)

    # -- regression: a checked-off CV item does not block re-append --

    def test_checked_cv_item_reappends_and_numbering_continues(self):
        root = self._project()
        tasks = (
            "# Tasks\n\n- [ ] T1 existing task\n\n"
            "## Converge Findings (auto)\n\n"
            "- [x] CV-3 [high] missing: no converge.md writer — AC#3, from converge 2026-06-01\n"
        )
        self._tasks_path(root).write_text(tasks, encoding="utf-8")
        judgment = make_judgment(
            verdicts=[verdict_entry("AC#3", "missing", "high", "", "no converge.md writer")]
        )
        judgment_path = self._write_judgment(root, judgment)

        code, _ = self._run(root, judgment_path)

        self.assertEqual(code, 0)
        text = self._tasks_path(root).read_text(encoding="utf-8")
        # Re-appended as CV-4 (numbering continues past checked CV-3).
        self.assertIn(
            f"- [ ] CV-4 [high] missing: no converge.md writer — AC#3, from converge {self.DATE}\n",
            text,
        )
        # Existing lines untouched; only one findings header.
        self.assertIn("- [x] CV-3 [high]", text)
        self.assertIn("- [ ] T1 existing task", text)
        self.assertEqual(text.count("## Converge Findings (auto)"), 1)

    # -- GC3: fully converged run is a byte-for-byte no-op on tasks.md --

    def test_fully_converged_is_byte_identical_noop(self):
        root = self._project()
        original = "# Tasks\n\n- [ ] T1 keep me\n"
        self._tasks_path(root).write_text(original, encoding="utf-8")
        judgment = make_judgment(
            verdicts=[
                verdict_entry("AC#1", "converged", "", "q", "ok"),
                verdict_entry("AC#2", "converged", "", "q", "ok"),
            ]
        )
        judgment_path = self._write_judgment(root, judgment)

        code, _ = self._run(root, judgment_path)

        self.assertEqual(code, 0)
        self.assertEqual(
            self._tasks_path(root).read_bytes(), original.encode("utf-8")
        )
        self.assertNotIn(
            "Converge Findings", self._tasks_path(root).read_text(encoding="utf-8")
        )
        # converge.md still records the run.
        self.assertIn(
            f"## Converge Run {self.DATE}",
            self._converge_path(root).read_text(encoding="utf-8"),
        )

    def test_noop_without_tasks_file_does_not_create_it(self):
        root = self._project()
        judgment = make_judgment(
            verdicts=[verdict_entry("AC#1", "converged", "", "q", "ok")]
        )
        judgment_path = self._write_judgment(root, judgment)

        code, _ = self._run(root, judgment_path)

        self.assertEqual(code, 0)
        self.assertFalse(self._tasks_path(root).exists())

    # -- low severity is report-only --

    def test_low_severity_is_report_only(self):
        root = self._project()
        original = "# Tasks\n"
        self._tasks_path(root).write_text(original, encoding="utf-8")
        judgment = make_judgment(
            verdicts=[verdict_entry("AC#1", "partial", "low", "", "minor gap")],
            unrequested=[
                {"behavior": "debug print", "file": "scripts/x.py", "severity": "low"}
            ],
        )
        judgment_path = self._write_judgment(root, judgment)

        code, _ = self._run(root, judgment_path)

        self.assertEqual(code, 0)
        self.assertEqual(self._tasks_path(root).read_bytes(), original.encode("utf-8"))
        report = self._converge_path(root).read_text(encoding="utf-8")
        self.assertIn("| AC#1 | partial | low | minor gap |", report)
        self.assertIn("- [low] debug print — scripts/x.py", report)

    # -- CV numbering continues after existing (unchecked, different) items --

    def test_cv_numbering_continues_after_existing_cv3(self):
        root = self._project()
        self._tasks_path(root).write_text(
            "## Converge Findings (auto)\n\n"
            "- [ ] CV-3 [high] old finding — AC#1, from converge 2026-06-01\n",
            encoding="utf-8",
        )
        judgment = make_judgment(
            verdicts=[verdict_entry("AC#2", "contradicting", "high", "", "wrong exit code")]
        )
        judgment_path = self._write_judgment(root, judgment)

        code, _ = self._run(root, judgment_path)

        self.assertEqual(code, 0)
        text = self._tasks_path(root).read_text(encoding="utf-8")
        self.assertIn(
            f"- [ ] CV-4 [high] contradicting: wrong exit code — AC#2, from converge {self.DATE}\n",
            text,
        )
        self.assertEqual(text.count("## Converge Findings (auto)"), 1)
        # Existing unchecked line preserved verbatim above the new one.
        self.assertLess(text.index("CV-3"), text.index("CV-4"))

    # -- unrequested high item gets unrequested:<file> source-ref --

    def test_unrequested_high_item_uses_unrequested_source_ref(self):
        root = self._project()
        judgment = make_judgment(
            unrequested=[
                {"behavior": "opens network socket", "file": "scripts/net.py", "severity": "high"}
            ]
        )
        judgment_path = self._write_judgment(root, judgment)

        code, _ = self._run(root, judgment_path)

        self.assertEqual(code, 0)
        self.assertIn(
            f"- [ ] CV-1 [high] opens network socket — unrequested:scripts/net.py, from converge {self.DATE}\n",
            self._tasks_path(root).read_text(encoding="utf-8"),
        )

    # -- GC4: invalid judgment / missing spec dir exit non-zero, both modes --

    def test_unknown_verdict_value_exits_nonzero_json_mode(self):
        root = self._project()
        judgment = make_judgment(
            verdicts=[verdict_entry("AC#1", "kinda-done", "high", "", "n")]
        )
        judgment_path = self._write_judgment(root, judgment)

        code, out = self._run(root, judgment_path, extra=("--json",))

        self.assertEqual(code, 1)
        errors = json.loads(out)["errors"]
        self.assertTrue(any("unknown verdict" in e for e in errors))
        self.assertFalse(self._converge_path(root).exists())
        self.assertFalse(self._tasks_path(root).exists())

    def test_unknown_verdict_value_exits_nonzero_human_mode_too(self):
        root = self._project()
        judgment = make_judgment(
            verdicts=[verdict_entry("AC#1", "kinda-done", "high", "", "n")]
        )
        judgment_path = self._write_judgment(root, judgment)

        code, out = self._run(root, judgment_path)

        self.assertEqual(code, 1)
        self.assertIn("unknown verdict", out)

    def test_missing_required_verdict_key_exits_nonzero(self):
        root = self._project()
        judgment = make_judgment(
            verdicts=[{"ac_id": "AC#1", "verdict": "missing", "severity": "high"}]
        )
        judgment_path = self._write_judgment(root, judgment)

        code, out = self._run(root, judgment_path, extra=("--json",))

        self.assertEqual(code, 1)
        errors = json.loads(out)["errors"]
        self.assertTrue(any("missing required keys" in e for e in errors))

    def test_wrong_schema_exits_nonzero(self):
        root = self._project()
        judgment = mixed_judgment()
        judgment["schema"] = "moduflow.other.v9"
        judgment_path = self._write_judgment(root, judgment)

        code, out = self._run(root, judgment_path, extra=("--json",))

        self.assertEqual(code, 1)
        self.assertTrue(
            any("schema" in e for e in json.loads(out)["errors"])
        )

    def test_malformed_json_file_exits_nonzero(self):
        root = self._project()
        judgment_path = root / "judgment.json"
        judgment_path.write_text("{not json", encoding="utf-8")

        code, out = self._run(root, judgment_path, extra=("--json",))

        self.assertEqual(code, 1)
        self.assertTrue(
            any("not valid JSON" in e for e in json.loads(out)["errors"])
        )

    def test_missing_judgment_file_exits_nonzero(self):
        root = self._project()

        code, out = self._run(root, root / "nope.json", extra=("--json",))

        self.assertEqual(code, 1)
        self.assertTrue(
            any("cannot read judgment file" in e for e in json.loads(out)["errors"])
        )

    def test_missing_spec_dir_exits_nonzero(self):
        root = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: __import__("shutil").rmtree(root))
        judgment_path = self._write_judgment(root, mixed_judgment())

        code, out = self._run(root, judgment_path, extra=("--json",))

        self.assertEqual(code, 1)
        self.assertTrue(
            any("issue spec dir missing" in e for e in json.loads(out)["errors"])
        )


if __name__ == "__main__":
    unittest.main()
