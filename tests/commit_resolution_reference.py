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

BASE_CANDIDATES = ("main", "origin/main", "master", "origin/master")


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


def _base_ref(refs):
    """The branch other branches are cut from. Its history is never a branch's
    own contribution."""
    for candidate in BASE_CANDIDATES:
        if candidate in refs:
            return candidate
    return None


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
    base = _base_ref(refs)
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
        if merge_source_issue(subject.strip(), known_ids) != issue_id:
            continue
        found.add(sha)
        side = _out(runner, ["git", "rev-list", f"{sha}^2", "--not", f"{sha}^1"], cwd)
        if side:
            found.update(side.split())

    return found
