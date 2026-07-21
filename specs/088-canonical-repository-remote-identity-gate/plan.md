# Canonical Repository/Remote Identity Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make ModuFlow prove that the active checkout and every repository-writing workflow target the configured canonical repository before the first write.

**Architecture:** Add one injected-runner identity module that owns configuration parsing, URL normalization, Git/provider inspection, artifact-link classification, capability calculation, and operation decisions. Project profile, doctor/status, execution, commit/push, GitHub issue, PR, release, and validation consumers receive its versioned result instead of parsing remotes independently. Read-only commands report evidence; write commands fail closed at their immediate write boundary.

**Tech Stack:** Python 3 standard library, `unittest`, Git/GitHub CLI through injected runners, JSON/Markdown Git-native artifacts.

---

## Global Constraints

Constitution v1.0 applies (`workspace/constitution.md`). Plan-specific additions:

- `scripts/project_repository_identity.py` is the only parser for `git.identity`, Git remote URLs, and repository-bearing artifact URLs (C8).
- Every Git, GitHub CLI, and subprocess call uses an injected runner; tests never depend on a live remote or authenticated account (C1).
- Gate failures return explicit reason codes and sanitized evidence; no broad exception may convert a failure into an empty or allowed result (C2).
- Doctor/status/validation remain read-only. Execute, commit, push, issue sync, PR, and release stop before the first local or external write when their requested capability is false.
- No code path changes remotes, adopts an observed URL as canonical intent, rewrites artifact URLs, unarchives a repository, or provides a generic force bypass.
- Credential-bearing URLs are sanitized before entering results, errors, logs, profile output, or handoff artifacts.
- All fetch and push URLs are evaluated without truncation. Any non-canonical URL relevant to the operation blocks rather than being silently ignored (C11).
- Existing `git.remote` remains readable only as migration evidence. It never satisfies a remote-mode write gate by itself.
- Feature branches are valid. The configured base ref must exist, but the current branch does not have to equal it.
- Existing staged/unstaged user changes are preserved. Files with overlapping edits are inspected before patching and are never reset or overwritten.

## Recommended Discipline

| Stream | Discipline / Adapter | Reason |
| --- | --- | --- |
| A — identity core | Superpowers TDD | URL and policy edge cases must be fixed by tests before consumers depend on them. |
| B — profile migration | TDD + Git-native artifact model | Canonical intent must be explicit and unrelated config/profile content must survive. |
| C — read surfaces | TDD + ModuFlow progress dashboard | Doctor/status need stable, compact expected-versus-observed evidence. |
| D — write gates | TDD + systematic debugging | Each consumer has a distinct first-write boundary that must be proven. |
| E — artifact links | TDD + Git-native artifact model | One classifier must distinguish canonical, mirror, reference, and unsafe write targets. |
| F — completion | verification-before-completion | Focused tests, project validation, and release check are required before review. |

## File Structure

- Create `scripts/project_repository_identity.py`: canonical config parser, URL normalizer, artifact-link classifier, Git/provider inspector, capability evaluator, and operation decision.
- Create `tests/test_project_repository_identity.py`: core URL, Git/provider evidence, lifecycle, and capability matrix coverage using `FakeRunner`.
- Modify `scripts/project_profile.py`: propose and explicitly write `git.identity`; render a delimited human projection without replacing unrelated profile text.
- Modify `tests/test_project_profile.py`: migration proposal, explicit write, local-only, and preservation tests.
- Modify `.moduflow/config.json`, `templates/moduflow-config.json`, `.moduflow/project-profile.md`: dogfood the canonical identity and update the starter shape.
- Modify `scripts/project_doctor.py`, `scripts/project_sync.py`: add the shared identity result to doctor/status preflight output.
- Modify `tests/test_project_doctor.py`, `tests/test_project_sync.py`: report-only mismatch/unconfigured/provider-unavailable coverage.
- Modify `scripts/project_execution.py`, `scripts/project_git_handoff.py`: gate execute/commit/push before artifact, index, commit, API, or push mutation.
- Modify `tests/test_project_execution.py`, `tests/test_project_git_handoff.py`: prove the first-write boundary is not reached on mismatch.
- Modify `scripts/project_github_issues.py`, `scripts/project_pr.py`, `scripts/release_check.py`: resolve explicit canonical `owner/repo` and gate GitHub writes/releases.
- Create `tests/test_project_github_issues.py`; modify `tests/test_project_pr.py`, `tests/test_validation_distribution.py`: stale-link and provider-evidence tests.
- Modify `scripts/validate_project_artifacts.py`: audit repository-bearing artifact links using the shared classifier.
- Create `tests/test_project_repository_links.py`: canonical, declared mirror/reference, stale write-handoff, and credential-redaction cases.
- Modify `commands/product-profile.md`, `commands/product-doctor.md`, `commands/product-status.md`, `commands/product-execute.md`, `commands/product-pr.md`, `commands/product-release.md`, and `commands/product-sync.md`: document report and hard-stop behavior.
- Update `issues/088-canonical-repository-remote-identity-gate.md`, `specs/088-canonical-repository-remote-identity-gate/tasks.md`, `specs/088-canonical-repository-remote-identity-gate/status.md`, `status.md`, and `workspace/roadmap.md` as execution advances.

