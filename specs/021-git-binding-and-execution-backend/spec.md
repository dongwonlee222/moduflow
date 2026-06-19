# Spec 021: Git Binding And Execution Backend

## Problem

ModuFlow can now recommend the next loop step, but it does not yet bind that work to Git evidence. Branches, commits, PRs, releases, and execution backend choices are still implied by chat or local practice. That makes it hard to tell which agent did the work, which branch belongs to the active issue, and whether a release can be traced back to a goal.

## Goal

Make Git the execution evidence layer for the loop. Every active issue can declare its branch, commits, PR, release, and selected execution backend while still working in local `git-files` mode. GitHub sync, Copilot Cloud Agent, and other remote executors remain optional upgrades.

## Non-Goals

- Full Copilot Cloud Agent API automation.
- Creating GitHub issues, PRs, or releases automatically.
- Worker file isolation or parallel worktree dispatch. That belongs to `023-worker-routing-and-isolation`.
- Rich artifact relationship validation beyond the Git binding checks needed here. That belongs to `024-artifact-schema-and-doctor-gates`.

## Branch Rule

Default branch names are issue-bound:

```text
codex/<issue-id>
```

Examples:

- `codex/021-git-binding-and-execution-backend`
- `codex/022-intake-to-goal-graph`

The `codex/` prefix matches the Codex desktop branch convention. Other backends may use their own prefix only if the issue ID remains present in the branch name.

## Loop State Binding

`workspace/loop-state.json` gains a `git_binding` object:

```json
{
  "git_binding": {
    "mode": "git-files",
    "branch": "codex/021-git-binding-and-execution-backend",
    "base_branch": "main",
    "commits": ["abc1234"],
    "pull_request": "https://github.com/org/repo/pull/21",
    "release": "v0.2.8",
    "execution_backend": {
      "type": "codex",
      "status": "recommended",
      "reason": "local Git-file artifact work fits Codex execution",
      "session": null
    }
  }
}
```

Required semantics:

- `mode`: `git-files` or `github-sync`.
- `branch`: optional but, when present, must include `active_issue_id`.
- `commits`: local commit hashes or remote commit IDs tied to the active issue.
- `pull_request`: optional mirror link.
- `release`: optional release tag or URL.
- `execution_backend.type`: `codex`, `claude-code`, `copilot-cloud-agent`, `openhands`, or `manual`.
- `execution_backend.status`: `not_selected`, `recommended`, `running`, `done`, or a backend-specific state string.

## Backend Selection

Default recommendation rules:

- High-risk work: `manual`, because the user should explicitly control the change.
- Docs/spec/planning work: `codex`, because it is local Git-file artifact work.
- Code work with GitHub available: `copilot-cloud-agent` can be recommended.
- Code work without GitHub available: `codex` is the default local backend.

The backend recommendation is advisory. `product:execute` can recommend an executor and record the choice, but it should not start a remote executor unless the user explicitly asks.

## Validation

Doctor and project validation should flag:

- declared `git_binding.branch` that does not include `active_issue_id`
- malformed loop-state JSON
- missing issue files referenced by loop state

Doctor may additionally report the current local Git branch and warn when it does not match the active issue, except for neutral branches such as `main` or `master`.

## Acceptance Criteria

- Loop state preserves a normalized `git_binding` object.
- Default issue branch recommendation is `codex/<issue-id>`.
- Validation catches declared branch/active issue mismatch.
- Doctor output includes current Git branch and declared Git binding.
- `product:execute` documents backend recommendation behavior instead of assuming ModuFlow is always the executor.
- Git-files mode works without GitHub or Copilot configuration.

## Risks

- Branch mismatch checks could be too strict on `main`. Mitigation: only hard-fail declared binding mismatch; current-branch mismatch is a doctor recommendation.
- Backend selection could overpromise remote automation. Mitigation: keep backend start out of scope and require explicit user intent for remote writes.
- Git binding could drift from issue lifecycle. Mitigation: 024 will strengthen cross-artifact doctor gates.

## Next Command

`product:plan 021-git-binding-and-execution-backend`
