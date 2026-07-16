#!/usr/bin/env python3
"""Source adapters and CLI boundary for verified ModuFlow review intake."""

import argparse
import copy
import json
import sys
from datetime import date
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

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


def _load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _public_packet(packet):
    visible = copy.deepcopy(packet)
    source = visible.get("source") or {}
    if "copied_text" in source:
        source["copied_text"] = "<retained-in-packet-redacted-from-output>"
    return visible


def render_summary_ko(packet):
    source = packet["source"]
    target = packet["target"]
    lines = [
        f"# 코드리뷰 접수: {packet['review_id']}",
        "",
        "## 출처",
        "",
        f"- 유형: `{source['kind']}`",
        f"- 제공자: `{source['provider']}`",
        f"- 작성자/도구: `{source.get('identity', 'unknown')}`",
        f"- 보관: `{source['retention']}`",
        f"- 대상: `{target['repository']}@{target['commit'][:12]}`",
        "",
        "## 어댑터 실행",
        "",
        "- 호출: "
        + (", ".join(packet.get("adapter_run", {}).get("invoked", [])) or "없음"),
        "- 생략: "
        + (", ".join(packet.get("adapter_run", {}).get("skipped", [])) or "없음"),
        "",
        "## Finding",
        "",
    ]
    for finding in packet["findings"]:
        provider = finding.get("provider_evidence") or {}
        lines.extend(
            [
                f"### {finding['id']} — {finding['risk']['severity']}",
                "",
                f"- 관찰: {finding['observation']}",
                f"- 권장: {finding['recommendation'] or '없음'}",
                f"- 원인 가설: {finding['root_cause_hypothesis'] or '없음'}",
                f"- 리뷰어 확신도: `{finding['reviewer_confidence']}`",
                f"- 검증 상태: `{finding['verification']['state']}`",
                f"- 판정: `{finding['disposition']['state']}`",
                f"- 경로: `{finding['route']['lane'] or '미정'}`",
                f"- Provider 상태: `{provider.get('state', '해당 없음')}`",
                f"- Provider dismiss 사유: `{provider.get('dismissed_reason', '해당 없음')}`",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def render_candidate_queue(candidates):
    lines = ["# Review Candidates", ""]
    for item in candidates:
        overlap = (
            ", ".join(
                hint["issue_id"] for hint in item.get("overlap_hints", [])
            )
            or "없음"
        )
        reasons = ", ".join(item.get("routing_reason_codes", [])) or "없음"
        lines.extend(
            [
                f"## {item['id']} — {item['title']}",
                "",
                f"- State: `{item['state']}`",
                f"- Lane: `{item['lane']}`",
                f"- Priority: `{item['priority']}`",
                f"- CognitiveDemand: `{item['CognitiveDemand']}`",
                f"- Findings: {', '.join(item['finding_ids'])}",
                f"- Routing reasons: {reasons}",
                f"- Overlap hints: {overlap}",
                f"- Next: `{item['next_command']}`",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def _write_text_atomic(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)


def _packet_files(root):
    return sorted(
        (Path(root).resolve() / "workspace" / "reviews").glob("*.json")
    )


def _existing_candidates(root, exclude_review_id):
    candidates = []
    for path in _packet_files(root):
        try:
            packet = _load_json(path)
        except (OSError, json.JSONDecodeError):
            continue
        if packet.get("review_id") != exclude_review_id:
            candidates.extend(packet.get("candidates") or [])
    return candidates


def _add_overlap_hints(root, candidates):
    from scripts.project_intake import find_related_issues

    enriched = copy.deepcopy(candidates)
    for candidate in enriched:
        candidate["overlap_hints"] = find_related_issues(
            root, candidate["title"] + "\n" + candidate["problem"]
        )[:3]
    return enriched


def write_review_artifacts(root, packet):
    root = Path(root).resolve()
    reviews = root / "workspace" / "reviews"
    existing = _existing_candidates(root, packet["review_id"])
    candidate_result = ri.build_candidates(
        packet, existing_candidates=existing
    )
    stored = copy.deepcopy(packet)
    stored["candidates"] = _add_overlap_hints(
        root, candidate_result["candidates"]
    )
    stored["trace"] = candidate_result["trace"]
    for finding in stored["findings"]:
        finding["route"]["candidate_ids"] = stored["trace"][
            "finding_to_candidates"
        ].get(finding["id"], [])

    errors = ri.validate_packet(stored)
    if errors:
        raise ri.ReviewIntakeError(errors[0]["code"], errors[0]["message"])

    packet_path = reviews / f"{stored['review_id']}.json"
    summary_path = reviews / f"{stored['review_id']}.md"
    candidate_path = root / "workspace" / "review-candidates.md"
    _write_text_atomic(
        packet_path,
        json.dumps(stored, ensure_ascii=False, indent=2) + "\n",
    )
    _write_text_atomic(summary_path, render_summary_ko(stored))
    all_candidates = _existing_candidates(root, stored["review_id"]) + stored[
        "candidates"
    ]
    _write_text_atomic(candidate_path, render_candidate_queue(all_candidates))
    return {
        "packet": packet_path,
        "summary": summary_path,
        "candidates": candidate_path,
    }


def _required_new_args(args):
    required = {
        "review_id": args.review_id,
        "adapter": args.adapter,
        "source": args.source,
        "source_kind": args.source_kind,
        "target_repository": args.target_repository,
        "target_commit": args.target_commit,
    }
    missing = [name for name, value in required.items() if not value]
    if missing:
        raise ri.ReviewIntakeError(
            "usage_error",
            "missing required arguments: " + ", ".join(missing),
        )


def _adapt_new_source(args):
    if args.adapter == "manual":
        if not args.findings_file:
            raise ri.ReviewIntakeError(
                "manual_findings_missing",
                "manual adapter requires --findings-file",
            )
        return adapt_manual_findings(_load_json(args.findings_file))
    if args.adapter == "github":
        return adapt_github_threads(_load_json(args.source))
    if args.adapter == "sarif":
        return adapt_sarif(_load_json(args.source))
    return adapt_codeql_alerts(_load_json(args.source))


def run_new_intake(root, args):
    _required_new_args(args)
    source_path = Path(args.source)
    copied_text = (
        source_path.read_text(encoding="utf-8")
        if args.retention == "copy" and source_path.is_file()
        else None
    )
    source = ri.build_source_record(
        args.source_kind,
        args.provider,
        args.source_identity,
        args.received_at,
        args.retention,
        locator=args.source,
        copied_text=copied_text,
        source_hash=args.source_hash,
    )
    raw_findings = _adapt_new_source(args)
    trigger_event = {
        "manual": "manual_intake",
        "github": "pr_review",
        "sarif": "security_alert",
        "codeql": "security_alert",
    }[args.adapter]
    requires_plan = any(
        (item.get("router") or {}).get("requires_plan")
        for item in raw_findings
    )
    security_requested = any(
        (item.get("router") or {}).get("classification") == "security"
        for item in raw_findings
    )
    changed_paths = [
        location.get("path", "")
        for item in raw_findings
        for location in item.get("locations", [])
    ]
    adapter_run = select_adapters(
        trigger_event,
        args.adapter,
        changed_paths,
        requires_plan=requires_plan,
        security_requested=security_requested,
    )
    packet = ri.new_packet(
        args.review_id,
        source,
        {
            "repository": args.target_repository,
            "commit": args.target_commit,
            "base_branch": args.base_branch,
        },
        {"event": trigger_event, "reason_codes": ["review_received"]},
        adapter_run,
        raw_findings,
    )
    if not args.write:
        return {"action": "preview", "packet": _public_packet(packet)}
    paths = write_review_artifacts(root, packet)
    return {
        "action": "written",
        "packet": _public_packet(packet),
        "paths": {key: str(value) for key, value in paths.items()},
    }


def _verify_reference_integrity(packet):
    source = packet.get("source") or {}
    locator = Path(str(source.get("locator") or ""))
    if source.get("retention") == "reference" and locator.is_file():
        actual = ri.sha256_file(locator)
        if actual != source.get("sha256"):
            raise ri.ReviewIntakeError(
                "source_integrity_mismatch",
                "referenced review source changed after intake",
            )


def apply_decisions_to_path(root, review_id, decisions_path, write=False):
    packet_path = (
        Path(root).resolve()
        / "workspace"
        / "reviews"
        / f"{review_id}.json"
    )
    packet = _load_json(packet_path)
    _verify_reference_integrity(packet)
    decisions = _load_json(decisions_path).get("decisions") or []
    if not isinstance(decisions, list):
        raise ri.ReviewIntakeError(
            "decisions_invalid", "decisions must be a list"
        )
    for decision in decisions:
        packet = ri.apply_decision(packet, decision)
    if not write:
        return {"action": "preview", "packet": _public_packet(packet)}
    paths = write_review_artifacts(root, packet)
    return {
        "action": "written",
        "packet": _public_packet(packet),
        "paths": {key: str(value) for key, value in paths.items()},
    }


def run_validation(packet, final=False):
    errors = ri.validate_packet(packet, final=final)
    return {"action": "validated", "valid": not errors, "errors": errors}


def build_parser():
    parser = argparse.ArgumentParser(
        description="Verified ModuFlow code-review intake"
    )
    parser.add_argument("project_path", nargs="?", default=".")
    operation = parser.add_mutually_exclusive_group(required=True)
    operation.add_argument("--new", action="store_true")
    operation.add_argument("--apply-decisions")
    operation.add_argument("--validate")
    parser.add_argument("--review-id")
    parser.add_argument(
        "--adapter", choices=["manual", "github", "codeql", "sarif"]
    )
    parser.add_argument("--source")
    parser.add_argument("--findings-file")
    parser.add_argument("--source-kind", choices=sorted(ri.SOURCE_KINDS))
    parser.add_argument("--provider", default="unknown")
    parser.add_argument("--source-identity", default="unknown")
    parser.add_argument("--received-at", default=date.today().isoformat())
    parser.add_argument(
        "--retention", choices=sorted(ri.RETENTION_MODES), default="reference"
    )
    parser.add_argument("--source-hash")
    parser.add_argument("--target-repository")
    parser.add_argument("--target-commit")
    parser.add_argument("--base-branch", default="main")
    parser.add_argument("--final", action="store_true")
    parser.add_argument("--write", action="store_true")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    root = Path(args.project_path).resolve()
    try:
        if args.new:
            result = run_new_intake(root, args)
        elif args.apply_decisions:
            if not args.review_id:
                raise ri.ReviewIntakeError(
                    "usage_error", "--apply-decisions requires --review-id"
                )
            result = apply_decisions_to_path(
                root,
                args.review_id,
                args.apply_decisions,
                write=args.write,
            )
        else:
            result = run_validation(_load_json(args.validate), final=args.final)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result.get("valid", True) else 1
    except (OSError, json.JSONDecodeError, ri.ReviewIntakeError) as exc:
        code = getattr(exc, "code", "review_intake_error")
        print(
            json.dumps(
                {"action": "error", "reason_code": code, "error": str(exc)},
                ensure_ascii=False,
            )
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
