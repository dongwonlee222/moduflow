#!/usr/bin/env python3
"""Repository shapes for differential testing (issue 095, review round 3).

Each builder returns (repo, issue_ids). The shapes are chosen for what the
implementation's author had least reason to try — three review rounds showed
that the happy shape (branch from main, commit, merge) is the only one the
original fixtures built, and every defect lived outside it.

Shapes marked LIVE are arrangements that exist in the ModuFlow repository
today; the rest are arrangements git permits and the resolver must survive.
"""
ALPHA = "101-alpha"
BETA = "102-beta"


def _seed(repo, *issue_ids):
    repo.commit("chore: unrelated base one")
    repo.commit("chore: unrelated base two")
    for issue_id in issue_ids:
        repo.add_issue_file(issue_id)


def happy_merge(repo):
    """The only shape the original fixtures built."""
    _seed(repo, ALPHA)
    name = repo.branch(f"codex/{ALPHA}")
    repo.commit("feat: alpha work")
    repo.checkout("main")
    repo.merge(name, message=f"Merge branch 'codex/{ALPHA}'")
    return [ALPHA]


def sync_merge_then_pr_merge(repo):
    """LIVE. `Merge branch 'main' into codex/X` names the issue in its subject
    while merging main *into* the branch — claiming its second-parent side
    attributes the whole base branch to the issue."""
    _seed(repo, ALPHA)
    name = repo.branch(f"codex/{ALPHA}")
    repo.commit("feat: alpha work")
    repo.checkout("main")
    repo.commit("chore: main moved on one")
    repo.commit("chore: main moved on two")
    repo.checkout(name)
    repo.merge("main", message=f"Merge branch 'main' into codex/{ALPHA}")
    repo.checkout("main")
    repo.merge(name, message=f"Merge pull request #9 from o/codex/{ALPHA}")
    return [ALPHA]


def stacked_live_branches(repo):
    """LIVE (codex/089-… and codex/089-…-release). A follow-up branch built on
    top of another; excluding by name lets the descendant zero its parent."""
    _seed(repo, ALPHA, BETA)
    first = repo.branch(f"codex/{ALPHA}")
    repo.commit("feat: alpha one")
    repo.commit("feat: alpha two")
    second = repo.branch(f"codex/{BETA}")
    repo.commit("feat: beta on top of alpha")
    repo.publish(first)
    repo.publish(second)
    repo.checkout("main")
    return [ALPHA, BETA]


def single_branch_clone(repo):
    """`clone --single-branch` / CI checkout: the issue branch is the only ref
    besides its own counterpart, so a name-based exclusion list is empty."""
    _seed(repo, ALPHA)
    name = repo.branch(f"codex/{ALPHA}")
    repo.commit("feat: alpha work")
    repo.publish(name)
    return [ALPHA]


def detached_before_commit(repo):
    """Detach first, then commit — the commit is on no branch at all. The
    original detached-HEAD fixture detached afterwards, leaving the commit on
    main where the arrangement cannot bite."""
    _seed(repo, ALPHA)
    repo.detach()
    repo.commit("feat: work with trailer", issue=ALPHA)
    repo.commit("feat: more work", issue=ALPHA)
    return [ALPHA]


def nested_merges(repo):
    """Branch A merged into branch B, then B merged to main. A's commits must
    stay A's."""
    _seed(repo, ALPHA, BETA)
    first = repo.branch(f"codex/{ALPHA}")
    repo.commit("feat: alpha one")
    repo.checkout("main")
    second = repo.branch(f"codex/{BETA}")
    repo.commit("feat: beta one")
    repo.merge(first, message=f"Merge branch 'codex/{ALPHA}'")
    repo.checkout("main")
    repo.merge(second, message=f"Merge branch 'codex/{BETA}'")
    return [ALPHA, BETA]


def branch_name_not_matching_issue(repo):
    """LIVE (codex/092-current-dashboard-korean vs 092-project-home-dashboard).
    A branch whose name is not the issue id it belongs to."""
    _seed(repo, ALPHA)
    name = repo.branch("codex/199-unregistered-name")
    repo.commit("feat: work under a non-conforming branch")
    repo.publish(name)
    repo.checkout("main")
    return [ALPHA]


