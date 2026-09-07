#!/usr/bin/env python3
"""Issue 104 — one natural-language request in, one routing result out.

Five stages, called in a fixed order by `route_request`, which is the only
public entry:

    route_request(request, registry_path, *, host=None)
      ├─ stage_resolve      project_registry.resolve_project
      ├─ stage_overlap      the resolved project's open issues
      ├─ stage_capability   capability_routing.route_request
      ├─ stage_execution    execution_routing.build_routing
      └─ stage_commit       project_lifecycle_transaction

Nothing here re-implements what those modules do. Each stage calls one of them
and carries its result verbatim; a disagreement between two of them is a defect
in this module, not something to smooth over (spec R4).

**Order is enforced by structure, not by discipline.** Each stage takes the
accumulated result and raises `StageOrderError` when the field its predecessor
sets is missing. The spec names silent reordering as this issue's characteristic
failure, so a stage called out of order fails loudly rather than running against
an unresolved project.

Step 1 of the plan ships the contract and stage 1. Stages 2–5 are declared here
with their refusal paths so the ordering is testable from the start; each is
filled in by its own step. A half-built pipeline that runs stages 1–3 and falls
through is worse than one that stops and says where it stopped.
"""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

try:
    from scripts import (
        capability_routing,
        execution_routing,
        project_issue_schema,
        project_lifecycle,
        project_registry,
    )
except ImportError:  # pragma: no cover - direct script execution fallback
    import capability_routing
    import execution_routing
    import project_issue_schema
    import project_lifecycle
    import project_registry


ROUTING_SCHEMA = "moduflow.request-routing.v1"

STAGES = ("resolve", "overlap", "capability", "execution", "commit")
STATUSES = ("ok", "ambiguous", "refused", "blocked")


class StageOrderError(RuntimeError):
    """A stage was called before the stage that sets the field it reads.

    Raised rather than returning a refusal on purpose: an out-of-order call is a
    programming error in this module, not a condition a caller can act on.
    """


def _request_id(request):
    """A stable id for one request text. Not a secret, just a handle."""
    digest = hashlib.sha256(request.encode("utf-8")).hexdigest()
    return f"req-{digest[:12]}"


def new_result(request):
    """Every field the contract requires, present before any stage runs.

    R1: a reader must be able to assert that nothing happened rather than infer
    it, so `written` is an empty list from the start and stays one unless a
    stage actually writes.
    """
    return {
        "schema": ROUTING_SCHEMA,
        "request_id": _request_id(request),
        "request": request,
        "project": None,
        "stage": "resolve",
        "status": "ok",
        "action": None,
        "issue": None,
        # Stage 2's whole output. A list, never a ranking: the corpus
        # measurement found no rule that orders these honestly, so the order is
        # the issue id's and nothing more.
        "overlap_candidates": [],
        "capability": None,
        "execution": None,
        "question": None,
        "written": [],
        "next_command": None,
    }


def _stop(result, *, stage, status, question=None, next_command=None):
    """Finish here. `written` is emptied because no non-ok status may claim one."""
    result["stage"] = stage
    result["status"] = status
    result["question"] = question
    result["next_command"] = next_command
    if status != "ok":
        result["written"] = []
    return result


# ---------------------------------------------------------------------------
# Stage 1 — resolve
# ---------------------------------------------------------------------------

