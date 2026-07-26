#!/usr/bin/env python3
"""Shared commit-to-issue resolution for ModuFlow gates (issue 095, stream A).

Before this module, two consumers answered "which issue owns this commit?" with
different rules in opposite directions:

    linkage_check.resolve_issue_for_commit   commit -> issue   trailer, branch
    project_converge.resolve_commits         issue  -> commits trailer, merge-subject

Neither was a superset of the other, so a commit reachable only through its
branch name was invisible to converge — measured at 10 collected against 53
resolvable on issue 093's history, with an empty error list.

This module owns the rules, the precedence order, and the git access strategy
for both directions. Consumers delegate; they do not reimplement.

Plan 095 Global Constraints honored here:
  GC1  sole owner of trailer, branch, merge-subject matching and precedence
  GC2  precedence is exactly trailer > branch > merge-subject
  GC3  the trailer format and codex/<issue-id> convention are unchanged
  GC4  branch membership is built once per invocation, never per commit
  GC5  unmatched_count is descriptive; it never populates errors
  GC8  degraded resolution is reported, never raised

Every function takes an injected runner so callers control subprocess access.
No git failure is swallowed: failures surface in the result's `errors` list.
"""
import re

ISSUE_ID_PATTERN = r"\d{3}-[a-z0-9-]+"
TRAILER_RE = re.compile(rf"^Issue:\s*({ISSUE_ID_PATTERN})\s*$", re.MULTILINE)
BRANCH_ISSUE_RE = re.compile(rf"^codex/({ISSUE_ID_PATTERN})$")

# NUL-separated fields, \x01-terminated records: sha, subject, parents, body.
GIT_LOG_FORMAT = "%H%x00%s%x00%P%x00%B%x01"

# GC2. Highest first. A commit matching several sources is recorded once, at
# the highest that matched.
SOURCE_PRECEDENCE = ("trailer", "branch", "merge-subject")

DEGRADED_BRANCH_UNAVAILABLE = "branch-unavailable"


def _run(runner, args, cwd):
    return runner(list(args), cwd)


def _error_text(args, result):
    detail = (result.stderr or "").strip() or (result.stdout or "").strip()
    detail = detail or f"exit code {result.returncode}"
    return f"{' '.join(args)} failed: {detail}"


# ---------------------------------------------------------------------------
# Branch-name interpretation
# ---------------------------------------------------------------------------

