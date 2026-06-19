# Tasks: Reduce Approval Popup Friction

- [x] Map approval-triggering commands and classify risk [files: specs/027-reduce-approval-popup-friction/approval-surface.md]
- [ ] Normalize importable validation APIs [files: scripts/validate_project_artifacts.py, scripts/validate_moduflow.py, scripts/project_doctor.py, scripts/release_check.py]
  - [x] Add `validate_moduflow(root)` importable API [files: scripts/validate_moduflow.py, tests/test_validation_distribution.py]
  - [x] Add `project_doctor.inspect_project(root, include_preflight=False)` local-only mode [files: scripts/project_doctor.py, tests/test_validation_distribution.py]
- [x] Keep CLI wrappers backward-compatible while release_check uses importable validation for safe checks [files: scripts/release_check.py, tests/test_validation_distribution.py]
- [ ] Keep remaining CLI wrappers backward-compatible [files: scripts/*]
  - [x] Add `scripts/project_doctor.py --no-preflight` while preserving default full preflight [files: scripts/project_doctor.py]
- [x] Add host/tool adapter guidance for shell-free validation [files: docs/host-adapter-guidance.md, specs/027-reduce-approval-popup-friction/status.md]
- [x] Add resume banner contract for interrupted/resumed work [files: commands/moduflow.md, commands/product-loop.md, commands/product-status.md, docs/host-adapter-guidance.md]
- [x] Add focused tests for importable validation paths [files: tests/*]
- [x] Run validation and release checks [files: specs/027-reduce-approval-popup-friction/status.md]

## Next Command

`/product:execute 027-reduce-approval-popup-friction`
