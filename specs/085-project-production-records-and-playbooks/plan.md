# Project Production Records and Playbooks Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a project-local, validated Production Record and human-approved Playbook workflow that captures recurring production knowledge and retrieves it for future work without changing existing asset locations.

**Architecture:** Add a focused `scripts/project_production.py` domain module rather than enlarging the already broad dashboard/memory renderer. It reuses `project_memory.parse_frontmatter` / `parse_list_value` and `linkage_check.load_human_identities`, owns the only Production Record/Playbook parsers, exposes deterministic init/create/decision/search/validate functions plus a CLI, and is consumed by project validation and the later Issue 086 dashboard. Git Markdown under `memory/production-records/` and `playbooks/` stays canonical.

**Tech Stack:** Python 3 standard library, Markdown + simple YAML-like frontmatter, `unittest`, existing ModuFlow command/skill Markdown, Git-native project artifacts.

Issue: `085-project-production-records-and-playbooks`
Spec: `specs/085-project-production-records-and-playbooks/spec.md`
Prev: spec · Next: `product:execute 085-project-production-records-and-playbooks`

---

## Global Constraints

Constitution v1.0 applies (`workspace/constitution.md`). Plan-specific additions:

1. **Project isolation is structural:** every public function accepts one explicit project root and never scans sibling/portfolio projects.
2. **One parser per artifact:** `project_production.py` owns Production Record/Playbook parsing; validator, search, CLI, and Issue 086 must consume its normalized output.
3. **Human approval is exact:** `approved_by` must equal a configured `.moduflow/humans.json` `name` or `email`; missing/malformed configuration fails approval loudly.
4. **No network validation:** `https` artifact links are accepted syntactically and never fetched; project-relative files are checked locally; absolute local paths warn.
5. **No destructive capture:** initialization creates missing directories/templates only; record creation returns `created`, `update_required`, or `noop`; it never overwrites a populated record.
6. **No silent truncation:** search/retrieval returns `truncated` and `dropped_count` whenever `limit` removes matches.
7. **No dashboard work:** expose normalized collector interfaces for Issue 086, but do not edit dashboard HTML/templates in this issue.
8. **Audit decisions:** approve/reject/defer appends a dated decision to the source record's `Playbook Updates`; rejection/defer never deletes evidence.

## Recommended Discipline

| Stream | Discipline / Adapter | Reason |
| --- | --- | --- |
| A — schema/parser | Superpowers TDD + writing-plans | Parser contracts and section ordering need RED/GREEN fixtures before implementation. |
| B — mutation/approval | Superpowers TDD + ModuFlow Git artifact model | Creation and canonical approval transitions must be idempotent and auditable. |
| C — retrieval | Superpowers TDD + project-memory patterns | Ranking, project isolation, and explicit caps are behavioral contracts. |
| D — validation | ModuFlow artifact validation + verification-before-completion | Broken links and invalid approval must fail the same project gate users already trust. |
| E — command surface | ModuFlow PM router + documentation review | Natural-language routing must reuse memory semantics without creating a competing subsystem. |
| F — dogfood/review | requesting-code-review + verification-before-completion | Two different production types must prove the schema before handoff. |

## Execution Mode

Use sequential subagent-driven development in an issue worktree. Tasks 1–5 all touch or consume `scripts/project_production.py`, so parallel implementation would create merge and contract drift. After Task 5 stabilizes interfaces, Task 6 documentation/distribution can run independently; Task 7 is an independent review/dogfood pass.

Recommended cognitive demand:

- Tasks 1–5: `balanced` implementation workers with focused tests.
- Task 6: `fast` documentation/package worker after interfaces are frozen.
- Task 7: independent `deep` spec/quality reviewer; coordinator retains final acceptance and user communication.

## File Structure

### Create

