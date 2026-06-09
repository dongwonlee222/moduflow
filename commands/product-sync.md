---
description: Update or inspect upstream source references.
argument-hint: "[source id]"
---

# /product:sync

Keep upstream skills/plugins easy to update.

## Do

1. Read `vendor.lock.json`.
2. Show current pins and available local vendor folders.
3. Pull or refresh upstream only with user approval.
4. Keep local customizations in `overlays/` and `adapters/`.

## Next

- `/product:doctor` after sync
- `/product:status` to resume work