## Interfaces

### Canonical configuration

```json
{
  "git": {
    "required": true,
    "github_sync": "optional",
    "issue_source": "git-files",
    "remote": "https://github.com/dongwonlee222/moduflow",
    "identity": {
      "mode": "remote",
      "provider": "github",
      "canonical_repository": "github.com/dongwonlee222/moduflow",
      "remote_name_hint": "origin",
      "base_branch": "main",
      "lifecycle": "active"
    }
  }
}
```

### Core functions

```python
def load_repository_identity(root):
    """Return validated canonical identity or explicit configuration reasons."""


def normalize_git_url(value, provider):
    """Return credential-free host/path identity or raise IdentityConfigError."""


def inspect_repository_identity(root, runner=None, provider_check=None):
    """Return moduflow.repository-identity.v1 expected/observed/capability evidence."""


def operation_decision(result, operation):
    """Return allowed, capability, reasons, and sanitized evidence for one operation."""
```

### Result and decision

```python
{
    "schema": "moduflow.repository-identity.v1",
    "status": "match",
    "expected": {
        "mode": "remote",
        "provider": "github",
        "repository": "github.com/dongwonlee222/moduflow",
        "remote_name_hint": "origin",
        "base_branch": "main",
        "lifecycle": "active",
    },
    "observed": {
        "git_root": "/project/moduflow",
        "fetch_repositories": ["github.com/dongwonlee222/moduflow"],
        "push_repositories": ["github.com/dongwonlee222/moduflow"],
        "base_ref": "refs/remotes/origin/main",
        "provider_repository": "github.com/dongwonlee222/moduflow",
        "provider_default_branch": "main",
        "provider_archived": False,
        "provider_fork": False,
        "artifact_link_mismatches": [],
    },
    "capabilities": {
        "read": True,
        "execute": True,
        "commit": True,
        "push": True,
        "github_write": True,
        "release": True,
    },
    "reasons": [],
}
```

```python
{
    "schema": "moduflow.repository-operation-decision.v1",
    "operation": "push",
    "capability": "push",
    "allowed": False,
    "reasons": [
        {
            "code": "push_remote_mismatch",
            "message": "Observed push repository does not match the canonical repository.",
        }
    ],
}
```

Operation mapping is fixed: `doctor/status/validate -> read`, `execute -> execute`, `commit -> commit`, `push -> push`, `github_issue/pr -> github_write`, `release -> release`.

## Implementation Readiness Inputs

- API contract: N/A; this feature calls Git and GitHub CLI through injected runner contracts.
- Test strategy: focused `unittest` RED/GREEN slices for each stream, then full discovery and release checks.
- Storybook/MSW/Playwright: N/A; no frontend runtime is changed.
- Permission model: read-only operations always report; local and external writes require the matching capability and existing workflow approval rules remain in force.
- Release/rollback: release only after the new gate passes for ModuFlow itself. Roll back by reverting the issue commit; configuration keeps legacy `git.remote` for compatibility and no remote is mutated.

### Stream A — Identity Core

#### Task 1: Core Configuration And URL Normalization

**Files:**
- Create: `scripts/project_repository_identity.py`
- Create: `tests/test_project_repository_identity.py`

- [x] **Step 1: Write failing URL/config tests**

Add tests for HTTPS, `ssh://`, SCP-style SSH, optional `.git`, GitHub lowercase comparison, generic path case preservation, credential redaction, malformed URLs, local paths in remote mode, missing identity, invalid enums, and explicit local-only configuration.

