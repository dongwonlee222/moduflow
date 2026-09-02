# Purpose-First Plugin Rule Follow-up

Issue: `060-cross-agent-output-format-convention` (existing output convention; no duplicate issue).
Owner / decision maker: Dongwon Lee.
Source: user requested why needed → problem → expected benefits in PRs/work reports, then clarified that this must be a ModuFlow rule, not only repository AGENTS.md; 2026-09-02.
Phase: local implementation, focused and full verification passed; remote handoff in progress, integration/publication pending. The original 060 completion record is unchanged.
Next command: `product:review 060-cross-agent-output-format-convention` for this follow-up diff, without changing the active 111 release cursor.

## Why Needed

Users need to understand the purpose of work before reviewing its technical changes. The convention must travel with the installed ModuFlow plugin across projects and hosts.

## Problem

The previous rule was saved only in the development worktree's AGENTS.md. The PR generator still used generic PR-process prose as its Purpose and did not include the owning issue's rationale, problem or expected benefit. The original Issue 111 explanation and PR required manual correction.

## Expected Benefits

PRs and reports can explain user value first, and later sessions can discover the same rule from the package. Fewer clarification exchanges are expected, not a measured result or a guarantee of model compliance.

## Changes

- Shared shipped rule: `docs/output-format.md`; AGENTS.md now points to it instead of owning a separate personal preference.
- Package entry and artifact skills reference the rule. Direct PR/report/update/status/weekly commands reference the executing package's copy, not a target-project file.
- `scripts/project_pr.py` renders the three source-backed sections before technical review/evidence. Issue fields take precedence over the configured spec per field; missing fields are explicit rather than inferred from code/test summaries. Source language is preserved for author review/translation.
- Existing Issue 111 hand-edited PR documents and the 25 unrelated untracked Issue 103 plans are preserved. No generator was run against those live review documents.

## Verification

- RED: three added PR tests produced six expected subtest failures for missing rationale sections/source content.
- GREEN: final PR, installer, registry and operation focused run passed 78 tests in 2.363s, including Korean/per-field precedence. Artifact validation passed with 0 errors and 21 existing warnings; `git diff --check` passed.
- Temporary-home package smoke: `docs/output-format.md` bytes and skill-relative links survived the real packaging path; installed-package validation passed. No real cache or host configuration was changed.
- Source package validation passed (`valid=true`, 203 required files); legacy source receipt warning remains. This is not the full source release check.
- Skill Creator's standalone `quick_validate.py` could not run: PyYAML is missing in both checked Python runtimes. No dependency was installed; ModuFlow's own package validator passed and edited skill frontmatter was unchanged.
- No subagent pressure tests or actual host behavioral observations were performed, respecting the user's no-subagent constraint. Script output and package inclusion checks do not prove universal AI compliance.
- Final full suite on the 0.3.56 follow-up tree: 1,614 tests passed in 315.623s, exit 0, no skips. Full suite used process-local bundled native Git; no host settings were changed.
- Remote CI for this follow-up, merge, publication and installation are not yet complete. PR #45 CI passed separately at `d5e143b`; it does not cover this follow-up.
