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
5. Run `scripts/release_check.py .` after sync-sensitive changes.
6. Run `python3 scripts/antigravity_sync.py --host <host task.md> --git <git tasks.md>` to sync checkboxes between Antigravity and ModuFlow.

## Antigravity Artifact Sync

To keep host-native planning artifacts (like `task.md` in Antigravity) synced with Git-native spec tracking (like `tasks.md` in ModuFlow):
```bash
python3 scripts/antigravity_sync.py --host /path/to/host/task.md --git /path/to/moduflow/specs/<issue>/tasks.md
```
This command performs a bidirectional status merge of checked (`[x]`), in-progress (`[/]`), and uncompleted (`[ ]`) checkboxes.

## Next

- `/product:doctor` after sync
- `/product:status` to resume work
