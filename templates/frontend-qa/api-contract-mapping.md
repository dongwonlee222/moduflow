# API Contract Mapping

Issue: `<issue-id>`
Spec: `<spec path>`
Owner:
Reviewer:
Status: draft

## Scope

Describe which UI, screen, or flow depends on API/data behavior.

## Contracts

| Contract | Method / Source | Request / Input | Response / Output | Error / Empty State | Owner |
| --- | --- | --- | --- | --- | --- |
| Example: Load items | `GET /api/items` | query/filter params | item list fields | 401, 404, empty list | backend/frontend |

## Assumptions

- No unstated API shapes should be invented during implementation.
- If a contract is unchanged, link the existing source instead of rewriting it.

## Review Notes

- Open contract questions:
- Approved deviations:
