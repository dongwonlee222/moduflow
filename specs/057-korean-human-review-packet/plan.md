# Plan: Korean Human Review Packet

Issue: `057-korean-human-review-packet`
Spec: `specs/057-korean-human-review-packet/spec.md` · Next: `product:execute 057-korean-human-review-packet`

## Implementation Shape

Make Korean-first human review a standard ModuFlow gate without replacing English canonical artifacts.

Issue 056 already dogfooded the core pieces:

- `project_pr.py --write` creates `human-review.ko.md`.
- `product:pr` documents GitHub preflight and local PR-ready fallback.
- Issue detail pages show a generated `한글 개요`.
- `workspace/issue-descriptions.ko.json` gives every issue a Korean dashboard description.

This issue formalizes and hardens that behavior so future review/release flows do not depend on ad hoc manual edits.

## Streams

### Stream A — PR Packet Generator

- Keep `scripts/project_pr.py` as the packet owner.
- Ensure `write_pr_handoff()` always writes both:
  - the issue's `pr.md`
  - the issue's `human-review.ko.md`
- Keep the Korean packet compact:
  - first links to dashboard and issue detail
  - Korean issue summary
  - source artifact checklist
  - verification summary
  - review findings
  - hold criteria
  - approval checklist
  - next action
- Preserve English canonical artifacts as the source of truth.

### Stream B — Review/Release Command Contract

- Update `commands/product-pr.md` to require GitHub PR preflight before `gh pr create`.
- Update `commands/product-review.md` to require `human-review.ko.md` before review completion.
- Update `commands/product-release.md` so release preparation checks for:
  - `human-review.ko.md`
  - human approval record
  - dashboard issue detail Korean overview
- Make failure modes explicit:
  - GitHub API/auth failure → local PR-ready
  - missing Korean sidecars → Korean overview fallback
  - missing Korean packet → review not complete

### Stream C — Dashboard Detail Surface

- Keep generated issue detail pages zero-backend.
- Ensure the `한글` tab is visible when any Korean material exists.
- Include generated `한글 개요` for every issue with a Korean description overlay.
- Include Korean-only artifacts such as `human-review.ko.md`.
- Keep full sidecar rendering for `spec.ko.md`, `plan.ko.md`, `tasks.ko.md`, `review.ko.md`, and similar files.

### Stream D — Validation And Tests

- Extend tests for:
  - `project_pr.py --write` writes the packet.
  - packet uses Korean description overlay.
  - GitHub PR preflight stops before `gh pr create` when auth/API is unavailable.
  - issue detail pages surface Korean overview.
  - Korean-only artifacts are visible in detail pages.
- Keep release gate green:
  - `python3 -m unittest discover -s tests`
  - `python3 scripts/validate_project_artifacts.py .`
  - `python3 scripts/validate_moduflow.py .`
  - `python3 scripts/release_check.py .`

### Stream E — Dogfood And Handoff

- Dogfood on Issue 056.
- Generate or refresh `specs/056-dashboard-database-list-view/human-review.ko.md`.
- Confirm `memory/issue-056-dashboard-database-list-view.html` exposes Korean review material.
- Record review/release evidence in 057 status and later review artifacts.

## Tests

Primary test files:

- `tests/test_project_pr.py`
- `tests/test_project_memory.py`

Required cases:

- `github_pr_preflight()` returns `local-pr-ready` when `gh auth status` or `gh api rate_limit` fails.
- `github_pr_preflight()` returns `github-draft-pr` when both checks pass.
- `write_pr_handoff()` writes `human-review.ko.md`.
- `build_human_review_packet_ko()` uses `workspace/issue-descriptions.ko.json`.
- `_collect_issue_artifacts()` includes Korean-only artifacts.
- `render_issue_panel()` exposes generated Korean overview.

## Manual QA

1. Run `python3 scripts/project_memory.py . --dashboard`.
2. Open `memory/dashboard.html#issue-db`.
3. Open any issue detail page.
4. Confirm `한글` tab appears when Korean overview exists.
5. Confirm 056 detail includes `한글 검토 패킷`.
6. Open `specs/056-dashboard-database-list-view/human-review.ko.md`.
7. Confirm a reviewer can approve or hold without reading the full English artifact set.

## Gates

- `python3 -m unittest tests.test_project_pr tests.test_project_memory`
- `python3 -m unittest discover -s tests`
- `python3 scripts/validate_project_artifacts.py .`
- `python3 scripts/validate_moduflow.py .`
- `python3 scripts/release_check.py .`

## Rollback

This change is additive. Rollback by reverting:

- `scripts/project_pr.py` Korean packet/preflight additions
- `commands/product-pr.md`, `commands/product-review.md`, `commands/product-release.md` contract changes
- dashboard detail Korean overview additions in `scripts/project_memory.py`
- related tests

Existing English canonical artifacts remain valid.

## Out Of Scope

- Runtime translation API.
- Replacing English canonical artifacts.
- Full retro-translation of all historical artifacts.
- Automatic merge approval.
- GitHub PR creation when `gh` auth or API preflight fails.
