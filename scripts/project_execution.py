#!/usr/bin/env python3
import argparse
from pathlib import Path


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
    parser.add_argument("--review-handoff", action="store_true")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    if not args.review_handoff:
        parser.error("--review-handoff is required")
    if args.write:
        path = write_review_handoff(args.project_path, args.issue_id)
        print(path)
    else:
        print(build_review_handoff(args.project_path, args.issue_id))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
