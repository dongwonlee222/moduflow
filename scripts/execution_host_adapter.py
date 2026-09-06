#!/usr/bin/env python3
"""Issue 112 Stream C — one adapter per host, pure and registry-gated.

The routing result carries intent; this module carries vocabulary. The test for
which side a value belongs on is in
`docs/superpowers/specs/2026-09-05-issue-112-host-adapter-interface.md`: *would
its value change if the same work were done on a different host?* If yes, it
lives here.

Three things that are host vocabulary arrive here from `worker_orchestrator`,
where spec §8 measured them leaking into the canonical `worker-plan.json`:

  the `codex/` branch prefix        `worker_orchestrator.py:408`
  the GPT-5.6 model names          `worker_orchestrator.py:50-66`, used at `:388`
  the Superpowers subagent shape   `worker_orchestrator.py:412-417`

They are **relocated, not deleted** — each is correct for exactly one host, and
`CodexAdapter` is where all three are correct. T09 removes them from the write
path; this module is the destination that has to exist first.

Nothing here reads or writes a file, and nothing here imports another ModuFlow
module. An adapter takes a routing task and returns a host record. That purity
is what makes T07's proof a comparison rather than an integration test, and it
is asserted in `tests/test_execution_host_adapter.py`.
"""

# Intent vocabularies. Fixed here so an adapter cannot quietly widen them:
# a fourth tier or a third isolation mode is a change to the routing result and
# to every host at once, not a change one adapter may make on its own.
# Decision: `memory/decisions/2026-09-06-three-cognitive-demand-tiers-stay-the-
# adapter-gains-a-second-axis.md`.
COGNITIVE_DEMANDS = ("deep", "balanced", "fast")
ISOLATION_REQUIREMENTS = ("shared", "isolated")

# Every value below is a band of the live de-facto effort ladder —
# low, medium, high, xhigh, max — shared by OpenAI, Anthropic, OpenRouter's
# `cost_tier`, Codex CLI's `model_reasoning_effort` and Claude Code. The design
# doc's Evidence section verified that literal array in the shipped `claude`
# binary on 2026-09-06, alongside `effortLevel` and twelve
# `CLAUDE_CODE_EFFORT_LEVEL` occurrences.
#
# `balanced` is `high`, deliberately not `medium`. The bundled `claude-api`
# skill puts intelligence-sensitive work at a minimum of `high`, and every
# worker `balanced` covers — implementation-worker, qa-reviewer, ux-flow-worker
# — is coding or review. The "medium reasoning as the starting point" wording
# in `worker_orchestrator.py:60` is text from the file under audit and was not
# used as a source.
EFFORT_BY_DEMAND = {"deep": "xhigh", "balanced": "high", "fast": "low"}


class UnregisteredHostError(LookupError):
    """Raised for a host with no adapter. Decided 2026-09-06: refuse.

    `memory/decisions/2026-09-06-unregistered-host-refuses-rather-than-falling-
    back.md`. There is no generic adapter, because a generic adapter always
    works and something that always works is never replaced — which is exactly
    how a hardcoded `codex/` prefix survived in every worker plan regardless of
    host. The refusal makes the missing adapter visible at the moment it is
    missing.
    """

    def __init__(self, host_id, known):
        self.host_id = host_id
        self.known = tuple(known)
        super().__init__(
            f"no host adapter for {host_id!r}; ModuFlow refuses rather than guessing "
            f"host values. Add an adapter class to scripts/execution_host_adapter.py "
            f"and a fixture row to tests/fixtures/execution-routing/hosts.json "
            f"(hosts with an adapter today: {', '.join(self.known)})"
        )


def _check_demand(cognitive_demand):
    if cognitive_demand not in COGNITIVE_DEMANDS:
        raise ValueError(
            f"unknown cognitive demand {cognitive_demand!r}; "
            f"expected one of {', '.join(COGNITIVE_DEMANDS)}"
        )
    return cognitive_demand


def _check_requirement(requirement):
    if requirement not in ISOLATION_REQUIREMENTS:
        raise ValueError(
            f"unknown isolation requirement {requirement!r}; "
            f"expected one of {', '.join(ISOLATION_REQUIREMENTS)}"
        )
    return requirement


