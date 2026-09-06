# Issue 128: Linked Artifact Check Runs For One Issue Only

**Status: backlog** — created 2026-09-06.
**Priority: p2**

## 요약

이슈 파일의 링크가 실제로 존재하는지 검사하는 규칙이 있습니다. 그런데
`.moduflow/state.json`의 **활성 이슈 하나에만** 걸립니다. 활성 이슈가 없으면
아예 한 건도 검사하지 않습니다. 오늘 기준 127개 이슈 파일 중 1개만 봅니다.

게다가 규칙 자체가 세 종류를 구분하지 못합니다 — 아직 안 만든 산출물,
`파일:줄번호` 인용, 진짜 깨진 링크. 지금 없는 링크 87건 중 75건은 정상이고
6건은 오탐입니다. 진짜는 19건입니다.

## Summary

`validate_active_issue_links` verifies that paths written in an issue file
exist. It runs for exactly one issue — the one named in `.moduflow/state.json` —
and for none when that field is empty. The rule also cannot distinguish an
artifact that does not exist *yet* from one that is missing, and reads
`path.md:24` citations as file paths.

## Source

- Type: found while verifying why Issue 123's validation passed clean, 2026-09-06
- Owner / decision maker: Dongwon Lee
- Trigger: advisor review of the Issue 126 diagnosis asked why a known-missing
  link did not fail validation. It did not fail because it was never checked.

## Opportunity

### Fault 1 — scope is one issue

```python
# scripts/validate_project_artifacts.py:352-354
active_issue_id = (state.get("active_issue") or "").strip()
if active_issue_id:
    validate_active_issue_links(
```

The id comes from `.moduflow/state.json`, not from the issue being examined. So:

| State | Issues link-checked |
| --- | --- |
| `active_issue: "112-…"` | 1 of 127 |
| `active_issue: ""` | 0 of 127 |

Issue 123 was written with a link to `specs/123-…/review.md`, which does not
exist. It validated clean. Not because the rule tolerated it — because the rule
never looked.

### Fault 2 — the rule cannot tell three cases apart

Measured across all 127 issue files on 2026-09-06 — 87 links resolve to nothing:

| Kind | Count | Correct verdict |
| --- | --- | --- |
| Unchecked workflow task, e.g. `- [ ] spec → specs/X/spec.md` | 75 | not an error — the artifact is future work |
| `path.md:24` citation read as a path | 6 | not an error — the file exists, the suffix does not |
| Genuinely broken, e.g. `workspace/artifacts.md` | 19 | error |

The rule would report all 87 identically. Because it only ever examines one
file, that has never been visible.

The 19 real ones include `workspace/artifacts.md` and `workspace/knowledge.md`,
referenced by issues 090 and 091 as existing infrastructure. Neither file exists;
the artifact registry reports `initialized: false, entries: 0`.

### The existing escape hatch is not a fix

`linked_artifacts` skips any path containing `<>{}`
(`scripts/validate_project_artifacts.py:150-151`), and 14 issue files use it.
That is a documented convention and it works — but it asks the author to
pre-declare which links are future work, at the exact moment they are least sure.
The checkbox already carries that information.

## Scope

### In

- Check the links of the issue being validated, not only the globally active one.
- Derive "not yet" from the workflow task's own checkbox: an unchecked task's
  target is expected to be absent; a checked task's target must exist.
- Stop reading a trailing `:<line>` as part of the path; verify the file and
  ignore the anchor.
- Report the 19 real breakages, and separately decide what
  `workspace/artifacts.md` and `workspace/knowledge.md` should be — issues 090
  and 091 own the answer, not this one.

### Out

- Removing the `<>{}` placeholder convention. It stays valid for paths with no
  checkbox to key off.
- Creating the missing files. Naming them is in scope; deciding what they
  contain belongs to 090 and 091.
- Changing when validation runs, or making it a release gate. Correctness first.

## Acceptance Criteria

- Validating any issue checks that issue's links, whether or not it is active.
- With no active issue set, link validation still runs for the issue under
  examination.
- An unchecked workflow task pointing at a non-existent artifact does not error;
  the same line checked, with the artifact still absent, does.
- `specs/086-…/plan.md:24` validates against `plan.md` and does not error on the
  suffix.
- A fixture asserts the counts above do not silently regress: the suite fails if
  the by-design and false-positive classes start reporting as errors again.
- The 19 real breakages are either fixed or recorded on their owning issues. No
  suppression list.
- `python3 scripts/release_check.py .` passes, `valid` checked at the top level.

## Verification

- Fixture issue with one checked and one unchecked task, both targets absent.
- Fixture issue with a `path.md:24` citation to a file that exists.
- Fixture with no active issue in `.moduflow/state.json`.
- A repository-wide count assertion, so the three classes stay separated.
- `tests/test_validate_project_artifacts.py`.

## Entry Points

- `scripts/validate_project_artifacts.py:352-354` — the caller that scopes to one issue
- `scripts/validate_project_artifacts.py:261-287` — `validate_active_issue_links`
- `scripts/validate_project_artifacts.py:137-154` — `linked_artifacts`, the
  placeholder skip and the missing line-anchor case
- `scripts/validate_project_artifacts.py:105` — `LINK_RE`

## Scope Fence

Do not widen the check and then suppress the noise with an ignore list. If a
link cannot be classified, that is a rule to write, not an exception to record.

## Workflow Tasks

- [ ] spec → `specs/<issue>/spec.md`
- [ ] plan → `specs/<issue>/plan.md` + `tasks.md`
- [ ] execute → scope fix, checkbox-derived expectation, line-anchor handling
- [ ] review → `specs/<issue>/review.md`

## Related Issues

- related: `090-project-knowledge-and-artifact-registry` and
  `091-reproducible-analysis-runs-and-template-pack` (own the two workspace
  files among the 19), `123-empty-declarations-file-disables-linkage-warning`
  (the issue whose clean validation exposed this), `048-artifact-lifecycle-sync`

## Next Command

`product:spec 128-linked-artifact-check-runs-for-one-issue-only`
