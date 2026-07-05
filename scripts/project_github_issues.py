#!/usr/bin/env python3
"""Opt-in one-way sync of a git-file issue to a GitHub Issue (054).

`issues/<id>.md` stays canonical; the GitHub Issue is a synced projection with
a `moduflow:<status>` label. The GitHub issue URL is written back into the
issue file's `## Links` section, which is the create-vs-update discriminator.
"""
import argparse
import json
import re
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.project_sync import run_command
from scripts.project_lifecycle import _issue_status

LABELS = {
    "backlog": "moduflow:backlog",
    "active": "moduflow:active",
    "done": "moduflow:done",
    "superseded": "moduflow:superseded",
}
LABEL_COLORS = {
    "backlog": "ededed",
    "active": "fbca04",
    "done": "0e8a16",
    "superseded": "6f42c1",
}
BODY_MARKER = "<!-- moduflow:issue-sync -->"

SSH_URL_RE = re.compile(r"^git@[^:/]+:([^/]+)/(.+?)(?:\.git)?/?$")
HTTPS_URL_RE = re.compile(r"^https://github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$")
GITHUB_LINK_RE = re.compile(r"^-\s*GitHub:\s*(\S+)\s*$", re.MULTILINE)
ISSUE_NUMBER_RE = re.compile(r"/issues/(\d+)/?$")


def _parse_owner_repo(url):
    for pattern in (SSH_URL_RE, HTTPS_URL_RE):
        m = pattern.match((url or "").strip())
        if m:
            repo = m.group(2)
            # Reject nested paths early so the failure is a clear parse error
            # instead of an opaque gh error from "-R owner/nested/repo".
            if "/" in repo:
                return None
            return f"{m.group(1)}/{repo}"
    return None


def _github_sync_mode(root):
    config_path = Path(root) / ".moduflow" / "config.json"
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except Exception:
        return None
    git_config = config.get("git")
    if not isinstance(git_config, dict):
        return None
    return git_config.get("github_sync")


def _links_section(text):
    lines = text.splitlines()
    start = next((i for i, line in enumerate(lines) if line.strip() == "## Links"), None)
    if start is None:
        return ""
    end = len(lines)
    for i in range(start + 1, len(lines)):
        if lines[i].startswith("## "):
            end = i
            break
    return "\n".join(lines[start + 1:end])


def _github_link(text):
    # The Links section is the only place the mapping is canonical — a stray
    # "- GitHub:" bullet elsewhere must not flip create into update.
    m = GITHUB_LINK_RE.search(_links_section(text))
    return m.group(1) if m else None


def _issue_title(text):
    for line in text.splitlines():
        if line.startswith("# "):
            heading = line[2:].strip()
            if ":" in heading:
                heading = heading.split(":", 1)[1].strip()
            return heading.strip("`").strip()
    return ""


def _outcome_section(text):
    lines = text.splitlines()
    collected = []
    in_outcome = False
    in_fence = False
    for line in lines:
        if line.strip() == "## Outcome":
            in_outcome = True
            continue
        if in_outcome:
            if line.lstrip().startswith("```"):
                in_fence = not in_fence
            # A "## " line inside a code fence is content, not a heading.
            if line.startswith("## ") and not in_fence:
                break
            collected.append(line)
    section = "\n".join(collected).strip()
    if section:
        return section
    # Fallback: first non-heading, non-blank paragraph.
    paragraph = []
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            if paragraph:
                break
            continue
        paragraph.append(stripped)
    return "\n".join(paragraph).strip()


def _issue_body(text, repo, issue_id):
    base = _outcome_section(text)
    return (
        f"{base}\n\n---\n"
        f"Canonical source: https://github.com/{repo}/blob/HEAD/issues/{issue_id}.md\n"
        f"{BODY_MARKER}"
    )


