#!/usr/bin/env python3
"""Immutable Git graph snapshots for commit-to-issue resolution.

This module deliberately knows nothing about issue identifiers, branch naming,
trailers, or attribution precedence.  It owns only the bounded Git inventory
and the graph queries that later policy code can reuse.
"""

# NUL-separated fields, \x01-terminated records: sha, subject, parents, body.
GIT_LOG_FORMAT = "%H%x00%s%x00%P%x00%B%x01"
GIT_LOG_ARGS = ("git", "log", "--all", f"--format={GIT_LOG_FORMAT}")
BRANCH_REF_ARGS = (
    "git",
    "for-each-ref",
    "--format=%(refname) %(objectname)",
    "refs/heads",
    "refs/remotes",
)


def diagnostic(code, message, *, sha=None, issue_id=None, ref=None):
    """Build a structured graph diagnostic without empty scope fields."""
    result = {"code": code, "message": message}
    for key, value in (("sha", sha), ("issue_id", issue_id), ("ref", ref)):
        if value is not None:
            result[key] = value
    return result


def _failure(args, result):
    if result.returncode < 0:
        return diagnostic(
            "git-terminated",
            f"{' '.join(args)} terminated by signal {-result.returncode}",
        )["message"]
    detail = (result.stderr or "").strip() or (result.stdout or "").strip()
    detail = detail or f"exit code {result.returncode}"
    return diagnostic("git-command-failed", f"{' '.join(args)} failed: {detail}")["message"]


def _result(field, value, fatal_errors):
    """Return a caller-owned result mapping from immutable cached values."""
    return {field: value, "fatal_errors": list(fatal_errors)}


def _merge_base_sha(stdout):
    """Validate Git's successful merge-base response before trusting it."""
    lines = (stdout or "").splitlines()
    if len(lines) != 1:
        return None
    tokens = lines[0].split()
    return tokens[0] if len(tokens) == 1 else None


def _merge_base_shas(stdout):
    """Validate all of Git's best common ancestors from ``merge-base --all``."""
    shas = []
    for line in (stdout or "").splitlines():
        tokens = line.split()
        if len(tokens) != 1:
            return None
        shas.append(tokens[0])
    return tuple(sorted(set(shas))) if shas else None


def merge_base(runner, cwd, snapshot, left, right):
    """Return a cached common-base result for an unordered graph pair."""
    key = tuple(sorted((left, right)))
    cache = snapshot["merge_base_cache"]
    if key in cache:
        sha, fatal_errors = cache[key]
        return _result("sha", sha, fatal_errors)
    args = ["git", "merge-base", left, right]
    result = runner(args, cwd)
    if result.returncode == 0:
        sha = _merge_base_sha(result.stdout)
        fatal_errors = (
            ()
            if sha is not None
            else (
                "git merge-base produced malformed output "
                "(expected exactly one nonempty SHA token)",
            )
        )
    elif result.returncode == 1:
        sha, fatal_errors = None, ()
    else:
        sha, fatal_errors = None, (_failure(args, result),)
    cache[key] = (sha, fatal_errors)
    return _result("sha", sha, fatal_errors)


def merge_bases(runner, cwd, snapshot, left, right):
    """Return every cached best common ancestor for an unordered graph pair."""
    key = tuple(sorted((left, right)))
    cache = snapshot.setdefault("merge_bases_cache", {})
    if key in cache:
        shas, fatal_errors = cache[key]
        return _result(
            "shas", list(shas) if shas is not None else None, fatal_errors
        )
    args = ["git", "merge-base", "--all", left, right]
    result = runner(args, cwd)
    if result.returncode == 0:
        shas = _merge_base_shas(result.stdout)
        fatal_errors = (
            ()
            if shas is not None
            else (
                "git merge-base --all produced malformed output "
                "(expected one or more SHA tokens, one per line)",
            )
        )
    elif result.returncode == 1:
        shas, fatal_errors = None, ()
    else:
        shas, fatal_errors = None, (_failure(args, result),)
    cache[key] = (shas, fatal_errors)
    return _result(
        "shas", list(shas) if shas is not None else None, fatal_errors
    )


