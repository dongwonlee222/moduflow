# Tasks: Silent Status Fallback in the Issue Parser

Issue: `120-silent-status-fallback-in-issue-parser`
Plan: `specs/120-silent-status-fallback-in-issue-parser/plan.md`
Status: planned — awaiting the section 6 non-ASCII decision before execute

## Stream A — Parser result

- [ ] Add reason fixtures covering ok, missing, unreadable and unrecognised, plus empty text and an empty status value [files: tests/fixtures/issue-status/README.md, tests/test_project_issue_schema.py]
- [ ] Add markdown_status_result and reduce markdown_status to a wrapper over it, keeping its return values identical [files: scripts/project_issue_schema.py] [depends: T01]
- [ ] Separate a present-but-unreadable status line from an absent one so non-ASCII reports unreadable, not missing [files: scripts/project_issue_schema.py] [depends: T02]
- [ ] Add the parity test asserting markdown_status output is unchanged across every file in issues/ [files: tests/test_project_issue_schema.py] [depends: T02]

## Stream B — Validator surfacing

- [ ] Confirm which validator entry owns issue diagnostics and whether its output reaches product:doctor, and record the answer before writing code [files: specs/120-silent-status-fallback-in-issue-parser/status.md] [depends: T03]
- [ ] Emit one diagnostic per non-ok issue naming the issue id and the raw token [files: scripts/validate_project_artifacts.py] [depends: T05]
- [ ] Assert a valid corpus produces no new diagnostics and an invalid fixture produces exactly one [files: tests/test_project_issue_schema.py] [depends: T06]

## Stream C — Documentation and scan

- [ ] Document the supported status vocabulary and the treatment of an unsupported token [files: commands/product-issue.md] [depends: T03]
- [ ] Run the corpus scan and record the count relying on the fallback without editing any issue file [files: specs/120-silent-status-fallback-in-issue-parser/status.md] [depends: T06]

## Required Gates

- [ ] `markdown_status` output identical across all 125 issue files before and after.
- [ ] `python3 -m unittest discover -s tests` green.
- [ ] `python3 scripts/project_lifecycle.py . --drift` unchanged before and after.
- [ ] The diagnostic is shown on a surface a person reads, not only in returned JSON.
- [ ] `python3 scripts/release_check.py .` reports 14 of 14.
- [ ] `LIFECYCLE_STATES` is byte-identical to its value at the start of this issue.

## Next Command

`product:workers 120-silent-status-fallback-in-issue-parser`
