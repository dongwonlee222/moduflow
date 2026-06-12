# Team Workflow Spec

## Problem

When multiple people use ModuFlow, issues and specs need explicit states, roles, review gates, approval history, risks, and handoff notes. Without these artifacts, teams cannot audit who owns work, who reviewed it, and what remains blocked.

## Users

- Project owners coordinating multiple contributors.
- Reviewers and approvers checking readiness.
- Agents preparing release, risk, and handoff summaries.

## Goals

- Define standard workflow states and roles.
- Add a `workflow/` structure for review gates, approval policy, release policy, handoff, and risks.
- Add a script to initialize workflow files and create workflow records.
- Keep the workflow useful in `git-files` mode.
- Preserve existing files.

## Non-Goals

- Enterprise permission enforcement.
- Replacing GitHub branch protections.
- Replacing legal approval systems.

## Artifact Structure

```text
workflow/
  review-gates.md
  approval-policy.md
  release-policy.md
  handoff.md
  risks.md
```

## Standard States

- `draft`
- `ready-for-review`
- `approved`
- `in-progress`
- `blocked`
- `released`
- `archived`

## Standard Roles

- `owner`
- `reviewer`
- `implementer`
- `approver`
- `stakeholder`

## Requirements

- `scripts/project_workflow.py` supports dry-run initialization by default.
- `scripts/project_workflow.py --write` creates missing workflow files only.
- Existing workflow files are never overwritten.
- The script can create a workflow record with issue ID, state, owner, reviewers, approver, blocker, and next command.
- `project_doctor.py` reports `workflow.initialized` and `workflow.missing`.
- Commands exist for `product:handoff` and `product:risks`.

## Acceptance Criteria

- A project can initialize workflow policy files.
- A workflow record includes state, owner, reviewers, approver, blockers, and next command.
- Doctor recommends `product:handoff --write` or workflow initialization when missing.
- Validator requires the new script, commands, and templates.

## Next Command

`product:plan 005-team-workflow`
