#!/usr/bin/env python3
"""A slow, obviously-correct commit-to-issue resolver used as a test oracle.

Issue 095 was reviewed three times. Each round fixed the case it was handed and
missed the class, because the tests encoded the same understanding of git that
the implementation did — a fixture can only fail when reality differs from what
its author imagined, and the author's imagination was the defect source.

This module exists so correctness is not decided by that imagination. It asks
git directly, one question at a time, with no batching, no index, and no
cleverness. It is far too slow to ship and that is the point: every step is
checkable on its own, and `tests/test_commit_resolution_differential.py`
compares the fast implementation against it across generated repository shapes.

Definitions used here, each independently verifiable at a shell:

  trailer  a commit whose body carries `Issue: <id>`
           -> git log --all, read each body

  branch   a commit a branch named codex/<id> contributed
           -> live branch:   git rev-list <ref> --not <base>
              merged branch: git rev-list <merge>^2 --not <merge>^1

A merge only contributes its second-parent side when codex/<id> is what was
merged *from*. `Merge branch 'main' into codex/<id>` names the issue but merges
main into the branch, so its second-parent side is main's history, not the
issue's — claiming it attributes the whole base branch to the issue.
"""
import re

ISSUE_ID_PATTERN = r"\d{3}-[a-z0-9-]+"
TRAILER_RE = re.compile(rf"^Issue:\s*({ISSUE_ID_PATTERN})\s*$", re.MULTILINE)
BRANCH_RE = re.compile(rf"^codex/({ISSUE_ID_PATTERN})$")

# Deliberately no hardcoded name list. `commit_resolution.base_ref` has one,
# and a copy here would make the oracle blind to whether that list is right —
# the second independent review found exactly that: the implementation prefers
# a stale local `main` over `origin/main`, and the differential suite agreed
# with it because both sides consulted the same four names.


def _out(runner, args, cwd):
    result = runner(list(args), cwd)
    if result.returncode != 0:
        return None
    return result.stdout or ""


def _refs(runner, cwd):
    text = _out(runner, ["git", "for-each-ref", "--format=%(refname:short)",
                         "refs/heads", "refs/remotes"], cwd)
    if text is None:
        return []
    return [line.strip().split(" -> ")[0].strip()
            for line in text.splitlines() if line.strip()]


def _base_ref(runner, cwd, refs):
    """The branch other branches are cut from, derived from the repository
    rather than from a list of names this project happens to use.

    Two derivations, in order:

    1. `origin/HEAD` — what the remote itself calls its default branch. This is
       git's own answer and needs no guessing.
    2. The ref contributing the fewest commits that no other ref has. A trunk is
       contained in the branches cut from it, so it contributes nothing unique;
       a topic branch contributes its own work. Ties go to the ref reachable
       from the most others.

    Neither consults a name, so this disagrees with the implementation whenever
    the implementation's name list picks the wrong ref."""
    head = _out(runner, ["git", "symbolic-ref", "--short", "refs/remotes/origin/HEAD"], cwd)
    if head and head.strip() in refs:
        return head.strip()

    if not refs:
        return None

    scored = []
    for ref in refs:
        others = [other for other in refs if other != ref]
        if not others:
            continue
        exclusive = _out(runner, ["git", "rev-list", ref, "--not", *others], cwd)
        exclusive_count = len(exclusive.split()) if exclusive else 0
        contained_in = 0
        for other in others:
            merged = _out(runner, ["git", "merge-base", "--is-ancestor", ref, other], cwd)
            if merged is not None:
                contained_in += 1
        scored.append((exclusive_count, -contained_in, ref))
    if not scored:
        return refs[0]
    scored.sort()
    return scored[0][2]


def _branch_issue(ref, known_ids):
    tail = ref.split("/", 1)[1] if "/" in ref and not ref.startswith("codex/") else ref
    match = BRANCH_RE.match(tail)
    if not match:
        return None
    found = match.group(1)
    best = None
    for issue_id in known_ids:
        if found == issue_id or found.startswith(issue_id + "-"):
            if best is None or len(issue_id) > len(best):
                best = issue_id
    return best or found


def _known_ids(runner, cwd):
    text = _out(runner, ["git", "ls-files", "issues"], cwd)
    if text is None:
        return []
    ids = []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("issues/") and line.endswith(".md"):
            candidate = line[len("issues/"):-len(".md")]
            if re.fullmatch(ISSUE_ID_PATTERN, candidate):
                ids.append(candidate)
    return ids


