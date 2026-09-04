# Status: Reproducible Analysis Runs and Template Pack

Issue: `091-reproducible-analysis-runs-and-template-pack` · Owner: Dongwon Lee
Phase: implementation substantially complete and verified in this worktree on 2026-09-04. Not committed to main, not merged, not published, not installed. Canonical lifecycle state is unchanged and still `backlog`.
Source: [spec](spec.md), [plan](plan.md), [simulation matrix](simulation-matrix.md) · Next: finish the open item below, then owner review.

## Delivered

| Stream | Result |
| --- | --- |
| A1 · A2 | `scripts/project_analysis_run.py`: one parser for `moduflow.analysis-runs.v1`, 32-field validation, the three code checks, four independent states, the six-field amendment boundary, follow-up rules |
| B2 | `resolve_playbook` (project overrides the read-only default, no silent fallback) and `prefill_run` |
| C1 | `read_analysis_runs`: `moduflow.analysis-run-read.v1` envelope, `working`/`shared` views, explicit `total`/`returned`/`omitted`/`truncated` |
| C2 | `resolve_run_sources` through the delivered 090 facades at each pinned commit; `check_playbook_binding` for `PLAYBOOK_MISMATCH` |
| D1 | `analysis-run-append` intent inside the existing 103 transaction owner; no second lock, journal or recovery |
| D2 | `register_run_output` through 090's boundary, before the run is written |
| E1 | `plan_playbook_scaffold` and `plan_playbook_promotion`, both preview-first and refusing to overwrite |
| E2 | Five default analysis playbooks plus README under `templates/analysis-playbooks/` |
| F1 | Analysis runs surfaced in `validate_project_artifacts`, `project_doctor`, `validate_moduflow` and `release_check` |
| Docs | `commands/product-analyze.md` and `skills/data-analysis-bridge/SKILL.md` |

## Acceptance Demonstration — observed 2026-09-04

Run on two synthetic projects in temporary directories. No repository, checkout or worktree outside the fixtures was touched.

| Step | Observed |
| --- | --- |
| Scaffold a default into the project | `playbooks/monthly-trend.md` created; the next resolution reports source `project` with its reason; the read-only default's bytes are unchanged |
| First run, every field supplied | Applied |
| Second run | Applied, linked to the first by `supersedes` with a change reason; claim class, measure unit, caveats and the check skeleton came from the playbook |
| Off-cycle policy-impact run | Applied with claim class `causal`, `maturity=immature`, `decision_state=waiting_on_maturity`, `follow_up.scheduled=false` |
| Read at a date past the follow-up | `FOLLOW_UP_DUE` and `FOLLOW_UP_INTENT_ONLY` diagnostics only; all four states of all three runs unchanged; nothing executed |
| Second project | Holds its own differing playbook; none of project A's three runs appear in project B's envelope |

## What the Demonstration Corrected

The spec's own language, and this session's summaries, said a second run "needs only the time window". The demonstration shows that is an overstatement. What the playbook supplies is the claim class, the measure unit, the required-check skeleton, the caveats, the structure reference and the pinned playbook version. Population definition, numerator and denominator, method steps, title and conclusion remain the author's to write.

The measured saving is real but smaller than claimed: the standard and the checks stop being restated, not the whole run.

## Closed Gap

`R7` promised that selecting a playbook fills `measure.unit` while the implementation did not. Closed on 2026-09-04: each default playbook now states `기본 측정 단위` beside its claim class, `prefill_run` reads it the same way it reads the claim class, and a promoted playbook carries the finished run's unit forward so the next run inherits it. Spec and implementation now agree.

## Not Done

- Not merged, released or installed. The installed package remains 0.3.57; this work is source at 0.3.61 on `codex/115-playbook-process-and-checklist-extension`.
- Canonical lifecycle state for both Issues 091 and 115 is still `backlog`; transitions belong to an explicit transaction, not a hand edit.
- `F2` offline simulation scenarios S01–S12 are being written separately and are not yet recorded here.
- No company project has adopted any of this; every observation above is synthetic.
