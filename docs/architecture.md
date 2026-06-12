# ModuFlow Architecture

## Layers

```mermaid
flowchart TB
  U["User command: /product:*"] --> R["PM execution router"]
  R --> G["Git artifact model"]
  G --> I["issues/*.md"]
  G --> S["specs/*"]
  G --> M["workspace/roadmap.md + status views"]
  R --> A["Adapters"]
  A --> PM["Product Management"]
  A --> P["Productivity dashboard"]
  A --> SK["Spec Kit"]
  A --> SP["Superpowers"]
  A --> PD["Product Design"]
  A --> DA["Data Analytics"]
  A --> DOC["Documents / Sheets / Slides"]
  SP --> W["Workers / subagents"]
  W --> V["Verification"]
  V --> PR["PR / release / update"]
```

## Rule

All durable state is Git-managed. Adapters may create views, drafts, reports, dashboards, and prototypes, but they must reference an issue ID.

## Project Artifact Tree

```text
.moduflow/
  config.json
  state.json
issues/
  001-example.md
specs/
  001-example/
    spec.md
    analysis.md
    metrics.md
    design-brief.md
    prototype.md
    plan.md
    tasks.md
    status.md
    pr.md
    release.md
    stakeholder-update.md
workspace/
  inbox.md
  opportunities.md
  roadmap.md
  dashboard.md
```

