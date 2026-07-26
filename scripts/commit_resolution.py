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

# `--branches --remotes` rather than a bare `git log`, which walks HEAD only.
# Work on a branch that has not been merged is not reachable from HEAD, so a
# bare log cannot see the very commits this module exists to attribute.
GIT_LOG_ARGS = ("git", "log", "--branches", "--remotes", f"--format={GIT_LOG_FORMAT}")

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


def _same_branch(ref, name):
    """True when two ref names denote the same branch.

    A branch usually exists twice — `codex/X` and `origin/codex/X`. Excluding
    only the exact name lets the counterpart exclude the branch from itself,
    which yields an empty commit set."""
    if ref == name:
        return True
    return _branch_tail(ref) == _branch_tail(name)


def _branch_tail(ref):
    """Strip a remote prefix: origin/codex/X -> codex/X."""
    if "/" in ref and not ref.startswith("codex/"):
        return ref.split("/", 1)[1]
    return ref


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

    all_refs = []
    for line in (result.stdout or "").splitlines():
        name = line.strip().split(" -> ")[0].strip()
        if name:
            all_refs.append(name)

    issue_ids = known_issue_ids(runner, cwd, errors)
    # One owner for branch-name interpretation (GC1) — no second copy here.
    branches = [name for name in all_refs if issue_id_from_branch(name, issue_ids)]

    if not branches:
        degraded.append(DEGRADED_BRANCH_UNAVAILABLE)

    for name in branches:
        # Branch-exclusive commits only: plain `rev-list <branch>` returns every
        # ancestor, i.e. all of the base branch's history.
        #
        # The exclusion is an explicit ref list rather than `--exclude` plus ref
        # globs. `--exclude` applies only to the *next* glob, so
        # `--exclude=<b> --branches --remotes` leaves a remote branch excluded
        # from `--branches` (where it never appeared) and re-included by
        # `--remotes` — the branch excludes itself and the result is empty.
        # That shipped, and made every live-branch commit invisible.
        others = [ref for ref in all_refs if not _same_branch(ref, name)]
        rev_args = ["git", "rev-list", name, "--not", *others]
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
# One attribution index, read by both directions
# ---------------------------------------------------------------------------

def build_attribution(runner, cwd, *, rev_range=None):
    """Attribute every commit in range to at most one issue, once.

    This is the single source both query directions read. Building the index
    rather than answering per commit is what makes parity structural: there is
    no second code path that could resolve the same commit differently.

    Sources are applied in precedence order (GC2):
      trailer        an `Issue:` line in the commit body
      branch         the branch side of a merge naming codex/<issue-id>, or a
                     commit exclusive to a live codex/<issue-id> branch
      merge-subject  the merge commit itself

    Returns {attribution: {sha: {issue_id, source}}, records, order,
    unmatched, degraded, errors}."""
    errors = []
    degraded = []

    if rev_range:
        args = ["git", "log", f"--format={GIT_LOG_FORMAT}", rev_range]
    else:
        args = list(GIT_LOG_ARGS)
    result = _run(runner, args, cwd)
    if result.returncode != 0:
        errors.append(_error_text(args, result))
        return {
            "attribution": {},
            "records": {},
            "order": [],
            "unmatched": [],
            "degraded": degraded,
            "errors": errors,
        }

    records = {}
    order = []
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
        records[sha] = {
            "sha": sha,
            "subject": subject.strip(),
            "parents": parents.split(),
            "body": body,
        }
        order.append(sha)

    attribution = {}

    def claim(sha, issue_id, source):
        current = attribution.get(sha)
        if current is None:
            attribution[sha] = {"issue_id": issue_id, "source": source}
            return
        if SOURCE_PRECEDENCE.index(source) < SOURCE_PRECEDENCE.index(current["source"]):
            attribution[sha] = {"issue_id": issue_id, "source": source}

    for sha in order:
        trailer = TRAILER_RE.search(records[sha]["body"])
        if trailer:
            claim(sha, trailer.group(1), "trailer")

    issue_ids = known_issue_ids(runner, cwd, errors)

    # Merged work: the merge commit delimits exactly what its branch added.
    # Derived from `records`, so it costs no extra subprocess (GC4).
    for sha in order:
        entry = records[sha]
        if len(entry["parents"]) < 2:
            continue
        match = re.search(rf"codex/({ISSUE_ID_PATTERN})", entry["subject"])
        if not match:
            continue
        # Work branches carry suffixes (codex/<id>-<suffix>), and the id
        # pattern would otherwise swallow the suffix. Same disambiguation the
        # branch-name path uses, so both agree on what the id is.
        issue_id = issue_id_from_branch(f"codex/{match.group(1)}", issue_ids)
        if not issue_id:
            continue
        claim(sha, issue_id, "merge-subject")
        for side_sha in branch_side_commits(records, sha):
            claim(side_sha, issue_id, "branch")

    # Live branches have no merge commit to delimit them.
    built = build_branch_membership(runner, cwd)
    errors.extend(built["errors"])
    degraded.extend(built["degraded"])
    for sha, names in built["membership"].items():
        if sha not in records:
            continue
        for name in names:
            issue_id = issue_id_from_branch(name, issue_ids)
            if issue_id:
                claim(sha, issue_id, "branch")

    unmatched = [sha for sha in order if sha not in attribution]
    return {
        "attribution": attribution,
        "records": records,
        "order": order,
        "unmatched": unmatched,
        "degraded": degraded,
        "errors": errors,
    }


