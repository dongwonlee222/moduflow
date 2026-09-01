#!/usr/bin/env python3
"""Artifact lifecycle sync (048).

Canonical lifecycle and dependencies come from the shared issue schema model,
which preserves Markdown `**Status:**` / `**Blocked-by:**` compatibility. This
module projects that model into lifecycle views (.moduflow/state.json + the
dashboard's Active Issue section) and detects drift by consensus. It does NOT
write back to issue files (canonical source is human-authored).
"""
import argparse
import json
import re
from pathlib import Path

try:
    from scripts import project_operation, project_registry
except ImportError:  # pragma: no cover - direct script execution fallback
    import project_operation
    import project_registry

try:
    from scripts.project_issue_schema import (
        build_artifact_index,
        evaluate_project,
        markdown_blocked_by,
        markdown_priority,
        markdown_status,
        markdown_title,
        metadata_region,
    )
except ModuleNotFoundError:
    from project_issue_schema import (
        build_artifact_index,
        evaluate_project,
        markdown_blocked_by,
        markdown_priority,
        markdown_status,
        markdown_title,
        metadata_region,
    )


_READY_BLOCKING_DIAGNOSTICS = {
    "ISSUE_SOURCE_UNREADABLE",
    "ISSUE_SCHEMA_MALFORMED",
    "ISSUE_SCHEMA_UNSUPPORTED",
    "ISSUE_DUPLICATE_FIELD",
    "ISSUE_STATE_PROJECTION_MISMATCH",
    "ISSUE_DEPENDENCY_PROJECTION_MISMATCH",
    "ISSUE_AUX_STATUS_INVALID",
    "ISSUE_DEPENDENCY_UNMET",
    "ISSUE_DEPENDENCY_DANGLING",
    "ISSUE_DEPENDENCY_CYCLE",
}
_LIFECYCLE_SCHEMA_DIAGNOSTICS = {
    "ISSUE_SOURCE_UNREADABLE",
    "ISSUE_SCHEMA_MALFORMED",
    "ISSUE_SCHEMA_UNSUPPORTED",
    "ISSUE_DUPLICATE_FIELD",
    "ISSUE_STATE_PROJECTION_MISMATCH",
    "ISSUE_DEPENDENCY_PROJECTION_MISMATCH",
    "ISSUE_AUX_STATUS_INVALID",
}
_SYNC_FATAL_DIAGNOSTICS = {
    "ISSUE_SOURCE_UNREADABLE",
    "ISSUE_SCHEMA_MALFORMED",
    "ISSUE_SCHEMA_UNSUPPORTED",
    "ISSUE_DUPLICATE_FIELD",
}
_TRANSITION_ACTIONS = frozenset({"start", "update", "pause", "resume", "complete"})
_ROADMAP_PRIORITIES = frozenset({"p0", "p1", "p2", "p3"})

_ROADMAP_START = "<!-- moduflow:roadmap-projection:start -->"
_ROADMAP_END = "<!-- moduflow:roadmap-projection:end -->"


def _utf8_bytes(value, label):
    if not isinstance(value, bytes):
        raise TypeError(f"{label} must be bytes")
    value.decode("utf-8")
    return value


def _json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def render_issue_transition(issue_bytes, target_lifecycle, *, changed_on):
    """Return issue Markdown with only its canonical lifecycle line changed."""
    text = _utf8_bytes(issue_bytes, "issue_bytes").decode("utf-8")
    if target_lifecycle is None:
        return bytes(issue_bytes)
    if target_lifecycle not in {"backlog", "active", "done"}:
        raise ValueError("Unsupported target lifecycle")
    match = re.search(r"^\*\*Status:\s*[^*]+\*\*(?P<suffix>[^\n]*)$", text, re.M)
    if not match:
        raise ValueError("Owning issue requires a canonical Status line")
    suffix = match.group("suffix").strip()
    if suffix.startswith("—"):
        suffix = suffix[1:].strip()
    facts = [part.strip() for part in suffix.rstrip(".").split(";") if part.strip()]
    facts = [fact for fact in facts if not fact.startswith(("started ", "done "))]
    if target_lifecycle in {"active", "done"}:
        facts.append(f"started {changed_on}")
    if target_lifecycle == "done":
        facts.append(f"done {changed_on}")
    rendered_suffix = f" — {'; '.join(facts)}." if facts else ""
    replacement = f"**Status: {target_lifecycle}**{rendered_suffix}"
    return (text[: match.start()] + replacement + text[match.end() :]).encode("utf-8")