def task_prompt(task):
    """The two host-neutral lines of `worker_orchestrator.py:385-390`.

    The third line — `Cognitive demand: … — use gpt-5.6-…` — is gone. It existed
    because one field was doing two jobs and could not say "hard work" without
    naming something concrete; `model()` now says it on two axes instead, so no
    prompt has to carry a model name.
    """
    files = ", ".join(task.get("expected_files") or []) or "none"
    return f"Implement task: {task['text']}\nExpected files: {files}"


class HostAdapter:
    """Three methods, no state, no I/O. One instance is interchangeable with
    another, so callers may construct freely."""

    host_id = None

    def isolation(self, issue_id, task_id, requirement):
        """`shared` | `isolated` -> this host's isolation record.

        Every adapter answers with the same four keys so that a diff between
        two hosts in `tests/fixtures/execution-routing/hosts.json` lines up
        row for row:

          requirement  the intent, echoed back unchanged
          honoured     whether this host can actually provide it
          mechanism    how, in this host's own words; None when it cannot
          workspace    this host's name for the workspace, when it has one
          detail       why, when there is something the record must say

        A host that cannot honour `isolated` says so. It never downgrades to
        `shared` — the design's Known Limit is explicit that a silent downgrade
        is the wrong answer, and whether the planner should then refuse is a
        routing decision Gate 3 already owns.
        """
        raise NotImplementedError

    def model(self, cognitive_demand):
        """`deep` | `balanced` | `fast` -> {"effort": …, "model_hint": …}.

        Two values, not one, and both keys are always present — `dispatch` is
        the only method the design lets return `{}`. A host that chooses its
        own model answers with None twice, which is a real answer.
        """
        raise NotImplementedError

    def dispatch(self, task, plan):
        """One routing task -> this host's execution record, or `{}`.

        `{}` means the host has no subagent concept and the plan is executed
        inline. That is a legitimate host, not a broken adapter.
        """
        raise NotImplementedError


class ClaudeCodeAdapter(HostAdapter):
    """Claude Code. Effort ladder plus a subagent model, per the design doc's
    Evidence table (`deep` -> effortLevel + `model: opus`)."""

    host_id = "claude-code"

    def isolation(self, issue_id, task_id, requirement):
        del issue_id, task_id  # Claude Code names its own worktree; see below.
        if _check_requirement(requirement) == "shared":
            return {
                "requirement": "shared",
                "honoured": True,
                "mechanism": "same-working-tree",
                "workspace": None,
                "detail": None,
            }
        # Claude Code's subagent launcher takes an isolation mode and provisions
        # the git worktree itself; there is no name parameter to fill in. So the
        # adapter reports the mechanism and leaves `workspace` empty. Emitting a
        # branch name here would be a ModuFlow invention rather than a Claude
        # Code convention — the same mistake as `codex/` being written on every
        # host.
        return {
            "requirement": "isolated",
            "honoured": True,
            "mechanism": "agent-worktree",
            "workspace": None,
            "detail": "the host provisions and names the worktree",
        }

    def model(self, cognitive_demand):
        return {
            "effort": EFFORT_BY_DEMAND[_check_demand(cognitive_demand)],
            "model_hint": {"deep": "opus", "balanced": "sonnet", "fast": "haiku"}[
                cognitive_demand
            ],
        }

    def dispatch(self, task, plan):
        del plan  # Claude Code dispatches one task at a time.
        # Every key is a real parameter of Claude Code's subagent launcher.
        # `subagent_type` is the general-purpose agent because the ModuFlow
        # worker role is a ModuFlow concept, not a registered Claude Code agent
        # type; mapping the eight roles onto agent types is a separate question
        # and inventing type names here would be the failure this issue exists
        # to prevent.
        requirement = _check_requirement(task["isolation"])
        return {
            "subagent_type": "general-purpose",
            "description": f"ModuFlow {task['id']}",
            "prompt": task_prompt(task),
            "model": self.model(task["cognitive_demand"])["model_hint"],
            "isolation": "worktree" if requirement == "isolated" else None,
        }


