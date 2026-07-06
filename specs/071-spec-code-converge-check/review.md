# Review: 071-spec-code-converge-check

Issue: `071-spec-code-converge-check`
Date: 2026-07-06
Verdict: pass (spec compliance: pass · quality: pass)

> Subagent note: implementation workers ran as host subagents (A1/A2 standard tier, B1/B2 light tier); converge judgments came from independent judge subagents per GC9. QA/spec-compliance review concerns were performed inline by the coordinator with direct verification, recorded below unfiltered.

## Scope Reviewed

- `scripts/project_converge.py` (evidence + apply-judgment), `templates/converge-judgment-prompt.md`, `commands/product-converge.md`, `commands/product-review.md` (auto-run step)
- Plan/spec/tasks artifacts; both converge production runs (075 dogfood, 071 self-converge)

## Verification

- Full suite **393 tests OK** (47 converge-focused: 32 evidence + 14 apply + pre-existing). Exit-code, caps, no-op, dedup, regression-re-append paths covered.
- `release_check .` valid (linkage gate green on `codex/071-*` + trailers); `spec_consistency` 0/0/0; artifact validation clean.
- **Self-application ×2**:
  - 075 dogfood: full pipeline (evidence → independent judge → apply) → **caught a real gap** (CV-1: two decision records missing `retrieval_trigger` per 075 GC#8) — fixed same session.
  - 071 self-converge (via the new review auto-run): 4 converged / 5 unverifiable / **1 high unrequested — the judge caught the coordinator's own drift**: `unrequested:<path>` source-refs were implemented beyond plan GC#6's original grammar. Resolved by dated plan amendment legitimizing the third source form (converge itself never edits the plan; the coordinator did, with the amendment note pointing back to the finding).
- CV items on 071 checked off with out-of-bundle evidence: tests run green by coordinator (CV-2/3/5), judge template line "GC violation = automatically high" verified by direct read (CV-4), plan amendment (CV-1). 075's CV-2..4 remain open as honest bundle-cap artifacts.

## Findings

1. (resolved) Doc workers twice invented CLI flags (`--judge`, `--judge-inline`, `--judgment-file`) not present in the implemented surface — corrected by coordinator both times; the pattern (doc workers extrapolating CLI) is worth a line in worker prompts going forward.
2. (resolved) Plan GC#6 grammar gap for unrequested findings — caught by 071's own converge run; plan amended with dated note.
3. (open, follow-up candidate) Bundle file ordering: tight caps truncate implementing code first, inflating `unverifiable` (8/9 on 075's first run). Evidence collection should prioritize scripts/tests over docs when capping. Not blocking; candidate CV/inbox item for a 071 follow-up.
4. (accepted) Judgment variance risk stands as spec'd — run history in converge.md keeps it visible.

## Visual Evidence

- Dashboard: `memory/dashboard.html` (76 issue, 14 memory panels) · Drill-down: `memory/issue-071-spec-code-converge-check.html`
- Converge reports: `specs/075-issue-less-context-capture/converge.md`, `specs/071-spec-code-converge-check/converge.md`

## Next

`product:pr 071-spec-code-converge-check` — Draft PR + human approval.
