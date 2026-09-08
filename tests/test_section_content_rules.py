"""Issue 129 — the sections a reader depends on, checked for what is in them.

Two defects, one missing mechanism. A bug issue's cause could be an unverified
guess: three reworks in one session came from that, and issue 126 shows why
labelling the guess is not enough — it *did* say "That is a hypothesis from the
error shape, **not verified**", and the next reader still went to the wrong
function. A spec's decision request could be four noun phrases with nothing to
decide with: spec 112 §15 cost the owner a round trip.

The checker was the small part. Measured on 2026-09-06, it had nothing to attach
to on either side. `- Type:` is free prose holding *provenance* — `user product
direction`, `daily work log` — so 107 of 142 issues cannot be classified at all.
No issue has a `## 원인` section; the cause sits inside `## Opportunity`. And
nine of 78 specs carry a decision section under nine different headings.

So these tests are mostly about the anchors, and two of them carry the design
rather than any behaviour:

- `test_hedging_outside_cause_is_ignored` — the phrase ban is scoped to one
  section. Unscoped, `~것 같` is ordinary Korean and the rule would be unusable.
  This is why the section had to exist before the content rule could be safe.
- `test_a_third_rule_needs_no_code` — appends an entry to `SECTION_RULES` and
  asserts it fires. If this fails, the table is a switch statement wearing a
  table's clothes, and the merge of 129 and 130 bought nothing.

`test_legacy_issues_are_skipped_not_failed` runs against the live tree on
purpose. A rule that starts failing history gets switched off, and then the
whole issue ships as decoration.
"""

import importlib.util
import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))


def load_module(name, relative_path):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


validator = load_module(
    "validate_project_artifacts_129", "scripts/validate_project_artifacts.py"
)

HEDGES = ("추측", "~것 같", "~로 보임", "hypothesis", "suspicion", "likely", "probably")


def issue(type_line, body="", blocked="아무도 안 막히면 이 픽스처가 잘못된 것입니다."):
    """Every issue needs `## 안 고치면`, so the fixture carries one.

    These tests exercise the cause and spike rules; without the section they
    would all fail on the 안 고치면 rule instead and stop testing anything.
    """
    return (
        f"# Issue 999: Fixture\n\n**Status: backlog** — created.\n\n"
        f"## 안 고치면\n\n{blocked}\n\n"
        f"## Source\n\n{type_line}\n\n{body}"
    )


class TypeToken(unittest.TestCase):
    def test_the_four_tokens_parse(self):
        for token in ("bug", "feature", "chore", "spike"):
            with self.subTest(token=token):
                self.assertEqual(validator.parse_type_token(f"- Type: {token}")[0], token)

    def test_prose_after_an_em_dash_is_kept_not_dropped(self):
        """The tail carries provenance, the only thing the field holds today."""
        token, prose = validator.parse_type_token(
            "- Type: bug — reported by the owner, 2026-09-06"
        )
        self.assertEqual(token, "bug")
        self.assertEqual(prose, "reported by the owner, 2026-09-06")

    def test_prose_in_the_token_position_yields_none(self):
        for line in (
            "- Type: user product direction",
            "- Type: daily work log",
            "- Type: user multi-project orchestration improvement request",
        ):
            with self.subTest(line=line):
                self.assertIsNone(validator.parse_type_token(line)[0])

    def test_a_missing_type_line_yields_none(self):
        self.assertIsNone(validator.parse_type_token("")[0])

    def test_removed_tokens_are_not_accepted(self):
        """opportunity moved to workspace/; audit was renamed spike."""
        for token in ("opportunity", "audit"):
            with self.subTest(token=token):
                self.assertIsNone(validator.parse_type_token(f"- Type: {token}")[0])


