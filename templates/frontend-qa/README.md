# Frontend QA Template Pack

Use these templates when frontend work needs implementation-ready QA evidence.
Copy only the applicable files into:

```text
specs/<issue>/frontend-qa/
```

Issue 077 owns the readiness gate behavior. This pack provides the evidence
shapes that make the gate easy to satisfy.

## Use Matrix

| Template | Required When | Optional When | Not Applicable When |
| --- | --- | --- | --- |
| `api-contract-mapping.md` | API-backed UI, integration, or data-fetching UI | static UI depends on known external assumptions | no API or data contract changes |
| `storybook-required-states.md` | component, screen, or visual state work | visual review needs repeatable examples | no UI/component work |
| `msw-fixture-catalog.md` | API-backed UI needs mocked states | existing fixtures are reused unchanged | no mocked API behavior |
| `playwright-smoke-matrix.md` | browser-visible user flow or regression path | low-risk visual-only UI | no browser flow |
| `qa-evidence-checklist.md` | frontend implementation or review | design/prototype quality review | backend-only/docs-only work |

## Copy Contract

Each copied template should keep:

- `Issue`
- `Spec`
- `Owner`
- `Reviewer`
- `Status`

Use `Status: not_applicable` with a short reason when a template is reviewed
and deliberately skipped.