```python
def test_github_url_forms_normalize_to_one_identity(self):
    values = [
        "https://github.com/Owner/Repo.git",
        "ssh://git@github.com/Owner/Repo.git",
        "git@github.com:Owner/Repo.git",
    ]
    normalized = {self.module.normalize_git_url(value, "github") for value in values}
    self.assertEqual(normalized, {"github.com/owner/repo"})


def test_credentials_never_appear_in_normalized_value_or_error(self):
    value = "https://oauth2:secret-token@github.com/Owner/Repo.git"
    self.assertEqual(
        self.module.normalize_git_url(value, "github"),
        "github.com/owner/repo",
    )
    self.assertNotIn("secret-token", repr(self.module.normalize_git_url(value, "github")))
```

- [x] **Step 2: Run the RED slice**

```bash
python3 -m unittest tests.test_project_repository_identity.RepositoryUrlTests tests.test_project_repository_identity.RepositoryConfigTests -v
```

Expected: import or attribute failures because the core module does not exist.

- [x] **Step 3: Implement the smallest parser/normalizer**

Implement `IdentityConfigError`, `sanitize_url`, `normalize_git_url`, and `load_repository_identity`. Return stable configuration reasons instead of inferred values. Do not call Git in this step.

- [x] **Step 4: Run the GREEN slice**

```bash
python3 -m unittest tests.test_project_repository_identity.RepositoryUrlTests tests.test_project_repository_identity.RepositoryConfigTests -v
```

Expected: all URL/config tests pass.

#### Task 2: Git/Provider Inspection And Capability Policy

**Files:**
- Modify: `scripts/project_repository_identity.py`
- Modify: `tests/test_project_repository_identity.py`

- [x] **Step 1: Write failing inspection/policy tests**

Use one `FakeRunner` keyed by argument tuples. Cover matching fetch/push, wrong fetch, wrong push, missing remote, missing base ref, linked worktree root, feature branch, multiple URLs, fork, provider mismatch, provider unavailable, active/read-only/archived, and local-only.

```python
def test_origin_name_cannot_hide_wrong_repository(self):
    runner = FakeRunner({
        ("git", "rev-parse", "--show-toplevel"): ok("/project/moduflow\n"),
        ("git", "remote", "get-url", "--all", "origin"): ok("git@github.com:other/repo.git\n"),
        ("git", "remote", "get-url", "--push", "--all", "origin"): ok("git@github.com:other/repo.git\n"),
        ("git", "rev-parse", "--abbrev-ref", "HEAD"): ok("codex/088-identity\n"),
        ("git", "show-ref", "--verify", "--quiet", "refs/remotes/origin/main"): ok(""),
    })
    result = self.module.inspect_repository_identity(self.root, runner=runner)
    self.assertEqual(result["status"], "mismatch")
    self.assertIn("fetch_remote_mismatch", reason_codes(result))
    self.assertFalse(self.module.operation_decision(result, "execute")["allowed"])
```

- [x] **Step 2: Run the RED slice**

```bash
python3 -m unittest tests.test_project_repository_identity.RepositoryInspectionTests tests.test_project_repository_identity.RepositoryPolicyTests -v
```

Expected: inspection and operation-decision tests fail because those functions are not implemented.

- [x] **Step 3: Implement evidence collection and policy**

Collect all fetch/push lines, resolve local then remote base refs, query the explicit canonical GitHub slug through the injected provider check, and calculate status/capabilities from stable reason codes. Provider evidence is required only for GitHub write/release decisions; provider outage must not become `provider_repository_mismatch`.

- [x] **Step 4: Run the core module tests**

```bash
python3 -m unittest tests.test_project_repository_identity -v
```

Expected: all core tests pass.

### Stream B — Profile And Migration

#### Task 3: Profile Migration And Current-Repo Dogfood

**Files:**
- Modify: `scripts/project_profile.py`
- Modify: `tests/test_project_profile.py`
- Modify: `.moduflow/config.json`
- Modify: `templates/moduflow-config.json`
- Modify: `.moduflow/project-profile.md`
- Modify: `commands/product-profile.md`

- [x] **Step 1: Write failing profile tests**

Cover dry-run proposal from legacy `git.remote`, refusal to adopt without explicit canonical input, remote/local-only writes, invalid lifecycle, idempotent projection update, and preservation of unrelated config keys/profile sections.

- [x] **Step 2: Run profile tests and confirm RED**

```bash
python3 -m unittest tests.test_project_profile -v
```

- [x] **Step 3: Add explicit proposal/write arguments**

