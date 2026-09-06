"""Issue 112 Stream C: the host adapter boundary.

The claim under test is the one
`docs/superpowers/specs/2026-09-05-issue-112-host-adapter-interface.md` states:
the routing result carries intent, the adapter carries vocabulary, and one
routing result maps to Claude Code, Codex and Copilot without the shared input
changing. Everything a host would recognise — a `codex/` branch prefix, an
OpenAI model name, a Superpowers subagent shape — must live on the adapter side
of that line and nowhere else.

`tests/fixtures/execution-routing/hosts.json` is hand-authored and only ever
read here. Generating it from the adapters would let a wrong adapter and a
wrong fixture agree with each other forever.
"""
import importlib.util
import inspect
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

FIXTURES = ROOT / "tests/fixtures/execution-routing"

# The design doc's whole point, expressed as strings. Any of these appearing in
# a routing result means a host value is still upstream of the adapter.
#
# Scanned only against the synthetic plan below, deliberately. A corpus spec can
# legitimately write `docs/` or the word `worktree` in its own task text, and
# scanning one of those would report the author's prose as a leak.
HOST_VOCABULARY = (
    "codex/",
    "gpt-5.6",
    "opus",
    "sonnet",
    "haiku",
    "worktree",
    "TypeName",
    "copilot-cloud-agent",
)


def load_module(name, relative_path):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


routing = load_module("execution_routing", "scripts/execution_routing.py")
adapters = load_module("execution_host_adapter", "scripts/execution_host_adapter.py")


ISSUE_ID = "112-execution-planner-and-backend-boundary"

# One synthetic plan, not a corpus spec. `test_execution_routing.py:405-412`
# records what pinning corpus state costs: checking a box broke the test, so the
# file could no longer say what had been done. Three task texts chosen so
# `assign_worker` lands on three different roles and the one plan exercises
# `deep`, `balanced` and `fast` at once.
SAMPLE_TASKS = (
    "- [ ] Write the code for the parser [files: scripts/parser.py]\n"
    "- [ ] Draft the module interface [files: docs/module-interface.md]\n"
    "- [ ] Publish the release notes [files: notes/release-notes.md]\n"
)


def route(body):
    tmp = Path(tempfile.mkdtemp())
    path = tmp / "tasks.md"
    path.write_text(body, encoding="utf-8")
    return routing.build_routing(routing.scan_tasks(path), path.parent)


def sample_result():
    return route(SAMPLE_TASKS)


def host_record(adapter, result, issue_id=ISSUE_ID):
    """Compose one host's record from the three methods, in the test.

    The composition lives here rather than in the module because the design
    gives the adapter exactly three methods and leaves it to `worker_orchestrator`
    (T09) to hold both sides and decide what to write.
    """
    return {
        "host_id": adapter.host_id,
        "tasks": {
            task["id"]: {
                "isolation": adapter.isolation(issue_id, task["id"], task["isolation"]),
                "model": adapter.model(task["cognitive_demand"]),
                "dispatch": adapter.dispatch(task, result),
            }
            for task in result["tasks"]
        },
    }


def fixture():
    return json.loads((FIXTURES / "hosts.json").read_text(encoding="utf-8"))


