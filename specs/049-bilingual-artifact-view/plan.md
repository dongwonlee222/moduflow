# Plan: Bilingual Artifact View

Issue: `049-bilingual-artifact-view`
Spec: `specs/049-bilingual-artifact-view/spec.md` · Next: `product:execute 049`

## Changes (small — extends the 047 panel)

1. **`_collect_issue_artifacts`** (`project_memory.py`): attach each artifact's `<name>.ko.md` sibling as a `ko` field (or `null`); exclude `*.ko.md` from being listed as its own artifact.
2. **`ISSUE_PANEL_TEMPLATE` / `render_issue_panel`**: add an `English / 한글` toggle (shown only when ≥1 sidecar exists). Refactor the render into a `render(lang)` function; 한글 picks `a.ko` when present, else falls back to `a.md` per-artifact; default English. Mermaid re-runs on each render.
3. **Policy** (`commands/product-spec.md`): document that new artifacts get a `.ko.md` sidecar written alongside — convention, not a gate. English stays canonical.

## Tests (`tests/test_project_memory.py`)

- sidecar attach: `spec.ko.md` present → artifact has `ko`; `*.ko.md` not listed as a separate artifact.
- panel: toggle markup present when a sidecar exists; absent (no clutter) when none.
- fallback: panel includes both EN and KO bodies in the payload so the client can switch; an artifact without a sidecar has `ko: null`.

## Gates

- `python3 -m unittest tests.test_project_memory` + `release_check` exit 0.
- Dogfood: write `specs/049-bilingual-artifact-view/spec.ko.md` (new artifact → Korean sidecar) and confirm the toggle renders it.

## Out of scope

- Stale-sidecar drift gate (noted as future `--drift` extension); retro-translating existing specs; machine translation; Korean-canonical.
