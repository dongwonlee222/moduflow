# Memory Capture And Sync Workflow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local-first memory candidate, approval, retrieval, validation, and export-documentation workflow for ModuFlow while keeping Git-tracked Markdown as the canonical source.

**Architecture:** Extend the existing `scripts/project_memory.py` CLI in place with small pure functions for candidate creation, candidate listing, approval, enriched search, and export guidance. Keep memory entries and candidates as Markdown files so downloaded ModuFlow users need no hosted service. Add validation in `scripts/validate_project_artifacts.py` for broken memory links and candidate structure, then document PM/team usage in command docs.

**Tech Stack:** Python standard library, Markdown files with frontmatter, `unittest`, existing ModuFlow scripts and command docs.

---

## File Structure

- Modify: `scripts/project_memory.py`
  - Add `memory/.candidates` initialization.
  - Add candidate file creation and approval.
  - Extend memory entry frontmatter with source artifact, source event, supersede, review, storage, and mirror fields.
  - Add search match reasons and linked artifact metadata.
  - Add export guidance output.
- Modify: `tests/test_project_memory.py`
  - Add TDD coverage for candidate lifecycle, enriched entry fields, match reasons, and export guidance.
- Modify: `scripts/validate_project_artifacts.py`
  - Validate memory entry/candidate links that point to project-local artifacts.
  - Validate candidate files include approval status.
- Modify: `commands/product-memory.md`
  - Replace low-level-only examples with PM-friendly capture, candidate, approve, search, and export examples.
- Modify: `templates/memory/entry.md`
  - Add new frontmatter fields.
- Modify: `specs/034-memory-capture-and-sync-workflow/status.md`
  - Track implementation progress and verification.
- Modify: `issues/034-memory-capture-and-sync-workflow.md`
  - Check off plan and later implementation tasks.

## Task 1: Initialize Candidate Storage

**Files:**
- Modify: `scripts/project_memory.py`
- Modify: `tests/test_project_memory.py`

- [ ] **Step 1: Write failing test for candidate directory initialization**

Add this test method to `ProjectMemoryTests` in `tests/test_project_memory.py`:

```python
    def test_memory_write_creates_candidate_directory(self):
        project_memory = load_module("project_memory", "scripts/project_memory.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            plan = project_memory.build_memory_plan(root, dry_run=False)
            result = project_memory.apply_memory_plan(plan)

            self.assertIn("memory/.candidates", result["written"])
            self.assertTrue((root / "memory" / ".candidates").is_dir())
```

- [ ] **Step 2: Run focused test and verify it fails**

Run:

```bash
python3 -m unittest tests.test_project_memory.ProjectMemoryTests.test_memory_write_creates_candidate_directory -v
```

Expected: FAIL because `memory/.candidates` is not created or reported.

- [ ] **Step 3: Add candidate directory to memory structure**

In `scripts/project_memory.py`, update `MEMORY_DIRS`:

```python
MEMORY_DIRS = [
    "memory/.candidates",
    "memory/deliverables",
    "memory/decisions",
    "memory/evidence",
    "memory/meetings",
    "memory/releases",
    "memory/notes",
    "memory/references",
]
```

- [ ] **Step 4: Run focused test and verify it passes**

Run:

```bash
python3 -m unittest tests.test_project_memory.ProjectMemoryTests.test_memory_write_creates_candidate_directory -v
```

Expected: PASS.

- [ ] **Step 5: Run existing project memory tests**

Run:

```bash
python3 -m unittest tests.test_project_memory -v
```

Expected: PASS.

## Task 2: Extend Memory Entry Schema

**Files:**
- Modify: `scripts/project_memory.py`
- Modify: `templates/memory/entry.md`
- Modify: `tests/test_project_memory.py`

- [ ] **Step 1: Write failing test for extended metadata fields**

Add this test method:

```python
    def test_create_memory_entry_records_source_and_review_fields(self):
        project_memory = load_module("project_memory", "scripts/project_memory.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "specs" / "034-memory-capture-and-sync-workflow").mkdir(parents=True)
            (root / "specs" / "034-memory-capture-and-sync-workflow" / "spec.md").write_text(
                "# Spec\n", encoding="utf-8"
            )

            entry = project_memory.create_memory_entry(
                root,
                kind="decision",
                title="Use Git canonical memory",
                issue_id="034-memory-capture-and-sync-workflow",
                spec_path="specs/034-memory-capture-and-sync-workflow/spec.md",
                summary="Keep memory canonical in Git-tracked Markdown.",
                source_event="decision-approved",
                source_artifacts=["specs/034-memory-capture-and-sync-workflow/spec.md"],
                review_after="2026-07-26",
                supersedes=["2026-06-24-use-portable-project-memory"],
                storage_policy="team",
                mirror_targets=["google-drive", "obsidian"],
                tags=["memory", "team"],
            )

            content = (root / entry["path"]).read_text(encoding="utf-8")
            self.assertIn("source_event: decision-approved", content)
            self.assertIn("source_artifacts: [specs/034-memory-capture-and-sync-workflow/spec.md]", content)
            self.assertIn("review_after: 2026-07-26", content)
            self.assertIn("supersedes: [2026-06-24-use-portable-project-memory]", content)
            self.assertIn("storage_policy: team", content)
            self.assertIn("mirror_targets: [google-drive, obsidian]", content)
```

- [ ] **Step 2: Run focused test and verify it fails**

Run:

```bash
python3 -m unittest tests.test_project_memory.ProjectMemoryTests.test_create_memory_entry_records_source_and_review_fields -v
```

Expected: FAIL with unexpected keyword arguments.

- [ ] **Step 3: Extend helper and entry body signatures**

In `scripts/project_memory.py`, update `entry_body()` and `create_memory_entry()` signatures to accept:

```python
    source_event="",
    source_artifacts=None,
    review_after="",
    supersedes=None,
    superseded_by=None,
    storage_policy="local",
    mirror_targets=None,
```

- [ ] **Step 4: Add frontmatter fields to generated entries**

In the `entry_body()` frontmatter, add these lines after `spec`:

```python
source_event: {frontmatter_value(source_event)}
source_artifacts: {format_list(source_artifacts or [])}
review_after: {frontmatter_value(review_after)}
supersedes: {format_list(supersedes or [])}
superseded_by: {format_list(superseded_by or [])}
storage_policy: {frontmatter_value(storage_policy)}
mirror_targets: {format_list(mirror_targets or [])}
```

- [ ] **Step 5: Pass fields from create function to entry body**

Inside `create_memory_entry()`, pass the new arguments through:

```python
            source_event=source_event,
            source_artifacts=source_artifacts or [],
            review_after=review_after,
            supersedes=supersedes or [],
            superseded_by=superseded_by or [],
            storage_policy=storage_policy,
            mirror_targets=mirror_targets or [],
```

- [ ] **Step 6: Update the entry template**

In `templates/memory/entry.md`, add:

```markdown
source_event: {{source_event}}
source_artifacts: {{source_artifacts}}
review_after: {{review_after}}
supersedes: {{supersedes}}
superseded_by: {{superseded_by}}
storage_policy: {{storage_policy}}
mirror_targets: {{mirror_targets}}
```

- [ ] **Step 7: Run focused and full memory tests**

Run:

```bash
python3 -m unittest tests.test_project_memory.ProjectMemoryTests.test_create_memory_entry_records_source_and_review_fields -v
python3 -m unittest tests.test_project_memory -v
```

Expected: PASS.

## Task 3: Add Memory Candidate Creation

**Files:**
- Modify: `scripts/project_memory.py`
- Modify: `tests/test_project_memory.py`

- [ ] **Step 1: Write failing test for candidate creation**

Add this test:

```python
    def test_create_memory_candidate_writes_reviewable_candidate(self):
        project_memory = load_module("project_memory", "scripts/project_memory.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            candidate = project_memory.create_memory_candidate(
                root,
                kind="decision",
                title="Use Git canonical memory",
                issue_id="034-memory-capture-and-sync-workflow",
                summary="Keep memory canonical in Git-tracked Markdown.",
                source_event="decision-detected",
                source_artifacts=["specs/034-memory-capture-and-sync-workflow/spec.md"],
                tags=["memory", "team"],
            )

            candidate_path = root / candidate["path"]
            content = candidate_path.read_text(encoding="utf-8")
            self.assertEqual(candidate["status"], "candidate")
            self.assertTrue(candidate["path"].startswith("memory/.candidates/"))
            self.assertIn("status: candidate", content)
            self.assertIn("kind: decision", content)
            self.assertIn("source_event: decision-detected", content)
```

- [ ] **Step 2: Run focused test and verify it fails**

Run:

```bash
python3 -m unittest tests.test_project_memory.ProjectMemoryTests.test_create_memory_candidate_writes_reviewable_candidate -v
```

Expected: FAIL because `create_memory_candidate` does not exist.

- [ ] **Step 3: Add candidate body helper**

Add this function below `entry_body()`:

```python
def candidate_body(**kwargs):
    body = entry_body(**kwargs)
    return body.replace(
        f"id: {kwargs['entry_id']}\n",
        f"id: {kwargs['entry_id']}\nstatus: candidate\n",
        1,
    )
```

- [ ] **Step 4: Add `create_memory_candidate()` implementation**

Add this function near `create_memory_entry()`:

```python
def create_memory_candidate(
    path,
    kind,
    title,
    issue_id="",
    spec_path="",
    summary="",
    rationale="",
    evidence="",
    alternatives="",
    owner="",
    reversal_conditions="",
    source_event="",
    source_artifacts=None,
    review_after="",
    supersedes=None,
    storage_policy="local",
    mirror_targets=None,
    tags=None,
):
    if kind not in KIND_TO_DIR:
        raise ValueError(f"Unsupported memory kind: {kind}")
    project_root = Path(path).resolve()
    target_dir = project_root / "memory" / ".candidates"
    target_dir.mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()
    base_id = f"{today}-{slugify(title)}"
    entry_id = base_id
    suffix = 2
    while (target_dir / f"{entry_id}.md").exists():
        entry_id = f"{base_id}-{suffix}"
        suffix += 1
    target = target_dir / f"{entry_id}.md"
    target.write_text(
        candidate_body(
            kind=kind,
            title=title,
            entry_id=entry_id,
            issue_id=issue_id,
            spec_path=spec_path,
            summary=summary,
            rationale=rationale,
            evidence=evidence,
            alternatives=alternatives,
            owner=owner,
            reversal_conditions=reversal_conditions,
            source_event=source_event,
            source_artifacts=source_artifacts or [],
            review_after=review_after,
            supersedes=supersedes or [],
            superseded_by=[],
            storage_policy=storage_policy,
            mirror_targets=mirror_targets or [],
            tags=tags or [],
        ),
        encoding="utf-8",
    )
    return {
        "id": entry_id,
        "kind": kind,
        "status": "candidate",
        "path": str(target.relative_to(project_root)),
        "portable": True,
    }
```

- [ ] **Step 5: Run candidate creation test**

Run:

```bash
python3 -m unittest tests.test_project_memory.ProjectMemoryTests.test_create_memory_candidate_writes_reviewable_candidate -v
```

Expected: PASS.

## Task 4: Add Candidate Listing And Approval

**Files:**
- Modify: `scripts/project_memory.py`
- Modify: `tests/test_project_memory.py`

- [ ] **Step 1: Write failing test for candidate approval**

Add this test:

```python
    def test_list_and_approve_memory_candidate_moves_to_kind_folder(self):
        project_memory = load_module("project_memory", "scripts/project_memory.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidate = project_memory.create_memory_candidate(
                root,
                kind="decision",
                title="Use Git canonical memory",
                summary="Keep memory canonical in Git-tracked Markdown.",
                tags=["memory"],
            )

            candidates = project_memory.list_memory_candidates(root)
            approved = project_memory.approve_memory_candidate(root, candidate["id"])

            self.assertEqual([item["id"] for item in candidates], [candidate["id"]])
            self.assertTrue(approved["path"].startswith("memory/decisions/"))
            self.assertFalse((root / candidate["path"]).exists())
            self.assertTrue((root / approved["path"]).exists())
            self.assertIn("status: approved", (root / approved["path"]).read_text(encoding="utf-8"))
```

- [ ] **Step 2: Run focused test and verify it fails**

Run:

```bash
python3 -m unittest tests.test_project_memory.ProjectMemoryTests.test_list_and_approve_memory_candidate_moves_to_kind_folder -v
```

Expected: FAIL because listing/approval functions do not exist.

- [ ] **Step 3: Add candidate iterator**

Add:

```python
def iter_candidate_files(root):
    candidate_root = Path(root).resolve() / "memory" / ".candidates"
    if not candidate_root.exists():
        return []
    return sorted(path for path in candidate_root.glob("*.md") if path.is_file())
```

- [ ] **Step 4: Add listing function**

Add:

```python
def list_memory_candidates(path):
    project_root = Path(path).resolve()
    candidates = []
    for candidate_file in iter_candidate_files(project_root):
        text = candidate_file.read_text(encoding="utf-8")
        metadata, _ = parse_frontmatter(text)
        candidates.append(
            {
                "id": metadata.get("id") or candidate_file.stem,
                "kind": metadata.get("kind", ""),
                "title": metadata.get("title", ""),
                "path": str(candidate_file.relative_to(project_root)),
                "summary": metadata.get("summary", ""),
                "status": metadata.get("status", "candidate"),
            }
        )
    return candidates
```

- [ ] **Step 5: Add approval function**

Add:

```python
def approve_memory_candidate(path, candidate_id):
    project_root = Path(path).resolve()
    for candidate_file in iter_candidate_files(project_root):
        text = candidate_file.read_text(encoding="utf-8")
        metadata, _ = parse_frontmatter(text)
        found_id = metadata.get("id") or candidate_file.stem
        if found_id != candidate_id:
            continue
        kind = metadata.get("kind", "")
        if kind not in KIND_TO_DIR:
            raise ValueError(f"Unsupported memory kind: {kind}")
        target_dir = project_root / KIND_TO_DIR[kind]
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / candidate_file.name
        approved_text = text.replace("status: candidate", "status: approved", 1)
        target.write_text(approved_text, encoding="utf-8")
        candidate_file.unlink()
        return {
            "id": found_id,
            "kind": kind,
            "status": "approved",
            "path": str(target.relative_to(project_root)),
            "portable": True,
        }
    return None
```

- [ ] **Step 6: Run focused and full memory tests**

Run:

```bash
python3 -m unittest tests.test_project_memory.ProjectMemoryTests.test_list_and_approve_memory_candidate_moves_to_kind_folder -v
python3 -m unittest tests.test_project_memory -v
```

Expected: PASS.

## Task 5: Add Search Match Reasons And Source Links

**Files:**
- Modify: `scripts/project_memory.py`
- Modify: `tests/test_project_memory.py`

- [ ] **Step 1: Write failing test for search explanations**

Add:

```python
    def test_search_memory_entries_returns_match_reasons_and_source_artifacts(self):
        project_memory = load_module("project_memory", "scripts/project_memory.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project_memory.create_memory_entry(
                root,
                kind="decision",
                title="Use Git canonical memory",
                issue_id="034-memory-capture-and-sync-workflow",
                summary="Keep memory canonical in Git-tracked Markdown.",
                source_artifacts=["specs/034-memory-capture-and-sync-workflow/spec.md"],
                tags=["memory", "team"],
            )

            hits = project_memory.search_memory_entries(root, "canonical memory", tag="team")

            self.assertEqual(len(hits), 1)
            self.assertIn("query: canonical", hits[0]["match_reasons"])
            self.assertIn("query: memory", hits[0]["match_reasons"])
            self.assertIn("tag: team", hits[0]["match_reasons"])
            self.assertEqual(
                hits[0]["source_artifacts"],
                ["specs/034-memory-capture-and-sync-workflow/spec.md"],
            )
```

- [ ] **Step 2: Run focused test and verify it fails**

Run:

```bash
python3 -m unittest tests.test_project_memory.ProjectMemoryTests.test_search_memory_entries_returns_match_reasons_and_source_artifacts -v
```

Expected: FAIL because result lacks `match_reasons` and `source_artifacts`.

- [ ] **Step 3: Add list parser for frontmatter arrays**

Add:

```python
def parse_list_value(value):
    value = value.strip()
    if not value.startswith("[") or not value.endswith("]"):
        return []
    inner = value[1:-1].strip()
    if not inner:
        return []
    return [item.strip() for item in inner.split(",") if item.strip()]
```

- [ ] **Step 4: Build match reasons in search**

Inside `search_memory_entries()`, before appending a hit:

```python
        match_reasons = []
        for token in tokens:
            if token in haystack:
                match_reasons.append(f"query: {token}")
        if kind:
            match_reasons.append(f"kind: {kind}")
        if issue_id:
            match_reasons.append(f"issue_id: {issue_id}")
        if spec_path:
            match_reasons.append(f"spec: {spec_path}")
        if tag:
            match_reasons.append(f"tag: {tag}")
```

- [ ] **Step 5: Add fields to hit objects**

In the hit dictionary, add:

```python
                "match_reasons": match_reasons,
                "source_artifacts": parse_list_value(metadata.get("source_artifacts", "[]")),
                "issue_id": metadata.get("issue_id", ""),
                "spec": metadata.get("spec", ""),
```

- [ ] **Step 6: Run focused and full memory tests**

Run:

```bash
python3 -m unittest tests.test_project_memory.ProjectMemoryTests.test_search_memory_entries_returns_match_reasons_and_source_artifacts -v
python3 -m unittest tests.test_project_memory -v
```

Expected: PASS.

## Task 6: Add CLI Flags For Candidates, Approval, And Export Guidance

**Files:**
- Modify: `scripts/project_memory.py`
- Modify: `tests/test_project_memory.py`

- [ ] **Step 1: Write failing unit test for export guidance**

Add:

```python
    def test_memory_export_guidance_keeps_markdown_canonical(self):
        project_memory = load_module("project_memory", "scripts/project_memory.py")

        guidance = project_memory.memory_export_guidance("google-drive")

        self.assertEqual(guidance["target"], "google-drive")
        self.assertEqual(guidance["canonical"], "memory/")
        self.assertIn("mirror", guidance["mode"])
        self.assertIn("Do not treat Google Drive as the source of truth.", guidance["warnings"])
```

- [ ] **Step 2: Run focused test and verify it fails**

Run:

```bash
python3 -m unittest tests.test_project_memory.ProjectMemoryTests.test_memory_export_guidance_keeps_markdown_canonical -v
```

Expected: FAIL because `memory_export_guidance` does not exist.

- [ ] **Step 3: Add export guidance function**

Add:

```python
def memory_export_guidance(target):
    target = (target or "").strip() or "local"
    warnings = [
        "Repo-local Markdown remains canonical.",
        "External indexes and mirrors must be rebuildable from memory/.",
    ]
    if target == "google-drive":
        warnings.append("Do not treat Google Drive as the source of truth.")
        warnings.append("Avoid syncing .git/ through Google Drive conflict handling.")
    return {
        "schema": "moduflow.memory-export-guidance.v1",
        "target": target,
        "canonical": "memory/",
        "mode": "mirror/export",
        "recommended_sources": ["memory/", "specs/", "issues/", "workspace/", "business/", "reports/"],
        "warnings": warnings,
    }
```