def render_state_projection(
    state_bytes,
    *,
    active_issue,
    phase,
    next_command,
    changed_on,
):
    """Return deterministic state JSON while preserving unrelated keys."""
    _utf8_bytes(state_bytes, "state_bytes")
    state = json.loads(state_bytes.decode("utf-8")) if state_bytes else {}
    if not isinstance(state, dict):
        raise ValueError("state projection requires a JSON object")
    state.setdefault("schema", "moduflow.state.v1")
    state["active_issue"] = active_issue
    state["phase"] = phase
    state.setdefault("active_goal", "")
    state["next_command"] = next_command
    state.setdefault("blockers", [])
    state["updated_at"] = changed_on
    return _json_bytes(state)


def render_dashboard_projection(
    dashboard_bytes,
    *,
    active_issue,
    phase,
    source_path,
):
    """Return dashboard bytes with only the Active Issue section replaced."""
    text = _utf8_bytes(dashboard_bytes, "dashboard_bytes").decode("utf-8")
    if active_issue:
        section = (
            "## Active Issue\n\n"
            f"- `{active_issue}` (phase: {phase}). Canonical: `{source_path}`.\n\n"
        )
    else:
        section = (
            "## Active Issue\n\n- None active. "
            "Run `product:status` to pick the next issue.\n\n"
        )
    pattern = re.compile(r"^##\s+Active Issue\s*$.*?(?=^##\s|\Z)", re.M | re.S)
    if not pattern.search(text):
        raise ValueError("dashboard requires an Active Issue section")
    return pattern.sub(lambda _match: section, text).encode("utf-8")


def render_issue_index(issues):
    """Return a deterministic physical compatibility index from projected issues."""
    if not isinstance(issues, list):
        raise TypeError("issues must be a list")
    detached = [dict(issue) for issue in issues]
    return _json_bytes(
        {
            "schema": "moduflow.issue-index.v1",
            "issues": sorted(detached, key=lambda issue: issue["id"]),
        }
    )


def render_roadmap_projection(
    roadmap_bytes,
    *,
    issue_id,
    priority,
    dependencies,
    release_order,
):
    """Replace or append the one bounded ModuFlow roadmap projection block."""
    text = _utf8_bytes(roadmap_bytes, "roadmap_bytes").decode("utf-8")
    dependency_text = ", ".join(dependencies) if dependencies else "none"
    release_text = str(release_order) if release_order not in (None, "") else "none"
    block = (
        f"{_ROADMAP_START}\n"
        f"- `{issue_id}` — priority `{priority}`; dependencies `{dependency_text}`; "
        f"release order `{release_text}`.\n"
        f"{_ROADMAP_END}"
    )
    pattern = re.compile(
        rf"{re.escape(_ROADMAP_START)}.*?{re.escape(_ROADMAP_END)}",
        re.S,
    )
    matches = list(pattern.finditer(text))
    if len(matches) > 1:
        raise ValueError("roadmap contains duplicate managed projection blocks")
    if matches:
        return pattern.sub(lambda _match: block, text).encode("utf-8")
    separator = "" if not text else ("\n\n" if not text.endswith("\n\n") else "")
    return (text + separator + block + "\n").encode("utf-8")


def read_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return None


def _issue_status(text):
    return markdown_status(text)


