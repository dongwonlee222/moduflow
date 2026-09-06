"""Issue 131 stage 1 — the menu a person can read, and the 29 it hides.

The `/` menu listed 41 commands and 11 skills, every description in English
using this product's internal vocabulary. The owner, who commissioned it and
uses it daily, said on 2026-09-06 that half of what it says does not land.

The mechanism was verified against the shipped host binary rather than assumed.
Claude Code's own schema description for the frontmatter key:

    user-invocable: "If false, hides the slash command from users; only the
    model can invoke it via the Skill tool."

That is exactly what is wanted, because `/moduflow <name>` *is* the model
invoking it. The cost — the typed `/moduflow:product-<name>` form stops working
— was put to the owner and approved on 2026-09-06: "moduflow knowledge 최근
형태만 나두자고".

The load-bearing pair of tests is the visibility split and
`test_every_command_is_reachable_through_the_hub`. Hiding a command is only
legitimate while the hub can still reach it; if the second test fails, the first
one has removed capability rather than narrowed a menu.

The visible list is ordered by what a person does, not by what the product
stores — start/goal/roadmap once, status/loop/inbox daily, issue…release per
issue, decision/memory/doctor as they come up. The owner corrected an earlier
list that hid `goal` and `roadmap`: "골이나 로드맵 등 써야 할 것들도 있는 거
아니야? 사용자가 해야 할 것들?"
"""

import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
COMMANDS = ROOT / "commands"
SKILLS = ROOT / "skills"

# Ordered by when a person uses it, per spec R1.
VISIBLE_COMMANDS = frozenset(
    {
        "moduflow",
        "product-start",
        "product-goal",
        "product-roadmap",
        "product-status",
        "product-loop",
        "product-inbox",
        "product-issue",
        "product-decision",
        "product-memory",
        "product-doctor",
        "product-release",
    }
)

HIDDEN_COMMANDS = frozenset(
    "product-" + name
    for name in (
        "analyze", "benchmark", "converge", "dashboard", "design", "evidence",
        "execute", "handoff", "issues", "knowledge", "migrate", "opportunity",
        "plan", "portfolio", "pr", "production", "profile", "projects",
        "promote", "prototype", "report", "research", "review", "risks",
        "spec", "sync", "update", "weekly", "workers",
    )
)

VISIBLE_SKILLS = frozenset(
    {"index", "progress-dashboard", "roadmap-management", "business-plan"}
)

HIDDEN_SKILLS = frozenset(
    {
        "data-analysis-bridge",
        "design-prototype-bridge",
        "git-native-artifact-model",
        "pm-execution-router",
        "source-adapter-policy",
        "spec-kit-validation-bridge",
        "superpowers-execution-bridge",
    }
)

# Frozen so a rename fails loudly rather than silently changing the surface.
EXPECTED_COMMAND_FILES = VISIBLE_COMMANDS | HIDDEN_COMMANDS

DISPLAY_LABELS = {
    "rationale": "왜 이렇게 정했나요?",
    "alternatives": "다른 선택은 무엇이었나요?",
    "reversal_conditions": "언제 이 결정을 뒤집나요?",
    "retrieval_trigger": "언제 다시 살펴보면 될까요?",
    "evidence": "참고한 자료가 있나요?",
}

HANGUL = re.compile(r"[가-힣]")


def frontmatter(path):
    """Return the frontmatter block of a Markdown file as a dict of raw strings."""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    out = {}
    for line in text[3:end].splitlines():
        if ":" not in line or line.startswith((" ", "\t", "#")):
            continue
        key, _, value = line.partition(":")
        out[key.strip()] = value.strip()
    return out


def is_hidden(path):
    return frontmatter(path).get("user-invocable", "").lower() == "false"


def command_path(stem):
    return COMMANDS / (stem + ".md")


def skill_path(name):
    return SKILLS / name / "SKILL.md"


class CommandVisibilitySplit(unittest.TestCase):
    def test_exactly_the_named_commands_are_hidden(self):
        actual = {p.stem for p in COMMANDS.glob("*.md") if is_hidden(p)}
        self.assertEqual(actual, set(HIDDEN_COMMANDS))

    def test_exactly_the_named_commands_stay_visible(self):
        actual = {p.stem for p in COMMANDS.glob("*.md") if not is_hidden(p)}
        self.assertEqual(actual, set(VISIBLE_COMMANDS))

    def test_a_new_command_must_declare_its_visibility(self):
        """A command outside both sets means someone added one without deciding."""
        actual = {p.stem for p in COMMANDS.glob("*.md")}
        self.assertEqual(actual, set(EXPECTED_COMMAND_FILES))


class SkillVisibilitySplit(unittest.TestCase):
    def test_exactly_the_named_skills_are_hidden(self):
        actual = {p.name for p in SKILLS.iterdir()
                  if p.is_dir() and skill_path(p.name).exists()
                  and is_hidden(skill_path(p.name))}
        self.assertEqual(actual, set(HIDDEN_SKILLS))

    def test_exactly_the_named_skills_stay_visible(self):
        actual = {p.name for p in SKILLS.iterdir()
                  if p.is_dir() and skill_path(p.name).exists()
                  and not is_hidden(skill_path(p.name))}
        self.assertEqual(actual, set(VISIBLE_SKILLS))


class NothingWasRenamed(unittest.TestCase):
    """Hiding must never become renaming. The issue's Scope Fence is explicit."""

    def test_the_command_filename_set_is_unchanged(self):
        self.assertEqual(
            {p.stem for p in COMMANDS.glob("*.md")}, set(EXPECTED_COMMAND_FILES)
        )

    def test_the_stored_memory_keys_are_unchanged(self):
        source = (ROOT / "scripts" / "project_memory.py").read_text(encoding="utf-8")
        for key in DISPLAY_LABELS:
            self.assertIn(
                key,
                source,
                f"stored key {key!r} disappeared from project_memory.py; "
                "this issue changes display only",
            )


