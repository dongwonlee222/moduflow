#!/usr/bin/env python3
import importlib.util
import json
import subprocess
import sys
from pathlib import Path


def run_command(args, cwd):
    result = subprocess.run(args, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    return {
        "args": args,
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }


def load_script_module(name, relative_path):
    path = Path(__file__).resolve().parents[1] / relative_path
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_importable_validation(name, func, root):
    result = func(root)
    return {
        "returncode": 0 if result.get("valid") else 1,
        "ok": bool(result.get("valid")),
        "errors": result.get("errors", []),
    }


def run_release_check(path):
    root = Path(path).resolve()
    checks = {}
    errors = []

    validate_moduflow = load_script_module("validate_moduflow", "scripts/validate_moduflow.py")
    validate_project_artifacts = load_script_module("validate_project_artifacts", "scripts/validate_project_artifacts.py")

    importable_checks = {
        "validate_moduflow": (validate_moduflow.validate_moduflow, root),
        "validate_project_artifacts": (validate_project_artifacts.validate_project, root),
    }
    for name, (func, target) in importable_checks.items():
        result = run_importable_validation(name, func, target)
        checks[name] = {
            "returncode": result["returncode"],
            "ok": result["ok"],
        }
        if not result["ok"]:
            errors.append(f"{name} failed: {'; '.join(result['errors'])}")

    commands = {
        "tests": [
            "python3",
            "-m",
            "unittest",
            "tests.test_project_migration",
            "tests.test_project_profile",
            "tests.test_project_knowledge",
            "tests.test_project_portfolio",
            "tests.test_project_workflow",
            "tests.test_worker_orchestration",
            "tests.test_codex_personal_install",
            # NOTE: test_validation_distribution is intentionally excluded here.
            # It calls release_check.run_release_check itself, so listing it would
            # make release_check recurse into itself. CI runs `unittest discover`
            # (which includes it) as a separate, non-recursive step instead.
            "-v",
        ],
        "project_doctor": ["python3", "scripts/project_doctor.py", "."],
    }

    for name, args in commands.items():
        result = run_command(args, root)
        checks[name] = {
            "returncode": result["returncode"],
            "ok": result["returncode"] == 0,
        }
        if result["returncode"] != 0:
            errors.append(f"{name} failed: {result['stderr'] or result['stdout']}")

    for required_doc in ["docs/release-checklist.md", "docs/upgrade-guide.md"]:
        if not (root / required_doc).exists():
            errors.append(f"Missing release doc: {required_doc}")
        checks[required_doc] = {
            "ok": (root / required_doc).exists(),
        }

    return {
        "schema": "moduflow.release-check.v1",
        "project_root": str(root),
        "valid": not errors,
        "errors": errors,
        "checks": checks,
    }


def main():
    result = run_release_check(sys.argv[1] if len(sys.argv) > 1 else ".")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
