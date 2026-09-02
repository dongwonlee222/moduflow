# ModuFlow Workflow

```mermaid
flowchart LR
  A["/product:inbox"] --> B["/product:opportunity"]
  B --> C["/product:issue"]
  C --> D["/product:spec"]
  D --> E{"Needs evidence?"}
  E -->|yes| F["/product:analyze"]
  E -->|no| G{"Needs UX?"}
  F --> G
  G -->|yes| H["/product:design"]
  H --> I["/product:prototype"]
  G -->|no| J["/product:plan"]
  I --> J
  J --> K["/product:execute"]
  K --> L["/product:review"]
  L --> M{"Pass?"}
  M -->|no| J
  M -->|yes| N["/product:pr"]
  N --> O["/product:release"]
  O --> P["/product:update"]
  C --> R["/product:roadmap"]
  D --> R
  O --> R
  R --> S["/product:status"]
```

## Verification Ownership

- Main agent: orchestration, final synthesis, risk calls
- `implementation-worker`: code and task execution
- `qa-reviewer`: tests and acceptance criteria
- `ux-flow-worker`: UX flow and prototype review
- `data-reviewer`: metric integrity and analysis checks
- `release-manager`: PR, deploy, release, rollback checks

## Operation Policy Gate

Every target-project mutation resolves and validates its project context, then checks the declared operation before reading unrelated project files, creating temporary files, invoking Git, or calling an external service.

| Project policy | Read | Write / Execute / Publish |
| --- | --- | --- |
| active + internal | allowed | policy-eligible; downstream gates still apply |
| archived | diagnostic read allowed | denied |
| read-only trust | diagnostic read allowed | denied |
| missing or unknown policy | diagnostic read allowed | denied |
| unresolved or ambiguous context | denied | denied |

CLI policy denials print `moduflow.project-operation-authorization.v1` JSON and return non-zero without a traceback. Publication eligibility never replaces canonical repository identity, review evidence, release checks, required status checks, or explicit human approval.

Portfolio dashboard, initialization, and recent-selection writes use a separate portfolio-control context. A selected target project's capability decision cannot authorize a portfolio write, and a portfolio decision cannot be reused to mutate that target.

A standalone non-project transport may be classified as `external-control` only when it performs network-only publication. The audit rejects that scope if the same function also creates or changes a file, temporary artifact, Git state, or project state.

## Lifecycle Transaction and Remote-After-Local

Lifecycle-changing commands follow one local sequence:

```text
plan -> authorize -> recover incomplete transactions -> re-plan
-> projected validation -> lock + canonical hash/semantic recheck
-> journaled local apply -> post-apply validation
-> applied/noop or exact rollback/recovery_required
-> review/release/human gates -> remote publication or deployment
```

The plan and projected validation occur before private transaction writes. Authorization occurs before lock, journal, staging, temporary, evidence, or canonical mutation. The locked recheck prevents a concurrent edit or duplicate semantic Production Record version from being overwritten.

The **remote-after-local** rule is strict: Git commit, Git push, GitHub mutation, deployment, and external message delivery may begin only after the local result is `applied` or `noop` and every existing review, release, CI, repository-identity, capability, and human-approval gate has passed. `denied`, `conflict`, `rolled_back`, and `recovery_required` stop the workflow before remote work.

A failure in a later remote system belongs to that remote workflow and is recorded or retried there. It does not make the lifecycle transaction guess about remote state or speculatively roll back an already verified local result. For incomplete local state, inspect with Doctor and run `python3 scripts/project_lifecycle.py <root> --recover <transaction-id>`; never manually delete transaction state, and never guess when recovery evidence is ambiguous.
