#!/usr/bin/env python3
"""Repository shapes for differential testing (issue 095, review round 3).

Each builder returns (repo, issue_ids). The shapes are chosen for what the
implementation's author had least reason to try — three review rounds showed
that the happy shape (branch from main, commit, merge) is the only one the
original fixtures built, and every defect lived outside it.

Shapes marked LIVE are arrangements that exist in the ModuFlow repository
today; the rest are arrangements git permits and the resolver must survive.

Every commit declares `belongs_to` (issue 095, review round 8). That is the
ground truth, written by hand by the shape that built the history, and it
replaced a reference oracle that re-derived the answer from git — which is why
the oracle kept agreeing with the bug. Two rules keep the declarations honest:

1. Declare issue ids only, never a `source`. Truth is what a commit belongs to,
   not how the resolver found it. Asserting the strategy is the same coupling
   one level down.
2. A merge commit belongs to every issue branch it touches — the branch it sits
   on and the branches it brings in. Merges carry no content of their own, so a
   reviewer who sees one in either bundle is not misled; the strict part of the
   declaration is the *content* commits, where an id crossing from one issue to
   another is a real defect and is declared as such even where it disagrees
   with what the shipped resolver returns today.
"""
ALPHA = "101-alpha"
BETA = "102-beta"
GAMMA = "103-gamma"


def _seed(repo, *issue_ids):
    repo.commit("chore: unrelated base one", belongs_to=None)
    repo.commit("chore: unrelated base two", belongs_to=None)
    for issue_id in issue_ids:
        repo.add_issue_file(issue_id)


def happy_merge(repo):
    """The only shape the original fixtures built."""
    _seed(repo, ALPHA)
    name = repo.branch(f"codex/{ALPHA}")
    repo.commit("feat: alpha work", belongs_to=ALPHA)
    repo.checkout("main")
    repo.merge(name, message=f"Merge branch 'codex/{ALPHA}'", belongs_to=ALPHA)
    return [ALPHA]


def sync_merge_then_pr_merge(repo):
    """LIVE. `Merge branch 'main' into codex/X` names the issue in its subject
    while merging main *into* the branch — claiming its second-parent side
    attributes the whole base branch to the issue."""
    _seed(repo, ALPHA)
    name = repo.branch(f"codex/{ALPHA}")
    repo.commit("feat: alpha work", belongs_to=ALPHA)
    repo.checkout("main")
    repo.commit("chore: main moved on one", belongs_to=None)
    repo.commit("chore: main moved on two", belongs_to=None)
    repo.checkout(name)
    # Sits on codex/alpha, brings in main. Alpha's, by the branch it is on.
    repo.merge("main", message=f"Merge branch 'main' into codex/{ALPHA}",
               belongs_to=ALPHA)
    repo.checkout("main")
    repo.merge(name, message=f"Merge pull request #9 from o/codex/{ALPHA}",
               belongs_to=ALPHA)
    return [ALPHA]


def stacked_live_branches(repo):
    """LIVE (codex/089-… and codex/089-…-release). A follow-up branch built on
    top of another; excluding by name lets the descendant zero its parent."""
    _seed(repo, ALPHA, BETA)
    first = repo.branch(f"codex/{ALPHA}")
    repo.commit("feat: alpha one", belongs_to=ALPHA)
    repo.commit("feat: alpha two", belongs_to=ALPHA)
    second = repo.branch(f"codex/{BETA}")
    repo.commit("feat: beta on top of alpha", belongs_to=BETA)
    repo.publish(first)
    repo.publish(second)
    repo.checkout("main")
    return [ALPHA, BETA]


def single_branch_clone(repo):
    """`clone --single-branch` / CI checkout: the issue branch is the only ref
    besides its own counterpart, so a name-based exclusion list is empty."""
    _seed(repo, ALPHA)
    name = repo.branch(f"codex/{ALPHA}")
    repo.commit("feat: alpha work", belongs_to=ALPHA)
    repo.publish(name)
    return [ALPHA]


