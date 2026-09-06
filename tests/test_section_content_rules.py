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


def issue(type_line, body=""):
    return f"# Issue 999: Fixture\n\n**Status: backlog** — created.\n\n## Source\n\n{type_line}\n\n{body}"


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
            self.assertEqual(errors, [], f"{path.name} is legacy and must be skipped")
        self.assertGreater(skipped, 100, "expected the ~107 free-prose issues here")

    def test_the_whole_project_still_validates(self):
        result = validator.validate_project(str(ROOT))
        self.assertTrue(result["valid"], result.get("errors"))


if __name__ == "__main__":
    unittest.main()
