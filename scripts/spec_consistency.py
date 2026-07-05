#!/usr/bin/env python3
"""Read-only checker: validate that an issue's spec.md, plan.md, and tasks.md
agree with each other before execution starts.

Stdlib only. Never writes files. Never invokes subprocess.
"""
import argparse
import json
import re
import sys
from pathlib import Path

STOPWORDS = {
    "the", "and", "for", "that", "with", "must", "should", "when", "given",
    "then", "every", "each", "this", "are", "not", "its", "into", "from",
}

VAGUE = {
    "fast", "quick", "slow", "easy", "simple", "secure", "intuitive",
    "scalable", "robust", "efficient", "user-friendly", "seamless",
    "performant",
}

SEVERITY_RANK = {"error": 0, "warn": 1, "info": 2}


def _strip_fences(text):
    out, in_fence = [], False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if not in_fence:
            out.append(line)
    return "\n".join(out)


def _section(text, name):
    pattern = re.compile(
        r"^##\s+" + re.escape(name) + r"\s*$(.*?)(?=^## |\Z)",
        re.M | re.S,
    )
    match = pattern.search(text)
    if not match:
        return ""
    return match.group(1).strip("\n")


def _bullets(section_text):
    """Top-level '- ' bullets, joined with indented continuation lines."""
    bullets = []
    current = None
    for line in section_text.splitlines():
        if re.match(r"^-\s+", line):
            if current is not None:
                bullets.append(current.strip())
            current = re.sub(r"^-\s+", "", line)
        elif current is not None and re.match(r"^\s{2,}\S", line):
            current += " " + line.strip()
        elif current is not None and line.strip() == "":
            continue
        else:
            if current is not None:
                bullets.append(current.strip())
                current = None
    if current is not None:
        bullets.append(current.strip())
    return bullets


def _tokens(text):
    return set(re.findall(r"[a-z0-9]{3,}", text.lower())) - STOPWORDS


def _check_coverage(spec_text, target_text):
    findings = []
    checked = 0
    flagged = 0
    ac_section = _section(spec_text, "Acceptance Criteria")
    bullets = _bullets(ac_section)
    target_tokens = _tokens(target_text)
    for bullet in bullets:
        bt = _tokens(bullet)
        if not bt:
            # Zero-token bullets (e.g. Korean-only text with this ASCII
            # tokenizer) are never evaluated — don't count them as checked.
            continue
        checked += 1
        shared = bt & target_tokens
        flag = len(shared) < 2 or len(shared) < 0.3 * len(bt)
        if flag:
            flagged += 1
            truncated = bullet if len(bullet) <= 80 else bullet[:80] + "..."
            findings.append({
                "severity": "warn",
                "check": "coverage",
                "message": f"possibly uncovered acceptance criterion: '{truncated}'",
            })
    return findings, checked, flagged


def _check_vague_terms(spec_text):
    findings = []
    for section_name in ("Requirements", "Acceptance Criteria"):
        section_text = _section(spec_text, section_name)
        for bullet in _bullets(section_text):
            if re.search(r"\d", bullet):
                continue
            for term in VAGUE:
                if re.search(r"\b" + re.escape(term) + r"\b", bullet, re.IGNORECASE):
                    findings.append({
                        "severity": "warn",
                        "check": "vague-term",
                        "message": f"requirement lacks a measurable criterion (vague term '{term}'): '{bullet[:80]}{'...' if len(bullet) > 80 else ''}'",
                    })
    return findings