def known_issue_ids(runner, cwd, errors):
    """Issue ids from tracked issues/*.md, used to disambiguate branch names
    such as codex/075-issue-less-context-capture-gate where the trailing
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


def issue_id_from_branch(name, issue_ids):
    """Extract an issue id from a branch name, or None.

    Accepts remote-qualified names (origin/codex/094-...). When a work-branch
    suffix is present, the longest known issue id that prefixes the tail wins;
    with no known ids the whole tail is treated as the issue id."""
    candidates = [name]
    if "/" in name and not name.startswith("codex/"):
        candidates.append(name.split("/", 1)[1])
    for candidate in candidates:
        match = BRANCH_ISSUE_RE.match(candidate)
        if not match:
            continue
        tail = match.group(1)
        best = None
        for issue_id in issue_ids:
            if tail == issue_id or tail.startswith(issue_id + "-"):
                if best is None or len(issue_id) > len(best):
                    best = issue_id
        return best or tail
    return None


def branch_side_commits(records, merge_sha):
    """Commits contributed by the branch side of a merge commit.

    Walks the second-parent side of `merge_sha` and subtracts everything
    reachable from the first parent — the graph equivalent of
    `git rev-list <merge>^2 --not <merge>^1`, computed from the log records
    already in hand so it costs no extra subprocess (GC4).

    Containment alone is the wrong rule and measurably so: on issue 093,
    `git rev-list <branch>` yields 279 commits because a branch cut from main
    has all of main as ancestors, while the branch actually contributed 52.
    `--not main` is not a substitute either — after the merge it yields 0."""
    parents = records.get(merge_sha, {}).get("parents", [])
    if len(parents) < 2:
        return set()

    def reachable(start):
        seen = set()
        stack = [start]
        while stack:
            sha = stack.pop()
            if sha in seen or sha not in records:
                continue
            seen.add(sha)
            stack.extend(records[sha].get("parents", []))
        return seen

    mainline = reachable(parents[0])
    return reachable(parents[1]) - mainline


def build_branch_membership(runner, cwd):
    """Map every commit sha to the branch names that contain it.

    Used for commits on a branch that has not been merged yet, where no merge
    commit exists to delimit the branch's contribution. For merged work use
    `branch_side_commits`, which is both cheaper and correct.

    GC4: one `git for-each-ref` plus one `git rev-list` per issue-shaped
    branch — bounded by branch count, never by history length. This replaces
    the previous per-commit `git branch --contains` fan-out.

    Returns {membership: {sha: [branch_name, ...]}, branches: [...],
    degraded: [...], errors: [...]}."""
    errors = []
    degraded = []
    membership = {}

    args = [
        "git",
        "for-each-ref",
        "--format=%(refname:short)",
        "refs/heads",
        "refs/remotes",
    ]
    result = _run(runner, args, cwd)
    if result.returncode != 0:
        errors.append(_error_text(args, result))
        return {
            "membership": {},
            "branches": [],
            "degraded": [DEGRADED_BRANCH_UNAVAILABLE],
            "errors": errors,
        }

    branches = []
    for line in (result.stdout or "").splitlines():
        name = line.strip().split(" -> ")[0].strip()
        if name and BRANCH_ISSUE_RE.match(name.split("/", 1)[1] if "/" in name and not name.startswith("codex/") else name):
            branches.append(name)

    if not branches:
        degraded.append(DEGRADED_BRANCH_UNAVAILABLE)

    for name in branches:
        # Branch-exclusive commits only. Plain `rev-list <branch>` would return
        # every ancestor, i.e. all of the base branch's history.
        rev_args = ["git", "rev-list", name, "--not", "--exclude=" + name, "--branches", "--remotes"]
        rev = _run(runner, rev_args, cwd)
        if rev.returncode != 0:
            errors.append(_error_text(rev_args, rev))
            continue
        for sha in (rev.stdout or "").split():
            membership.setdefault(sha, []).append(name)

    return {
        "membership": membership,
        "branches": branches,
        "degraded": degraded,
        "errors": errors,
    }


# ---------------------------------------------------------------------------
# commit -> issue
# ---------------------------------------------------------------------------

def resolve_issue_for_commit(runner, cwd, sha, *, membership=None, issue_ids=None):
    """Resolve the issue id linked to one commit.

    Pass `membership` (from build_branch_membership) when resolving many
    commits so branch lookup stays a dict read instead of a subprocess.

    Returns {sha, issue_id, source, degraded, errors} where source is
    'trailer' | 'branch' | 'merge-subject' | None."""
    errors = []
    degraded = []
    result = {
        "sha": sha,
        "issue_id": None,
        "source": None,
        "degraded": degraded,
        "errors": errors,
    }

    show_args = ["git", "show", "-s", "--format=%B%x00%s%x00%P", sha]
    show = _run(runner, show_args, cwd)
    if show.returncode != 0:
        errors.append(_error_text(show_args, show))
        return result

    parts = (show.stdout or "").split("\x00")
    body = parts[0] if parts else ""
    subject = parts[1].strip() if len(parts) > 1 else ""
    parents = parts[2] if len(parts) > 2 else ""
    is_merge = len(parents.split()) >= 2

    trailer = TRAILER_RE.search(body)
    if trailer:
        result["issue_id"] = trailer.group(1)
        result["source"] = "trailer"
        return result

    if membership is None:
        built = build_branch_membership(runner, cwd)
        membership = built["membership"]
        errors.extend(built["errors"])
        degraded.extend(built["degraded"])

    if issue_ids is None:
        issue_ids = known_issue_ids(runner, cwd, errors)

    names = membership.get(sha, [])
    resolved = sorted(
        {
            issue_id
            for issue_id in (issue_id_from_branch(name, issue_ids) for name in names)
            if issue_id
        }
    )
    if resolved:
        result["issue_id"] = resolved[0]
        result["source"] = "branch"
        return result

    if is_merge:
        for issue_id in issue_ids or []:
            if f"codex/{issue_id}" in subject:
                result["issue_id"] = issue_id
                result["source"] = "merge-subject"
                return result
        match = re.search(rf"codex/({ISSUE_ID_PATTERN})", subject)
        if match:
            result["issue_id"] = match.group(1)
            result["source"] = "merge-subject"
            return result

    if not names and DEGRADED_BRANCH_UNAVAILABLE not in degraded:
        # Nothing matched and no branch contained this commit. Say so rather
        # than letting an unresolvable branch-only commit look like a commit
        # that genuinely belongs to no issue (GC8).
        degraded.append(DEGRADED_BRANCH_UNAVAILABLE)

    return result


# ---------------------------------------------------------------------------
# issue -> commits
# ---------------------------------------------------------------------------

def resolve_commits_for_issue(runner, cwd, issue_id, *, rev_range=None):
    """Resolve every commit linked to issue_id, in git log order.

    Returns {commits: [{sha, subject, source, is_merge}], unmatched_count,
    examined_count, degraded, errors}. `unmatched_count` counts commits in the
    examined range that matched no issue — descriptive, never an error (GC5)."""
    errors = []
    degraded = []

    args = ["git", "log", f"--format={GIT_LOG_FORMAT}"]
    if rev_range:
        args.append(rev_range)
    result = _run(runner, args, cwd)
    if result.returncode != 0:
        errors.append(_error_text(args, result))
        return {
            "commits": [],
            "unmatched_count": 0,
            "examined_count": 0,
            "degraded": degraded,
            "errors": errors,
        }

    built = build_branch_membership(runner, cwd)
    membership = built["membership"]
    errors.extend(built["errors"])
    degraded.extend(built["degraded"])
    issue_ids = known_issue_ids(runner, cwd, errors)

    branch_token = f"codex/{issue_id}"
    by_sha = {}
    order = []
    examined = 0
    unmatched = 0

    records = {}
    parsed = []
    for record in (result.stdout or "").split("\x01"):
        record = record.strip("\n")
        if not record.strip():
            continue
        parts = record.split("\x00")
        if len(parts) != 4:
            errors.append(
                f"git log produced a malformed record (expected 4 fields, "
                f"got {len(parts)}): {record[:80]!r}"
            )
            continue
        sha, subject, parents, body = parts
        sha = sha.strip()
        entry = {
            "sha": sha,
            "subject": subject.strip(),
            "parents": parents.split(),
            "body": body,
        }
        records[sha] = entry
        parsed.append(entry)

    # Merged work: the merge commit delimits exactly what the branch added.
    # Computed from `records`, so this costs no extra subprocess (GC4).
    merged_side = set()
    for entry in parsed:
        if len(entry["parents"]) >= 2 and branch_token in entry["subject"]:
            merged_side |= branch_side_commits(records, entry["sha"])

    for entry in parsed:
        sha = entry["sha"]
        subject = entry["subject"]
        body = entry["body"]
        is_merge = len(entry["parents"]) >= 2
        examined += 1

        source = None
        trailer = TRAILER_RE.search(body)
        if trailer:
            if trailer.group(1) == issue_id:
                source = "trailer"
            else:
                continue  # belongs to another issue; not unmatched
        if source is None:
            names = membership.get(sha, [])
            branch_issues = {
                candidate
                for candidate in (
                    issue_id_from_branch(name, issue_ids) for name in names
                )
                if candidate
            }
            if issue_id in branch_issues or sha in merged_side:
                source = "branch"
            elif is_merge and branch_token in subject:
                source = "merge-subject"

        if source is None:
            unmatched += 1
            continue

        if sha in by_sha:
            existing = by_sha[sha]["source"]
            if SOURCE_PRECEDENCE.index(source) < SOURCE_PRECEDENCE.index(existing):
                by_sha[sha]["source"] = source
            continue

        by_sha[sha] = {
            "sha": sha,
            "subject": subject,
            "source": source,
            "is_merge": is_merge,
        }
        order.append(sha)

    return {
        "commits": [by_sha[sha] for sha in order],
        "unmatched_count": unmatched,
        "examined_count": examined,
        "degraded": degraded,
        "errors": errors,
    }