- `scripts/project_production.py` — canonical Production Record/Playbook parser, initializer, record creation, approval decisions, search/retrieval, validation, and CLI.
- `templates/production/record.md` — complete Production Record frontmatter and nine-section body.
- `templates/production/playbook.md` — candidate/approved Playbook frontmatter and six-section body.
- `commands/product-production.md` — natural-language/CLI workflow for init, capture, search, and human-gated playbook decisions.
- `tests/test_project_production.py` — focused domain, CLI, project-isolation, and validation integration tests.
- `tests/fixtures/production-project/` — two production records, one approved playbook, source issues, humans config, and linked sample assets.

### Modify

- `scripts/validate_project_artifacts.py` — call the canonical production validator and merge its errors/warnings.
- `scripts/validate_moduflow.py` — require the new command, templates, and script in the distributed package.
- `tests/test_validation_distribution.py` — assert the new production surface is required.
- `commands/product-memory.md` — explain Production Records/Playbooks as the structured recurring-production path.
- `skills/index/SKILL.md` — add `production`, `제작 기록`, and `플레이북` aliases.
- `skills/pm-execution-router/SKILL.md` — route recurring-production capture/retrieval to `product:production`.
- `README.md` — add the optional production-memory command to the on-demand command surface.
- `issues/085-project-production-records-and-playbooks.md` — track plan/execute/review tasks.
- `specs/085-project-production-records-and-playbooks/status.md` — implementation evidence and next command.
- `workspace/roadmap.md`, `workspace/dashboard.md`, `workspace/loop-state.json`, `.moduflow/state.json` — lifecycle projection.

## Interfaces

`scripts/project_production.py` exports these stable interfaces for this issue and Issue 086:

| Function | Inputs | Output |
| --- | --- | --- |
| `build_production_plan` | `project_root`, `dry_run=True` | plan dict with schema, writes, preservation flag |
| `apply_production_plan` | plan dict | same dict plus exact `written` paths |
| `parse_production_record` | `project_root`, record path | normalized record dict below; raises `ValueError` on malformed canonical content |
| `parse_playbook` | `project_root`, playbook path | normalized playbook dict with approval and source state |
| `list_production_records` | `project_root` | stable path-sorted normalized record list |
| `list_playbooks` | `project_root` | stable path-sorted normalized playbook list |
| `create_production_record` | project root plus title, issue/source context, type, channel, audiences, lifecycle, retrieval trigger, owner, variant | `created`, `update_required`, or `noop` result dict |
| `decide_playbook_update` | project root, record ID, playbook ID, `approve/reject/defer`, named human, reason, date | audited decision result dict; approval also returns playbook status/path |
| `search_production` | project root, query, structured filters, positive limit | bounded result envelope below |
| `retrieve_production_context` | project root, type, channel, audiences, positive limit | approved-first bounded result envelope below |
| `validate_production_project` | `project_root` | `errors` / `warnings` envelope below |
| `main` | optional argv list | CLI exit code (`0` success, `2` usage, `1` validation/mutation failure) |

Normalized record shape consumed by search/validator/086:

```python
{
    "id": "2026-07-10-summer-banner",
    "kind": "production_record",
    "title": "Summer banner",
    "path": "memory/production-records/2026-07-10-summer-banner.md",
    "issue_id": "123-summer-event",
    "deliverable_type": "banner",
    "channel": "home-popup",
    "audiences": ["customer", "internal"],
    "variant": "mobile",
    "lifecycle": "published",
    "owner": "marketing",
    "created": "2026-07-10",
    "updated": "2026-07-10",
    "playbook_refs": ["banner-mobile"],
    "retrieval_trigger": "when creating a mobile banner",
    "sections": {
        "Artifacts": "- [Final](marketing/banner.png) — final · customer",
        "External Copy": "Charge now to receive the event benefit.",
        "Internal Reporting Copy": "This variant tests mobile conversion.",
    },
    "artifacts": [{"label": "Final", "target": "marketing/banner.png",
                   "variant": "final", "audience": "customer"}],
    "playbook_updates": [{"playbook_id": "banner-mobile", "state": "candidate"}],
}
```

Validation interface:

```python
{"errors": ["relative/path.md: message"], "warnings": ["relative/path.md: message"]}
```

Search/retrieval interface:

