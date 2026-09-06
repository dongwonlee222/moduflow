# Issue 146: The Validator Throws Away Severity At The Last Step

**Status: backlog** — created 2026-09-06.
**Priority: p1**

## 요약

검사기 안에서는 발견 하나하나가 **등급(`severity`)과 코드(`code`)를 달고** 다닙니다.
그런데 **마지막 줄에서 그걸 다 버리고 문자열 두 뭉치로** 내보냅니다. 그래서 순위도
못 매기고, 묶지도 못하고, 접지도 못합니다. 그리고 **몇 개를 검사했는지 아무도
말하지 않습니다** — 조용한 게 "깨끗하다"인지 "안 봤다"인지 구분이 안 됩니다.

## Summary

`validate_project_artifacts.validate_project` builds structured findings and
flattens them into two string arrays at the return. Every downstream renderer
therefore has strings and nothing to rank, group, or collapse by.

## Source

- Type: bug — found while answering the owner's question on 2026-09-06: "120이
  doctor 출력 관련해서 다른 사람들은 어떻게 하고 있어?"
- Owner / decision maker: Dongwon Lee
- Evidence: a survey of ESLint, ruff, flake8, mypy, rustc, clippy, go vet,
  shellcheck, npm audit, brew doctor, npm doctor, flutter doctor and expo-doctor,
  2026-09-06

## 원인

```
$ grep -n 'severity"\] == "error"' scripts/validate_project_artifacts.py
919:        if finding["severity"] == "error":
929:        if finding["severity"] == "error":

$ sed -n '939p' scripts/validate_project_artifacts.py
        "valid": not errors,

$ python3 scripts/project_doctor.py . 2>&1 | python3 -c "import json,sys;print(len(json.load(sys.stdin)))"
31
```

Findings carry `severity` and `code` at `:804`, `:919` and `:929`. The return at
`:933-941` keeps `{"valid", "errors", "warnings"}` — two arrays of rendered
strings. The structure exists and is destroyed one line before it leaves.

This is not "there is no rendering layer". It is that **the rendering layer is
the only layer**, so nothing survives for a second one.

`product:doctor` then emits 31 top-level keys and no summary. Nothing says how
many issues or specs were checked.

**Correction to a claim made during this investigation:** `project_doctor.py`
was reported as always exiting 0. It does not. `:890-904` returns 0 only when
the project is initialized, has no missing artifacts, passes schema gates and
has healthy recovery — a real gate, with a comment saying it was made one
deliberately. That half needs no fixing.

## Opportunity

What the survey found, and what each finding implies here:

**Nobody ranks.** Not one of the thirteen tools sorts findings globally and says
"fix this first". The universal substitute is a per-finding remedy — flutter's
`To resolve this, run: flutter doctor --android-licenses`, expo's `Advice:`,
npm doctor's `Use npm v12.0.2`. **If every finding is actionable, ranking stops
mattering.**

**expo-doctor is the best output seen.** Captured from a real build log:

```
Running 17 checks on your project...
16/17 checks passed. 1 checks failed. Possible issues detected:
Use the --verbose flag to see more details about passed checks.

✖ Check for common project setup issues
The .expo directory is not ignored by Git. …
Advice:
Add ".expo/" to your .gitignore to avoid committing local Expo state.
```

Four things ModuFlow has none of: the denominator first, a pass ratio, passing
checks collapsed behind a flag, and a named check with an `Advice:` block.

**`brew doctor` is the anti-pattern**, and it is the one ModuFlow most resembles:
73 checks, a flat `Warning:` list, no denominator, no passing checks — and a
header telling the reader "just ignore this" while exiting 1. **The text and the
exit code say opposite things.**

**SARIF already has the vocabulary.** OASIS SARIF v2.1.0 §3.27.10 defines
`result.level`:

- `note` — "The rule applies to this location, but the problem it describes **is
  not a defect**."
- `warning` — "…a potential defect."
- `error` — "…is a defect."

`note` is exactly "a person should see this and it must not fail the build", and
it does not have to be invented.

**Display and failure must be separate knobs.** `npm audit --audit-level` gates
the exit code and never changes what is printed. `shellcheck -S` gates *display*,
and since display is what sets its exit code, shellcheck has no "shown but not
failing" state at all — to stop a low finding failing you must also erase it from
the screen. Tying the two together kills the diagnostic either way.

