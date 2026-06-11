# Knowledge Evidence Layer Spec

## Problem

Projects need durable evidence for product decisions, but benchmarks, reports, research notes, data interpretations, and reference links are often scattered. ModuFlow should make these artifacts first-class Git files connected to issues, specs, and roadmap decisions.

## Users

- Project owners recording why a decision was made.
- Agents preparing specs, roadmaps, reports, or status updates.
- Team members reviewing evidence behind a priority or release.

## Goals

- Add a standard `knowledge/` structure.
- Create templates for decisions, benchmarks, reports, research, data notes, and references.
- Provide scripts and commands for initialization and artifact creation.
- Require optional but explicit issue/spec linkage fields.
- Let doctor report whether the knowledge layer is initialized.

## Non-Goals

- Full-text search server.
- External document ingestion without user approval.
- Moving existing reports or research files.
- Storing private personal data, credentials, signed originals, or sealed documents.

## Artifact Structure

```text
knowledge/
  decisions/
  benchmarks/
  reports/
  research/
  data-notes/
  references/
  index.md
```

## Requirements

- `scripts/project_knowledge.py` supports dry-run initialization by default.
- `scripts/project_knowledge.py --write` creates missing knowledge folders and `knowledge/index.md`.
- Existing knowledge files are never overwritten.
- The script can create a single artifact with `--kind`, `--title`, `--issue-id`, `--spec`, and `--decision-supported`.
- `project_doctor.py` reports `knowledge.initialized` and `knowledge.missing`.
- Commands exist for `product:knowledge`, `product:decision`, `product:research`, `product:benchmark`, `product:report`, and `product:evidence`.

## Acceptance Criteria

- A new project can initialize the knowledge structure.
- A knowledge artifact includes issue/spec/decision support fields.
- Doctor output recommends `product:knowledge --write` when the layer is missing.
- Validator requires the new scripts, commands, and templates.

## Next Command

`product:plan 003-knowledge-evidence-layer`
