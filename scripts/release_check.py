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


linkage_check = load_script_module("linkage_check", "scripts/linkage_check.py")

DECLARATIONS_RELPATH = "releases/no-issue-declarations.md"


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


def get_modified_python_files(root, runner=None, diff_base=None):
    """Collect modified .py files for targeted lint checks.

    Returns {"files": [Path, ...], "errors": [str, ...]}. Global Constraint 2
    (plan 075): a git failure surfaces as an explicit error entry — it never
    silently degrades to an empty set.
    """
    runner = runner or linkage_check.run_command
    diff_base = diff_base or "main"
    files = set()
    errors = []

    diff_args = ["git", "diff", "--name-only", diff_base]
    diff = runner(diff_args, str(root))
    if diff.returncode != 0:
        errors.append(linkage_check._error_text(diff_args, diff))
    else:
        for line in (diff.stdout or "").splitlines():
            line = line.strip()
            if line.endswith(".py"):
                files.add(root / line)

    status_args = ["git", "status", "--porcelain"]
    status = runner(status_args, str(root))
    if status.returncode != 0:
        errors.append(linkage_check._error_text(status_args, status))
    else:
        for line in (status.stdout or "").splitlines():
            if len(line) > 3:
                path_str = line[3:].strip()
                if path_str.endswith(".py"):
                    files.add(root / path_str)

    return {"files": [p for p in files if p.exists()], "errors": errors}


def run_lint_check(root, runner=None, diff_base=None):
    errors = []
    root = Path(root).resolve()
    modified = get_modified_python_files(root, runner, diff_base)
    errors.extend(modified["errors"])
    for path in sorted(modified["files"]):
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


def resolve_merge_base(root, runner=None):
    """Resolve `git merge-base HEAD origin/main`, fetching main once for
    shallow clones. Returns {"merge_base": sha|None, "errors": [...]}.
    A None merge_base always comes with errors — never a silent pass."""
    runner = runner or linkage_check.run_command
    merge_base_args = ["git", "merge-base", "HEAD", "origin/main"]

    first = runner(merge_base_args, str(root))
    if first.returncode == 0 and (first.stdout or "").strip():
        return {"merge_base": first.stdout.strip(), "errors": []}

    errors = [linkage_check._error_text(merge_base_args, first)]

    fetch_args = ["git", "fetch", "origin", "main", "--depth=200"]
    fetch = runner(fetch_args, str(root))
    if fetch.returncode != 0:
        errors.append(linkage_check._error_text(fetch_args, fetch))

    second = runner(merge_base_args, str(root))
    if second.returncode == 0 and (second.stdout or "").strip():
        # Shallow clone recovered by the fetch: not an error condition.
        return {"merge_base": second.stdout.strip(), "errors": []}
    errors.append(linkage_check._error_text(merge_base_args, second))

    return {"merge_base": None, "errors": errors}


def load_declaration_lines(root):
    """Non-empty, non-heading lines of releases/no-issue-declarations.md.

    Missing file means zero declarations (fine only when nothing is unlinked).
    Returns [{"line_no": int, "text": str}, ...] with 1-based line numbers
    matching git blame."""
    path = Path(root) / DECLARATIONS_RELPATH
    if not path.exists():
        return []
    declarations = []
    for line_no, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        text = raw.strip()
        # Headings, blockquote prose, and format examples in backticks are
        # documentation, not declarations — only bare lines count, so prose
        # can never be mistaken for an approved declaration.
        if not text or text.startswith(("#", ">", "`")):
            continue
        declarations.append({"line_no": line_no, "text": text})
    return declarations


def _declaration_mentions_sha(text, sha):
    for token in text.replace("—", " ").split():
        token = token.strip(",;:()")
        if len(token) >= 7 and sha.startswith(token):
            return True
    return False


def _declaration_mentions_path(text, path):
    for token in text.replace("—", " ").split():
        token = token.strip(",;:()")
        if token == path or (token.endswith("/") and path.startswith(token)):
            return True
    return False


