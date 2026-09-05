import importlib.util
import re
import tempfile
import unittest
from pathlib import Path

from tests.test_project_production import (
    VALID_PLAYBOOK,
    VALID_RECORD,
    write_playbook,
    write_project,
    write_record,
)

ROOT = Path(__file__).resolve().parents[1]


def load_module(name, relative_path):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


memory = load_module("project_memory", "scripts/project_memory.py")
production = load_module("project_production", "scripts/project_production.py")


def record_type():
    return re.search(r"^deliverable_type:\s*(.+)$", VALID_RECORD, re.M).group(1).strip()


class PlaybookCoverageTest(unittest.TestCase):
    """A record with no playbook reference means one of two opposite things."""

    APPROVED = {"status": "approved", "deliverable_types": ["banner"]}
    CANDIDATE = {"status": "candidate", "deliverable_types": ["banner"]}

    def test_a_named_playbook_wins_over_everything(self):
        record = {"playbook_refs": ["pb-x"], "deliverable_type": "banner"}
        self.assertEqual(memory.playbook_coverage(record, [self.APPROVED]), "named")
        self.assertEqual(memory.playbook_coverage(record, []), "named")

    def test_an_approved_standard_of_the_same_type_means_unapplied(self):
        record = {"playbook_refs": [], "deliverable_type": "banner"}
        self.assertEqual(memory.playbook_coverage(record, [self.APPROVED]), "unapplied")

    def test_a_candidate_standard_never_triggers_unapplied(self):
        record = {"playbook_refs": [], "deliverable_type": "banner"}
        self.assertEqual(memory.playbook_coverage(record, [self.CANDIDATE]), "no-standard")

    def test_a_different_type_is_not_a_match(self):
        record = {"playbook_refs": [], "deliverable_type": "email"}
        self.assertEqual(memory.playbook_coverage(record, [self.APPROVED]), "no-standard")

    def test_channel_and_audience_are_deliberately_not_consulted(self):
        record = {
            "playbook_refs": [],
            "deliverable_type": "banner",
            "channel": "somewhere-else",
            "audiences": ["nobody"],
        }
        self.assertEqual(memory.playbook_coverage(record, [self.APPROVED]), "unapplied")

    def test_a_record_without_a_type_claims_nothing(self):
        record = {"playbook_refs": [], "deliverable_type": ""}
        self.assertEqual(memory.playbook_coverage(record, [self.APPROVED]), "no-standard")

    def test_the_function_is_pure(self):
        record = {"playbook_refs": [], "deliverable_type": "banner"}
        playbooks = [dict(self.APPROVED)]
        before = (dict(record), [dict(p) for p in playbooks])
        memory.playbook_coverage(record, playbooks)
        self.assertEqual((record, playbooks), before)


class ProductionCollectorTest(unittest.TestCase):
    def test_an_empty_project_is_empty_not_broken(self):
        with tempfile.TemporaryDirectory() as tmp:
            write_project(Path(tmp))
            records = memory._collect_production_records(tmp)
            playbooks = memory._collect_playbooks(tmp)
            self.assertEqual((records["rows"], records["warnings"]), ([], []))
            self.assertEqual((playbooks["rows"], playbooks["warnings"]), ([], []))

    def test_records_carry_only_the_fields_the_table_needs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_project(root)
            write_record(root)
            row = memory._collect_production_records(tmp)["rows"][0]
            for field in ("id", "title", "deliverable_type", "audiences",
                          "retrieval_trigger", "lifecycle", "playbook_refs",
                          "coverage", "path"):
                self.assertIn(field, row)
            # The detail modal has no backend to fetch from, so section text ships
            # in the payload. It is capped and the cut is reported, never silent.
            self.assertIn("sections", row)
            for body in row["sections"].values():
                self.assertEqual(sorted(body), ["omitted_chars", "text", "truncated"])
            self.assertFalse(Path(row["path"]).is_absolute())

    def test_one_unparseable_file_does_not_blank_the_tab(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_project(root)
            write_record(root)
            broken = root / "memory" / "production-records" / "broken.md"
            broken.write_text("no frontmatter here\n", encoding="utf-8")
            result = memory._collect_production_records(tmp)
            self.assertEqual(len(result["rows"]), 1)
            self.assertEqual(len(result["warnings"]), 1)
            self.assertIn("broken.md", result["warnings"][0]["path"])

    def test_coverage_uses_the_projects_own_playbooks(self):
        """A record with no reference reads differently depending on what exists."""
        stripped = re.sub(r"^playbook_refs:.*$", "playbook_refs: []", VALID_RECORD, flags=re.M)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_project(root)
            write_record(root, stripped)
            self.assertEqual(
                memory._collect_production_records(tmp)["rows"][0]["coverage"], "no-standard"
            )

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_project(root)
            write_record(root, stripped)
            write_playbook(root, re.sub(
                r"^applies_to_types:.*$", f"applies_to_types: [{record_type()}]",
                VALID_PLAYBOOK, flags=re.M,
            ))
            self.assertEqual(
                memory._collect_production_records(tmp)["rows"][0]["coverage"], "unapplied"
            )

    def test_playbook_rows_expose_the_issue_115_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_project(root)
            text = VALID_PLAYBOOK.replace(
                "version: 1.0\n",
                "version: 1.0\nretrieval_trigger: 배너를 새로 만들 때\n"
                "process_ref_kind: document\nprocess_ref: docs/banner.md\nprocess_ref_version: 2.0\n",
            ).replace(
                "## Approved Copy Blocks",
                "## Required Checks\n\n- CHK001 [auto] section:Artifacts\n"
                "- CHK002 [review] 문구 확인\n- CHK003 [review] 옛 규칙 (retired)\n\n## Approved Copy Blocks",
            )
            write_playbook(root, text)
            row = memory._collect_playbooks(tmp)["rows"][0]
            self.assertEqual(row["retrieval_trigger"], "배너를 새로 만들 때")
            self.assertEqual(row["process_ref_kind"], "document")
            self.assertEqual(row["process_ref_version"], "2.0")
            self.assertEqual((row["auto_checks"], row["review_checks"]), (1, 1))

    def test_absent_and_none_process_ref_stay_distinguishable(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_project(root)
            write_playbook(root, VALID_PLAYBOOK)
            self.assertEqual(memory._collect_playbooks(tmp)["rows"][0]["process_ref_kind"], "")

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_project(root)
            write_playbook(root, VALID_PLAYBOOK.replace(
                "version: 1.0\n",
                "version: 1.0\nprocess_ref_kind: none\nprocess_ref:\nprocess_ref_version:\n"
                "process_ref_missing:\n  - process_ref: 아직 없습니다\n",
            ))
            self.assertEqual(memory._collect_playbooks(tmp)["rows"][0]["process_ref_kind"], "none")


if __name__ == "__main__":
    unittest.main()


class DashboardTabRenderingTest(unittest.TestCase):
    """T05/T06 rendering. Modal coverage lands with T07."""

    def _render(self, root):
        (root / "issues").mkdir(exist_ok=True)
        (root / "issues" / "001-x.md").write_text(
            "# Issue: `001-x`\n\n**Status: done** — created 2026-09-04.\n", encoding="utf-8"
        )
        return memory.render_project_view(root)

    def _payload(self, html, name):
        import json
        # One embedded payload holds every tab's rows (Issue 086 T09), so read
        # the envelope and index into the default project rather than matching
        # a per-tab constant that no longer exists.
        match = re.search(
            r"const PROJECTS = (.*?);\nfunction projectPayload", html, re.S
        )
        self.assertIsNotNone(match, "PROJECTS payload not found")
        envelope = json.loads(match.group(1))
        self.assertEqual(envelope["schema"], "moduflow.dashboard-projects.v1")
        project = envelope["projects"][envelope["default_project_id"]]
        return project[name.lower()]

    def test_both_tabs_exist_after_the_original_three(self):
        with tempfile.TemporaryDirectory() as tmp:
            html = self._render(Path(tmp))
        order = [html.index(f'id="tab-{name}"') for name in
                 ("db", "issues", "memory", "production", "playbooks")]
        self.assertEqual(order, sorted(order), "new tabs must follow the existing three")

    def test_empty_states_say_not_registered_yet_not_nothing_exists(self):
        with tempfile.TemporaryDirectory() as tmp:
            html = self._render(Path(tmp))
        self.assertIn("아직 제작물을 등록하지 않았습니다", html)
        self.assertIn("아직 기준을 등록하지 않았습니다", html)

    def test_only_approved_playbooks_get_the_green_treatment(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_project(root)
            write_playbook(root, VALID_PLAYBOOK)
            approved = self._payload(self._render(root), "PLAYBOOK_ROWS")["rows"][0]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_project(root)
            write_playbook(root, re.sub(r"^status:.*$", "status: candidate", VALID_PLAYBOOK, flags=re.M))
            candidate = self._payload(self._render(root), "PLAYBOOK_ROWS")["rows"][0]
        self.assertEqual(approved["status"], "approved")
        self.assertEqual(candidate["status"], "candidate")

    def test_the_page_offers_no_way_to_complete_a_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            html = self._render(Path(tmp))
        for affordance in ("checkbox", "complete_check", "markCheck", "promote("):
            self.assertNotIn(
                affordance, html.split("function projectPayload")[-1],
                f"{affordance} would let the page act on a check",
            )

    def test_a_broken_record_is_counted_not_hidden(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_project(root)
            write_record(root)
            (root / "memory" / "production-records" / "broken.md").write_text(
                "not a record\n", encoding="utf-8"
            )
            payload = self._payload(self._render(root), "PRODUCTION_ROWS")
        self.assertEqual(len(payload["rows"]), 1)
        self.assertEqual(len(payload["warnings"]), 1)


class DetailModalTest(unittest.TestCase):
    """T07/T08: one modal shell for both tabs, read-only."""

    def _render(self, root):
        (root / "issues").mkdir(exist_ok=True)
        (root / "issues" / "001-x.md").write_text(
            "# Issue: `001-x`\n\n**Status: done** — created 2026-09-04.\n", encoding="utf-8"
        )
        return memory.render_project_view(root)

    def test_one_modal_shell_serves_both_tabs(self):
        with tempfile.TemporaryDirectory() as tmp:
            html = self._render(Path(tmp))
        self.assertEqual(html.count('id="modal"'), 1)
        self.assertEqual(html.count('id="modal-back"'), 1)
        for opener in ("openRecord", "openPlaybook"):
            self.assertIn(opener, html)

    def test_all_nine_record_sections_are_rendered_in_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            html = self._render(Path(tmp))
        for section in production.RECORD_SECTIONS:
            self.assertIn(section, html, section)

    def test_external_and_internal_copy_are_visibly_separated(self):
        with tempfile.TemporaryDirectory() as tmp:
            html = self._render(Path(tmp))
        self.assertIn("COPY_SECTIONS", html)
        for name in ("External Copy", "Internal Reporting Copy"):
            self.assertIn(name, html)
        self.assertIn(".modal .copy", html)

    def test_the_modal_says_a_check_is_an_assertion_and_offers_no_control(self):
        with tempfile.TemporaryDirectory() as tmp:
            html = self._render(Path(tmp))
        self.assertIn("검토자의 주장", html)
        modal_js = html.split("function openPlaybook")[1].split("function showTab")[0]
        for affordance in ("<input", "checkbox", "onchange"):
            self.assertNotIn(affordance, modal_js, affordance)

    def test_closing_restores_focus_and_escape_works(self):
        with tempfile.TemporaryDirectory() as tmp:
            html = self._render(Path(tmp))
        self.assertIn("modalOpener", html)
        self.assertIn("e.key === 'Escape'", html)

    def test_opening_a_second_row_replaces_rather_than_stacks(self):
        with tempfile.TemporaryDirectory() as tmp:
            html = self._render(Path(tmp))
        self.assertIn("modal.innerHTML =", html)
        self.assertNotIn("insertAdjacentHTML", html)

    def test_a_long_section_is_capped_and_the_cut_is_reported(self):
        long_body = "x" * (memory.SECTION_CHAR_BUDGET + 500)
        capped = memory._capped_sections({"Artifacts": long_body, "Decisions": "short"})
        self.assertTrue(capped["Artifacts"]["truncated"])
        self.assertEqual(capped["Artifacts"]["omitted_chars"], 500)
        self.assertEqual(len(capped["Artifacts"]["text"]), memory.SECTION_CHAR_BUDGET)
        self.assertFalse(capped["Decisions"]["truncated"])


class ProjectSelectorTest(unittest.TestCase):
    """T09: one payload, one selector, one restorable URL state."""

    def _render(self, root):
        (root / "issues").mkdir(exist_ok=True)
        (root / "issues" / "001-x.md").write_text(
            "# Issue: `001-x`\n\n**Status: done** — created 2026-09-04.\n",
            encoding="utf-8",
        )
        return memory.render_project_view(root)

    def _envelope(self, html):
        import json

        match = re.search(
            r"const PROJECTS = (.*?);\nfunction projectPayload", html, re.S
        )
        self.assertIsNotNone(match, "PROJECTS payload not found")
        return json.loads(match.group(1))

    def test_the_page_embeds_one_payload_not_five(self):
        with tempfile.TemporaryDirectory() as tmp:
            html = self._render(Path(tmp))
        self.assertEqual(html.count("const PROJECTS = "), 1)
        # The five per-tab payload constants are gone; nothing may reintroduce
        # a second embedded source that a project switch would have to keep
        # in sync by hand.
        for stale in (
            "const ISSUE_ROWS = [",
            "const PRODUCTION_ROWS = [",
            "const PLAYBOOK_ROWS = [",
        ):
            self.assertNotIn(stale, html, stale)
        self.assertNotIn("__PROJECTS_JSON__", html, "placeholder was not filled")

    def test_every_tab_reads_from_the_same_envelope(self):
        with tempfile.TemporaryDirectory() as tmp:
            envelope = self._envelope(self._render(Path(tmp)))
        self.assertEqual(envelope["schema"], "moduflow.dashboard-projects.v1")
        project = envelope["projects"][envelope["default_project_id"]]
        for key in (
            "issue_rows",
            "issue_elements",
            "memory_elements",
            "production_rows",
            "playbook_rows",
        ):
            self.assertIn(key, project, key)

    def test_a_project_without_a_profile_id_falls_back_to_its_root_slug(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            envelope = self._envelope(self._render(root))
        self.assertEqual(envelope["default_project_id"], root.name)
        self.assertEqual(
            envelope["projects"][root.name]["label"], root.name
        )

    def test_the_selector_is_present_and_inert_for_a_single_project(self):
        with tempfile.TemporaryDirectory() as tmp:
            html = self._render(Path(tmp))
        self.assertIn('id="project-select"', html)
        # One registered project means nothing to switch to. The control still
        # ships so Issue 092 has a stable contract to bind against.
        self.assertIn("select.disabled = ids.length < 2;", html)

    def test_url_state_is_written_and_restored(self):
        with tempfile.TemporaryDirectory() as tmp:
            html = self._render(Path(tmp))
        self.assertIn("currentProjectParam", html)
        self.assertIn("url.searchParams.set('project', id)", html)
        self.assertIn("history.replaceState", html)

    def test_an_unknown_project_id_warns_and_falls_back(self):
        with tempfile.TemporaryDirectory() as tmp:
            html = self._render(Path(tmp))
        restore = html.split("const requestedProject")[-1]
        self.assertIn("console.warn", restore)
        self.assertIn("applyProject(requestedProject)", restore)

    def test_switching_projects_refuses_loudly_instead_of_half_rendering(self):
        """The graphs are built once at load; a silent no-op would lie."""
        with tempfile.TemporaryDirectory() as tmp:
            html = self._render(Path(tmp))
        switch = html.split("function selectProject")[-1]
        self.assertIn("throw new Error", switch.split("closeModal")[0])
        self.assertIn("Issue 118", switch)

    def test_a_switch_closes_the_modal_before_it_repaints(self):
        with tempfile.TemporaryDirectory() as tmp:
            html = self._render(Path(tmp))
        body = html.split("function selectProject")[-1].split("\n}")[0]
        self.assertLess(
            body.index("closeModal()"),
            body.index("renderIssueTable()"),
            "a stale modal would survive the repaint",
        )


class ProjectIdentityTest(unittest.TestCase):
    """The id in the payload is resolved, never invented."""

    def test_a_profile_id_wins_over_the_slug(self):
        context = {"canonical_root": "/tmp/some-root", "project_id": "modu-charge"}
        self.assertEqual(
            memory._dashboard_project_identity("/tmp/some-root", context),
            ("modu-charge", "some-root"),
        )

    def test_a_blank_profile_id_is_not_used_as_an_id(self):
        context = {"canonical_root": "/tmp/some-root", "project_id": "   "}
        self.assertEqual(
            memory._dashboard_project_identity("/tmp/some-root", context),
            ("some-root", "some-root"),
        )


def _unterminated_literals(src):
    """Return (line, excerpt) for every ' or " literal broken by a newline.

    PROJECT_VIEW_TEMPLATE is a plain (non-raw) Python string, so a JS escape
    written `\n` instead of `\\n` reaches the browser as a real newline and
    kills the whole script. String-existence assertions cannot see this; the
    page still contains every marker they look for.

    Lexes strings, template literals, comments and regex literals. Quotes
    inside a `${}` substitution are treated as template text, so a literal
    broken in there would be missed — the scanner is validated against the
    real template rather than trusted in the abstract.
    """
    bad, i, n, line = [], 0, len(src), 1
    state, prev = None, ""
    while i < n:
        ch = src[i]
        if ch == "\n":
            line += 1
        if state in ("'", '"'):
            if ch == "\\":
                i += 2
                continue
            if ch == "\n":
                bad.append((line - 1, src[max(0, i - 70):i].rsplit("\n", 1)[-1]))
                state = None
            elif ch == state:
                state = None
        elif state == "`":
            if ch == "\\":
                i += 2
                continue
            if ch == "`":
                state = None
        elif state == "/re":
            if ch == "\\":
                i += 2
                continue
            if ch == "[":
                state = "/re["
            elif ch in "/\n":
                state = None
        elif state == "/re[":
            if ch == "\\":
                i += 2
                continue
            if ch == "]":
                state = "/re"
        elif state == "//":
            if ch == "\n":
                state = None
        elif state == "/*":
            if src.startswith("*/", i):
                state = None
                i += 2
                continue
        else:
            if src.startswith("//", i):
                state = "//"
                i += 2
                continue
            if src.startswith("/*", i):
                state = "/*"
                i += 2
                continue
            if ch == "/" and (prev == "" or prev in "(,=:[!&|?{};+-*%~^<>"):
                state = "/re"
            elif ch in "'\"`":
                state = ch
        if not ch.isspace():
            prev = ch
        i += 1
    return bad


class RenderedScriptIsRunnableTest(unittest.TestCase):
    """The page shipped on 2026-09-05 parsed as HTML but died as JavaScript.

    Two `.join('\\n')` calls lost a backslash when T07/T08 landed, so every
    tab, the issue table and both graphs were dead in the browser while 25
    marker-based tests reported success.
    """

    def _script(self, html):
        blocks = [
            body
            for body in re.findall(r"<script[^>]*>(.*?)</script>", html, re.S)
            if "function showTab" in body
        ]
        self.assertEqual(len(blocks), 1, "expected exactly one inline page script")
        return blocks[0]

    def _render(self, root):
        (root / "issues").mkdir(exist_ok=True)
        (root / "issues" / "001-x.md").write_text(
            "# Issue: `001-x`\n\n**Status: done** — created 2026-09-04.\n",
            encoding="utf-8",
        )
        return memory.render_project_view(root)

    def test_no_string_literal_is_broken_by_a_newline(self):
        with tempfile.TemporaryDirectory() as tmp:
            script = self._script(self._render(Path(tmp)))
        self.assertEqual(
            _unterminated_literals(script),
            [],
            "a lost backslash would kill the entire page script",
        )

    def test_the_scanner_would_actually_catch_the_regression(self):
        """A test that cannot fail protects nothing."""
        with tempfile.TemporaryDirectory() as tmp:
            script = self._script(self._render(Path(tmp)))
        broken = script.replace(".join('\\n')", ".join('\n')", 1)
        self.assertNotEqual(broken, script, "the guarded construct disappeared")
        self.assertTrue(_unterminated_literals(broken))


class StatusGroupOrderTest(unittest.TestCase):
    """workspace/inbox.md 2026-07-06: the user could not find their own active issue.

    Group order followed whichever status the first row happened to carry, so
    under the default created_desc sort the active group sat below a screenful
    of done ones.

    These are marker assertions on generated JS — the same kind that let a
    dead page ship on 2026-09-05. The ordering itself was verified in a
    browser against a probe row set (done, done, backlog, active, review,
    weird, blocked → active, review, blocked, backlog, done, weird); what
    these pin is that the ordering code stays present and keeps its sequence.
    """

    def _render(self, root):
        (root / "issues").mkdir(exist_ok=True)
        (root / "issues" / "001-x.md").write_text(
            "# Issue: `001-x`\n\n**Status: done** — created 2026-09-04.\n",
            encoding="utf-8",
        )
        return memory.render_project_view(root)

    def test_attention_states_are_ordered_ahead_of_settled_ones(self):
        with tempfile.TemporaryDirectory() as tmp:
            html = self._render(Path(tmp))
        match = re.search(r"const STATUS_GROUP_ORDER = \[(.*?)\];", html)
        self.assertIsNotNone(match, "status group order was removed")
        order = [item.strip().strip("'\"") for item in match.group(1).split(",")]
        self.assertEqual(
            order,
            ["active", "review", "blocked", "backlog", "done", "superseded"],
        )

    def test_grouping_by_goal_is_left_alone(self):
        """Only the status axis has a meaningful order; goals do not."""
        with tempfile.TemporaryDirectory() as tmp:
            html = self._render(Path(tmp))
        body = html.split("function groupedRows")[1].split("\n}")[0]
        self.assertIn("if(key !== 'status') return groups;", body)

    def test_an_unknown_status_is_kept_not_dropped(self):
        with tempfile.TemporaryDirectory() as tmp:
            html = self._render(Path(tmp))
        body = html.split("function groupedRows")[1].split("function renderIssueTable")[0]
        self.assertIn("index === -1 ? STATUS_GROUP_ORDER.length", body)