def is_ancestor(runner, cwd, snapshot, older, newer):
    """Return a cached directional ancestry-query result."""
    key = (older, newer)
    cache = snapshot["ancestor_cache"]
    if key in cache:
        value, fatal_errors = cache[key]
        return _result("value", value, fatal_errors)
    args = ["git", "merge-base", "--is-ancestor", older, newer]
    result = runner(args, cwd)
    if result.returncode == 0:
        value, fatal_errors = True, ()
    elif result.returncode == 1:
        value, fatal_errors = False, ()
    else:
        value, fatal_errors = None, (_failure(args, result),)
    cache[key] = (value, fatal_errors)
    return _result("value", value, fatal_errors)


def _preserve_fatal_errors(snapshot, key, fatal_errors):
    """Add cached query failures to a snapshot once, at their query identity."""
    if not fatal_errors:
        return
    recorded = snapshot.setdefault("fatal_error_cache_keys", set())
    if key in recorded:
        return
    snapshot["fatal_errors"].extend(fatal_errors)
    recorded.add(key)


def _snapshot_graph_error(snapshot, key, message):
    """Record malformed snapshot topology once without guessing through it."""
    recorded = snapshot.setdefault("fatal_error_cache_keys", set())
    if key not in recorded:
        snapshot["fatal_errors"].append(message)
        recorded.add(key)


def _record_ancestors(snapshot, start):
    """Return cached recorded ancestors with fatal topology metadata."""
    cache = snapshot.setdefault("record_ancestor_cache", {})
    if start in cache:
        ancestors, fatal_errors = cache[start]
        return {"ancestors": ancestors, "fatal_errors": list(fatal_errors)}
    records = snapshot["records"]

    def failed(key, message):
        _snapshot_graph_error(snapshot, key, message)
        cache[start] = (None, (message,))
        return {"ancestors": None, "fatal_errors": [message]}

    if start not in records:
        return failed(
            ("record-ancestor-missing", start),
            f"snapshot graph is incomplete: missing record for {start}",
        )
    seen = set()
    active = set()
    stack = [(start, False)]
    while stack:
        sha, expanded = stack.pop()
        if expanded:
            active.discard(sha)
            continue
        if sha in seen:
            continue
        if sha in active:
            return failed(
                ("record-ancestor-cycle", sha),
                f"snapshot graph contains a parent cycle at {sha}",
            )
        record = records.get(sha)
        if record is None:
            return failed(
                ("record-ancestor-missing", sha),
                f"snapshot graph is incomplete: missing record for {sha}",
            )
        seen.add(sha)
        active.add(sha)
        stack.append((sha, True))
        for parent in record.get("parents", []):
            if parent in active:
                return failed(
                    ("record-ancestor-cycle", parent),
                    f"snapshot graph contains a parent cycle at {parent}",
                )
            if parent not in records:
                return failed(
                    ("record-ancestor-missing", parent),
                    f"snapshot graph is incomplete: missing record for {parent}",
                )
            if parent not in seen:
                stack.append((parent, False))
    cache[start] = (frozenset(seen), ())
    return {"ancestors": cache[start][0], "fatal_errors": []}