def detached_before_commit(repo):
    """Detach first, then commit — the commit is on no branch at all. The
    original detached-HEAD fixture detached afterwards, leaving the commit on
    main where the arrangement cannot bite."""
    _seed(repo, ALPHA)
    repo.detach()
    repo.commit("feat: work with trailer", issue=ALPHA, belongs_to=ALPHA)
    repo.commit("feat: more work", issue=ALPHA, belongs_to=ALPHA)
    return [ALPHA]


def nested_merges(repo):
    """Branch A merged into branch B, then B merged to main. A's commits must
    stay A's."""
    _seed(repo, ALPHA, BETA)
    first = repo.branch(f"codex/{ALPHA}")
    repo.commit("feat: alpha one", belongs_to=ALPHA)
    repo.checkout("main")
    second = repo.branch(f"codex/{BETA}")
    repo.commit("feat: beta one", belongs_to=BETA)
    # Sits on codex/beta, brings in codex/alpha — touches both issue branches.
    repo.merge(first, message=f"Merge branch 'codex/{ALPHA}'",
               belongs_to=[ALPHA, BETA])
    repo.checkout("main")
    repo.merge(second, message=f"Merge branch 'codex/{BETA}'", belongs_to=BETA)
    return [ALPHA, BETA]


def nested_merges_reversed_issue_order(repo):
    """FH-005: inner ownership survives an outer merge regardless of id sort."""
    _seed(repo, ALPHA, BETA)
    inner = repo.branch(f"codex/{BETA}")
    repo.commit("feat: beta inner work", belongs_to=BETA)
    repo.checkout("main")
    outer = repo.branch(f"codex/{ALPHA}")
    repo.commit("feat: alpha outer work", belongs_to=ALPHA)
    repo.merge(
        inner,
        message=f"Merge branch 'codex/{BETA}'",
        belongs_to=[ALPHA, BETA],
    )
    repo.checkout("main")
    repo.merge(
        outer,
        message=f"Merge branch 'codex/{ALPHA}'",
        belongs_to=ALPHA,
    )
    repo.delete_branch(inner)
    repo.delete_branch(outer)
    return [ALPHA, BETA]


def branch_name_not_matching_issue(repo):
    """LIVE (codex/092-current-dashboard-korean vs 092-project-home-dashboard).
    A branch whose name is not the issue id it belongs to."""
    _seed(repo, ALPHA)
    name = repo.branch("codex/199-unregistered-name")
    # 199 is not a registered issue and the work is not alpha's. Naming a
    # branch is not the same as having an issue (round 6).
    repo.commit("feat: work under a non-conforming branch", belongs_to=None)
    repo.publish(name)
    repo.checkout("main")
    return [ALPHA]


def disconnected_non_issue_base(repo):
    """A disconnected non-issue ref is not a usable branch base.

    With the real trunk deleted, selecting the orphan as base makes the issue
    branch appear to contribute every commit in its disconnected history."""
    _seed(repo, ALPHA)
    issue_branch = repo.branch(f"codex/{ALPHA}")
    repo.commit(
        "feat: alpha work",
        issue=ALPHA,
        belongs_to=ALPHA,
    )
    repo.checkout("main")
    repo._git("checkout", "-q", "--orphan", "orphan-base")
    repo.commit("chore: disconnected root", belongs_to=None)
    repo.checkout(issue_branch)
    repo.delete_branch("main")
    return [ALPHA]


def local_slash_branch_is_not_remote(repo):
    """A local `release/main` branch is not `main`'s remote counterpart."""
    _seed(repo, ALPHA)
    repo.branch(f"codex/{ALPHA}")
    repo.commit("feat: alpha work", belongs_to=ALPHA)
    repo._git("branch", "release/main")
    repo.checkout("main")
    return [ALPHA]


