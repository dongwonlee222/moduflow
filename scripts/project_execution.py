#!/usr/bin/env python3
import argparse
import json
import re
from pathlib import Path


READINESS_SCHEMA = "moduflow.implementation-readiness.v1"
VERIFY_COMMANDS = [
    "python3 -m unittest discover -s tests -v",
    "python3 scripts/release_check.py .",
]


def _read_if_exists(path):
    path = Path(path)
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _task_lines(tasks_text):
    return [line.strip() for line in tasks_text.splitlines() if line.strip().startswith("- [")]


def _implementation_tasks(tasks_text):
    tasks = []
    for line in _task_lines(tasks_text):
        lowered = line.lower()
        if any(keyword in lowered for keyword in ["implementation", "code", "script", "helper"]):
            tasks.append(line)
    return tasks or _task_lines(tasks_text)


def _combined_issue_text(root, issue_id):
    root = Path(root).resolve()
    spec_dir = root / "specs" / issue_id
    paths = [
        root / "issues" / f"{issue_id}.md",
        spec_dir / "spec.md",
        spec_dir / "plan.md",
        spec_dir / "tasks.md",
        spec_dir / "status.md",
    ]
    return "\n".join(_read_if_exists(path) for path in paths)


def _has_any(text, keywords):
    lowered = text.lower()
    for keyword in keywords:
        keyword = keyword.lower()
        if keyword.isalpha() and len(keyword) <= 4:
            if re.search(rf"\b{re.escape(keyword)}\b", lowered):
                return True
        elif keyword in lowered:
            return True
    return False


def _readiness_check(check_id, required, evidence_present, severity, label, recommendation):
    if not required:
        return {
            "id": check_id,
            "state": "not_applicable",
            "severity": "low",
            "evidence": f"{label} not in scope.",
            "gap": "",
            "recommendation": "",
        }
    if evidence_present:
        return {
            "id": check_id,
            "state": "pass",
            "severity": "low",
            "evidence": f"{label} evidence found.",
            "gap": "",
            "recommendation": "",
        }
    state = "fail" if severity == "high" else "warn"
    return {
        "id": check_id,
        "state": state,
        "severity": severity,
        "evidence": "",
        "gap": f"{label} is missing.",
        "recommendation": recommendation,
    }


def build_implementation_readiness(root, issue_id):
    root = Path(root).resolve()
    text = _combined_issue_text(root, issue_id)
    lowered = text.lower()

    frontend_scope = _has_any(
        lowered,
        ["ui", "frontend", "component", "screen", "storybook", "browser", "playwright"],
    )
    api_scope = _has_any(
        lowered,
        ["api", "endpoint", "request", "response", "integration", "msw"],
    )
    permission_scope = _has_any(
        lowered,
        ["permission", "role", "auth", "admin", "access control"],
    )
    release_scope = True

    checks = [
        _readiness_check(
            "api_contract",
            api_scope,
            _has_any(lowered, ["api contract", "contract mapping", "endpoint", "request/response", "response {"]),
            "high",
            "API contract mapping",
            f"Return to product:plan {issue_id} and define endpoints, request/response shapes, and error states.",
        ),
        _readiness_check(
            "test_strategy",
            True,
            _has_any(lowered, ["test strategy", "unit test", "integration test", "smoke", "unittest", "release_check"]),
            "high",
            "Test strategy",
            f"Return to product:plan {issue_id} and state which tests prove the behavior.",
        ),
        _readiness_check(
            "storybook_states",
            frontend_scope,
            _has_any(lowered, ["storybook required states", "storybook states", "loading, empty", "empty, error"]),
            "medium",
            "Storybook required states",
            f"Return to product:plan {issue_id} and list required component/UI states or mark not applicable.",
        ),
        _readiness_check(
            "msw_fixtures",
            frontend_scope and api_scope,
            _has_any(lowered, ["msw fixture", "msw fixtures", "fixture baseline", "fixture"]),
            "medium",
            "MSW fixture baseline",
            f"Return to product:plan {issue_id} and list API fixture names or mark not applicable.",
        ),
        _readiness_check(
            "playwright_smoke",
            frontend_scope,
            _has_any(lowered, ["playwright smoke", "smoke matrix", "browser smoke", "route/path"]),
            "medium",
            "Playwright smoke matrix",
            f"Return to product:plan {issue_id} and define route, action, assertion, and viewport scope.",
        ),
        _readiness_check(
            "permission_model",
            permission_scope,
            _has_any(lowered, ["permission/role model", "role model", "admin allowed", "viewer denied", "allowed", "denied"]),
            "high",
            "Permission/role model",
            f"Return to product:plan {issue_id} and define roles, allowed/denied actions, and edge cases.",
        ),
        _readiness_check(
            "release_rollback",
            release_scope,
            _has_any(lowered, ["release/rollback", "rollback", "release_check", "post-release"]),
            "medium",
            "Release/rollback verification",
            f"Return to product:plan {issue_id} and define release verification plus rollback path.",
        ),
    ]

    if any(check["state"] == "fail" and check["severity"] == "high" for check in checks):
        status = "not_ready"
    elif any(check["state"] in {"fail", "warn"} for check in checks):
        status = "warning"
    else:
        status = "ready"

    next_command = f"product:plan {issue_id}" if status == "not_ready" else f"product:execute {issue_id}"
    return {
        "schema": READINESS_SCHEMA,
        "issue_id": issue_id,
        "status": status,
        "mode": "report-only",
        "checks": checks,
        "next_command": next_command,
    }


