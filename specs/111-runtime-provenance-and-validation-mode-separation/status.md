# Status: Issue 111

Issue: `111-runtime-provenance-and-validation-mode-separation`
Owner: Dongwon Lee
Source: approved `plan.md`; user approval on 2026-09-02.
Phase: implementation; Streams A/B/C complete, D pending.
Next command: `product:execute 111-runtime-provenance-and-validation-mode-separation`.

## Evidence — 2026-09-02

- Baseline: 137 tests passed in 73.664s. Distribution tests invoke the large source release suite twice; subsequent focused checks exclude these two recursive integration wrappers until final verification.
- RED: new runtime suite failed with 11 failures and 2 errors: missing reader, missing explicit mode keyword and source subprocess reached for a cache target.
- GREEN: 13 new runtime/mode tests passed; runtime + release unit tests 34 passed, validator-focused 9 passed, existing cache distribution 3 passed.
- The canonical start transaction applied as `txn-7e5518bb96b35e50d79840c7496209d2`; projected and post-apply validation passed. Preceding rejected attempts and preparation corrections are described in `review.md`.
- Workspace remains the existing linked worktree. Issue-specific branch: `codex/111-runtime-provenance-and-validation-mode-separation`.

## Remaining

Offline scenarios and full release verification (D). No real cache installation, publication, remote push or actual-host observation has occurred.

## Stream B Evidence

- RED: five installer tests failed for missing receipts, conflicting-version overwrite, invalid-payload exposure and missing atomic/Git-evidence helpers.
- GREEN: installer/runtime/operation-audit suite passed 59 tests. A further symlink test then reproduced an external-manifest write before payload rejection; moving link validation before staged manifest writes fixed it. The expanded suite passed 60 tests.
- Cache tests use temporary homes only. Repeated identical packages retain receipt bytes; conflicting versions and invalid payloads never replace/activate the prior cache. New receipt writes are classified as package-maintenance.

## Stream C Evidence

- RED: new consumer/inventory checks failed with 5 failures and 2 errors (9 existing inventory tests remained green).
- GREEN: full MCP, Doctor, installed-staleness and runtime suites passed 82 tests in 1.439s.
- Source/package identity no longer comes from a selected project or newest cache. MCP initialization and subsequent status/Doctor calls share injected startup evidence. Wrong-target checks run before parent Git/project discovery; valid unrelated-plugin projects remain project targets.
