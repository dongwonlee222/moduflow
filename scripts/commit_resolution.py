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
import importlib.util
import sys
from pathlib import Path

try:  # Works both as `scripts.commit_resolution` and a direct script import.
    from . import commit_graph
except ImportError:  # pragma: no cover - exercised by direct script consumers.
    graph_path = Path(__file__).resolve().with_name("commit_graph.py")
    module_key = "_moduflow_commit_graph"
    existing = sys.modules.get(module_key)
    if (
        existing is not None
        and Path(getattr(existing, "__file__", "")).resolve() == graph_path
    ):
        commit_graph = existing
    else:
        spec = importlib.util.spec_from_file_location(
            module_key, graph_path
        )
        commit_graph = importlib.util.module_from_spec(spec)
        sys.modules[module_key] = commit_graph
        spec.loader.exec_module(commit_graph)

ISSUE_ID_PATTERN = r"\d{3}-[a-z0-9-]+"
TRAILER_RE = re.compile(rf"^Issue:\s*({ISSUE_ID_PATTERN})\s*$", re.MULTILINE)
BRANCH_ISSUE_RE = re.compile(rf"^codex/({ISSUE_ID_PATTERN})$")

# Re-exported for callers during the graph-snapshot migration.
GIT_LOG_FORMAT = commit_graph.GIT_LOG_FORMAT
GIT_LOG_ARGS = commit_graph.GIT_LOG_ARGS
BRANCH_REF_ARGS = commit_graph.BRANCH_REF_ARGS
ORIGIN_HEAD_ARGS = (
    "git",
    "symbolic-ref",
    "--quiet",
    "--short",
    "refs/remotes/origin/HEAD",
)
ISSUE_HISTORY_ARGS = (
    "git",
    "log",
    "--all",
    "--name-only",
    "--format=",
    "--",
    "issues",
)

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
    """Issue ids ever registered in reachable Git history.

    The current index is checkout-dependent and loses deleted issue files.
    History is the registry: an issue remains registered after archival and
    while another branch is checked out.
    """
    args = list(ISSUE_HISTORY_ARGS)
    result = _run(runner, args, cwd)
    if result.returncode != 0:
        errors.append(_error_text(args, result))
        return []
    ids = set()
    for line in (result.stdout or "").splitlines():
        line = line.strip()
        if line.startswith("issues/") and line.endswith(".md"):
            issue_id = line[len("issues/") : -len(".md")]
            if re.fullmatch(ISSUE_ID_PATTERN, issue_id):
                ids.add(issue_id)
    return sorted(ids)


def issue_id_from_branch(name, issue_ids):
    """Extract an issue id from a branch name, or None.

    Accepts remote-qualified names (origin/codex/094-...). When a work-branch
    suffix is present, the longest known issue id that prefixes the tail wins.
    A branch name never registers an issue by itself."""
    branch_name = _branch_tail(name)
    candidates = [name, branch_name]
    if (
        branch_name == name
        and "/" in name
        and not name.startswith("codex/")
    ):
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
        if best:
            return best
        return None
    return None


def _merge_source_text(subject):
    """The part of a merge subject naming what was merged *from*."""
    return subject.split(" into ")[0] if " into " in subject else subject


def merge_source_issue(subject, issue_ids):
    """The issue whose branch a merge commit merged *from*, or None.

    Direction matters and the subject carries it:

      Merge branch 'codex/X'                -> X    (X merged in)
      Merge pull request #9 from o/codex/X  -> X    (X merged in)
      Merge branch 'main' into codex/X      -> None (main merged into X)

    A sync merge names the issue while merging the base branch *into* the
    branch, so its second-parent side is the base branch's history. Claiming
    it attributes all of main to the issue — measured live in this repository,
    where issue 081's merge commit landed inside issue 093's evidence."""
    source = _merge_source_text(subject)
    match = re.search(rf"codex/({ISSUE_ID_PATTERN})", source)
    if not match:
        return None
    return issue_id_from_branch(f"codex/{match.group(1)}", issue_ids)


