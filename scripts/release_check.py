#!/usr/bin/env python3
import importlib.util
import json
import re
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


SECRET_RE = re.compile(
    r'(?i)(api_key|secret_key|secret_token|password|auth_token)\s*=\s*["\'][a-z0-9\-_]{8,}["\']',
    re.IGNORECASE
)


def get_modified_python_files(root):
    files = set()
    try:
        out = subprocess.check_output(["git", "diff", "--name-only", "main"], cwd=str(root), text=True)
        for line in out.splitlines():
            line = line.strip()
            if line.endswith(".py"):
                files.add(root / line)
    except Exception:
        pass

    try:
        out = subprocess.check_output(["git", "status", "--porcelain"], cwd=str(root), text=True)
        for line in out.splitlines():
            if len(line) > 3:
                path_str = line[3:].strip()
                if path_str.endswith(".py"):
                    files.add(root / path_str)
    except Exception:
        pass

    return [p for p in files if p.exists()]


def run_lint_check(root):
    errors = []
    root = Path(root).resolve()
    modified_files = get_modified_python_files(root)
    for path in sorted(modified_files):
        path = path.resolve()
        if "__pycache__" in str(path) or ".venv" in str(path) or ".git" in str(path):
            continue
        try:
            content = path.read_text(encoding="utf-8")
            compile(content, str(path), 'exec')
        except SyntaxError as e:
            try:
                rel = path.relative_to(root)
            except ValueError:
                rel = path
            errors.append(f"{rel}: Syntax error at line {e.lineno}: {e.msg}")
        except Exception as e:
            try:
                rel = path.relative_to(root)
            except ValueError:
                rel = path
            errors.append(f"{rel}: Failed to read/parse: {e}")

    return {
        "ok": len(errors) == 0,
        "errors": errors
    }


def run_security_check(root):
    errors = []
    root = Path(root).resolve()
    for path in sorted(root.rglob("*")):
        if path.is_dir() or "__pycache__" in str(path) or ".git" in str(path) or ".venv" in str(path):
            continue
        if path.suffix in {".png", ".jpg", ".jpeg", ".gif", ".pdf", ".pyc", ".db", ".zip", ".tar", ".gz"}:
            continue
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
            for i, line in enumerate(content.splitlines(), 1):
                if SECRET_RE.search(line):
                    if "mock" in line.lower() or "placeholder" in line.lower() or "test_" in line.lower():
                        continue
                    try:
                        rel = path.resolve().relative_to(root)
                    except ValueError:
                        rel = path
                    errors.append(f"{rel}: Potential credential leak at line {i}: {line.strip()}")
        except Exception:
            pass

    return {
        "ok": len(errors) == 0,
        "errors": errors
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

    lint_res = run_lint_check(root)
    checks["lint_check"] = {"ok": lint_res["ok"]}
    if not lint_res["ok"]:
        for err in lint_res["errors"]:
            errors.append(f"Lint: {err}")

    sec_res = run_security_check(root)
    checks["security_check"] = {"ok": sec_res["ok"]}
    if not sec_res["ok"]:
        for err in sec_res["errors"]:
            errors.append(f"Security: {err}")

    version_bump = load_script_module("version_bump", "scripts/version_bump.py")
    bump_res = version_bump.check_bump_applied(root)
    checks["version_bump_gate"] = {"ok": bump_res["ok"]}
    if not bump_res["ok"]:
        errors.extend(bump_res["errors"])

    commands = {
        "tests": [
            "python3",
            "-m",
            "unittest",
            "tests.test_project_migration",
            "tests.test_project_profile",
            "tests.test_project_knowledge",
            "tests.test_project_memory",
            "tests.test_project_portfolio",
            "tests.test_project_workflow",
            "tests.test_project_execution",
            "tests.test_project_pr",
            "tests.test_project_sync",
            "tests.test_github_issue_sync",
            "tests.test_worker_orchestration",
            "tests.test_codex_personal_install",
            "tests.test_installed_plugin_staleness",
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