def _metadata_region(text):
    """Header region before the first '## ' section — metadata lines live
    there by convention (048/069). Restricting parsing here keeps body prose
    that QUOTES the syntax (e.g. a session note explaining the convention)
    from being misread as metadata."""
    return metadata_region(text)


def _issue_priority(text):
    return markdown_priority(text)


def _issue_blocked_by(text):
    return markdown_blocked_by(text)


def _lifecycle_state_from_evaluation(evaluation):
    issues = {
        issue["issue_id"]: issue.get("lifecycle_state")
        for issue in evaluation["issues"]
    }
    pick = lambda state: [
        issue_id for issue_id, lifecycle in issues.items() if lifecycle == state
    ]
    return {
        "issues": issues,
        "active": pick("active"),
        "done": pick("done"),
        "backlog": pick("backlog"),
        "superseded": pick("superseded"),
    }


def lifecycle_state(root, *, project_context=None):
    """Canonical lifecycle map projected from the shared issue model."""
    root = Path(root).resolve()
    context = project_context or project_registry.project_context_for_root(root)
    return _lifecycle_state_from_evaluation(
        evaluate_project(root, project_paths=context["relative_paths"])
    )


def _issue_title(text):
    return markdown_title(text)


def _compatibility_items(evaluation):
    return sorted(
        [
            {
                "id": issue["issue_id"],
                "status": issue.get("lifecycle_state"),
                "title": issue.get("title") or "",
                "priority": issue.get("priority"),
                "blocked_by": list(issue.get("blocked_by") or []),
            }
            for issue in evaluation["issues"]
        ],
        key=lambda item: item["id"],
    )


def list_issues(root, *, project_context=None):
    """Compatibility records for every issues/*.md file, sorted by id."""
    root = Path(root).resolve()
    context = project_context or project_registry.project_context_for_root(root)
    return _compatibility_items(
        evaluate_project(root, project_paths=context["relative_paths"])
    )


def ready_issues(root, *, project_context=None):
    """Startable backlog issues, priority-sorted (p0 first, then id).

    Structural spec/plan/review readiness is deliberately not required here.
    Shared schema, lifecycle projection, and dependency hard errors exclude an
    issue; satisfied dependencies allow it into this backward-compatible queue.
    """
    root = Path(root).resolve()
    context = project_context or project_registry.project_context_for_root(root)
    evaluation = evaluate_project(root, project_paths=context["relative_paths"])
    items = _compatibility_items(evaluation)
    blocked_ids = {
        issue["issue_id"]
        for issue in evaluation["issues"]
        if any(
            diagnostic.get("code") in _READY_BLOCKING_DIAGNOSTICS
            and (
                diagnostic.get("severity") == "error"
                or diagnostic.get("code") == "ISSUE_DEPENDENCY_UNMET"
            )
            for diagnostic in issue.get("diagnostics", [])
        )
    }
    ready = [
        i for i in items
        if i["status"] == "backlog"
        and i["id"] not in blocked_ids
    ]
    return sorted(ready, key=lambda i: (i["priority"], i["id"]))


def _phase_from_evaluated_issue(issue):
    artifact_phase = issue.get("artifact_phase") if issue else None
    return {
        "issue": "select",
        "spec": "spec",
        "plan": "plan",
        "tasks": "execute",
        "review": "review",
        "release": "release",
    }.get(artifact_phase, "select")


def infer_phase(root, issue_id, evaluation=None, *, project_context=None):
    if not issue_id:
        return "select"
    root = Path(root).resolve()
    context = project_context or project_registry.project_context_for_root(root)
    evaluation = evaluation or evaluate_project(
        root, project_paths=context["relative_paths"]
    )
    issue = next(
        (
            item
            for item in evaluation["issues"]
            if item["issue_id"] == issue_id
        ),
        None,
    )
    if issue is None:
        issue = build_artifact_index(root, [issue_id]).get(issue_id)
    return _phase_from_evaluated_issue(issue)


