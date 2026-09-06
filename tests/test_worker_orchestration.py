import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]


def load_module(name, relative_path):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class WorkerOrchestrationTests(unittest.TestCase):
    def test_archived_project_denies_worker_plan_before_build_or_write(self):
        orchestrator = load_module("worker_orchestrator_denied", "scripts/worker_orchestrator.py")
        project_registry = load_module("project_registry_worker_denied", "scripts/project_registry.py")
        project_operation = load_module("project_operation_worker_denied", "scripts/project_operation.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            context = project_registry.project_context_for_root(root)
            context.update(project_operation.compute_project_policy("archived", "internal"))

            with mock.patch.object(
                orchestrator,
                "build_worker_plan",
                side_effect=AssertionError("build called before authorization"),
            ) as build:
                with self.assertRaisesRegex(Exception, "Archived projects are read-only"):
                    orchestrator.write_worker_plan(
                        root,
                        "110-denied",
                        project_context=context,
                    )

            build.assert_not_called()
            self.assertFalse((root / "specs").exists())

    def make_project(self, root, tasks):
        spec_root = root / "specs" / "007-worker-orchestration"
        spec_root.mkdir(parents=True)
        (spec_root / "tasks.md").write_text(tasks, encoding="utf-8")
        workers_root = root / "workers"
        workers_root.mkdir()
        for name in [
            "pm-strategist",
            "spec-architect",
            "roadmap-planner",
            "ux-flow-worker",
            "data-reviewer",
            "implementation-worker",
            "qa-reviewer",
            "release-manager",
        ]:
            (workers_root / f"{name}.md").write_text(f"# {name}\n", encoding="utf-8")

    def test_build_worker_plan_marks_independent_tasks_parallel_eligible(self):
        orchestrator = load_module("worker_orchestrator", "scripts/worker_orchestrator.py")
        # Boundaries added for issue 112 Gate 2: a task with no declared file or
        # glob is refused now, so a fixture without one no longer reaches the
        # parallel decision this test is about.
        tasks = """# Tasks

- [ ] PM: refine acceptance criteria [files: specs/007-worker-orchestration/spec.md]
- [ ] Design: validate onboarding flow [files: docs/onboarding-flow.md]
- [ ] Data: define activation metric [files: docs/activation-metric.md]
- [ ] QA: verify regression checklist [files: tests/test_regression.py]
"""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_project(root, tasks)

            plan = orchestrator.build_worker_plan(root, "007-worker-orchestration")

            self.assertTrue(plan["parallel"]["eligible"])
            self.assertGreaterEqual(len(plan["tasks"]), 4)
            self.assertEqual(plan["tasks"][0]["worker"], "pm-strategist")
            self.assertTrue(any(task["worker"] == "ux-flow-worker" for task in plan["tasks"]))

    def test_shared_state_tasks_are_sequential(self):
        orchestrator = load_module("worker_orchestrator", "scripts/worker_orchestrator.py")
        # Boundaries added for issue 112 Gate 2; the shared-state words this
        # test is about are unchanged.
        tasks = """# Tasks

- [ ] Update shared config schema [files: scripts/config_schema.py]
- [ ] Change state migration handling [files: scripts/state_migration.py]
"""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_project(root, tasks)

            plan = orchestrator.build_worker_plan(root, "007-worker-orchestration")

            self.assertFalse(plan["parallel"]["eligible"])
            self.assertEqual(plan["parallel"]["mode"], "sequential")
            self.assertTrue(plan["parallel"]["risks"])

    def test_acceptance_verification_routes_to_qa_before_pm(self):
        orchestrator = load_module("worker_orchestrator", "scripts/worker_orchestrator.py")

        self.assertEqual(
            orchestrator.assign_worker("Acceptance verification and regression checklist"),
            "qa-reviewer",
        )

    def test_overlapping_expected_files_force_sequential_mode(self):
        orchestrator = load_module("worker_orchestrator", "scripts/worker_orchestrator.py")
        tasks = """# Tasks

- [ ] Implementation: update loop command [files: commands/product-loop.md]
- [ ] Release: document loop command [files: commands/product-loop.md]
"""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_project(root, tasks)

            plan = orchestrator.build_worker_plan(root, "007-worker-orchestration")

            self.assertFalse(plan["parallel"]["eligible"])
            self.assertEqual(plan["parallel"]["mode"], "sequential")
            self.assertIn("commands/product-loop.md", plan["parallel"]["risks"][0])
            self.assertEqual(plan["tasks"][0]["expected_files"], ["commands/product-loop.md"])

    def test_disjoint_files_include_isolation_and_merge_order(self):
        orchestrator = load_module("worker_orchestrator", "scripts/worker_orchestrator.py")
        tasks = """# Tasks

- [ ] PM: refine acceptance criteria [files: specs/023-worker-routing-and-isolation/spec.md]
- [ ] Implementation: update worker planner [files: scripts/worker_orchestrator.py]
- [ ] QA: verify routing tests [files: tests/test_worker_orchestration.py] [depends: T02]
"""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_project(root, tasks)

            plan = orchestrator.build_worker_plan(root, "007-worker-orchestration")

            self.assertTrue(plan["parallel"]["eligible"])
            # Was `isolation["worktree"] == "codex/…-t02"`. The requirement is
            # ModuFlow's; the mechanism and any branch name are the host's, and
            # under the default host there is no `codex/` string to assert.
            self.assertEqual(plan["tasks"][1]["isolation_requirement"], "isolated")
            self.assertEqual(plan["tasks"][1]["isolation"]["mechanism"], "agent-worktree")
            self.assertTrue(plan["tasks"][1]["isolation"]["honoured"])
            self.assertEqual(plan["tasks"][2]["dependencies"], ["T02"])
            self.assertEqual(plan["parallel"]["merge_order"], ["T01", "T02", "T03"])

    def test_dead_worker_files_are_reported(self):
        orchestrator = load_module("worker_orchestrator", "scripts/worker_orchestrator.py")
        tasks = """# Tasks

- [ ] Implementation: add command wiring [files: scripts/worker_orchestrator.py]
"""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_project(root, tasks)
            (root / "workers" / "business-planner.md").write_text("# business-planner\n", encoding="utf-8")

            plan = orchestrator.build_worker_plan(root, "007-worker-orchestration")

            self.assertIn("business-planner", plan["workers"]["dead_workers"])
            self.assertNotIn("implementation-worker", plan["workers"]["dead_workers"])


    def test_write_worker_plan_creates_json_and_markdown(self):
        orchestrator = load_module("worker_orchestrator", "scripts/worker_orchestrator.py")
        # Boundaries added for issue 112 Gate 2.
        tasks = """# Tasks

- [ ] Implementation: add command wiring [files: scripts/command_wiring.py]
- [ ] Release: update docs [files: docs/command-wiring.md]
"""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_project(root, tasks)

            result = orchestrator.write_worker_plan(root, "007-worker-orchestration")

            self.assertEqual(result["written"], ["worker-plan.json", "worker-plan.md"])
            plan_json = root / "specs" / "007-worker-orchestration" / "worker-plan.json"
            plan_md = root / "specs" / "007-worker-orchestration" / "worker-plan.md"
            self.assertTrue(plan_json.exists())
            self.assertTrue(plan_md.exists())
            self.assertEqual(json.loads(plan_json.read_text(encoding="utf-8"))["schema"], "moduflow.worker-plan.v2")

    def test_worker_plan_uses_canonical_specs_and_ignores_decoy(self):
        orchestrator = load_module("worker_orchestrator_nested", "scripts/worker_orchestrator.py")
        project_registry = load_module("project_registry_worker", "scripts/project_registry.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            issue_id = "007-worker-orchestration"
            context = project_registry.project_context_for_root(root)
            for role, relative in {
                "specs": "delivery/specs",
                "memory": "project-memory",
            }.items():
                context["relative_paths"][role] = relative
                context["paths"][role] = str((root / relative).resolve())
            nested = root / "delivery" / "specs" / issue_id
            nested.mkdir(parents=True)
            (nested / "tasks.md").write_text(
                "- [ ] Implementation: canonical task [files: scripts/canonical.py]\n",
                encoding="utf-8",
            )
            decoy = root / "specs" / issue_id / "tasks.md"
            decoy.parent.mkdir(parents=True)
            decoy.write_text("- [ ] PM: decoy task\n", encoding="utf-8")

            result = orchestrator.write_worker_plan(
                root,
                issue_id,
                project_context=context,
            )

            plan = json.loads((nested / "worker-plan.json").read_text(encoding="utf-8"))
            self.assertEqual(result["written"], ["worker-plan.json", "worker-plan.md"])
            self.assertIn("canonical task", plan["tasks"][0]["text"])
            self.assertEqual(decoy.read_text(encoding="utf-8"), "- [ ] PM: decoy task\n")


    def test_build_worker_plan_includes_subagent_configs(self):
        orchestrator = load_module("worker_orchestrator", "scripts/worker_orchestrator.py")
        tasks = """# Tasks
 
- [ ] PM: refine acceptance criteria [files: specs/028-real-subagent-execution-backend/spec.md]
- [ ] Implementation: update worker planner [files: scripts/worker_orchestrator.py]
"""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_project(root, tasks)

            # The Superpowers subagent shape is the Codex host's vocabulary as
            # of issue 112, not every host's. Asserted here against the host it
            # is correct for; the default host's shape is the next test.
            plan = orchestrator.build_worker_plan(
                root, "007-worker-orchestration", host="codex"
            )

            self.assertEqual(len(plan["tasks"]), 2)
            task1 = plan["tasks"][0]
            self.assertIn("subagent", task1)
            self.assertEqual(task1["subagent"]["TypeName"], "self")
            self.assertEqual(task1["subagent"]["Role"], "ModuFlow pm-strategist")
            self.assertEqual(task1["subagent"]["Workspace"], "share")
            self.assertIn("PM: refine acceptance criteria", task1["subagent"]["Prompt"])
            self.assertIn("specs/028-real-subagent-execution-backend/spec.md", task1["subagent"]["Prompt"])

            task2 = plan["tasks"][1]
            self.assertEqual(task2["subagent"]["Role"], "ModuFlow implementation-worker")
            self.assertIn("scripts/worker_orchestrator.py", task2["subagent"]["Prompt"])

    def test_the_default_host_gets_its_own_dispatch_shape_not_the_codex_one(self):
        orchestrator = load_module("worker_orchestrator", "scripts/worker_orchestrator.py")
        tasks = """# Tasks

- [ ] PM: refine acceptance criteria [files: specs/028-real-subagent-execution-backend/spec.md]
- [ ] Implementation: update worker planner [files: scripts/worker_orchestrator.py]
"""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_project(root, tasks)

            plan = orchestrator.build_worker_plan(root, "007-worker-orchestration")

            self.assertEqual(plan["host"], "claude-code")
            record = plan["tasks"][0]["subagent"]
            self.assertEqual(record["subagent_type"], "general-purpose")
            self.assertEqual(record["description"], "ModuFlow T01")
            self.assertNotIn("TypeName", record)
            self.assertIn("PM: refine acceptance criteria", record["prompt"])

    def test_worker_orchestrator_injects_related_memories(self):
        orchestrator = load_module("worker_orchestrator", "scripts/worker_orchestrator.py")
        tasks = """# Tasks
 
- [ ] PM: refine acceptance criteria [files: specs/028-real-subagent-execution-backend/spec.md]
"""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_project(root, tasks)

            # Copy project_memory.py to tmp so it can be loaded dynamically
            (root / "scripts").mkdir(exist_ok=True)
            import shutil
            shutil.copy(ROOT / "scripts/project_memory.py", root / "scripts/project_memory.py")

            # Initialize memory structure
            project_memory = load_module("project_memory", "scripts/project_memory.py")
            project_memory.apply_memory_plan(project_memory.build_memory_plan(root, dry_run=False))

            # Create an approved decision record referencing the spec file
            project_memory.create_memory_entry(
                root,
                kind="decision",
                title="Subagent Execution Cache",
                summary="Cache results for subagents to save cost.",
                references=["specs/028-real-subagent-execution-backend/spec.md"],
            )

            # Build worker plan
            plan = orchestrator.build_worker_plan(root, "007-worker-orchestration")

            self.assertEqual(len(plan["tasks"]), 1)
            # `Prompt` -> `prompt`: the dispatch record's key is the host's, and
            # the default host is Claude Code.
            prompt = plan["tasks"][0]["subagent"]["prompt"]
            self.assertIn("Related Project Decisions", prompt)
            self.assertIn("Subagent Execution Cache", prompt)
            self.assertIn("memory/decisions", prompt)
            self.assertNotIn("confidence: medium", prompt)  # Ensure no full-text/frontmatter inlining
            # A canonical artifact must not carry one machine's layout (§7), and
            # the memory link was the last absolute path reaching the plan.
            self.assertNotIn(str(root), prompt)
            self.assertNotIn("file:///", prompt)



class RoutingResultDrivesTheWorkerPlanTests(unittest.TestCase):
    """Issue 112 T09 — the write path consumes the gates instead of the file.

    Before this, every checkbox in `tasks.md` became a worker task with a
    prompt, a `codex/` worktree and an absolute `project_root`. Measured on
    2026-09-05: 514 of 640 generated worker tasks were already `done`, and 9 of
    the 10 committed `worker-plan.json` files named a directory that does not
    exist on this machine.
    """

    ISSUE_ID = "007-worker-orchestration"

    def _module(self):
        return load_module("worker_orchestrator_routing", "scripts/worker_orchestrator.py")

    def _project(self, root, tasks):
        spec_root = root / "specs" / self.ISSUE_ID
        spec_root.mkdir(parents=True)
        (spec_root / "tasks.md").write_text(tasks, encoding="utf-8")
        return spec_root

    def test_only_unfinished_implementation_work_becomes_a_worker_task(self):
        tasks = """# Tasks

## Stream A

- [x] Implementation: the finished one [files: scripts/done.py]
- [ ] [deferred → 118-elsewhere] Implementation: the moved one [files: scripts/moved.py]
- [ ] Implementation: the real one [files: scripts/real.py]

## Required Gates

- [ ] `python3 -m unittest discover -s tests` green.
"""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._project(root, tasks)
            plan = self._module().build_worker_plan(root, self.ISSUE_ID)

            self.assertEqual(plan["status"], "ok")
            self.assertEqual([task["id"] for task in plan["tasks"]], ["T03"])

    def test_survivors_keep_the_numbers_the_source_file_gave_them(self):
        """A human-written `[depends: T01]` must keep pointing at the same line.

        Renumbering survivors would silently repoint every dependency in the
        corpus. `tests/test_execution_routing.py` asserts this upstream; the
        write path has to preserve it or the guarantee stops at the gate.
        """
        tasks = """# Tasks

- [x] Implementation: first [files: scripts/a.py]
- [x] Implementation: second [files: scripts/b.py]
- [ ] Implementation: third [files: scripts/c.py] [depends: T01]
- [ ] QA: fourth [files: tests/test_c.py] [depends: T03]
"""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._project(root, tasks)
            plan = self._module().build_worker_plan(root, self.ISSUE_ID)

            self.assertEqual([task["id"] for task in plan["tasks"]], ["T03", "T04"])
            self.assertEqual(plan["parallel"]["merge_order"], ["T03", "T04"])

    def test_a_dependency_on_a_completed_task_is_satisfied_not_blocking(self):
        """Spec section 5: shipped `dispatchable_now` treats a done dependency
        as satisfied, and Gate 2 was built to agree. The write path must too, or
        every partly finished spec reports nothing dispatchable."""
        tasks = """# Tasks

- [x] Implementation: groundwork [files: scripts/a.py]
- [ ] Implementation: build on it [files: scripts/b.py] [depends: T01]
"""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._project(root, tasks)
            plan = self._module().build_worker_plan(root, self.ISSUE_ID)

            self.assertEqual(plan["parallel"]["now"]["dispatchable"], ["T02"])
            self.assertEqual(plan["parallel"]["now"]["blocked"], [])

    def test_a_task_without_a_boundary_refuses_the_whole_plan(self):
        tasks = """# Tasks

- [ ] Implementation: bounded [files: scripts/a.py]
- [ ] Commit and push.
"""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._project(root, tasks)
            plan = self._module().build_worker_plan(root, self.ISSUE_ID)

            self.assertEqual(plan["status"], "needs_plan")
            self.assertEqual(plan["tasks"], [])
            self.assertEqual([gap["task_id"] for gap in plan["gaps"]], ["T02"])
            self.assertEqual(plan["next_command"], "product:plan")

    def test_a_refused_plan_writes_no_file(self):
        tasks = "# Tasks\n\n- [ ] Commit and push.\n"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            spec_root = self._project(root, tasks)

            result = self._module().write_worker_plan(root, self.ISSUE_ID)

            self.assertEqual(result["status"], "needs_plan")
            self.assertEqual(result["written"], [])
            self.assertFalse((spec_root / "worker-plan.json").exists())
            self.assertFalse((spec_root / "worker-plan.md").exists())

    def test_a_finished_spec_is_not_applicable_and_also_writes_nothing(self):
        tasks = "# Tasks\n\n- [x] Implementation: done [files: scripts/a.py]\n"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            spec_root = self._project(root, tasks)

            result = self._module().write_worker_plan(root, self.ISSUE_ID)

            self.assertEqual(result["status"], "not_applicable")
            self.assertEqual(result["written"], [])
            self.assertEqual(result["next_command"], "product:status")
            self.assertFalse((spec_root / "worker-plan.json").exists())

    def test_a_stale_plan_from_a_previous_run_is_left_alone_by_a_refusal(self):
        """A refusal must not half-update the artifact either: leaving the old
        file is honest, overwriting it with a partial plan is not."""
        tasks = "# Tasks\n\n- [ ] Commit and push.\n"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            spec_root = self._project(root, tasks)
            (spec_root / "worker-plan.json").write_text("{\"stale\": true}\n", encoding="utf-8")

            self._module().write_worker_plan(root, self.ISSUE_ID)

            self.assertEqual(
                json.loads((spec_root / "worker-plan.json").read_text(encoding="utf-8")),
                {"stale": True},
            )

    def test_a_rendered_refusal_reads_as_a_refusal_not_as_an_empty_plan(self):
        """`write_worker_plan` returns before rendering on a non-ok status, but
        `build_worker_plan` hands refusals to callers who may render one. A
        refusal rendered as a plan with no tasks reads as a finished plan."""
        tasks = "# Tasks\n\n- [ ] Commit and push.\n"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._project(root, tasks)
            module = self._module()

            rendered = module.render_worker_plan_markdown(
                module.build_worker_plan(root, self.ISSUE_ID)
            )

            self.assertIn("needs_plan", rendered)
            self.assertIn("no worker plan was written", rendered)
            self.assertIn("no_boundary", rendered)
            self.assertIn("T01", rendered)
            self.assertIn("product:plan", rendered)
            self.assertNotIn("Dispatchable Now", rendered)

    def test_the_written_project_root_is_repository_relative(self):
        tasks = "# Tasks\n\n- [ ] Implementation: real [files: scripts/a.py]\n"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            spec_root = self._project(root, tasks)

            self._module().write_worker_plan(root, self.ISSUE_ID)

            written = (spec_root / "worker-plan.json").read_text(encoding="utf-8")
            plan = json.loads(written)
            self.assertEqual(plan["project_root"], ".")
            self.assertFalse(Path(plan["project_root"]).is_absolute())
            self.assertNotIn(str(root), written)


class TheHostIsConfiguredNeverGuessedTests(unittest.TestCase):
    """`memory/decisions/2026-09-06-the-host-is-configured-with-a-per-run-override-never-guessed.md`.

    A guessed host writes a wrong value into a canonical artifact silently,
    which is how `codex/` reached every worker plan regardless of host.
    """

    ISSUE_ID = "007-worker-orchestration"
    TASKS = """# Tasks

- [ ] Implementation: parser [files: scripts/parser.py]
- [ ] Release: notes [files: docs/notes.md]
"""

    def _module(self):
        return load_module("worker_orchestrator_hosts", "scripts/worker_orchestrator.py")

    def _project(self, root, config=None):
        spec_root = root / "specs" / self.ISSUE_ID
        spec_root.mkdir(parents=True)
        (spec_root / "tasks.md").write_text(self.TASKS, encoding="utf-8")
        if config is not None:
            (root / ".moduflow").mkdir(parents=True, exist_ok=True)
            (root / ".moduflow" / "config.json").write_text(
                json.dumps(config), encoding="utf-8"
            )
        return spec_root

    def test_the_default_host_is_claude_code_when_nothing_is_configured(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._project(root)
            self.assertEqual(self._module().build_worker_plan(root, self.ISSUE_ID)["host"], "claude-code")

    def test_the_configured_host_is_read_from_the_project_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._project(root, {"schema": "moduflow.config.v1", "execution": {"host": "codex"}})
            self.assertEqual(self._module().build_worker_plan(root, self.ISSUE_ID)["host"], "codex")

    def test_an_invocation_may_override_the_configured_host(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._project(root, {"schema": "moduflow.config.v1", "execution": {"host": "codex"}})
            plan = self._module().build_worker_plan(root, self.ISSUE_ID, host="claude-code")
            self.assertEqual(plan["host"], "claude-code")

    def test_an_unreadable_or_silent_config_falls_back_to_the_default(self):
        """A config without the key is every project today. Throwing there would
        break `product:workers` everywhere for a field nobody has written yet."""
        for config in ({"schema": "moduflow.config.v1"}, {"execution": "codex"}, {"execution": {}}):
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                self._project(root, config)
                self.assertEqual(
                    self._module().build_worker_plan(root, self.ISSUE_ID)["host"],
                    "claude-code",
                    config,
                )

    def test_a_host_with_no_adapter_refuses_rather_than_writing_a_guess(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            spec_root = self._project(root)
            with self.assertRaisesRegex(LookupError, "no host adapter"):
                self._module().write_worker_plan(root, self.ISSUE_ID, host="cursor")
            self.assertFalse((spec_root / "worker-plan.json").exists())

    def test_the_codex_branch_prefix_is_written_only_under_the_codex_host(self):
        """The relocation, proved on the path that can actually reach it: these
        two tasks are disjoint with no shared state, so Gate 3 routes them to
        `superpowers-sdd` and the isolation requirement is `isolated`."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._project(root)
            module = self._module()

            codex = module.build_worker_plan(root, self.ISSUE_ID, host="codex")
            claude = module.build_worker_plan(root, self.ISSUE_ID, host="claude-code")

            self.assertEqual(codex["backend"], "superpowers-sdd")
            self.assertEqual(codex["tasks"][0]["isolation_requirement"], "isolated")
            self.assertEqual(
                codex["tasks"][0]["isolation"]["workspace"],
                f"codex/{self.ISSUE_ID}-t01",
            )
            self.assertNotIn("codex/", json.dumps(claude))

    def test_a_hosts_vocabulary_never_appears_in_another_hosts_plan(self):
        """`gpt-5.6-terra` under Codex is correct; under Claude Code it is the
        bug. The claim is not that model names vanish — it is that each one
        appears only where it is true."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._project(root)
            module = self._module()
            for host, forbidden in (
                ("claude-code", ("gpt-5.6", "codex/")),
                ("codex", ("opus", "sonnet", "haiku")),
                ("copilot-cloud-agent", ("gpt-5.6", "codex/", "opus", "sonnet", "haiku")),
            ):
                dumped = json.dumps(module.build_worker_plan(root, self.ISSUE_ID, host=host))
                for word in forbidden:
                    self.assertNotIn(word, dumped, f"{word} under {host}")

    def test_no_task_prompt_names_a_model_on_any_host(self):
        """The leak spec section 8 measured: `COGNITIVE_DEMAND_GUIDANCE` put a
        model name in every prompt on every host. `model()` says it on its own
        two axes now, so no prompt has to."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._project(root)
            module = self._module()
            for host in ("claude-code", "codex", "copilot-cloud-agent"):
                for task in module.build_worker_plan(root, self.ISSUE_ID, host=host)["tasks"]:
                    record = task["subagent"]
                    prompt = record.get("Prompt") or record.get("prompt") or ""
                    for name in ("gpt-5.6", "opus", "sonnet", "haiku", "cognitive demand"):
                        self.assertNotIn(name, prompt.lower(), f"{name} under {host}")

    def test_the_plan_records_the_host_it_was_built_for(self):
        """The design doc's complaint is that the file is wrong about its own
        provenance. Naming the host is what makes that checkable."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            spec_root = self._project(root)
            self._module().write_worker_plan(root, self.ISSUE_ID, host="codex")
            plan = json.loads((spec_root / "worker-plan.json").read_text(encoding="utf-8"))
            self.assertEqual(plan["host"], "codex")
            self.assertIn("codex", (spec_root / "worker-plan.md").read_text(encoding="utf-8"))


class DispatchableNowTests(unittest.TestCase):
    """Eligibility is not fixed at planning time; it moves as tasks complete."""

    def setUp(self):
        self.orchestrator = load_module(
            "worker_orchestrator", "scripts/worker_orchestrator.py"
        )

    def _task(self, task_id, files=(), depends=(), status="ready"):
        return {
            "id": task_id,
            "status": status,
            "expected_files": list(files),
            "expected_globs": [],
            "dependencies": list(depends),
        }

    def test_disjoint_ready_tasks_can_start_together(self):
        tasks = [
            self._task("T01", ["a.py"]),
            self._task("T02", ["b.py"]),
        ]
        self.assertEqual(
            self.orchestrator.dispatchable_now(tasks)["dispatchable"], ["T01", "T02"]
        )

    def test_tasks_sharing_a_file_do_not_both_dispatch(self):
        tasks = [
            self._task("T01", ["a.py"]),
            self._task("T02", ["a.py", "b.py"]),
        ]
        result = self.orchestrator.dispatchable_now(tasks)
        self.assertEqual(result["dispatchable"], ["T01"])
        self.assertIn("T02", result["ready"])

    def test_a_task_with_unmet_dependencies_is_blocked_not_ready(self):
        tasks = [
            self._task("T01", ["a.py"]),
            self._task("T02", ["b.py"], depends=["T01"]),
        ]
        result = self.orchestrator.dispatchable_now(tasks)
        self.assertEqual(result["ready"], ["T01"])
        self.assertEqual(result["blocked"], ["T02"])

    def test_finishing_a_task_opens_the_window(self):
        """The exact failure this exists to prevent: a window opening unnoticed."""
        tasks = [
            self._task("T01", ["a.py"], status="done"),
            self._task("T02", ["a.py"], depends=["T01"]),
            self._task("T03", ["b.py"], depends=["T01"]),
        ]
        self.assertEqual(
            self.orchestrator.dispatchable_now(tasks)["dispatchable"], ["T02", "T03"]
        )

    def test_a_task_without_declared_files_is_never_paired(self):
        tasks = [
            self._task("T01", ["a.py"]),
            self._task("T02", []),
        ]
        self.assertEqual(
            self.orchestrator.dispatchable_now(tasks)["dispatchable"], ["T01"]
        )

    def test_the_written_plan_names_what_can_start_together(self):
        tasks = [
            self._task("T01", ["a.py"], status="done"),
            self._task("T02", ["b.py"], depends=["T01"]),
            self._task("T03", ["c.py"], depends=["T01"]),
        ]
        now = self.orchestrator.dispatchable_now(tasks)
        self.assertEqual(now["dispatchable"], ["T02", "T03"])
        self.assertEqual(now["blocked"], [])


if __name__ == "__main__":
    unittest.main()


class DeferredTaskTest(unittest.TestCase):
    """A task moved to another issue keeps its line but is not work to pick up."""

    TASKS = """# Tasks

- [x] Implementation: collector [files: a.py]
- [ ] [deferred → 118-portfolio-mode-dashboard] Implementation: portfolio [files: b.py] [depends: T01]
- [ ] Release: register [files: c.py] [depends: T01]
"""

    def _module(self):
        return load_module("worker_orchestrator_deferred", "scripts/worker_orchestrator.py")

    def _tasks(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "tasks.md"
            path.write_text(self.TASKS, encoding="utf-8")
            return self._module().parse_tasks(path)

    def test_the_marker_becomes_a_status_not_prose(self):
        tasks = self._tasks()
        self.assertEqual(tasks[1]["status"], "deferred")
        self.assertEqual(tasks[1]["deferred_to"], "118-portfolio-mode-dashboard")
        self.assertNotIn("deferred", tasks[1]["text"])
        self.assertEqual(tasks[2]["status"], "ready")
        self.assertIsNone(tasks[2]["deferred_to"])

    def test_a_deferred_task_is_never_offered_for_dispatch(self):
        planned = [
            dict(task, id=f"T{index + 1:02d}")
            for index, task in enumerate(self._tasks())
        ]
        now = self._module().dispatchable_now(planned)
        self.assertNotIn("T02", now["dispatchable"])
        self.assertNotIn("T02", now["ready"])
        self.assertNotIn("T02", now["blocked"])
        self.assertEqual(now["deferred"], ["T02"])
        # The task behind it still runs; deferral is not a blocker.
        self.assertIn("T03", now["dispatchable"])