def divergent_same_tail_remotes(repo):
    """Choose the remote base whose ancestry the issue branch proves."""
    _seed(repo, ALPHA)
    origin_line = repo.branch("origin-line")
    repo.commit("chore: origin diverged", belongs_to=None)
    origin_tip = repo.head()
    repo.checkout("main")
    repo.commit("chore: upstream base moved", belongs_to=None)
    upstream_tip = repo.head()
    repo.branch(f"codex/{ALPHA}")
    repo.commit("feat: alpha work", belongs_to=ALPHA)
    repo._git("update-ref", "refs/remotes/origin/main", origin_tip)
    repo._git("update-ref", "refs/remotes/upstream/main", upstream_tip)
    repo.delete_branch(origin_line)
    repo.delete_branch("main")
    return [ALPHA]


def ambiguous_same_tail_remotes(repo):
    """Incomparable remote bases with equal issue ancestry must fail closed."""
    _seed(repo, ALPHA)
    origin_line = repo.branch("origin-line")
    repo.commit("chore: origin diverged", belongs_to=None)
    origin_tip = repo.head()
    repo.checkout("main")
    repo.commit("chore: upstream diverged", belongs_to=None)
    upstream_tip = repo.head()
    repo.merge(
        origin_line,
        message="Merge branch 'origin-line'",
        belongs_to=None,
    )
    repo.branch(f"codex/{ALPHA}")
    repo.commit(
        "feat: alpha work",
        issue=ALPHA,
        belongs_to=ALPHA,
    )
    repo._git("update-ref", "refs/remotes/origin/main", origin_tip)
    repo._git("update-ref", "refs/remotes/upstream/main", upstream_tip)
    repo.delete_branch(origin_line)
    repo.delete_branch("main")
    return [ALPHA]


def local_with_divergent_same_tail_remotes(repo):
    """Local and equivalent upstream beat an unrelated same-tail origin."""
    _seed(repo, ALPHA)
    origin_line = repo.branch("origin-line")
    repo.commit("chore: origin diverged", belongs_to=None)
    origin_tip = repo.head()
    repo.checkout("main")
    repo.commit("chore: local upstream base", belongs_to=None)
    local_tip = repo.head()
    repo.branch(f"codex/{ALPHA}")
    repo.commit("feat: alpha work", belongs_to=ALPHA)
    repo._git("update-ref", "refs/remotes/origin/main", origin_tip)
    repo._git("update-ref", "refs/remotes/upstream/main", local_tip)
    repo.delete_branch(origin_line)
    return [ALPHA]


def local_with_ambiguous_same_tail_remotes(repo):
    """Three incomparable same-tail bases must not be chosen arbitrarily."""
    _seed(repo, ALPHA)
    common = repo.head()
    origin_line = repo.branch("origin-line")
    repo.commit("chore: origin diverged", belongs_to=None)
    origin_tip = repo.head()
    repo.checkout("main")
    repo.commit("chore: local diverged", belongs_to=None)
    repo._git("checkout", "-q", "-b", "upstream-line", common)
    repo.commit("chore: upstream diverged", belongs_to=None)
    upstream_tip = repo.head()
    repo.checkout("main")
    integration = repo.branch("integration")
    repo.merge(
        origin_line,
        message="Merge branch 'origin-line'",
        belongs_to=None,
    )
    repo.merge(
        "upstream-line",
        message="Merge branch 'upstream-line'",
        belongs_to=None,
    )
    repo.branch(f"codex/{ALPHA}")
    repo.commit(
        "feat: alpha work",
        issue=ALPHA,
        belongs_to=ALPHA,
    )
    repo._git("update-ref", "refs/remotes/origin/main", origin_tip)
    repo._git("update-ref", "refs/remotes/upstream/main", upstream_tip)
    repo.delete_branch(origin_line)
    repo.delete_branch("upstream-line")
    repo.delete_branch(integration)
    return [ALPHA]