Add CLI arguments `--canonical-repository`, `--provider`, `--remote-name-hint`, `--base-branch`, `--lifecycle`, and `--local-only`. Dry-run prints the proposed JSON/profile diff; `--write` applies only explicitly supplied identity values and updates one delimited `Repository Identity` projection block.

- [x] **Step 4: Dogfood canonical ModuFlow identity**

Record `github.com/dongwonlee222/moduflow`, remote hint `origin`, base `main`, and lifecycle `active` in `.moduflow/config.json`; render the same values in `.moduflow/project-profile.md`; update the starter template without real repository credentials.

- [x] **Step 5: Run profile/core tests**

```bash
python3 -m unittest tests.test_project_profile tests.test_project_repository_identity -v
```

Expected: pass and repeated profile write produces no diff.

### Stream C — Read Surfaces

#### Task 4: Doctor And Status Reporting

**Files:**
- Modify: `scripts/project_doctor.py`
- Modify: `scripts/project_sync.py`
- Modify: `tests/test_project_doctor.py`
- Modify: `tests/test_project_sync.py`
- Modify: `commands/product-doctor.md`
- Modify: `commands/product-status.md`
- Modify: `commands/product-sync.md`

- [x] **Step 1: Write failing report-only tests**

Assert doctor and sync output include the full versioned identity result for match, mismatch, unconfigured, and provider-unavailable states; assert neither consumer performs a write or silently substitutes `origin/main` as identity.

- [x] **Step 2: Run doctor/sync tests and confirm RED**

```bash
python3 -m unittest tests.test_project_doctor tests.test_project_sync -v
```

- [x] **Step 3: Integrate the shared inspector**

Add optional runner/provider-check injection to `inspect_project` and `inspect_repo_sync`. Keep existing freshness fields for compatibility, but derive the default remote/base comparison from `expected.remote_name_hint` and `expected.base_branch` when configured.

- [x] **Step 4: Update Korean-first display guidance and rerun tests**

```bash
python3 -m unittest tests.test_project_doctor tests.test_project_sync -v
```

Expected: pass; doctor/status show lifecycle, expected repository/base, observed fetch/push/provider, blocked capabilities, reason codes, and next remediation.

### Stream D — Local Write Gates

#### Task 5: Execute, Commit, And Push Write Boundaries

**Files:**
- Modify: `scripts/project_execution.py`
- Modify: `scripts/project_git_handoff.py`
- Modify: `tests/test_project_execution.py`
- Modify: `tests/test_project_git_handoff.py`
- Modify: `commands/product-execute.md`

- [x] **Step 1: Write failing no-write-on-mismatch tests**

Inject an identity result with `execute`, `commit`, or `push` false and a spy writer/runner. Assert readiness/review artifact writes, `.git` probe writes, staging, commit fallback, and push/API calls are not reached.

- [x] **Step 2: Run execution/handoff tests and confirm RED**

```bash
python3 -m unittest tests.test_project_execution tests.test_project_git_handoff -v
```

- [x] **Step 3: Add immediate pre-write decisions**

Execution evaluates `operation_decision(result, "execute")` before `--write`; commit capability evaluates `commit` before probing `.git`; push handoff evaluates `push` before any push command. Local-only commit remains explicit and never gains push/GitHub/release capabilities.

- [x] **Step 4: Rerun focused tests**

```bash
python3 -m unittest tests.test_project_execution tests.test_project_git_handoff -v
```

Expected: pass and denied results include sanitized identity evidence.

### Stream E — GitHub Write Gates

#### Task 6: GitHub Issue, PR, And Release Gates

**Files:**
- Modify: `scripts/project_github_issues.py`
- Modify: `scripts/project_pr.py`
- Modify: `scripts/release_check.py`
- Create: `tests/test_project_github_issues.py`
- Modify: `tests/test_project_pr.py`
- Modify: `tests/test_validation_distribution.py`
- Modify: `commands/product-pr.md`
- Modify: `commands/product-release.md`

- [x] **Step 1: Write failing explicit-repository tests**

Prove that wrong fetch/push, stale issue/PR URL, provider mismatch, wrong default branch, archive state, fork state, and provider outage block before `_ensure_labels`, `gh issue`, `gh pr`, tag, release, or publish calls. Assert successful GitHub calls always contain `-R dongwonlee222/moduflow` or the explicit API repository path.

- [x] **Step 2: Run the GitHub/release RED slice**

```bash
python3 -m unittest tests.test_project_github_issues tests.test_project_pr tests.test_validation_distribution -v
```