```python
{"items": [{"id": "banner-mobile", "kind": "playbook", "authoritative": True}],
 "truncated": False, "dropped_count": 0, "total_matches": 1}
```

## Implementation Readiness Inputs

- **API contract mapping:** Not applicable. This is a local Python CLI/module and Markdown artifact contract; no HTTP API or external provider calls.
- **Test strategy:** `tests/test_project_production.py` proves parser normalization, required sections, artifact links, init preservation, duplicate handling, approval identity, decision audit, retrieval ranking/caps, and project isolation. Existing validation/distribution suites prove integration and packaging.
- **Storybook required states:** Not applicable; Issue 085 has no frontend.
- **MSW fixture baseline:** Not applicable; no API-backed UI.
- **Playwright smoke matrix:** Not applicable; dashboard UI belongs to Issue 086.
- **Permission/role model:** Human approval resolves exact configured `name`/`email` from `.moduflow/humans.json`; no configured identity means approval is impossible, never a pass.
- **Release condition:** Focused tests, full unit suite, package/project validation, spec consistency, and release check pass; two fixture records and one approved playbook parse and search correctly.
- **Rollback:** Revert Issue 085 commits. Project-created `memory/production-records/` and `playbooks/` Markdown remain readable data; removing the optional command/parser does not alter existing assets or legacy memory.

---

### Stream A — Canonical data model

#### Task 1: Canonical schema parser and templates

**Files:**

- Create: `scripts/project_production.py`
- Create: `templates/production/record.md`
- Create: `templates/production/playbook.md`
- Create: `tests/test_project_production.py`

**Interfaces produced:** `parse_production_record`, `parse_playbook`, `list_production_records`, `list_playbooks`, schema/section constants.

- [ ] **Step 1: Write failing parser tests**

Add tests that create one valid record and playbook and assert normalized fields, section preservation, artifact parsing, and external/internal separation:

```python
def test_parse_record_normalizes_metadata_sections_and_artifacts(self):
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_project(root)
        path = write_record(root, VALID_RECORD)

        record = production.parse_production_record(root, path)

        self.assertEqual(record["deliverable_type"], "banner")
        self.assertEqual(record["audiences"], ["customer", "internal"])
        self.assertEqual(record["variant"], "mobile")
        self.assertEqual(record["artifacts"][0]["target"], "marketing/banner-final.png")
        self.assertNotEqual(record["sections"]["External Copy"],
                            record["sections"]["Internal Reporting Copy"])

def test_parse_record_requires_nine_sections_in_order(self):
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_project(root)
        path = write_record(root, VALID_RECORD.replace("## Failed Attempts\n", ""))

        with self.assertRaisesRegex(ValueError, "missing section: Failed Attempts"):
            production.parse_production_record(root, path)
```

- [ ] **Step 2: Run tests and confirm RED**

Run: `python3 -m unittest tests.test_project_production.ProjectProductionParserTests -v`

Expected: import/file failure because `scripts/project_production.py` does not exist.

- [ ] **Step 3: Add exact templates**

`templates/production/record.md` must contain the required frontmatter and all nine headings in the spec order. `templates/production/playbook.md` must contain candidate-safe metadata (`status: candidate`, empty approval fields) and `Reusable Patterns`, `Do Not Repeat`, `Approved Copy Blocks`, `Approved Structures`, `Evidence`, `Revision History`.

- [ ] **Step 4: Implement the minimal parser**

Start `project_production.py` with shared parsing and deterministic section extraction:

```python
from pathlib import Path
import project_memory

RECORD_SCHEMA = "moduflow.production-record.v1"
PLAYBOOK_SCHEMA = "moduflow.playbook.v1"
RECORD_SECTIONS = (
    "Artifacts", "Source Inputs", "Decisions", "Failed Attempts",
    "Reusable Patterns", "Do Not Repeat", "Playbook Updates",
    "External Copy", "Internal Reporting Copy",
)
PLAYBOOK_SECTIONS = (
    "Reusable Patterns", "Do Not Repeat", "Approved Copy Blocks",
    "Approved Structures", "Evidence", "Revision History",
)

def _sections(body, required):
    positions = []
    lines = body.splitlines()
    for name in required:
        marker = f"## {name}"
        matches = [i for i, line in enumerate(lines) if line.strip() == marker]
        if not matches:
            raise ValueError(f"missing section: {name}")
        positions.append(matches[0])
    if positions != sorted(positions):
        raise ValueError("required sections are out of order")
    result = {}
    for index, name in enumerate(required):
        start = positions[index] + 1
        end = positions[index + 1] if index + 1 < len(positions) else len(lines)
        result[name] = "\n".join(lines[start:end]).strip()
    return result
```

