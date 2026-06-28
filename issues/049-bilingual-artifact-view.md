# Issue: `049-bilingual-artifact-view`

**Status: done** — created 2026-06-28, started 2026-06-28, done 2026-06-28. Part of goal `visual-workbench`, Axis A (view). Spun off from `045` to keep that issue's graph scope tight.

## Outcome

The 047 panel now shows Korean on demand while English stays canonical:

- **Sidecar convention**: `<name>.ko.md` beside the English `<name>.md`. `_ko_sidecar` attaches it as the artifact's `ko` field; `*.ko.md` is never listed as its own artifact.
- **Panel `English / 한글` toggle** (`render_issue_panel`): shown only when ≥1 sidecar exists; default English shows all artifacts in English; **한글 shows only artifacts that have a sidecar** (no English mixed in — artifacts without `.ko.md` are hidden in Korean mode). No `.ko.md` anywhere → panel behaves exactly as before.
- **New-artifacts-forward policy**: `commands/product-spec.md` documents writing `spec.ko.md` alongside new specs — convention, not a gate. No retro-translation; canonical file never translated in place.
- **Dogfood**: wrote `spec.ko.md` + `plan.ko.md` for 049; in 한글 mode the panel shows both rendered in Korean and hides the still-English issue header.

Tests: 34 pass (sidecar attach + not-listed-separately, toggle payload present-vs-absent). `release_check` exit 0. Stale-sidecar drift left as a future `--drift` extension (noted, out of scope).

## Scope decision (user, 2026-06-28)

English stays canonical ("영문으로 만드는 게 맞고"); only the **human-facing view** shows Korean ("사람이 보는 것만 한글로"); applied to **new artifacts going forward** ("신규부터 그렇게 하자") — existing English specs are not retro-translated. So: a Korean sidecar (`*.ko.md`) written alongside new artifacts, surfaced by the 047 panel via a language toggle. No runtime/machine translation (zero-backend).

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
