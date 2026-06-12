#!/usr/bin/env python3
import json
import sys
from pathlib import Path


REQUIRED_PATHS = [
    ".moduflow/config.json",
    ".moduflow/state.json",
]

OPTIONAL_CAPABILITY_PATHS = {
    "profile": [
        ".moduflow/project-profile.md",
        ".moduflow/environments.json",
        ".moduflow/integrations.json",
    ],
    "knowledge": [
        "knowledge/index.md",
        "knowledge/decisions",
        "knowledge/benchmarks",
        "knowledge/reports",
        "knowledge/research",
        "knowledge/data-notes",
        "knowledge/references",
    ],
    "workflow": [
        "workflow/review-gates.md",
        "workflow/approval-policy.md",
        "workflow/release-policy.md",
        "workflow/handoff.md",
        "workflow/risks.md",
    ],
}

JSON_FILES = [
    ".moduflow/config.json",
    ".moduflow/state.json",
]

OPTIONAL_JSON_FILES = [
    ".moduflow/environments.json",
    ".moduflow/integrations.json",
]


def read_json(path, errors):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"{path}: invalid JSON ({exc})")
        return None


def read_config_paths(root, errors):
    config_path = root / ".moduflow" / "config.json"
    if not config_path.exists():
        return {}
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    paths = config.get("paths", {})
    return paths if isinstance(paths, dict) else {}


def required_paths(root, errors):
    paths = read_config_paths(root, errors)
    issues = paths.get("issues", "issues")
    specs = paths.get("specs", "specs")
    workspace = paths.get("workspace", "workspace")
    return REQUIRED_PATHS + [
        issues,
        specs,
        f"{workspace}/inbox.md",
        f"{workspace}/opportunities.md",
        f"{workspace}/roadmap.md",
        f"{workspace}/dashboard.md",
    ]


def validate_project(path):
    root = Path(path).resolve()
    errors = []
    warnings = []

    for relative in required_paths(root, errors):
        if not (root / relative).exists():
            errors.append(f"Missing required project artifact: {relative}")

    for capability, paths in OPTIONAL_CAPABILITY_PATHS.items():
        missing = [relative for relative in paths if not (root / relative).exists()]
        if missing:
            warnings.append(
                f"Optional project capability not initialized: {capability} ({', '.join(missing)})"
            )

    parsed = {}
    for relative in JSON_FILES + OPTIONAL_JSON_FILES:
        target = root / relative
        if target.exists():
            parsed[relative] = read_json(target, errors)

    config = parsed.get(".moduflow/config.json")
    if config and config.get("schema") != "moduflow.config.v1":
        errors.append(".moduflow/config.json: schema must be moduflow.config.v1")

    state = parsed.get(".moduflow/state.json")
    if state:
        if state.get("schema") != "moduflow.state.v1":
            errors.append(".moduflow/state.json: schema must be moduflow.state.v1")
        if "phase" not in state:
            errors.append(".moduflow/state.json: missing phase")
        if "next_command" not in state:
            errors.append(".moduflow/state.json: missing next_command")

    return {
        "schema": "moduflow.project-validation.v1",
        "project_root": str(root),
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
    }


def main():
    result = validate_project(sys.argv[1] if len(sys.argv) > 1 else ".")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
