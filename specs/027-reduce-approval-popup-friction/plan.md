# Plan: Reduce Approval Popup Friction

Goal: Reduce approval fatigue by separating safe in-process validation from operations that genuinely require shell, Git, network, credential, or destructive permissions.

Architecture: Keep existing scripts as CLI wrappers, but expose importable validation functions and document approval classes. Defer host-specific Antigravity integration until its API surface is verified.

Tech Stack: Python standard library, existing validation scripts, Markdown command docs, ModuFlow issue/spec/status artifacts.

## Task 1: Approval Surface Map

- [ ] List common ModuFlow commands and scripts that trigger shell, Git, network, credential, or destructive approvals.
- [ ] Classify each operation as local read-only, local write, Git write, network/GitHub, account/credential, or destructive.
- [ ] Document which prompts are expected and which can be avoided.

## Task 2: Importable Validation API

- [ ] Add or normalize importable functions for project artifact validation.
- [ ] Add or normalize importable functions for ModuFlow package validation.
- [ ] Ensure project doctor and release check use importable functions internally where feasible.
- [ ] Keep CLI wrappers backward-compatible.

## Task 3: Host Tool Adapter Guidance

- [ ] Define how a host can call validation without shelling out.
- [ ] Document Antigravity as a candidate host integration pending API verification.
- [ ] Keep host-specific adapters separate from core validation logic.

## Task 4: Verification

- [ ] Add focused tests for importable validation APIs.
- [ ] Run focused validation tests.
- [ ] Run `python3 scripts/validate_project_artifacts.py .`.
- [ ] Run `python3 scripts/validate_moduflow.py .`.
- [ ] Run `python3 scripts/release_check.py .`.

## Next Command

`/product:execute 027-reduce-approval-popup-friction`
