# Release Checklist

## Required Checks

Run before publishing or reinstalling ModuFlow:

```bash
python3 scripts/validate_moduflow.py . --mode source --json
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
6. Validate the returned exact cache path with `scripts/validate_moduflow.py <cache-path> --mode installed --json`; retain `.moduflow-package.json` and its payload digest as evidence.
7. Start a new Codex task and test `@ModuFlow product:status`. Record package path/version and CLI/MCP startup separately from host skill-loading evidence; an unavailable host field stays unknown.

## Evidence Boundaries (111)

Record implementation, unit tests, offline simulations, packaged CLI/MCP smoke, remote integration, publication, installed receipt and actual Codex/Claude observations separately. Run `python3 -m unittest tests.test_runtime_provenance_simulation -v` using fake homes; this is not a real installation. Source version equality, a recent cache directory, or a successful CLI invocation never proves that the host reloaded its prompt skills.

The installer publishes a prepared, validated cache and rejects conflicting payloads at the same version with `PACKAGE_DESTINATION_CONFLICT`. Use an explicitly approved new version/build identifier; never delete the old package to make the conflict disappear. Missing receipts on legacy packages remain explicit warnings; malformed receipts or payload mismatches fail installed validation. Doctor takes a project, not the cache, and reports wrong-target diagnostics before project discovery.

## Rollback

Preserve the prior approved package and registration/link values before installation. After explicit approval, restore those values or install the prior approved source as a distinct validated package, restart the affected process and verify its evidence. Do not hard-reset a dirty worktree, overwrite an immutable receipt, or infer successful rollback from source files alone. Cache publication does not claim atomic rollback of every host configuration/link change; report activation failures separately.