def _publication_forks(runner, cwd, snapshot, topic_sha, base_sha):
    """Recover no-ff publication forks without probing unrelated records."""
    base_result = _record_ancestors(snapshot, base_sha)
    topic_result = _record_ancestors(snapshot, topic_sha)
    fatal_errors = [*base_result["fatal_errors"], *topic_result["fatal_errors"]]
    if fatal_errors:
        return [], set(), fatal_errors
    base_ancestors = base_result["ancestors"]
    topic_ancestors = topic_result["ancestors"]
    recovered = []
    publication_sides = set()
    for merge_sha in sorted(base_ancestors):
        record = snapshot["records"][merge_sha]
        if len(record["parents"]) < 2:
            continue
        topic_sides = [
            parent for parent in record["parents"] if parent in topic_ancestors
        ]
        # The topic parent must be in the current topic ref's own history. A
        # later unrelated merge has main (which contains the topic) as a
        # parent, but that merge object is not an ancestor of the topic ref.
        if not topic_sides:
            continue
        maximal_sides = []
        for side in topic_sides:
            other_results = [
                _record_ancestors(snapshot, other)
                for other in topic_sides if side != other
            ]
            fatal_errors.extend(
                error for result in other_results for error in result["fatal_errors"]
            )
            if fatal_errors:
                return [], publication_sides, fatal_errors
            if not any(side in result["ancestors"] for result in other_results):
                maximal_sides.append(side)
        if len(maximal_sides) != 1:
            continue
        publication_sides.update(maximal_sides)
        for parent in record["parents"]:
            if parent in maximal_sides:
                continue
            bases = merge_bases(runner, cwd, snapshot, topic_sha, parent)
            _preserve_fatal_errors(
                snapshot,
                ("merge-bases", tuple(sorted((topic_sha, parent)))),
                bases["fatal_errors"],
            )
            fatal_errors.extend(bases["fatal_errors"])
            recovered.extend(bases["shas"] or [])
    return sorted(set(recovered)), publication_sides, fatal_errors