Parse inline lists with `project_memory.parse_list_value`; normalize slugs with `project_memory.slugify`. Parse artifact lines with one compiled regex accepting Markdown link + `— variant · audience`.

- [ ] **Step 5: Run parser tests and confirm GREEN**

Run: `python3 -m unittest tests.test_project_production.ProjectProductionParserTests -v`

Expected: all parser tests pass.

- [ ] **Step 6: Commit Task 1**

```bash
git add scripts/project_production.py templates/production tests/test_project_production.py
git commit -m "feat: add production record and playbook parsers" -m "Issue: 085-project-production-records-and-playbooks"
```

---

#### Task 2: Initialization, record creation, and duplicate-safe capture

**Files:**

- Modify: `scripts/project_production.py`
- Modify: `tests/test_project_production.py`

**Consumes:** Task 1 templates/parsers.  
**Produces:** `build_production_plan`, `apply_production_plan`, `create_production_record`, CLI `--init`/`--new-record`.

- [ ] **Step 1: Write failing init/create tests**

```python
def test_init_creates_only_missing_production_paths(self):
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        existing = root / "marketing" / "keep.txt"
        existing.parent.mkdir(parents=True)
        existing.write_text("keep", encoding="utf-8")

        result = production.apply_production_plan(
            production.build_production_plan(root, dry_run=False)
        )

        self.assertTrue((root / "memory/production-records").is_dir())
        self.assertTrue((root / "playbooks").is_dir())
        self.assertEqual(existing.read_text(encoding="utf-8"), "keep")
        self.assertNotIn("marketing/keep.txt", result["written"])

def test_same_capture_key_returns_update_required_without_overwrite(self):
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_project(root)
        first = production.create_production_record(
            root, title="Summer banner", issue_id="123-summer-event",
            deliverable_type="banner", channel="home-popup",
            audiences=["customer"], lifecycle="draft",
            retrieval_trigger="when creating mobile banners", variant="mobile",
        )
        path = root / first["path"]
        path.write_text(path.read_text(encoding="utf-8") + "\nHuman note\n", encoding="utf-8")

        second = production.create_production_record(
            root, title="Summer banner", issue_id="123-summer-event",
            deliverable_type="banner", channel="home-popup",
            audiences=["customer"], lifecycle="draft",
            retrieval_trigger="when creating mobile banners", variant="mobile",
        )

        self.assertEqual(second["action"], "update_required")
        self.assertIn("Human note", path.read_text(encoding="utf-8"))
```

- [ ] **Step 2: Run tests and confirm RED**

Run: `python3 -m unittest tests.test_project_production.ProjectProductionMutationTests -v`

Expected: failures for missing init/create functions.

- [ ] **Step 3: Implement init and duplicate key**

Use `memory/production-records` and `playbooks` as the only created directories. Define the capture key as normalized `(issue_id or source_context, deliverable_type, channel, variant, title)` and scan parsed records before writing. Return:

```python
{"action": "created", "id": record_id, "path": relative_path}
{"action": "update_required", "id": existing_id, "path": existing_path}
{"action": "noop", "id": existing_id, "path": existing_path}
```

`noop` is returned only when the generated untouched template is byte-for-byte equal; populated existing records return `update_required`.

- [ ] **Step 4: Add testable CLI**

Implement `main(argv=None)` with mutually exclusive `--init`, `--new-record`, `--search`, `--retrieve`, `--validate`, and `--decide-playbook` operations. `--new-record` requires title, type, channel, audience, lifecycle, and retrieval trigger; requires `--issue-id` or `--source-context`.

