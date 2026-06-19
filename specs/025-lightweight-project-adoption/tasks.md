# Tasks: Lightweight Project Adoption

- [x] Add lightweight doctor RED tests [files: tests/test_validation_distribution.py]
- [x] Implement lightweight mode detection in project doctor [files: scripts/project_doctor.py] [depends: T01]
- [x] Exclude tooling directories from project doctor checks in lightweight mode [files: scripts/project_doctor.py] [depends: T02]
- [ ] Update migration and project start logic to only write lightweight files [files: scripts/project_migrate.py, scripts/project_intake.py] [depends: T03]
- [x] Run full verification for current doctor slice [files: specs/025-lightweight-project-adoption/status.md] [depends: T03]
- [ ] Release 025 after start/migrate lightweight write behavior is complete [depends: T04]
