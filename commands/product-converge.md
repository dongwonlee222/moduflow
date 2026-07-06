---
description: Post-implementation spec↔code audit; re-runnable anytime.
argument-hint: "<issue-id>"
---

# /product:converge

Run a deterministic spec-code convergence check on a completed issue. Unlike `product:review`, which gates *before* merge, converge audits *after* merge — and stays runnable indefinitely, even on released issues, to catch spec drift.

## What Converge Is

Converge is a **non-blocking recheck**: it compares the current code against the issue's spec and plan, grades each acceptance criterion (AC) and global constraint (GC), and reports gaps. It is:

- **Post-implementation** — run after `product:execute` commits, typically as the final evidence step of `product:review`
- **Re-runnable anytime** — include in CI, run manually on a released issue, audit after maintenance changes
- **Non-gate** — findings auto-append to `tasks.md` for visibility and future planning, but do not block the issue's closure or release
- **Semantic audit** — a deterministic script collects evidence (commits, files, parsed AC/GC list), and an independent subagent judges each AC against that fixed bundle

## The 3-Step Flow

### Step 1: Collect Evidence

```bash
python3 scripts/project_converge.py <project-path> --issue-id <id> --evidence --json
```

Outputs `specs/<id>/converge-evidence.json` with:
- Commits linked to the issue (via `Issue: <id>` trailers and `codex/<id>-*` branch merges)
- Files touched by those commits, with their **current** content
- Parsed acceptance criteria from `spec.md`
- Global constraints from `plan.md`
- Explicit `truncated` flag if the bundle hit size caps (30 files / 200KB total)
- `no_evidence` flag if no commits resolved (work not yet committed or linkage missing) — report only, do not judge

**Exit codes**: non-zero on git failure or bundle error (never exits 0 with silent failures).

### Step 2: Dispatch Judge Subagent (or Inline Fallback)

This step is performed by the **host agent**, not by a script flag: dispatch ONE judge subagent whose prompt is `templates/converge-judgment-prompt.md` with the contents of `specs/<id>/converge-evidence.json` attached. Save the subagent's output as `specs/<id>/converge-judgment.json`. The judge must not be the agent that implemented the issue.

The subagent:
- Receives **only the evidence JSON** (no repo access)
- Outputs one verdict per AC: `converged | missing | partial | contradicting | unverifiable`
- Prefers `unverifiable` over guessing
- Also lists `unrequested` behaviors (code not asked for by AC/GC) and `bundle_gaps` (what could not be verified and why)
- Issues with `"parseable": false` in the AC list MUST be emitted as `unverifiable` (never dropped)

**Inline fallback** (when subagent dispatch is unavailable, e.g., session limits): the coordinating agent (you) judges the bundle directly using the same template, writes `converge-judgment.json` yourself, and records the limitation as a note inside the judgment's `bundle_gaps` so it lands in `converge.md`:

```
**Note (2026-07-06)**: Subagent dispatch unavailable; judgment performed inline by coordinating agent. Judge independence rule recorded for review.
```

This mirrors `product:review`'s inline fallback rule — the limitation is visible, not hidden.

**Output**: `specs/<id>/converge-judgment.json` with verdicts, severity, evidence quotes, and any unrequested/gaps findings.

### Step 3: Apply Judgment & Report

```bash
python3 scripts/project_converge.py <project-path> --issue-id <id> --apply-judgment \
  --judgment-file specs/<id>/converge-judgment.json
```

Appends to:

- **`specs/<id>/converge.md`** (append-only): dated run section with verdict table, unrequested list, bundle-gaps report, and references to the evidence bundle
- **`specs/<id>/tasks.md`** (high/medium only): new task lines under `## Converge Findings (auto)` with the format:
  ```
  - [ ] CV-<n> [<severity>] <finding> — <source-ref>, from converge <date>
  ```
  where `source-ref` is `AC#<k>` or `GC#<k>` (the plan's Global Constraint it relates to)

Low-severity findings appear only in `converge.md`, not in tasks.

**Byte-for-byte no-op**: if the run finds no high/medium issues and all lower-severity findings already exist in tasks.md as unchecked items, `tasks.md` remains **byte-identical** and no empty `## Converge Findings` header is emitted.

**Dedup rule**: on re-runs, the script does not re-append a CV item whose finding text matches an existing unchecked CV line with the same source-ref. If the CV line is checked off, a recurring finding re-appends (it regressed).

## Special Cases

### No Evidence (`no_evidence: true`)

If the issue has no linked commits (work not yet committed, or branch name doesn't match `codex/<id>-*` pattern, or trailer missing):

```bash
python3 scripts/project_converge.py <project-path> --issue-id <id> --evidence --json
```

Returns `no_evidence: true` in the bundle. Do not run step 2 (judgment). Report in `converge.md` only:

```
No linked commits found for this issue. Converge cannot audit code. Possible causes:
- Work committed but without `Issue: <id>` trailer or merge-commit mentioning `codex/<id>-*`
- Issue opened but work not yet committed
- Branch deleted post-merge and trailers not present in merge commit

Re-run converge after committing with proper linking.
```

### Bundle Truncation

The evidence script enforces a bundle size cap (default: 30 files, 200KB total content). If exceeded:

- The evidence JSON includes `"truncated": true`
- The report surfaces this loudly:
  ```
  **Bundle truncated**: evidence contains only the first 30 files (200KB) of the issue's changes.
  The following files and their content are not included: [list]
  Converge verdict is incomplete; re-run on a smaller issue or request a manual audit.
  ```

Silent caps are forbidden (Global Constraint 5).

## Convergence Verdict Grammar

The CV task line format is strict (Global Constraint 6):

```
- [ ] CV-<n> [<severity>] <finding> — <source-ref>, from converge <date>
```

Example:
```
- [ ] CV-1 [high] AC#3 unimplemented: POST /users endpoint missing error handling for invalid email — AC#3, from converge 2026-07-06
- [ ] CV-2 [medium] AC#5 partial: cache TTL hardcoded to 60s; spec allows configurable TTL — AC#5, from converge 2026-07-06
```

**Source-ref** is the AC or GC from the plan/spec, formatted as `AC#<k>` or `GC#<k>`.

**Dedup key**: normalized finding text + source-ref. Re-runs never re-append the same finding to the same AC unless the existing CV task is checked off (indicating it was addressed or dismissed).

## Write-Surface Guardrails

The converge pass writes **only**:

1. `specs/<id>/converge.md` (append-only dated sections; never overwrites prior runs)
2. `specs/<id>/tasks.md` (only the `## Converge Findings (auto)` section; never modifies existing task lines, never edits spec.md or plan.md)

Violations:
- ❌ Rewriting spec.md acceptance criteria
- ❌ Renumbering, reordering, or deleting existing task lines
- ❌ Editing plan.md Global Constraints
- ❌ Merging findings into task lines not under the auto section

These constraints enforce the append-only principle: converge reports findings but never rewrites history.

## Auto-Run During Review

`product:review` automatically runs converge as its final evidence step:

```bash
python3 scripts/project_converge.py <project-path> --issue-id <id> --evidence --json
# (host agent dispatches the judge subagent with templates/converge-judgment-prompt.md
#  + the evidence JSON, saving specs/<id>/converge-judgment.json)
python3 scripts/project_converge.py <project-path> --issue-id <id> --apply-judgment specs/<id>/converge-judgment.json
```

If evidence collection fails or returns `no_evidence: true`:
- The report is logged in `converge.md`
- Review proceeds (converge is non-blocking)
- The limitation is visible in the review's final report

If judgment dispatch fails:
- The inline fallback is used
- The limitation is recorded in converge.md for future review

## Standalone Usage

Run converge on an issue anytime:

```bash
product:converge 075
```

This works on:
- Merged issues (already done)
- Released features (re-audit after maintenance)
- In CI pipelines (detect spec drift)
- Manually, after a suspicion ("I think we changed this behavior")

Output is always appended to converge.md with a dated section, so a long-lived issue accumulates an audit history.

## Next Steps

- **If converge finds high/medium issues**: examine the CV lines in `specs/<id>/tasks.md`, plan promotions to new issues with `/product:plan`, or update the spec if the implementation was correct and the spec was wrong.
- **If converge says `unverifiable`**: the bundle may be truncated, the AC may be untestable from code alone, or the evidence may be incomplete. Review the `bundle_gaps` section and decide whether to re-run with a focused scope or request a manual audit.
- **`product:review`**: review the converge findings as part of the final evidence handoff; converge does not override review's verdict but surfaces gaps.

## References

- Plan: `specs/071-spec-code-converge-check/plan.md` (Global Constraints, interfaces, test gates)
- Spec: `specs/071-spec-code-converge-check/spec.md` (detailed problem, solution, scenarios, AC definitions)
- Template: `templates/converge-judgment-prompt.md` (judge instruction, verdict vocabulary, output schema)
