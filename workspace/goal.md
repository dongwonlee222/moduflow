# Goal: Trustworthy Execution and Project Knowledge

## Objective

Make ModuFlow stop unsafe work before it reaches the wrong repository, turn external review into evidence-backed remediation, and give each project a reproducible knowledge, artifact, analysis, and dashboard home.

## Owner

Dongwon Lee

## Why Now

Repository sync, review handoff, production records, and dashboard foundations already exist. The remaining risk is trust and continuity: remote names can conceal the wrong repository, external review can be accepted without proof, and project conclusions or artifacts can become scattered across files and Sheets.

## Issues

- `088-canonical-repository-remote-identity-gate` — P0 spec ready; canonical repo/base branch identity, artifact-link audit, and pre-write blocking.
- `090-project-knowledge-and-artifact-registry` — P1; structured project wiki and artifact registry.
- `091-reproducible-analysis-runs-and-template-pack` — P1; reproducible run history and five reusable analysis templates; blocked by 090.
- `089-verified-code-review-intake-and-remediation-routing` — P1; evidence-backed review disposition and remediation candidates.
- `093-frontmatter-issue-schema-readiness-gate` — P1; normalize frontmatter/Markdown issue state and block contradictory readiness/dependencies.
- `094-risk-based-security-and-quality-review-gate` — P1; select preventive checks from feature risk and learn from approved review history; blocked by 089.
- `087-korean-github-pr-review-surface` — P1; Korean-first human review publication.
- `086-project-aware-production-library-dashboard` — P2; project-scoped dashboard foundation.
- `092-project-home-dashboard` — P2; one-screen project home; blocked by 086, 090, and 091.

## Completion Criteria

- Wrong repository or archived/read-only identity stops execute, PR, release, and push before writes.
- External review findings have evidence, disposition, remediation timing, and CognitiveDemand-backed issue candidates.
- Review source authorship and history are durable, and approved security findings can become preventive checks without automatic policy promotion.
- Mixed issue schemas cannot report ready/execute while dependencies or definition readiness are unmet.
- Projects can maintain structured `workspace/knowledge.md` and `workspace/artifacts.md` without duplicating source truth.
- Repeated analyses record sources, filters, exclusions, processing, conclusions, and changes across runs.
- The project home shows current work, recent outputs, key Sheets, final conclusions, next actions, and update dates from canonical records.

## Constraints

- Git-tracked project files remain canonical; GitHub and dashboard surfaces are projections.
- No automatic remote rewrite, GitHub issue publication, or external file upload.
- Sensitive source data and credentials stay outside the repository.
- Existing staged work for issues 081–084 must be preserved and completed independently.

## History

- `team-visibility-onboarding` — closed before 2026-07-16; GitHub issue projection and command onboarding delivered through issues 054/055.
- `visual-workbench` — closed 2026-07-05; issue/knowledge graphs, artifact drill-down, list view, and Korean review packets delivered.

## Next Command

`product:plan 088-canonical-repository-remote-identity-gate`
