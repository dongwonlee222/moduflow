#!/usr/bin/env python3
"""Source adapters and CLI boundary for verified ModuFlow review intake."""

import copy

from scripts import review_intake as ri


ADAPTER_ORDER = [
    "manual-review-document",
    "github-review",
    "security-review",
    "superpowers-review",
    "spec-kit",
]
SENSITIVE_PARTS = {
    "auth",
    "permission",
    "payment",
    "billing",
    "secret",
    "upload",
    "deploy",
    ".github/workflows",
}
SARIF_LEVEL_TO_SEVERITY = {
    "error": "high",
    "warning": "medium",
    "note": "low",
    "none": "low",
}


def select_adapters(
    event,
    adapter,
    changed_paths,
    requires_plan=False,
    security_requested=False,
):
    paths = [str(path).lower() for path in changed_paths]
    sensitive = any(
        any(part in path for part in SENSITIVE_PARTS) for path in paths
    )
    if event == "routine" and not any(
        (adapter, sensitive, requires_plan, security_requested)
    ):
        return {
            "invoked": [],
            "skipped": ADAPTER_ORDER.copy(),
            "reason_codes": ["l0_routine"],
        }

    invoked = set()
    reasons = []
    if adapter == "manual":
        invoked.update({"manual-review-document", "superpowers-review"})
        reasons.append("manual_source")
    elif adapter == "github":
        invoked.update({"github-review", "superpowers-review"})
        reasons.append("pr_threads_present")
    elif adapter in {"sarif", "codeql"}:
        invoked.update({"security-review", "superpowers-review"})
        reasons.append("security_payload")

    if sensitive:
        invoked.update({"security-review", "superpowers-review"})
        reasons.append("sensitive_path")
    if security_requested:
        invoked.update({"security-review", "superpowers-review"})
        reasons.append("router_security_request")
    if requires_plan:
        invoked.add("spec-kit")
        reasons.append("planning_required")

    return {
        "invoked": [name for name in ADAPTER_ORDER if name in invoked],
        "skipped": [name for name in ADAPTER_ORDER if name not in invoked],
        "reason_codes": reasons,
    }


def adapt_manual_findings(payload):
    findings = payload.get("findings") if isinstance(payload, dict) else payload
    if not isinstance(findings, list):
        raise ri.ReviewIntakeError(
            "manual_findings_invalid",
            "manual adapter requires a findings list",
        )
    return copy.deepcopy(findings)


def _thread_comments(thread):
    comment_field = thread.get("comments") or []
    if isinstance(comment_field, dict):
        return comment_field.get("nodes") or []
    return comment_field


def adapt_github_threads(payload):
    findings = []
    for thread in payload.get("threads", []):
        if thread.get("isResolved") or thread.get("isOutdated"):
            continue
        comments = _thread_comments(thread)
        if not comments:
            continue
        comment = comments[-1]
        observation = str(comment.get("body") or "").strip()
        if not observation:
            continue
        author = comment.get("author") or {}
        login = author.get("login", "unknown")
        author_kind = (
            "ai"
            if author.get("type") == "Bot" or login.endswith("[bot]")
            else "human"
        )
        findings.append(
            {
                "rule_id": f"github-thread:{thread.get('id')}",
                "observation": observation,
                "recommendation": "",
                "root_cause_hypothesis": "",
                "locations": [
                    {
                        "path": thread.get("path"),
                        "line": thread.get("line"),
                        "anchor": thread.get("diffSide") or "",
                    }
                ],
                "source_author": {
                    "kind": author_kind,
                    "identity": login,
                },
                "provider_fingerprint": f"github-thread:{thread.get('id')}",
                "provider_evidence": {
                    "kind": "review",
                    "format": "github-thread",
                    "id": thread.get("id"),
                    "resolved": False,
                    "outdated": False,
                },
            }
        )
    return findings


def _sarif_location(result):
    locations = result.get("locations") or []
    physical = (locations[0].get("physicalLocation") or {}) if locations else {}
    artifact = physical.get("artifactLocation") or {}
    region = physical.get("region") or {}
    return {
        "path": artifact.get("uri"),
        "line": region.get("startLine"),
        "anchor": result.get("ruleId") or "",
    }


def _sarif_severity(result):
    properties = result.get("properties") or {}
    raw = str(
        properties.get("severity")
        or properties.get("security-severity")
        or result.get("level")
        or "error"
    ).lower()
    if raw in ri.SEVERITIES:
        return raw
    return SARIF_LEVEL_TO_SEVERITY.get(raw, "high")


def adapt_sarif(payload):
    findings = []
    for run in payload.get("runs", []):
        driver = (run.get("tool") or {}).get("driver") or {}
        for result in run.get("results", []):
            partials = result.get("partialFingerprints") or {}
            findings.append(
                {
                    "rule_id": result.get("ruleId"),
                    "observation": (result.get("message") or {}).get("text", ""),
                    "recommendation": "",
                    "root_cause_hypothesis": "",
                    "locations": [_sarif_location(result)],
                    "severity": _sarif_severity(result),
                    "source_author": {
                        "kind": "tool",
                        "identity": driver.get("name", "unknown"),
                        "version": driver.get("version"),
                    },
                    "provider_fingerprint": partials.get(
                        "primaryLocationLineHash"
                    )
                    or next(iter(partials.values()), None),
                    "provider_evidence": {
                        "kind": "security",
                        "format": "sarif",
                        "tool": driver.get("name"),
                        "version": driver.get("version"),
                    },
                }
            )
    return findings


def adapt_codeql_alerts(payload):
    alerts = payload.get("alerts") if isinstance(payload, dict) else payload
    if not isinstance(alerts, list):
        raise ri.ReviewIntakeError(
            "codeql_alerts_invalid",
            "CodeQL adapter requires an alerts list",
        )
    findings = []
    for alert in alerts:
        rule = alert.get("rule") or {}
        instance = alert.get("most_recent_instance") or {}
        location = instance.get("location") or {}
        raw_severity = str(
            rule.get("security_severity_level")
            or rule.get("severity")
            or "high"
        ).lower()
        severity = (
            raw_severity
            if raw_severity in ri.SEVERITIES
            else SARIF_LEVEL_TO_SEVERITY.get(raw_severity, "high")
        )
        number = alert.get("number")
        tool = alert.get("tool") or {}
        findings.append(
            {
                "rule_id": rule.get("id"),
                "observation": rule.get("description")
                or rule.get("name")
                or "Code scanning alert",
                "recommendation": "",
                "root_cause_hypothesis": "",
                "locations": [
                    {
                        "path": location.get("path"),
                        "line": location.get("start_line"),
                        "anchor": rule.get("id") or "",
                    }
                ],
                "severity": severity,
                "source_author": {
                    "kind": "tool",
                    "identity": tool.get("name", "CodeQL"),
                    "version": tool.get("version"),
                },
                "provider_fingerprint": f"codeql-alert:{number}",
                "provider_evidence": {
                    "kind": "security",
                    "format": "codeql-alert",
                    "number": number,
                    "state": alert.get("state"),
                    "dismissed_reason": alert.get("dismissed_reason"),
                    "dismissed_comment": alert.get("dismissed_comment"),
                    "dismissed_by": (alert.get("dismissed_by") or {}).get(
                        "login"
                    ),
                    "dismissed_at": alert.get("dismissed_at"),
                },
            }
        )
    return findings
