# Review: Project Production Records and Playbooks

Issue: `085-project-production-records-and-playbooks`
Reviewer: independent read-only Codex (`gpt-5.5`, medium reasoning)
Date: 2026-07-10
Verdict: approved after fixes

## Scope

Reviewed the uncommitted Issue 085 implementation against the issue, canonical spec, and implementation plan. Focus areas were correctness, project isolation, exact human approval, offline validation, duplicate preservation, internal/external copy separation, CLI behavior, and stable collector interfaces for Issue 086.

## Findings

1. **High — same-day/title ID collision blocked distinct records.** Resolved by preserving the simple base ID for the first record and deterministically adding source context when a different capture key collides. Added a regression test proving both records are created without overwrite.
2. **Medium — CLI usage errors raised `SystemExit(2)` instead of returning `2`.** Resolved with a returning argument parser and a focused direct-`main(argv)` test.
3. **Medium — missing `--issue-id` and `--source-context` returned mutation failure `1`.** Resolved by classifying the missing source as a usage error and returning `2`.

## Additional Contract Fixes

- Aligned Playbook parsing/templates with canonical `applies_to_types`, `applies_to_channels`, `version`, `review_after`, and `superseded_by` metadata while preserving normalized Issue 086 fields.
- Corrected the record lifecycle vocabulary to `draft`, `review`, `approved`, `published`, and `archived`.
- Added stale Playbook review-date warnings and stable `updated desc, id asc` search ordering.

## Verification Review

A second read-only review confirmed the same-day/title collision fix. It re-raised the two CLI items on the opposite premise that `main(argv)` should raise `SystemExit` and missing source context should not be a usage error. Those two follow-up findings are recorded but rejected: the implementation plan explicitly defines `main` as returning `0` success, `2` usage, and `1` validation/mutation failure, and explicitly requires `--issue-id` or `--source-context` for `--new-record`. The regression tests therefore preserve the specified interface.

## Residual Risk

- The Markdown frontmatter parser intentionally follows ModuFlow's existing lightweight YAML-like conventions; complex quoted YAML values remain outside this issue's scope.
- Cross-project retrieval remains unavailable by design and requires a future explicit human-approved workflow.