def base_ref(runner, cwd, refs, issue_ids=None, errors=None):
    """The branch other branches are cut from.

    A branch's own contribution is what it has that the base does not. Deriving
    it by excluding every *other* ref instead makes any unmerged descendant
    branch zero its parent, and leaves nothing to exclude at all in a
    single-branch clone.

    Asked of the repository rather than guessed from a list of names. A name
    list gets two cases wrong that this does not: a trunk called something else
    (`develop`), and a local `main` left behind `origin/main`, where measuring
    against the stale one hands the branch every commit the trunk has moved on
    by."""
    errors = errors if errors is not None else []
    issue_ids = issue_ids or []
    candidates = [
        ref for ref in refs if BRANCH_ISSUE_RE.match(_branch_tail(ref)) is None
    ]
    issue_refs = [
        ref for ref in refs if issue_id_from_branch(ref, issue_ids) is not None
    ]

    if issue_refs:
        connected = []
        for ref in candidates:
            usable = True
            for issue_ref in issue_refs:
                merge_args = ["git", "merge-base", ref, issue_ref]
                probe = _run(runner, merge_args, cwd)
                if probe.returncode == 1:
                    usable = False
                    break
                if probe.returncode != 0:
                    errors.append(_error_text(merge_args, probe))
                    return None
            if usable:
                connected.append(ref)
        candidates = connected

    head_args = list(ORIGIN_HEAD_ARGS)
    head = _run(runner, head_args, cwd)
    if head.returncode == 0:
        name = (head.stdout or "").strip()
        if not name.startswith("refs/"):
            name = f"refs/remotes/{name}"
        if name in candidates:
            return name
    elif head.returncode != 1:
        errors.append(_error_text(head_args, head))
        return None

    # A local and remote-tracking ref usually denote the same branch. Score
    # that branch once, using the remote counterpart when the local ref is
    # stale. Otherwise the stale local trunk becomes the base and every commit
    # by which origin moved ahead is handed to each issue branch.
    by_tail = {}
    for ref in candidates:
        by_tail.setdefault(_branch_tail(ref), []).append(ref)

    candidates = []
    for tail in sorted(by_tail):
        counterparts = sorted(by_tail[tail])
        if len(counterparts) == 1 or not issue_refs:
            candidates.append(counterparts[0])
            continue

        ancestor_cache = {}

        def is_ancestor(older, newer):
            key = (older, newer)
            if key in ancestor_cache:
                return ancestor_cache[key]
            merge_args = [
                "git",
                "merge-base",
                "--is-ancestor",
                older,
                newer,
            ]
            probe = _run(runner, merge_args, cwd)
            if probe.returncode == 0:
                ancestor_cache[key] = True
                return True
            if probe.returncode == 1:
                ancestor_cache[key] = False
                return False
            errors.append(_error_text(merge_args, probe))
            return None

        eligible = []
        for counterpart in counterparts:
            relations = [
                is_ancestor(counterpart, issue_ref)
                for issue_ref in issue_refs
            ]
            if any(relation is None for relation in relations):
                return None
            if all(relations):
                eligible.append(counterpart)

        maximal = []
        for counterpart in eligible:
            relations = [
                is_ancestor(other, counterpart)
                for other in eligible
                if other != counterpart
            ]
            if any(relation is None for relation in relations):
                return None
            if all(relations):
                maximal.append(counterpart)

        if len(maximal) == 1:
            candidates.append(maximal[0])
            continue

        if maximal:
            first = maximal[0]
            equivalent = [
                is_ancestor(first, other)
                and is_ancestor(other, first)
                for other in maximal[1:]
            ]
            if any(relation is None for relation in equivalent):
                return None
            if all(equivalent):
                candidates.append(sorted(maximal)[0])
                continue

        errors.append(
            f"same-tail local/remote base refs for {tail} are ambiguous: "
            f"{', '.join(counterparts)}"
        )
        return None

    # Fall back to the ref contributing the fewest commits no other ref has. A
    # trunk is contained in the branches cut from it and so contributes nothing
    # unique; a topic branch contributes its own work.
    # Ties are the common case — in stacked work both the trunk and the lower
    # branch contribute nothing unique. Break them by containment: a trunk is
    # an ancestor of everything cut from it, a lower branch only of what sits
    # on top. Picking wrong here silently zeroes a branch.
    scored = []
    relevant_refs = list(dict.fromkeys([*issue_refs, *candidates]))
    for ref in candidates:
        others = [
            other for other in relevant_refs if not _same_branch(other, ref)
        ]
        if not others:
            continue
        rev = _run(runner, ["git", "rev-list", ref, "--not", *others], cwd)
        if rev.returncode != 0:
            errors.append(
                _error_text(["git", "rev-list", ref, "--not", *others], rev)
            )
            return None
        exclusive = len((rev.stdout or "").split())
        contained_in = 0
        for other in others:
            merge_args = ["git", "merge-base", "--is-ancestor", ref, other]
            probe = _run(runner, merge_args, cwd)
            if probe.returncode == 0:
                contained_in += 1
            elif probe.returncode not in (0, 1):
                errors.append(_error_text(merge_args, probe))
                return None
        scored.append((exclusive, -contained_in, ref))
    if not scored:
        return None
    scored.sort()
    return scored[0][2]


