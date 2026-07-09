---
description: Review issue/spec/work across PM, UX, data, QA, and release gates.
argument-hint: "<issue id>"
---

# /product:review

Run staged verification.

## Do

1. Assign review concerns to workers where useful.
2. Check acceptance criteria, tests, UX, metrics, release risk, and docs.
   - For frontend or API-backed browser work, check whether the copied `templates/frontend-qa/` evidence exists, is linked from the plan, and has explicit pass/fail/not-applicable decisions.
3. Ensure `specs/<issue>/review-handoff.md` exists; if missing, generate it:

```bash
python3 scripts/project_execution.py <project-path> --issue-id <issue id> --review-handoff --write
```

4. Generate the dashboard visual inspection surface before concluding review:

```bash
python3 scripts/project_memory.py <project-path> --dashboard
python3 scripts/project_memory.py <project-path> --issue <issue id>
```

5. Run the converge pass as the final evidence step (issue 071): collect evidence with `python3 scripts/project_converge.py <project-path> --issue-id <issue id> --evidence --json`, dispatch the judge subagent with `templates/converge-judgment-prompt.md` + the evidence JSON inline (coordinator judges and records the limitation if dispatch is unavailable), then `python3 scripts/project_converge.py <project-path> --issue-id <issue id> --apply-judgment specs/<issue id>/converge-judgment.json`. Converge findings are review evidence — include `specs/<issue>/converge.md` in status.md's evidence list. Converge never blocks the review verdict (`no_evidence` or a failed run is reported, not gating), but must be reported.

6. Save subagent findings, verification output, the dashboard path `memory/dashboard.html`, the issue drill-down path `memory/issue-<issue>.html`, and converge report `specs/<issue>/converge.md` to `specs/<issue>/status.md`.
7. Ensure `specs/<issue>/pr.md` and `specs/<issue>/human-review.ko.md` exist or refresh them so PR review carries the same verification, dashboard evidence, and Korean human-review surface:

```bash
python3 scripts/project_pr.py <project-path> --issue-id <issue id> --write
```

8. Reconcile issue workflow tasks, `tasks.md`, `.moduflow/state.json`, and `workspace/dashboard.md` before reporting completion. A completed review should not leave the issue routing back to `product:execute`.

## Subagent Review

When the host-subagent execution backend is supported, `product:review` should dispatch specialized review tasks directly to subagents:
- `qa-reviewer` to run all test suites (`discover`), project doctor checks, and verify acceptance criteria.
- `pm-strategist` / `spec-architect` to review file changes against the spec design.

The host agent must call `invoke_subagent` to execute these reviews, and document the subagents' findings in `specs/<issue>/status.md` before concluding the review phase.

If the current host exposes a different subagent tool, map the handoff's worker sections to that tool. If no subagent tool is available, record that limitation in `status.md` and perform the same review concerns inline; do not silently skip review.

Review integrity rules (absorbed from Superpowers v6 subagent-driven-development, issue `067`):

- Reviewers are **read-only**: a review task never mutates the working tree or branches; it reports.
- The coordinating agent must **not suppress or pre-rate reviewer findings** — every finding reaches `status.md` as reported; severity judgment and dismissal belong to the human (or an explicitly recorded decision), not to the agent that dispatched the review.
- Each review verdict answers two questions separately: does the change match the spec (spec compliance), and is the change well-built (quality)? "Can't verify from the diff" is a valid verdict and must be recorded rather than rounded up to a pass.
- **Constitution compliance (issue 073)**: every review verdict includes a constitution-check line against `workspace/constitution.md` — `Constitution: v<X.Y> checked — no violations` or the explicit violation list (C-refs). An amendment adopted without a logged human approval is itself a violation to report.

## Visual Review Gate

Review is not complete until the dashboard and issue drill-down views have been generated or the failure is documented:

- Dashboard command: `python3 scripts/project_memory.py <project-path> --dashboard`
- Dashboard output: `memory/dashboard.html`
- Issue drill-down command: `python3 scripts/project_memory.py <project-path> --issue <issue id>`
- Issue drill-down output: `memory/issue-<issue>.html`
- Converge report: `specs/<issue>/converge.md` (spec↔code divergence audit, non-blocking)
- If an in-chat visualization/browser surface is available, open or render the HTML there for inspection. Otherwise, final user-facing report must include the output path.

## PR Evidence Gate

Review is not complete until the PR handoff has the same evidence a human needs in GitHub:

- PR handoff: `specs/<issue>/pr.md`
- Korean human-review packet: `specs/<issue>/human-review.ko.md`
- PR state command: `python3 scripts/project_workflow.py <project-path> --pr-state --issue-id <issue id> --pr "<draft-pr-url-or-local-marker>" --reviewer "Reviewer"`
- Required evidence: summary, verification, dashboard path, issue drill-down path, review findings, and human approval checkpoints.
- If a GitHub PR exists, mirror the evidence into the PR body or a PR comment. If GitHub sync fails, keep `pr.md` current and report the mirror failure separately.

For Korean reviewers, the packet is the first review surface. The dashboard detail page's `한글` tab must at least show a Korean overview, and any missing full Korean sidecars should be visible as a review limitation rather than hidden.

## Next

- `/product:plan` if gaps require more work
- `/product:pr` if review passes
