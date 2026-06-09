# Vendor Sources

Keep upstream repositories or exported plugin snapshots here when needed.

Recommended model:

1. Track source metadata in `../vendor.lock.json`.
2. Place upstream checkouts under `vendor/<source-id>/`.
3. Keep local Dongwon-specific rules in `../overlays/`.
4. Keep mapping logic in `../adapters/`.

Do not edit upstream files directly unless intentionally forking.