def _section_body(text, header):
    """Body between '## <header>' and the next '## ' (or end)."""
    m = re.search(r"^##\s+" + re.escape(header) + r"\s*$", text, re.M)
    if not m:
        return ""
    rest = text[m.end():]
    nxt = re.search(r"^##\s+", rest, re.M)
    return rest[:nxt.start()] if nxt else rest


def _format_schema_diagnostic(diagnostic):
    return (
        f"{diagnostic['code']} [{diagnostic.get('source_path') or 'unknown source'}]: "
        f"{diagnostic.get('message') or 'Issue schema drift.'} "
        f"Recommendation: {diagnostic.get('recommendation') or 'Run product:doctor.'}"
    )


def _dependency_drift_from_evaluation(evaluation):
    """Translate shared diagnostics to the lifecycle drift compatibility form."""
    drift = []
    issues = evaluation["issues"]
    reported_schema = set()
    reported_cycles = set()
    reported_cycle_groups = set()
    pending_cycle_fallbacks = []
    pending_cycle_groups = set()

    for issue in issues:
        issue_id = issue["issue_id"]
        lifecycle = issue.get("lifecycle_state")
        for diagnostic in issue.get("diagnostics", []):
            code = diagnostic.get("code")
            if (
                diagnostic.get("severity") == "error"
                and code in _LIFECYCLE_SCHEMA_DIAGNOSTICS
            ):
                key = (
                    code,
                    diagnostic.get("source_path"),
                    diagnostic.get("message"),
                )
                if key not in reported_schema:
                    reported_schema.add(key)
                    drift.append(_format_schema_diagnostic(diagnostic))
                continue

            if code == "ISSUE_DEPENDENCY_DANGLING":
                if lifecycle not in ("done", "superseded"):
                    drift.append(
                        "blocked_by references unknown issue "
                        f"'{diagnostic.get('current')}' in {issue_id}"
                    )
                continue

            if code == "ISSUE_DEPENDENCY_UNMET" and lifecycle == "active":
                dependency, _, blocker_status = str(
                    diagnostic.get("current") or ""
                ).partition(": ")
                drift.append(
                    f"active issue {issue_id} has unmet blocker '{dependency}' "
                    f"(status: {blocker_status or 'unknown'})"
                )
                continue

            if code != "ISSUE_DEPENDENCY_CYCLE":
                continue
            current = diagnostic.get("current")
            if isinstance(current, dict):
                representative = current.get("representative_issue_id")
                component_size = current.get("component_size")
                cycle_group = ("group", representative, component_size)
                fallback = (
                    f"dependency cycle group: {representative} "
                    f"(component size: {component_size})"
                )
            else:
                members = tuple(
                    sorted(
                        member.strip()
                        for member in str(current or "").split(",")
                        if member.strip()
                    )
                )
                cycle_group = ("members", *members)
                fallback = (
                    "dependency cycle members: "
                    f"{current or ', '.join(members)}"
                )
            cycle_paths = diagnostic.get("cycle_paths")
            if not cycle_paths:
                cycle_path = diagnostic.get("cycle_path")
                cycle_paths = [cycle_path] if cycle_path else []
            if cycle_paths:
                reported_cycle_groups.add(cycle_group)
                for cycle_path in cycle_paths:
                    cycle_key = tuple(cycle_path)
                    if cycle_key in reported_cycles:
                        continue
                    reported_cycles.add(cycle_key)
                    drift.append(
                        f"dependency cycle: {' -> '.join(cycle_path)}"
                    )
            elif (
                cycle_group not in reported_cycle_groups
                and cycle_group not in pending_cycle_groups
            ):
                pending_cycle_groups.add(cycle_group)
                pending_cycle_fallbacks.append((cycle_group, fallback))

    for cycle_group, fallback in pending_cycle_fallbacks:
        if cycle_group not in reported_cycle_groups:
            drift.append(fallback)

    return drift


