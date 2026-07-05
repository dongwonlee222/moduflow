# Issue 035: Team Issue Branch Pr Workflow

**Status: done** — completed 2026-06-26.

## Summary

Make ModuFlow practical for small teams and TFs by supporting a clear issue-to-branch-to-PR workflow that PMs can drive in natural language and developers can execute through Git.

## Source

- Type: user feedback / product direction
- Link: conversation, 2026-06-26
- Date: 2026-06-26

## Lifecycle

- Phase: status
- Created: 2026-06-26
- Started:
- Target End:
- Completed: 2026-06-26
- Last Updated: 2026-06-26

## Opportunity

ModuFlow already stores issues, specs, plans, status, and memory in Git. The next product step is to make that model usable by a small team where PMs create and prioritize work, developers pick up issues on branches, reviewers check PRs, and completed work turns into durable project memory.

The workflow must work without a hosted server or mandatory GitHub dependency, but it should optionally mirror to GitHub Issues and PRs when the team uses GitHub.

## Scope

### In

- Define a PM-friendly team workflow for creating, assigning, starting, reviewing, and completing issues.
- Add issue metadata for owner, assignee, reviewer, status, branch, PR, lock state, and last handoff.
- Define branch naming and start-work rules so two developers can avoid stepping on the same issue.
- Define PR/review/merge/done states that update Git-native artifacts first.
- Add team status views that summarize who owns what, what is blocked, and what needs review.
- Support `git-files` mode by default and `github-sync` mode as an optional mirror.
- Link completed issue outcomes to Issue 034 memory candidates so decisions and lessons can be reviewed before becoming permanent memory.

### Out

- Building a full hosted project management service.
- Replacing GitHub, GitLab, Linear, or Jira.
- Real-time collaborative editing or distributed locking beyond Git-visible state.
- Mandatory cloud sync.
- Automatic merge or deployment without review gates.

## Acceptance Criteria

- A PM can say "새 이슈 만들고 A에게 맡겨줘" and ModuFlow records the issue with owner/assignee/reviewer fields.
- A developer can start an assigned issue and get a deterministic branch name plus an updated active-work state.
- ModuFlow can show a team status summary: active work, review queue, blockers, and recently completed items.
- PR state can be linked back to the issue and status artifact in local Git files.
- Completion creates or recommends a memory candidate for durable decisions, tradeoffs, and follow-up context.
- The flow works in local `git-files` mode and can optionally mirror to GitHub Issues/PRs.
- Validation can detect obvious drift such as missing branch/PR links, duplicate active owners, or an issue marked done without required status/review evidence.

## Workflow Tasks

Every artifact-producing step is a tracked task here - never produce a spec/plan/design/review off the books. Check the box and link the artifact when done.

- [x] spec -> `specs/035-team-issue-branch-pr-workflow/spec.md`
- [x] plan -> `specs/035-team-issue-branch-pr-workflow/plan.md`
- [x] execute -> PR / commits
- [x] review -> `specs/035-team-issue-branch-pr-workflow/review.md`
- [x] release -> version, commit, and release notes
- [x] design -> issue assignment, branch, PR, and lock metadata
- [x] design -> PM-friendly team status and handoff UX
- [x] validation -> team workflow drift checks

## Related Issues

- blocks:
- blocked_by:
- duplicates:
- follows_up: `021-git-binding-and-execution-backend`, `022-intake-to-goal-graph`, `023-worker-routing-and-isolation`, `034-memory-capture-and-sync-workflow`
- supersedes:
- related: `024-artifact-schema-and-doctor-gates`, `029-antigravity-artifact-sync-connector`

## Sessions

- 2026-06-26: User asked whether two people can create issues, work through Git, and support team issue-to-work flows for small teams and TFs.
- 2026-06-26: Implemented team-state helpers, PM-friendly team status, PR state binding, completion-memory suggestions, validation drift checks, and command docs.

## Links

- Spec: `specs/035-team-issue-branch-pr-workflow/spec.md`
- Status: `specs/035-team-issue-branch-pr-workflow/status.md`
- Roadmap: `workspace/roadmap.md`

## Next Command

`/product:status`