def trailer_outside_any_branch(repo):
    """A trailer-bearing commit merged and then its branch deleted, plus one
    committed straight to main."""
    _seed(repo, ALPHA)
    repo.commit("feat: straight to main", issue=ALPHA, belongs_to=ALPHA)
    name = repo.branch(f"codex/{ALPHA}")
    repo.commit("feat: on branch", issue=ALPHA, belongs_to=ALPHA)
    repo.checkout("main")
    repo.merge(name, message=f"Merge branch 'codex/{ALPHA}'", belongs_to=ALPHA)
    repo.delete_branch(name)
    return [ALPHA]


def two_issues_interleaved(repo):
    _seed(repo, ALPHA, BETA)
    first = repo.branch(f"codex/{ALPHA}")
    repo.commit("feat: alpha", issue=ALPHA, belongs_to=ALPHA)
    repo.checkout("main")
    second = repo.branch(f"codex/{BETA}")
    repo.commit("feat: beta", belongs_to=BETA)
    repo.checkout("main")
    repo.merge(first, message=f"Merge branch 'codex/{ALPHA}'", belongs_to=ALPHA)
    repo.merge(second, message=f"Merge branch 'codex/{BETA}'", belongs_to=BETA)
    return [ALPHA, BETA]


def empty_repository(repo):
    return [ALPHA]


def no_issue_commits_at_all(repo):
    repo.commit("chore: one", belongs_to=None)
    repo.commit("chore: two", belongs_to=None)
    return [ALPHA]


def non_main_default_branch(repo):
    """A repository whose trunk is not called `main`. Review finding N1:
    ground truth 2, both implementation and oracle 0, differential agreeing —
    unreachable while the builder hardcoded `-b main`."""
    _seed(repo, ALPHA)
    name = repo.branch(f"codex/{ALPHA}")
    repo.commit("feat: alpha work", belongs_to=ALPHA)
    repo.publish(name)
    repo.checkout(repo.default_branch)
    return [ALPHA]


def stale_local_default_branch(repo):
    """Review finding Q4. `origin/main` has moved ahead of local `main`; a
    name list that tries `main` first measures the branch against a base that
    is four commits behind, and hands the issue all four."""
    _seed(repo, ALPHA)
    repo.publish("main")
    repo.commit("chore: main moved one", belongs_to=None)
    repo.commit("chore: main moved two", belongs_to=None)
    repo.publish("main")
    stale = repo.head()
    name = repo.branch(f"codex/{ALPHA}")
    repo.commit("feat: alpha work", belongs_to=ALPHA)
    repo.publish(name)
    repo.checkout("main")
    repo._git("reset", "-q", "--hard", "HEAD~2")
    return [ALPHA]


def two_registered_stacked_issues(repo):
    """Review finding Q3, with both issues registered. `stacked_live_branches`
    only avoids the over-collection because its second branch name is not a
    tracked issue."""
    _seed(repo, ALPHA, BETA)
    first = repo.branch(f"codex/{ALPHA}")
    repo.commit("feat: alpha one", belongs_to=ALPHA)
    repo.commit("feat: alpha two", belongs_to=ALPHA)
    second = repo.branch(f"codex/{BETA}")
    repo.commit("feat: beta on top of alpha", belongs_to=BETA)
    repo.publish(first)
    repo.publish(second)
    repo.checkout(repo.default_branch)
    return [ALPHA, BETA]


def trailer_disagrees_with_branch(repo):
    """Two sources naming different issues for one commit.

    Reversing `SOURCE_PRECEDENCE` to put merge-subject ahead of trailer changed
    no shape's outcome — the mutation survived — because no shape ever made two
    sources disagree. Precedence was the one rule the suite asserted nowhere.
    The trailer is the author saying outright which issue the work is for, and
    the spec makes it authoritative over the branch it happens to sit on."""
    _seed(repo, ALPHA, BETA)
    name = repo.branch(f"codex/{ALPHA}")
    repo.commit("feat: alpha work", belongs_to=ALPHA)
    repo.commit("fix: actually beta's work", issue=BETA, belongs_to=BETA)
    repo.publish(name)
    repo.checkout("main")
    return [ALPHA, BETA]


