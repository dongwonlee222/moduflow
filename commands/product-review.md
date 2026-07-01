---
description: Review issue/spec/work across PM, UX, data, QA, and release gates.
argument-hint: "<issue id>"
---

# /product:review

Run staged verification.

## Do

1. Assign review concerns to workers where useful.
2. Check acceptance criteria, tests, UX, metrics, release risk, and docs.
3. Ensure `specs/<issue>/review-handoff.md` exists; if missing, generate it:

```bash
python3 scripts/project_execution.py <project-path> --issue-id <issue id> --review-handoff --write
```

4. Generate the dashboard visual inspection surface before concluding review:

```bash
python3 scripts/project_memory.py <project-path> --dashboard
python3 scripts/project_memory.py <project-path> --issue <issue id>
```

5. Save subagent findings, verification output, the dashboard path `memory/dashboard.html`, and the issue drill-down path `memory/issue-<issue>.html` to `specs/<issue>/status.md`.
6. Ensure `specs/<issue>/pr.md` exists or refresh it so PR review carries the same verification and dashboard evidence:

```bash
python3 scripts/project_pr.py <project-path> --issue-id <issue id> --write
```

7. Reconcile issue workflow tasks, `tasks.md`, `.moduflow/state.json`, and `workspace/dashboard.md` before reporting completion. A completed review should not leave the issue routing back to `product:execute`.

## Subagent Review

When the host-subagent execution backend is supported, `product:review` should dispatch specialized review tasks directly to subagents:
- `qa-reviewer` to run all test suites (`discover`), project doctor checks, and verify acceptance criteria.
- `pm-strategist` / `spec-architect` to review file changes against the spec design.

The host agent must call `invoke_subagent` to execute these reviews, and document the subagents' findings in `specs/<issue>/status.md` before concluding the review phase.

If the current host exposes a different subagent tool, map the handoff's worker sections to that tool. If no subagent tool is available, record that limitation in `status.md` and perform the same review concerns inline; do not silently skip review.

## Visual Review Gate

Review is not complete until the dashboard and issue drill-down views have been generated or the failure is documented:

- Dashboard command: `python3 scripts/project_memory.py <project-path> --dashboard`
- Dashboard output: `memory/dashboard.html`
- Issue drill-down command: `python3 scripts/project_memory.py <project-path> --issue <issue id>`
- Issue drill-down output: `memory/issue-<issue>.html`
- If an in-chat visualization/browser surface is available, open or render the HTML there for inspection. Otherwise, final user-facing report must include the output path.

## PR Evidence Gate

Review is not complete until the PR handoff has the same evidence a human needs in GitHub:

- PR handoff: `specs/<issue>/pr.md`
- PR state command: `python3 scripts/project_workflow.py <project-path> --pr-state --issue-id <issue id> --pr "<draft-pr-url-or-local-marker>" --reviewer "Reviewer"`
- Required evidence: summary, verification, dashboard path, issue drill-down path, review findings, and human approval checkpoints.
- If a GitHub PR exists, mirror the evidence into the PR body or a PR comment. If GitHub sync fails, keep `pr.md` current and report the mirror failure separately.

## Next

- `/product:plan` if gaps require more work
- `/product:pr` if review passes