def trailer_outside_any_branch(repo):
    """A trailer-bearing commit merged and then its branch deleted, plus one
    committed straight to main."""
    _seed(repo, ALPHA)
    repo.commit("feat: straight to main", issue=ALPHA)
    name = repo.branch(f"codex/{ALPHA}")
    repo.commit("feat: on branch", issue=ALPHA)
    repo.checkout("main")
    repo.merge(name, message=f"Merge branch 'codex/{ALPHA}'")
    repo.delete_branch(name)
    return [ALPHA]


def two_issues_interleaved(repo):
    _seed(repo, ALPHA, BETA)
    first = repo.branch(f"codex/{ALPHA}")
    repo.commit("feat: alpha", issue=ALPHA)
    repo.checkout("main")
    second = repo.branch(f"codex/{BETA}")
    repo.commit("feat: beta")
    repo.checkout("main")
    repo.merge(first, message=f"Merge branch 'codex/{ALPHA}'")
    repo.merge(second, message=f"Merge branch 'codex/{BETA}'")
    return [ALPHA, BETA]


def empty_repository(repo):
    return [ALPHA]


def no_issue_commits_at_all(repo):
    repo.commit("chore: one")
    repo.commit("chore: two")
    return [ALPHA]


def non_main_default_branch(repo):
    """A repository whose trunk is not called `main`. Review finding N1:
    ground truth 2, both implementation and oracle 0, differential agreeing —
    unreachable while the builder hardcoded `-b main`."""
    _seed(repo, ALPHA)
    name = repo.branch(f"codex/{ALPHA}")
    repo.commit("feat: alpha work")
    repo.publish(name)
    repo.checkout(repo.default_branch)
    return [ALPHA]


def stale_local_default_branch(repo):
    """Review finding Q4. `origin/main` has moved ahead of local `main`; a
    name list that tries `main` first measures the branch against a base that
    is four commits behind, and hands the issue all four."""
    _seed(repo, ALPHA)
    repo.publish("main")
    repo.commit("chore: main moved one")
    repo.commit("chore: main moved two")
    repo.publish("main")
    stale = repo.head()
    name = repo.branch(f"codex/{ALPHA}")
    repo.commit("feat: alpha work")
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
    repo.commit("feat: alpha one")
    repo.commit("feat: alpha two")
    second = repo.branch(f"codex/{BETA}")
    repo.commit("feat: beta on top of alpha")
    repo.publish(first)
    repo.publish(second)
    repo.checkout(repo.default_branch)
    return [ALPHA, BETA]


def octopus_merge(repo):
    """Review finding N2. Two branches merged at once; the second-parent-only
    walk loses everything past `^2`, and the reviewer measured an entire
    issue's work attributed to nothing."""
    _seed(repo, ALPHA, BETA)
    first = repo.branch(f"codex/{ALPHA}")
    repo.commit("feat: alpha work")
    repo.checkout(repo.default_branch)
    second = repo.branch(f"codex/{BETA}")
    repo.commit("feat: beta work")
    repo.checkout(repo.default_branch)
    repo._git("merge", "-q", "--no-ff", "-m",
              f"Merge branches 'codex/{ALPHA}' and 'codex/{BETA}'", first, second)
    return [ALPHA, BETA]


ALL_SHAPES = {
    "happy_merge": happy_merge,
    "sync_merge_then_pr_merge": sync_merge_then_pr_merge,
    "stacked_live_branches": stacked_live_branches,
    "single_branch_clone": single_branch_clone,
    "detached_before_commit": detached_before_commit,
    "nested_merges": nested_merges,
    "branch_name_not_matching_issue": branch_name_not_matching_issue,
    "trailer_outside_any_branch": trailer_outside_any_branch,
    "two_issues_interleaved": two_issues_interleaved,
    "empty_repository": empty_repository,
    "no_issue_commits_at_all": no_issue_commits_at_all,
    "non_main_default_branch": non_main_default_branch,
    "stale_local_default_branch": stale_local_default_branch,
    "two_registered_stacked_issues": two_registered_stacked_issues,
    "octopus_merge": octopus_merge,
}


# Shapes that need the repository built differently, not just committed to
# differently.
REPO_KWARGS = {
    "non_main_default_branch": {"default_branch": "develop"},
}
