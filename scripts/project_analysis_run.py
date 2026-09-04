"""Append-only analysis run records for Issue 091.

One parser for `moduflow.analysis-runs.v1`. Mirrors the structure of
`project_artifact_registry` so the two canonical Markdown+JSON formats stay
reviewable side by side. No I/O beyond the caller's text.
"""

import json
import re

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
