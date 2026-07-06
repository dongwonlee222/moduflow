# Issue 003: Knowledge Evidence Layer

**Status: done** — body says "Done. Implemented and merged. (2026-06-16)"; commit 0cf86f8, `scripts/project_knowledge.py` live. Status line added 2026-07-06 (issue 066 follow-up: files whose specs-link line matched the migration's `Status:` grep were skipped).

## Summary

Add a knowledge layer for benchmarks, research, reports, decisions, data notes, and references tied to issues and specs.

## Source

- Type: product direction
- Link: user conversation
- Date: 2026-06-11

## Opportunity

Projects need more than tasks. They need durable evidence explaining why decisions were made and which reports, data, and benchmarks support them.

## Scope

### In

- Add `knowledge/` artifact structure.
- Add templates for decisions, benchmarks, reports, research, data notes, and references.
- Add command definitions for `product:decision`, `product:research`, `product:benchmark`, `product:report`, `product:evidence`, and `product:knowledge`.
- Require issue/spec linkage where applicable.

### Out

- Full-text search server.
- External document ingestion without user approval.

## Acceptance Criteria

- Knowledge artifacts can reference issue IDs and decision support.
- `workspace/dashboard.md` can summarize important decisions and evidence.
- Roadmap decisions can link to evidence.

## Links

- Spec: `specs/003-knowledge-evidence-layer/spec.md`
- Status: `specs/003-knowledge-evidence-layer/status.md`
- Roadmap: `workspace/roadmap.md`

## Status

Done. Implemented and merged. (2026-06-16)

## Next Command
