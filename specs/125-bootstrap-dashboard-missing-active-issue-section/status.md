# Status: Issue 125 — Bootstrap Dashboard Missing Active Issue Section

**Verdict:** pass, with three recorded limitations and one new defect found during review.
**Reviewed:** 2026-09-05, inline (no subagent backend available in this session).
**Commit under review:** `83f95c5`

## Spec compliance

There is no `spec.md` — the issue records the S-grade bugfix exception. Compliance
is therefore judged against the issue's own Scope and Acceptance Criteria.

| Criterion | Verdict | Evidence |
| --- | --- | --- |
| `templates/workspace/dashboard.md` survives the projection | pass | `test_product_start_template_survives_the_projection` |
| `project_migrate.WORKSPACE_FILES["dashboard.md"]` survives it | pass | `test_product_migrate_template_survives_the_projection` |
| Any `dashboard.md` under `templates/` survives it | pass | `test_every_workspace_template_named_dashboard_survives` |
| Projection still rejects a section-less dashboard | pass | `test_projection_still_rejects_a_dashboard_with_no_section` |
| Output stable on a second pass | pass | `test_projected_bootstrap_dashboard_is_stable_on_a_second_pass` |

Scope was respected. `render_dashboard_projection` was not made lenient, which
Scope Out named as the tempting wrong fix — the guard test asserts the rejection
still happens, so a future author cannot satisfy the suite by weakening it.

Scope was also correctly *widened* against the report: the inbox named
`product:migrate`, and `product:start`'s canonical template had the same defect.
Fixing only what was reported would have left the more common path broken.

## Quality

- The `project_migrate.py` change carries a comment saying *why* the section is
  required and pointing at the test. The next person to trim that template will
  see the reason.
- The third test globs `templates/**/dashboard.md` rather than naming the two
  known files, so a bootstrap path added later is covered without anyone
  remembering to extend the test. That is the difference between fixing this bug
  and preventing its class.
- Both templates use the exact string the projection itself emits for the
  no-active-issue case, so the first projection is a no-op rather than a rewrite.

No quality findings to report.

## Verification

| Check | Result |
| --- | --- |
| `tests/test_bootstrap_dashboard_projection.py` | 5 tests — RED 4 before the fix, GREEN 5 after |
| `tests/test_hooks_on_stop.py` | 20 tests, pass |
| `tests/test_project_migration.py` | 9 tests, pass |
| Full suite at review time | 1858 tests, **3 failures** — see below |
| `release_check` at review time | `valid: false` — see below |

### The three failures were real, and mine

All three were in `tests/test_validation_distribution` and none were caused by
the 125 fix itself. They were caused by other edits made in the same session:

1. **`lifecycle drift: multiple active issues`** — issues 120 and 125 were both
   set to `**Status: active**`. Only one issue may be active. 120 was returned to
   `backlog`, which is honest: its spec and plan are written but execute is
   gated on a pending decision.
2. **Version bump gate** — `83f95c5` classifies as a `patch` bump and
   `.claude-plugin/plugin.json` was left at 0.3.64. Bumped to 0.3.65 with
   `scripts/version_bump.py`, and `.codex-plugin/plugin.json` bumped to match
   after the gate flagged the manifests disagreeing.
3. **`project_doctor failed`** — a consequence of (1).

**How this was missed:** the fix was committed after running only a 25-test
subset plus a `release_check` from *before* the code change, and the earlier
report of "release_check 14 checks all pass" read the `checks` sub-dictionary
while `valid` at the top level was already false. Checking `checks` without
checking `valid` is not a verification.

## Limitations

1. **`review-handoff.md` could not be generated.**
   `project_execution.py --review-handoff --write` returns `allowed: false`;
   this repository's identity is `unverifiable` because its remote is the SSH
   alias `github-evmodu`. `project_pr.py --write` has no such gate and wrote
   `pr.md` and `human-review.ko.md` in the same run. Recorded on Issue 122,
   which was widened from two write paths to three as a result.
2. **Converge could not run.** `project_converge.py --evidence` returned
   `spec file missing: specs/125-…/spec.md`. The absence is deliberate — the
   S-grade bugfix exception — so converge cannot audit an issue that correctly
   has no spec. `examined_count` and `unmatched_count` are therefore unavailable
   for this review, and the review command's instruction to report them cannot
   be satisfied. Worth its own issue; not filed here to avoid widening a closed
   bug.
3. **No subagent dispatch.** Reviewed inline, as the command permits when no
   subagent backend is available.

## New defect found during review

`python3 scripts/project_lifecycle.py . --sync` is the remedy that
`validate_project_artifacts`, `project_doctor` and the error text all recommend
for lifecycle drift. With issue 125 active it refused:

```
transaction.failed_stage      = projected-validation
transaction.status            = conflict
projected_validation.valid    = False
projected_validation.error_codes = ['PROJECTED_PROJECT_INVALID']
```

Recovery diagnostics reported `healthy` with no stuck transactions, so the
refusal is not a recovery state — the projected state itself fails validation,
which means the documented fix for drift cannot clear that drift. The drift was
resolved instead by taking 125 to `done`, so the blocker is currently invisible.
It should be reproduced and filed before someone hits it with no such option.

## Constitution

Constitution: v1.0 checked — no violations.

## Reference improvements

Reference improvements: none found.

## Evidence

- Dashboard: `memory/dashboard.html` (126 issue panels, 15 memory panels)
- Issue drill-down: `memory/issue-125-bootstrap-dashboard-missing-active-issue-section.html`
- PR handoff: `specs/125-…/pr.md`
- Korean packet: `specs/125-…/human-review.ko.md`
- Converge: unavailable, see Limitations 2