def octopus_merge(repo):
    """Review finding N2. Two branches merged at once; the second-parent-only
    walk loses everything past `^2`, and the reviewer measured an entire
    issue's work attributed to nothing."""
    _seed(repo, ALPHA, BETA)
    first = repo.branch(f"codex/{ALPHA}")
    repo.commit("feat: alpha work", belongs_to=ALPHA)
    repo.checkout(repo.default_branch)
    second = repo.branch(f"codex/{BETA}")
    repo.commit("feat: beta work", belongs_to=BETA)
    repo.checkout(repo.default_branch)
    repo._git("merge", "-q", "--no-ff", "-m",
              f"Merge branches 'codex/{ALPHA}' and 'codex/{BETA}'", first, second)
    # Brings in both branches, so it belongs to both.
    repo.record(repo.head(), [ALPHA, BETA])
    return [ALPHA, BETA]


def octopus_subject_order_reversed(repo):
    """Octopus subject token order is not evidence of parent order."""
    _seed(repo, ALPHA, BETA)
    first = repo.branch(f"codex/{ALPHA}")
    repo.commit("feat: alpha work", belongs_to=ALPHA)
    repo.checkout(repo.default_branch)
    second = repo.branch(f"codex/{BETA}")
    repo.commit("feat: beta work", belongs_to=BETA)
    repo.checkout(repo.default_branch)
    repo._git(
        "merge",
        "-q",
        "--no-ff",
        "-m",
        f"Merge branches 'codex/{BETA}' and 'codex/{ALPHA}'",
        first,
        second,
    )
    repo.record(repo.head(), [ALPHA, BETA])
    return [ALPHA, BETA]


def octopus_mapping_ambiguous(repo):
    """Without corroborating refs, octopus side ownership is unavailable."""
    _seed(repo, ALPHA, BETA)
    first = repo.branch(f"codex/{ALPHA}")
    repo.commit("feat: alpha work", issue=ALPHA, belongs_to=ALPHA)
    repo.checkout(repo.default_branch)
    second = repo.branch(f"codex/{BETA}")
    repo.commit("feat: beta work", issue=BETA, belongs_to=BETA)
    repo.checkout(repo.default_branch)
    repo._git(
        "merge",
        "-q",
        "--no-ff",
        "-m",
        f"Merge branches 'codex/{BETA}' and 'codex/{ALPHA}'",
        first,
        second,
    )
    repo.record(repo.head(), [ALPHA, BETA])
    repo.delete_branch(first)
    repo.delete_branch(second)
    return [ALPHA, BETA]


def two_parent_multi_name_subject(repo):
    """Two-parent side ownership follows the parent ref, not token order."""
    _seed(repo, ALPHA, BETA)
    first = repo.branch(f"codex/{ALPHA}")
    repo.commit("feat: alpha work", belongs_to=ALPHA)
    repo.checkout(repo.default_branch)
    repo.merge(
        first,
        message=f"Merge codex/{BETA} and codex/{ALPHA}",
        belongs_to=[ALPHA, BETA],
    )
    return [ALPHA, BETA]


def two_parent_multi_name_ambiguous(repo):
    """Two distinct issue refs at parent2 make side ownership ambiguous."""
    _seed(repo, ALPHA, BETA)
    first = repo.branch(f"codex/{ALPHA}")
    repo.commit(
        "feat: alpha work",
        issue=ALPHA,
        belongs_to=ALPHA,
    )
    repo._git("branch", f"codex/{BETA}")
    repo.checkout(repo.default_branch)
    repo.merge(
        first,
        message=f"Merge codex/{BETA} and codex/{ALPHA}",
        belongs_to=[ALPHA, BETA],
    )
    return [ALPHA, BETA]


