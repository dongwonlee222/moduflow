# Playwright Smoke Matrix

Issue: `<issue-id>`
Spec: `<spec path>`
Owner:
Reviewer:
Status: draft

## Smoke Matrix

| Flow | Route / Entry | User Action | Assertion | Viewport / Device | Fixture / Data |
| --- | --- | --- | --- | --- | --- |
| Example: View item list | `/items` | open page | list or empty state renders | desktop | `itemsSuccess` |
| Example: Retry error | `/items` | click retry | request retried and recovery visible | desktop | `itemsError` |

## Scope

- Primary happy path:
- Regression-prone edge path:
- Auth/permission path:
- Responsive path:

## Review Notes

- Paths intentionally covered elsewhere:
- Manual-only checks:
