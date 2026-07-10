# Status: Project Production Records and Playbooks

Issue: `085-project-production-records-and-playbooks`
Phase: ready-for-pr
Updated: 2026-07-10

## Completed

- Product direction and project-local ownership approved.
- Canonical English and Korean specs completed.
- Production Record and Playbook parsers, templates, collectors, and duplicate-safe capture completed.
- Exact configured-human approval, audited approve/reject/defer decisions, project-local search/retrieval, and offline validation completed.
- `product:production` routing, package checks, and banner/press-release dogfood fixtures completed.
- Independent review found three actionable defects; all were fixed with regression tests. See `review.md`.

## Pending

- PR/release artifacts.

## Blockers

- None for Issue 085.
- Issue 086 implementation remains blocked until Issue 085's parser and normalized payload interfaces are complete.

## Verification

- Focused production suite: 24 passed.
- Full repository suite: 483 passed.
- Spec consistency: 0 findings.
- Package, project, release, lint, and security gates: passed.

## Next Command

`product:pr 085-project-production-records-and-playbooks`