# ---------------------------------------------------------------------------
# commit -> issue
# ---------------------------------------------------------------------------

def resolve_issue_for_commit(runner, cwd, sha, *, attribution=None, membership=None, issue_ids=None):
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

    # The trailer is intrinsic to the commit object, so it answers without the
    # index. Everything else is positional and needs the graph.
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

    if attribution is None:
        built = build_attribution(runner, cwd)
        attribution = built["attribution"]
        errors.extend(built["errors"])
        degraded.extend(built["degraded"])

    found = attribution.get(sha)
    if found:
        result["issue_id"] = found["issue_id"]
        result["source"] = found["source"]
        return result

    # Whether branch evidence was consultable is a property of the index, not
    # of this commit, and `build_attribution` already reports it. Probing per
    # commit here reintroduced the fan-out task A2 removed — measured at one
    # `git branch --contains` per unresolved commit. A caller that supplies its
    # own `attribution` reads `degraded` from the same build.
    return result


# ---------------------------------------------------------------------------
# issue -> commits
# ---------------------------------------------------------------------------

def resolve_commits_for_issue(runner, cwd, issue_id, *, rev_range=None, index=None):
    """Resolve every commit linked to issue_id, in git log order.

    Reads the same attribution index as `resolve_issue_for_commit`, so the two
    directions cannot disagree — the parity acceptance criterion is structural
    rather than a property both implementations happen to share.

    Returns {commits: [{sha, subject, source, is_merge}], unmatched_count,
    examined_count, degraded, errors}. `unmatched_count` counts commits in the
    examined range attributed to no issue at all — descriptive, never an
    error (GC5)."""
    built = index or build_attribution(runner, cwd, rev_range=rev_range)
    attribution = built["attribution"]
    records = built["records"]

    commits = []
    for sha in built["order"]:
        found = attribution.get(sha)
        if not found or found["issue_id"] != issue_id:
            continue
        entry = records[sha]
        commits.append(
            {
                "sha": sha,
                "subject": entry["subject"],
                "source": found["source"],
                "is_merge": len(entry["parents"]) >= 2,
            }
        )

    return {
        "commits": commits,
        "unmatched_count": len(built["unmatched"]),
        "examined_count": len(built["order"]),
        "degraded": list(built["degraded"]),
        "errors": list(built["errors"]),
    }
