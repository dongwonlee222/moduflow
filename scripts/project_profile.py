#!/usr/bin/env python3
import argparse
import json
import re
from pathlib import Path

from scripts.project_repository_identity import (
    ALLOWED_LIFECYCLES,
    ALLOWED_PROVIDERS,
    IdentityConfigError,
    load_repository_identity,
    normalize_git_url,
)


IDENTITY_BLOCK_START = "<!-- moduflow:repository-identity:start -->"
IDENTITY_BLOCK_END = "<!-- moduflow:repository-identity:end -->"


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


def _read_config(root):
    path = Path(root) / ".moduflow" / "config.json"
    if not path.is_file():
        return {"schema": "moduflow.config.v1", "git": {}}
    try:
        config = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(".moduflow/config.json must contain valid JSON before profile write.") from exc
    if not isinstance(config, dict):
        raise ValueError(".moduflow/config.json must contain a JSON object.")
    return config


def _legacy_remote_candidate(config, provider):
    git_config = config.get("git")
    remote = git_config.get("remote") if isinstance(git_config, dict) else None
    if not isinstance(remote, str) or not remote.strip():
        return None
    try:
        return normalize_git_url(remote, provider)
    except IdentityConfigError:
        return None


def build_repository_identity_proposal(
    path,
    canonical_repository=None,
    provider=None,
    remote_name_hint=None,
    base_branch=None,
    lifecycle=None,
    local_only=False,
):
    """Build an explicit identity proposal without adopting observed state."""
    root = Path(path).resolve()
    config = _read_config(root)
    selected_provider = provider or "github"
    selected_base = base_branch or "main"
    selected_lifecycle = lifecycle or "active"

    if selected_provider not in ALLOWED_PROVIDERS:
        raise ValueError("provider must be github or generic")
    if selected_lifecycle not in ALLOWED_LIFECYCLES:
        raise ValueError("lifecycle must be active, read_only, or archived")
    if not isinstance(selected_base, str) or not selected_base.strip():
        raise ValueError("base_branch must be a non-empty string")

    existing = load_repository_identity(root)
    proposed_identity = None
    source = "none"
    if local_only:
        proposed_identity = {
            "mode": "local_only",
            "provider": selected_provider,
            "base_branch": selected_base.strip(),
            "lifecycle": selected_lifecycle,
        }
        source = "explicit_local_only"
    elif canonical_repository is not None:
        proposed_identity = {
            "mode": "remote",
            "provider": selected_provider,
            "canonical_repository": normalize_git_url(
                canonical_repository,
                selected_provider,
            ),
            "remote_name_hint": (remote_name_hint or "origin").strip(),
            "base_branch": selected_base.strip(),
            "lifecycle": selected_lifecycle,
        }
        if not proposed_identity["remote_name_hint"]:
            raise ValueError("remote_name_hint must be a non-empty string")
        source = "explicit_remote"
    elif existing["configured"]:
        proposed_identity = dict(existing["identity"])
        source = "existing_identity"

    legacy_candidate = _legacy_remote_candidate(config, selected_provider)
    return {
        "schema": "moduflow.repository-identity-proposal.v1",
        "project_root": str(root),
        "source": source,
        "requires_confirmation": proposed_identity is None and legacy_candidate is not None,
        "legacy_remote_candidate": legacy_candidate,
        "proposed_identity": proposed_identity,
        "writes": proposed_identity is not None,
    }


def render_repository_identity_projection(identity):
    lines = [
        IDENTITY_BLOCK_START,
        "## Repository Identity",
        "",
        f"- Mode: `{identity['mode']}`",
        f"- Provider: `{identity['provider']}`",
    ]
    if identity["mode"] == "remote":
        lines.extend(
            [
                f"- Canonical repository: `{identity['canonical_repository']}`",
                f"- Remote name hint: `{identity['remote_name_hint']}`",
            ]
        )
    lines.extend(
        [
            f"- Base branch: `{identity['base_branch']}`",
            f"- Lifecycle: `{identity['lifecycle']}`",
            IDENTITY_BLOCK_END,
        ]
    )
    return "\n".join(lines) + "\n"


def _project_profile_with_identity(existing, identity):
    block = render_repository_identity_projection(identity)
    pattern = re.compile(
        re.escape(IDENTITY_BLOCK_START)
        + r".*?"
        + re.escape(IDENTITY_BLOCK_END)
        + r"\n?",
        re.DOTALL,
    )
    if pattern.search(existing):
        return pattern.sub(block, existing, count=1)
    separator = "" if not existing else ("\n" if existing.endswith("\n") else "\n\n")
    return existing + separator + block


def apply_repository_identity_proposal(path, proposal):
    """Write one confirmed identity while preserving unrelated project content."""
    identity = proposal.get("proposed_identity")
    if not isinstance(identity, dict):
        raise ValueError("repository identity proposal requires explicit confirmation before write")

    root = Path(path).resolve()
    config_path = root / ".moduflow" / "config.json"
    profile_path = root / ".moduflow" / "project-profile.md"
    config = _read_config(root)
    git_config = config.get("git")
    if not isinstance(git_config, dict):
        git_config = {}
        config["git"] = git_config
    git_config["identity"] = dict(identity)
    config_text = json.dumps(config, ensure_ascii=False, indent=2) + "\n"

    existing_profile = (
        profile_path.read_text(encoding="utf-8")
        if profile_path.is_file()
        else render_content(PROFILE_FILES[".moduflow/project-profile.md"])
    )
    profile_text = _project_profile_with_identity(existing_profile, identity)

    previous_config = config_path.read_text(encoding="utf-8") if config_path.is_file() else None
    previous_profile = profile_path.read_text(encoding="utf-8") if profile_path.is_file() else None
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(config_text, encoding="utf-8")
    profile_path.write_text(profile_text, encoding="utf-8")
    return {
        "schema": "moduflow.repository-identity-write.v1",
        "written": previous_config != config_text or previous_profile != profile_text,
        "config_path": str(config_path),
        "profile_path": str(profile_path),
        "identity": identity,
    }


def main():
    parser = argparse.ArgumentParser(description="Plan or create ModuFlow project profile metadata.")
    parser.add_argument("project_path", nargs="?", default=".")
    parser.add_argument("--write", action="store_true", help="Create missing profile metadata files.")
    parser.add_argument("--canonical-repository")
    parser.add_argument("--provider", choices=sorted(ALLOWED_PROVIDERS))
    parser.add_argument("--remote-name-hint")
    parser.add_argument("--base-branch")
    parser.add_argument("--lifecycle", choices=sorted(ALLOWED_LIFECYCLES))
    parser.add_argument("--local-only", action="store_true")
    args = parser.parse_args()

    plan = build_profile_plan(args.project_path, dry_run=not args.write)
    proposal = build_repository_identity_proposal(
        args.project_path,
        canonical_repository=args.canonical_repository,
        provider=args.provider,
        remote_name_hint=args.remote_name_hint,
        base_branch=args.base_branch,
        lifecycle=args.lifecycle,
        local_only=args.local_only,
    )
    plan["repository_identity"] = proposal
    if args.write:
        plan = apply_profile_plan(plan)
        if proposal["proposed_identity"] is not None and (
            args.canonical_repository is not None or args.local_only
        ):
            plan["repository_identity_write"] = apply_repository_identity_proposal(
                args.project_path,
                proposal,
            )
    print(json.dumps(plan, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