class CodexAdapter(HostAdapter):
    """Codex CLI with Superpowers. Every value here was measured in
    `worker_orchestrator` and is correct for this host and no other."""

    host_id = "codex"

    def isolation(self, issue_id, task_id, requirement):
        if _check_requirement(requirement) == "shared":
            return {
                "requirement": "shared",
                "honoured": True,
                "mechanism": "same-working-tree",
                "workspace": None,
                "detail": None,
            }
        # The relocated leak. `worker_orchestrator.py:408` writes exactly this
        # string on every host; here it is written on the one host where a
        # `codex/` branch prefix is the right convention.
        return {
            "requirement": "isolated",
            "honoured": True,
            "mechanism": "git-worktree",
            "workspace": f"codex/{issue_id}-{task_id.lower()}",
            "detail": None,
        }

    def model(self, cognitive_demand):
        # `effort` feeds Codex CLI's `model_reasoning_effort`; `model_hint` is
        # the GPT-5.6 vocabulary relocated from `COGNITIVE_DEMAND_GUIDANCE`
        # (`worker_orchestrator.py:50-66`), which used to reach every task
        # prompt on every host through `:388`.
        return {
            "effort": EFFORT_BY_DEMAND[_check_demand(cognitive_demand)],
            "model_hint": {
                "deep": "gpt-5.6-sol",
                "balanced": "gpt-5.6-terra",
                "fast": "gpt-5.6-luna",
            }[cognitive_demand],
        }

    def dispatch(self, task, plan):
        del plan
        # The Superpowers subagent shape from `worker_orchestrator.py:412-417`,
        # kept field for field. `Workspace: "share"` is the only value present
        # in the shipped code, so it is the only one written here; the isolated
        # case is expressed by `isolation()`'s worktree instead of by a second
        # Workspace token nobody has verified.
        #
        # `Role` carried the ModuFlow worker name, which the routing result does
        # not have — the worker role is assigned in `worker_orchestrator`, and
        # T06 adds only the two intent fields the design names. When T09 holds
        # both sides it can pass the role on the task; until then the task id
        # identifies the work.
        return {
            "TypeName": "self",
            "Role": f"ModuFlow {task.get('worker') or task['id']}",
            "CognitiveDemand": _check_demand(task["cognitive_demand"]),
            "Workspace": "share",
            "Prompt": task_prompt(task),
        }


class CopilotAdapter(HostAdapter):
    """GitHub Copilot. The host that exercises the escape hatches.

    Researched 2026-09-06: Copilot uses automatic model selection and exposes no
    user-facing tier or effort field
    (https://docs.github.com/copilot/concepts/auto-model-selection). No
    subagent-delegation surface was verified either. So this adapter answers
    with less rather than with invented key names — an adapter that returns less
    is correct; one that returns a made-up field is the defect this issue exists
    to prevent.
    """

    host_id = "copilot"

    def isolation(self, issue_id, task_id, requirement):
        del issue_id, task_id
        if _check_requirement(requirement) == "shared":
            return {
                "requirement": "shared",
                "honoured": True,
                "mechanism": "same-working-tree",
                "workspace": None,
                "detail": None,
            }
        # The Known Limit, made concrete: no verified workspace-isolation
        # control on this host, so the record says the requirement is not
        # honoured. Reporting `shared` here would be a silent downgrade, and the
        # caller would have no way to know the plan is not what it asked for.
        return {
            "requirement": "isolated",
            "honoured": False,
            "mechanism": None,
            "workspace": None,
            "detail": "no verified workspace-isolation control on this host",
        }

    def model(self, cognitive_demand):
        # Both keys, no values. The shape is the contract; the content is what
        # this host genuinely does not expose.
        _check_demand(cognitive_demand)
        return {"effort": None, "model_hint": None}

    def dispatch(self, task, plan):
        del task, plan
        return {}


# One row per host. Adding a host is one class and one row here, plus one
# fixture row — and no change to `execution_routing.py` or to any canonical
# artifact. If a new host ever needs either, the boundary is in the wrong place.
ADAPTERS = {
    adapter.host_id: adapter
    for adapter in (ClaudeCodeAdapter, CodexAdapter, CopilotAdapter)
}


def known_hosts():
    return tuple(sorted(ADAPTERS))


def adapter_for(host_id):
    """The registry lookup, and the only place the refusal is decided."""
    try:
        adapter = ADAPTERS[host_id]
    except (KeyError, TypeError):
        # TypeError covers an unhashable host id. Either way the answer is the
        # same refusal, never a default adapter.
        raise UnregisteredHostError(host_id, known_hosts()) from None
    return adapter()