def merge_source_issue(subject, known_ids):
    """The issue a merge commit merged *from*, or None.

    `Merge branch 'codex/X'`                 -> X   (branch merged in)
    `Merge pull request #9 from o/codex/X`   -> X   (branch merged in)
    `Merge branch 'main' into codex/X`       -> None (main merged into branch)
    `Merge branch 'codex/X' into codex/Y`    -> X   (X merged into Y)
    """
    source = subject.split(" into ")[0] if " into " in subject else subject
    match = re.search(rf"codex/({ISSUE_ID_PATTERN})", source)
    if not match:
        return None
    return _branch_issue(f"codex/{match.group(1)}", known_ids)


def reference_commits_for_issue(runner, cwd, issue_id):
    """Every commit belonging to issue_id. Returns a set of shas."""
    known_ids = _known_ids(runner, cwd)
    refs = _refs(runner, cwd)
    base = _base_ref(runner, cwd, refs)
    found = set()

    # 1. Trailers. Intrinsic to the commit; no graph reasoning needed.
    log = _out(runner, ["git", "log", "--all", "--format=%H%x00%B%x01"], cwd) or ""
    merges = []
    for record in log.split("\x01"):
        record = record.strip("\n")
        if not record.strip():
            continue
        sha, _, body = record.partition("\x00")
        sha = sha.strip()
        if not sha:
            continue
        trailer = TRAILER_RE.search(body)
        if trailer and trailer.group(1) == issue_id:
            found.add(sha)

    # 2. Live branches named for this issue. A branch's contribution is what it
    #    has that the base branch does not — independent of every other branch.
    for ref in refs:
        if _branch_issue(ref, known_ids) != issue_id:
            continue
        if base is None:
            continue
        text = _out(runner, ["git", "rev-list", ref, "--not", base], cwd)
        if text:
            found.update(text.split())

    # 3. Merges that brought this issue's branch in.
    subjects = _out(runner, ["git", "log", "--all", "--merges",
                             "--format=%H%x00%s%x01"], cwd) or ""
    for record in subjects.split("\x01"):
        record = record.strip("\n")
        if not record.strip():
            continue
        sha, _, subject = record.partition("\x00")
        sha = sha.strip()
        if not sha:
            continue
        source = subject.strip()
        source = source.split(" into ")[0] if " into " in source else source
        named = [
            _branch_issue(f"codex/{m}", known_ids)
            for m in re.findall(rf"codex/({ISSUE_ID_PATTERN})", source)
        ]
        if issue_id not in named:
            continue
        found.add(sha)
        # An octopus merge has one parent per branch it brought in, in the
        # order the subject names them.
        for offset, named_id in enumerate(named):
            if named_id != issue_id:
                continue
            side = _out(
                runner,
                ["git", "rev-list", f"{sha}^{offset + 2}", "--not", f"{sha}^1"],
                cwd,
            )
            if side:
                found.update(side.split())

    return found


def reference_issues_for_commit(runner, cwd, sha):
    """Every issue a commit belongs to. Returns a set of issue ids.

    Derived by inverting `reference_commits_for_issue` over every known issue
    rather than by asking a per-commit question — the point of an oracle is
    that it reaches the answer a different way than the implementation, which
    builds one attribution index and reads it from both directions.

    A commit can belong to several issues: one merged from branch A into branch
    B before B reached main belongs to both.
    """
    found = set()
    for issue_id in _known_ids(runner, cwd):
        if sha in reference_commits_for_issue(runner, cwd, issue_id):
            found.add(issue_id)

    # Trailers can name an issue with no tracked issues/<id>.md file, which
    # `_known_ids` cannot enumerate. Read them off the commit itself.
    body = _out(runner, ["git", "show", "-s", "--format=%B", sha], cwd) or ""
    trailer = TRAILER_RE.search(body)
    if trailer:
        found.add(trailer.group(1))

    # Same for a merge naming a branch whose issue is not registered.
    subject = _out(runner, ["git", "show", "-s", "--format=%s", sha], cwd) or ""
    parents = _out(runner, ["git", "show", "-s", "--format=%P", sha], cwd) or ""
    if len(parents.split()) >= 2:
        merged = merge_source_issue(subject.strip(), _known_ids(runner, cwd))
        if merged:
            found.add(merged)

    return found
