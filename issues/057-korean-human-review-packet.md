# Issue: `057-korean-human-review-packet`

**Status: backlog** — spec drafted 2026-07-03.

## Outcome

ModuFlow generates a Korean human-review packet for PR/review/release gates, so Korean-speaking reviewers can approve or request changes without reading every English canonical artifact.

## Why

English canonical artifacts are useful for interoperability and tool compatibility, but human approval is currently uncomfortable because the PR handoff, review notes, and checklist are mostly English. The user needs a compact Korean review surface that answers:

- What changed?
- What must I check?
- What passed?
- What can I ignore?
- Should I approve, hold, or request changes?

Issue 049 added Korean sidecars for human-facing artifact views, but the policy mostly covered spec/plan style artifacts. PR/review/release gates need a stronger Korean-first review packet.

## Scope

### In

- Add a Korean human-review packet convention such as `specs/<issue>/human-review.ko.md`.
- Make `product:review` and/or `product:pr` generate or refresh the packet.
- Include: PR link, summary, files to check, verification summary, dashboard links, approval checklist, hold criteria, and next command.
- Link the packet from `specs/<issue>/pr.md`, issue file, and dashboard issue drill-down.
- Keep English canonical artifacts unchanged.
- Dogfood on Issue 034.

### Out

- No runtime translation API.
- No Korean canonical replacement.
- No full retro-translation of every old artifact.
- No automatic merge approval.

## Acceptance Criteria

- `product:pr <issue>` or `product:review <issue>` produces `specs/<issue>/human-review.ko.md`.
- PR handoff links to the Korean packet.
- The packet contains an explicit approval checklist and hold criteria.
- Dashboard issue drill-down can surface the Korean packet when present.
- Tests cover packet generation and issue artifact collection.
- `python3 scripts/release_check.py .` passes.

## Related Issues

- follows_up: `049-bilingual-artifact-view`
- related: `051-autonomous-execute-review-visual-handoff`
- related: `052-draft-pr-review-handoff`
- related: `056-dashboard-database-list-view`

## Sessions

- 2026-07-03: User said PR review is hard because the check surface is English and inconvenient. Created this improvement and dogfooded a Korean review packet for Issue 034.

## Links

- Dogfood packet: `specs/034-memory-capture-and-sync-workflow/human-review.ko.md`
- Spec: `specs/057-korean-human-review-packet/spec.md`
- Spec KO: `specs/057-korean-human-review-packet/spec.ko.md`
- Roadmap: `workspace/roadmap.md`

## Next Command

`/product:plan 057-korean-human-review-packet`
