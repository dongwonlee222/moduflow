# ModuFlow Roadmap

## Now

### `001-project-migration`

- Outcome: Existing projects can adopt ModuFlow safely.
- Reason: This prevents data loss and lowers adoption friction.
- Confidence: high
- Dependency: current project doctor and config path support
- Next command: `product:spec 001-project-migration`

### `002-project-profile`

- Outcome: Each project has consistent metadata, environment, and integration context.
- Reason: Multi-project work needs stable project identity before portfolio views.
- Confidence: high
- Dependency: config schema extension
- Next command: `product:spec 002-project-profile`

## Next

### `003-knowledge-evidence-layer`

- Outcome: Decisions, benchmarks, reports, research, and data notes become first-class artifacts.
- Reason: Roadmap and spec decisions need traceable evidence.
- Confidence: high
- Dependency: project profile and issue/spec links
- Next command: `product:spec 003-knowledge-evidence-layer`

### `004-portfolio-workspace`

- Outcome: Multiple projects can be viewed from one central workspace.
- Reason: Project-local dashboards are useful but not enough for portfolio management.
- Confidence: medium
- Dependency: project profile and state files
- Next command: `product:spec 004-portfolio-workspace`

## Later

### `005-team-workflow`

- Outcome: Teams can track ownership, review, approval, blockers, and handoff.
- Reason: Multi-person use needs explicit governance without leaving Git.
- Confidence: medium
- Dependency: issue/spec metadata conventions
- Next command: `product:spec 005-team-workflow`

### `006-validation-and-distribution`

- Outcome: Installation, validation, migration, and release flows become repeatable.
- Reason: A plugin used by multiple people needs safe upgrade and doctor tools.
- Confidence: medium
- Dependency: finalized artifact schemas
- Next command: `product:spec 006-validation-and-distribution`