- [ ] **Step 5: Run mutation and CLI tests**

Run: `python3 -m unittest tests.test_project_production.ProjectProductionMutationTests tests.test_project_production.ProjectProductionCliTests -v`

Expected: all pass; repeated CLI capture does not overwrite.

- [ ] **Step 6: Commit Task 2**

```bash
git add scripts/project_production.py tests/test_project_production.py
git commit -m "feat: add duplicate-safe production capture" -m "Issue: 085-project-production-records-and-playbooks"
```

---

### Stream B — Human-gated Playbooks

#### Task 3: Human-gated Playbook decisions and audit trail

**Files:**

- Modify: `scripts/project_production.py`
- Modify: `tests/test_project_production.py`

**Consumes:** parsed record/playbook objects and `.moduflow/humans.json`.  
**Produces:** `decide_playbook_update` with approve/reject/defer behavior.

- [ ] **Step 1: Write failing approval tests**

```python
def test_approve_requires_exact_configured_human_and_source_record(self):
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_project(root, humans=[{"name": "Dongwon Lee", "email": "webn77@gmail.com"}])
        record = write_record(root, VALID_RECORD)
        write_playbook(root, CANDIDATE_PLAYBOOK)

        with self.assertRaisesRegex(ValueError, "configured human"):
            production.decide_playbook_update(
                root, record_id=record.stem, playbook_id="banner-mobile",
                decision="approve", approved_by="agent", reason="looks good",
                decided_at="2026-07-10",
            )

        result = production.decide_playbook_update(
            root, record_id="2026-07-10-summer-banner",
            playbook_id="banner-mobile", decision="approve",
            approved_by="Dongwon Lee", reason="validated on mobile",
            decided_at="2026-07-10",
        )
        self.assertEqual(result["status"], "approved")

def test_reject_and_defer_append_record_without_deleting_candidate(self):
    # Assert both decisions append one dated line under Playbook Updates,
    # leave the playbook file present, and never set status: approved.
```

- [ ] **Step 2: Run tests and confirm RED**

Run: `python3 -m unittest tests.test_project_production.ProjectProductionApprovalTests -v`

Expected: missing decision function.

- [ ] **Step 3: Implement identity and decision helpers**

Reuse `linkage_check.load_human_identities(root)`. Accept only exact non-empty `name` or `email` values:

```python
def _configured_human_values(root):
    values = set()
    for identity in linkage_check.load_human_identities(root):
        if isinstance(identity, dict):
            values.update(v for v in (identity.get("name"), identity.get("email")) if v)
    return values
```

Approval must also confirm the source record ID exists and is listed in `source_records`. Update frontmatter deterministically, append one revision-history line, and append one decision line to the source record. Reject/defer changes only the source record audit line and candidate status when explicitly represented; no deletion.

- [ ] **Step 4: Prove idempotency and loud failures**

Add tests for missing/malformed humans config, missing source record, duplicate identical approval (`noop`), and conflicting second approver (error unless a new revision is created).

- [ ] **Step 5: Run approval tests**

Run: `python3 -m unittest tests.test_project_production.ProjectProductionApprovalTests -v`

Expected: all pass.

- [ ] **Step 6: Commit Task 3**

```bash
git add scripts/project_production.py tests/test_project_production.py
git commit -m "feat: gate production playbooks on human approval" -m "Issue: 085-project-production-records-and-playbooks"
```

---

### Stream C — Reuse

#### Task 4: Project-local search and bounded retrieval

**Files:**

- Modify: `scripts/project_production.py`
- Modify: `tests/test_project_production.py`

**Consumes:** normalized records/playbooks.  
**Produces:** `search_production`, `retrieve_production_context`, stable payload for Issue 086.

- [ ] **Step 1: Write failing search/isolation tests**