class HubReachability(unittest.TestCase):
    """The half that makes hiding legitimate rather than destructive."""

    def setUp(self):
        self.hub = command_path("moduflow").read_text(encoding="utf-8")

    def test_the_hub_documents_bare_name_dispatch(self):
        self.assertIn("/moduflow <name>", self.hub)
        self.assertRegex(
            self.hub,
            r"commands/product-<name>\.md",
            "the hub must say which file a bare argument resolves to",
        )

    def test_every_command_is_reachable_through_the_hub(self):
        """All 41, hidden included. If this fails, hiding removed capability."""
        rule = re.search(
            r"##\s*Argument Resolution(.*?)(?=\n## |\Z)", self.hub, re.S
        )
        self.assertIsNotNone(
            rule, "the hub needs an explicit '## Argument Resolution' section"
        )
        body = rule.group(1)
        for stem in sorted(EXPECTED_COMMAND_FILES):
            name = stem.replace("product-", "")
            resolved = command_path("product-" + name)
            if not resolved.exists():
                resolved = command_path(name)
            self.assertTrue(
                resolved.exists(),
                f"/moduflow {name} resolves to no file",
            )
        self.assertIn("product-<arg>.md", body)

    def test_issue_and_issues_stay_distinct(self):
        self.assertTrue(command_path("product-issue").exists())
        self.assertTrue(command_path("product-issues").exists())
        rule = re.search(
            r"##\s*Argument Resolution(.*?)(?=\n## |\Z)", self.hub, re.S
        )
        self.assertIsNotNone(rule)
        self.assertIn(
            "exact",
            rule.group(1).lower(),
            "resolution must be exact-match; a prefix rule collapses "
            "issue and issues",
        )


class VisibleCommandsAreReadable(unittest.TestCase):
    """The owner asked for both halves: 설명 and 어떻게 사용하는지 예시."""

    def visible_command_files(self):
        return sorted(
            command_path(s) for s in VISIBLE_COMMANDS if s != "moduflow"
        )

    def test_each_description_is_korean_first(self):
        for path in self.visible_command_files():
            with self.subTest(command=path.stem):
                description = frontmatter(path).get("description", "")
                self.assertTrue(description, "description is missing")
                self.assertRegex(
                    description[:1],
                    HANGUL,
                    f"{path.stem}: description must start in Korean, got "
                    f"{description[:40]!r}",
                )

    def test_each_carries_a_usage_example_section(self):
        for path in self.visible_command_files():
            with self.subTest(command=path.stem):
                self.assertIn(
                    "## 사용 예시",
                    path.read_text(encoding="utf-8"),
                    f"{path.stem}: no 사용 예시 section",
                )

    def test_each_example_section_has_a_korean_and_an_english_line(self):
        for path in self.visible_command_files():
            with self.subTest(command=path.stem):
                block = re.search(
                    r"##\s*사용 예시(.*?)(?=\n## |\Z)",
                    path.read_text(encoding="utf-8"),
                    re.S,
                )
                self.assertIsNotNone(block, "no 사용 예시 section")
                lines = [
                    line.strip()
                    for line in block.group(1).splitlines()
                    if line.strip().startswith("/moduflow")
                ]
                self.assertGreaterEqual(
                    len(lines), 2, f"{path.stem}: need a Korean and an English example"
                )
                self.assertTrue(
                    any(HANGUL.search(line) for line in lines),
                    f"{path.stem}: no Korean example",
                )
                self.assertTrue(
                    any(not HANGUL.search(line) for line in lines),
                    f"{path.stem}: no English example",
                )

    def test_the_hub_quick_list_holds_exactly_the_eleven(self):
        hub = command_path("moduflow").read_text(encoding="utf-8")
        block = re.search(r"##\s*Quick command list(.*?)(?=\n## |\Z)", hub, re.S)
        self.assertIsNotNone(block)
        body = block.group(1)
        for stem in sorted(VISIBLE_COMMANDS - {"moduflow"}):
            name = stem.replace("product-", "")
            with self.subTest(command=name):
                self.assertRegex(
                    body,
                    rf"/moduflow {re.escape(name)}\b",
                    f"{name} missing from the quick list",
                )
        for stem in sorted(HIDDEN_COMMANDS):
            name = stem.replace("product-", "")
            with self.subTest(hidden=name):
                self.assertNotRegex(
                    body,
                    rf"^\s*\S*\s*/moduflow {re.escape(name)}\b",
                    f"{name} is hidden but listed in the quick list",
                )


class FieldNamesAreNeverShownRaw(unittest.TestCase):
    def test_the_display_labels_are_defined_where_a_reader_meets_them(self):
        decision = command_path("product-decision").read_text(encoding="utf-8")
        for key, label in DISPLAY_LABELS.items():
            with self.subTest(field=key):
                self.assertIn(
                    label,
                    decision,
                    f"{key} has no Korean display label in product-decision.md",
                )


class OneSentenceDecision(unittest.TestCase):
    def test_the_command_accepts_a_single_sentence(self):
        text = command_path("product-decision").read_text(encoding="utf-8")
        self.assertIn("결정으로 남겨줘", text)

    def test_at_most_one_follow_up_question_is_specified(self):
        text = command_path("product-decision").read_text(encoding="utf-8")
        self.assertIn("이 선택을 한 가장 큰 이유가 무엇이었나요?", text)
        self.assertRegex(
            text,
            r"(정확히 한 개|exactly one question|at most one)",
            "the command must state that only one question may be asked",
        )


if __name__ == "__main__":
    unittest.main()