**Nobody marks a diagnostic that has never fired.** The closest is rustc's
`expect` lint level, which reports when an expected lint does *not* fire. The
common answer is simpler: **show the denominator.** A finding count of zero is
only meaningful next to "12 checks run".

## Scope

### In

- Three levels, using SARIF's names and definitions: `error`, `warning`, `note`.
- `validate_project` returns a `findings` array carrying `level`, `code`,
  `path` and `advice`. `errors` and `warnings` stay as derived views so nothing
  breaks.
- A terminal renderer that is a pure function of that array. It leads with the
  denominator, shows a pass ratio, collapses passing checks behind `--verbose`,
  and gives every finding a code and an `Advice:` line.
- One failure knob, `--fail-level` (default `error`), which never changes what is
  displayed. A display filter, if ever needed, is a separate flag.

### Out

- Grouping by subsystem. At roughly a dozen checks it is noise; `brew doctor`
  groups nothing at 73 and is unreadable, but that is an argument about scale,
  not about grouping. Revisit above ~30 checks.
- `project_doctor.py`'s exit code. It already gates correctly at `:890-904`.
- SARIF output itself. The vocabulary is worth copying; the format is not needed
  until something external consumes it.
- Issue 120's parser change. This issue owns where its diagnostic lands, not how
  it is produced.

## Known Limit

A denominator makes silence legible; it does not make the checks correct. "12
checks passed" is worth exactly as much as the twelve checks are, and this issue
does not add or improve one.

## Acceptance Criteria

- `validate_project` returns `findings` with `level` in `{error, warning, note}`,
  plus `code`, `path` and `advice` on every entry.
- `errors` and `warnings` still return what they return today; a test asserts
  the derived views are unchanged.
- The renderer's first line names what was checked and how many.
- Passing checks are hidden without `--verbose` and shown with it.
- `--fail-level` changes the exit code and never the output; a test asserts the
  printed text is byte-identical across two `--fail-level` values.
- Every finding carries an `Advice:` line. A test asserts none is empty.
- `python3 scripts/release_check.py .` passes, `valid` checked at the top level.

## Verification

- Fixture with one `note`, one `warning`, one `error`; assert exit codes at each
  `--fail-level`.
- Fixture with zero findings; assert the denominator still prints.
- Assert output text identical across `--fail-level=error` and `=note`.
- Snapshot the derived `errors`/`warnings` arrays against today's output for the
  live tree.
- `tests/test_validate_project_artifacts.py`, `tests/test_project_doctor.py`.

## Entry Points

- `scripts/validate_project_artifacts.py:804`, `:919`, `:929` — where severity
  exists
- `scripts/validate_project_artifacts.py:933-941` — where it is destroyed
- `scripts/project_doctor.py:889` — the 31-key dump
- `scripts/project_doctor.py:890-904` — the exit gate that already works
- OASIS SARIF v2.1.0 §3.27.10 — the `note` / `warning` / `error` definitions

## Scope Fence

Do not add a display filter in the same change as `--fail-level`. One knob for
what is shown and one for what fails, or shellcheck's outcome follows: the only
way to stop a low finding failing the build becomes erasing it from the screen.

## Workflow Tasks

- [ ] spec → `specs/<issue>/spec.md`
- [ ] plan → `specs/<issue>/plan.md` + `tasks.md`
- [ ] execute → findings array, renderer, --fail-level, advice lines
- [ ] review → `specs/<issue>/review.md`

## Related Issues

- blocks: `120-silent-status-fallback-in-issue-parser` — 120 produces a
  diagnostic and its open question is where it lands. This owns the landing
  place, so 120's answer is "here".
- related: `105-schema-migration-and-doctor-triage` (p0 — owns grouping doctor
  results into blockers versus legacy noise, and `--summary` / `--current`
  views; this owns the finding shape those views would render),
  `138` (unsafe transaction advice drops the error code),
  `129-required-sections-are-named-but-never-checked` (the rule table whose
  findings would flow through this)

## Next Command

`product:spec 146-the-validator-throws-away-severity-at-the-last-step`