class RoutingResultCarriesIntent(unittest.TestCase):
    """The two fields the adapter needs, added upstream of every host."""

    def test_every_selected_task_names_one_of_the_three_cognitive_demands(self):
        for task in sample_result()["tasks"]:
            self.assertIn(task["cognitive_demand"], {"deep", "balanced", "fast"}, task["id"])

    def test_every_selected_task_says_whether_it_needs_isolation(self):
        for task in sample_result()["tasks"]:
            self.assertIn(task["isolation"], {"shared", "isolated"}, task["id"])

    def test_the_demand_comes_from_the_worker_role_not_from_the_task_order(self):
        """`WORKER_COGNITIVE_DEMAND` is a role table with no host in it, so
        three tasks routed to three roles must carry three different demands."""
        demands = {task["id"]: task["cognitive_demand"] for task in sample_result()["tasks"]}
        self.assertEqual(demands, {"T01": "balanced", "T02": "deep", "T03": "fast"})

    def test_disjoint_parallel_work_is_isolated(self):
        for task in sample_result()["tasks"]:
            self.assertEqual(task["isolation"], "isolated", task["id"])

    def test_a_task_declaring_shared_state_is_shared(self):
        result = route(
            "- [ ] Write the parser [files: scripts/parser.py] [shared_state: true]\n"
            "- [ ] Draft the module interface [files: docs/m.md]\n"
        )
        self.assertEqual([task["isolation"] for task in result["tasks"]], ["shared", "shared"])

    def test_an_inline_plan_marks_every_task_shared(self):
        """Gate 3 chose one working tree for the plan; no task in it is isolated."""
        result = route("- [ ] Write the code for the parser [files: scripts/parser.py]\n")
        self.assertEqual(result["backend"], "inline")
        self.assertEqual([task["isolation"] for task in result["tasks"]], ["shared"])

    def test_the_intent_fields_are_absent_from_the_gate_one_survivors(self):
        """Gate 1 stays a filter. The fields exist only on the emitted result,
        so nothing downstream can read them off a half-built task."""
        tmp = Path(tempfile.mkdtemp()) / "tasks.md"
        tmp.write_text(SAMPLE_TASKS, encoding="utf-8")
        for task in routing.gate1_executable(routing.scan_tasks(tmp)):
            self.assertNotIn("cognitive_demand", task)
            self.assertNotIn("isolation", task)

    def test_a_refusal_carries_no_tasks_and_therefore_no_intent(self):
        self.assertEqual(route("- [ ] Commit and push.\n")["tasks"], [])


class RoutingResultCarriesNoVocabulary(unittest.TestCase):
    """Spec section 8: the routing result must contain no host-specific value."""

    def test_no_host_word_appears_anywhere_in_a_routing_result(self):
        dumped = json.dumps(sample_result()).lower()
        for word in HOST_VOCABULARY:
            self.assertNotIn(word.lower(), dumped, f"{word} leaked into the routing result")

    def test_the_result_names_no_worktree_and_no_prompt(self):
        for task in sample_result()["tasks"]:
            self.assertNotIn("subagent", task)
            self.assertNotIn("prompt", task)
            self.assertNotIsInstance(task["isolation"], dict, "isolation is intent, not a record")


class UnregisteredHostRefuses(unittest.TestCase):
    """Decision 2026-09-06: refuse, never fall back.

    `memory/decisions/2026-09-06-unregistered-host-refuses-rather-than-falling-back.md`
    — a generic fallback always works, and something that always works is never
    replaced, which is how `codex/` survived in every worker plan.
    """

    def test_an_unknown_host_raises_instead_of_returning_an_adapter(self):
        with self.assertRaises(adapters.UnregisteredHostError):
            adapters.adapter_for("cursor")

    def test_the_refusal_names_the_host_and_asks_for_an_adapter(self):
        with self.assertRaises(adapters.UnregisteredHostError) as caught:
            adapters.adapter_for("cursor")
        message = str(caught.exception)
        self.assertIn("cursor", message)
        self.assertIn("adapter", message)

    def test_the_refusal_lists_the_hosts_that_do_have_an_adapter(self):
        with self.assertRaises(adapters.UnregisteredHostError) as caught:
            adapters.adapter_for("cursor")
        for host_id in adapters.known_hosts():
            self.assertIn(host_id, str(caught.exception))

    def test_exactly_three_hosts_are_registered_and_none_of_them_is_a_default(self):
        self.assertEqual(adapters.known_hosts(), ("claude-code", "codex", "copilot-cloud-agent"))
        for host_id in ("", "default", "generic", "*", None):
            with self.assertRaises(adapters.UnregisteredHostError):
                adapters.adapter_for(host_id)

    def test_every_adapter_is_spelled_the_way_the_execution_backends_set_spells_it(self):
        """One host registry, not two.

        `project_loop.EXECUTION_BACKENDS` already names the hosts this product
        knows, and a git binding already records one of those names. An adapter
        spelled `copilot` while the rest of the product says
        `copilot-cloud-agent` would make a configured host unroutable for a
        reason nobody could see. Decision:
        `memory/decisions/2026-09-06-the-host-is-configured-with-a-per-run-override-never-guessed.md`.
        """
        project_loop = load_module("project_loop_host_names", "scripts/project_loop.py")
        for host_id in adapters.known_hosts():
            self.assertIn(host_id, project_loop.EXECUTION_BACKENDS)


