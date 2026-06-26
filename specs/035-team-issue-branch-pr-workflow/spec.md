# Spec: Team Issue Branch PR Workflow

## Issue

`035-team-issue-branch-pr-workflow`

## Source Request

Small teams and TFs should be able to use ModuFlow to create issues, assign work, branch in Git, open/review PRs, complete work, and preserve reusable memory without requiring every user to be a developer.

## Problem

ModuFlow's Git-native artifact model is strong for durability, but the team workflow is still implicit. PMs need a natural workflow for creating and tracking work, while developers need deterministic branch and PR conventions. Without a shared lifecycle, two people can work on the same issue, PR status can drift from issue status, and completed lessons may not be captured as memory.

## Goals

- Make the default team workflow understandable to PMs and executable by developers.
- Keep Git-tracked files as the canonical state.
- Let GitHub Issues/PRs act as mirrors when available, not as required infrastructure.
- Make active ownership, review state, blockers, and handoffs visible.
- Reuse Issue 034 memory candidates when work completes.

## Non-Goals

- Build a hosted project-management backend.
- Depend on GitHub authentication for local team use.
- Auto-merge branches or bypass review.
- Store private personal memory inside shared project artifacts.

## User Flows

### PM Creates Work

1. PM says: "이 기능 이슈로 만들고 민수에게 맡겨줘."
2. ModuFlow checks for similar issues.
3. ModuFlow creates or updates an issue with owner, assignee, reviewer, priority, and next command.
4. Team status shows the new issue under assigned work.

### Developer Starts Work

1. Developer says: "035 시작해줘" or "내 작업 시작."
2. ModuFlow checks whether the issue is already locked or active for another assignee.
3. ModuFlow recommends or creates a branch name such as `codex/035-team-issue-branch-pr-workflow`.
4. ModuFlow updates the issue/status artifacts with branch, assignee, started_at, and active state.

### Developer Opens PR

1. Developer finishes implementation and asks for review or PR.
2. ModuFlow verifies required artifacts and tests.
3. In `git-files` mode, ModuFlow records PR-ready status and review notes.
4. In `github-sync` mode, ModuFlow can mirror to a GitHub PR and store the PR URL back in the issue.

### Reviewer Completes Review

1. Reviewer checks the PR, status artifact, and validation output.
2. ModuFlow records review result, requested changes, or approval.
3. If approved and merged, ModuFlow marks the issue complete.
4. ModuFlow creates or recommends memory candidates for decisions, risks, lessons, and follow-up context.

### PM Checks Team Status

1. PM says: "팀 상태 보여줘."
2. ModuFlow summarizes assigned work, active branches, review queue, blockers, and recent completions.
3. The summary uses project artifacts first and GitHub mirrors only when configured.

## Data Model

Team workflow state should be represented in Git-visible artifacts before any external mirror.

Suggested issue metadata:

- `owner`: accountable PM or decision maker.
- `assignee`: person currently responsible for execution.
- `reviewer`: expected reviewer or approver.
- `status`: proposed, ready, active, blocked, review, approved, done, archived.
- `branch`: active or expected branch name.
- `pr`: local PR-ready marker or external PR URL.
- `lock_state`: none, recommended, active, stale, released.
- `locked_by`: current active worker when known.
- `last_handoff`: short latest handoff summary.
- `memory_candidates`: candidate memory files generated from completion.

## Command Surface

Natural-language aliases should map to existing or new product commands:

- "새 이슈 만들어줘" -> `product:issue`
- "A에게 맡겨줘" -> issue assignment update
- "035 시작해줘" -> issue start + branch binding
- "PR 준비해줘" -> `product:pr`
- "리뷰 요청해줘" -> `product:review`
- "팀 상태 보여줘" -> `product:status` or future `product:handoff`
- "완료 처리해줘" -> guarded completion + memory candidate recommendation

## GitHub Sync Policy

- `git-files` is the default and must work offline.
- `github-sync` mirrors issue/PR state when `origin` and `gh` auth are available.
- GitHub links are stored back into the canonical issue/status artifacts.
- If GitHub sync fails, ModuFlow keeps local artifacts valid and reports the mirror failure separately.

## Memory Capture

On issue completion, ModuFlow should suggest memory candidates for:

- product decisions made during the issue
- workflow patterns worth repeating
- failed approaches that should not be retried
- PR/review lessons
- release notes or customer-facing implications

Memory candidates remain reviewable before approval, following Issue 034.

## Open Questions

- Should active locks live only in issue/status files, or also in a small workspace team-state index?
- Should branch creation be automatic by default, or recommended until the user confirms?
- How much GitHub Issue/PR creation should be automatic when `github-sync` is configured?
- Should team status support per-person filters in v1?

## Next Command

`/product:plan 035-team-issue-branch-pr-workflow`