def _same_branch(ref, name):
    """True when two ref names denote the same branch.

    A branch usually exists twice — `codex/X` and `origin/codex/X`. Excluding
    only the exact name lets the counterpart exclude the branch from itself,
    which yields an empty commit set."""
    if ref == name:
        return True
    if not (
        ref.startswith(("refs/heads/", "refs/remotes/"))
        and name.startswith(("refs/heads/", "refs/remotes/"))
    ):
        return False
    return _branch_tail(ref) == _branch_tail(name)


def _branch_tail(ref):
    """Return a branch name while preserving local-vs-remote provenance."""
    if ref.startswith("refs/heads/"):
        return ref[len("refs/heads/") :]
    if ref.startswith("refs/remotes/"):
        remote_and_branch = ref[len("refs/remotes/") :]
        if "/" in remote_and_branch:
            return remote_and_branch.split("/", 1)[1]
    return ref


def _short_ref(ref):
    """Render a full ref using Git's familiar short spelling."""
    if ref.startswith("refs/heads/"):
        return ref[len("refs/heads/") :]
    if ref.startswith("refs/remotes/"):
        return ref[len("refs/remotes/") :]
    return ref


def merge_side_commits(records, merge_sha, parent_index):
    """Commits contributed by one non-first parent of a merge.

    An octopus merge has three or more parents. Walking only `^2` loses every
    branch past the second — the second independent review measured an entire
    issue's work attributed to nothing that way."""
    parents = records.get(merge_sha, {}).get("parents", [])
    if parent_index >= len(parents):
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
    return reachable(parents[parent_index]) - mainline


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


def build_branch_membership(runner, cwd, *, issue_ids=None, refs=None, snapshot=None):
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
    diagnostics = []

    if snapshot is None:
        snapshot = commit_graph.load_snapshot(runner, cwd)
        if snapshot["fatal_errors"]:
            return {
                "membership": {},
                "branches": [],
                "ref_tips": {},
                "degraded": [DEGRADED_BRANCH_UNAVAILABLE],
                "errors": list(snapshot["fatal_errors"]),
                "diagnostics": [],
            }
    ref_tips = dict(refs if refs is not None else snapshot["refs"])
    all_refs = list(ref_tips)

    if issue_ids is None:
        issue_ids = known_issue_ids(runner, cwd, errors)
    # One owner for branch-name interpretation (GC1) — no second copy here.
    branches = [name for name in all_refs if issue_id_from_branch(name, issue_ids)]

    # Note what is NOT degraded: having no issue-shaped branch at all. Nothing
    # was unavailable there — the repository simply has none, and every merged
    # branch still resolves through merge topology. Firing here made the flag
    # true of most healthy repositories, which is how it came to mean nothing.

    topic_refs = {
        name: issue_id_from_branch(name, issue_ids) for name in branches
    }
    base_refs = [name for name in all_refs if name not in topic_refs]
    # Local and remote refs to the same object are one topic observation. A
    # same-issue ref at another object remains distinct, so its ambiguity is
    # contained to that issue's graph result rather than silently discarded.
    representatives = {}
    for name in sorted(branches):
        key = (topic_refs[name], ref_tips[name])
        representatives.setdefault(key, name)

    fatal_before = len(snapshot["fatal_errors"])
    for (_issue_id, _tip), name in sorted(representatives.items()):
        delta = commit_graph.topic_delta(
            runner,
            cwd,
            snapshot,
            name,
            topic_refs[name],
            topic_refs=topic_refs,
            base_refs=base_refs,
        )
        diagnostics.extend(delta["diagnostics"])
        if delta["fork_point"] is None:
            if DEGRADED_BRANCH_UNAVAILABLE not in degraded:
                degraded.append(DEGRADED_BRANCH_UNAVAILABLE)
            continue
        for sha in delta["commits"]:
            membership.setdefault(sha, []).append(_short_ref(name))
    if len(snapshot["fatal_errors"]) != fatal_before:
        errors.extend(snapshot["fatal_errors"][fatal_before:])
        if DEGRADED_BRANCH_UNAVAILABLE not in degraded:
            degraded.append(DEGRADED_BRANCH_UNAVAILABLE)
    for item in diagnostics:
        message = item["message"]
        if item["code"] == "ambiguous-topic-fork":
            message = f"remote topic fork ambiguity: {message}"
        if message not in errors:
            errors.append(message)

    return {
        "membership": membership,
        "branches": [_short_ref(name) for name in branches],
        "ref_tips": ref_tips,
        "degraded": degraded,
        "errors": errors,
        "diagnostics": diagnostics,
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

    snapshot = commit_graph.load_snapshot(runner, cwd, rev_range=rev_range)
    graph_errors = snapshot["fatal_errors"]
    errors.extend(graph_errors)
    if graph_errors:
        return {
            "attribution": {},
            "records": {},
            "order": [],
            "unmatched": [],
            "degraded": degraded,
            "errors": errors,
            "diagnostics": [],
        }
    records = snapshot["records"]
    order = snapshot["order"]

    issue_ids = known_issue_ids(runner, cwd, errors)
    built = build_branch_membership(
        runner,
        cwd,
        issue_ids=issue_ids,
        refs=snapshot["refs"],
        snapshot=snapshot,
    )
    errors.extend(built["errors"])
    degraded.extend(built["degraded"])
    diagnostics = list(built.get("diagnostics", []))

    # sha -> {issue_id: source}. Content has one owner. Merge boundaries can
    # legitimately touch several issues and retain one claim per issue.
    attribution = {}

    def claim(sha, issue_id, source):
        if issue_id not in issue_ids:
            return
        per_issue = attribution.setdefault(sha, {})

        if len(records[sha]["parents"]) < 2:
            if not per_issue:
                per_issue[issue_id] = source
                return
            _, current_source = next(iter(per_issue.items()))
            if (
                SOURCE_PRECEDENCE.index(source)
                < SOURCE_PRECEDENCE.index(current_source)
            ):
                per_issue.clear()
                per_issue[issue_id] = source
            # Equal evidence keeps the earlier claim. Merge records are walked
            # inner-first below, so an outer branch cannot relabel content
            # already owned by the inner issue.
            return

        current = per_issue.get(issue_id)
        if current is None or SOURCE_PRECEDENCE.index(source) < SOURCE_PRECEDENCE.index(current):
            per_issue[issue_id] = source

    for sha in order:
        trailer = TRAILER_RE.search(records[sha]["body"])
        if trailer:
            claim(sha, trailer.group(1), "trailer")

    # Merged work: the merge commit delimits exactly what its branch added.
    # Derived from `records`, so it costs no extra subprocess (GC4). Git's
    # default log order is date-based and is not reliably topological when
    # fixtures (or rebases) give several commits the same timestamp. Walk the
    # record graph parents-first so nested/inner merges always claim first.
    graph_order = []
    visit_state = {}

    for sha in order:
        if visit_state.get(sha) == 2:
            continue
        stack = [(sha, False)]
        while stack:
            current, expanded = stack.pop()
            if current not in records:
                continue
            if expanded:
                if visit_state.get(current) != 2:
                    visit_state[current] = 2
                    graph_order.append(current)
                continue
            if visit_state.get(current):
                continue
            visit_state[current] = 1
            stack.append((current, True))
            for parent in reversed(records[current]["parents"]):
                if visit_state.get(parent) != 2:
                    stack.append((parent, False))

    for sha in graph_order:
        entry = records[sha]
        if len(entry["parents"]) < 2:
            continue
        named = [
            issue_id_from_branch(f"codex/{m}", issue_ids)
            for m in re.findall(rf"codex/({ISSUE_ID_PATTERN})", _merge_source_text(entry["subject"]))
        ]
        named = [i for i in named if i]
        if not named:
            continue
        for issue_id in named:
            claim(sha, issue_id, "merge-subject")

        needs_parent_mapping = (
            len(entry["parents"]) > 2 or len(set(named)) > 1
        )
        if needs_parent_mapping:
            parent_issues = []
            for parent in entry["parents"][1:]:
                corroborated = {
                    issue_id_from_branch(ref, issue_ids)
                    for ref, tip in built["ref_tips"].items()
                    if tip == parent
                }
                corroborated.discard(None)
                if len(corroborated) != 1:
                    parent_issues = []
                    break
                parent_issues.append(corroborated.pop())

            octopus = len(entry["parents"]) > 2
            invalid_mapping = (
                len(parent_issues) != len(entry["parents"]) - 1
                or len(set(parent_issues)) != len(parent_issues)
                or not set(parent_issues).issubset(set(named))
                or (octopus and set(parent_issues) != set(named))
            )
            if invalid_mapping:
                if DEGRADED_BRANCH_UNAVAILABLE not in degraded:
                    degraded.append(DEGRADED_BRANCH_UNAVAILABLE)
                errors.append(
                    f"{'octopus ' if octopus else ''}merge {sha} "
                    "has no unambiguous "
                    "parent-to-issue ref mapping"
                )
                continue

            for parent_index, issue_id in enumerate(parent_issues, start=1):
                for side_sha in merge_side_commits(
                    records,
                    sha,
                    parent_index,
                ):
                    claim(side_sha, issue_id, "branch")
            continue

        for offset, issue_id in enumerate(named):
            for side_sha in merge_side_commits(records, sha, offset + 1):
                claim(side_sha, issue_id, "branch")

    # Live branches have no merge commit to delimit them.
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
        "branches": built["branches"],
        "issue_ids": issue_ids,
        "degraded": degraded,
        "errors": errors,
        "diagnostics": diagnostics,
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

    # A supplied index already holds every source for this commit, trailer
    # included — `build_attribution` read the bodies out of the same log it
    # walked. Asking git again per commit is the fan-out this module exists to
    # remove; measured at 65 redundant `git show` calls, 1.7s, on a 65-commit
    # range through `find_unlinked_behavior_commits`.
    if attribution is not None and sha in attribution:
        return _from_index(result, attribution, sha)

    # The trailer is intrinsic to the commit object, so it answers without the
    # index. Everything else is positional and needs the graph.
    show_args = ["git", "show", "-s", "--format=%B", sha]
    show = _run(runner, show_args, cwd)
    if show.returncode != 0:
        errors.append(_error_text(show_args, show))
        return result

    trailer = TRAILER_RE.search(show.stdout or "")
    if trailer:
        registered = issue_ids
        if registered is None:
            registered = known_issue_ids(runner, cwd, errors)
        if errors:
            return result
        if (
            trailer.group(1) in registered
            and SOURCE_PRECEDENCE[0] == "trailer"
        ):
            result["issue_id"] = trailer.group(1)
            result["source"] = "trailer"
            return result

    if attribution is None:
        built = build_attribution(runner, cwd)
        attribution = built["attribution"]
        errors.extend(built["errors"])
        degraded.extend(built["degraded"])

    return _from_index(result, attribution, sha)


def _from_index(result, attribution, sha):
    per_issue = attribution.get(sha) or {}
    if per_issue:
        # A commit can belong to several issues; this direction answers "which
        # issue owns it", so pick the strongest source, ties by issue id.
        issue_id, source = min(
            per_issue.items(),
            key=lambda item: (SOURCE_PRECEDENCE.index(item[1]), item[0]),
        )
        result["issue_id"] = issue_id
        result["source"] = source
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
        found = (attribution.get(sha) or {}).get(issue_id)
        if not found:
            continue
        entry = records[sha]
        commits.append(
            {
                "sha": sha,
                "subject": entry["subject"],
                "source": found,
                "is_merge": len(entry["parents"]) >= 2,
            }
        )

    sources = {}
    branch_refs = sorted(
        {
            name
            for name, names_issue in (
                (name, issue_id_from_branch(name, built.get("issue_ids", [])))
                for name in built.get("branches", [])
            )
            if names_issue == issue_id
        }
    )
    for entry in commits:
        sources[entry["source"]] = sources.get(entry["source"], 0) + 1

    return {
        "commits": commits,
        # Repository-wide, not per issue: the same numbers for every issue in
        # the range. Named so, because the earlier `unmatched_count` read as a
        # per-run gap and could not be one — it does not move when a commit is
        # attributed to the wrong issue, which is the failure it was added for.
        "repo_examined_count": len(built["order"]),
        "repo_unmatched_count": len(built["unmatched"]),
        # Per issue, and what a reviewer can actually act on: which evidence
        # carried this bundle, and which branch refs were read for it.
        "coverage": {
            "sources": sources,
            "branch_refs": branch_refs,
            "base_ref_available": DEGRADED_BRANCH_UNAVAILABLE not in built["degraded"],
        },
        "degraded": list(built["degraded"]),
        "errors": list(built["errors"]),
    }
