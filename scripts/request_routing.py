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
import hashlib
import json
import sys
from pathlib import Path

try:
    from scripts import capability_routing, execution_routing, project_registry
except ImportError:  # pragma: no cover - direct script execution fallback
    import capability_routing
    import execution_routing
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


def stage_overlap(result, **kwargs):
    """R3 — surface the resolved project's open issues, judge none of them.

    Measured 2026-09-07 over 147 issues and 10,731 pairs: no mechanical rule
    separates same-work pairs from unrelated ones. Five of seven confirmed pairs
    score 0.00 on title similarity. So this stage returns candidates and the
    reader names the overlap. See
    `memory/evidence/2026-09-07-overlap-detection-corpus-measurement.md`.

    Step 2 of the plan fills this in.
    """
    _require(result, "project", "overlap")
    return result


def stage_capability(result, **kwargs):
    """R4 — consume `capability_routing`, never re-derive it.

    Step 3 of the plan fills this in. `outcome: none` is a normal result, not a
    refusal: reading it as one would refuse every request ModuFlow handles
    itself, which is most of them.
    """
    _require(result, "project", "capability")
    return result


def stage_execution(result, **kwargs):
    """R4 — consume 112's `build_routing` unchanged. Step 4 fills this in."""
    _require(result, "project", "execution")
    return result


def stage_commit(result, **kwargs):
    """R6 — the only stage that writes, and it writes through 103's transaction.

    Step 5 fills this in. Last on purpose: a validation failure has to roll back
    rather than leave half-written state, and that is only true if nothing wrote
    before it.
    """
    _require(result, "project", "commit")
    return result


# ---------------------------------------------------------------------------
# The only public entry
# ---------------------------------------------------------------------------

def route_request(request, registry_path, *, host=None, explicit_project_id="",
                  cwd=None, active_project_id="", recent_selection=None):
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

    result = stage_overlap(result, host=host)
    if result["status"] != "ok":
        return _public(result)

    result = stage_capability(result, host=host)
    if result["status"] != "ok":
        return _public(result)

    result = stage_execution(result, host=host)
    if result["status"] != "ok":
        return _public(result)

    result = stage_commit(result, host=host)
    return _public(result)


def _public(result):
    """Drop the internal carry fields.

    R5: the resolution carries the other candidates' ids, and returning it would
    surface project B to a request that resolved to project A — a leak that
    passes every behavioural test because the value is never *used*.
    """
    return {key: value for key, value in result.items() if not key.startswith("_")}


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        print("usage: request_routing.py <request> [registry-path]", file=sys.stderr)
        return 2
    request = argv[0]
    registry = Path(argv[1]) if len(argv) > 1 else Path(".moduflow/projects.json")
    result = route_request(request, registry)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
