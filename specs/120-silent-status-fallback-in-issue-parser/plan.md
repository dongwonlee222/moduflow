# Plan: Silent Status Fallback in the Issue Parser

Issue: `120-silent-status-fallback-in-issue-parser`
Spec: `specs/120-silent-status-fallback-in-issue-parser/spec.md`
Prev: `product:spec` · Next: `product:workers 120-silent-status-fallback-in-issue-parser`

## Global Constraints

Constitution v1.0 applies (`workspace/constitution.md`). Plan-specific additions:

- **GC1 — `markdown_status` is frozen at the boundary.** Its signature and its
  return value for every input stay exactly as they are today. Any diff that
  changes what an existing caller receives is out of bounds, whatever the tests
  say.
- **GC2 — One implementation.** `markdown_status` becomes a wrapper over
  `markdown_status_result`. Two functions that each parse are a C8 violation,
  and this issue exists because the single parser was worth keeping.
- **GC3 — The parser stays pure.** No logging, no printing, no file access
  inside it. It runs in a loop over every issue.
- **GC4 — Nothing raises.** Every input, including empty text and a status line
  with no value, returns a result. Alternative 1 in the spec was rejected for a
  reason.
- **GC5 — Do not enlarge the vocabulary.** No state is added, renamed or
  translated. If a fixture is easier to write by adding `review`, the fixture is
  wrong.

## Recommended Discipline

| Stream | Discipline / Adapter | Reason |
| --- | --- | --- |
| A — parser result | Superpowers TDD | Four reasons and two edges; each needs RED before GREEN. |
| B — validator surfacing | verification-before-completion | The risk here is a diagnostic nobody reads; it has to be proven visible, not assumed. |
| C — documentation | product-review | The vocabulary rule is a human contract, so it gets read by a person. |

## File Structure

### Modify

| Path | Change |
| --- | --- |
| `scripts/project_issue_schema.py` | Add `markdown_status_result`; rewrite `markdown_status` as a wrapper over it. Distinguish `missing` from `unreadable` at the token step. |
| `scripts/validate_project_artifacts.py` or the schema validator entry that reports issue diagnostics | Consume the richer result and emit one diagnostic per non-`ok` issue. Which module owns this is confirmed in A1 before B1 starts. |
| `commands/product-issue.md` | Document the supported vocabulary and the treatment of an unsupported token. |
| `tests/test_project_issue_schema.py` | Reason coverage and the two edges. |

### Create

| Path | Purpose |
| --- | --- |
| `tests/fixtures/issue-status/` | One issue file per reason, including the real `**Status: review**` regression case. |

No new script. This issue adds a function and a diagnostic, not a module.

## Stable Interfaces

```
markdown_status_result(text) -> {
    "state":  "active" | "backlog" | "done" | "superseded",
    "reason": "ok" | "missing" | "unreadable" | "unrecognised",
    "token":  raw token as written, or None when no status line was present,
}

markdown_status(text) -> str        # unchanged; returns result["state"]
```

- **A produces, B consumes.** The validator reads `reason` and `token` only. It
  does not re-parse and does not infer a reason from `state`.
- **`token` is the raw text**, not lowercased and not normalised — a diagnostic
  that prints `review` when the author wrote `Review` sends them looking for the
  wrong string.
- `state` for every non-`ok` reason is `backlog`, unchanged from today. The spec
  is explicit that the default value is not what is being fixed.

## Implementation Readiness Contracts

- **API contract mapping**: not applicable. No HTTP surface; the contract is the
  two function signatures above.
- **Test strategy**: one test per reason plus empty text and empty value; a
  parity test asserting `markdown_status` output is identical before and after
  across every file in `issues/`; a validator test that a valid corpus adds no
  diagnostics.
- **Storybook / MSW / Playwright**: not applicable, no UI.
- **Permission/role model**: not applicable.
- **Release/rollback**: `release_check` 14/14 and unchanged lifecycle drift.
  Rollback is reverting the commit; no data or file format changes.

## Streams

### Stream A — Parser result

Add `markdown_status_result`, move the existing logic into it, and reduce
`markdown_status` to a wrapper. The one behavioural subtlety: today a non-ASCII
token and a missing line are the same code path because the regex simply fails
to match. Separating them means detecting that a `**Status:`-shaped line exists
before deciding the token is absent.

The parity test is the real gate on this stream. Run both implementations over
all 125 issue files and assert identical output; GC1 is not satisfied by unit
tests alone.

### Stream B — Validator surfacing

Emit one diagnostic per non-`ok` issue naming the id and the raw token.

**Confirm which surface a person actually reads before writing this.** The spec
names this as the main risk: a diagnostic that lands only inside a JSON blob
moves the silence rather than removing it. `product:doctor` is the candidate
surface. If it turns out the validator's output does not reach doctor, say so
and stop — do not add a second reporting path to work around it.

### Stream C — Documentation and scan

Document the vocabulary rule in `commands/product-issue.md`, and run the corpus
scan that acceptance criterion 10 requires. The scan is verification output, not
a repair pass: if it finds a file relying on the fallback, report it rather than
editing it.

## Gates

| Gate | Condition |
| --- | --- |
| Parity | `markdown_status` output identical across all 125 issue files, before and after |
| Test | `python3 -m unittest tests.test_project_issue_schema` and the full suite green |
| Drift | `python3 scripts/project_lifecycle.py . --drift` unchanged before and after |
| Visibility | The diagnostic is shown to appear on a surface a person reads, not only in returned JSON |
| Release | `python3 scripts/release_check.py .` 14 of 14 |

## Next

- `python3 scripts/spec_consistency.py . --issue-id 120-silent-status-fallback-in-issue-parser`
- `product:workers 120-silent-status-fallback-in-issue-parser`
- `product:execute` after the section 6 decision is approved