def derive_fork_point(runner, cwd, snapshot, topic_ref, issue_id, *, base_refs):
    """Select one ancestry-maximal historical fork point for a topic ref.

    A base ref contributes a merge-base candidate only when it is connected to
    the topic. Full ref names remain distinct throughout: refs are equivalent
    only when Git returns the exact same selected merge-base object.
    """
    if topic_ref not in snapshot["refs"]:
        return {
            "issue_id": issue_id,
            "topic_ref": topic_ref,
            "fork_point": None,
            "equivalent_base_refs": [],
            "fatal_errors": [],
            "diagnostics": [
                diagnostic(
                    "topic-ref-missing",
                    f"{topic_ref} is not present in the graph snapshot",
                    issue_id=issue_id,
                    ref=topic_ref,
                )
            ],
        }

    topic_sha = snapshot["refs"][topic_ref]
    by_fork = {}
    recovered_forks = set()
    publication_sides = set()
    ordinary_forks = set()
    needs_publication_recovery = False
    fatal_errors = []
    for ref in sorted(set(base_refs)):
        if ref not in snapshot["refs"]:
            continue
        base_sha = snapshot["refs"][ref]
        result = merge_bases(runner, cwd, snapshot, topic_sha, base_sha)
        _preserve_fatal_errors(
            snapshot,
            ("merge-bases", tuple(sorted((topic_sha, base_sha)))),
            result["fatal_errors"],
        )
        fatal_errors.extend(result["fatal_errors"])
        candidates = result["shas"] or []
        recovered = []
        if not result["fatal_errors"] and topic_sha in snapshot["records"]:
            recovered, sides, recovery_errors = _publication_forks(
                runner, cwd, snapshot, topic_sha, base_sha
            )
            publication_sides.update(sides)
            fatal_errors.extend(recovery_errors)
        candidates = [sha for sha in candidates if sha not in publication_sides]
        if recovered:
            needs_publication_recovery = True
            recovered_forks.update(recovered)
            candidates = [
                sha for sha in candidates
                if sha not in _record_ancestors(snapshot, topic_sha)["ancestors"]
            ]
            ordinary_forks.update(candidates)
            candidates.extend(recovered)
        elif topic_sha in candidates:
            needs_publication_recovery = True
            candidates = [sha for sha in candidates if sha != topic_sha]
            ordinary_forks.update(candidates)
        else:
            ordinary_forks.update(candidates)
        for fork_sha in candidates:
            by_fork.setdefault(fork_sha, []).append(ref)

    if not by_fork and needs_publication_recovery:
        return {
            "issue_id": issue_id,
            "topic_ref": topic_ref,
            "fork_point": None,
            "equivalent_base_refs": [],
            "fatal_errors": fatal_errors,
            "diagnostics": [
                diagnostic(
                    "topic-publication-fork-unresolved",
                    f"{topic_ref} publication boundary has no unique pre-publication fork",
                    issue_id=issue_id,
                    ref=topic_ref,
                )
            ],
        }

    # Historical publication boundaries are one lineage: select its earliest
    # valid point first, then compare that point against every ordinary base.
    # A recovery must never erase an incomparable ordinary base candidate.
    recovered_minimal = set(recovered_forks)
    for fork_sha in sorted(recovered_forks):
        for other_sha in sorted(recovered_forks):
            if fork_sha == other_sha:
                continue
            relation = is_ancestor(runner, cwd, snapshot, other_sha, fork_sha)
            _preserve_fatal_errors(
                snapshot, ("is-ancestor", other_sha, fork_sha), relation["fatal_errors"]
            )
            fatal_errors.extend(relation["fatal_errors"])
            if relation["value"] is True:
                reverse = is_ancestor(runner, cwd, snapshot, fork_sha, other_sha)
                _preserve_fatal_errors(
                    snapshot, ("is-ancestor", fork_sha, other_sha), reverse["fatal_errors"]
                )
                fatal_errors.extend(reverse["fatal_errors"])
                if reverse["value"] is False:
                    recovered_minimal.discard(fork_sha)
                    break

    selected_forks = ordinary_forks | recovered_minimal
    maximal = []
    for fork_sha in sorted(selected_forks):
        dominated = False
        for other_sha in sorted(selected_forks):
            if fork_sha == other_sha:
                continue
            left, right = fork_sha, other_sha
            relation = is_ancestor(runner, cwd, snapshot, left, right)
            _preserve_fatal_errors(
                snapshot,
                ("is-ancestor", left, right),
                relation["fatal_errors"],
            )
            fatal_errors.extend(relation["fatal_errors"])
            if relation["value"] is not True:
                continue
            reverse = is_ancestor(runner, cwd, snapshot, right, left)
            _preserve_fatal_errors(
                snapshot,
                ("is-ancestor", right, left),
                reverse["fatal_errors"],
            )
            fatal_errors.extend(reverse["fatal_errors"])
            if reverse["value"] is False:
                dominated = True
                break
        if not dominated:
            maximal.append(fork_sha)

    if len(maximal) != 1:
        return {
            "issue_id": issue_id,
            "topic_ref": topic_ref,
            "fork_point": None,
            "equivalent_base_refs": [],
            "fatal_errors": fatal_errors,
            "diagnostics": [
                diagnostic(
                    "ambiguous-topic-fork",
                    f"{topic_ref} has {len(maximal)} incomparable fork points",
                    issue_id=issue_id,
                    ref=topic_ref,
                )
            ],
        }

    fork_point = maximal[0]
    return {
        "issue_id": issue_id,
        "topic_ref": topic_ref,
        "fork_point": fork_point,
        "equivalent_base_refs": sorted(by_fork[fork_point]),
        "fatal_errors": fatal_errors,
        "diagnostics": [],
    }


def _ancestry_maximal(runner, cwd, snapshot, candidates):
    """Keep only candidate commits not strictly below another candidate."""
    maximal = []
    for candidate in sorted(set(candidates)):
        dominated = False
        for other in sorted(set(candidates)):
            if candidate == other:
                continue
            relation = is_ancestor(runner, cwd, snapshot, candidate, other)
            _preserve_fatal_errors(
                snapshot,
                ("is-ancestor", candidate, other),
                relation["fatal_errors"],
            )
            if relation["fatal_errors"]:
                return None
            if relation["value"] is not True:
                continue
            reverse = is_ancestor(runner, cwd, snapshot, other, candidate)
            _preserve_fatal_errors(
                snapshot,
                ("is-ancestor", other, candidate),
                reverse["fatal_errors"],
            )
            if reverse["fatal_errors"]:
                return None
            if reverse["value"] is False:
                dominated = True
                break
        if not dominated:
            maximal.append(candidate)
    return sorted(maximal)


