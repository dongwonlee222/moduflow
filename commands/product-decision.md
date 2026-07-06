---
description: Create a decision record tied to an issue, spec, or roadmap choice.
argument-hint: "<title> [--issue-id id] [--spec path]"
---

# /product:decision

Record why a product or technical decision was made.

## Script

```bash
python3 scripts/project_knowledge.py . --kind decision --title "Payment priority" --issue-id 003-payment --spec specs/003-payment/spec.md --decision-supported "Prioritize card onboarding"
```

## Required Fields

- issue ID when applicable
- spec path when applicable
- decision supported
- evidence
- caveats
- next action

## Next

- `/product:evidence` to review supporting material
- `/product:roadmap` when priority changes

## Record Contract (issue 075)

Every decision record this command writes carries shared frontmatter so `product:promote` and retention tooling can operate on it:

- `kind`: `decision`
- `date`: ISO date
- `summary`: one line
- `retrieval_trigger`: when a future session should re-read this record (semantic cue, required for new records)
- `promoted_to`: issue id, written by `product:promote` only
- `superseded_by`: record id — supersede, never delete or move record files

Write discipline (AI writers create records for free, so creation is NOT the default):

1. Before creating, search existing records of this kind for the same subject.
2. Prefer UPDATE (extend the existing record) or SUPERSEDE (new record + `superseded_by` on the old one) over ADD.
3. NOOP when nothing genuinely new — do not write a file to log activity.