class CognitiveDemandMapping(unittest.TestCase):
    """The Evidence table in the design doc, asserted per host."""

    def test_balanced_maps_to_high_effort_and_never_to_medium(self):
        """The doc's reason: the bundled claude-api skill puts intelligence-
        sensitive work at a minimum of `high`, and every worker `balanced`
        covers is coding or review."""
        for host_id in ("claude-code", "codex"):
            self.assertEqual(adapters.adapter_for(host_id).model("balanced")["effort"], "high")

    def test_deep_and_fast_take_the_ends_of_the_effort_ladder(self):
        for host_id in ("claude-code", "codex"):
            adapter = adapters.adapter_for(host_id)
            self.assertEqual(adapter.model("deep")["effort"], "xhigh")
            self.assertEqual(adapter.model("fast")["effort"], "low")

    def test_every_effort_value_comes_from_the_five_band_ladder(self):
        ladder = {"low", "medium", "high", "xhigh", "max"}
        for host_id in adapters.known_hosts():
            adapter = adapters.adapter_for(host_id)
            for demand in ("deep", "balanced", "fast"):
                effort = adapter.model(demand)["effort"]
                self.assertTrue(effort is None or effort in ladder, f"{host_id} {demand}")

    def test_every_host_answers_with_both_axes_even_when_it_has_no_answer(self):
        for host_id in adapters.known_hosts():
            for demand in ("deep", "balanced", "fast"):
                answer = adapters.adapter_for(host_id).model(demand)
                self.assertEqual(sorted(answer), ["effort", "model_hint"], f"{host_id} {demand}")

    def test_a_tier_outside_the_three_is_refused_rather_than_defaulted(self):
        for host_id in adapters.known_hosts():
            for demand in ("medium", "deepest", "", None):
                with self.assertRaises(ValueError, msg=f"{host_id} accepted {demand!r}"):
                    adapters.adapter_for(host_id).model(demand)

    def test_an_isolation_requirement_outside_the_two_is_refused(self):
        for host_id in adapters.known_hosts():
            with self.assertRaises(ValueError):
                adapters.adapter_for(host_id).isolation(ISSUE_ID, "T01", "worktree")


class CodexKeepsItsOwnVocabulary(unittest.TestCase):
    """The two leaks named in spec section 8, relocated rather than deleted."""

    def test_the_codex_worktree_prefix_now_lives_in_the_codex_adapter(self):
        record = adapters.adapter_for("codex").isolation(ISSUE_ID, "T06", "isolated")
        self.assertEqual(record["workspace"], f"codex/{ISSUE_ID}-t06")

    def test_the_openai_model_names_now_live_in_the_model_hint(self):
        codex = adapters.adapter_for("codex")
        self.assertEqual(
            {demand: codex.model(demand)["model_hint"] for demand in ("deep", "balanced", "fast")},
            {"deep": "gpt-5.6-sol", "balanced": "gpt-5.6-terra", "fast": "gpt-5.6-luna"},
        )

    def test_codex_keeps_the_superpowers_subagent_shape(self):
        result = sample_result()
        record = adapters.adapter_for("codex").dispatch(result["tasks"][0], result)
        self.assertEqual(record["TypeName"], "self")
        self.assertEqual(record["CognitiveDemand"], "balanced")
        self.assertIn("Prompt", record)