def two_parent_multi_name_ambiguous_no_trailer(repo):
    """FH-016: unresolved same-tip refs cannot guess no-trailer content."""
    _seed(repo, ALPHA, BETA)
    first = repo.branch(f"codex/{ALPHA}")
    repo.commit(
        "feat: ambiguous untrailed work",
        belongs_to=None,
    )
    repo._git("branch", f"codex/{BETA}")
    repo.checkout(repo.default_branch)
    repo.merge(
        first,
        message=f"Merge codex/{ALPHA} and codex/{BETA}",
        belongs_to=[ALPHA, BETA],
    )
    return [ALPHA, BETA]


def nested_ambiguous_merge_into_outer(repo):
    """FH-016: an inner unresolved side blocks broader outer ownership."""
    _seed(repo, ALPHA, BETA, GAMMA)
    first = repo.branch(f"codex/{ALPHA}")
    repo.commit(
        "feat: inner ambiguous work",
        belongs_to=None,
    )
    repo._git("branch", f"codex/{BETA}")
    repo.checkout(repo.default_branch)
    outer = repo.branch(f"codex/{GAMMA}")
    repo.commit("feat: gamma outer work", belongs_to=GAMMA)
    repo.merge(
        first,
        message=f"Merge codex/{ALPHA} and codex/{BETA}",
        belongs_to=[ALPHA, BETA, GAMMA],
    )
    repo.checkout(repo.default_branch)
    repo.merge(
        outer,
        message=f"Merge branch 'codex/{GAMMA}'",
        belongs_to=GAMMA,
    )
    repo.delete_branch(first)
    repo.delete_branch(f"codex/{BETA}")
    repo.delete_branch(outer)
    return [ALPHA, BETA, GAMMA]


ALL_SHAPES = {
    "happy_merge": happy_merge,
    "sync_merge_then_pr_merge": sync_merge_then_pr_merge,
    "stacked_live_branches": stacked_live_branches,
    "single_branch_clone": single_branch_clone,
    "detached_before_commit": detached_before_commit,
    "nested_merges": nested_merges,
    "nested_merges_reversed_issue_order": nested_merges_reversed_issue_order,
    "branch_name_not_matching_issue": branch_name_not_matching_issue,
    "disconnected_non_issue_base": disconnected_non_issue_base,
    "local_slash_branch_is_not_remote": local_slash_branch_is_not_remote,
    "divergent_same_tail_remotes": divergent_same_tail_remotes,
    "ambiguous_same_tail_remotes": ambiguous_same_tail_remotes,
    "local_with_divergent_same_tail_remotes": (
        local_with_divergent_same_tail_remotes
    ),
    "local_with_ambiguous_same_tail_remotes": (
        local_with_ambiguous_same_tail_remotes
    ),
    "trailer_outside_any_branch": trailer_outside_any_branch,
    "two_issues_interleaved": two_issues_interleaved,
    "empty_repository": empty_repository,
    "no_issue_commits_at_all": no_issue_commits_at_all,
    "non_main_default_branch": non_main_default_branch,
    "stale_local_default_branch": stale_local_default_branch,
    "two_registered_stacked_issues": two_registered_stacked_issues,
    "trailer_disagrees_with_branch": trailer_disagrees_with_branch,
    "octopus_merge": octopus_merge,
    "octopus_subject_order_reversed": octopus_subject_order_reversed,
    "octopus_mapping_ambiguous": octopus_mapping_ambiguous,
    "two_parent_multi_name_subject": two_parent_multi_name_subject,
    "two_parent_multi_name_ambiguous": two_parent_multi_name_ambiguous,
    "two_parent_multi_name_ambiguous_no_trailer": (
        two_parent_multi_name_ambiguous_no_trailer
    ),
    "nested_ambiguous_merge_into_outer": nested_ambiguous_merge_into_outer,
}


# Shapes that need the repository built differently, not just committed to
# differently.
REPO_KWARGS = {
    "non_main_default_branch": {"default_branch": "develop"},
}