def stage_resolve(result, registry_path, *, explicit_project_id="", cwd=None,
                  active_project_id="", recent_selection=None):
    """Resolve one project before any project file is opened (R2).

    Ambiguity asks exactly one question, writes nothing, and calls no
    capability. Issue 129 settled that a decision request asks one question at a
    time; the same rule applies to this one.
    """
    resolution = project_registry.resolve_project(
        registry_path,
        explicit_project_id=explicit_project_id,
        cwd=cwd,
        request_text=result["request"],
        active_project_id=active_project_id,
        recent_selection=recent_selection,
    )
    status = resolution.get("status")
    if status == "resolved":
        result["project"] = resolution.get("project_id") or None
        result["stage"] = "resolve"
        result["status"] = "ok"
        result["_resolution"] = resolution
        return result

    question = (resolution.get("question") or "").strip()
    if not question:
        # The resolver always supplies one. If it ever does not, ask the only
        # question that is always answerable rather than inventing a candidate.
        question = "어느 프로젝트를 말씀하시는 건가요?"
    # One question. A resolver that joined two with a newline would make this a
    # two-question prompt, which the spec calls a defect.
    question = question.splitlines()[0].strip()
    return _stop(
        result,
        stage="resolve",
        status="ambiguous",
        question=question,
        next_command="프로젝트 이름을 넣어 다시 말씀해 주세요.",
    )


# ---------------------------------------------------------------------------
# Stages 2-5 — declared with their refusal paths, filled in by later steps
# ---------------------------------------------------------------------------

def _require(result, field, stage):
    if not isinstance(result, dict) or result.get(field) is None:
        raise StageOrderError(
            f"stage_{stage} called before a project was resolved "
            f"({field!r} is missing)"
        )


_BLOCKED_SECTION = re.compile(r"^##\s+안 고치면\s*$(.*?)(?=^## |\Z)", re.M | re.S)

OPEN_STATES = ("backlog", "active")


def _blocked_without_this(issues_dir, source_path):
    """The issue's `## 안 고치면` line, or "" when it has none.

    This is the one line that says who is blocked without the work, so it is
    what a reader needs to recognise an overlap. A missing section is not an
    error here — issue 129 owns requiring it, and stage 2 refusing on it would
    make an unrelated rule block routing.
    """
    path = issues_dir / Path(source_path).name
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return ""
    match = _BLOCKED_SECTION.search(text)
    if not match:
        return ""
    return " ".join(match.group(1).split())


def stage_overlap(result, *, chosen_issue=None, **kwargs):
    """R3 — surface the resolved project's open issues, judge none of them.

    Measured 2026-09-07 over 147 issues and 10,731 pairs: no mechanical rule
    separates same-work pairs from unrelated ones. Five of seven confirmed pairs
    score 0.00 on title similarity, and three share no Entry Points file at all.
    So this stage returns candidates in issue-id order and the reader names the
    overlap. See
    `memory/evidence/2026-09-07-overlap-detection-corpus-measurement.md`.

    `chosen_issue` is that reader's answer coming back in. It must name a
    candidate: an id outside this project's open issues is refused rather than
    attached, which is R5's sharpest edge — the caller, not the resolver, is
    the one reaching across.
    """
    _require(result, "project", "overlap")
    resolution = result["_resolution"]
    root = Path(resolution["canonical_root"])
    relative_paths = resolution.get("relative_paths") or {}
    issues_dir = root / relative_paths.get("issues", "issues")

    records = project_issue_schema.list_normalized_issues(root, relative_paths or None)
    candidates = [
        {
            "issue": record["issue_id"],
            "title": record["title"],
            "priority": record["priority"],
            "blocked_without_this": _blocked_without_this(
                issues_dir, record["source_path"]
            ),
        }
        for record in records
        if record.get("lifecycle_state") in OPEN_STATES
    ]
    result["overlap_candidates"] = candidates

    if chosen_issue is None:
        return result

    if chosen_issue not in {candidate["issue"] for candidate in candidates}:
        return _stop(
            result,
            stage="overlap",
            status="refused",
            next_command=(
                f"`{chosen_issue}`는 이 프로젝트의 열린 이슈가 아닙니다. "
                "후보 목록에서 골라 주세요."
            ),
        )
    result["action"] = "attach"
    result["issue"] = chosen_issue
    return result


