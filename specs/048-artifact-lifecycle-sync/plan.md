# Plan: Artifact Lifecycle Sync

Issue: `048-artifact-lifecycle-sync`
Spec: `specs/048-artifact-lifecycle-sync/spec.md` · Next: `product:execute 048`

## Decisions (from spec + advisor)

- Canonical = issue file `**Status:**`. Propagation flows issue → derived; never back.
- New module **`scripts/project_lifecycle.py`** (single responsibility; avoids bloating project_loop, which is the legacy loop machinery we're retiring from the gate).
- **Sequencing is mandatory** (advisor): reporter → reconcile → hard gate. Never gate before reconcile or 048's own commit breaks.

## Build order

### Step 1 — `project_lifecycle.py`: read canonical + detect drift (reporter only)
- `lifecycle_state(root)` → `{issues: {id: status}, active: [ids with status active], done: [...], backlog: [...], superseded: [...]}` parsed from `issues/*.md` `**Status:**` lines (reuse the 045 parser shape).
- `lifecycle_drift(root)` → list of disagreements via **consensus**, comparing:
  - issue files' active set vs `.moduflow/state.json` `active_issue`,
  - each issue's status vs how `dashboard.md` lists it (done issue must not sit in "Active Issue"; active issue must appear),
  - more than one active issue (ambiguous) → drift.
  - Returns `[]` when sources agree. Pure read, no writes.
- CLI: `--drift` (print report, exit 0 always at this step), `--state` (print lifecycle_state JSON).

### Step 2 — `--sync`: single propagation point (the writer)
- Regenerate `.moduflow/state.json` lifecycle fields from `lifecycle_state`: `active_issue` (the single active id, or ""), `phase` (infer: spec/plan/execute from that issue's `specs/<id>/` artifacts, else "select"). Preserve `active_goal`, `schema`. state.json has no prose → safe full rewrite of those fields.
- Regenerate **only** `dashboard.md`'s `## Active Issue` section body (between that header and the next `##`) from the active issue. Leave Recently-Completed / Queue / Verification / Blockers / **Next Command** (`product:status`) untouched — they carry human prose. Marker = the section header.
- Idempotent: running twice changes nothing.

### Step 3 — Reconcile today's divergence (the dogfood)
- Run `--sync` against this repo: brings `state.json` + dashboard's Active-Issue section into agreement with the issue files (active = 048).
- **Retire `loop-state.json` from the lifecycle gate**: point `validate_active_state_views` at `.moduflow/state.json` (`active_issue`) instead of `loop_state.active_issue_id`; drop the `loop-state.json next_command` coupling (`validate_next_command_matches_phase`) or guard it behind "loop-state present and live". Document loop-state as dormant/legacy in the file or a note. Keep `project_loop`/`mcp_server` reads working (shim: if loop-state absent, those paths no-op — verify).

### Step 4 — Promote drift to a gate (only after Step 3 is green)
- `project_doctor`: add `lifecycle_drift` to the report. After reconcile, surface it; wire into `release_check` expectations so real drift fails, in-sync passes.
- Keep the exit-0 discipline: the gate fails **only** on genuine disagreement, which Step 3 just cleared.

### Step 5 — Tests
- `lifecycle_state` parses statuses + derives active/done/backlog.
- `--sync` idempotence; updates a stale state.json/dashboard active section; preserves prose sections.
- `lifecycle_drift`: returns `[]` when in sync, flags a planted divergence (done issue listed active; state.active_issue ≠ issue files).
- `validate_active_state_views` now keys off state.json; passes when aligned, fails on drift.
- `release_check` exit 0 after reconcile.

## Risks / guards

- **Prose clobber**: sync touches only the Active-Issue section + state.json fields. Test asserts Recently-Completed/Verification survive.
- **Gate-before-reconcile**: Steps ordered so reconcile (3) precedes gate promotion (4).
- **loop-state consumers**: before retiring, grep confirms `project_loop --update`, `mcp_server`, `product-execute/loop/start` still function with loop-state dormant (read paths no-op when absent).

## Out of scope (confirmed)

- v1/v2 schema unification + consumer migration; execution-backend (021/028); full dashboard regeneration (prose stays hand-authored); live watcher.