class CauseRule(unittest.TestCase):
    def check(self, text):
        errors = []
        validator.check_sections(text, "issues/999-fixture.md", errors)
        return errors

    def test_a_bug_without_a_cause_section_fails(self):
        errors = self.check(issue("- Type: bug"))
        self.assertTrue(errors)
        self.assertIn("## 원인", errors[0])
        self.assertIn("issues/999-fixture.md", errors[0])

    def test_pasted_output_passes(self):
        text = issue("- Type: bug", "## 원인\n\n```\n$ pytest\nE   AssertionError\n```\n")
        self.assertEqual(self.check(text), [])

    def test_the_literal_unknown_passes(self):
        text = issue("- Type: bug", "## 원인\n\n원인 미상\n")
        self.assertEqual(self.check(text), [])

    def test_each_hedge_fails_and_is_quoted_back(self):
        for hedge in HEDGES:
            with self.subTest(hedge=hedge):
                text = issue("- Type: bug", f"## 원인\n\n```\n$ run\n```\n\n{hedge} 입니다.\n")
                errors = self.check(text)
                self.assertTrue(errors, f"{hedge!r} was not caught")
                self.assertTrue(
                    any(hedge.lstrip("~") in e for e in errors),
                    f"the message must quote {hedge!r}; got {errors}",
                )

    def test_hedging_outside_cause_is_ignored(self):
        """Scoped to the section. `~것 같` is ordinary Korean everywhere else."""
        text = issue(
            "- Type: bug",
            "## Opportunity\n\n원인은 트랜잭션인 것 같습니다.\n\n"
            "## 원인\n\n```\n$ run\nE  boom\n```\n",
        )
        self.assertEqual(self.check(text), [])

    def test_non_bug_types_need_no_cause(self):
        for token in ("feature", "chore"):
            with self.subTest(token=token):
                self.assertEqual(self.check(issue(f"- Type: {token}")), [])


class SpikeRule(unittest.TestCase):
    """The Beads contract: a spike answers a question and records what it found."""

    def check(self, text):
        errors = []
        validator.check_sections(text, "issues/999-fixture.md", errors)
        return errors

    def test_a_spike_needs_goal_and_findings(self):
        errors = self.check(issue("- Type: spike"))
        joined = " ".join(errors)
        self.assertIn("## Goal", joined)
        self.assertIn("## Findings", joined)

    def test_a_spike_with_both_passes(self):
        text = issue("- Type: spike", "## Goal\n\n무엇을 알아낼 것인가.\n\n## Findings\n\n알아낸 것.\n")
        self.assertEqual(self.check(text), [])

    def test_chore_is_the_bucket_and_demands_nothing(self):
        """A bucket that requires sections stops being a bucket."""
        self.assertEqual(self.check(issue("- Type: chore")), [])


class DecisionRule(unittest.TestCase):
    SLOTS = (
        "왜 이 결정이 필요한가요?",
        "지금 무엇이 잘못되고 있나요?",
        "실제로 측정된 예시",
        "다른 선택지와 그 비용",
        "승인하면 무엇이 달라지나요?",
    )

    def check(self, text):
        errors = []
        validator.check_sections(text, "specs/999-x/spec.md", errors, kind="spec")
        return errors

    def spec(self, decisions):
        return f"# Spec: Fixture\n\nIssue: 999-x\n\n## Human Review Decisions\n\n{decisions}\n"

    def test_a_spec_with_no_decision_section_passes(self):
        self.assertEqual(self.check("# Spec: Fixture\n\nIssue: 999-x\n"), [])

    def test_an_unmarked_item_fails(self):
        errors = self.check(self.spec("- fail-closed at plan level\n"))
        self.assertTrue(errors)
        joined = " ".join(errors)
        self.assertIn("[사장님 결정]", joined)
        self.assertIn("[확인만]", joined)

    def test_a_ratification_item_may_be_one_line(self):
        self.assertEqual(
            self.check(self.spec("- [확인만] substring matching deleted 4 real tasks\n")), []
        )

    def test_an_owner_decision_missing_a_slot_fails_naming_it(self):
        filled = "\n".join(f"  - {s} 내용" for s in self.SLOTS[:-1])
        errors = self.check(self.spec(f"- [사장님 결정] fail-closed at plan level\n{filled}\n"))
        self.assertTrue(errors)
        self.assertIn(self.SLOTS[-1], " ".join(errors))

    def test_an_owner_decision_with_all_five_passes(self):
        filled = "\n".join(f"  - {s} 내용" for s in self.SLOTS)
        self.assertEqual(
            self.check(self.spec(f"- [사장님 결정] fail-closed at plan level\n{filled}\n")), []
        )


