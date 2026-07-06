# Spec: Korean Human Review Packet

Issue: `057-korean-human-review-packet`

## Problem

ModuFlow intentionally keeps canonical artifacts in English to reduce token cost and preserve compatibility with tools, prompts, and external collaborators. That is still useful, but it makes human approval uncomfortable for Korean-speaking reviewers. A reviewer should not need to read every English spec, plan, review note, and PR handoff just to decide whether to approve, hold, or request changes.

## Goals

- Keep English artifacts canonical.
- Provide a Korean-first review surface for PR, review, and release gates.
- Make `product:pr` generate a per-issue `human-review.ko.md` packet.
- Make the dashboard issue detail page expose at least a Korean overview for every issue.
- Make missing full Korean sidecars visible instead of silently falling back to English.
- Let reviewers start from the Korean packet and drill down to English only when needed.

## Non-Goals

- No runtime translation API.
- No Korean canonical replacement.
- No full retro-translation requirement for every old artifact.
- No automatic approval or merge.
- No hidden machine translation that looks like reviewed Korean prose.

## Design

The model is layered:

1. English canonical artifacts remain the source of truth.
2. Korean sidecars such as `spec.ko.md`, `plan.ko.md`, `tasks.ko.md`, and `review.ko.md` provide human-readable equivalents when available.
3. `workspace/issue-descriptions.ko.json` provides short Korean issue descriptions for dashboard scanning.
4. Issue detail pages synthesize a Korean overview from that description so every issue has at least one Korean reading surface.
5. `human-review.ko.md` is the PR gate packet. It summarizes what changed, what to check, verification evidence, hold conditions, and approval checklist.

## Product Behavior

`product:pr {issue}` should run:

```bash
python3 scripts/project_pr.py <project-path> --issue-id {issue} --write
```

This writes:

- the issue's `pr.md`
- the issue's `human-review.ko.md`

The Korean packet links to:

- `memory/dashboard.html#issue-db`
- the dashboard issue detail page
- PR URL or local PR-ready marker
- key source artifacts

## Dashboard Behavior

The issue DB list shows Korean descriptions when present.

The issue detail page `한글` tab should show:

- Korean overview for every issue.
- Full Korean sidecars when present.
- Korean-only artifacts such as `human-review.ko.md`.

## Acceptance Criteria

- `project_pr.py --write` writes `human-review.ko.md` next to `pr.md`.
- `pr.md` links to the Korean packet.
- `product:pr` and `product:review` docs tell reviewers to start from the Korean packet.
- Dashboard issue detail pages show a Korean overview even when full sidecars are missing.
- Tests cover packet generation and detail-page Korean overview.
- `python3 scripts/release_check.py .` passes.

## Next Command

`product:plan 057-korean-human-review-packet`
