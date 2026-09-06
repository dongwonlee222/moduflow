---
description: Create UX/product design brief for an issue/spec.
argument-hint: "<issue id>"
user-invocable: false
---

# /product:design

Bridge PM intent to design work.

## Do

1. Use Product Design brief gating where available.
2. Define user journey, screens, states, edge cases, and interaction requirements.
3. For UI work that may proceed to implementation, identify the Storybook required states and QA evidence checklist entries that should be copied from `templates/frontend-qa/`.
4. Save to `specs/<issue>/design-brief.md`.

## Next

- `/moduflow prototype` for a reviewable prototype
- `/moduflow plan` if design is sufficient
- `/moduflow review` for UX validation
