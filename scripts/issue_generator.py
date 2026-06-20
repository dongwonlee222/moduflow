#!/usr/bin/env python3
import argparse
import sys
import re
from datetime import date
from pathlib import Path

def get_next_issue_number(issues_dir):
    issues_path = Path(issues_dir)
    if not issues_path.exists():
        return 1
    max_num = 0
    for f in issues_path.glob("*.md"):
        m = re.match(r"^(\d+)-", f.name)
        if m:
            num = int(m.group(1))
            if num > max_num:
                max_num = num
    return max_num + 1

def format_issue_filename(num, title):
    slug = title.lower()
    slug = re.sub(r"[^a-z0-9가-힣\s-]", "", slug)
    slug = re.sub(r"[\s-]+", "-", slug).strip("-")
    return f"{num:03d}-{slug}.md"

def generate_issues_from_goal(goal, search_mock_data=None):
    # This simulates/implements a benchmarking engine that breaks a Goal into 3 granular issues.
    # In a real environment, it can query search_web or read mock benchmarking patterns.
    # Supported localized translations: Convert English benchmarking insights to Korean summaries.
    benchmarked_info = "Benchmarked from industry best practices."
    if search_mock_data:
        benchmarked_info = search_mock_data
    
    # Simple rule-based English-to-Korean translation simulation for benchmarking data
    translated_info = benchmarked_info
    if "best practices" in benchmarked_info.lower():
        translated_info = "업계 최고 모범 사례 (Best Practices) 기반 분석 결과 반영"
    elif "oauth2 rfc" in benchmarked_info.lower():
        translated_info = "OAuth2 RFC 보안 표준 스펙 분석 결과 반영"

    issues = [
        {
            "title": f"Setup database schema and auth scope for {goal}",
            "summary": f"Define the persistence layer, environment parameters, and models needed for {goal}. ({translated_info})",
            "opportunity": f"Industry standards ({benchmarked_info}) recommend starting with a clean data contract.",
            "scope_in": [
                "Define DB schema and tables",
                "Setup basic config models"
            ],
            "scope_out": [
                "Advanced caching layer",
                "Frontend integration"
            ],
            "acceptance_criteria": [
                "Database migrations execute with exit code 0",
                "Schema validates against target models"
            ],
            "tasks": [
                "Design schema parameters",
                "Create initial migration scripts"
            ]
        },
        {
            "title": f"Implement core services and middleware for {goal}",
            "summary": f"Create the backend services, controllers, and verification middleware logic for {goal}.",
            "opportunity": f"Securing access using production-ready standards ensures reliability.",
            "scope_in": [
                "Core domain service classes",
                "Middleware validation endpoints"
            ],
            "scope_out": [
                "Performance load testing",
                "Third-party external notifications"
            ],
            "acceptance_criteria": [
                "All backend endpoint tests pass successfully",
                "Unauthorized requests are correctly blocked with 401 status"
            ],
            "tasks": [
                "Implement service controllers",
                "Setup middleware validation layers"
            ]
        },
        {
            "title": f"Integrate frontend client interface for {goal}",
            "summary": f"Create user-facing client controllers, flows, and interactive state visualizers for {goal}.",
            "opportunity": f"A smooth interface helps users easily understand and interact with the service.",
            "scope_in": [
                "Build basic control panel UI",
                "Connect client to backend APIs"
            ],
            "scope_out": [
                "Native mobile application wrappers"
            ],
            "acceptance_criteria": [
                "Frontend correctly fetches state from backend APIs",
                "Basic action clicks trigger correct states"
            ],
            "tasks": [
                "Create frontend views and templates",
                "Hook event listeners to backend endpoints"
            ]
        }
    ]
    return issues

def write_issue_file(root_dir, num, issue_data):
    issues_dir = Path(root_dir) / "issues"
    issues_dir.mkdir(parents=True, exist_ok=True)
    filename = format_issue_filename(num, issue_data["title"])
    file_path = issues_dir / filename
    
    tasks_block = "\n".join([f"- [ ] {task}" for task in issue_data["tasks"]])
    scope_in_block = "\n".join([f"- {item}" for item in issue_data["scope_in"]])
    scope_out_block = "\n".join([f"- {item}" for item in issue_data["scope_out"]])
    ac_block = "\n".join([f"- {item}" for item in issue_data["acceptance_criteria"]])
    
    content = f"""# Issue {num:03d}: {issue_data["title"]}

## Summary

{issue_data["summary"]}

## Source

- Type: product improvement / Autonomous PM Agent
- Link: goal-decomposition
- Date: {date.today().isoformat()}

## Lifecycle

- Phase: issue
- Created: {date.today().isoformat()}
- Started:
- Target End:
- Completed:
- Last Updated: {date.today().isoformat()}

## Opportunity

{issue_data["opportunity"]}

## Scope

### In

{scope_in_block}

### Out

{scope_out_block}

## Acceptance Criteria

{ac_block}

## Workflow Tasks

- [ ] spec -> specs/{format_issue_filename(num, issue_data["title"])[:-3]}/spec.md
- [ ] plan -> specs/{format_issue_filename(num, issue_data["title"])[:-3]}/plan.md
- [ ] execute -> PR / commits
- [ ] review -> review notes
{tasks_block}
"""
    file_path.write_text(content, encoding="utf-8")
    return file_path

def main():
    parser = argparse.ArgumentParser(description="Autonomous goal benchmarking and issue generator")
    parser.add_argument("goal", help="The high-level goal to decompose")
    parser.add_argument("--root", default=".", help="Project root directory")
    args = parser.parse_args()

    root_dir = Path(args.root).resolve()
    next_num = get_next_issue_number(root_dir / "issues")
    
    print(f"Goal: {args.goal}")
    print(f"Decomposing goal and generating issues starting from #{next_num}...")
    
    issues = generate_issues_from_goal(args.goal)
    for i, issue_data in enumerate(issues):
        num = next_num + i
        fpath = write_issue_file(root_dir, num, issue_data)
        print(f"Generated issue: {fpath.relative_to(root_dir)}")

if __name__ == "__main__":
    main()