class NoAdapterWritesAModelNameIntoAPrompt(unittest.TestCase):
    """`w_o.py:388` put the model name in the prompt because one field was doing
    two jobs. With `model()` returning two values, no prompt needs one."""

    def test_no_dispatch_prompt_names_a_model(self):
        result = sample_result()
        for host_id in adapters.known_hosts():
            record = adapters.adapter_for(host_id).dispatch(result["tasks"][0], result)
            prompt = record.get("Prompt") or record.get("prompt") or ""
            for name in ("gpt-5.6", "opus", "sonnet", "haiku", "reasoning"):
                self.assertNotIn(name, prompt.lower(), f"{host_id} prompt names {name}")

    def test_a_dispatch_prompt_still_carries_the_task_and_its_boundary(self):
        result = sample_result()
        record = adapters.adapter_for("codex").dispatch(result["tasks"][0], result)
        self.assertIn("Write the code for the parser", record["Prompt"])
        self.assertIn("scripts/parser.py", record["Prompt"])

    def test_a_caller_may_append_its_own_context_and_every_host_carries_it(self):
        """ModuFlow's related-decision block is content, not host vocabulary.

        `worker_orchestrator` has injected project decisions into the prompt
        since issue 028 and drops them on the floor if the adapter cannot carry
        them. The block names no model and no worktree, so it is passed in as
        text and each host renders it in its own prompt key.
        """
        result = sample_result()
        for host_id in ("claude-code", "codex"):
            task = dict(result["tasks"][0], prompt_context="\n### Related Project Decisions\n")
            record = adapters.adapter_for(host_id).dispatch(task, result)
            prompt = record.get("Prompt") or record.get("prompt") or ""
            self.assertIn("Related Project Decisions", prompt, host_id)

    def test_a_task_without_that_context_is_unchanged(self):
        """The T07 fixture never sets the key, so it must stay byte-identical."""
        result = sample_result()
        task = result["tasks"][0]
        self.assertEqual(
            adapters.task_prompt(task),
            adapters.task_prompt(dict(task, prompt_context="")),
        )


class CopilotReturnsLessRatherThanInventing(unittest.TestCase):
    """Researched 2026-09-06: Copilot selects the model automatically and
    exposes no user-facing tier field
    (https://docs.github.com/copilot/concepts/auto-model-selection). An adapter
    that returns less is correct; one that returns a made-up field name is the
    failure this issue exists to prevent."""

    def test_copilot_offers_no_model_hint_because_it_picks_the_model_itself(self):
        copilot = adapters.adapter_for("copilot-cloud-agent")
        for demand in ("deep", "balanced", "fast"):
            self.assertIsNone(copilot.model(demand)["model_hint"], demand)
            self.assertIsNone(copilot.model(demand)["effort"], demand)

    def test_copilot_dispatch_is_empty_rather_than_a_borrowed_subagent_shape(self):
        result = sample_result()
        self.assertEqual(adapters.adapter_for("copilot-cloud-agent").dispatch(result["tasks"][0], result), {})

    def test_a_host_with_no_subagent_concept_is_legitimate_not_broken(self):
        """The design allows exactly one method to return `{}`."""
        result = sample_result()
        copilot = adapters.adapter_for("copilot-cloud-agent")
        self.assertTrue(copilot.isolation(ISSUE_ID, "T01", "shared"))
        self.assertTrue(copilot.model("deep"))
        self.assertEqual(copilot.dispatch(result["tasks"][0], result), {})

    def test_copilot_says_it_cannot_honour_isolation_instead_of_downgrading(self):
        """Known Limit: the honest answer is a record saying so, never a silent
        downgrade to `shared`."""
        record = adapters.adapter_for("copilot-cloud-agent").isolation(ISSUE_ID, "T01", "isolated")
        self.assertEqual(record["requirement"], "isolated")
        self.assertIs(record["honoured"], False)
        self.assertTrue(record["detail"], "an unhonoured requirement must say why")

    def test_claude_code_lets_its_own_harness_name_the_worktree(self):
        """Claude Code's subagent launcher takes an isolation mode and creates
        the worktree itself, so the adapter has no name to supply. Emitting one
        would be a ModuFlow invention, not a Claude Code convention."""
        record = adapters.adapter_for("claude-code").isolation(ISSUE_ID, "T01", "isolated")
        self.assertIs(record["honoured"], True)
        self.assertIsNone(record["workspace"])


