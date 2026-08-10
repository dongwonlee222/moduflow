# Vendor Sources

`vendor/spec-kit/0.16.1/` contains only four byte-exact command-template
snapshots from `github/spec-kit` commit
`684b3d8e05263a7c1948d3d0699ab1cb4f77c3d5`:

- `commands/clarify.md`
- `commands/analyze.md`
- `commands/checklist.md`
- `commands/converge.md`

`manifest.json` is the executable source/hash contract. Verify or refresh the
snapshot only through the explicit command below; it downloads all four files,
checks every SHA-256 before replacing any destination, and writes nothing
without `--write`.

```bash
python3 scripts/sync_spec_kit_templates.py . --write
```

The Markdown files are upstream bytes, not local policy. Do not edit, import,
or execute them. ModuFlow safety and ownership rules live in
`adapters/spec-kit.yaml` and the selective-validation overlay.