def _no_capability(request, issue_id, reason):
    """097's own shape for "nothing routed", built without loading a registry.

    Emitted verbatim rather than as a bespoke dict so a consumer reads one
    shape whether or not the project has adapters.
    """
    return {
        "schema": capability_routing.ROUTING_SCHEMA,
        "request": request,
        "issue_id": issue_id,
        "outcome": "none",
        "stages": [],
        "current_stage": None,
        "sequence_state": "not_applicable",
        "clarification": None,
        "fallback": None,
        "reason": reason,
    }


def stage_capability(result, **kwargs):
    """R4 — consume `capability_routing`, never re-derive it.

    `outcome: none` is a normal result, not a refusal: reading it as one would
    refuse every request ModuFlow handles itself, which is most of them.

    **A missing registry and a broken one are different facts.** A project with
    no `adapters/capability-routing.json` has no adapters, which is `none`. A
    registry that exists and does not parse is a blocked project, and saying
    `none` there would report "nothing matched" for a file nobody can read.
    """
    _require(result, "project", "capability")
    resolution = result["_resolution"]
    root = Path(resolution["canonical_root"])
    issue_id = result["issue"] or "unassigned"

    if not (root / "adapters" / "capability-routing.json").is_file():
        result["capability"] = _no_capability(
            result["request"], issue_id, "no capability registry in this project"
        )
        return result

    try:
        registry = capability_routing.load_registry(root)
    except capability_routing.RegistryError as exc:
        return _stop(
            result,
            stage="capability",
            status="blocked",
            next_command=(
                "이 프로젝트의 `adapters/capability-routing.json`을 읽을 수 "
                f"없습니다: {exc}"
            ),
        )

    try:
        result["capability"] = capability_routing.route_request(
            result["request"],
            registry,
            issue_id=issue_id,
            target_root=str(root),
        )
    except capability_routing.RegistryError as exc:
        # `load_registry` is not the only place a bad registry surfaces.
        # `_build_stage` validates `output_artifact` against the target root at
        # routing time, so a registry that loads can still raise here — found by
        # a fixture whose artifact path escaped `specs/`. Uncaught, that turns a
        # misconfigured project into a traceback instead of a blocked result.
        return _stop(
            result,
            stage="capability",
            status="blocked",
            next_command=(
                "이 프로젝트의 어댑터 설정이 잘못됐습니다: " f"{exc}"
            ),
        )
    return result


def stage_execution(result, **kwargs):
    """R4 — consume 112's `build_routing` unchanged.

    Execution needs a task list, and a task list belongs to an issue. With no
    `chosen_issue` there is nothing to route and `execution` stays null; that is
    the ordinary case for "상태 알려줘", not a failure.

    `needs_plan` blocks. 112 already reports it with `written: []`, and this
    stage stops rather than continuing to the one stage that writes.
    """
    _require(result, "project", "execution")
    if not result["issue"]:
        return result

    resolution = result["_resolution"]
    root = Path(resolution["canonical_root"])
    relative_paths = resolution.get("relative_paths") or {}
    tasks_path = root / relative_paths.get("specs", "specs") / result["issue"] / "tasks.md"
    if not tasks_path.is_file():
        return result

    tasks = execution_routing.scan_tasks(tasks_path)
    routing_result = execution_routing.build_routing(
        tasks, str(root), issue_id=result["issue"]
    )
    result["execution"] = routing_result

    if routing_result.get("status") == "needs_plan":
        return _stop(
            result,
            stage="execution",
            status="blocked",
            next_command=routing_result.get("next_command"),
        )
    return result


