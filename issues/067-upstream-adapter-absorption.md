# Issue: `067-upstream-adapter-absorption`

**Status: done** — created 2026-07-05, started 2026-07-05, done 2026-07-05.

## Outcome

The adapters in `adapters/*.yaml` reflect the *current* state of their upstream sources instead of a frozen 2026-06-12 snapshot, and `vendor.lock.json`'s `last_synced` stamp means "content reviewed against this SHA" — not merely "SHA recorded". A recurring, relevance-filtered absorption pass exists so upstream drift gets absorbed, not just detected.

## Why

User raised it directly: "아답터 보면 클로드, git spec kit 그외 플러그인 스킬들 최신본도 업데이트 안되서" — the adapters/skills borrowed from upstream never track upstream's latest. Confirmed:

- `adapters/*.yaml` last touched 2026-06-12 (commit `72a0599`); since then upstream moved 100+ commits each for spec-kit, superpowers, and knowledge-work-plugins (superpowers shipped multiple releases incl. v6.1.1).
- `vendor/` contains only a README describing a checkout model that was never implemented — no upstream content was ever vendored.
- **Semantics flaw in `053`**: running `vendor_freshness.py --sync` on 2026-07-05 stamped `last_synced` = that day's SHAs *without any content review*, so the freshness gate now reports "up to date" while the adapters are 3+ weeks stale. The gate measures stamping, not absorption — it hid the debt the user is pointing at.
- Mapping inconsistencies: `adapters/documents.yaml` references source `codex-documents-presentations-spreadsheets` which does not exist in `vendor.lock.json`; `anthropic-skills` exists in the lock with no corresponding adapter.
- `adapters/superpowers.yaml` carried a hardcoded foreign path (`/Users/dongwon.lee/...`), same class as the INSTALL.md flaw fixed earlier today.

## Scope

### In

- Relevance-filtered upstream review (only the paths ModuFlow actually borrows): spec-kit spec/plan/tasks templates; superpowers execution-practice skills; knowledge-work-plugins product-management/productivity patterns; anthropic-skills (2 commits, both claude-api docs — confirmed irrelevant to PM patterns).
- Update `adapters/*.yaml` with findings: a `reviewed` block (sha + date + summary of what changed upstream and whether it was absorbed or intentionally skipped).
- Fix `adapters/superpowers.yaml` hardcoded `local_path`.
- Reconcile adapter↔lock mapping: add `codex-documents-presentations-spreadsheets` to `vendor.lock.json` (or re-point the adapter), note `anthropic-skills`' adapterless role.
- Redefine `--sync` semantics in `commands/product-sync.md`: stamping `last_synced` requires an actual review; record what was reviewed.

### Out

- No vendored checkouts under `vendor/<id>/` — the review-and-absorb model works without carrying upstream code in-repo; revisit only if adapters start needing file-level diffs routinely.
- No automated absorption (an agent auto-rewriting adapters from upstream diffs) — review stays human/agent-judged per pass.
- No changes to the `type: local-plugin` Codex sources' pins (version-string pinned, separate mechanism).

## Acceptance Criteria

- Each github-source adapter records the upstream SHA it was reviewed against and what was absorbed/skipped.
- `adapters/superpowers.yaml` has no machine-specific absolute path.
- `vendor.lock.json` and `adapters/*.yaml` sources reconcile 1:1 (or the exception is documented).
- `commands/product-sync.md` states the review-before-stamp rule.
- `python3 scripts/release_check.py .` passes.

## Related Issues

- follows_up: `053-vendor-freshness-gate` (built detection; this issue fixes what detection alone couldn't — absorption, and the stamp-without-review semantics hole)
- related: `065-installed-plugin-staleness-detection` (same "our own copies drift silently" theme, other direction)

## Workflow Tasks

- [x] execute → `adapters/spec-kit.yaml`, `adapters/superpowers.yaml`, `adapters/product-management.yaml`, `adapters/productivity.yaml`, `commands/product-plan.md`, `commands/product-review.md`, `commands/product-sync.md`, `vendor.lock.json`

## Sessions

- 2026-07-05: User clarified the staleness complaint targets the upstream adapters (spec-kit, superpowers, skills), not the installed moduflow plugin. Quantified drift (100+ commits each since adapters' last touch 2026-06-12), found the `--sync` stamp-without-review semantics hole, launched relevance-filtered upstream reviews.
- 2026-07-05: Reviews complete (3 subagents + inline). Findings: spec-kit spec/plan/tasks templates unchanged since 2026-05-12 (all churn is CLI/integrations); knowledge-work-plugins product-management/ and productivity/ trees have zero commits since 2026-06-12 (path-filtered); anthropic-skills' 2 commits are claude-api docs, irrelevant; **superpowers v6.0.0-v6.1.1 substantially changed subagent-driven-development and writing-plans**. Absorbed into ModuFlow: review integrity rules (read-only reviewers, no finding suppression, dual spec/quality verdicts + "can't verify") into `product-review.md`; plan structure (Global Constraints, per-task Interfaces, task right-sizing) into `product-plan.md`. Skipped (documented in adapter): SDD file-handoff scripts and model-tier mechanics — harness-specific. All 4 github-source adapters now carry `reviewed:` blocks; `vendor.lock.json` gained the missing `codex-documents-presentations-spreadsheets` entry; stamp rule added to `product-sync.md`. Done.

## Links

- Roadmap: `workspace/roadmap.md`
- Freshness gate: `scripts/vendor_freshness.py` (issue `053`)

## Next Command

`/product:execute 067-upstream-adapter-absorption`
