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

