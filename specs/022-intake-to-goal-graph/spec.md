# Spec 022: Intake To Goal Graph

## Problem

ModuFlow accepts simple aliases such as `이거 해줘`, but before this issue the routing decision was only described in chat and command docs. A loose request could become an inbox item, an issue, an active-loop update, a business-plan flow, or a goal with several issues, but there was no deterministic artifact that explained why.

## Goal

Add a local intake router that classifies a raw request, checks existing issues for overlap, decides whether to attach to the active issue or create new work, and emits a JSON routing record that can be appended to `workspace/inbox.md`.

## Non-Goals

- Full semantic search or embeddings.
- Automatic creation of many issue files without review.
- External PM SaaS sync.
- Worker assignment or isolation. That belongs to `023-worker-routing-and-isolation`.

## Classification

The router classifies requests into:

- `dev`
- `planning`
- `design`
- `data`
- `docs`
- `ops`
- `research`
- `business`

Classification is rule-based and deterministic. It uses keyword scores plus a small bilingual alias table for common Korean/English overlap such as `로그인`/`login` and `버그`/`bug`.

## Routing Rules

Small request:

- If it overlaps the active issue, recommend `attach_active_issue`.
- If it does not overlap the active issue, recommend `create_issue`.

Large request:

- If it spans multiple domains or contains multiple work connectors, recommend `create_goal_with_issues`.
- Generate issue candidates, but do not create full issue files automatically.

Related request:

- Existing issue files are tokenized and compared with the request.
- Strong overlap becomes `duplicate_candidate`.
- Weaker useful overlap becomes `related`.

Low-friction write mode:

- `scripts/project_intake.py --write` appends the routing JSON to `workspace/inbox.md`.
- The inbox record is the safe mutation boundary for ambiguous or multi-issue intake.

## Output Schema

```json
{
  "schema": "moduflow.intake-routing.v1",
  "request": "로그인 버그 고쳐줘",
  "classification": {"primary": "dev", "scores": {"dev": 5}},
  "size": "small",
  "active_goal": "goal-auth",
  "active_issue": "042-login-bug-fix",
  "recommended_action": "attach_active_issue",
  "related_issues": [],
  "issue_candidates": [],
  "next_command": "product:execute 042-login-bug-fix",
  "updated_at": "2026-06-18"
}
```

## Acceptance Criteria

- `이거 해줘` requests can be routed without forcing users to pick artifact types.
- Dev and business requests classify correctly.
- Korean requests can match English issue titles for common product terms.
- Related issues are returned before creating a duplicate.
- Small active-loop requests attach to the active issue.
- Large multi-domain requests produce goal plus issue candidates.
- Write mode appends a durable intake record to `workspace/inbox.md`.

## Risks

- Rule-based classification can miss subtle intent. Mitigation: keep output explainable and allow inbox fallback.
- Candidate titles can be rough for Korean-only input. Mitigation: candidates are reviewable and not auto-created.
- Similarity thresholds can drift. Mitigation: cover duplicate/related behavior with unit tests and leave richer validation to 024.

## Next Command

`product:plan 022-intake-to-goal-graph`
