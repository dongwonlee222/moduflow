#!/usr/bin/env python3
"""Pure domain model for verified ModuFlow review intake packets."""

import copy
import hashlib
import json
import re
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit


REVIEW_SCHEMA = "moduflow.review-intake.v1"
SOURCE_KINDS = {"human", "ai", "tool"}
RETENTION_MODES = {"copy", "reference", "hash_only"}
VERIFICATION_STATES = {"unverified", "confirmed", "contradicted", "inconclusive"}
FINAL_DISPOSITIONS = {"accept", "partial_accept", "defer", "reject"}
LANES = {"security", "pre_release", "post_release_refactor"}
SEVERITIES = {"low", "medium", "high", "critical"}
REVIEW_ID_RE = re.compile(r"[0-9A-Za-z][0-9A-Za-z._-]{2,127}")
SHA256_RE = re.compile(r"[0-9a-f]{64}")
COMMIT_RE = re.compile(r"[0-9a-f]{40}")
SENSITIVE_PATH_PARTS = (
    "auth",
    "permission",
    "payment",
    "billing",
    "secret",
    "upload",
    "deploy",
    ".github/workflows",
)


class ReviewIntakeError(ValueError):
    """A review-intake validation error with a stable reason code."""

    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


def _sha256_bytes(value):
    return hashlib.sha256(value).hexdigest()


def sha256_file(path):
    return _sha256_bytes(Path(path).read_bytes())


def _safe_locator(value):
    text = str(value or "")
    parsed = urlsplit(text)
    if parsed.scheme.lower() in {"http", "https"}:
        host = (parsed.hostname or "").lower()
        port = f":{parsed.port}" if parsed.port else ""
        return urlunsplit((parsed.scheme.lower(), host + port, parsed.path, "", ""))
    return text


def build_source_record(
    kind,
    provider,
    identity,
    received_at,
    retention,
    locator=None,
    copied_text=None,
    source_hash=None,
    model=None,
    version=None,
    policy_version=None,
):
    if kind not in SOURCE_KINDS:
        raise ReviewIntakeError(
            "source_kind_invalid", f"unsupported source kind: {kind}"
        )
    if retention not in RETENTION_MODES:
        raise ReviewIntakeError(
            "retention_invalid", f"unsupported retention: {retention}"
        )

    record = {
        "kind": kind,
        "provider": str(provider or "unknown"),
        "identity": str(identity or "unknown"),
        "received_at": str(received_at),
        "retention": retention,
    }
    optional = {
        "model": model,
        "version": version,
        "policy_version": policy_version,
    }
    for key, value in optional.items():
        if value:
            record[key] = str(value)

    if retention == "reference":
        path = Path(str(locator or ""))
        if path.is_file():
            record.update(
                locator=_safe_locator(path.resolve()),
                sha256=sha256_file(path),
            )
        elif re.match(r"^https?://", str(locator or "")) and SHA256_RE.fullmatch(
            str(source_hash or "")
        ):
            record.update(locator=_safe_locator(locator), sha256=source_hash)
        else:
            raise ReviewIntakeError(
                "source_unavailable",
                "reference requires a readable local file or URL plus SHA-256",
            )
    elif retention == "copy":
        if copied_text is None:
            raise ReviewIntakeError(
                "source_copy_missing", "copy retention requires copied text"
            )
        text = str(copied_text)
        record.update(
            copied_text=text,
            sha256=_sha256_bytes(text.encode("utf-8")),
        )
    else:
        digest = str(source_hash or "")
        if not SHA256_RE.fullmatch(digest):
            raise ReviewIntakeError(
                "source_hash_invalid",
                "hash_only requires a lowercase SHA-256",
            )
        record["sha256"] = digest
        if locator:
            record["description"] = _safe_locator(locator)

    return record


def _normalized_location(location):
    if not isinstance(location, dict):
        raise ReviewIntakeError(
            "finding_location_invalid", "finding locations must be objects"
        )
    path = str(location.get("path") or "").replace("\\", "/")
    while path.startswith("./"):
        path = path[2:]
    if not path or ".." in Path(path).parts or path.startswith("/"):
        raise ReviewIntakeError(
            "finding_path_invalid", "finding path must remain inside the project"
        )
    line = location.get("line")
    if line is not None and (not isinstance(line, int) or line < 1):
        raise ReviewIntakeError(
            "finding_line_invalid", "finding line must be a positive integer"
        )
    return {
        "path": path,
        "line": line,
        "anchor": str(location.get("anchor") or ""),
    }


