#!/usr/bin/env python3
"""Commit-to-issue linkage checking for ModuFlow gates (issue 075, task A1).

Pure importable module: every function takes an injected command runner so
callers (release_check.py, issue 072 hooks, tests) control subprocess access.
Also runnable as a CLI for debugging.

Global Constraint 2 (plan 075): no git subprocess failure is ever swallowed.
Every failure surfaces as an explicit entry in the result dict, and no
function returns a passing/empty result on error.
"""
import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

ISSUE_ID_PATTERN = r"\d{3}-[a-z0-9-]+"
TRAILER_RE = re.compile(rf"^Issue:\s*({ISSUE_ID_PATTERN})\s*$", re.MULTILINE)
BRANCH_ISSUE_RE = re.compile(rf"^codex/({ISSUE_ID_PATTERN})$")

BEHAVIOR_PREFIXES = (
    "scripts/",
    "commands/",
    "skills/",
    "templates/",
    "hooks/",
    ".github/workflows/",
)
BEHAVIOR_FILES = frozenset(
    {
        ".claude-plugin/plugin.json",
        ".codex-plugin/plugin.json",
    }
)

HUMANS_CONFIG_RELPATH = Path(".moduflow") / "humans.json"


@dataclass
class CommandResult:
    returncode: int
    stdout: str
    stderr: str


def _no_prompt_env():
    env = dict(os.environ)
    env["GIT_TERMINAL_PROMPT"] = "0"
    return env


def run_command(args, cwd, timeout=None):
    try:
        result = subprocess.run(
            args,
            cwd=str(cwd),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=timeout,
            env=_no_prompt_env(),
        )
    except FileNotFoundError as exc:
        return CommandResult(127, "", str(exc))
    except subprocess.TimeoutExpired:
        suffix = f" after {timeout}s" if timeout else ""
        return CommandResult(124, "", f"git command timed out{suffix}")
    return CommandResult(result.returncode, result.stdout, result.stderr)


def _run(runner, args, cwd):
    return runner(args, cwd)


def _error_text(args, result):
    detail = (result.stderr or "").strip() or (result.stdout or "").strip()
    detail = detail or f"exit code {result.returncode}"
    return f"{' '.join(args)} failed: {detail}"


def _known_issue_ids(runner, cwd, errors):
    """Issue ids from tracked issues/*.md files, used to disambiguate branch
    names such as codex/075-issue-less-context-capture-gate where the trailing
    segment is a work-branch suffix rather than part of the issue id."""
    args = ["git", "ls-files", "issues"]
    result = _run(runner, args, cwd)
    if result.returncode != 0:
        errors.append(_error_text(args, result))
        return []
    ids = []
    for line in (result.stdout or "").splitlines():
        line = line.strip()
        if line.startswith("issues/") and line.endswith(".md"):
            issue_id = line[len("issues/") : -len(".md")]
            if re.fullmatch(ISSUE_ID_PATTERN, issue_id):
                ids.append(issue_id)
    return ids


def _branch_names(runner, cwd, sha, errors):
    names = []
    for args in (
        ["git", "branch", "-r", "--contains", sha],
        ["git", "branch", "--contains", sha],
    ):
        result = _run(runner, args, cwd)
        if result.returncode != 0:
            errors.append(_error_text(args, result))
            continue
        for line in (result.stdout or "").splitlines():
            name = line.strip()
            if name.startswith("* "):
                name = name[2:].strip()
            # "origin/HEAD -> origin/main" style lines
            name = name.split(" -> ")[0].strip()
            if name:
                names.append(name)
    return names