- [ ] **Step 4: Extend CLI parser**

Add parser arguments:

```python
    parser.add_argument("--candidate", action="store_true", help="Create a reviewable memory candidate.")
    parser.add_argument("--list-candidates", action="store_true", help="List reviewable memory candidates.")
    parser.add_argument("--approve", default="", help="Approve a memory candidate by id.")
    parser.add_argument("--source-event", default="")
    parser.add_argument("--source-artifacts", default="", help="Comma-separated source artifact links.")
    parser.add_argument("--review-after", default="")
    parser.add_argument("--supersedes", default="", help="Comma-separated superseded memory ids.")
    parser.add_argument("--storage-policy", default="local")
    parser.add_argument("--mirror-targets", default="", help="Comma-separated mirror/export targets.")
    parser.add_argument("--export-guidance", default="", help="Return mirror/export guidance for a target.")
```

- [ ] **Step 5: Route CLI actions in `main()`**

Before the `elif args.kind:` branch, add:

```python
    elif args.export_guidance:
        result = memory_export_guidance(args.export_guidance)
    elif args.list_candidates:
        result = list_memory_candidates(args.project_path)
    elif args.approve:
        result = approve_memory_candidate(args.project_path, args.approve)
    elif args.candidate:
        if not args.kind or not args.title:
            parser.error("--candidate requires --kind and --title")
        tags = [tag.strip() for tag in args.tags.split(",") if tag.strip()]
        source_artifacts = [item.strip() for item in args.source_artifacts.split(",") if item.strip()]
        supersedes = [item.strip() for item in args.supersedes.split(",") if item.strip()]
        mirror_targets = [item.strip() for item in args.mirror_targets.split(",") if item.strip()]
        result = create_memory_candidate(
            args.project_path,
            args.kind,
            args.title,
            issue_id=args.issue_id,
            spec_path=args.spec,
            summary=args.summary,
            rationale=args.rationale,
            evidence=args.evidence,
            alternatives=args.alternatives,
            owner=args.owner,
            reversal_conditions=args.reversal_conditions,
            source_event=args.source_event,
            source_artifacts=source_artifacts,
            review_after=args.review_after,
            supersedes=supersedes,
            storage_policy=args.storage_policy,
            mirror_targets=mirror_targets,
            tags=tags,
        )
```

- [ ] **Step 6: Extend direct entry CLI creation with new fields**

In the existing `elif args.kind:` block, parse and pass:

```python
        source_artifacts = [item.strip() for item in args.source_artifacts.split(",") if item.strip()]
        supersedes = [item.strip() for item in args.supersedes.split(",") if item.strip()]
        mirror_targets = [item.strip() for item in args.mirror_targets.split(",") if item.strip()]
```

And pass:

```python
            source_event=args.source_event,
            source_artifacts=source_artifacts,
            review_after=args.review_after,
            supersedes=supersedes,
            storage_policy=args.storage_policy,
            mirror_targets=mirror_targets,
```

- [ ] **Step 7: Run focused and full tests**

Run:

```bash
python3 -m unittest tests.test_project_memory.ProjectMemoryTests.test_memory_export_guidance_keeps_markdown_canonical -v
python3 -m unittest tests.test_project_memory -v
```

Expected: PASS.

## Task 7: Validate Memory Links And Candidate Status

**Files:**
- Modify: `scripts/validate_project_artifacts.py`
- Modify: `tests/test_project_memory.py`

- [ ] **Step 1: Write failing test for broken memory link validation**

Add:

```python
    def test_project_validation_reports_broken_memory_source_artifact(self):
        validate_project_artifacts = load_module(
            "validate_project_artifacts", "scripts/validate_project_artifacts.py"
        )
        project_memory = load_module("project_memory", "scripts/project_memory.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".moduflow").mkdir()
            (root / ".moduflow" / "config.json").write_text(
                '{"schema":"moduflow.config.v1","paths":{}}', encoding="utf-8"
            )
            (root / ".moduflow" / "state.json").write_text(
                '{"schema":"moduflow.state.v1","phase":"status","next_command":"product:status"}',
                encoding="utf-8",
            )
            for relative in ["issues", "specs", "workspace"]:
                (root / relative).mkdir()
            for relative in ["inbox.md", "opportunities.md", "roadmap.md", "dashboard.md"]:
                (root / "workspace" / relative).write_text("# Test\n", encoding="utf-8")
            project_memory.apply_memory_plan(project_memory.build_memory_plan(root, dry_run=False))
            project_memory.create_memory_entry(
                root,
                kind="decision",
                title="Broken source",
                source_artifacts=["specs/missing/spec.md"],
            )

            result = validate_project_artifacts.validate_project(root)

            self.assertFalse(result["valid"])
            self.assertIn(
                "memory/decisions/",
                "\n".join(result["errors"]),
            )
            self.assertIn("broken source_artifacts link: specs/missing/spec.md", "\n".join(result["errors"]))
```

- [ ] **Step 2: Run focused test and verify it fails**

Run:

```bash
python3 -m unittest tests.test_project_memory.ProjectMemoryTests.test_project_validation_reports_broken_memory_source_artifact -v
```

Expected: FAIL because validator does not inspect memory links.

- [ ] **Step 3: Add memory file iteration to validator**

In `scripts/validate_project_artifacts.py`, add:

```python
def iter_memory_markdown(root):
    memory_root = root / "memory"
    if not memory_root.exists():
        return []
    return sorted(path for path in memory_root.glob("*/*.md") if path.is_file())
```

- [ ] **Step 4: Add frontmatter parser and list parser to validator**

Add:

```python
def parse_frontmatter(text):
    if not text.startswith("---\n"):
        return {}
    parts = text.split("\n---\n", 1)
    if len(parts) != 2:
        return {}
    meta_text = parts[0].split("\n", 1)[1]
    metadata = {}
    for line in meta_text.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip()
    return metadata


def parse_list_value(value):
    value = (value or "").strip()
    if not value.startswith("[") or not value.endswith("]"):
        return []
    inner = value[1:-1].strip()
    if not inner:
        return []
    return [item.strip() for item in inner.split(",") if item.strip()]
```

- [ ] **Step 5: Add memory link validation**

Add:

```python
def validate_memory_links(root, errors):
    for memory_file in iter_memory_markdown(root):
        metadata = parse_frontmatter(memory_file.read_text(encoding="utf-8"))
        relative_memory = str(memory_file.relative_to(root))
        for linked in parse_list_value(metadata.get("source_artifacts", "[]")):
            if linked and not (root / linked).exists():
                errors.append(f"{relative_memory}: broken source_artifacts link: {linked}")
        if "memory/.candidates/" in relative_memory and metadata.get("status") != "candidate":
            errors.append(f"{relative_memory}: candidate memory must have status: candidate")
```

- [ ] **Step 6: Call validation from `validate_project()`**

Before returning the result, add:

```python
    validate_memory_links(root, errors)
```

- [ ] **Step 7: Run focused validation test**

Run:

```bash
python3 -m unittest tests.test_project_memory.ProjectMemoryTests.test_project_validation_reports_broken_memory_source_artifact -v
```

Expected: PASS.

## Task 8: Update PM-Friendly Command Documentation

**Files:**
- Modify: `commands/product-memory.md`
- Modify: `specs/034-memory-capture-and-sync-workflow/status.md`

- [ ] **Step 1: Update `commands/product-memory.md` with PM flows**

Replace the `## Do` section with:

```markdown
## PM-Friendly Flow

1. Initialize memory:

```bash
python3 scripts/project_memory.py <project-path> --write
```

2. Create a reviewable candidate when a workflow produces a durable decision, deliverable, evidence summary, release note, or failed approach:

```bash
python3 scripts/project_memory.py <project-path> --candidate --kind decision --title "Use Git canonical memory" --issue-id 034-memory-capture-and-sync-workflow --spec specs/034-memory-capture-and-sync-workflow/spec.md --summary "Keep memory canonical in Git-tracked Markdown." --source-event decision-detected --source-artifacts specs/034-memory-capture-and-sync-workflow/spec.md --tags memory,team,pm
```

3. Review candidates:

```bash
python3 scripts/project_memory.py <project-path> --list-candidates
```

4. Approve a candidate:

```bash
python3 scripts/project_memory.py <project-path> --approve 2026-06-26-use-git-canonical-memory
```

5. Search with source links and match reasons:

```bash
python3 scripts/project_memory.py <project-path> --search "canonical memory"
```

6. Get mirror/export guidance:

```bash
python3 scripts/project_memory.py <project-path> --export-guidance google-drive
```
```

- [ ] **Step 2: Add team and adapter rules**

In the `## Rules` section, add:

```markdown
- In team mode, shared memory should be approved through Git branch/PR review before merge.
- RAG, LangGraph, MCP servers, Basic Memory, projectmem, mem0, Supermemory, Google Drive, and Obsidian are adapters or mirrors, not the source of truth.
- PMs can approve memory candidates through natural language; implementation hosts may translate that approval into the CLI calls above.
```

- [ ] **Step 3: Update 034 status**

In `specs/034-memory-capture-and-sync-workflow/status.md`, add under Pending or Done as appropriate:

```markdown
- Document PM-friendly candidate, approval, search, and export usage in `commands/product-memory.md`.
```

## Task 9: Run Full Verification And Update ModuFlow State

**Files:**
- Modify: `issues/034-memory-capture-and-sync-workflow.md`
- Modify: `specs/034-memory-capture-and-sync-workflow/status.md`
- Modify: `workspace/dashboard.md`
- Modify: `workspace/loop-state.json`
- Modify: `.moduflow/state.json`

- [ ] **Step 1: Run focused tests**

Run:

```bash
python3 -m unittest tests.test_project_memory -v
```

Expected: PASS.

- [ ] **Step 2: Run project validation**

Run:

```bash
python3 scripts/validate_project_artifacts.py .
```

Expected: JSON output with `"valid": true`.

- [ ] **Step 3: Run package validation**

Run:

```bash
python3 scripts/validate_moduflow.py .
```

Expected: `ModuFlow validation passed`.

- [ ] **Step 4: Update issue checklist**

In `issues/034-memory-capture-and-sync-workflow.md`, check:

```markdown
- [x] plan -> `specs/034-memory-capture-and-sync-workflow/plan.md`
```

After implementation also check:

```markdown
- [x] execute -> PR / commits
- [x] validation -> schema and link checks for memory entries
```

- [ ] **Step 5: Update status with verification**

In `specs/034-memory-capture-and-sync-workflow/status.md`, add the verification commands and results.

- [ ] **Step 6: Update state to review**

If implementation is complete, set:

```json
"phase": "review",
"next_command": "product:review 034-memory-capture-and-sync-workflow"
```

in `.moduflow/state.json` and `workspace/loop-state.json`, and update `workspace/dashboard.md`.

## Self-Review

- Spec coverage: plan covers candidate creation, approval, storage, retrieval explanations, source links, validation, external mirror guidance, and PM/team documentation.
- Deferred from v1: real RAG index, LangGraph runner, MCP server, Google Drive API integration, hosted team service. These remain adapters and should not block local-first memory.
- Placeholder scan: no implementation step should rely on unspecified behavior; code-level steps include concrete function names, fields, commands, and expected results.

## Execution Handoff

Plan complete for `034-memory-capture-and-sync-workflow`. Recommended execution path: subagent-driven or inline execution task-by-task, starting with Task 1.