def _rev_list_shas(stdout, records):
    """Accept only complete one-SHA-per-line rev-list success output."""
    shas = []
    for line in (stdout or "").splitlines():
        fields = line.split()
        if len(fields) != 1 or fields[0] not in records:
            return None
        shas.append(fields[0])
    return set(shas)


def topic_delta(
    runner,
    cwd,
    snapshot,
    topic_ref,
    issue_id,
    *,
    topic_refs,
    base_refs,
):
    """Return commits introduced by one topic, excluding stacked issue work."""
    fatal_before = len(snapshot["fatal_errors"])
    topic_sha = snapshot["refs"].get(topic_ref)
    # A non-issue alias at the topic tip (for example local `release/main`)
    # is evidence of publication, not a historical fork candidate.
    fork_base_refs = [
        ref for ref in base_refs if snapshot["refs"].get(ref) != topic_sha
    ]
    fork = derive_fork_point(
        runner, cwd, snapshot, topic_ref, issue_id, base_refs=fork_base_refs
    )
    diagnostics = list(fork["diagnostics"])
    if fork["fork_point"] is None:
        return {
            **fork,
            "stacked_exclusions": [],
            "commits": set(),
            "diagnostics": diagnostics,
        }
    if fork["fatal_errors"]:
        return {
            **fork,
            "stacked_exclusions": [],
            "commits": set(),
            "diagnostics": diagnostics,
        }
    if len(snapshot["fatal_errors"]) != fatal_before:
        return {
            **fork,
            "stacked_exclusions": [],
            "commits": set(),
            "diagnostics": diagnostics,
        }

    exclusions = []
    for other_ref in sorted(topic_refs):
        if other_ref == topic_ref or topic_refs[other_ref] == issue_id:
            continue
        other_sha = snapshot["refs"].get(other_ref)
        if other_sha is None:
            continue
        pair = merge_bases(runner, cwd, snapshot, topic_sha, other_sha)
        _preserve_fatal_errors(
            snapshot,
            ("merge-bases", tuple(sorted((topic_sha, other_sha)))),
            pair["fatal_errors"],
        )
        if pair["fatal_errors"]:
            return {
                **fork,
                "stacked_exclusions": [],
                "commits": set(),
                "fatal_errors": [*fork["fatal_errors"], *pair["fatal_errors"]],
                "diagnostics": diagnostics,
            }
        for candidate in pair["shas"] or []:
            # A descendant topic's merge-base can be this topic's own tip.
            # That proves the *other* topic stacks on us; it must not erase us.
            if candidate in (fork["fork_point"], topic_sha):
                continue
            above_fork = is_ancestor(
                runner, cwd, snapshot, fork["fork_point"], candidate
            )
            _preserve_fatal_errors(
                snapshot,
                ("is-ancestor", fork["fork_point"], candidate),
                above_fork["fatal_errors"],
            )
            if above_fork["fatal_errors"]:
                return {
                    **fork,
                    "stacked_exclusions": [],
                    "commits": set(),
                    "fatal_errors": [*fork["fatal_errors"], *above_fork["fatal_errors"]],
                    "diagnostics": diagnostics,
                }
            if above_fork["value"] is True:
                exclusions.append(candidate)

    exclusions = _ancestry_maximal(runner, cwd, snapshot, exclusions)
    if exclusions is None:
        return {
            **fork,
            "stacked_exclusions": [],
            "commits": set(),
            "diagnostics": diagnostics,
        }
    if len(snapshot["fatal_errors"]) != fatal_before:
        return {
            **fork,
            "stacked_exclusions": [],
            "commits": set(),
            "diagnostics": diagnostics,
        }
    args = [
        "git",
        "rev-list",
        topic_sha,
        "--not",
        fork["fork_point"],
        *exclusions,
    ]
    result = runner(args, cwd)
    if result.returncode != 0:
        message = _failure(args, result)
        _snapshot_graph_error(snapshot, ("rev-list-failed", tuple(args)), message)
        return {
            **fork,
            "stacked_exclusions": exclusions,
            "commits": set(),
            "fatal_errors": [*fork["fatal_errors"], message],
            "diagnostics": diagnostics,
        }
    else:
        commits = _rev_list_shas(result.stdout, snapshot["records"])
        if commits is None:
            message = (
                "git rev-list produced malformed output "
                "(expected one known SHA token per line)"
            )
            _snapshot_graph_error(
                snapshot, ("rev-list-malformed", tuple(args)), message
            )
            return {
                **fork,
                "stacked_exclusions": exclusions,
                "commits": set(),
                "fatal_errors": [*fork["fatal_errors"], message],
                "diagnostics": diagnostics,
            }
        else:
            # Merge boundaries are attributed by resolver merge policy. A
            # topic delta supplies only side-content, so an inner publication
            # merge cannot become outer topic work.
            commits = {
                sha
                for sha in commits
                if len(snapshot["records"][sha]["parents"]) < 2
            }
    return {
        **fork,
        "stacked_exclusions": exclusions,
        "commits": commits,
        "diagnostics": diagnostics,
    }