class TheTableIsATable(unittest.TestCase):
    def test_a_third_rule_needs_no_code(self):
        """If this fails, merging 129 and 130 bought nothing."""
        original = list(validator.SECTION_RULES)
        try:
            validator.SECTION_RULES.append(
                validator.SectionRule(
                    kind="issue",
                    type_token="chore",
                    section="## Inventory",
                    required=True,
                    message="chore 이슈에는 `## Inventory`가 필요합니다.",
                )
            )
            errors = []
            validator.check_sections(issue("- Type: chore"), "issues/999-fixture.md", errors)
            self.assertTrue(errors)
            self.assertIn("## Inventory", errors[0])
        finally:
            validator.SECTION_RULES[:] = original


class TheLiveTree(unittest.TestCase):
    """History must not fail, or the rule gets switched off and this is decoration."""

    def test_legacy_issues_are_skipped_not_failed(self):
        skipped = 0
        for path in sorted((ROOT / "issues").glob("*.md")):
            text = path.read_text(encoding="utf-8")
            match = re.search(r"^- Type:.*$", text, re.M)
            if validator.parse_type_token(match.group(0) if match else "")[0] is not None:
                continue
            skipped += 1
            errors = []
            validator.check_sections(text, path.name, errors)
            # The 안 고치면 rule is not type-keyed — it asks whether the issue
            # should exist, which is prior to what kind it is. Only the
            # type-keyed rules skip a legacy issue.
            self.assertEqual(errors, [], f"{path.name} is legacy and must be skipped")
        self.assertGreater(skipped, 100, "expected the ~107 free-prose issues here")

    def test_the_whole_project_still_validates(self):
        result = validator.validate_project(str(ROOT))
        self.assertTrue(result["valid"], result.get("errors"))


class TechnicalTermRuleIsStated(unittest.TestCase):
    """Rewritten twice from guesses before it was checked against anything.

    v1 said explain the term or drop it — dropping it stops an expert
    searching for the thing. v2 put the plain phrase first and the term in
    parentheses, which produced `말길 알아듣는 장치(라우터, router)`: an invented
    name in front of one the reader already knew, and longer for it.

    Four sources agree and all put the term in the body: Google ("If the
    majority of your audience is likely to recognize and understand the term,
    then you don't need to spell it out"), Microsoft ("Don't create a new word
    if one already exists"), plainlanguage.gov ("use them rarely"), and
    국립국어원's 2025 전문용어 표준화 안내서 (토착화한 외래어 stay; 간결성).

    Three of v2's own four examples fail v3. They are kept in the file as the
    failure table, because a rule with no counter-example gets read as advice.
    """

    HEADING = "## 전문용어"

    def block(self):
        text = (ROOT / "commands" / "product-spec.md").read_text(encoding="utf-8")
        self.assertIn(self.HEADING, text)
        return re.search(
            rf"{re.escape(self.HEADING)}(.*?)(?=\n## |\Z)", text, re.S
        ).group(1)

    def test_the_term_goes_in_the_body_not_the_parenthesis(self):
        body = self.block()
        self.assertIn("전문용어를 본문에 그대로 씁니다", body)
        self.assertIn("괄호에 한 줄", body)

    def test_the_test_is_the_reader_not_the_word(self):
        self.assertIn("읽는 사람이 그 말을 아는지", self.block())

    def test_inventing_a_name_is_forbidden(self):
        """The v2 failure, stated so v4 cannot reintroduce it."""
        self.assertIn("새 이름을 지어내지 않습니다", self.block())

    def test_the_failed_examples_are_kept(self):
        body = self.block()
        for wrong in ("말길 알아듣는 장치", "doctor 출력"):
            with self.subTest(example=wrong):
                self.assertIn(wrong, body)

    def test_it_says_no_machine_can_check_it(self):
        self.assertIn("기계는 검사할 수 없습니다", self.block())

    def test_the_issue_command_states_it_too(self):
        text = (ROOT / "commands" / "product-issue.md").read_text(encoding="utf-8")
        self.assertIn("전문용어는 본문에, 설명은 그 뒤 괄호에", text)
        self.assertIn("읽는 사람이 그 말을 아는지", text)