def _dependency_drift(root, *, project_context=None):
    context = project_context or project_registry.project_context_for_root(root)
    return _dependency_drift_from_evaluation(
        evaluate_project(
            Path(root).resolve(), project_paths=context["relative_paths"]
        )
    )


def consensus_drift(root, evaluation=None, *, project_context=None):
    """Return only issue/state/dashboard consensus drift from one evaluation."""
    root = Path(root).resolve()
    context = project_context or project_registry.project_context_for_root(root)
    evaluation = evaluation or evaluate_project(
        root, project_paths=context["relative_paths"]
    )
    ls = _lifecycle_state_from_evaluation(evaluation)
    drift = []
    active = ls["active"]
    if len(active) > 1:
        drift.append(f"multiple active issues in issue files: {active}")
    issue_active = active[0] if len(active) == 1 else ""

    state = read_json(root / ".moduflow" / "state.json") or {}
    state_active = (state.get("active_issue") or "").strip()
    if state_active != issue_active:
        drift.append(
            f".moduflow/state.json active_issue '{state_active}' != issue-file active '{issue_active}'"
        )

    dash = project_registry.canonical_path(context, "workspace") / "dashboard.md"
    if dash.exists():
        dtext = dash.read_text(encoding="utf-8")
        active_body = _section_body(dtext, "Active Issue")
        for did in ls["done"]:
            if did in active_body:
                drift.append(f"dashboard Active Issue section still lists done issue {did}")
        if issue_active:
            if issue_active not in active_body:
                drift.append(f"dashboard Active Issue section omits active issue {issue_active}")
            if re.search(r"none active", active_body, re.I):
                drift.append(f"dashboard Active Issue says 'None active' but issue files have active {issue_active}")
        elif re.search(r"`0\d\d-[a-z0-9-]+`\s*\(phase", active_body):
            drift.append("dashboard Active Issue names an active issue but issue files have none")
    return drift


def lifecycle_drift(root, *, project_context=None):
    """Consensus and issue diagnostic drift. Returns [] when sources agree."""
    root = Path(root).resolve()
    context = project_context or project_registry.project_context_for_root(root)
    evaluation = evaluate_project(root, project_paths=context["relative_paths"])
    return (
        _dependency_drift_from_evaluation(evaluation)
        + consensus_drift(root, evaluation, project_context=context)
    )


def _load_lifecycle_transaction_module():
    try:
        import project_lifecycle_transaction
    except ImportError:  # pragma: no cover - package import fallback
        from scripts import project_lifecycle_transaction
    return project_lifecycle_transaction


def transition_lifecycle(
    root,
    issue_id,
    action,
    *,
    actor,
    source_event,
    target_status=None,
    priority=None,
    idempotency_key="",
    expected_issue_sha256="",
    loop_blocker="",
    require_issue_index=False,
    project_context=None,
    clock=None,
    fault_injector=None,
):
    """Apply one lifecycle transition through the transaction boundary."""
    values = {
        "issue_id": str(issue_id or "").strip(),
        "action": str(action or "").strip().lower(),
        "actor": str(actor or "").strip(),
        "source_event": str(source_event or "").strip(),
    }
    if values["action"] not in _TRANSITION_ACTIONS:
        raise ValueError("Unsupported lifecycle transition action")
    if not values["issue_id"] or not values["actor"] or not values["source_event"]:
        raise ValueError(
            "Lifecycle transition requires issue_id, actor, and source_event"
        )
    normalized_priority = None
    if priority is not None:
        normalized_priority = str(priority).strip().lower()
        if normalized_priority not in _ROADMAP_PRIORITIES:
            raise ValueError("Unsupported roadmap priority")

    boundary = _load_lifecycle_transaction_module()
    intent = boundary.LifecycleIntent(
        **values,
        target_lifecycle=target_status,
        roadmap_change=(
            {"priority": normalized_priority}
            if normalized_priority is not None
            else None
        ),
        idempotency_key=idempotency_key,
        expected_issue_sha256=expected_issue_sha256,
        loop_blocker=loop_blocker,
        require_issue_index=require_issue_index,
    )
    return boundary.apply_lifecycle_transaction(
        root,
        intent,
        project_context=project_context,
        clock=clock,
        fault_injector=fault_injector,
    )


def sync_lifecycle(
    root,
    *,
    project_context=None,
    actor="moduflow.lifecycle",
    source_event="sync_lifecycle",
    idempotency_key="",
    expected_issue_sha256="",
    require_issue_index=False,
    clock=None,
    fault_injector=None,
):
    """Single propagation point: issue Status -> .moduflow/state.json + dashboard
    Active Issue section. Idempotent. Touches only structured fields/sections."""
    root = Path(root).resolve()
    context = project_registry.context_for_operation(
        root,
        project_context=project_context,
    )
    project_operation.require_project_capability(context, "execute")
    evaluation = evaluate_project(root, project_paths=context["relative_paths"])
    ls = _lifecycle_state_from_evaluation(evaluation)
    errors = []
    for issue in evaluation["issues"]:
        issue_errors = [
            _format_schema_diagnostic(diagnostic)
            for diagnostic in issue.get("diagnostics", [])
            if (
                diagnostic.get("severity") == "error"
                and diagnostic.get("code") in _SYNC_FATAL_DIAGNOSTICS
            )
        ]
        errors.extend(issue_errors)
        if issue.get("lifecycle_state") is None and not issue_errors:
            errors.append(
                f"ISSUE_LIFECYCLE_UNRESOLVED [{issue['source_path']}]: "
                "Canonical lifecycle state is unavailable. Recommendation: "
                "Restore a supported, readable issue source and run product:doctor."
            )
    if errors:
        return {
            "status": "blocked",
            "active": "",
            "phase": "unresolved",
            "dashboard_updated": False,
            "errors": errors,
        }
    active = ls["active"][0] if len(ls["active"]) == 1 else ""
    active_issue = next(
        (
            issue
            for issue in evaluation["issues"]
            if issue["issue_id"] == active
        ),
        None,
    )
    phase = infer_phase(root, active, evaluation, project_context=context)
    owner = active_issue or next(
        (
            issue
            for issue in sorted(
                evaluation["issues"], key=lambda item: item["issue_id"]
            )
            if issue.get("lifecycle_state") in {"backlog", "active", "done"}
        ),
        None,
    )
    if owner is None:
        return {
            "status": "blocked",
            "active": "",
            "phase": "unresolved",
            "dashboard_updated": False,
            "errors": [
                "ISSUE_RECONCILE_OWNER_UNAVAILABLE: No canonical issue can own "
                "the lifecycle reconcile transaction. Recommendation: Create or "
                "restore a valid issue and run product:doctor."
            ],
        }

    boundary = _load_lifecycle_transaction_module()
    intent = boundary.LifecycleIntent(
        issue_id=owner["issue_id"],
        action="reconcile",
        actor=actor,
        source_event=source_event,
        target_lifecycle=None,
        idempotency_key=idempotency_key,
        expected_issue_sha256=expected_issue_sha256,
        require_issue_index=require_issue_index,
    )
    transaction = boundary.apply_lifecycle_transaction(
        root,
        intent,
        project_context=context,
        clock=clock,
        fault_injector=fault_injector,
    )
    dashboard_updated = (
        transaction.get("status") == "applied"
        and any(
            target.get("role") == "dashboard" and target.get("changed") is True
            for target in transaction.get("targets", [])
            if isinstance(target, dict)
        )
    )
    result = {
        "active": active,
        "phase": phase,
        "dashboard_updated": dashboard_updated,
        "transaction": transaction,
    }
    if transaction.get("status") not in {"applied", "noop"}:
        error_code = (
            transaction.get("error_code")
            or transaction.get("status")
            or "unknown"
        )
        result.update(
            {
                "status": "blocked",
                "errors": [
                    f"{error_code}: Lifecycle reconcile transaction did not commit. "
                    "Recommendation: Run product:doctor before retrying."
                ],
            }
        )
    return result


def _mutation_exit_code(result):
    return 0 if result.get("status") in {"applied", "noop"} else 1


@project_operation.cli_denial_boundary
def main():
    parser = argparse.ArgumentParser(description="ModuFlow artifact lifecycle sync (048).")
    parser.add_argument("project_path", nargs="?", default=".")
    parser.add_argument("--state", action="store_true", help="Print canonical lifecycle_state JSON.")
    parser.add_argument("--drift", action="store_true", help="Print lifecycle drift report (consensus).")
    parser.add_argument("--sync", action="store_true", help="Propagate issue Status to state.json + dashboard.")
    parser.add_argument("--issues", action="store_true", help="Print list_issues(root) JSON.")
    parser.add_argument("--ready", action="store_true", help="Print ready_issues(root) JSON.")
    mutation = parser.add_mutually_exclusive_group()
    mutation.add_argument("--transition", choices=sorted(_TRANSITION_ACTIONS))
    mutation.add_argument("--recover", nargs="?", const="", default=None)
    parser.add_argument("--issue-id")
    parser.add_argument("--target-status", choices=("backlog", "active", "done"))
    parser.add_argument("--priority", choices=sorted(_ROADMAP_PRIORITIES))
    parser.add_argument("--actor")
    parser.add_argument("--source-event")
    parser.add_argument("--idempotency-key", default="")
    parser.add_argument("--expected-issue-sha256", default="")
    parser.add_argument("--loop-blocker", default="")
    parser.add_argument("--require-issue-index", action="store_true")
    args = parser.parse_args()

    legacy_mode = any((args.state, args.drift, args.sync, args.issues, args.ready))
    transition_options = any(
        (
            args.issue_id,
            args.target_status,
            args.priority,
            args.actor,
            args.source_event,
            args.idempotency_key,
            args.expected_issue_sha256,
            args.loop_blocker,
            args.require_issue_index,
        )
    )
    if args.transition:
        if legacy_mode:
            parser.error("--transition cannot be combined with legacy operation flags")
        missing = [
            flag
            for flag, value in (
                ("--issue-id", args.issue_id),
                ("--actor", args.actor),
                ("--source-event", args.source_event),
            )
            if not value or not value.strip()
        ]
        if missing:
            parser.error(f"--transition requires {', '.join(missing)}")
    elif args.recover is not None:
        if legacy_mode:
            parser.error("--recover cannot be combined with legacy operation flags")
        if transition_options:
            parser.error("transition-only arguments require --transition")
    elif transition_options:
        parser.error("transition-only arguments require --transition")

    if args.transition:
        result = transition_lifecycle(
            args.project_path,
            args.issue_id,
            args.transition,
            actor=args.actor,
            source_event=args.source_event,
            target_status=args.target_status,
            priority=args.priority,
            idempotency_key=args.idempotency_key,
            expected_issue_sha256=args.expected_issue_sha256,
            loop_blocker=args.loop_blocker,
            require_issue_index=args.require_issue_index,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return _mutation_exit_code(result)
    if args.recover is not None:
        boundary = _load_lifecycle_transaction_module()
        result = boundary.recover_incomplete_transaction(
            args.project_path,
            args.recover,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return _mutation_exit_code(result)
    if args.issues:
        print(json.dumps(list_issues(args.project_path), ensure_ascii=False, indent=2))
        return 0
    if args.ready:
        print(json.dumps(ready_issues(args.project_path), ensure_ascii=False, indent=2))
        return 0
    if args.sync:
        result = sync_lifecycle(args.project_path)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1 if result.get("status") == "blocked" else 0
    if args.drift:
        print(json.dumps(lifecycle_drift(args.project_path), ensure_ascii=False, indent=2))
        return 0
    print(json.dumps(lifecycle_state(args.project_path), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
