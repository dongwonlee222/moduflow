#!/usr/bin/env python3
import json
import sys
from pathlib import Path


def load_json(path, errors):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"{path}: invalid JSON ({exc})")
        return {}


def inspect_portfolio(path):
    root = Path(path).resolve()
    errors = []
    warnings = []
    registry_path = root / "projects.json"
    if not registry_path.exists():
        errors.append("Missing portfolio registry: projects.json")
        registry = {"projects": []}
    else:
        registry = load_json(registry_path, errors)

    projects = []
    for entry in registry.get("projects", []):
        project_path = Path(entry.get("path", "")).expanduser()
        if not project_path.is_absolute():
            project_path = (root / project_path).resolve()
        else:
            project_path = project_path.resolve()
        project_warnings = []
        if not project_path.exists():
            project_warnings.append(f"missing project path: {project_path}")
        elif not (project_path / ".moduflow" / "state.json").exists():
            project_warnings.append(f"missing state: {project_path / '.moduflow' / 'state.json'}")
        warnings.extend(project_warnings)
        projects.append(
            {
                "id": entry.get("id", project_path.name),
                "name": entry.get("name", entry.get("id", project_path.name)),
                "path": str(project_path),
                "warnings": project_warnings,
            }
        )

    return {
        "schema": "moduflow.portfolio-doctor.v1",
        "portfolio_root": str(root),
        "valid": not errors and not warnings,
        "errors": errors,
        "warnings": warnings,
        "projects": projects,
    }


def main():
    result = inspect_portfolio(sys.argv[1] if len(sys.argv) > 1 else ".")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
