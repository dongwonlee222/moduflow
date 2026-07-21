# Issue 091: Reproducible Analysis Runs and Template Pack

**Status: backlog** — created 2026-07-16.
**Priority: p1**
**Blocked-by: `090-project-knowledge-and-artifact-registry`**

## Summary

Record reproducible analysis runs and provide reusable templates for monthly trends, CPO changes, amount bands, charging speed, and policy-impact analysis.

## Source

- Type: user product direction
- Link: local Codex session, 2026-07-16
- Owner / decision maker: Dongwon Lee
- Current phase: backlog

## Problem

Data-analysis conclusions change when source populations, filters, exclusions, or processing rules change. A final chart or Sheet link alone cannot explain why the analysis was performed, how it was processed, or why the conclusion changed. Repeated analyses also waste time when each starts from an empty plan.

## Product Decision

- Every analysis is a run with explicit source and processing provenance.
- Run history records why the analysis was requested, inclusion/exclusion rules, processing method, conclusion, caveats, and linked decision.
- Reusable templates guide the analysis contract but do not hardcode project-specific metrics or data logic.
- `workspace/artifacts.md` from Issue 090 registers outputs; analysis run records preserve reproducibility details.

## Scope

### In

- An analysis-run schema covering source Sheet/file, tab/range, extraction timestamp, source hash when available, grain, period, filters, exclusions, processing steps, code/query, outputs, caveats, conclusion, and decision links.
- Append-oriented history that records why conclusions or methods changed.
- Templates for monthly trend, CPO change, amount-band user analysis, slow/fast charging analysis, and policy-change impact analysis.
- `product:analyze --template <name>` guidance or equivalent natural-language routing.
- Links from runs to related issues, knowledge entries, artifact records, reports, and decision records.
- Validation and examples using synthetic/non-sensitive data.

### Out

- Embedding 모두의충전 production data in the ModuFlow repository.
- Hardcoding one company’s metric definitions into generic templates.
- Replacing notebooks, SQL, Sheets, or report artifacts.
- Automatically rerunning paid/external data sources.

## Acceptance Criteria

- A completed run records the request reason, source, time/grain, filters, exclusions, processing, output, caveats, and conclusion.
- A later run can explain what changed from the prior run.
- Each of the five requested analysis templates exists and states required inputs, checks, outputs, and interpretation cautions.
- Run outputs register in `workspace/artifacts.md` and durable interpretation changes can update `workspace/knowledge.md`.
- Decision records remain separate and are linked when analysis leads to an action.
- Templates work with Sheets, CSV/XLSX, SQL extracts, or local files without requiring a specific vendor.
- Validation uses non-sensitive fixtures and `python3 scripts/release_check.py .` passes.

## Verification

- `python3 -m unittest discover -s tests -p 'test_*analysis*run*.py' -v`
- `python3 scripts/validate_project_artifacts.py .`
- `python3 scripts/release_check.py .`

## Entry Points

- `commands/product-analyze.md`
- `skills/data-analysis-bridge/SKILL.md`
- `templates/analysis/`
- `workspace/`
- `scripts/`
- `tests/`

## Scope Fence

Do not store production datasets or credentials in Git. Templates define reproducible contracts and evidence, not company-specific business logic.

## Workflow Tasks

- [ ] spec → `specs/091-reproducible-analysis-runs-and-template-pack/spec.md`
- [ ] plan → `specs/091-reproducible-analysis-runs-and-template-pack/plan.md`
- [ ] execute → run schema, history, five templates, routing, validation, and tests
- [ ] review → `specs/091-reproducible-analysis-runs-and-template-pack/review.md`

## Related Issues

- follows_up: `033-business-document-workflow`, `034-memory-capture-and-sync-workflow`, `090-project-knowledge-and-artifact-registry`
- related: `070-spec-consistency-analyze`, `092-project-home-dashboard`
- blocks: `092-project-home-dashboard`
- blocked_by: `090-project-knowledge-and-artifact-registry`

## Reference Implementations

- MLflow run metadata, parameters, metrics, code versions, and output artifacts: `https://mlflow.org/docs/latest/ml/tracking/`
- MLflow artifact/metadata separation: `https://mlflow.org/docs/latest/self-hosting/architecture/artifact-store/`

## Sessions

- 2026-07-16: User approved reproducibility history and five reusable analysis templates after the knowledge/artifact registry.

## Links

- Roadmap: `workspace/roadmap.md`
- Goal: `workspace/goal.md`
- GitHub: https://github.com/dongwonlee222/moduflow/issues/21

## Next Command

`product:spec 091-reproducible-analysis-runs-and-template-pack`