def _fingerprint(raw, source, target, locations):
    stable = {
        "provider": source.get("provider", "unknown"),
        "rule_id": raw.get("rule_id") or "",
        "provider_fingerprint": raw.get("provider_fingerprint") or "",
        "repository": str(target["repository"]).lower(),
        "locations": [
            {"path": item["path"], "anchor": item["anchor"]}
            for item in locations
        ],
        "observation": re.sub(
            r"\s+",
            " ",
            str(raw.get("observation") or "").strip().lower(),
        ),
    }
    encoded = json.dumps(
        stable, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return "sha256:" + _sha256_bytes(encoded)


def normalize_finding(raw, index, source, target):
    if not isinstance(raw, dict):
        raise ReviewIntakeError("finding_invalid", "each finding must be an object")
    locations = [
        _normalized_location(item) for item in raw.get("locations", [])
    ]
    observation = str(raw.get("observation") or "").strip()
    if not observation:
        raise ReviewIntakeError(
            "observation_missing", "each finding requires an observation"
        )
    severity = str(raw.get("severity") or "medium").lower()
    if severity not in SEVERITIES:
        raise ReviewIntakeError(
            "severity_invalid", f"unsupported severity: {severity}"
        )

    source_author = raw.get("source_author") or {
        "kind": source["kind"],
        "identity": source["identity"],
    }
    router = raw.get("router") or {
        "classification": "unclassified",
        "confidence": "low",
        "proposed_lane": None,
        "reason_codes": [],
        "actor": None,
    }
    no_risk_claim = bool(raw.get("no_risk_claim"))
    return {
        "id": f"F-{index:03d}",
        "fingerprint": _fingerprint(raw, source, target, locations),
        "rule_id": raw.get("rule_id"),
        "source_author": copy.deepcopy(source_author),
        "observation": observation,
        "recommendation": str(raw.get("recommendation") or "").strip(),
        "root_cause_hypothesis": str(
            raw.get("root_cause_hypothesis") or ""
        ).strip(),
        "reviewer_confidence": str(
            raw.get("reviewer_confidence") or "unknown"
        ),
        "locations": locations,
        "provider_evidence": copy.deepcopy(raw.get("provider_evidence") or {}),
        "verification": {
            "state": "unverified",
            "verifier": None,
            "files_checked": [],
            "reproduction": [],
            "tests": [],
            "architecture": [],
            "import_boundaries": [],
            "contradictions": [],
            "verified_at": None,
        },
        "risk": {
            "severity": severity,
            "release_impact": raw.get("release_impact", "unknown"),
            "no_risk_claim": no_risk_claim,
            "no_risk_state": "unverified" if no_risk_claim else "not_claimed",
        },
        "router": copy.deepcopy(router),
        "disposition": {
            "state": "pending_verification",
            "rationale": "",
            "decided_by": None,
            "decided_at": None,
            "human_approved": False,
        },
        "decision_history": [],
        "route": {
            "lane": None,
            "CognitiveDemand": None,
            "candidate_ids": [],
            "existing_issue_ids": [],
        },
    }


def new_packet(review_id, source, target, trigger, adapter_run, raw_findings):
    packet = {
        "schema": REVIEW_SCHEMA,
        "review_id": str(review_id),
        "source": copy.deepcopy(source),
        "target": copy.deepcopy(target),
        "trigger": copy.deepcopy(trigger),
        "adapter_run": copy.deepcopy(adapter_run),
        "findings": [
            normalize_finding(raw, index, source, target)
            for index, raw in enumerate(raw_findings, 1)
        ],
        "trace": {
            "finding_to_candidates": {},
            "candidate_to_findings": {},
        },
        "updated_at": date.today().isoformat(),
    }
    errors = validate_packet(packet)
    if errors:
        raise ReviewIntakeError(errors[0]["code"], errors[0]["message"])
    return packet


def validate_packet(packet, final=False):
    errors = []

    def add(code, path, message):
        errors.append({"code": code, "path": path, "message": message})

    if not isinstance(packet, dict):
        add("packet_invalid", "$", "packet must be an object")
        return errors
    if packet.get("schema") != REVIEW_SCHEMA:
        add("schema_invalid", "schema", f"expected {REVIEW_SCHEMA}")
    if not REVIEW_ID_RE.fullmatch(str(packet.get("review_id") or "")):
        add(
            "review_id_invalid",
            "review_id",
            "review_id must be a safe 3-128 character artifact identifier",
        )

    source = packet.get("source") or {}
    if source.get("kind") not in SOURCE_KINDS:
        add(
            "source_kind_invalid",
            "source.kind",
            "source kind must be human, ai, or tool",
        )
    if source.get("retention") not in RETENTION_MODES:
        add(
            "retention_invalid",
            "source.retention",
            "source retention must be copy, reference, or hash_only",
        )
    if not SHA256_RE.fullmatch(str(source.get("sha256") or "")):
        add(
            "source_hash_invalid",
            "source.sha256",
            "source requires a lowercase SHA-256",
        )
    if source.get("retention") == "reference" and not source.get("locator"):
        add(
            "source_reference_missing",
            "source.locator",
            "reference retention requires a locator",
        )

    target = packet.get("target") or {}
    if not target.get("repository") or not COMMIT_RE.fullmatch(
        str(target.get("commit") or "")
    ):
        add(
            "target_unverifiable",
            "target",
            "repository and full commit SHA are required",
        )

    finding_ids = set()
    for index, finding in enumerate(packet.get("findings") or []):
        path = f"findings[{index}]"
        finding_id = finding.get("id")
        if not finding_id or finding_id in finding_ids:
            add("finding_id_invalid", path + ".id", "finding IDs must be unique")
        finding_ids.add(finding_id)
        if not str(finding.get("fingerprint") or "").startswith("sha256:"):
            add(
                "finding_fingerprint_invalid",
                path + ".fingerprint",
                "finding requires a SHA-256 fingerprint",
            )
        if not finding.get("observation"):
            add(
                "observation_missing",
                path + ".observation",
                "finding requires an observation",
            )
        if finding.get("verification", {}).get("state") not in VERIFICATION_STATES:
            add(
                "verification_state_invalid",
                path + ".verification.state",
                "unsupported verification state",
            )
        disposition = finding.get("disposition", {}).get("state")
        if final and disposition not in FINAL_DISPOSITIONS:
            add(
                "disposition_pending",
                path + ".disposition.state",
                "final packets require a disposition",
            )
    return errors


def evaluate_policy(finding):
    """Return deterministic routing and approval requirements for a finding."""
    paths = [
        item["path"].lower() for item in finding.get("locations", [])
    ]
    severity = finding.get("risk", {}).get("severity", "medium")
    sensitive = any(
        any(part in path for part in SENSITIVE_PATH_PARTS) for path in paths
    )
    security_signal = (
        sensitive
        or finding.get("router", {}).get("classification") == "security"
        or finding.get("provider_evidence", {}).get("kind") == "security"
    )
    reasons = []
    if sensitive:
        reasons.append("sensitive_path")
    if severity in {"high", "critical"}:
        reasons.append("elevated_severity")

    verification = finding.get("verification") or {}
    if finding.get("risk", {}).get("no_risk_claim") and not (
        verification.get("tests") and verification.get("import_boundaries")
    ):
        reasons.append("no_risk_evidence_missing")

    if security_signal:
        lane = "security"
    elif (
        severity in {"high", "critical"}
        or finding.get("risk", {}).get("release_impact") == "blocking"
    ):
        lane = "pre_release"
    else:
        lane = "post_release_refactor"

    if lane == "security" or verification.get("architecture"):
        cognitive_demand = "deep"
    elif lane == "pre_release":
        cognitive_demand = "balanced"
    else:
        cognitive_demand = "fast"

    router = finding.get("router") or {}
    return {
        "lane": lane,
        "CognitiveDemand": cognitive_demand,
        "requires_verifier": (
            severity in {"medium", "high", "critical"}
            or router.get("confidence") != "high"
        ),
        "requires_human_for_reject": (
            severity in {"high", "critical"} or lane == "security"
        ),
        "reason_codes": reasons,
    }


def _provenance_key(actor):
    actor = actor or {}
    return (
        actor.get("kind"),
        actor.get("identity"),
        actor.get("run_id"),
    )


def _normalized_verification(decision):
    verification = copy.deepcopy(decision.get("verification") or {})
    state = verification.get("state")
    if state not in VERIFICATION_STATES:
        raise ReviewIntakeError(
            "verification_state_invalid",
            "decision requires a valid verification state",
        )
    verification.setdefault("verifier", None)
    for key in (
        "files_checked",
        "reproduction",
        "tests",
        "architecture",
        "import_boundaries",
        "contradictions",
    ):
        value = verification.setdefault(key, [])
        if not isinstance(value, list):
            raise ReviewIntakeError(
                "verification_evidence_invalid",
                f"verification {key} must be a list",
            )
    verification.setdefault("verified_at", date.today().isoformat())
    return verification


def apply_decision(packet, decision):
    """Apply one evidence-backed disposition and return a new packet."""
    updated = copy.deepcopy(packet)
    if decision.get("target_commit") != updated.get("target", {}).get("commit"):
        raise ReviewIntakeError(
            "target_commit_mismatch",
            "decision target commit differs from the reviewed commit",
        )

    finding = next(
        (
            item
            for item in updated.get("findings", [])
            if item.get("id") == decision.get("finding_id")
        ),
        None,
    )
    if finding is None:
        raise ReviewIntakeError(
            "finding_not_found", "decision finding does not exist"
        )

    verification = _normalized_verification(decision)
    disposition = decision.get("disposition")
    if disposition not in FINAL_DISPOSITIONS:
        raise ReviewIntakeError(
            "disposition_invalid", "decision requires a final disposition"
        )
    rationale = str(decision.get("rationale") or "").strip()
    if not rationale:
        raise ReviewIntakeError(
            "disposition_rationale_missing",
            "every disposition requires rationale",
        )
    state = verification["state"]
    if disposition == "accept" and state != "confirmed":
        raise ReviewIntakeError(
            "accept_requires_evidence", "accept requires confirmed evidence"
        )
    if disposition == "partial_accept" and state not in {
        "confirmed",
        "inconclusive",
    }:
        raise ReviewIntakeError(
            "partial_accept_requires_evidence",
            "partial accept requires confirmed or inconclusive evidence",
        )

    finding["verification"] = verification
    policy = evaluate_policy(finding)
    verifier = verification.get("verifier") or {}
    if policy["requires_verifier"]:
        if verifier.get("role") != "verifier" or not verifier.get("identity"):
            raise ReviewIntakeError(
                "verifier_missing",
                "policy requires explicit verifier provenance",
            )
        blocked_keys = {
            _provenance_key(finding.get("source_author")),
            _provenance_key(finding.get("router", {}).get("actor")),
        }
        blocked_keys = {key for key in blocked_keys if any(key)}
        if _provenance_key(verifier) in blocked_keys:
            raise ReviewIntakeError(
                "verifier_not_independent",
                "verifier must differ from source reviewer and Router run",
            )

    actor = copy.deepcopy(
        decision.get("actor") or {"kind": "unknown", "identity": "unknown"}
    )
    human_approved = bool(decision.get("human_approved"))
    if (
        disposition == "reject"
        and policy["requires_human_for_reject"]
        and not human_approved
    ):
        raise ReviewIntakeError(
            "high_risk_reject_requires_human",
            "high-risk rejection requires human approval",
        )

    if finding["risk"].get("no_risk_claim"):
        finding["risk"]["no_risk_state"] = (
            "verified"
            if verification["tests"] and verification["import_boundaries"]
            else "unverified"
        )

    event = {
        "state": disposition,
        "rationale": rationale,
        "decided_by": actor,
        "decided_at": date.today().isoformat(),
        "human_approved": human_approved,
    }
    finding.setdefault("decision_history", []).append(copy.deepcopy(event))
    finding["disposition"] = event
    if disposition in {"accept", "partial_accept"}:
        finding["route"].update(
            lane=policy["lane"],
            CognitiveDemand=policy["CognitiveDemand"],
        )
    else:
        finding["route"].update(lane=None, CognitiveDemand=None)
    finding["policy"] = policy
    updated["updated_at"] = date.today().isoformat()
    return updated
