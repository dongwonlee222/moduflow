# Issue: `049-bilingual-artifact-view`

**Status: backlog** — created 2026-06-28. Part of goal `visual-workbench`, Axis A (view). Spun off from `045` to keep that issue's graph scope tight.

## Goal

Let a human read an issue's artifacts (spec / plan / tasks …) **in Korean** when reviewing, while keeping the **English Markdown canonical**. Decided with the user: don't translate at runtime (외부 API → breaks zero-backend) and don't overwrite the English; instead **generate a separate Korean version** that the 047 panel can surface on demand.

## Why

The 047 artifact panel renders the stored Markdown as-is, and current specs are written in English. The user wants "사람이 확인할 때만 한글 버전" — a review aid, not a source-of-truth change.

## Decisions so far (from the user)

- English artifact stays canonical (`spec.md` etc.) — unchanged.
- A Korean version is a **separate file** (convention to decide in spec, e.g. `spec.ko.md` beside `spec.md`).
- The 047 panel offers a **language toggle** (영문 / 한글) that shows the `.ko.md` when present; falls back to English when absent (selective, like everything else — never a forced empty Korean section).

## Scope (decide in spec)

- File convention for the Korean version (`<name>.ko.md` sidecar vs a `i18n/ko/` dir).
- Who writes it: AI-generated on request (a command like `product:translate <id>`) vs authored alongside. Likely a command that writes the `.ko.md` sidecar from the English source; the human reviews it. **No runtime/browser translation.**
- 047 panel: language toggle, per-artifact fallback, label in Korean.
- Drift handling: when English changes, the `.ko.md` is stale — flag it (ties to `048-artifact-lifecycle-sync`).

## Out of Scope

- Translating UI chrome (already Korean via 045).
- Machine translation inside the panel (zero-backend constraint).
- Translating memory entries (separate if needed).

## Related

- `045-issue-graph-visualization` (the panel this extends; spun off from it)
- `047-issue-artifact-drilldown` (the panel that gets the toggle)
- `046-planning-artifact-templates` (where a "write Korean alongside" policy could live)
- `048-artifact-lifecycle-sync` (stale-translation drift detection)