def write_implementation_readiness(root, issue_id):
    root = Path(root).resolve()
    target = root / "specs" / issue_id / "implementation-readiness.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(build_implementation_readiness(root, issue_id), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return target


def build_review_handoff(root, issue_id):
    root = Path(root).resolve()
    spec_dir = root / "specs" / issue_id
    issue_path = root / "issues" / f"{issue_id}.md"
    spec_path = spec_dir / "spec.md"
    tasks_path = spec_dir / "tasks.md"
    status_path = spec_dir / "status.md"
    dashboard_path = "memory/dashboard.html"
    issue_html_path = f"memory/issue-{issue_id}.html"

    issue_text = _read_if_exists(issue_path)
    spec_text = _read_if_exists(spec_path)
    tasks_text = _read_if_exists(tasks_path)
    status_text = _read_if_exists(status_path)

    impl_tasks = _implementation_tasks(tasks_text)
    task_summary = "\n".join(impl_tasks) if impl_tasks else "- No implementation tasks found."

    lines = [
        f"# Review Handoff: {issue_id}",
        "",
        "## Purpose",
        "",
        "Continue through implementation review without asking the user to manually decide each next step.",
        "The main agent maps these host-agnostic dispatch blocks to the subagent tools available in the current environment.",
        "",
        "## Implementation Subagent",
        "",
        "- Worker: `implementation-worker`",
        "- Goal: review the completed implementation tasks and identify missing code/doc changes before review.",
        "- Input artifacts:",
        f"  - `{issue_path.relative_to(root)}`",
        f"  - `{spec_path.relative_to(root)}`",
        f"  - `{tasks_path.relative_to(root)}`",
        "",
        "### Implementation Tasks",
        "",
        task_summary,
        "",
        "## Review Subagents",
        "",
        "### QA Review",
        "",
        "- Worker: `qa-reviewer`",
        "- Goal: run verification, check acceptance criteria, and report regressions.",
        "- Required commands:",
        *[f"  - `{command}`" for command in VERIFY_COMMANDS],
        "",
        "### PM / Spec Review",
        "",
        "- Worker: `pm-strategist`",
        "- Worker: `spec-architect`",
        "- Goal: compare implementation against problem, goals, non-goals, and acceptance criteria.",
        "- Constitution check (issue 073): verify against `workspace/constitution.md` and record the compliance line in review.md — `Constitution: v<X.Y> checked — no violations` or the violation list.",
        "",
        "## Visual Handoff",
        "",
        "Regenerate the ModuFlow dashboard and its issue drill-down before reporting completion.",
        "The issue HTML is not a separate source artifact; it is a derived L2 view linked from the dashboard system.",
        "",
        "```bash\npython3 scripts/project_memory.py . --dashboard\n```",
        "",
        f"```bash\npython3 scripts/project_memory.py . --issue {issue_id}\n```",
        "",
        f"- Dashboard output: `{dashboard_path}`",
        f"- Issue drill-down output: `{issue_html_path}`",
        "- The final user report should include the dashboard path first and the issue drill-down path when a specific issue was changed.",
        "",
        "## Final Report Contract",
        "",
        "- Summarize implementation changes.",
        "- Summarize implementation-worker findings.",
        "- Summarize QA reviewer findings.",
        "- Summarize PM/spec reviewer findings.",
        "- Include verification command results.",
        f"- Include dashboard HTML path: `{dashboard_path}`.",
        f"- Include issue drill-down path: `{issue_html_path}`.",
        "",
    ]
    if issue_text or spec_text or status_text:
        lines.extend(
            [
                "## Source Snapshot",
                "",
                f"- Issue bytes: {len(issue_text.encode('utf-8'))}",
                f"- Spec bytes: {len(spec_text.encode('utf-8'))}",
                f"- Status bytes: {len(status_text.encode('utf-8'))}",
                "",
            ]
        )
    return "\n".join(lines)


def write_review_handoff(root, issue_id):
    root = Path(root).resolve()
    target = root / "specs" / issue_id / "review-handoff.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(build_review_handoff(root, issue_id), encoding="utf-8")
    return target


def main():
    parser = argparse.ArgumentParser(description="Generate ModuFlow execution/review handoff artifacts.")
    parser.add_argument("project_path", nargs="?", default=".")
    parser.add_argument("--issue-id", required=True)
    parser.add_argument("--readiness", action="store_true")
    parser.add_argument("--review-handoff", action="store_true")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    if args.readiness:
        if args.write:
            print(write_implementation_readiness(args.project_path, args.issue_id))
        else:
            print(
                json.dumps(
                    build_implementation_readiness(args.project_path, args.issue_id),
                    ensure_ascii=False,
                    indent=2,
                )
            )
        return 0

    if not args.review_handoff:
        parser.error("--readiness or --review-handoff is required")
    if args.write:
        path = write_review_handoff(args.project_path, args.issue_id)
        print(path)
    else:
        print(build_review_handoff(args.project_path, args.issue_id))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
