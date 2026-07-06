# Converge: 071-spec-code-converge-check

## Converge Run 2026-07-06

| AC | Verdict | Severity | Note |
| --- | --- | --- | --- |
| AC#1 | unverifiable | medium | The missing/unrequested fixtures are asserted to live in the test file, but its content is truncated out of the bundle; a doc claim in status.md is not code evidence. |
| AC#3 | unverifiable | medium | Evidence-only input and the unverifiable verdict in the vocabulary are verified in command doc and script, but the judge template content and the fixture that exercises unverifiable are truncated — the 'exercised in at least one fixture' clause cannot be judged. |
| AC#5 | unverifiable | medium | Non-zero exit on git/bundle failure in both output modes is clearly converged in code, but 'Global-Constraint violations grade high automatically' is enforced by the judge prompt template, whose content is truncated out of the bundle. |
| AC#9 | unverifiable | medium | The required focused tests cannot be verified: the test file content is truncated; test counts exist only as status.md prose. |
| AC#2 | converged | low | Both linkage sources, loud caps, and loud git-failure paths are all present in the shipped script; the bundle under judgment is a live demonstration. |
| AC#4 | converged | low | High/medium-only append, fixed CV grammar, no-write no-op path, and insertion that leaves existing lines untouched are all visible in code. |
| AC#6 | converged | low | Repeat runs strictly append; same-date collisions get distinct run-numbered headings instead of overwriting. |
| AC#7 | converged | low | Review auto-run step is present in the review doc; the converge command doc frames standalone re-runs on released issues, and the full-git-log trailer scan mechanically supports it. |
| AC#8 | unverifiable | low | A command-execution result is inherently untestable from a static evidence bundle; no run log is included. |

Unrequested:
- [high] build_findings emits source_ref "unrequested:<file>" for high/medium unrequested items, producing CV lines whose source-ref is neither AC#<k> nor GC#<k>. GC#6 fixes the grammar to "source-ref is `AC#<k>` or `GC#<k>`" and commands/product-converge.md repeats that restriction, so any high/medium unrequested finding will write a tasks.md line outside the fixed grammar. — scripts/project_converge.py
- [low] _run_heading appends a "(run N)" suffix to same-date converge.md headings; no AC or GC asked for same-date run disambiguation. Defensive and consistent with the never-overwrite rule. — scripts/project_converge.py

Bundle gaps:
- Bundle top-level "truncated": true; 11 of 22 files have content: null (spec.md, spec.ko.md, templates/converge-judgment-prompt.md, tests/test_project_converge.py, worker-plan.json, workspace/dashboard.md, workspace/loop-state.json, and all four 075 dogfood artifacts) — truncated files prove nothing.
- tests/test_project_converge.py truncated — AC#1 fixtures, AC#3 fixture exercise, and AC#9 focused tests are judged only through status.md prose, hence unverifiable.
- templates/converge-judgment-prompt.md truncated — the auto-high rule for Global-Constraint violations (AC#5 second clause) and the judge's evidence-only/prefer-unverifiable instructions cannot be verified from the bundle.
- specs/075-issue-less-context-capture/converge-evidence.json, converge-judgment.json, converge.md, and tasks.md all truncated — the D1 dogfood end-to-end claim (AC#2's '075 itself is the dogfood fixture', AC#3 exercise) rests on status.md narrative only.
- AC#8 (release_check.py passes) depends on executing a command; no run output is captured in the bundle.

Summary: 9 AC: 4 converged, 5 unverifiable; 2 unrequested