def _issue_id_from_branch(name, known_issue_ids):
    candidates = [name]
    if "/" in name and not name.startswith("codex/"):
        # remote-qualified names, e.g. origin/codex/074-...
        candidates.append(name.split("/", 1)[1])
    for candidate in candidates:
        match = BRANCH_ISSUE_RE.match(candidate)
        if not match:
            continue
        tail = match.group(1)
        best = None
        for issue_id in known_issue_ids:
            if tail == issue_id or tail.startswith(issue_id + "-"):
                if best is None or len(issue_id) > len(best):
                    best = issue_id
        # No known issue id matched: treat the whole tail as the issue id
        # (codex/<issue-id> with no extra suffix).
        return best or tail
    return None


def resolve_issue_for_commit(runner, cwd, sha):
    """Resolve the issue id linked to a commit.

    Returns {sha, issue_id, source, errors} where source is
    'trailer' | 'branch' | None. Trailer wins over branch on conflict
    (Global Constraint 7)."""
    errors = []
    result = {"sha": sha, "issue_id": None, "source": None, "errors": errors}

    show_args = ["git", "show", "-s", "--format=%B", sha]
    show = _run(runner, show_args, cwd)
    if show.returncode != 0:
        errors.append(_error_text(show_args, show))
        return result

    trailer = TRAILER_RE.search(show.stdout or "")
    if trailer:
        result["issue_id"] = trailer.group(1)
        result["source"] = "trailer"
        return result

    branch_names = _branch_names(runner, cwd, sha, errors)
    matched = [n for n in branch_names if _issue_id_from_branch(n, []) is not None]
    if not matched:
        return result

    known_issue_ids = _known_issue_ids(runner, cwd, errors)
    issue_ids = sorted(
        {
            issue_id
            for issue_id in (
                _issue_id_from_branch(name, known_issue_ids) for name in matched
            )
            if issue_id
        }
    )
    if issue_ids:
        result["issue_id"] = issue_ids[0]
        result["source"] = "branch"
    return result


def classify_changed_paths(paths):
    """Split changed paths into behavior vs neutral. Pure function, no git."""
    behavior = []
    neutral = []
    for path in paths:
        path = path.strip()
        if not path:
            continue
        if path in BEHAVIOR_FILES or path.startswith(BEHAVIOR_PREFIXES):
            behavior.append(path)
        else:
            neutral.append(path)
    return {"behavior": behavior, "neutral": neutral}


def _changed_paths_for_commit(runner, cwd, sha, errors):
    args = ["git", "show", "--name-only", "--format=", sha]
    result = _run(runner, args, cwd)
    if result.returncode != 0:
        errors.append(_error_text(args, result))
        return None
    return [line.strip() for line in (result.stdout or "").splitlines() if line.strip()]


def find_unlinked_behavior_commits(runner, cwd, merge_base, head):
    """Check every commit in merge_base..head that touches behavior paths.

    Returns {ok, commits, unlinked, errors}. ok is True only when there are
    no unlinked behavior commits AND no git errors (no silent pass)."""
    errors = []
    commits = []
    unlinked = []

    rev_list_args = ["git", "rev-list", f"{merge_base}..{head}"]
    rev_list = _run(runner, rev_list_args, cwd)
    if rev_list.returncode != 0:
        errors.append(_error_text(rev_list_args, rev_list))
        return {"ok": False, "commits": commits, "unlinked": unlinked, "errors": errors}

    shas = [line.strip() for line in (rev_list.stdout or "").splitlines() if line.strip()]
    for sha in shas:
        paths = _changed_paths_for_commit(runner, cwd, sha, errors)
        if paths is None:
            continue
        classified = classify_changed_paths(paths)
        if not classified["behavior"]:
            continue
        resolution = resolve_issue_for_commit(runner, cwd, sha)
        errors.extend(resolution["errors"])
        entry = {
            "sha": sha,
            "issue_id": resolution["issue_id"],
            "source": resolution["source"],
            "behavior_paths": classified["behavior"],
        }
        commits.append(entry)
        if entry["issue_id"] is None:
            unlinked.append(entry)

    ok = not errors and not unlinked
    return {"ok": ok, "commits": commits, "unlinked": unlinked, "errors": errors}