```python
def test_search_filters_failures_patterns_and_audience_with_explicit_cap(self):
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_project(root)
        write_record(root, VALID_RECORD)
        write_record(root, PRESS_RECORD)

        result = production.search_production(
            root, "small Korean text", deliverable_type="banner",
            audience="customer", limit=1,
        )

        self.assertEqual(result["items"][0]["deliverable_type"], "banner")
        self.assertEqual(result["total_matches"], 1)
        self.assertFalse(result["truncated"])

def test_retrieval_never_reads_sibling_project(self):
    with tempfile.TemporaryDirectory() as tmp:
        parent = Path(tmp)
        project_a, project_b = parent / "a", parent / "b"
        write_project(project_a); write_project(project_b)
        write_record(project_a, VALID_RECORD)
        write_record(project_b, PRESS_RECORD)

        result = production.retrieve_production_context(
            project_a, deliverable_type="press-release",
            channel="media", audiences=["journalist"], limit=5,
        )
        self.assertEqual(result["items"], [])
```

- [ ] **Step 2: Run tests and confirm RED**

Run: `python3 -m unittest tests.test_project_production.ProjectProductionSearchTests -v`

- [ ] **Step 3: Implement deterministic ranking**

Search all record text fields but filter structured dimensions exactly after slug normalization. Retrieval score is additive and stable: approved exact-scope playbook `+100`; type `+20`; channel `+10`; each audience match `+5`; newer record tie-breaks by `updated` descending then ID ascending. Return `truncated`, `dropped_count`, and `total_matches` after sorting, never during iteration.

- [ ] **Step 4: Add cap/project-isolation regression cases**

Cover zero/negative limit rejection, a two-match `limit=1` response with `truncated=True`, no cross-root reads, candidate playbooks excluded from authoritative results, and fallback records labeled `authoritative=False`.

- [ ] **Step 5: Run search tests**

Run: `python3 -m unittest tests.test_project_production.ProjectProductionSearchTests -v`

Expected: all pass.

- [ ] **Step 6: Commit Task 4**

```bash
git add scripts/project_production.py tests/test_project_production.py
git commit -m "feat: add project-local production retrieval" -m "Issue: 085-project-production-records-and-playbooks"
```

---

### Stream D — Trust gates

#### Task 5: Project validation integration

**Files:**

- Modify: `scripts/project_production.py`
- Modify: `scripts/validate_project_artifacts.py`
- Modify: `tests/test_project_production.py`

**Consumes:** canonical Production Record/Playbook parser.  
**Produces:** hard errors and soft warnings in the existing project validation result.

- [ ] **Step 1: Write failing validation tests**

```python
def test_validation_errors_on_missing_relative_artifact_and_invalid_approval(self):
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_minimal_moduflow_project(root)
        write_record(root, VALID_RECORD.replace("marketing/banner-final.png",
                                                "marketing/missing.png"))
        write_playbook(root, APPROVED_PLAYBOOK.replace("Dongwon Lee", "agent"))

        result = validator.validate_project(root)

        self.assertFalse(result["valid"])
        self.assertTrue(any("missing artifact" in e for e in result["errors"]))
        self.assertTrue(any("approved_by" in e for e in result["errors"]))

def test_validation_accepts_https_without_network_and_warns_absolute_path(self):
    # No HTTP mock is needed because validator must never perform network I/O.
    # Assert https produces no error and /Users/example/file.png produces warning.
```

- [ ] **Step 2: Run tests and confirm RED**

Run: `python3 -m unittest tests.test_project_production.ProjectProductionValidationTests -v`

- [ ] **Step 3: Implement `validate_production_project`**

Validate required metadata/sections, lifecycle, duplicate IDs/capture keys, issue/context source, artifact targets, playbook/source refs, approval identity/date, stale review date, and weak/empty learning signals. Catch read/parser failures and report the relative file; never silently skip.

- [ ] **Step 4: Integrate the canonical validator**

At module load in `validate_project_artifacts.py`, import `project_production` via the same scripts-directory import path used elsewhere. In `validate_project`, merge:

```python
production = project_production.validate_production_project(root)
errors.extend(production["errors"])
warnings.extend(production["warnings"])
```

No Production Record/Playbook paths means a clean optional no-op, preserving lightweight projects.

- [ ] **Step 5: Run focused and existing validation tests**