def stage_commit(result, *, commit=False, actor="moduflow", **kwargs):
    """R6 — the only stage that writes, and it writes through 103's transaction.

    Last on purpose: a validation failure has to roll back rather than leave
    half-written state, and that is only true if nothing wrote before it.

    **`commit` defaults to False, and that is a decision, not an oversight.**
    R6 says this stage commits and does not say when it is asked to. Making a
    routing call transact by default means "what would this request do?" changes
    state to answer, which is the opposite of what stage 2 was just rebuilt to
    do. A caller that wants the transition asks for it. Recorded in the spec
    under R6 as a deviation so it is visible rather than discovered.

    The transition itself is `project_lifecycle.transition_lifecycle` — the same
    entry `product:start` uses. Rebuilding a `LifecycleIntent` here would be
    re-deriving what a working module already derives, which is the mistake R4
    names one layer up.
    """
    _require(result, "project", "commit")
    if not commit or result["action"] != "attach" or not result["issue"]:
        return result

    resolution = result["_resolution"]
    root = Path(resolution["canonical_root"])
    try:
        transaction = project_lifecycle.transition_lifecycle(
            root,
            result["issue"],
            "start",
            actor=actor,
            source_event="request-routing",
        )
    except Exception as exc:  # noqa: BLE001 - the boundary raises several types
        # 103 owns rolling back; this owns not reporting success afterwards.
        # The exception type is deliberately not narrowed: `LifecyclePlanError`,
        # `LifecycleProjectedValidationError` and `LifecycleJournalError` are
        # three of several, and a new one must stop the pipeline rather than
        # escape as a traceback through a routing call.
        return _stop(
            result,
            stage="commit",
            status="blocked",
            next_command=f"전이가 거부됐습니다: {exc}",
        )

    result["stage"] = "commit"
    result["written"] = list(transaction.get("written") or []) or [
        f"{result['issue']} 상태 전이"
    ]
    return result


# ---------------------------------------------------------------------------
# The only public entry
# ---------------------------------------------------------------------------

def route_request(request, registry_path, *, host=None, explicit_project_id="",
                  cwd=None, active_project_id="", recent_selection=None,
                  chosen_issue=None, commit=False, actor="moduflow"):
    """One request in, one `moduflow.request-routing.v1` result out."""
    if not isinstance(request, str):
        raise TypeError("request must be a string")
    result = new_result(request)

    result = stage_resolve(
        result,
        registry_path,
        explicit_project_id=explicit_project_id,
        cwd=cwd,
        active_project_id=active_project_id,
        recent_selection=recent_selection,
    )
    if result["status"] != "ok":
        return _public(result)

    result = stage_overlap(result, host=host, chosen_issue=chosen_issue)
    if result["status"] != "ok":
        return _public(result)

    result = stage_capability(result, host=host)
    if result["status"] != "ok":
        return _public(result)

    result = stage_execution(result, host=host)
    if result["status"] != "ok":
        return _public(result)

    result = stage_commit(result, host=host, commit=commit, actor=actor)
    return _public(result)


def _public(result):
    """Drop the internal carry fields.

    R5: the resolution carries the other candidates' ids, and returning it would
    surface project B to a request that resolved to project A — a leak that
    passes every behavioural test because the value is never *used*.
    """
    return {key: value for key, value in result.items() if not key.startswith("_")}


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Route one natural-language request through the five stages.",
    )
    parser.add_argument("request", help="what the person said, verbatim")
    parser.add_argument(
        "registry",
        nargs="?",
        default=".moduflow/projects.json",
        help="project registry path (default: .moduflow/projects.json)",
    )
    parser.add_argument(
        "--project",
        default="",
        help="skip resolution and name the project id outright",
    )
    parser.add_argument(
        "--chosen-issue",
        default=None,
        help="the overlap the reader picked from `overlap_candidates`",
    )
    parser.add_argument(
        "--commit",
        action="store_true",
        help=(
            "actually transition the chosen issue. Without it nothing is "
            "written and the result says what it would do."
        ),
    )
    args = parser.parse_args(list(sys.argv[1:] if argv is None else argv))

    result = route_request(
        args.request,
        Path(args.registry),
        explicit_project_id=args.project,
        chosen_issue=args.chosen_issue,
        commit=args.commit,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