def _write_github_link(path, url):
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    link_line = f"- GitHub: {url}"

    links_idx = next((i for i, line in enumerate(lines) if line.strip() == "## Links"), None)

    # Replace an existing "- GitHub:" bullet inside Links instead of appending
    # a duplicate.
    if links_idx is not None:
        section_end = len(lines)
        for i in range(links_idx + 1, len(lines)):
            if lines[i].startswith("## "):
                section_end = i
                break
        for i in range(links_idx + 1, section_end):
            if GITHUB_LINK_RE.match(lines[i].strip()):
                lines[i] = link_line
                path.write_text("\n".join(lines) + "\n", encoding="utf-8")
                return

    if links_idx is None:
        section = ["## Links", "", link_line, ""]
        next_idx = next(
            (i for i, line in enumerate(lines) if line.strip() == "## Next Command"), None
        )
        if next_idx is None:
            if lines and lines[-1].strip():
                lines.append("")
            lines.extend(["## Links", "", link_line])
        else:
            lines[next_idx:next_idx] = section
    else:
        end = len(lines)
        for i in range(links_idx + 1, len(lines)):
            if lines[i].startswith("## "):
                end = i
                break
        insert = end
        while insert > links_idx + 1 and not lines[insert - 1].strip():
            insert -= 1
        lines.insert(insert, link_line)

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _ensure_labels(runner, cwd, repo):
    result = runner(["gh", "label", "list", "-R", repo, "--json", "name"], cwd)
    if result.returncode != 0:
        return f"gh label list failed: {(result.stderr or '').strip()}"
    try:
        existing = {item.get("name") for item in json.loads(result.stdout or "[]")}
    except json.JSONDecodeError:
        existing = set()
    for status, name in LABELS.items():
        if name in existing:
            continue
        created = runner(
            ["gh", "label", "create", name, "-R", repo, "--color", LABEL_COLORS[status]], cwd
        )
        if created.returncode != 0:
            # "already exists" is success for this idempotent bootstrap — it
            # happens when `gh label list` output couldn't be parsed and we
            # conservatively retried creation.
            if "already exists" in (created.stderr or "").lower():
                continue
            return f"gh label create {name} failed: {(created.stderr or '').strip()}"
    return None


def _error(message, issue_id):
    return {"action": "error", "issue_id": issue_id, "error": message}


def sync_issue(root, issue_id, runner=None):
    root = Path(root).resolve()

    mode = _github_sync_mode(root)
    if mode == "off":
        return {
            "action": "disabled",
            "issue_id": issue_id,
            "reason": "git.github_sync is 'off' in .moduflow/config.json",
        }

    runner = runner or run_command

    issue_path = root / "issues" / f"{issue_id}.md"
    if not issue_path.is_file():
        return _error(f"issue file not found: {issue_path}", issue_id)
    text = issue_path.read_text(encoding="utf-8")

    status = _issue_status(text)
    label = LABELS[status]

    remote = runner(["git", "remote", "get-url", "origin"], root)
    if remote.returncode != 0:
        return _error(f"git remote get-url origin failed: {(remote.stderr or '').strip()}", issue_id)
    repo = _parse_owner_repo((remote.stdout or "").strip())
    if not repo:
        return _error(f"could not parse owner/repo from origin URL: {(remote.stdout or '').strip()}", issue_id)

    label_error = _ensure_labels(runner, root, repo)
    if label_error:
        return _error(label_error, issue_id)

    existing_url = _github_link(text)
    if existing_url:
        number_match = ISSUE_NUMBER_RE.search(existing_url)
        if not number_match:
            return _error(f"could not parse issue number from URL: {existing_url}", issue_id)
        stale = [name for name in LABELS.values() if name != label]
        args = ["gh", "issue", "edit", number_match.group(1), "-R", repo, "--add-label", label]
        for name in stale:
            args.extend(["--remove-label", name])
        edited = runner(args, root)
        if edited.returncode != 0:
            return _error(f"gh issue edit failed: {(edited.stderr or '').strip()}", issue_id)
        return {"action": "updated", "issue_id": issue_id, "url": existing_url, "label": label}

    title = _issue_title(text)
    body = _issue_body(text, repo, issue_id)
    created = runner(
        ["gh", "issue", "create", "-R", repo, "--title", title, "--body", body, "--label", label],
        root,
    )
    if created.returncode != 0:
        return _error(f"gh issue create failed: {(created.stderr or '').strip()}", issue_id)
    stdout_lines = [line.strip() for line in (created.stdout or "").splitlines() if line.strip()]
    if not stdout_lines:
        return _error("gh issue create returned no URL", issue_id)
    url = stdout_lines[-1]
    _write_github_link(issue_path, url)
    return {"action": "created", "issue_id": issue_id, "url": url, "label": label}


def main():
    parser = argparse.ArgumentParser(
        description="Sync a git-file issue to a GitHub Issue (opt-in, one-way)."
    )
    parser.add_argument("project_path", nargs="?", default=".")
    parser.add_argument("--issue-id", required=True)
    parser.add_argument("--sync", action="store_true", help="Create or update the GitHub Issue.")
    args = parser.parse_args()
    if not args.sync:
        parser.error("--sync is required")
    result = sync_issue(args.project_path, args.issue_id)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result.get("action") == "error" else 0


if __name__ == "__main__":
    raise SystemExit(main())