Run:

```bash
python3 -m unittest tests.test_project_production.ProjectProductionValidationTests -v
python3 -m unittest tests.test_validation_distribution -v
python3 -m unittest tests.test_project_memory -v
```

Expected: all pass; lightweight projects remain valid.

- [ ] **Step 6: Commit Task 5**

```bash
git add scripts/project_production.py scripts/validate_project_artifacts.py tests/test_project_production.py
git commit -m "feat: validate project production knowledge" -m "Issue: 085-project-production-records-and-playbooks"
```

---

### Stream E — Product surface

#### Task 6: Command routing and package distribution

**Files:**

- Create: `commands/product-production.md`
- Modify: `commands/product-memory.md`
- Modify: `skills/index/SKILL.md`
- Modify: `skills/pm-execution-router/SKILL.md`
- Modify: `README.md`
- Modify: `scripts/validate_moduflow.py`
- Modify: `tests/test_validation_distribution.py`

**Consumes:** frozen CLI/interfaces from Tasks 1–5.  
**Produces:** user-facing entry point and install/package completeness.

- [ ] **Step 1: Write the distribution test first**

```python
def test_validate_moduflow_requires_production_knowledge_surface(self):
    validator = load_module("validate_moduflow", "scripts/validate_moduflow.py")
    expected = {
        "commands/product-production.md",
        "scripts/project_production.py",
        "templates/production/record.md",
        "templates/production/playbook.md",
    }
    self.assertTrue(expected.issubset(set(validator.REQUIRED_FILES)))
```

- [ ] **Step 2: Run and confirm RED**

Run: `python3 -m unittest tests.test_validation_distribution.ValidationDistributionTests.test_validate_moduflow_requires_production_knowledge_surface -v`

- [ ] **Step 3: Add the command contract**

`commands/product-production.md` must show:

- initialize optional project paths;
- create/open a record from natural language without moving artifacts;
- list/search/retrieve by type/channel/audience;
- show playbook candidates;
- require explicit named human for approve/reject/defer;
- explain `created` / `update_required` / `noop`;
- end with a concrete example such as `product:production --search "mobile banner" --type banner --channel home-popup` or the source issue's exact next command.

- [ ] **Step 4: Wire routing without duplicating logic**

Add aliases `production`, `제작 기록`, `제작지식`, `플레이북`, and recurring-work examples to `skills/index` and `pm-execution-router`. `product:memory` links to the focused command for structured recurring-production knowledge; it retains generic memory ownership.

- [ ] **Step 5: Add package requirements and README entry**

Add the four new required files to `validate_moduflow.REQUIRED_FILES` and document `product:production` under on-demand workflows, not the three-command onboarding core.

- [ ] **Step 6: Run docs/package checks**

Run:

```bash
python3 -m unittest tests.test_validation_distribution -v
python3 scripts/validate_moduflow.py .
```

Expected: valid package, focused distribution test green.

- [ ] **Step 7: Commit Task 6**

```bash
git add commands/product-production.md commands/product-memory.md skills/index/SKILL.md skills/pm-execution-router/SKILL.md README.md scripts/validate_moduflow.py tests/test_validation_distribution.py
git commit -m "docs: expose production knowledge workflow" -m "Issue: 085-project-production-records-and-playbooks"
```

---

### Stream F — Dogfood and review

#### Task 7: Dogfood fixtures, end-to-end verification, and handoff

**Files:**

- Create: `tests/fixtures/production-project/.moduflow/humans.json`
- Create: `tests/fixtures/production-project/issues/001-summer-banner.md`
- Create: `tests/fixtures/production-project/issues/002-partnership-press-release.md`
- Create: `tests/fixtures/production-project/assets/banner-final.svg`
- Create: `tests/fixtures/production-project/documents/press-release-final.md`
- Create: `tests/fixtures/production-project/memory/production-records/2026-07-10-summer-banner.md`
- Create: `tests/fixtures/production-project/memory/production-records/2026-07-10-partnership-press-release.md`
- Create: `tests/fixtures/production-project/playbooks/banner-mobile.md`
- Modify: `tests/test_project_production.py`
- Modify: `issues/085-project-production-records-and-playbooks.md`
- Create: `specs/085-project-production-records-and-playbooks/status.md`
- Modify: `workspace/roadmap.md`
- Modify: `workspace/dashboard.md`
- Modify: `workspace/loop-state.json`
- Modify: `.moduflow/state.json`

