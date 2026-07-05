#!/usr/bin/env python3
import argparse
import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

FETCH_TIMEOUT_SECONDS = 5


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


def _run(runner, args, cwd, timeout=None):
    if timeout is not None:
        return runner(args, cwd, timeout=timeout)
    return runner(args, cwd)


def _stdout(result):
    return (result.stdout or "").strip()


def _parse_rev_counts(text):
    parts = text.replace("\t", " ").split()
    if len(parts) < 2:
        return 0, 0
    try:
        return int(parts[0]), int(parts[1])
    except ValueError:
        return 0, 0


def _current_branch_vv_line(branch_vv, branch):
    for line in branch_vv.splitlines():
        stripped = line.strip()
        if stripped.startswith("* "):
            return stripped
        if branch and stripped.startswith(branch + " "):
            return stripped
    return ""


def _default_remote_branch(runner, cwd):
    result = _run(runner, ["git", "symbolic-ref", "refs/remotes/origin/HEAD"], cwd)
    if result.returncode == 0:
        ref = _stdout(result)
        prefix = "refs/remotes/"
        if ref.startswith(prefix):
            return ref[len(prefix) :]
    return "origin/main"


def _issue_id(path):
    if not path.startswith("issues/") or not path.endswith(".md"):
        return None
    name = path[len("issues/") : -len(".md")]
    return name or None


def _issue_ids_from_paths(paths_text):
    issue_ids = []
    for line in paths_text.splitlines():
        issue_id = _issue_id(line.strip())
        if issue_id:
            issue_ids.append(issue_id)
    return sorted(set(issue_ids))


def inspect_repo_sync(path=".", runner=None):
    cwd = Path(path).resolve()
    runner = runner or run_command
    is_repo = _run(runner, ["git", "rev-parse", "--is-inside-work-tree"], cwd)
    if is_repo.returncode != 0:
        return {
            "schema": "moduflow.repo-sync.v1",
            "project_root": str(cwd),
            "is_repo": False,
            "recommendations": ["Choose a Git repository before running repo sync preflight."],
            "errors": [_stdout(is_repo) or (is_repo.stderr or "").strip()],
        }

    try:
        fetch_result = _run(runner, ["git", "fetch", "--quiet"], cwd, timeout=FETCH_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired:
        fetch_result = CommandResult(124, "", f"git fetch timed out after {FETCH_TIMEOUT_SECONDS}s")
    fetched = fetch_result.returncode == 0
    fetch_warning = None
    if not fetched:
        stderr = (fetch_result.stderr or "").strip()
        fetch_warning = f"git fetch failed: {stderr}" if stderr else "git fetch failed"

    branch_result = _run(runner, ["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd)
    branch = _stdout(branch_result) if branch_result.returncode == 0 else None

    upstream_result = _run(
        runner,
        ["git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"],
        cwd,
    )
    upstream = _stdout(upstream_result) if upstream_result.returncode == 0 else None

    branch_vv_result = _run(runner, ["git", "branch", "-vv"], cwd)
    branch_vv = _stdout(branch_vv_result) if branch_vv_result.returncode == 0 else ""
    branch_line = _current_branch_vv_line(branch_vv, branch)
    upstream_gone = ": gone]" in branch_line or "[gone]" in branch_line

    default_remote = _default_remote_branch(runner, cwd)

    upstream_ahead = 0
    upstream_behind = 0
    if upstream:
        counts = _run(runner, ["git", "rev-list", "--left-right", "--count", f"HEAD...{upstream}"], cwd)
        if counts.returncode == 0:
            upstream_ahead, upstream_behind = _parse_rev_counts(counts.stdout)

    default_remote_behind = 0
    default_remote_ahead = 0
    if default_remote:
        counts = _run(
            runner,
            ["git", "rev-list", "--left-right", "--count", f"HEAD...{default_remote}"],
            cwd,
        )
        if counts.returncode == 0:
            default_remote_behind, default_remote_ahead = _parse_rev_counts(counts.stdout)

    status = _run(runner, ["git", "status", "--porcelain"], cwd)
    dirty = bool(_stdout(status)) if status.returncode == 0 else None

    remote_issues = _run(runner, ["git", "ls-tree", "-r", "--name-only", default_remote, "issues"], cwd)
    local_issues = _run(runner, ["git", "ls-files", "issues"], cwd)
    remote_issue_ids = _issue_ids_from_paths(remote_issues.stdout if remote_issues.returncode == 0 else "")
    local_issue_ids = _issue_ids_from_paths(local_issues.stdout if local_issues.returncode == 0 else "")
    remote_only_issue_ids = sorted(set(remote_issue_ids) - set(local_issue_ids))

    result = {
        "schema": "moduflow.repo-sync.v1",
        "project_root": str(cwd),
        "is_repo": True,
        "fetched": fetched,
        "fetch_warning": fetch_warning,
        "branch": branch,
        "upstream": upstream,
        "upstream_gone": upstream_gone,
        "upstream_ahead": upstream_ahead,
        "upstream_behind": upstream_behind,
        "default_remote": default_remote,
        "default_remote_behind": default_remote_behind,
        "default_remote_ahead": default_remote_ahead,
        "dirty": dirty,
        "remote_only_issue_ids": remote_only_issue_ids,
        "mode_note": "git-files mode stores ModuFlow issues in repo files such as issues/*.md; GitHub Issues objects are optional mirrors.",
    }
    result["recommendations"] = format_recommendations(result)
    return result


def format_recommendations(result):
    recommendations = []
    if not result.get("is_repo"):
        return result.get("recommendations", [])
    if result.get("fetched") is False:
        recommendations.append(
            f"Could not fetch from the remote ({result.get('fetch_warning')}); freshness numbers below reflect the last local fetch, not the current remote."
        )
    if not result.get("upstream"):
        recommendations.append(
            f"Current branch {result.get('branch') or '(unknown)'} has no upstream; compare against the default remote before trusting local artifact state."
        )
    if result.get("upstream_gone"):
        recommendations.append(
            "Current upstream branch is gone; switch to the default branch or choose an active work branch before reading local artifacts."
        )
    if result.get("dirty"):
        recommendations.append(
            "The worktree has local changes; do not auto-fast-forward until those changes are reviewed."
        )
    default_remote_ahead = result.get("default_remote_ahead") or 0
    if default_remote_ahead:
        if result.get("dirty"):
            recommendations.append(
                f"{result.get('default_remote')} is {default_remote_ahead} commits ahead, but the worktree is dirty; review local changes before fast-forward."
            )
        else:
            recommendations.append(
                f"{result.get('default_remote')} is {default_remote_ahead} commits ahead; fast-forward the local branch before status if you want the latest Git-file artifacts."
            )
    if result.get("remote_only_issue_ids"):
        sample = ", ".join(result["remote_only_issue_ids"][:5])
        recommendations.append(
            f"{result.get('default_remote')} has issue files missing locally: {sample}. Refresh the checkout before concluding GitHub work is missing."
        )
    if not recommendations:
        recommendations.append("Repo sync preflight is clean.")
    return recommendations


def main():
    parser = argparse.ArgumentParser(description="Inspect ModuFlow repo sync freshness.")
    parser.add_argument("project_path", nargs="?", default=".")
    args = parser.parse_args()
    print(json.dumps(inspect_repo_sync(args.project_path), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
