# Release Checklist

## Required Checks

Run before publishing or reinstalling ModuFlow:

```bash
python3 scripts/validate_moduflow.py .
python3 -m unittest discover -s tests -v
python3 scripts/project_doctor.py .
python3 scripts/validate_project_artifacts.py .
python3 scripts/release_check.py .
```

## Plugin Update

1. Confirm working tree is clean.
2. Update version metadata when releasing a new plugin version.
3. Run the cachebuster update script when Codex should pick up a changed package.
4. Run `python3 scripts/register_codex_personal_marketplace.py .`.
5. Confirm the output includes a Codex cache path for the new version.
6. Start a new Codex thread and test `@ModuFlow product:status`.

## Rollback

Use Git to return to the previous known-good commit or tag, then reinstall the plugin from that source.
