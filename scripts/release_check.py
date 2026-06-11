#!/usr/bin/env python3
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


def run_release_check(path):
    root = Path(path).resolve()
    checks = {}
    errors = []

    commands = {
        "validate_moduflow": ["python3", "scripts/validate_moduflow.py", "."],
        "tests": [
            "python3",
            "-m",
            "unittest",
            "tests.test_project_migration",
            "tests.test_project_profile",
            "tests.test_project_knowledge",
            "tests.test_project_portfolio",
            "tests.test_project_workflow",
            "-v",
        ],
        "project_doctor": ["python3", "scripts/project_doctor.py", "."],
        "validate_project_artifacts": ["python3", "scripts/validate_project_artifacts.py", "."],
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