class WorkflowChecklistIsAPlanNotAManifest(unittest.TestCase):
    """Issue 147. An issue could not start until it was finished.

    `validate_active_issue_links` required every specs/ path named anywhere in
    the active issue to exist, and a Workflow Tasks checklist names all four
    artifacts. So issue 104 could not become active because plan.md and
    review.md were missing — files written after starting, review.md last.

    Issue 132 started fine only because it wrote `specs/<issue>/plan.md`, which
    `linked_artifacts` skips as a placeholder. The issue that named its
    artifacts precisely was the one punished.

    The rule is what the checkbox already meant: a checked row's artifact must
    exist, an unchecked row's must not be required.
    """

    HEAD = "# Issue 999: Fixture\n\n**Status: active** — probe.\n\n"

    def links(self, body):
        return set(validator.linked_artifacts(self.HEAD + body))

    def test_an_unchecked_row_is_not_required(self):
        body = (
            "## Workflow Tasks\n\n"
            "- [x] spec → `specs/999-x/spec.md`\n"
            "- [ ] plan → `specs/999-x/plan.md`\n"
            "- [ ] review → `specs/999-x/review.md`\n"
        )
        self.assertEqual(self.links(body), {"specs/999-x/spec.md"})

    def test_a_checked_row_is_still_required(self):
        """The fix must narrow the check, not switch it off."""
        body = "## Workflow Tasks\n\n- [x] plan → `specs/999-x/plan.md`\n"
        self.assertIn("specs/999-x/plan.md", self.links(body))

    def test_tasks_md_beside_plan_follows_the_same_row(self):
        """`tasks.md` has no row of its own; it rides the plan row's checkbox."""
        checked = "## Workflow Tasks\n\n- [x] plan → `specs/999-x/plan.md` + `specs/999-x/tasks.md`\n"
        unchecked = checked.replace("- [x]", "- [ ]")
        self.assertIn("specs/999-x/tasks.md", self.links(checked))
        self.assertNotIn("specs/999-x/tasks.md", self.links(unchecked))

    def test_links_outside_the_checklist_are_untouched(self):
        """`## Links` and `## Entry Points` name things that exist."""
        body = (
            "## Workflow Tasks\n\n- [ ] plan → `specs/999-x/plan.md`\n\n"
            "## Links\n\n- Goal: `workspace/goal.md`\n\n"
            "## Entry Points\n\n- `specs/999-x/spec.md`\n"
        )
        found = self.links(body)
        self.assertIn("workspace/goal.md", found)
        self.assertIn("specs/999-x/spec.md", found)
        self.assertNotIn("specs/999-x/plan.md", found)

    def test_placeholders_are_still_skipped(self):
        body = "## Workflow Tasks\n\n- [x] plan → `specs/<issue>/plan.md`\n"
        self.assertEqual(self.links(body), set())

    def test_only_checked_rows_contribute_links(self):
        """The property, not one issue's state at one moment.

        This used to pin issue 104 — "spec.md is written; plan.md and review.md
        are not" — and it broke the day 104 finished, because the premise it
        asserted was a snapshot rather than a rule. That is the same defect the
        112 dogfood test had. The rule is what is asserted now.
        """
        body = (
            "## Workflow Tasks\n\n"
            "- [x] spec → `specs/999-x/spec.md`\n"
            "- [ ] review → `specs/999-x/review.md`\n"
        )
        found = self.links(body)
        self.assertIn("specs/999-x/spec.md", found)
        self.assertNotIn("specs/999-x/review.md", found)

    def test_a_finished_issue_links_every_artifact_it_claims(self):
        """104, now that all four rows are checked: each link must exist on disk.

        Reads whatever the file currently says rather than asserting which rows
        are checked, so finishing more work cannot break it.
        """
        text = (ROOT / "issues"
                / "104-project-aware-natural-language-request-orchestrator.md"
                ).read_text(encoding="utf-8")
        found = set(validator.linked_artifacts(text))
        self.assertTrue(found, "a finished issue links at least one artifact")
        for link in found:
            if link.startswith("specs/104-"):
                self.assertTrue((ROOT / link).is_file(), f"{link} is linked but absent")