def _check_structure(spec_text, plan_text, tasks_text, has_plan, has_tasks):
    findings = []

    ac_present = re.search(r"^##\s+Acceptance Criteria\s*$", spec_text, re.M) is not None
    if not ac_present:
        findings.append({
            "severity": "error",
            "check": "structure",
            "message": "spec.md is missing a '## Acceptance Criteria' section",
        })

    if has_plan and has_tasks:
        plan_streams = set(re.findall(r"^###\s+Stream\s+([A-Z0-9]+)", plan_text, re.M))
        task_streams = set(re.findall(r"^##\s+Stream\s+([A-Z0-9]+)", tasks_text, re.M))

        for stream in sorted(plan_streams - task_streams):
            findings.append({
                "severity": "error",
                "check": "structure",
                "message": f"plan.md Stream {stream} has no corresponding '## Stream {stream}' section in tasks.md",
            })
        for stream in sorted(task_streams - plan_streams):
            findings.append({
                "severity": "warn",
                "check": "structure",
                "message": f"tasks.md Stream {stream} traces to no plan.md stream",
            })

    if has_tasks:
        checkbox_count = len(re.findall(r"^-\s+\[[ xX]\]", tasks_text, re.M))
        if checkbox_count == 0:
            findings.append({
                "severity": "error",
                "check": "structure",
                "message": "tasks.md has zero checkboxes",
            })

    return findings


def analyze(root, issue_id):
    root = Path(root).resolve()
    spec_dir = root / "specs" / issue_id
    if not spec_dir.is_dir():
        raise FileNotFoundError(f"specs/{issue_id}/ directory not found")

    findings = []

    spec_path = spec_dir / "spec.md"
    plan_path = spec_dir / "plan.md"
    tasks_path = spec_dir / "tasks.md"

    if not spec_path.exists():
        findings.append({
            "severity": "error",
            "check": "artifacts",
            "message": "spec.md is missing",
        })
        spec_text_raw = ""
    else:
        spec_text_raw = spec_path.read_text(encoding="utf-8")

    has_plan = plan_path.exists()
    has_tasks = tasks_path.exists()

    if not has_plan:
        findings.append({
            "severity": "info",
            "check": "artifacts",
            "message": "plan.md is missing",
        })
    if not has_tasks:
        findings.append({
            "severity": "info",
            "check": "artifacts",
            "message": "tasks.md is missing",
        })

    plan_text_raw = plan_path.read_text(encoding="utf-8") if has_plan else ""
    tasks_text_raw = tasks_path.read_text(encoding="utf-8") if has_tasks else ""

    spec_text = _strip_fences(spec_text_raw)
    plan_text = _strip_fences(plan_text_raw)
    tasks_text = _strip_fences(tasks_text_raw)

    coverage_checked = 0
    coverage_flagged = 0
    if spec_text_raw:
        target_text = plan_text + "\n" + tasks_text
        coverage_findings, coverage_checked, coverage_flagged = _check_coverage(spec_text, target_text)
        findings.extend(coverage_findings)
        findings.extend(_check_vague_terms(spec_text))
        findings.extend(_check_structure(spec_text, plan_text, tasks_text, has_plan, has_tasks))

    findings.sort(key=lambda f: (SEVERITY_RANK.get(f["severity"], 99), f["check"], f["message"]))

    summary = {
        "error": sum(1 for f in findings if f["severity"] == "error"),
        "warn": sum(1 for f in findings if f["severity"] == "warn"),
        "info": sum(1 for f in findings if f["severity"] == "info"),
        "coverage_checked": coverage_checked,
        "coverage_flagged": coverage_flagged,
    }

    return {
        "schema": "moduflow.spec-consistency.v1",
        "issue_id": issue_id,
        "findings": findings,
        "summary": summary,
    }


def main():
    parser = argparse.ArgumentParser(description="Check spec/plan/tasks consistency for an issue.")
    parser.add_argument("root", help="Project root directory")
    parser.add_argument("--issue-id", required=True, help="Issue ID (specs/<id>/ directory name)")
    args = parser.parse_args()

    try:
        result = analyze(args.root, args.issue_id)
    except FileNotFoundError as exc:
        error_obj = {
            "schema": "moduflow.spec-consistency.v1",
            "error": str(exc),
        }
        print(json.dumps(error_obj, ensure_ascii=False, indent=2))
        return 1

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