class OneResultThreeHosts(unittest.TestCase):
    """Criterion 13, at the level reachable before T09 lands.

    T09 has not wired `worker_orchestrator` onto the adapter, so no canonical
    artifact is produced here to diff. What is provable now is the precondition:
    the same routing result, unmutated, yields three different host records.
    """

    def test_the_three_host_records_match_the_hand_authored_fixture(self):
        result = sample_result()
        expected = fixture()
        for host_id in adapters.known_hosts():
            self.assertEqual(
                host_record(adapters.adapter_for(host_id), result),
                expected["hosts"][host_id],
                f"{host_id} drifted from tests/fixtures/execution-routing/hosts.json",
            )

    def test_the_fixture_covers_every_registered_host(self):
        """Adding a host adds a fixture row; a host without one is unproven."""
        self.assertEqual(tuple(sorted(fixture()["hosts"])), adapters.known_hosts())

    def test_the_routing_result_is_unchanged_after_all_three_adapters_run(self):
        result = sample_result()
        before = json.dumps(result, sort_keys=True)
        for host_id in adapters.known_hosts():
            host_record(adapters.adapter_for(host_id), result)
        self.assertEqual(before, json.dumps(result, sort_keys=True))

    def test_the_three_hosts_read_the_very_same_task_objects(self):
        """Not equal copies — the same objects, so the comparison above is a
        mutation check rather than a check on three private copies."""
        result = sample_result()
        seen = []

        class Recorder:
            host_id = "recorder"

            def isolation(self, issue_id, task_id, requirement):
                return {}

            def model(self, cognitive_demand):
                return {}

            def dispatch(self, task, plan):
                seen.append(id(task))
                return {}

        for _ in adapters.known_hosts():
            host_record(Recorder(), result)
        self.assertEqual(len(set(seen)), len(result["tasks"]))

    def test_the_three_hosts_disagree_with_each_other_on_that_one_input(self):
        result = sample_result()
        rendered = {
            host_id: json.dumps(host_record(adapters.adapter_for(host_id), result), sort_keys=True)
            for host_id in adapters.known_hosts()
        }
        self.assertEqual(len(set(rendered.values())), 3, "two hosts produced the same record")

    def test_no_adapter_method_takes_a_path_to_read_or_write(self):
        """The design's purity claim, checked at the signature rather than by
        chdir-ing the whole process into a sandbox — the adapters accept no
        path, so there is nothing for a cwd to change."""
        for host_id in adapters.known_hosts():
            adapter = adapters.adapter_for(host_id)
            for name in ("isolation", "model", "dispatch"):
                parameters = inspect.signature(getattr(adapter, name)).parameters
                for parameter in parameters:
                    self.assertNotIn("path", parameter, f"{host_id}.{name}")
                    self.assertNotIn("root", parameter, f"{host_id}.{name}")

    def test_the_adapter_module_imports_nothing_from_moduflow(self):
        """An adapter that reached back into the repository could read a file
        without ever naming one."""
        source = (ROOT / "scripts/execution_host_adapter.py").read_text(encoding="utf-8")
        for line in source.splitlines():
            stripped = line.strip()
            self.assertFalse(
                stripped.startswith("import ") or stripped.startswith("from "),
                f"the adapter module imports something: {stripped}",
            )

    def test_an_adapter_carries_no_state_between_calls(self):
        result = sample_result()
        adapter = adapters.adapter_for("codex")
        first = host_record(adapter, result)
        second = host_record(adapters.adapter_for("codex"), result)
        self.assertEqual(first, host_record(adapter, result))
        self.assertEqual(first, second)


class FixtureIsAuthoredNotGenerated(unittest.TestCase):
    """If the suite could regenerate the fixture, a wrong adapter and a wrong
    fixture would agree forever. Same defect as the one recorded in
    `test_execution_routing.py` about tests that derive their own answer."""

    def test_the_fixture_says_it_is_hand_authored(self):
        self.assertIn("hand-authored", fixture()["note"].lower())

    def test_the_fixture_pins_the_two_values_this_issue_exists_to_relocate(self):
        body = (FIXTURES / "hosts.json").read_text(encoding="utf-8")
        self.assertIn("codex/112-execution-planner-and-backend-boundary-t01", body)
        self.assertIn("gpt-5.6-sol", body)

    def test_running_the_adapters_leaves_the_fixture_byte_identical(self):
        """The comparison above is only worth anything if the run cannot
        rewrite what it is compared against."""
        path = FIXTURES / "hosts.json"
        before = path.read_bytes()
        result = sample_result()
        for host_id in adapters.known_hosts():
            host_record(adapters.adapter_for(host_id), result)
        self.assertEqual(before, path.read_bytes())


if __name__ == "__main__":
    unittest.main()
