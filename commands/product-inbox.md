---
description: Capture raw requests, notes, customer feedback, ideas, or bugs.
argument-hint: "<raw request or source>"
---

# /product:inbox

Capture unstructured input without over-shaping it.

## Do

1. Append the request to `workspace/inbox.md`.
2. Preserve source, date, owner, and confidence when available.
3. Suggest whether it should become an opportunity, issue, or parking-lot item.
4. When available, preserve `moduflow.intake-routing.v1` JSON from `scripts/project_intake.py --write` so later commands can create/link issues without reclassifying the request.

## Next

- `/product:opportunity` for product shaping
- `/product:issue` for obvious implementation work
- `/product:status` to inspect queue

## Record Contract (issue 075)

Every inbox record this command writes carries shared frontmatter so `product:promote` and retention tooling can operate on it:

- `kind`: `inbox`
- `date`: ISO date
- `summary`: one line
- `retrieval_trigger`: when a future session should re-read this record (semantic cue, required for new records)
- `promoted_to`: issue id, written by `product:promote` only
- `superseded_by`: record id — supersede, never delete or move record files

Write discipline (AI writers create records for free, so creation is NOT the default):

1. Before creating, search existing records of this kind for the same subject.
2. Prefer UPDATE (extend the existing record) or SUPERSEDE (new record + `superseded_by` on the old one) over ADD.
3. NOOP when nothing genuinely new — do not write a file to log activity.