def _parse_records(stdout, fatal_errors):
    records = {}
    order = []
    for record in (stdout or "").split("\x01"):
        record = record.strip("\n")
        if not record.strip():
            continue
        parts = record.split("\x00")
        if len(parts) != 4:
            fatal_errors.append(
                "git log produced a malformed record "
                f"(expected 4 fields, got {len(parts)}): {record[:80]!r}"
            )
            continue
        sha, subject, parents, body = parts
        sha = sha.strip()
        if not sha:
            fatal_errors.append(
                "git log produced a malformed record with an empty SHA"
            )
            continue
        records[sha] = {
            "sha": sha,
            "subject": subject.strip(),
            "parents": parents.split(),
            "body": body,
        }
        order.append(sha)
    return records, order


def _parse_refs(stdout, fatal_errors):
    refs = {}
    for line in (stdout or "").splitlines():
        if not line.strip():
            continue
        if line[0].isspace():
            fatal_errors.append(
                "git for-each-ref produced malformed output with an empty ref name"
            )
            continue
        fields = line.split(maxsplit=1)
        if len(fields) != 2 or not fields[1].strip():
            fatal_errors.append(
                "git for-each-ref produced malformed output with a missing object ID"
            )
            continue
        ref = fields[0].split(" -> ")[0].strip()
        if not ref:
            fatal_errors.append(
                "git for-each-ref produced malformed output with an empty ref name"
            )
            continue
        if ref.startswith("refs/remotes/") and ref.endswith("/HEAD"):
            continue
        refs[ref] = fields[1].strip()
    return refs


def load_snapshot(runner, cwd, *, rev_range=None):
    """Read commit records and refs once into one reusable graph snapshot."""
    # Topology must remain complete even when a consumer later projects a
    # requested range; fork recovery and rev-list validation need --all.
    log_args = list(GIT_LOG_ARGS)
    ref_args = list(BRANCH_REF_ARGS)
    log_result = runner(log_args, cwd)
    ref_result = runner(ref_args, cwd)
    fatal_errors = []
    if log_result.returncode != 0:
        fatal_errors.append(_failure(log_args, log_result))
        records, order = {}, []
    else:
        records, order = _parse_records(log_result.stdout, fatal_errors)
    if ref_result.returncode != 0:
        fatal_errors.append(_failure(ref_args, ref_result))
        refs = {}
    else:
        refs = _parse_refs(ref_result.stdout, fatal_errors)
    return {
        "records": records,
        "order": order,
        "refs": refs,
        "merge_base_cache": {},
        "merge_bases_cache": {},
        "ancestor_cache": {},
        "fatal_errors": fatal_errors,
        "fatal_error_cache_keys": set(),
    }
