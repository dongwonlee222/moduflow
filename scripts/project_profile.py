#!/usr/bin/env python3
import argparse
import json
from pathlib import Path


PROFILE_FILES = {
    ".moduflow/project-profile.md": """# Project Profile

## Summary

- Project:
- Owner:
- Team:
- Status:

## Purpose

Describe what this project is responsible for and why it exists.

## Key Links

- Repository:
- Product docs:
- Design:
- Dashboard:
- Deployment:

## Operating Notes

- Primary workflow:
- Release cadence:
- Support channel:

## Sensitive Data Rules

- Do not store credentials, API keys, private keys, signed originals, seals, identity documents, or direct personal contact/payment identifiers in this repo.
- Store secret manager references or environment variable names instead of secret values.
""",
    ".moduflow/environments.json": {
        "schema": "moduflow.environments.v1",
        "environments": [
            {
                "name": "development",
                "url": "",
                "deploy_target": "",
                "data_source": "",
                "notes": "",
            },
            {
                "name": "staging",
                "url": "",
                "deploy_target": "",
                "data_source": "",
                "notes": "",
            },
            {
                "name": "production",
                "url": "",
                "deploy_target": "",
                "data_source": "",
                "notes": "",
            },
        ],
        "sensitive_data_policy": "Store references only. Do not store secret values.",
    },
    ".moduflow/integrations.json": {
        "schema": "moduflow.integrations.v1",
        "integrations": {
            "github": {
                "repository": "",
                "issues": "",
                "pull_requests": "",
            },
            "docs": {
                "primary": "",
                "design": "",
                "analytics": "",
            },
            "communication": {
                "slack_channel": "",
                "email_group": "",
            },
            "analytics": {
                "dashboard": "",
                "warehouse": "",
            },
        },
        "sensitive_data_policy": "Store links and labels only. Do not store credentials.",
    },
}


def render_content(content):
    if isinstance(content, str):
        return content
    return json.dumps(content, ensure_ascii=False, indent=2) + "\n"


def build_profile_plan(path, dry_run=True):
    project_root = Path(path).resolve()
    writes = []
    for relative in PROFILE_FILES:
        if not (project_root / relative).exists():
            writes.append(relative)
    return {
        "schema": "moduflow.profile-plan.v1",
        "project_root": str(project_root),
        "dry_run": dry_run,
        "writes": writes,
        "preserves_existing_files": True,
        "sensitive_data_policy": "Do not store credentials, secrets, signed originals, seals, identity documents, or direct personal contact/payment identifiers.",
    }


def write_if_missing(path, content):
    if path.exists():
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_content(content), encoding="utf-8")
    return True


def apply_profile_plan(plan):
    project_root = Path(plan["project_root"])
    written = []
    for relative, content in PROFILE_FILES.items():
        if write_if_missing(project_root / relative, content):
            written.append(relative)
    plan["written"] = written
    return plan


def main():
    parser = argparse.ArgumentParser(description="Plan or create ModuFlow project profile metadata.")
    parser.add_argument("project_path", nargs="?", default=".")
    parser.add_argument("--write", action="store_true", help="Create missing profile metadata files.")
    args = parser.parse_args()

    plan = build_profile_plan(args.project_path, dry_run=not args.write)
    if args.write:
        plan = apply_profile_plan(plan)
    print(json.dumps(plan, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
