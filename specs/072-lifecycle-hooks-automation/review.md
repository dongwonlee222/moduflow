# Review: 072-lifecycle-hooks-automation

Issue: `072-lifecycle-hooks-automation`
Date: 2026-07-06
Verdict: pass (spec compliance: pass · quality: pass)

> Workers: A1/A2 standard tier, B1 light tier, V1 via claude-code-guide (official docs cited); converge judged by an independent subagent. QA/spec-compliance concerns performed inline by the coordinator, recorded unfiltered.

## Scope Reviewed

- `hooks/hooks.json`, `hooks/session_start.py`, `hooks/on_stop.py`
- `scripts/project_doctor.py` (hook-log surfacing), `scripts/linkage_check.py` (hooks/ prefix)
- `hook-schema-notes.md` (V1), doc updates (product-doctor/product-status), `.gitignore`

## Verification

- Full suite **439 tests OK** (44 new: session_start 7, on_stop 20, doctor 17) + linkage hooks-prefix test. `release_check` valid; artifacts validation clean.
- **Schema-first discipline held**: no hook code was written before V1's doc-verified contract; the two forbidden blocking channels (Stop exit 2, `decision:"block"`) are absent from the code (grepped) and tested.
- **Self-application ×2 live**: this branch — on_stop silent, sync fired, marker written, exit 0; temp fixture — unlinked `scripts/rogue.py` warned exactly once, deduped on rerun, exit 0. session_start produced the correct 5-line banner against live repo state in 0.32s.
- **Converge auto-run (first as a mandatory review step)**: 5 converged / 1 partial / 2 unverifiable / 0 violations — best convergence yet (larger evidence caps). Both CVs were bundle-truncation artifacts on test files; coordinator ran those exact test files directly (44 green) and checked them off with that evidence.

## Findings

1. (resolved) Coordination incident: uncommitted B2 edits (hooks/ prefix + test) were reverted mid-wave by an unidentified parallel actor; re-applied and verified post-wave. **Lesson adopted**: commit inline edits before dispatching parallel workers.
2. (accepted) A2 judgment calls all sound: `-uall` porcelain (untracked dirs), declaration-file presence check only (content validation stays with the release gate), fingerprint retained on git errors (fail-open without forgetting).
3. (noted) Unrequested items from converge are all documented deltas (resume matcher, gitignore, declaration suppression) — traceable to hook-schema-notes/judgment calls, no action.
4. (carried) Codex-host parity and richer doctor hook-health remain follow-ups per spec Non-Goals.

## Visual Evidence

- Dashboard: `memory/dashboard.html` · Drill-down: `memory/issue-072-lifecycle-hooks-automation.html`
- Converge report: `specs/072-lifecycle-hooks-automation/converge.md`

## Next

`product:pr 072` — **blocked on main push**: local main carries unpushed `f56999d` (028 fix, parallel session); opening the PR before the user pushes main would mix 22 unrelated files into the diff. PR-ready state recorded locally; Draft PR opens after `git push origin main`.