- [x] **Step 3: Replace implicit remote parsing with the shared decision**

Remove `_parse_owner_repo` as an identity source. Derive `owner/repo` only from the canonical identity result after `github_write` or `release` is allowed. Existing artifact URLs may identify an issue/PR number only after their repository matches the canonical slug.

- [x] **Step 4: Rerun focused tests**

```bash
python3 -m unittest tests.test_project_github_issues tests.test_project_pr tests.test_validation_distribution -v
```

Expected: pass and no GitHub write uses current-directory inference.

### Stream F — Artifact Link Audit

#### Task 7: Repository-Bearing Artifact Link Audit

**Files:**
- Modify: `scripts/project_repository_identity.py`
- Modify: `scripts/validate_project_artifacts.py`
- Create: `tests/test_project_repository_links.py`

- [x] **Step 1: Write failing classifier/validation tests**

Create temporary issue/spec/plan/status/review/pr/release artifacts containing canonical URLs, stale URLs, and URLs explicitly marked `mirror` or `reference`. Assert undeclared non-canonical read links warn and non-canonical write-handoff links error.

- [x] **Step 2: Run link tests and confirm RED**

```bash
python3 -m unittest tests.test_project_repository_links -v
```

- [x] **Step 3: Implement one shared link classifier**

Return artifact path, line, sanitized URL, normalized repository, declared role, classification, and write-handoff flag. `validate_project_artifacts.py` consumes this output and never reparses repository URLs.

- [x] **Step 4: Run link and project validation tests**

```bash
python3 -m unittest tests.test_project_repository_links tests.test_validation_distribution -v
python3 scripts/validate_project_artifacts.py .
```

Expected: tests pass and current ModuFlow artifacts have no unsafe repository link errors.

### Stream G — Verification And Handoff

#### Task 8: End-To-End Verification And Review Handoff

**Files:**
- Modify: `specs/088-canonical-repository-remote-identity-gate/tasks.md`
- Create: `specs/088-canonical-repository-remote-identity-gate/status.md`
- Modify: `issues/088-canonical-repository-remote-identity-gate.md`
- Modify: `status.md`
- Modify: `workspace/roadmap.md`

- [x] **Step 1: Run focused identity suites**

```bash
python3 -m unittest tests.test_project_repository_identity tests.test_project_profile tests.test_project_repository_links tests.test_project_doctor tests.test_project_sync tests.test_project_execution tests.test_project_git_handoff tests.test_project_github_issues tests.test_project_pr -v
```

- [x] **Step 2: Run complete validation**

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 scripts/validate_moduflow.py .
python3 scripts/validate_project_artifacts.py .
python3 scripts/release_check.py .
```

Expected: all commands exit 0. If the full suite exposes unrelated pre-existing failures, record exact failing tests and keep 088 open.

- [x] **Step 3: Dogfood operation decisions**

```bash
python3 scripts/project_doctor.py .
python3 scripts/project_repository_identity.py . --operation execute
python3 scripts/project_repository_identity.py . --operation push --provider-check
```

Expected: canonical ModuFlow identity matches, active lifecycle is shown, and execute/push decisions are allowed only with current evidence.

- [x] **Step 4: Record evidence and move to review**

Check completed tasks, write `status.md` with verification output, update the issue lifecycle to review, and set the next command to:

```text
product:review 088-canonical-repository-remote-identity-gate
```

## Parallelism And Merge Order

- Task 1 must land before every other code task because it defines the parser contract.
- Task 2 follows Task 1 and freezes the result/capability schema.
- After Task 2, Task 3 and Task 7 are logically independent, but this session executes inline/sequentially because no subagent delegation was requested.
- Task 4 follows Task 3 so doctor/status can dogfood configured identity.
- Task 5 follows Task 4; it establishes local write boundaries before external GitHub boundaries.
- Task 6 follows Task 5 and reuses the same decision semantics.
- Task 8 runs only after Tasks 1–7.

## Gates

- **Test:** every behavior change has focused tests with injected runners and failure-path assertions.
- **Security:** credential-bearing URLs never survive sanitization; malformed or ambiguous inputs fail closed.
- **Architecture:** consumers import the shared module; repository URL/config parsing is not duplicated.
- **Write boundary:** a mismatch test proves the downstream writer/runner was not called.
- **Human:** canonical identity adoption and lifecycle changes remain explicit human decisions.
- **Release:** current ModuFlow identity passes doctor, artifact validation, full tests, and release check before review completion.
