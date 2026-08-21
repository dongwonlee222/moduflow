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
- `097-single-entry-capability-routing-contract` — P2; predictable single-entry specialist routing with offline safety simulation.
- `098-speckit-selective-validation-adapter` — P2; selectively activate Spec Kit validation after Issue 097 proves the routing boundary.
- `102-project-registry-and-resolver` — P0; explicit registry v2, deterministic project resolution, and canonical artifact paths.
- `103-atomic-lifecycle-state-transaction` — P0; all-or-nothing lifecycle/state/dashboard/production updates with rollback.
- `104-project-aware-natural-language-request-orchestrator` — P0; connect the existing single entry point to project context, production knowledge, capability routing, verification, and atomic handoff.
- `105-schema-migration-and-doctor-triage` — P0; prioritize blockers, plan/apply reversible migrations, and safely fix deterministic legacy drift.
- `106-korean-production-search-and-stable-ids` — P1; Korean multi-token retrieval, match reasons, and meaningful collision-resistant production IDs.
- `107-shared-approved-playbook-layer` — P1; share only explicitly approved and redacted organization rules while raw project knowledge stays isolated.
- `108-production-approval-and-verification-gates` — P1; approver readiness and evidence-backed deliverable-specific final-state gates.
- `109-canonical-project-context-consumer-convergence` — P0; eliminate remaining direct project-path assumptions before Issue 103 implementation.
- `110-project-operation-capability-enforcement` — P0; separate resolved identity from read/write/execute/publish authorization before Issue 103 implementation.
- `111-runtime-provenance-and-validation-mode-separation` — P1; distinguish source, installed package, and target-project validation and expose active runtime provenance before the next plugin release.

## Workstream: Safe Multi-Project Request Orchestration

Route natural-language work to one explicit project, reuse only permitted project/shared knowledge, verify the result, and update every lifecycle view without partial state.

```mermaid
flowchart LR
    I085[085 Production records\ndone] --> I106[106 Korean search + stable IDs\nP1]
    I085 --> I104[104 Request orchestrator\nP0]
    I048[048 Lifecycle sync\ndone] --> I103[103 Atomic state transaction\nP0 spec review]
    I004[004 Portfolio registry\ndone] --> I102[102 Registry v2 + resolver\nP0]
    I002[002 Project profile\ndone] --> I102
    I102 --> I109[109 Canonical consumers\nP0]
    I102 --> I110[110 Capability enforcement\nP0]
    I102 --> I111[111 Runtime diagnostics\nP1]
    I109 --> I103
    I110 --> I103
    I102 --> I104
    I103 --> I104
    I102 --> I105[105 Migration + Doctor triage\nP0]
    I103 --> I105
    I102 --> I107[107 Shared approved playbooks\nP1]
    I106 --> I107
    I104 --> I108[108 Production approval + verification\nP1]
    I102 --> I086[086 Production dashboard\nP2]
```

**Review decision:** existing Issues 020, 022, 065, 076, 088, 097, 102, 103, and 105 were checked before registration. The verified Issue 102 follow-up findings are not duplicate deliverables: Issues 109 and 110 are P0 prerequisites for Issue 103 implementation, while the two related runtime/validation findings are intentionally grouped into Issue 111.

## Completion Criteria

- Wrong repository or archived/read-only identity stops execute, PR, release, and push before writes.
- External review findings have evidence, disposition, remediation timing, and issue candidates.
- Mixed issue schemas cannot report ready/execute while dependencies or readiness are unmet.
- Projects maintain structured knowledge, artifact, and reproducible analysis records.
- The project home shows current work, recent outputs, key Sheets, conclusions, and next actions.
- A request resolves exactly one registered project before any project-local read or write.
- Every project-aware path consumer uses that resolved context, including non-default registered folders.
- Archived/read-only projects remain readable but cannot write, execute, or publish.
- Project A raw issues, records, local playbooks, and brand language never appear in Project B work.
- Related work attaches to an existing issue; only independent deliverables create new issue candidates.
- Lifecycle mutations either update all configured canonical/derived state together or preserve the complete prior state.
- Legacy migration is planned, reversible, idempotent, and separated from current-work blockers in Doctor output.
- Source release validation, installed-plugin self-check, and target-project Doctor are distinct, and status identifies the actually loaded runtime/package provenance.
- Korean multi-token production search returns explained matches and Korean-titled records receive stable meaningful IDs.
- Only explicitly approved, redacted shared playbooks cross project boundaries.
- Production artifacts cannot become final, approved, published, or upload-ready without required verification evidence.

## Constraints

- Git-tracked project files remain canonical; GitHub and dashboard surfaces are projections.
- No automatic remote rewrite or unapproved external publication.
- Sensitive source data and credentials stay outside the repository.
- Existing staged work for issues 081–084 remains independent from this branch.
- Existing Issues 085 and 086 are extended through follow-ups, not replaced or rewritten.
- Registered projects only; no arbitrary sibling-project crawling or cross-project raw-record search.
- No automatic shared-playbook promotion, approver authorization, or unverified final-state transition.
- Issue 102 is merged and externally revalidated. Issue 103 implementation cannot begin until Issues 109 and 110 complete; Issue 111 may run in parallel but must complete before the next plugin release.

## Status

- State: `active`
- Blocker: Issues 109 and 110 must complete before Issue 103 implementation.
- Updated: 2026-08-21

## History

- `team-visibility-onboarding` — closed before 2026-07-16.
- `visual-workbench` — closed 2026-07-05.

## Next Command

`product:spec 109-canonical-project-context-consumer-convergence`

Issue 103 specification is ready for human review now; its implementation plan follows after Issues 109 and 110 complete.