def _parse_blame_porcelain(text):
    author_name = None
    author_email = None
    for line in (text or "").splitlines():
        if line.startswith("author "):
            author_name = line[len("author ") :].strip()
        elif line.startswith("author-mail "):
            author_email = line[len("author-mail ") :].strip().strip("<>")
    return author_name, author_email


def validate_no_issue_declaration(runner, cwd, file_path, line_no, human_identities):
    """Validate that a declaration line was authored by a configured human.

    Returns {valid, author_name, author_email, reason}. Fails closed: git
    errors, unknown authors, and an empty identity list are all invalid."""
    args = [
        "git",
        "blame",
        "-L",
        f"{line_no},{line_no}",
        "--line-porcelain",
        str(file_path),
    ]
    blame = _run(runner, args, cwd)
    if blame.returncode != 0:
        return {
            "valid": False,
            "author_name": None,
            "author_email": None,
            "reason": _error_text(args, blame),
        }

    author_name, author_email = _parse_blame_porcelain(blame.stdout)
    if not human_identities:
        return {
            "valid": False,
            "author_name": author_name,
            "author_email": author_email,
            "reason": "no configured human identities (.moduflow/humans.json missing or empty)",
        }

    for identity in human_identities:
        name = (identity or {}).get("name")
        email = (identity or {}).get("email")
        if (name and author_name and name == author_name) or (
            email and author_email and email == author_email
        ):
            return {
                "valid": True,
                "author_name": author_name,
                "author_email": author_email,
                "reason": None,
            }

    return {
        "valid": False,
        "author_name": author_name,
        "author_email": author_email,
        "reason": (
            f"blame author {author_name!r} <{author_email}> does not match any "
            "configured human identity"
        ),
    }


def load_human_identities(cwd):
    """Read .moduflow/humans.json. Missing file returns [] — callers must
    treat an empty list as 'no valid declarations possible', never as pass.
    Malformed JSON raises (loud failure, never a silent pass)."""
    config_path = Path(cwd) / HUMANS_CONFIG_RELPATH
    if not config_path.exists():
        return []
    data = json.loads(config_path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and isinstance(data.get("humans"), list):
        return data["humans"]
    raise ValueError(
        f"{config_path}: expected a JSON list of identities "
        '(or {"humans": [...]})'
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description="ModuFlow commit-to-issue linkage checks (debug CLI).")
    parser.add_argument("--cwd", default=".", help="Repository path (default: current directory).")
    sub = parser.add_subparsers(dest="command", required=True)

    p_resolve = sub.add_parser("resolve", help="Resolve the issue linked to a commit.")
    p_resolve.add_argument("sha")

    p_classify = sub.add_parser("classify", help="Classify paths as behavior/neutral.")
    p_classify.add_argument("paths", nargs="+")

    p_unlinked = sub.add_parser("unlinked", help="Find unlinked behavior commits in merge_base..head.")
    p_unlinked.add_argument("merge_base")
    p_unlinked.add_argument("head")

    p_declare = sub.add_parser("validate-declaration", help="Blame-validate a no-issue declaration line.")
    p_declare.add_argument("file_path")
    p_declare.add_argument("line_no", type=int)

    args = parser.parse_args(argv)
    cwd = Path(args.cwd).resolve()

    if args.command == "resolve":
        result = resolve_issue_for_commit(run_command, cwd, args.sha)
    elif args.command == "classify":
        result = classify_changed_paths(args.paths)
    elif args.command == "unlinked":
        result = find_unlinked_behavior_commits(run_command, cwd, args.merge_base, args.head)
    else:
        identities = load_human_identities(cwd)
        result = validate_no_issue_declaration(
            run_command, cwd, args.file_path, args.line_no, identities
        )

    print(json.dumps(result, ensure_ascii=False, indent=2))
    failed = bool(result.get("errors")) or result.get("ok") is False or result.get("valid") is False
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