**Consumes:** complete production module/CLI.  
**Produces:** two-channel proof, implementation evidence, and Issue 086-ready data contract.

- [ ] **Step 1: Create complete dogfood fixtures**

The banner record must include the observed mobile text/character consistency failures and external/internal copy separation. The press-release record must include headline/lead/company-description/quote patterns and advertising-tone failures. The approved banner playbook must cite the banner record and use `approved_by: Dongwon Lee` matching fixture `humans.json`.

- [ ] **Step 2: Add one end-to-end fixture test**

```python
def test_dogfood_project_validates_searches_and_retrieves(self):
    root = ROOT / "tests/fixtures/production-project"

    validation = production.validate_production_project(root)
    search = production.search_production(root, "small Korean text", limit=20)
    context = production.retrieve_production_context(
        root, deliverable_type="banner", channel="home-popup",
        audiences=["customer"], limit=5,
    )

    self.assertEqual(validation["errors"], [])
    self.assertEqual(len(search["items"]), 1)
    self.assertEqual(context["items"][0]["kind"], "playbook")
    self.assertTrue(context["items"][0]["authoritative"])
```

- [ ] **Step 3: Run the complete focused suite**

Run: `python3 -m unittest tests.test_project_production -v`

Expected: all production tests pass.

- [ ] **Step 4: Run full readiness gates**

Run:

```bash
python3 scripts/spec_consistency.py . --issue-id 085-project-production-records-and-playbooks
python3 -m unittest discover -s tests -v
python3 scripts/validate_moduflow.py .
python3 scripts/validate_project_artifacts.py .
python3 scripts/release_check.py .
git diff --check
```

Expected: no spec-consistency errors/warnings; all tests and validators pass; no whitespace errors.

- [ ] **Step 5: Request independent review**

Review against the spec with explicit attention to project isolation, approval identity, no-network validation, update/no-op preservation, internal/external separation, and Issue 086 interface stability. Record every finding in `status.md`; do not suppress coordinator-disputed findings.

- [ ] **Step 6: Update lifecycle artifacts**

Check execute/review tasks only after evidence exists. Before independent review completes, set the issue next command to `product:review 085-project-production-records-and-playbooks`; after an approved review, set it to `product:pr 085-project-production-records-and-playbooks`. Update dashboard/roadmap/loop-state through normal ModuFlow lifecycle rules.

- [ ] **Step 7: Commit Task 7**

```bash
git add tests/fixtures/production-project tests/test_project_production.py issues/085-project-production-records-and-playbooks.md specs/085-project-production-records-and-playbooks/status.md workspace/dashboard.md workspace/roadmap.md workspace/loop-state.json .moduflow/state.json
git commit -m "test: dogfood project production knowledge" -m "Issue: 085-project-production-records-and-playbooks"
```

## Self-Review

- **Spec coverage:** Tasks 1–7 cover initialization, one canonical parser, nine record sections, artifact links, external/internal copy, human-gated Playbooks, auditable decisions, search/retrieval, explicit caps, project isolation, compatibility, dogfood, validation, command routing, and distribution.
- **Scope check:** No Issue 086 dashboard UI, no network access, no asset migration, and no central database work is included.
- **Placeholder scan:** No TBD/TODO/similar-task references remain; code-changing steps include exact interfaces, tests, commands, and expected outcomes.
- **Type consistency:** `project_root`, record/playbook normalized dictionaries, `items/truncated/dropped_count/total_matches`, and exact `approved_by` values are consistent across tasks.
- **Dependency order:** Task 1 → Task 2 → Task 3 → Task 4 → Task 5; Task 6 after interfaces freeze; Task 7 after all behavior/doc tasks.
