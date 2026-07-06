# Converge: 072-lifecycle-hooks-automation

## Converge Run 2026-07-06

| AC | Verdict | Severity | Note |
| --- | --- | --- | --- |
| AC#2 | partial | medium | The sync-trigger mechanism is clearly implemented, but the fixture-based verification demanded by the AC cannot be confirmed — the test file content is absent from the bundle. |
| AC#8 | unverifiable | medium | Test files exist in the commit file list, which suggests tests were written, but null-content entries prove nothing about banner-content, marker, dedup-fingerprint, fail-open, or doctor-surfacing coverage. |
| AC#7 | unverifiable | low | A command-execution AC cannot be judged from static file contents alone; no run evidence is present in the bundle. |
| AC#1 | converged | low | Goal, active issue, and next command are injected at session start without any manual product:status call; commands/product-status.md documents the banner. |
| AC#3 | converged | low | Single warning line, fingerprint dedupe across turns, silence for linked (issue-branch) changes, and re-warn after resolution are all implemented. |
| AC#4 | converged | low | Every failure path exits 0 and appends to hooks.log; stdout is reserved for the JSON contract, so the session is unaffected. |
| AC#5 | converged | low | Absent/empty log yields silence; recent entries surface as warnings, matching the AC. |
| AC#6 | converged | low | Exit-0 discipline, 5s self-budget, and reuse of existing sync/linkage/retention scripts are all visible in code; GC#1/GC#2 satisfied. |

Unrequested:
- [low] Stop-hook linkage warning is suppressed entirely when releases/no-issue-declarations.md exists (reason "no-issue-declaration"), a condition not mentioned in AC#3 or the global constraints (it defers to the issue-075 release gate). — hooks/on_stop.py
- [low] SessionStart matcher includes "resume" in addition to the startup|clear|compact set; documented in hook-schema-notes.md as implementation delta 1 ('spec said three; resume added') but not in the parsed AC/GC list. — hooks/hooks.json
- [low] .gitignore extended to exclude .moduflow/state/ and .moduflow/logs/ ('machine-local hook state (issue 072) — never commit') — consistent with GC#7's machine-local write surface but not itself requested by any AC/GC. — .gitignore

Bundle gaps:
- All four test files (tests/test_hooks_on_stop.py, tests/test_hooks_session_start.py, tests/test_linkage_check.py, tests/test_project_doctor.py) have content:null/truncated:true — AC#8 and the fixture-verification clause of AC#2 cannot be judged, and the '+ test' requirement of GC#8 (hooks/ prefix coverage in linkage_check tests) cannot be confirmed (the prefix itself IS present in scripts/linkage_check.py BEHAVIOR_PREFIXES).
- specs/072-lifecycle-hooks-automation/spec.md, plan.md, tasks.md, status.md, spec.ko.md, worker-plan.json, worker-plan.md are all null/truncated — judgments rely solely on the parsed AC/GC extracts in the bundle.
- AC#7 requires running `python3 scripts/release_check.py .`; the bundle contains no execution output and release_check.py is not among the bundled files.
- workspace/loop-state.json and workspace/dashboard.md are null/truncated — the dashboard-propagation half of AC#2 ('propagates state.json/dashboard') can only be inferred from the sync-invocation code, not observed.
- GC#9 (parallel-session hygiene: never touch scripts/validate_project_artifacts.py, targeted `git add`) is not checkable — the bundle has commit subjects only, no per-commit diffs or staging information; validate_project_artifacts.py is at least absent from the touched-files list.
- Bundle top-level "truncated": true — the evidence set itself is declared incomplete.

Summary: 8 AC: 5 converged, 1 partial, 2 unverifiable; 3 unrequested
