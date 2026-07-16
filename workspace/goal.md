# Goal: Trustworthy Execution and Project Knowledge

## Objective

Make ModuFlow stop unsafe work before it reaches the wrong repository, turn external review into evidence-backed remediation, and give each project a reproducible knowledge, artifact, analysis, and dashboard home.

## Owner

Dongwon Lee

## Why Now

Repository sync, review handoff, production records, and dashboard foundations already exist. The remaining risk is trust and continuity: remote names can conceal the wrong repository, external review can be accepted without proof, and project conclusions or artifacts can become scattered across files and Sheets.

## Issues

- `088-canonical-repository-remote-identity-gate` — P0; canonical repo/base identity and pre-write blocking.
- `089-verified-code-review-intake-and-remediation-routing` — P1; evidence-backed review disposition.
- `093-frontmatter-issue-schema-readiness-gate` — P1; contradictory readiness/dependency blocking.
- `094-risk-based-security-and-quality-review-gate` — P1; preventive checks learned from approved review history.
- `086-project-aware-production-library-dashboard` — P2; project-scoped production/playbook views after the safety gate sequence.
- `090-project-knowledge-and-artifact-registry` — P1; structured project wiki and artifact registry.
- `091-reproducible-analysis-runs-and-template-pack` — P1; reproducible analysis history and templates.
- `092-project-home-dashboard` — P2; final project home; blocked by 086, 090, and 091.
- `087-korean-github-pr-review-surface` — P1; Korean-first GitHub review publication.

## Completion Criteria

- Wrong repository or archived/read-only identity stops execute, PR, release, and push before writes.
- External review findings have evidence, disposition, remediation timing, and issue candidates.
- Mixed issue schemas cannot report ready/execute while dependencies or readiness are unmet.
- Projects maintain structured knowledge, artifact, and reproducible analysis records.
- The project home shows current work, recent outputs, key Sheets, conclusions, and next actions.

## Constraints

- Git-tracked project files remain canonical; GitHub and dashboard surfaces are projections.
- No automatic remote rewrite or unapproved external publication.
- Sensitive source data and credentials stay outside the repository.
- Existing staged work for issues 081–084 remains independent from this branch.

## History

- `team-visibility-onboarding` — closed before 2026-07-16.
- `visual-workbench` — closed 2026-07-05.

## Next Command

`product:pr 088-canonical-repository-remote-identity-gate`
