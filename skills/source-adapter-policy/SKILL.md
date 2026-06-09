---
name: source-adapter-policy
description: Use when ModuFlow needs to update, swap, vendor, or map external skills/plugins such as Productivity, Product Management, Spec Kit, Superpowers, Product Design, or Data Analytics.
---

# Source Adapter Policy

Keep upstream replaceable.

## Rules

1. Track source metadata in `vendor.lock.json`.
2. Put upstream checkouts or snapshots under `vendor/`.
3. Put local modifications under `overlays/`.
4. Put mapping logic under `adapters/`.
5. Do not edit vendored upstream files for local workflow changes.

## Update Flow

```text
vendor.lock.json -> vendor refresh -> adapter compatibility check -> doctor -> status
```

