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

