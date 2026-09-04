"""Append-only analysis run records for Issue 091.

One parser for `moduflow.analysis-runs.v1`. Mirrors the structure of
`project_artifact_registry` so the two canonical Markdown+JSON formats stay
reviewable side by side. No I/O beyond the caller's text.
"""

import importlib
import json
import re
from pathlib import Path

_HERE = Path(__file__).resolve().parent


def _module(name):
    """Load a sibling script whether imported as a package or by file path."""
    try:
        return importlib.import_module(f"scripts.{name}")
    except ImportError:
        spec = importlib.util.spec_from_file_location(name, _HERE / f"{name}.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

SCHEMA = "moduflow.analysis-runs.v1"
ID_RE = re.compile(
    r"run-[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\Z"
)
ISO_DATE_RE = re.compile(r"\A\d{4}-\d{2}-\d{2}\Z")

CLAIM_CLASSES = ("exploratory", "profitability", "causal")
RUN_STATES = ("draft", "completed")
VALIDATION_STATES = ("unvalidated", "passed", "failed")
APPROVAL_STATES = ("unapproved", "approved")
DECISION_STATES = ("decided", "waiting_on_maturity", "superseded")
MATURITY_STATES = ("mature", "immature", "unknown")
CHECK_RESULTS = ("pass", "fail", "not_applicable")
CHECK_SOURCES = ("code", "playbook")

# R5 amendment boundary: only these change in place on an existing run.
AMENDABLE_FIELDS = (
    "run_state",
    "validation_state",
    "approval_state",
    "approval_ref",
    "decision_state",
    "issue_id",
)

# R4 minimum checks enforced by code. Everything else lives in the playbook.
CODE_CHECKS = {
    "exploratory": ("population-defined",),
    "profitability": (
        "population-defined",
        "denominator-stated",
        "cost-applicability-explicit",
    ),
    "causal": ("population-defined", "denominator-stated"),
}

FIELDS = (
    "id",
    "title",
    "issue_id",
    "playbook_ref",
    "decision_question",
    "claim_class",
    "population",
    "measure",
    "time_window",
    "maturity",
    "costs",
    "filters",
    "exclusions",
    "method",
    "sources",
    "execution_evidence",
    "checks",
    "outputs",
    "production_record_ref",
    "conclusion",
    "caveats",
    "decision_refs",
    "run_state",
    "validation_state",
    "approval_state",
    "decision_state",
    "approval_ref",
    "state_history",
    "follow_up",
    "supersedes",
    "change_reason",
    "created_at",
)


def diagnostic(code, field="", run_id="", severity="error"):
    return {
        "code": code,
        "severity": severity,
        "run_id": run_id,
        "field": field,
    }


def _line(value):
    return isinstance(value, str) and value.strip() != "" and "\n" not in value


def _short_line(value):
    return _line(value) and len(value) <= 240


def _iso(value):
    return isinstance(value, str) and bool(ISO_DATE_RE.match(value))


def _mapping(value, keys):
    return isinstance(value, dict) and set(value) == set(keys)


def _rule_list(value, keys):
    if not isinstance(value, list):
        return False
    return all(_mapping(item, keys) and all(_line(item[k]) for k in keys) for item in value)


def _validate_population(entry, add):
    population = entry.get("population")
    if not _mapping(population, ("definition", "comparison", "comparison_reason")):
        add("RUN_FIELD_INVALID", "population")
        return
    if not _line(population["definition"]):
        add("RUN_FIELD_INVALID", "population.definition")
    if population["comparison"] is None and not _line(population["comparison_reason"]):
        add("RUN_NULL_WITHOUT_REASON", "population.comparison_reason")


def _validate_measure(entry, add):
    measure = entry.get("measure")
    if not _mapping(measure, ("numerator", "denominator", "denominator_reason", "unit")):
        add("RUN_FIELD_INVALID", "measure")
        return
    if not _line(measure["numerator"]) or not _line(measure["unit"]):
        add("RUN_FIELD_INVALID", "measure")
    if measure["denominator"] is None and not _line(measure["denominator_reason"]):
        add("RUN_NULL_WITHOUT_REASON", "measure.denominator_reason")


def _validate_window(entry, add):
    window = entry.get("time_window")
    if not _mapping(window, ("start", "end", "label", "grain")):
        add("RUN_FIELD_INVALID", "time_window")
        return
    if not _line(window["label"]):
        add("RUN_FIELD_INVALID", "time_window.label")
    dated = window["start"] is not None or window["end"] is not None
    if dated:
        if not (_iso(window["start"]) and _iso(window["end"])):
            add("RUN_FIELD_INVALID", "time_window")
        elif window["start"] > window["end"]:
            add("RUN_FIELD_INVALID", "time_window")
        if not _line(window["grain"]):
            add("RUN_FIELD_INVALID", "time_window.grain")


def _validate_maturity(entry, add):
    maturity = entry.get("maturity")
    if not _mapping(maturity, ("status", "observation_until", "reason")):
        add("RUN_FIELD_INVALID", "maturity")
        return
    if maturity["status"] not in MATURITY_STATES:
        add("RUN_FIELD_INVALID", "maturity.status")
    elif maturity["status"] == "immature":
        if not _iso(maturity["observation_until"]) or not _line(maturity["reason"]):
            add("RUN_FIELD_INVALID", "maturity")


def _validate_costs(entry, add):
    costs = entry.get("costs")
    if not _mapping(costs, ("applicable", "items", "unknown_items", "reason")):
        add("RUN_FIELD_INVALID", "costs")
        return
    if not isinstance(costs["applicable"], bool):
        add("RUN_FIELD_INVALID", "costs.applicable")
        return
    if not _rule_list(costs["items"], ("name", "basis")):
        add("RUN_FIELD_INVALID", "costs.items")
    if not isinstance(costs["unknown_items"], list) or not all(
        _line(item) for item in costs["unknown_items"]
    ):
        add("RUN_FIELD_INVALID", "costs.unknown_items")
    if not costs["applicable"] and not _line(costs["reason"]):
        add("RUN_NULL_WITHOUT_REASON", "costs.reason")


def _validate_checks(entry, add):
    checks = entry.get("checks")
    if not isinstance(checks, list):
        add("RUN_FIELD_INVALID", "checks")
        return []
    seen = []
    for check in checks:
        if not _mapping(check, ("id", "source", "result", "reason", "evidence_ref")):
            add("RUN_FIELD_INVALID", "checks")
            continue
        if not _line(check["id"]) or check["source"] not in CHECK_SOURCES:
            add("RUN_FIELD_INVALID", "checks")
            continue
        if check["result"] not in CHECK_RESULTS:
            add("RUN_FIELD_INVALID", "checks")
            continue
        if check["result"] in ("fail", "not_applicable") and not _line(check["reason"]):
            add("CHECK_UNEXPLAINED", check["id"])
        seen.append(check)
    return seen


def _validate_states(entry, add):
    if entry.get("run_state") not in RUN_STATES:
        add("RUN_FIELD_INVALID", "run_state")
    if entry.get("validation_state") not in VALIDATION_STATES:
        add("RUN_FIELD_INVALID", "validation_state")
    if entry.get("approval_state") not in APPROVAL_STATES:
        add("RUN_FIELD_INVALID", "approval_state")
    if entry.get("decision_state") not in DECISION_STATES:
        add("RUN_FIELD_INVALID", "decision_state")

    approved = entry.get("approval_state") == "approved"
    if approved and not _line(entry.get("approval_ref")):
        add("RUN_APPROVAL_EVIDENCE_MISSING", "approval_ref")
    if not approved and entry.get("approval_ref") not in (None, ""):
        # Retaining evidence on an unapproved run is allowed; only invent is not.
        pass
    if entry.get("issue_id") == "unassigned" and approved:
        add("RUN_UNASSIGNED_NOT_FINAL", "approval_state")
    if entry.get("decision_state") == "waiting_on_maturity":
        immature = isinstance(entry.get("maturity"), dict) and entry["maturity"].get(
            "status"
        ) == "immature"
        follow = entry.get("follow_up")
        conditioned = isinstance(follow, dict) and _line(follow.get("condition"))
        if not immature and not conditioned:
            add("RUN_FIELD_INVALID", "decision_state")


def _validate_follow_up(entry, add):
    follow = entry.get("follow_up")
    if follow is None:
        return
    if not _mapping(follow, ("due_on", "condition", "scheduled")):
        add("RUN_FIELD_INVALID", "follow_up")
        return
    if follow["scheduled"] is not False:
        add("FOLLOW_UP_NOT_SCHEDULABLE", "follow_up.scheduled")
    if not _iso(follow["due_on"]) or not _line(follow["condition"]):
        add("RUN_FIELD_INVALID", "follow_up")


def _validate_history(entry, add):
    history = entry.get("state_history")
    if not isinstance(history, list):
        add("RUN_FIELD_INVALID", "state_history")
        return
    latest = {}
    for item in history:
        if not _mapping(
            item, ("field", "from", "to", "reason", "evidence_ref", "recorded_at")
        ):
            add("RUN_FIELD_INVALID", "state_history")
            continue
        if item["field"] not in AMENDABLE_FIELDS:
            add("RUN_AMENDMENT_FORBIDDEN", item["field"])
            continue
        if not _line(item["reason"]) or not _iso(item["recorded_at"]):
            add("RUN_FIELD_INVALID", "state_history")
            continue
        if item["field"] in ("approval_state", "validation_state") and item["to"] in (
            "approved",
            "passed",
        ):
            if not _line(item["evidence_ref"]):
                add("RUN_APPROVAL_EVIDENCE_MISSING", "state_history")
        latest[item["field"]] = item["to"]
    for field, value in latest.items():
        if entry.get(field) != value:
            add("RUN_AMENDMENT_FORBIDDEN", field)


def _validate_code_checks(entry, add):
    claim = entry.get("claim_class")
    if claim not in CLAIM_CLASSES:
        add("RUN_FIELD_INVALID", "claim_class")
        return
    recorded = {
        check["id"]: check
        for check in entry.get("checks", [])
        if isinstance(check, dict) and isinstance(check.get("id"), str)
    }
    for required in CODE_CHECKS[claim]:
        if required not in recorded:
            add("CHECK_MISSING", required)
    if claim in ("profitability", "causal"):
        for check in recorded.values():
            if check.get("result") == "pass" and not _line(check.get("evidence_ref")):
                add("CHECK_EVIDENCE_MISSING", check.get("id", ""))
    if any(check.get("result") == "fail" for check in recorded.values()):
        if entry.get("validation_state") == "passed":
            add("RUN_VALIDATION_CONTRADICTED", "validation_state")
    costs = entry.get("costs")
    if (
        claim == "profitability"
        and isinstance(costs, dict)
        and costs.get("unknown_items")
        and entry.get("decision_state") == "decided"
    ):
        add("COST_UNKNOWN_NOT_ZERO", "costs.unknown_items")


def validate_run(entry, *, today=None):
    """Pure R2/R4/R5/R6 validation. Returns an ordered diagnostic list."""
    findings = []

    def add(code, field="", severity="error"):
        findings.append(
            diagnostic(
                code,
                field,
                entry.get("id", "") if isinstance(entry, dict) else "",
                severity,
            )
        )

    if not isinstance(entry, dict):
        return [diagnostic("RUN_RECORD_INVALID")]
    missing = [name for name in FIELDS if name not in entry]
    if missing:
        for name in missing:
            add("RUN_FIELD_MISSING", name)
        return findings
    if set(entry) - set(FIELDS):
        add("RUN_FIELD_UNKNOWN", ", ".join(sorted(set(entry) - set(FIELDS))))

    if not isinstance(entry["id"], str) or not ID_RE.match(entry["id"]):
        add("RUN_FIELD_INVALID", "id")
    for name in ("title", "decision_question", "conclusion"):
        if not _short_line(entry[name]):
            add("RUN_FIELD_INVALID", name)
    if not _line(entry["issue_id"]):
        add("RUN_FIELD_INVALID", "issue_id")
    if not _iso(entry["created_at"]):
        add("RUN_FIELD_INVALID", "created_at")

    playbook = entry["playbook_ref"]
    if playbook is not None and not (
        _mapping(playbook, ("playbook_id", "version", "deliverable_type"))
        and all(_line(playbook[key]) for key in playbook)
    ):
        add("RUN_FIELD_INVALID", "playbook_ref")

    _validate_population(entry, add)
    _validate_measure(entry, add)
    _validate_window(entry, add)
    _validate_maturity(entry, add)
    _validate_costs(entry, add)
    if not _rule_list(entry["filters"], ("rule", "reason")):
        add("RUN_FIELD_INVALID", "filters")
    if not _rule_list(entry["exclusions"], ("rule", "reason")):
        add("RUN_FIELD_INVALID", "exclusions")
    method = entry["method"]
    if not _mapping(method, ("steps", "tooling")) or not _line(method.get("tooling", "")):
        add("RUN_FIELD_INVALID", "method")
    elif not isinstance(method["steps"], list) or not method["steps"]:
        add("RUN_FIELD_INVALID", "method.steps")
    if not isinstance(entry["sources"], list):
        add("RUN_FIELD_INVALID", "sources")
    if not isinstance(entry["outputs"], list):
        add("RUN_FIELD_INVALID", "outputs")
    if not isinstance(entry["caveats"], list) or (
        entry["claim_class"] != "exploratory" and not entry["caveats"]
    ):
        add("RUN_FIELD_INVALID", "caveats")
    if not isinstance(entry["decision_refs"], list):
        add("RUN_FIELD_INVALID", "decision_refs")

    _validate_checks(entry, add)
    _validate_states(entry, add)
    _validate_follow_up(entry, add)
    _validate_history(entry, add)
    _validate_code_checks(entry, add)

    if entry["supersedes"] is not None:
        if not (isinstance(entry["supersedes"], str) and ID_RE.match(entry["supersedes"])):
            add("RUN_FIELD_INVALID", "supersedes")
        elif entry["supersedes"] == entry["id"]:
            add("RUN_FIELD_INVALID", "supersedes")
        if not _line(entry["change_reason"]):
            add("RUN_NULL_WITHOUT_REASON", "change_reason")

    if today and _iso(today) and isinstance(entry["follow_up"], dict):
        due = entry["follow_up"].get("due_on")
        if _iso(due) and due < today:
            add("FOLLOW_UP_DUE", "follow_up.due_on", "warning")
        add("FOLLOW_UP_INTENT_ONLY", "follow_up", "info")
    return findings


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def _run_blocks(text):
    headings = list(re.finditer(r"^## ([^\n]+)(?:\n|\Z)", text, re.M))
    for index, heading in enumerate(headings):
        end = headings[index + 1].start() if index + 1 < len(headings) else len(text)
        yield heading.group(1).strip(), text[heading.end():end]


def parse_analysis_runs(text):
    findings = []
    result = {"schema": SCHEMA, "entries": [], "diagnostics": findings, "metadata_valid": False}
    if not isinstance(text, str) or not re.match(
        r"\A---\nschema: moduflow\.analysis-runs\.v1\n---(?:\n|\Z)", text
    ):
        findings.append(diagnostic("RUNS_SCHEMA_UNSUPPORTED", "schema"))
        return result

    seen = set()
    for heading, body in _run_blocks(text):
        blocks = re.findall(r"```json\n(.*?)\n```", body, re.S)
        if len(blocks) != 1:
            findings.append(diagnostic("RUN_BLOCK_INVALID", "metadata", heading))
            continue
        try:
            entry = json.loads(blocks[0], object_pairs_hook=_unique_object)
        except ValueError:
            findings.append(diagnostic("RUN_BLOCK_INVALID", "metadata", heading))
            continue
        if not isinstance(entry, dict) or entry.get("id") != heading:
            findings.append(diagnostic("RUN_ID_MISMATCH", "id", heading))
            continue
        if heading in seen:
            findings.append(diagnostic("RUN_ID_DUPLICATE", "id", heading))
            continue
        seen.add(heading)
        entry_findings = validate_run(entry)
        findings.extend(entry_findings)
        if not [item for item in entry_findings if item["severity"] == "error"]:
            result["entries"].append(entry)

    result["metadata_valid"] = not [
        item for item in findings if item["severity"] == "error"
    ]
    return result


def render_run_entry(entry):
    if [item for item in validate_run(entry) if item["severity"] == "error"]:
        raise ValueError("RUN_RECORD_INVALID")
    return f"## {entry['id']}\n\n```json\n{json.dumps(entry, ensure_ascii=False, indent=2)}\n```\n\n"


def check_amendment(before, after):
    """R5: only the six amendable fields change, each with one new history entry."""
    findings = []
    if not isinstance(before, dict) or not isinstance(after, dict):
        return [diagnostic("RUN_RECORD_INVALID")]
    if before.get("id") != after.get("id"):
        return [diagnostic("RUN_AMENDMENT_FORBIDDEN", "id", before.get("id", ""))]

    changed = [
        name
        for name in FIELDS
        if name != "state_history" and before.get(name) != after.get(name)
    ]
    for name in changed:
        if name not in AMENDABLE_FIELDS:
            findings.append(diagnostic("RUN_AMENDMENT_FORBIDDEN", name, after["id"]))

    old_history = before.get("state_history") or []
    new_history = after.get("state_history") or []
    if new_history[: len(old_history)] != old_history:
        findings.append(diagnostic("RUN_AMENDMENT_FORBIDDEN", "state_history", after["id"]))
        return findings
    appended = new_history[len(old_history):]
    if before.get("issue_id") != after.get("issue_id") and before.get("issue_id") != "unassigned":
        findings.append(diagnostic("RUN_AMENDMENT_FORBIDDEN", "issue_id", after["id"]))
    allowed = [name for name in changed if name in AMENDABLE_FIELDS]
    if sorted(item.get("field") for item in appended) != sorted(allowed):
        findings.append(diagnostic("RUN_AMENDMENT_FORBIDDEN", "state_history", after["id"]))
    findings.extend(validate_run(after))
    return findings


READ_SCHEMA = "moduflow.analysis-run-read.v1"
DEFAULT_LIMIT = 20
CLAIM_LINE_RE = re.compile(r"^\s*-?\s*기본 주장 종류:\s*([a-z]+)", re.M)


class PlaybookUnresolved(ValueError):
    def __init__(self, name):
        super().__init__(f"PLAYBOOK_UNRESOLVED: {name}")
        self.name = name


def default_playbook_dir():
    return _HERE.parent / "templates" / "analysis-playbooks"


def _slug(value):
    return re.sub(r"[^a-z0-9]+", "-", str(value).casefold()).strip("-")


def resolve_playbook(root, name, *, project_context=None):
    """R7 resolution: a project playbook of the same name wins over a read-only default."""
    production = _module("project_production")
    registry = _module("project_registry")
    operation = _module("project_operation")
    context = registry.context_for_operation(root, project_context=project_context)
    operation.require_project_capability(context, "read")

    wanted = {_slug(name), _slug(f"pb-{name}")}
    for playbook in production.list_playbooks(root, project_context=context):
        if _slug(playbook["id"]) in wanted or _slug(playbook.get("title", "")) in wanted:
            return {
                "source": "project",
                "reason": "project playbook overrides the default",
                "playbook": playbook,
            }

    path = default_playbook_dir() / f"{name}.md"
    if path.is_file():
        return {
            "source": "default",
            "reason": "no project playbook of this name; using the read-only default",
            "playbook": production.parse_playbook(_HERE.parent, path),
        }
    raise PlaybookUnresolved(name)



def _section_lines(section):
    """Bullets when a section uses them, otherwise its nonempty lines."""
    lines = [line.strip() for line in str(section).splitlines() if line.strip()]
    bullets = [line.lstrip("-").strip() for line in lines if line.startswith("-")]
    return bullets or lines


def prefill_run(playbook):
    """R7 prefill. Returns a starting point, never a complete run."""
    sections = playbook.get("sections", {})
    match = CLAIM_LINE_RE.search(sections.get("Reusable Patterns", ""))
    claim = match.group(1) if match and match.group(1) in CLAIM_CLASSES else None
    active = [item for item in playbook.get("required_checks", []) if not item["retired"]]
    return {
        "playbook_ref": {
            "playbook_id": playbook["id"],
            "version": str(playbook["version"]),
            "deliverable_type": playbook["deliverable_type"],
        },
        "claim_class": claim,
        "required_code_checks": list(CODE_CHECKS.get(claim, ())),
        "playbook_check_ids": [item["id"] for item in active],
        "auto_check_ids": [item["id"] for item in active if item["kind"] == "auto"],
        "caveats": _section_lines(sections.get("Do Not Repeat", "")),
        "structure_ref": sections.get("Approved Structures", ""),
        "process_ref": playbook.get("process_ref"),
    }


def _match_reasons(entry, tokens):
    haystacks = {
        "title": entry.get("title", ""),
        "decision_question": entry.get("decision_question", ""),
        "issue_id": entry.get("issue_id", ""),
        "conclusion": entry.get("conclusion", ""),
    }
    playbook = entry.get("playbook_ref") or {}
    haystacks["playbook_id"] = playbook.get("playbook_id", "")
    reasons = []
    for field, value in haystacks.items():
        text = str(value).casefold()
        if all(token in text for token in tokens):
            reasons.append(field)
    return reasons


def _read_runs_text(root, relative, *, view, ref, runner):
    if view == "working":
        path = Path(root) / relative
        return (path.read_text(encoding="utf-8") if path.is_file() else None), None
    if runner is None:
        raise ValueError("RUNS_GIT_RUNNER_REQUIRED")
    resolved = runner(["git", "rev-parse", f"{ref}^{{commit}}"], Path(root))
    if resolved.returncode != 0:
        raise ValueError("GIT_SNAPSHOT_UNAVAILABLE")
    oid = resolved.stdout.strip()
    shown = runner(["git", "show", f"{oid}:{relative}"], Path(root))
    if shown.returncode != 0:
        return None, oid
    return shown.stdout, oid


def read_analysis_runs(
    root,
    *,
    project_context=None,
    view="working",
    ref="HEAD",
    query="",
    run_ids=(),
    issue_id=None,
    limit=DEFAULT_LIMIT,
    runner=None,
    today=None,
):
    """R8 read facade. One resolved context, explicit bounds, no source bodies."""
    if view not in ("working", "shared"):
        raise ValueError("RUNS_VIEW_UNSUPPORTED")
    if not isinstance(limit, int) or limit < 1:
        raise ValueError("RUNS_LIMIT_INVALID")

    registry = _module("project_registry")
    operation = _module("project_operation")
    context = registry.context_for_operation(root, project_context=project_context)
    operation.require_project_capability(context, "read")

    relative = context["relative_paths"]["workspace"] + "/analysis-runs.md"
    envelope = {
        "schema": READ_SCHEMA,
        "project_id": context.get("project_id") or None,
        "identity_status": context.get("status") or "unbound",
        "view": view,
        "snapshot_commit": None,
        "runs_path": relative,
        "entries": [],
        "diagnostics": [],
        "total": 0,
        "returned": 0,
        "omitted": 0,
        "truncated": False,
        "read_trace": [{"path": relative, "operation": "read"}],
    }

    text, oid = _read_runs_text(root, relative, view=view, ref=ref, runner=runner)
    envelope["snapshot_commit"] = oid
    if text is None:
        envelope["diagnostics"].append(diagnostic("RUNS_NOT_INITIALIZED", "runs_path"))
        return envelope

    parsed = parse_analysis_runs(text)
    envelope["diagnostics"].extend(parsed["diagnostics"])

    tokens = [token for token in str(query or "").casefold().split() if token]
    wanted = {str(value) for value in run_ids}
    matched = []
    for entry in parsed["entries"]:
        if wanted and entry["id"] not in wanted:
            continue
        if issue_id and entry.get("issue_id") != issue_id:
            continue
        reasons = _match_reasons(entry, tokens) if tokens else ["all"]
        if not reasons:
            continue
        matched.append((entry, reasons))

    for requested in sorted(wanted - {entry["id"] for entry, _ in matched}):
        envelope["diagnostics"].append(diagnostic("RUN_ID_UNKNOWN", "run_ids", requested))

    envelope["total"] = len(matched)
    for entry, reasons in matched[:limit]:
        item = dict(entry)
        item["run_anchor"] = f"{relative}#{entry['id']}"
        item["match_reasons"] = reasons
        item["diagnostics"] = validate_run(entry, today=today)
        envelope["entries"].append(item)
    envelope["returned"] = len(envelope["entries"])
    envelope["omitted"] = envelope["total"] - envelope["returned"]
    envelope["truncated"] = envelope["omitted"] > 0
    return envelope


SOURCE_FIELDS = (
    "project_id",
    "artifact_id",
    "snapshot_commit",
    "locator",
    "recorded_state",
    "tab_or_range",
    "extracted_at",
    "content_hash",
)


def _run_by_id(root, run_id, *, project_context, runner):
    envelope = read_analysis_runs(
        root, project_context=project_context, run_ids=[run_id], runner=runner
    )
    for entry in envelope["entries"]:
        if entry["id"] == run_id:
            return entry, envelope
    return None, envelope


def resolve_run_sources(root, run_id, *, project_context=None, runner=None):
    """R8 source binding. Reopens each pinned source through the delivered 090 facades.

    This module implements no registry parsing. A mismatch, an unknown id or a
    superseded input is reported; a similarly titled record is never substituted
    and the snapshot is never switched.
    """
    registry_module = _module("project_artifact_registry")
    registry = _module("project_registry")
    context = registry.context_for_operation(root, project_context=project_context)

    entry, envelope = _run_by_id(root, run_id, project_context=context, runner=runner)
    result = {
        "run_id": run_id,
        "project_id": envelope["project_id"],
        "sources": [],
        "diagnostics": list(envelope["diagnostics"]),
        "read_trace": list(envelope["read_trace"]),
    }
    if entry is None:
        result["diagnostics"].append(diagnostic("RUN_ID_UNKNOWN", "run_ids", run_id))
        return result

    by_commit = {}
    for source in entry.get("sources", []):
        if not _mapping(source, SOURCE_FIELDS):
            result["diagnostics"].append(diagnostic("SOURCE_RECORD_INVALID", "sources", run_id))
            continue
        project_id = envelope["project_id"]
        if project_id and source["project_id"] and source["project_id"] != project_id:
            result["diagnostics"].append(
                diagnostic("SOURCE_PROJECT_MISMATCH", source["artifact_id"], run_id)
            )
            continue
        if not project_id and source["project_id"]:
            # Unbound identity cannot verify a cross-project pin; say so rather than assume.
            result["diagnostics"].append(
                diagnostic("SOURCE_IDENTITY_UNVERIFIED", source["artifact_id"], run_id, "info")
            )
        by_commit.setdefault(source["snapshot_commit"], []).append(source)

    for commit, pinned in sorted(by_commit.items()):
        ids = [source["artifact_id"] for source in pinned]
        try:
            found = registry_module.read_artifact_registry(
                root,
                project_context=context,
                view="shared",
                ref=commit,
                artifact_ids=tuple(ids),
                runner=runner,
            )
        except Exception:  # surfaced, never swallowed
            result["diagnostics"].append(diagnostic("GIT_SNAPSHOT_UNAVAILABLE", "snapshot_commit", run_id))
            continue
        result["diagnostics"].extend(found.get("diagnostics", []))
        known = {item.get("id"): item for item in found.get("entries", [])}
        for source in pinned:
            item = known.get(source["artifact_id"])
            if item is None:
                result["diagnostics"].append(
                    diagnostic("SOURCE_ARTIFACT_UNKNOWN", source["artifact_id"], run_id)
                )
                continue
            if item.get("state") == "superseded":
                result["diagnostics"].append(
                    diagnostic("SOURCE_SUPERSEDED", source["artifact_id"], run_id, "warning")
                )
            result["sources"].append(
                {
                    "artifact_id": source["artifact_id"],
                    "snapshot_commit": commit,
                    "locator": source["locator"],
                    "recorded_state": source["recorded_state"],
                    "current_state": item.get("state"),
                    "tab_or_range": source["tab_or_range"],
                    "extracted_at": source["extracted_at"],
                }
            )
    return result


def check_playbook_binding(root, entry, *, project_context=None):
    """R3: a run's output must not claim a playbook its production record disowns."""
    findings = []
    reference = entry.get("production_record_ref")
    playbook = entry.get("playbook_ref") or {}
    if not reference or not playbook.get("playbook_id"):
        return findings
    production = _module("project_production")
    path = Path(root) / reference
    if not path.is_file():
        findings.append(diagnostic("PRODUCTION_RECORD_MISSING", "production_record_ref", entry.get("id", "")))
        return findings
    try:
        record = production.parse_production_record(root, path)
    except ValueError:
        findings.append(diagnostic("PRODUCTION_RECORD_INVALID", "production_record_ref", entry.get("id", "")))
        return findings
    named = [str(value) for value in record.get("playbook_refs", [])]
    if named and playbook["playbook_id"] not in named:
        findings.append(diagnostic("PLAYBOOK_MISMATCH", "playbook_ref", entry.get("id", "")))
    return findings