def _commit_covered_by_declarations(entry, valid_declarations):
    """A commit is covered when a valid declaration names its sha, or every
    behavior path is named (exactly or by a directory scope)."""
    texts = [decl["text"] for decl in valid_declarations]
    if any(_declaration_mentions_sha(text, entry["sha"]) for text in texts):
        return True
    if not entry["behavior_paths"]:
        return False
    return all(
        any(_declaration_mentions_path(text, path) for text in texts)
        for path in entry["behavior_paths"]
    )


def run_linkage_gate(root, runner=None):
    """Fail when merge_base..HEAD contains behavior commits that neither link
    to an issue nor carry a valid human no-issue declaration.

    Returns {"ok", "merge_base", "unlinked", "uncovered", "invalid_declarations",
    "errors"}. ok is True only with zero errors (Global Constraint 2)."""
    runner = runner or linkage_check.run_command
    root = Path(root)
    errors = []

    merge_base_result = resolve_merge_base(root, runner)
    merge_base = merge_base_result["merge_base"]
    if merge_base is None:
        return {
            "ok": False,
            "merge_base": None,
            "unlinked": [],
            "uncovered": [],
            "invalid_declarations": [],
            "errors": list(merge_base_result["errors"]),
        }

    linkage = linkage_check.find_unlinked_behavior_commits(runner, root, merge_base, "HEAD")
    errors.extend(linkage["errors"])

    uncovered = []
    invalid_declarations = []
    if linkage["unlinked"]:
        try:
            identities = linkage_check.load_human_identities(root)
        except Exception as exc:
            identities = []
            errors.append(f"failed to load human identities: {exc}")

        valid_declarations = []
        for declaration in load_declaration_lines(root):
            validation = linkage_check.validate_no_issue_declaration(
                runner, root, DECLARATIONS_RELPATH, declaration["line_no"], identities
            )
            if validation["valid"]:
                valid_declarations.append(declaration)
            else:
                invalid_declarations.append(
                    {
                        "line_no": declaration["line_no"],
                        "text": declaration["text"],
                        "reason": validation["reason"],
                    }
                )

        for entry in linkage["unlinked"]:
            if _commit_covered_by_declarations(entry, valid_declarations):
                continue
            uncovered.append(entry)
            errors.append(
                "unlinked behavior commit "
                f"{entry['sha']} has no linked issue and no valid no-issue "
                f"declaration (behavior paths: {', '.join(entry['behavior_paths'])})"
            )
        if uncovered and invalid_declarations:
            for invalid in invalid_declarations:
                errors.append(
                    f"declaration rejected at {DECLARATIONS_RELPATH}:"
                    f"{invalid['line_no']}: {invalid['reason']}"
                )

    return {
        "ok": not errors,
        "merge_base": merge_base,
        "unlinked": linkage["unlinked"],
        "uncovered": uncovered,
        "invalid_declarations": invalid_declarations,
        "errors": errors,
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

    linkage_gate = run_linkage_gate(root)
    checks["linkage_gate"] = {
        "ok": linkage_gate["ok"],
        "merge_base": linkage_gate["merge_base"],
    }
    for err in linkage_gate["errors"]:
        errors.append(f"Linkage: {err}")

    lint_res = run_lint_check(root, diff_base=linkage_gate["merge_base"] or "origin/main")
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
            "tests.test_project_repository_identity",
            "tests.test_project_repository_links",
            "tests.test_project_knowledge",
            "tests.test_project_memory",
            "tests.test_project_portfolio",
            "tests.test_project_workflow",
            "tests.test_project_execution",
            "tests.test_project_pr",
            "tests.test_project_sync",
            "tests.test_github_issue_sync",
            "tests.test_worker_orchestration",
            "tests.test_issue_dependencies",
            "tests.test_codex_personal_install",
            "tests.test_installed_plugin_staleness",
            "tests.test_mcp_server",
            "tests.test_spec_consistency",
            "tests.test_linkage_check",
            "tests.test_release_check",
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