class DuplicateIssueNumberTests(unittest.TestCase):
    """Issue 150 — two issues can share a number and nothing refuses.

    Found 2026-09-07 in a merge: a remote session and this one both took `127`
    without seeing each other. `030` was already doubled before that, so the
    merge exposed the class rather than creating it.

    **The exemption is a rule, not a list.** All four existing collisions are
    `done`/`superseded`, and a duplicate only matters while somebody could still
    attach work to the wrong one — issue 104 identifies overlap candidates by
    number. So: fail when at least one of the colliding issues is open. That is
    the same "only open work is checked" line issue 129 settled, and it needs no
    date, no issue number, and no list to maintain.
    """

    def build(self, tmp, files):
        root = Path(tmp)
        (root / "issues").mkdir(parents=True, exist_ok=True)
        for name, status in files.items():
            (root / "issues" / name).write_text(
                f"# Issue: {name}\n\n**Status: {status}** — created 2026-09-07.\n"
                f"**Priority: p2**\n",
                encoding="utf-8",
            )
        return root

    def test_two_open_issues_sharing_a_number_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.build(tmp, {
                "042-first-thing.md": "backlog",
                "042-second-thing.md": "active",
            })
            errors = validator.duplicate_issue_numbers(root)
            self.assertEqual(len(errors), 1, errors)
            self.assertIn("042-first-thing.md", errors[0])
            self.assertIn("042-second-thing.md", errors[0], "both files must be named")

    def test_one_open_one_closed_fails(self):
        """Still ambiguous: a request can still be attached to the open one."""
        with tempfile.TemporaryDirectory() as tmp:
            root = self.build(tmp, {
                "042-first-thing.md": "done",
                "042-second-thing.md": "backlog",
            })
            self.assertEqual(len(validator.duplicate_issue_numbers(root)), 1)

    def test_two_closed_issues_sharing_a_number_pass(self):
        """The four that exist today. History keeps its numbers."""
        with tempfile.TemporaryDirectory() as tmp:
            root = self.build(tmp, {
                "030-project-memory-layer.md": "superseded-by-042",
                "030-worker-cognitive-demand.md": "done",
            })
            self.assertEqual(validator.duplicate_issue_numbers(root), [])

    def test_distinct_numbers_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.build(tmp, {
                "042-first.md": "backlog",
                "043-second.md": "active",
            })
            self.assertEqual(validator.duplicate_issue_numbers(root), [])

    def test_the_live_tree_passes(self):
        """030 and 127 are doubled here and all four are closed."""
        self.assertEqual(validator.duplicate_issue_numbers(ROOT), [])

    def test_no_issues_directory_does_not_raise(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(validator.duplicate_issue_numbers(Path(tmp)), [])



if __name__ == "__main__":
    unittest.main()
