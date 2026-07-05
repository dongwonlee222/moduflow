# Issue 033: Business Document Workflow

**Status: done** — all workflow tasks checked incl. review/validation; deliverables on disk (`templates/business-plan/`, `tests/test_business_document_workflow.py`, commit 5929502). Status line added 2026-07-05 (issue 066 legacy-schema migration).

## Lifecycle

- Phase: review
- Owner: Dongwon Lee
- Source: Golden Goose market-entry analysis skill design and user feedback on business document outputs
- Created: 2026-06-24

## Outcome

ModuFlow can produce project-local business document artifacts, starting with market-entry analysis, while preserving decisions, assumptions, source evidence, calculations, validation results, exports, and project memory.

## Problem

`moduflow:business-plan` currently covers business plans, Lean Canvas, persona scenarios, and validation plans, but does not yet provide a structured workflow for market-entry reports, profitability review, decision-ready business documents, or Korean executive-report tone.

## Scope In

- Extend `moduflow:business-plan` into a `business-document` router.
- Add `market-entry-analysis` as the first specialized recipe.
- Add reusable templates for document type routing, sources, calculation model, PDF quality, and Korean writing style.
- Create a test market-entry analysis artifact package.
- Enforce polite Korean report tone such as `했습니다`, `검토했습니다`, and `예상됩니다`.
- Connect completed business documents to project memory as deliverables, decisions, and evidence.

## Scope Out

- Full PDF rendering engine implementation.
- Live external market research automation.
- Editing Golden Goose project files from this ModuFlow plugin task.

## Workflow Tasks

- [x] issue -> `issues/033-business-document-workflow.md`
- [x] test -> `tests/test_business_document_workflow.py`
- [x] execute -> business document router, market-entry references, and sample artifact
- [x] review -> full ModuFlow validation passed and plugin cache deployed

## Acceptance Criteria

- `skills/business-plan/SKILL.md` routes market-entry, profitability, pitch, and decision memo requests.
- `templates/business-plan/` includes market-entry analysis support files.
- A sample market-entry artifact exists under `business/test-market-entry-analysis/`.
- Korean narrative prose uses polite report endings, not plain declarative endings.
- Package validation includes the new business document templates.

## Next Command

`product:status`
