# Verified Code-Review Intake and Remediation Routing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a lightweight, adapter-first review intake pipeline that verifies human/AI/tool findings, applies deterministic risk policy, and creates traceable Git-file remediation candidates without automatically changing code or GitHub state.

**Architecture:** Add a pure `review_intake.py` domain module for the versioned packet, finding identity, verification, disposition, policy, and candidate contracts. Add `project_review.py` as the CLI/orchestration boundary that adapts manual structured findings, GitHub thread snapshots, CodeQL alert snapshots, and SARIF results, then writes JSON plus Korean Markdown projections. Existing Superpowers, GitHub, CodeQL/SARIF, and Spec Kit capabilities remain replaceable mappings under `adapters/`; routine commands do not import or invoke them without an explicit trigger.

**Tech Stack:** Python 3 standard library, `unittest`, JSON/Markdown Git-native artifacts, YAML metadata files without a runtime YAML dependency, GitHub plugin/`gh` snapshots supplied at the adapter boundary.

---

## Global Constraints

Constitution v1.0 applies (`workspace/constitution.md`). Plan-specific additions:

- `scripts/review_intake.py` is the only parser and validator for `moduflow.review-intake.v1`; consumers may not duplicate packet, finding, disposition, lane, or policy validation.
- `scripts/project_review.py` owns source adaptation, artifact rendering/writing, and CLI orchestration. It never implements review truth by keyword alone; AI/tool decisions arrive as explicit structured input and are checked by the core policy.
- External review material defaults to `reference` plus SHA-256. Tests and fixtures never copy `/Users/dongwon.lee/Downloads/code-review.md` or any externally owned source text into this repository.
- All default behavior is dry-run/read-only. `--write` may create only project-local review packets and candidate projections; GitHub reply, thread resolution, issue publication, code changes, and release changes remain outside this script.
- Adapter availability is recorded, not assumed. A missing GitHub/SARIF adapter cannot turn an unverified finding into a verified one, and an unrelated unavailable adapter cannot fail the whole intake.
- Router AI, source reviewer, verifier, and final approver provenance remain distinct fields. AI may propose but may not finalize a high-risk rejection, security dismissal, or release bypass without policy-compliant evidence and human approval.
- Exact fingerprints may deduplicate automatically. Semantic similarity is only an overlap hint and never auto-merges findings or candidates.
- No plugin is loaded during routine L0 work. Adapter selection is an explicit pure function of trigger, source type, paths, finding state, and release phase.
- Credentials, secrets, copied sensitive text, and hash inputs are never echoed in exception messages or Markdown projections.
- Existing dirty worktrees and the stacked Issue 088 branch remain untouched outside the isolated Issue 089 worktree.

## Recommended Discipline

| Stream | Discipline / Adapter | Reason |
| --- | --- | --- |
| A — packet and identity | Superpowers TDD | Stable IDs, hashing, and schema validation need deterministic RED/GREEN tests. |
| B — source adapters | source-adapter-policy + TDD | Manual, GitHub, and SARIF inputs must stay replaceable and normalized at one boundary. |
| C — AI/policy decisions | receiving-code-review + TDD | Recommendations must be checked against evidence and deterministic safety rules. |
| D — candidate routing | Git-native artifact model + TDD | Findings and issue candidates require durable two-way traceability. |
| E — CLI and human output | Korean-first review surface + focused tests | Dry-run/write behavior and readable summaries must be independently verifiable. |
| F — completion | verification-before-completion | Full tests, validators, and release check are required before review. |

## File Structure

- Create `scripts/review_intake.py`: schema constants, source/hash handling, finding normalization/fingerprint, validation, policy, decision application, lane/CognitiveDemand routing, deduplication, and candidate trace construction.
- Create `scripts/project_review.py`: manual/GitHub/CodeQL/SARIF adapters, trigger-based adapter selection, JSON loading, packet/decision orchestration, Korean Markdown rendering, candidate queue rendering, persistence, and CLI.
- Create `tests/test_review_intake.py`: pure model, hash, fingerprint, validation, policy, disposition, deduplication, routing, and trace tests.
- Create `tests/test_project_review.py`: adapter snapshots, lazy invocation, artifact output, CLI dry-run/write, redaction, and candidate queue tests.
- Create `templates/reviews/review-intake.json`: valid minimal packet starter with no real repository or review content.
- Create `templates/reviews/review-summary.ko.md`: Korean human-projection section contract.
- Create `templates/reviews/review-candidates.md`: generated queue section contract.
- Create `adapters/github-review.yaml`: GitHub plugin/GraphQL snapshot mapping and write-safety contract.
- Create `adapters/security-review.yaml`: CodeQL/SARIF mapping and severity/fingerprint contract.
- Modify `adapters/superpowers.yaml`: add `receiving code review` and evidence/disposition mapping.
- Create `overlays/review-policy.yaml`: human-readable v1 policy IDs, sensitive path classes, verification rules, lanes, and approval rules; Python constants are tested against these IDs without adding a YAML parser dependency.
- Modify `vendor.lock.json`: register the installed Codex GitHub plugin source/version.
- Modify `scripts/validate_moduflow.py`: require the new core, CLI, adapters, overlay, and templates.
- Modify `tests/test_validation_distribution.py`: prove the package validator requires the new review surface and GitHub source.
- Modify `commands/product-review.md`: add the `--intake` mode, Router/Verifier responsibilities, lazy invocation levels, commands, and write boundaries while preserving post-implementation review behavior.
- Modify `skills/index/SKILL.md`: route “외부 코드리뷰 접수/검증” to `product:review --intake` and retain plain `review` for post-implementation review.
- Update `issues/089-verified-code-review-intake-and-remediation-routing.md`, `tasks.md`, and later `status.md` as implementation advances.

## Interfaces

### Core packet

```python
REVIEW_SCHEMA = "moduflow.review-intake.v1"

packet = {
    "schema": REVIEW_SCHEMA,
    "review_id": "2026-07-16-sample-review",
    "source": {
        "kind": "human",
        "provider": "external-reviewer",
        "identity": "unknown",
        "received_at": "2026-07-16",
        "retention": "reference",
        "locator": "/absolute/path/to/review.md",
        "sha256": "64-lowercase-hex",
    },
    "target": {
        "repository": "github.com/owner/repository",
        "commit": "40-hex-sha",
        "base_branch": "main",
    },
    "trigger": {
        "event": "manual_intake",
        "reason_codes": ["external_review_received"],
    },
    "adapter_run": {
        "invoked": ["manual-review-document", "superpowers-review"],
        "skipped": ["github-review", "security-review", "spec-kit"],
        "reason_codes": ["manual_source", "no_pr_snapshot", "no_security_payload"],
    },
    "findings": [],
    "trace": {"finding_to_candidates": {}, "candidate_to_findings": {}},
    "updated_at": "2026-07-16",
}
```

### Normalized finding

```python
finding = {
    "id": "F-001",
    "fingerprint": "sha256:0000000000000000000000000000000000000000000000000000000000000000",
    "source_author": {"kind": "human", "identity": "unknown"},
    "observation": "Untrusted spreadsheet cells are exported verbatim.",
    "recommendation": "Escape formula-leading cells before CSV export.",
    "root_cause_hypothesis": "The exporter assumes all cell values are inert text.",
    "reviewer_confidence": "medium",
    "locations": [{"path": "src/export.py", "line": 41, "anchor": "build_csv"}],
    "provider_evidence": {},
    "verification": {
        "state": "unverified",
        "verifier": None,
        "files_checked": [],
        "reproduction": [],
        "tests": [],
        "architecture": [],
        "import_boundaries": [],
        "contradictions": [],
        "verified_at": None,
    },
    "risk": {
        "severity": "high",
        "release_impact": "blocking",
        "no_risk_claim": False,
        "no_risk_state": "not_claimed",
    },
    "router": {
        "classification": "actionable",
        "confidence": "high",
        "proposed_lane": "security",
        "reason_codes": ["security_input_boundary"],
    },
    "disposition": {
        "state": "pending_verification",
        "rationale": "",
        "decided_by": None,
        "decided_at": None,
        "human_approved": False,
    },
    "decision_history": [],
    "route": {
        "lane": None,
        "CognitiveDemand": None,
        "candidate_ids": [],
        "existing_issue_ids": [],
    },
}
```

### Core functions

- `build_source_record(kind, provider, identity, received_at, retention, locator=None, copied_text=None, source_hash=None, model=None, version=None, policy_version=None) -> dict`
- `new_packet(review_id, source, target, trigger, adapter_run, raw_findings) -> dict`
- `normalize_finding(raw, index, source, target) -> dict`
- `validate_packet(packet, final=False) -> list[dict]`
- `apply_decision(packet, decision) -> dict`
- `build_candidates(packet, existing_candidates=(), proposals=()) -> dict`

`validate_packet` returns a list of `{code, path, message}` errors and never mutates its input. `apply_decision` returns a deep-copied packet or raises `ReviewIntakeError(code, message)`; it never partially changes the caller's object.

### CLI

```text
python3 scripts/project_review.py <project-root> --new \
  --review-id <id> --adapter manual|github|codeql|sarif \
  --source <path> --source-kind human|ai|tool \
  --provider <provider> --source-identity <identity> \
  --retention copy|reference|hash_only \
  --target-repository <host/owner/repo> --target-commit <full-sha> \
  [--base-branch main] [--findings-file <normalized-findings.json>] [--write]

python3 scripts/project_review.py <project-root> \
  --apply-decisions <decisions.json> --review-id <id> [--write]

python3 scripts/project_review.py <project-root> \
  --validate <packet.json> [--final]
```

The manual adapter requires `--findings-file`; arbitrary prose interpretation belongs to the Router AI and is passed as structured input. GitHub and SARIF adapters deterministically extract observations and provenance from their snapshot formats, after which Router/Verifier decisions still remain separate.

## Implementation Readiness Inputs

- API contract: N/A for a network service. The packet, finding, decision, adapter payload, and CLI shapes above are the binding interfaces.
- Test strategy: stdlib `unittest` RED/GREEN slices for each pure function and CLI boundary, followed by full discovery and release checks.
- Storybook/MSW/Playwright: not applicable; no browser UI or API-backed frontend changes.
- Permission model: local packet/candidate writes require `--write`; GitHub writes are never performed by Issue 089.
- Release condition: all new focused tests, full test discovery, package validation, artifact validation, spec consistency, and `release_check` pass.
- Rollback: revert Issue 089 commits. Review packets already created in downstream projects remain readable JSON/Markdown; no remote state or source files are mutated.

## Task 1: Core Packet, Source Retention, And Finding Identity

**Files:**
- Create: `scripts/review_intake.py`
- Create: `tests/test_review_intake.py`

- [ ] **Step 1: Write failing source and packet tests**

Create `tests/test_review_intake.py` with a temporary referenced review file and explicit target metadata.

```python
import copy
import hashlib
import tempfile
import unittest
from pathlib import Path

from scripts import review_intake as ri


def make_packet(severity="medium", path="src/a.py", no_risk_claim=False, raw_findings=None):
    source = {
        "kind": "human",
        "provider": "external",
        "identity": "source-reviewer",
        "received_at": "2026-07-16",
        "retention": "hash_only",
        "sha256": "a" * 64,
    }
    target = {"repository": "github.com/o/r", "commit": "b" * 40, "base_branch": "main"}
    findings = raw_findings or [{
        "observation": "Observed behavior",
        "recommendation": "Suggested change",
        "root_cause_hypothesis": "Possible cause",
        "locations": [{"path": path, "line": 10, "anchor": "run"}],
        "severity": severity,
        "release_impact": "blocking" if severity in {"high", "critical"} else "non_blocking",
        "no_risk_claim": no_risk_claim,
    }]
    return ri.new_packet(
        review_id="review-1",
        source=source,
        target=target,
        trigger={"event": "manual_intake", "reason_codes": ["external_review_received"]},
        adapter_run={"invoked": ["manual-review-document"], "skipped": [], "reason_codes": ["manual_source"]},
        raw_findings=findings,
    )


def decision_for(finding_id, disposition="accept", actor_kind="human", human_approved=False,
                 verification_state="confirmed", target_commit="b" * 40):
    return {
        "finding_id": finding_id,
        "target_commit": target_commit,
        "verification": {
            "state": verification_state,
            "verifier": {"kind": "tool", "identity": "independent-verifier", "role": "verifier", "run_id": "verify-1"},
            "files_checked": ["src/a.py"],
            "reproduction": ["reproduced with fixture"],
            "tests": ["tests/test_a.py::test_behavior"],
            "architecture": [],
            "import_boundaries": ["src/a.py -> stdlib"],
            "contradictions": [],
            "verified_at": "2026-07-16",
        },
        "disposition": disposition,
        "rationale": f"Evidence supports {disposition}.",
        "actor": {"kind": actor_kind, "identity": "decision-owner", "run_id": "decision-1"},
        "human_approved": human_approved,
    }


class SourceAndPacketTests(unittest.TestCase):
    def test_reference_retention_hashes_without_copying_text(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "review.md"
            path.write_text("external review", encoding="utf-8")
            source = ri.build_source_record(
                kind="human",
                provider="external-reviewer",
                identity="unknown",
                received_at="2026-07-16",
                retention="reference",
                locator=str(path),
            )
        self.assertEqual(source["sha256"], hashlib.sha256(b"external review").hexdigest())
        self.assertNotIn("copied_text", source)

    def test_finding_separates_observation_recommendation_and_hypothesis(self):
        packet = ri.new_packet(
            review_id="review-1",
            source={"kind": "human", "provider": "external", "identity": "A", "received_at": "2026-07-16", "retention": "hash_only", "sha256": "a" * 64},
            target={"repository": "github.com/o/r", "commit": "b" * 40, "base_branch": "main"},
            trigger={"event": "manual_intake", "reason_codes": ["external_review_received"]},
            adapter_run={"invoked": ["manual-review-document"], "skipped": [], "reason_codes": ["manual_source"]},
            raw_findings=[{
                "observation": "Observed behavior",
                "recommendation": "Suggested change",
                "root_cause_hypothesis": "Possible cause",
                "locations": [{"path": "src/a.py", "line": 10, "anchor": "run"}],
            }],
        )
        finding = packet["findings"][0]
        self.assertEqual(finding["id"], "F-001")
        self.assertEqual(finding["verification"]["state"], "unverified")
        self.assertEqual(finding["disposition"]["state"], "pending_verification")
        self.assertTrue(finding["fingerprint"].startswith("sha256:"))

    def test_reference_url_removes_credentials_query_and_fragment(self):
        source = ri.build_source_record(
            kind="human", provider="external", identity="unknown", received_at="2026-07-16",
            retention="reference", locator="https://user:token@example.com/review.md?sig=secret#section",
            source_hash="c" * 64,
        )
        self.assertEqual(source["locator"], "https://example.com/review.md")
        self.assertNotIn("token", repr(source))
        self.assertNotIn("secret", repr(source))

    def test_line_movement_does_not_change_fingerprint(self):
        first = make_packet(raw_findings=[{"observation": "Same finding", "rule_id": "R1", "locations": [{"path": "src/a.py", "line": 10, "anchor": "run"}]}])
        second = make_packet(raw_findings=[{"observation": "Same finding", "rule_id": "R1", "locations": [{"path": "src/a.py", "line": 99, "anchor": "run"}]}])
        self.assertEqual(first["findings"][0]["fingerprint"], second["findings"][0]["fingerprint"])

    def test_validate_packet_does_not_mutate_input(self):
        packet = {"schema": "wrong"}
        before = copy.deepcopy(packet)
        self.assertTrue(ri.validate_packet(packet))
        self.assertEqual(packet, before)
```

- [ ] **Step 2: Run the RED slice**

Run:

```bash
python3 -m unittest tests.test_review_intake.SourceAndPacketTests -v
```

Expected: FAIL with `ImportError` or missing `review_intake` functions.

- [ ] **Step 3: Implement the minimal immutable domain core**

Create `scripts/review_intake.py` with exact enums, sanitized hashing, normalized paths, stable fingerprints, initial finding shape, and non-mutating validation.

```python
#!/usr/bin/env python3
import copy
import hashlib
import json
import re
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

REVIEW_SCHEMA = "moduflow.review-intake.v1"
SOURCE_KINDS = {"human", "ai", "tool"}
RETENTION_MODES = {"copy", "reference", "hash_only"}
VERIFICATION_STATES = {"unverified", "confirmed", "contradicted", "inconclusive"}
FINAL_DISPOSITIONS = {"accept", "partial_accept", "defer", "reject"}
LANES = {"security", "pre_release", "post_release_refactor"}
SEVERITIES = {"low", "medium", "high", "critical"}


class ReviewIntakeError(ValueError):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


def _sha256_bytes(value):
    return hashlib.sha256(value).hexdigest()


def sha256_file(path):
    return _sha256_bytes(Path(path).read_bytes())


def _safe_locator(value):
    text = str(value or "")
    parsed = urlsplit(text)
    if parsed.scheme.lower() in {"http", "https"}:
        host = (parsed.hostname or "").lower()
        port = f":{parsed.port}" if parsed.port else ""
        return urlunsplit((parsed.scheme.lower(), host + port, parsed.path, "", ""))
    return text


def build_source_record(kind, provider, identity, received_at, retention, locator=None,
                        copied_text=None, source_hash=None, model=None, version=None,
                        policy_version=None):
    if kind not in SOURCE_KINDS:
        raise ReviewIntakeError("source_kind_invalid", f"unsupported source kind: {kind}")
    if retention not in RETENTION_MODES:
        raise ReviewIntakeError("retention_invalid", f"unsupported retention: {retention}")
    record = {
        "kind": kind,
        "provider": str(provider or "unknown"),
        "identity": str(identity or "unknown"),
        "received_at": str(received_at),
        "retention": retention,
    }
    if model:
        record["model"] = str(model)
    if version:
        record["version"] = str(version)
    if policy_version:
        record["policy_version"] = str(policy_version)
    if retention == "reference":
        path = Path(locator or "")
        if path.is_file():
            record.update(locator=_safe_locator(path.resolve()), sha256=sha256_file(path))
        elif re.match(r"^https?://", str(locator or "")) and re.fullmatch(r"[0-9a-f]{64}", str(source_hash or "")):
            record.update(locator=_safe_locator(locator), sha256=source_hash)
        else:
            raise ReviewIntakeError("source_unavailable", "reference requires a readable local file or URL plus SHA-256")
    elif retention == "copy":
        if copied_text is None:
            raise ReviewIntakeError("source_copy_missing", "copy retention requires copied text")
        record.update(copied_text=str(copied_text), sha256=_sha256_bytes(str(copied_text).encode("utf-8")))
    else:
        digest = str(source_hash or "")
        if not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise ReviewIntakeError("source_hash_invalid", "hash_only requires a lowercase SHA-256")
        record["sha256"] = digest
        if locator:
            record["description"] = _safe_locator(locator)
    return record


def _normalized_location(location):
    path = str(location.get("path") or "").replace("\\", "/")
    while path.startswith("./"):
        path = path[2:]
    if not path or ".." in Path(path).parts:
        raise ReviewIntakeError("finding_path_invalid", "finding path must remain inside the project")
    return {
        "path": path,
        "line": location.get("line"),
        "anchor": str(location.get("anchor") or ""),
    }


def _fingerprint(raw, source, target, locations):
    stable = {
        "provider": source.get("provider", "unknown"),
        "rule_id": raw.get("rule_id") or "",
        "provider_fingerprint": raw.get("provider_fingerprint") or "",
        "repository": target["repository"].lower(),
        "locations": [{"path": item["path"], "anchor": item["anchor"]} for item in locations],
        "observation": re.sub(r"\s+", " ", str(raw.get("observation") or "").strip().lower()),
    }
    encoded = json.dumps(stable, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return "sha256:" + _sha256_bytes(encoded)


def normalize_finding(raw, index, source, target):
    locations = [_normalized_location(item) for item in raw.get("locations", [])]
    observation = str(raw.get("observation") or "").strip()
    if not observation:
        raise ReviewIntakeError("observation_missing", "each finding requires an observation")
    severity = str(raw.get("severity") or "medium")
    if severity not in SEVERITIES:
        raise ReviewIntakeError("severity_invalid", f"unsupported severity: {severity}")
    return {
        "id": f"F-{index:03d}",
        "fingerprint": _fingerprint(raw, source, target, locations),
        "rule_id": raw.get("rule_id"),
        "source_author": copy.deepcopy(raw.get("source_author") or {"kind": source["kind"], "identity": source["identity"]}),
        "observation": observation,
        "recommendation": str(raw.get("recommendation") or "").strip(),
        "root_cause_hypothesis": str(raw.get("root_cause_hypothesis") or "").strip(),
        "reviewer_confidence": str(raw.get("reviewer_confidence") or "unknown"),
        "locations": locations,
        "provider_evidence": copy.deepcopy(raw.get("provider_evidence") or {}),
        "verification": {"state": "unverified", "verifier": None, "files_checked": [], "reproduction": [], "tests": [], "architecture": [], "import_boundaries": [], "contradictions": [], "verified_at": None},
        "risk": {"severity": severity, "release_impact": raw.get("release_impact", "unknown"), "no_risk_claim": bool(raw.get("no_risk_claim")), "no_risk_state": "unverified" if raw.get("no_risk_claim") else "not_claimed"},
        "router": copy.deepcopy(raw.get("router") or {"classification": "unclassified", "confidence": "low", "proposed_lane": None, "reason_codes": [], "actor": None}),
        "disposition": {"state": "pending_verification", "rationale": "", "decided_by": None, "decided_at": None, "human_approved": False},
        "decision_history": [],
        "route": {"lane": None, "CognitiveDemand": None, "candidate_ids": [], "existing_issue_ids": []},
    }


def new_packet(review_id, source, target, trigger, adapter_run, raw_findings):
    packet = {
        "schema": REVIEW_SCHEMA,
        "review_id": str(review_id),
        "source": copy.deepcopy(source),
        "target": copy.deepcopy(target),
        "trigger": copy.deepcopy(trigger),
        "adapter_run": copy.deepcopy(adapter_run),
        "findings": [normalize_finding(raw, index, source, target) for index, raw in enumerate(raw_findings, 1)],
        "trace": {"finding_to_candidates": {}, "candidate_to_findings": {}},
        "updated_at": date.today().isoformat(),
    }
    errors = validate_packet(packet)
    if errors:
        raise ReviewIntakeError(errors[0]["code"], errors[0]["message"])
    return packet


def validate_packet(packet, final=False):
    errors = []
    def add(code, path, message): errors.append({"code": code, "path": path, "message": message})
    if packet.get("schema") != REVIEW_SCHEMA:
        add("schema_invalid", "schema", f"expected {REVIEW_SCHEMA}")
    if not re.fullmatch(r"[0-9A-Za-z][0-9A-Za-z._-]{2,127}", str(packet.get("review_id") or "")):
        add("review_id_invalid", "review_id", "review_id must be a safe 3-128 character artifact identifier")
    source = packet.get("source") or {}
    if source.get("kind") not in SOURCE_KINDS:
        add("source_kind_invalid", "source.kind", "source kind must be human, ai, or tool")
    if source.get("retention") not in RETENTION_MODES:
        add("retention_invalid", "source.retention", "source retention must be copy, reference, or hash_only")
    if not re.fullmatch(r"[0-9a-f]{64}", str(source.get("sha256") or "")):
        add("source_hash_invalid", "source.sha256", "source requires a lowercase SHA-256")
    if source.get("retention") == "reference" and not source.get("locator"):
        add("source_reference_missing", "source.locator", "reference retention requires a locator")
    target = packet.get("target") or {}
    if not target.get("repository") or not re.fullmatch(r"[0-9a-f]{40}", str(target.get("commit") or "")):
        add("target_unverifiable", "target", "repository and full commit SHA are required")
    for index, finding in enumerate(packet.get("findings") or []):
        path = f"findings[{index}]"
        if finding.get("verification", {}).get("state") not in VERIFICATION_STATES:
            add("verification_state_invalid", path + ".verification.state", "unsupported verification state")
        disposition = finding.get("disposition", {}).get("state")
        if final and disposition not in FINAL_DISPOSITIONS:
            add("disposition_pending", path + ".disposition.state", "final packets require a disposition")
    return errors
```

- [ ] **Step 4: Run the GREEN slice**

Run:

```bash
python3 -m unittest tests.test_review_intake.SourceAndPacketTests -v
```

Expected: all tests pass.

- [ ] **Step 5: Commit the core contract**

```bash
git add scripts/review_intake.py tests/test_review_intake.py
git commit -m "feat: add review intake packet model" -m "Issue: 089-verified-code-review-intake-and-remediation-routing"
```

## Task 2: Manual, GitHub, CodeQL, SARIF, And Lazy Adapter Selection

**Files:**
- Create: `scripts/project_review.py`
- Create: `tests/test_project_review.py`

**Interfaces:** Consumes structured manual findings, GitHub `reviewThreads` snapshots, or SARIF 2.1 JSON. Produces only raw finding dictionaries accepted by `review_intake.new_packet` plus an `adapter_run` record.

- [ ] **Step 1: Write failing adapter tests**

```python
import unittest
from scripts import project_review as pr


class SourceAdapterTests(unittest.TestCase):
    def test_github_adapter_keeps_only_unresolved_current_threads(self):
        payload = {"threads": [
            {"id": "T1", "isResolved": False, "isOutdated": False, "path": "src/a.py", "line": 8, "comments": [{"body": "Validate input", "author": {"login": "reviewer"}}]},
            {"id": "T2", "isResolved": True, "isOutdated": False, "path": "src/b.py", "line": 9, "comments": [{"body": "Done", "author": {"login": "reviewer"}}]},
        ]}
        findings = pr.adapt_github_threads(payload)
        self.assertEqual([item["rule_id"] for item in findings], ["github-thread:T1"])
        self.assertEqual(findings[0]["source_author"]["identity"], "reviewer")

    def test_sarif_adapter_preserves_rule_and_partial_fingerprint(self):
        payload = {"runs": [{"tool": {"driver": {"name": "scanner", "version": "1", "rules": []}}, "results": [{"ruleId": "SEC-1", "message": {"text": "Unsafe input"}, "partialFingerprints": {"primaryLocationLineHash": "abc"}, "locations": [{"physicalLocation": {"artifactLocation": {"uri": "src/a.py"}, "region": {"startLine": 4}}}]}]}]}
        finding = pr.adapt_sarif(payload)[0]
        self.assertEqual(finding["rule_id"], "SEC-1")
        self.assertEqual(finding["provider_fingerprint"], "abc")

    def test_codeql_adapter_preserves_alert_disposition_history(self):
        payload = {"alerts": [{"number": 7, "state": "dismissed", "dismissed_reason": "false positive", "dismissed_comment": "sanitized test fixture", "dismissed_by": {"login": "security-owner"}, "dismissed_at": "2026-07-16T00:00:00Z", "rule": {"id": "js/xss", "description": "Unsafe output", "security_severity_level": "high"}, "tool": {"name": "CodeQL", "version": "2"}, "most_recent_instance": {"location": {"path": "src/view.js", "start_line": 12}}}]}
        finding = pr.adapt_codeql_alerts(payload)[0]
        self.assertEqual(finding["provider_fingerprint"], "codeql-alert:7")
        self.assertEqual(finding["provider_evidence"]["dismissed_reason"], "false positive")
        self.assertEqual(finding["provider_evidence"]["kind"], "security")

    def test_l0_selects_no_review_adapters(self):
        result = pr.select_adapters(event="routine", adapter=None, changed_paths=[])
        self.assertEqual(result["invoked"], [])
        self.assertIn("l0_routine", result["reason_codes"])
```

- [ ] **Step 2: Run the RED slice**

```bash
python3 -m unittest tests.test_project_review.SourceAdapterTests -v
```

Expected: FAIL because `project_review.py` does not exist.

- [ ] **Step 3: Implement deterministic source adapters and selection**

Create `scripts/project_review.py` with imports and these exact pure functions before adding CLI behavior:

```python
#!/usr/bin/env python3
import argparse
import copy
import json
import sys
from datetime import date
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts import review_intake as ri

SENSITIVE_PARTS = {"auth", "permission", "payment", "billing", "secret", "upload", "deploy", ".github/workflows"}
SARIF_LEVEL_TO_SEVERITY = {"error": "high", "warning": "medium", "note": "low", "none": "low"}


def select_adapters(event, adapter, changed_paths, requires_plan=False, security_requested=False):
    invoked, skipped, reasons = [], [], []
    paths = [str(path).lower() for path in changed_paths]
    sensitive = any(any(part in path for part in SENSITIVE_PARTS) for path in paths)
    if event == "routine" and not any((adapter, sensitive, requires_plan, security_requested)):
        return {"invoked": [], "skipped": ["manual-review-document", "github-review", "security-review", "superpowers-review", "spec-kit"], "reason_codes": ["l0_routine"]}
    if adapter == "manual":
        invoked.extend(["manual-review-document", "superpowers-review"])
        reasons.append("manual_source")
    else:
        skipped.append("manual-review-document")
    if adapter == "github":
        invoked.extend(["github-review", "superpowers-review"])
        reasons.append("pr_threads_present")
    else:
        skipped.append("github-review")
    if adapter in {"sarif", "codeql"} or sensitive or security_requested:
        invoked.extend(["security-review", "superpowers-review"])
        reasons.append("security_payload" if adapter in {"sarif", "codeql"} else ("router_security_request" if security_requested else "sensitive_path"))
    else:
        skipped.append("security-review")
    if requires_plan:
        invoked.append("spec-kit")
        reasons.append("planning_required")
    else:
        skipped.append("spec-kit")
    return {"invoked": list(dict.fromkeys(invoked)), "skipped": list(dict.fromkeys(skipped)), "reason_codes": reasons}


def adapt_manual_findings(payload):
    findings = payload.get("findings") if isinstance(payload, dict) else payload
    if not isinstance(findings, list):
        raise ri.ReviewIntakeError("manual_findings_invalid", "manual adapter requires a findings list")
    return copy.deepcopy(findings)


def adapt_github_threads(payload):
    findings = []
    for thread in payload.get("threads", []):
        if thread.get("isResolved") or thread.get("isOutdated"):
            continue
        comment_field = thread.get("comments") or []
        comments = comment_field.get("nodes", []) if isinstance(comment_field, dict) else comment_field
        if not comments:
            continue
        comment = comments[-1]
        author = comment.get("author") or {}
        login = author.get("login", "unknown")
        author_kind = "ai" if author.get("type") == "Bot" or login.endswith("[bot]") else "human"
        findings.append({
            "rule_id": f"github-thread:{thread.get('id')}",
            "observation": str(comment.get("body") or "").strip(),
            "recommendation": "",
            "root_cause_hypothesis": "",
            "locations": [{"path": thread.get("path"), "line": thread.get("line"), "anchor": thread.get("diffSide") or ""}],
            "source_author": {"kind": author_kind, "identity": login},
            "provider_evidence": {"kind": "review", "format": "github-thread", "id": thread.get("id"), "resolved": False, "outdated": False},
        })
    return findings


def adapt_sarif(payload):
    findings = []
    for run in payload.get("runs", []):
        driver = (run.get("tool") or {}).get("driver") or {}
        for result in run.get("results", []):
            location = (((result.get("locations") or [{}])[0].get("physicalLocation") or {}))
            artifact = location.get("artifactLocation") or {}
            region = location.get("region") or {}
            partials = result.get("partialFingerprints") or {}
            raw_level = str((result.get("properties") or {}).get("severity") or result.get("level") or "error").lower()
            severity = raw_level if raw_level in ri.SEVERITIES else SARIF_LEVEL_TO_SEVERITY.get(raw_level, "high")
            findings.append({
                "rule_id": result.get("ruleId"),
                "observation": (result.get("message") or {}).get("text", ""),
                "recommendation": "",
                "root_cause_hypothesis": "",
                "locations": [{"path": artifact.get("uri"), "line": region.get("startLine"), "anchor": result.get("ruleId") or ""}],
                "severity": severity,
                "source_author": {"kind": "tool", "identity": driver.get("name", "unknown"), "version": driver.get("version")},
                "provider_fingerprint": partials.get("primaryLocationLineHash") or next(iter(partials.values()), None),
                "provider_evidence": {"kind": "security", "format": "sarif", "tool": driver.get("name"), "version": driver.get("version")},
            })
    return findings


def adapt_codeql_alerts(payload):
    alerts = payload.get("alerts") if isinstance(payload, dict) else payload
    findings = []
    for alert in alerts or []:
        rule = alert.get("rule") or {}
        instance = alert.get("most_recent_instance") or {}
        location = instance.get("location") or {}
        severity = str(rule.get("security_severity_level") or rule.get("severity") or "high").lower()
        severity = severity if severity in ri.SEVERITIES else SARIF_LEVEL_TO_SEVERITY.get(severity, "high")
        number = alert.get("number")
        findings.append({
            "rule_id": rule.get("id"),
            "observation": rule.get("description") or rule.get("name") or "Code scanning alert",
            "recommendation": "",
            "root_cause_hypothesis": "",
            "locations": [{"path": location.get("path"), "line": location.get("start_line"), "anchor": rule.get("id") or ""}],
            "severity": severity,
            "source_author": {"kind": "tool", "identity": (alert.get("tool") or {}).get("name", "CodeQL"), "version": (alert.get("tool") or {}).get("version")},
            "provider_fingerprint": f"codeql-alert:{number}",
            "provider_evidence": {"kind": "security", "format": "codeql-alert", "number": number, "state": alert.get("state"), "dismissed_reason": alert.get("dismissed_reason"), "dismissed_comment": alert.get("dismissed_comment"), "dismissed_by": (alert.get("dismissed_by") or {}).get("login"), "dismissed_at": alert.get("dismissed_at")},
        })
    return findings
```

- [ ] **Step 4: Run adapter tests**

```bash
python3 -m unittest tests.test_project_review.SourceAdapterTests -v
```

Expected: all adapter tests pass.

- [ ] **Step 5: Commit adapter normalization**

```bash
git add scripts/project_review.py tests/test_project_review.py
git commit -m "feat: adapt review and security sources" -m "Issue: 089-verified-code-review-intake-and-remediation-routing"
```

## Task 3: Verification, Router Decisions, And Deterministic Policy

**Files:**
- Modify: `scripts/review_intake.py`
- Modify: `tests/test_review_intake.py`

**Interfaces:** A decision input names one finding, supplies complete verification evidence, a proposed final disposition, actor provenance, and optional human approval. Policy returns stable rule IDs and the required lane/verifier/human constraints.

- [ ] **Step 1: Write failing policy and decision tests**

```python
class DecisionPolicyTests(unittest.TestCase):
    def test_no_risk_stays_unverified_without_tests_and_boundaries(self):
        finding = make_packet(no_risk_claim=True)["findings"][0]
        policy = ri.evaluate_policy(finding)
        self.assertIn("no_risk_evidence_missing", policy["reason_codes"])

    def test_ai_cannot_reject_high_risk_without_human_approval(self):
        packet = make_packet(severity="high")
        decision = decision_for("F-001", disposition="reject", actor_kind="ai", human_approved=False)
        with self.assertRaises(ri.ReviewIntakeError) as caught:
            ri.apply_decision(packet, decision)
        self.assertEqual(caught.exception.code, "high_risk_reject_requires_human")

    def test_confirmed_sensitive_finding_routes_security(self):
        packet = make_packet(path="src/auth/token.py")
        updated = ri.apply_decision(packet, decision_for("F-001", disposition="accept", actor_kind="human", human_approved=True))
        finding = updated["findings"][0]
        self.assertEqual(finding["route"]["lane"], "security")
        self.assertEqual(finding["route"]["CognitiveDemand"], "deep")

    def test_target_commit_mismatch_requires_reverification(self):
        with self.assertRaises(ri.ReviewIntakeError) as caught:
            ri.apply_decision(make_packet(), decision_for("F-001", target_commit="c" * 40))
        self.assertEqual(caught.exception.code, "target_commit_mismatch")

    def test_required_verifier_must_be_independent(self):
        packet = make_packet(severity="medium")
        decision = decision_for("F-001")
        decision["verification"]["verifier"] = {"kind": "human", "identity": "source-reviewer", "role": "verifier"}
        with self.assertRaises(ri.ReviewIntakeError) as caught:
            ri.apply_decision(packet, decision)
        self.assertEqual(caught.exception.code, "verifier_not_independent")

    def test_changed_disposition_keeps_append_only_history(self):
        packet = ri.apply_decision(make_packet(severity="low"), decision_for("F-001", disposition="defer", verification_state="inconclusive"))
        packet = ri.apply_decision(packet, decision_for("F-001", disposition="accept", verification_state="confirmed"))
        self.assertEqual([event["state"] for event in packet["findings"][0]["decision_history"]], ["defer", "accept"])
```

- [ ] **Step 2: Run the RED slice**

```bash
python3 -m unittest tests.test_review_intake.DecisionPolicyTests -v
```

Expected: FAIL because policy and decision functions are missing.

- [ ] **Step 3: Implement policy evaluation and atomic decision application**

Append these exact contracts to `scripts/review_intake.py`; helper functions must deep-copy before mutation.

```python
SENSITIVE_PATH_PARTS = ("auth", "permission", "payment", "billing", "secret", "upload", "deploy", ".github/workflows")


def evaluate_policy(finding):
    paths = [item["path"].lower() for item in finding.get("locations", [])]
    severity = finding.get("risk", {}).get("severity", "medium")
    sensitive = any(any(part in path for part in SENSITIVE_PATH_PARTS) for path in paths)
    security_signal = sensitive or finding.get("router", {}).get("classification") == "security" or finding.get("provider_evidence", {}).get("kind") == "security"
    reasons = []
    if sensitive:
        reasons.append("sensitive_path")
    if severity in {"high", "critical"}:
        reasons.append("elevated_severity")
    verification = finding.get("verification") or {}
    if finding.get("risk", {}).get("no_risk_claim") and not (verification.get("tests") and verification.get("import_boundaries")):
        reasons.append("no_risk_evidence_missing")
    lane = "security" if security_signal else (
        "pre_release" if severity in {"high", "critical"} or finding.get("risk", {}).get("release_impact") == "blocking" else "post_release_refactor"
    )
    demand = "deep" if lane == "security" or verification.get("architecture") else ("balanced" if lane == "pre_release" else "fast")
    return {
        "lane": lane,
        "CognitiveDemand": demand,
        "requires_verifier": severity in {"medium", "high", "critical"} or finding.get("router", {}).get("confidence") != "high",
        "requires_human_for_reject": severity in {"high", "critical"} or lane == "security",
        "reason_codes": reasons,
    }


def _provenance_key(actor):
    actor = actor or {}
    return (actor.get("kind"), actor.get("identity"), actor.get("run_id"))


def apply_decision(packet, decision):
    updated = copy.deepcopy(packet)
    if decision.get("target_commit") != updated.get("target", {}).get("commit"):
        raise ReviewIntakeError("target_commit_mismatch", "decision target commit differs from the reviewed commit")
    finding = next((item for item in updated["findings"] if item["id"] == decision.get("finding_id")), None)
    if finding is None:
        raise ReviewIntakeError("finding_not_found", "decision finding does not exist")
    verification = copy.deepcopy(decision.get("verification") or {})
    state = verification.get("state")
    if state not in VERIFICATION_STATES:
        raise ReviewIntakeError("verification_state_invalid", "decision requires a valid verification state")
    verification.setdefault("verifier", None)
    for key in ("files_checked", "reproduction", "tests", "architecture", "import_boundaries", "contradictions"):
        verification.setdefault(key, [])
    verification.setdefault("verified_at", date.today().isoformat())
    disposition = decision.get("disposition")
    if disposition not in FINAL_DISPOSITIONS:
        raise ReviewIntakeError("disposition_invalid", "decision requires a final disposition")
    rationale = str(decision.get("rationale") or "").strip()
    if not rationale:
        raise ReviewIntakeError("disposition_rationale_missing", "every disposition requires rationale")
    if disposition == "accept" and state != "confirmed":
        raise ReviewIntakeError("accept_requires_evidence", "accept requires confirmed evidence")
    if disposition == "partial_accept" and state not in {"confirmed", "inconclusive"}:
        raise ReviewIntakeError("partial_accept_requires_evidence", "partial accept requires confirmed or inconclusive evidence")
    finding["verification"] = verification
    policy = evaluate_policy(finding)
    verifier = verification.get("verifier") or {}
    if policy["requires_verifier"]:
        if verifier.get("role") != "verifier" or not verifier.get("identity"):
            raise ReviewIntakeError("verifier_missing", "policy requires explicit verifier provenance")
        blocked_keys = {_provenance_key(finding.get("source_author")), _provenance_key(finding.get("router", {}).get("actor"))}
        if _provenance_key(verifier) in {key for key in blocked_keys if any(key)}:
            raise ReviewIntakeError("verifier_not_independent", "verifier must differ from source reviewer and Router run")
    actor = copy.deepcopy(decision.get("actor") or {"kind": "unknown", "identity": "unknown"})
    human_approved = bool(decision.get("human_approved"))
    if disposition == "reject" and policy["requires_human_for_reject"] and not human_approved:
        raise ReviewIntakeError("high_risk_reject_requires_human", "high-risk rejection requires human approval")
    if finding["risk"].get("no_risk_claim"):
        finding["risk"]["no_risk_state"] = "verified" if verification["tests"] and verification["import_boundaries"] else "unverified"
    event = {"state": disposition, "rationale": rationale, "decided_by": actor, "decided_at": date.today().isoformat(), "human_approved": human_approved}
    finding.setdefault("decision_history", []).append(copy.deepcopy(event))
    finding["disposition"] = event
    finding["route"].update(lane=policy["lane"] if disposition in {"accept", "partial_accept"} else None, CognitiveDemand=policy["CognitiveDemand"] if disposition in {"accept", "partial_accept"} else None)
    finding["policy"] = policy
    updated["updated_at"] = date.today().isoformat()
    return updated
```

- [ ] **Step 4: Run all core tests**

```bash
python3 -m unittest tests.test_review_intake -v
```

Expected: all source, packet, policy, and decision tests pass.

- [ ] **Step 5: Commit verified decision policy**

```bash
git add scripts/review_intake.py tests/test_review_intake.py
git commit -m "feat: verify and route review findings" -m "Issue: 089-verified-code-review-intake-and-remediation-routing"
```

## Task 4: Deduplicated Remediation Candidates And Trace Matrix

**Files:**
- Modify: `scripts/review_intake.py`
- Modify: `tests/test_review_intake.py`

- [ ] **Step 1: Write failing candidate tests**

```python
def finalized_packet(dispositions):
    raw_findings = [{
        "observation": f"Observation {index}",
        "recommendation": f"Recommendation {index}",
        "locations": [{"path": f"src/file_{index}.py", "line": index, "anchor": f"fn_{index}"}],
        "severity": "low",
        "release_impact": "non_blocking",
    } for index in range(1, len(dispositions) + 1)]
    packet = make_packet(raw_findings=raw_findings)
    for index, disposition in enumerate(dispositions, 1):
        verification_state = "contradicted" if disposition == "reject" else ("inconclusive" if disposition in {"partial_accept", "defer"} else "confirmed")
        packet = ri.apply_decision(
            packet,
            decision_for(f"F-{index:03d}", disposition=disposition, verification_state=verification_state),
        )
    return packet


def accepted_packet():
    return finalized_packet(["accept"])


class CandidateRoutingTests(unittest.TestCase):
    def test_only_accept_and_partial_create_candidates(self):
        packet = finalized_packet(["accept", "partial_accept", "defer", "reject"])
        candidates = ri.build_candidates(packet)["candidates"]
        self.assertEqual(len(candidates), 2)

    def test_exact_fingerprint_links_existing_candidate(self):
        packet = accepted_packet()
        existing = [{"id": "RC-001", "fingerprint": packet["findings"][0]["fingerprint"], "issue_id": "123-existing"}]
        result = ri.build_candidates(packet, existing_candidates=existing)
        self.assertEqual(result["candidates"][0]["state"], "linked_existing")
        self.assertEqual(result["candidates"][0]["existing_issue_ids"], ["123-existing"])

    def test_trace_is_bidirectional(self):
        result = ri.build_candidates(accepted_packet())
        candidate = result["candidates"][0]
        self.assertEqual(result["trace"]["finding_to_candidates"]["F-001"], [candidate["id"]])
        self.assertEqual(result["trace"]["candidate_to_findings"][candidate["id"]], ["F-001"])

    def test_explicit_proposals_support_grouping_and_splitting(self):
        packet = finalized_packet(["accept", "accept"])
        proposals = [
            {"title": "Shared remediation", "finding_ids": ["F-001", "F-002"]},
            {"title": "Separate hardening", "finding_ids": ["F-001"]},
        ]
        trace = ri.build_candidates(packet, proposals=proposals)["trace"]
        self.assertEqual(len(trace["finding_to_candidates"]["F-001"]), 2)
        self.assertEqual(len(trace["finding_to_candidates"]["F-002"]), 1)
```

- [ ] **Step 2: Run the RED slice**

```bash
python3 -m unittest tests.test_review_intake.CandidateRoutingTests -v
```

Expected: FAIL because `build_candidates` is missing.

- [ ] **Step 3: Implement candidate generation without GitHub writes**

```python
def build_candidates(packet, existing_candidates=(), proposals=()):
    existing_by_fingerprint = {item.get("fingerprint"): item for item in existing_candidates if item.get("fingerprint")}
    accepted = {item["id"]: item for item in packet.get("findings", []) if item.get("disposition", {}).get("state") in {"accept", "partial_accept"}}
    candidate_specs = list(proposals) or [
        {"title": finding["recommendation"] or finding["observation"], "finding_ids": [finding_id]}
        for finding_id, finding in accepted.items()
    ]
    candidates = []
    finding_to_candidates = {finding_id: [] for finding_id in accepted}
    candidate_to_findings = {}
    demand_rank = {"fast": 0, "balanced": 1, "deep": 2}
    priority_rank = {"p2": 0, "p1": 1, "p0": 2}
    for spec in candidate_specs:
        finding_ids = list(dict.fromkeys(spec.get("finding_ids") or []))
        if not finding_ids or any(finding_id not in accepted for finding_id in finding_ids):
            raise ReviewIntakeError("candidate_finding_invalid", "candidate proposals must reference accepted findings")
        findings = [accepted[finding_id] for finding_id in finding_ids]
        fingerprints = sorted(finding["fingerprint"] for finding in findings)
        fingerprint = fingerprints[0] if len(fingerprints) == 1 else "sha256:" + _sha256_bytes("|".join(fingerprints).encode("utf-8"))
        candidate_id = f"{packet['review_id']}-RC-{len(candidates) + 1:03d}"
        existing = existing_by_fingerprint.get(fingerprint)
        lanes = {finding["route"]["lane"] for finding in findings}
        lane = "security" if "security" in lanes else ("pre_release" if "pre_release" in lanes else "post_release_refactor")
        demand = max((finding["route"]["CognitiveDemand"] for finding in findings), key=lambda value: demand_rank[value])
        priorities = ["p0" if finding["risk"]["severity"] == "critical" else ("p1" if finding["route"]["lane"] in {"security", "pre_release"} else "p2") for finding in findings]
        priority = max(priorities, key=lambda value: priority_rank[value])
        title = str(spec.get("title") or findings[0]["recommendation"] or findings[0]["observation"])
        existing_issue_ids = list(existing.get("existing_issue_ids") or []) if existing else []
        if existing and existing.get("issue_id") and existing["issue_id"] not in existing_issue_ids:
            existing_issue_ids.append(existing["issue_id"])
        candidate = {
            "id": candidate_id,
            "state": "linked_existing" if existing else "candidate",
            "title": title[:100],
            "problem": "\n".join(finding["observation"] for finding in findings),
            "scope": sorted({location["path"] for finding in findings for location in finding.get("locations", [])}),
            "acceptance_evidence": {finding["id"]: copy.deepcopy(finding["verification"]) for finding in findings},
            "priority": priority,
            "dependencies": list(spec.get("dependencies") or sorted({dependency for finding in findings for dependency in (finding.get("router", {}).get("dependency_hints") or [])})),
            "CognitiveDemand": demand,
            "routing_reason_codes": sorted({reason for finding in findings for reason in ((finding.get("router", {}).get("reason_codes") or []) + (finding.get("policy", {}).get("reason_codes") or []))}),
            "lane": lane,
            "release_impact": "blocking" if any(finding["risk"]["release_impact"] == "blocking" for finding in findings) else "non_blocking",
            "finding_ids": finding_ids,
            "fingerprint": fingerprint,
            "existing_issue_ids": existing_issue_ids,
            "linked_candidate_id": existing.get("id") if existing else None,
            "overlap_hints": [],
            "next_command": f"product:issue {existing_issue_ids[0]}" if existing_issue_ids else ("product:review --intake" if existing else "product:issue"),
        }
        candidates.append(candidate)
        for finding_id in finding_ids:
            finding_to_candidates[finding_id].append(candidate_id)
        candidate_to_findings[candidate_id] = finding_ids
    if any(not candidate_ids for candidate_ids in finding_to_candidates.values()):
        raise ReviewIntakeError("accepted_finding_unmapped", "every accepted finding must map to a candidate")
    return {"candidates": candidates, "trace": {"finding_to_candidates": finding_to_candidates, "candidate_to_findings": candidate_to_findings}}
```

- [ ] **Step 4: Run candidate and full core tests**

```bash
python3 -m unittest tests.test_review_intake -v
```

Expected: all tests pass.

- [ ] **Step 5: Commit candidate routing**

```bash
git add scripts/review_intake.py tests/test_review_intake.py
git commit -m "feat: generate review remediation candidates" -m "Issue: 089-verified-code-review-intake-and-remediation-routing"
```

## Task 5: Packet Persistence, Korean Projection, Decision Updates, And CLI

**Files:**
- Modify: `scripts/project_review.py`
- Modify: `tests/test_project_review.py`
- Create: `templates/reviews/review-intake.json`
- Create: `templates/reviews/review-summary.ko.md`
- Create: `templates/reviews/review-candidates.md`

- [ ] **Step 1: Write failing write-safety and rendering tests**

```python
import argparse
import json
import tempfile
from pathlib import Path

from scripts import project_review as pr
from scripts import review_intake as ri


def sample_final_packet(review_id="review-1"):
    packet = ri.new_packet(
        review_id=review_id,
        source={"kind": "human", "provider": "external", "identity": "source-reviewer", "received_at": "2026-07-16", "retention": "hash_only", "sha256": "a" * 64},
        target={"repository": "github.com/o/r", "commit": "b" * 40, "base_branch": "main"},
        trigger={"event": "manual_intake", "reason_codes": ["external_review_received"]},
        adapter_run={"invoked": ["manual-review-document", "superpowers-review"], "skipped": ["github-review", "security-review", "spec-kit"], "reason_codes": ["manual_source"]},
        raw_findings=[{"observation": "Observed behavior", "recommendation": "Fix behavior", "locations": [{"path": "src/a.py", "line": 1, "anchor": "run"}], "severity": "low", "release_impact": "non_blocking"}],
    )
    decision = {
        "finding_id": "F-001", "target_commit": "b" * 40,
        "verification": {"state": "confirmed", "verifier": {"kind": "tool", "identity": "verifier", "role": "verifier", "run_id": "v1"}, "files_checked": ["src/a.py"], "reproduction": ["fixture"], "tests": ["test_a"], "architecture": [], "import_boundaries": ["src/a.py -> stdlib"], "contradictions": [], "verified_at": "2026-07-16"},
        "disposition": "accept", "rationale": "Reproduced and tested.",
        "actor": {"kind": "human", "identity": "owner", "run_id": "d1"}, "human_approved": True,
    }
    return ri.apply_decision(packet, decision)


def new_args(source, findings_file, write=False):
    return argparse.Namespace(
        review_id="review-preview", adapter="manual", source=str(source), findings_file=str(findings_file),
        source_kind="human", provider="external", source_identity="unknown", received_at="2026-07-16", retention="reference", source_hash=None,
        target_repository="github.com/o/r", target_commit="b" * 40, base_branch="main", write=write,
    )


class ArtifactAndCliTests(unittest.TestCase):
    def test_write_packet_creates_json_korean_summary_and_queue(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = pr.write_review_artifacts(root, sample_final_packet())
            self.assertTrue(paths["packet"].is_file())
            self.assertIn("검증 상태", paths["summary"].read_text(encoding="utf-8"))
            self.assertIn("CognitiveDemand", paths["candidates"].read_text(encoding="utf-8"))

    def test_dry_run_does_not_create_workspace_reviews(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source.md"
            source.write_text("external source", encoding="utf-8")
            findings = root / "findings.json"
            findings.write_text(json.dumps({"findings": [{"observation": "Observed behavior", "locations": [{"path": "src/a.py", "line": 1, "anchor": "run"}]}]}), encoding="utf-8")
            result = pr.run_new_intake(root, new_args(source, findings, write=False))
            self.assertEqual(result["action"], "preview")
            self.assertFalse((root / "workspace" / "reviews").exists())

    def test_hash_mismatch_blocks_decision_update(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_path = root / "source.md"
            source_path.write_text("original", encoding="utf-8")
            packet = sample_final_packet()
            packet["source"] = ri.build_source_record("human", "external", "reviewer", "2026-07-16", "reference", locator=source_path)
            reviews = root / "workspace" / "reviews"
            reviews.mkdir(parents=True)
            (reviews / "review-1.json").write_text(json.dumps(packet), encoding="utf-8")
            decisions = root / "decisions.json"
            decisions.write_text(json.dumps({"decisions": []}), encoding="utf-8")
            source_path.write_text("changed", encoding="utf-8")
            with self.assertRaises(ri.ReviewIntakeError) as caught:
                pr.apply_decisions_to_path(root, "review-1", decisions, write=True)
            self.assertEqual(caught.exception.code, "source_integrity_mismatch")

    def test_candidate_queue_retains_other_review_packets(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pr.write_review_artifacts(root, sample_final_packet("review-one"))
            paths = pr.write_review_artifacts(root, sample_final_packet("review-two"))
            queue = paths["candidates"].read_text(encoding="utf-8")
            self.assertIn("review-one-RC-001", queue)
            self.assertIn("review-two-RC-001", queue)
```

- [ ] **Step 2: Run the RED slice**

```bash
python3 -m unittest tests.test_project_review.ArtifactAndCliTests -v
```

Expected: FAIL because persistence, rendering, and CLI functions are missing.

- [ ] **Step 3: Implement artifact rendering and atomic writes**

Add to `scripts/project_review.py`:

```python
def render_summary_ko(packet):
    lines = [f"# 코드리뷰 접수: {packet['review_id']}", "", "## 출처", "", f"- 유형: `{packet['source']['kind']}`", f"- 제공자: `{packet['source']['provider']}`", f"- 보관: `{packet['source']['retention']}`", f"- 대상: `{packet['target']['repository']}@{packet['target']['commit'][:12]}`", "", "## Finding", ""]
    for finding in packet["findings"]:
        lines.extend([
            f"### {finding['id']} — {finding['risk']['severity']}", "",
            f"- 관찰: {finding['observation']}",
            f"- 권장: {finding['recommendation'] or '없음'}",
            f"- 원인 가설: {finding['root_cause_hypothesis'] or '없음'}",
            f"- 리뷰어 확신도: `{finding['reviewer_confidence']}`",
            f"- 검증 상태: `{finding['verification']['state']}`",
            f"- 판정: `{finding['disposition']['state']}`",
            f"- 경로: `{finding['route']['lane'] or '미정'}`",
            "",
        ])
    return "\n".join(lines).rstrip() + "\n"


def render_candidate_queue(candidates):
    lines = ["# Review Candidates", ""]
    for item in candidates:
        overlap = ", ".join(hint["issue_id"] for hint in item.get("overlap_hints", [])) or "없음"
        reasons = ", ".join(item.get("routing_reason_codes", [])) or "없음"
        lines.extend([f"## {item['id']} — {item['title']}", "", f"- State: `{item['state']}`", f"- Lane: `{item['lane']}`", f"- CognitiveDemand: `{item['CognitiveDemand']}`", f"- Findings: {', '.join(item['finding_ids'])}", f"- Routing reasons: {reasons}", f"- Overlap hints: {overlap}", f"- Next: `{item['next_command']}`", ""])
    return "\n".join(lines).rstrip() + "\n"


def _write_text_atomic(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)


def _packet_files(root):
    return sorted((Path(root).resolve() / "workspace" / "reviews").glob("*.json"))


def _existing_candidates(root, exclude_review_id):
    candidates = []
    for path in _packet_files(root):
        try:
            packet = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if packet.get("review_id") != exclude_review_id:
            candidates.extend(packet.get("candidates") or [])
    return candidates


def _add_overlap_hints(root, candidates):
    from scripts.project_intake import find_related_issues
    enriched = copy.deepcopy(candidates)
    for candidate in enriched:
        candidate["overlap_hints"] = find_related_issues(root, candidate["title"] + "\n" + candidate["problem"])[:3]
    return enriched


def write_review_artifacts(root, packet):
    root = Path(root).resolve()
    reviews = root / "workspace" / "reviews"
    candidate_result = ri.build_candidates(packet, existing_candidates=_existing_candidates(root, packet["review_id"]))
    packet = copy.deepcopy(packet)
    packet["candidates"] = _add_overlap_hints(root, candidate_result["candidates"])
    packet["trace"] = candidate_result["trace"]
    packet_path = reviews / f"{packet['review_id']}.json"
    summary_path = reviews / f"{packet['review_id']}.md"
    candidate_path = root / "workspace" / "review-candidates.md"
    _write_text_atomic(packet_path, json.dumps(packet, ensure_ascii=False, indent=2) + "\n")
    _write_text_atomic(summary_path, render_summary_ko(packet))
    all_candidates = _existing_candidates(root, packet["review_id"]) + packet["candidates"]
    _write_text_atomic(candidate_path, render_candidate_queue(all_candidates))
    return {"packet": packet_path, "summary": summary_path, "candidates": candidate_path}
```

- [ ] **Step 4: Implement CLI operations with preview as the default**

Add the following orchestration functions, parser construction, JSON output, and `main`. `--new`, `--apply-decisions`, and `--validate` must be a required mutually exclusive group. `--write` is optional and false by default. Before applying decisions to a referenced local source, recompute SHA-256 and raise `source_integrity_mismatch` if it differs.

```python
def _load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def run_new_intake(root, args):
    required = {"review_id": args.review_id, "adapter": args.adapter, "source": args.source, "source_kind": args.source_kind, "target_repository": args.target_repository, "target_commit": args.target_commit}
    missing = [name for name, value in required.items() if not value]
    if missing:
        raise ri.ReviewIntakeError("usage_error", "missing required arguments: " + ", ".join(missing))
    source_path = Path(args.source)
    copied_text = source_path.read_text(encoding="utf-8") if args.retention == "copy" and source_path.is_file() else None
    source = ri.build_source_record(
        args.source_kind, args.provider, args.source_identity, args.received_at, args.retention,
        locator=args.source, copied_text=copied_text, source_hash=args.source_hash,
    )
    if args.adapter == "manual":
        if not args.findings_file:
            raise ri.ReviewIntakeError("manual_findings_missing", "manual adapter requires --findings-file")
        raw_findings = adapt_manual_findings(_load_json(args.findings_file))
    elif args.adapter == "github":
        raw_findings = adapt_github_threads(_load_json(args.source))
    elif args.adapter == "sarif":
        raw_findings = adapt_sarif(_load_json(args.source))
    else:
        raw_findings = adapt_codeql_alerts(_load_json(args.source))
    trigger_event = {"manual": "manual_intake", "github": "pr_review", "sarif": "security_alert", "codeql": "security_alert"}[args.adapter]
    requires_plan = any((item.get("router") or {}).get("requires_plan") for item in raw_findings)
    security_requested = any((item.get("router") or {}).get("classification") == "security" for item in raw_findings)
    adapter_run = select_adapters(
        trigger_event, args.adapter,
        [location.get("path", "") for item in raw_findings for location in item.get("locations", [])],
        requires_plan=requires_plan, security_requested=security_requested,
    )
    packet = ri.new_packet(
        args.review_id, source,
        {"repository": args.target_repository, "commit": args.target_commit, "base_branch": args.base_branch},
        {"event": trigger_event, "reason_codes": ["review_received"]},
        adapter_run, raw_findings,
    )
    if not args.write:
        return {"action": "preview", "packet": packet}
    paths = write_review_artifacts(root, packet)
    return {"action": "written", "packet": packet, "paths": {key: str(value) for key, value in paths.items()}}


def _verify_reference_integrity(packet):
    source = packet.get("source") or {}
    locator = Path(str(source.get("locator") or ""))
    if source.get("retention") == "reference" and locator.is_file():
        actual = ri.sha256_file(locator)
        if actual != source.get("sha256"):
            raise ri.ReviewIntakeError("source_integrity_mismatch", "referenced review source changed after intake")


def apply_decisions_to_path(root, review_id, decisions_path, write=False):
    packet_path = Path(root).resolve() / "workspace" / "reviews" / f"{review_id}.json"
    packet = _load_json(packet_path)
    _verify_reference_integrity(packet)
    decisions = _load_json(decisions_path).get("decisions") or []
    for decision in decisions:
        packet = ri.apply_decision(packet, decision)
    result = {"action": "preview", "packet": packet}
    if write:
        paths = write_review_artifacts(root, packet)
        result = {"action": "written", "packet": packet, "paths": {key: str(value) for key, value in paths.items()}}
    return result


def build_parser():
    parser = argparse.ArgumentParser(description="Verified ModuFlow code-review intake")
    parser.add_argument("project_path", nargs="?", default=".")
    operation = parser.add_mutually_exclusive_group(required=True)
    operation.add_argument("--new", action="store_true")
    operation.add_argument("--apply-decisions")
    operation.add_argument("--validate")
    parser.add_argument("--review-id")
    parser.add_argument("--adapter", choices=["manual", "github", "codeql", "sarif"])
    parser.add_argument("--source")
    parser.add_argument("--findings-file")
    parser.add_argument("--source-kind", choices=sorted(ri.SOURCE_KINDS))
    parser.add_argument("--provider", default="unknown")
    parser.add_argument("--source-identity", default="unknown")
    parser.add_argument("--received-at", default=date.today().isoformat())
    parser.add_argument("--retention", choices=sorted(ri.RETENTION_MODES), default="reference")
    parser.add_argument("--source-hash")
    parser.add_argument("--target-repository")
    parser.add_argument("--target-commit")
    parser.add_argument("--base-branch", default="main")
    parser.add_argument("--final", action="store_true")
    parser.add_argument("--write", action="store_true")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    root = Path(args.project_path).resolve()
    try:
        if args.new:
            result = run_new_intake(root, args)
        elif args.apply_decisions:
            if not args.review_id:
                raise ri.ReviewIntakeError("usage_error", "--apply-decisions requires --review-id")
            result = apply_decisions_to_path(root, args.review_id, args.apply_decisions, write=args.write)
        else:
            packet = _load_json(args.validate)
            errors = ri.validate_packet(packet, final=args.final)
            result = {"action": "validated", "valid": not errors, "errors": errors}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result.get("valid", True) else 1
    except (OSError, json.JSONDecodeError, ri.ReviewIntakeError) as exc:
        code = getattr(exc, "code", "review_intake_error")
        print(json.dumps({"action": "error", "reason_code": code, "error": str(exc)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 5: Add valid generic templates**

Create `templates/reviews/review-intake.json` as a valid non-sensitive starter:

```json
{
  "schema": "moduflow.review-intake.v1",
  "review_id": "example-review",
  "source": {
    "kind": "human",
    "provider": "example-provider",
    "identity": "unknown",
    "received_at": "1970-01-01",
    "retention": "hash_only",
    "sha256": "0000000000000000000000000000000000000000000000000000000000000000"
  },
  "target": {
    "repository": "example.invalid/owner/repository",
    "commit": "0000000000000000000000000000000000000000",
    "base_branch": "main"
  },
  "trigger": {"event": "manual_intake", "reason_codes": ["example"]},
  "adapter_run": {"invoked": [], "skipped": [], "reason_codes": ["example"]},
  "findings": [],
  "candidates": [],
  "trace": {"finding_to_candidates": {}, "candidate_to_findings": {}},
  "updated_at": "1970-01-01"
}
```

Create `templates/reviews/review-summary.ko.md`:

```markdown
# 코드리뷰 접수: {{review_id}}

## 출처

- 유형: `{{source_kind}}`
- 제공자: `{{source_provider}}`
- 보관: `{{retention}}`
- 대상: `{{target_repository}}@{{target_commit_short}}`

## Finding

각 finding은 관찰, 권장, 원인 가설, 검증 상태, 판정, 개선 경로를 분리해 표시한다.
```

Create `templates/reviews/review-candidates.md`:

```markdown
# Review Candidates

각 후보는 state, lane, CognitiveDemand, finding IDs, overlap hints, next command를 표시한다.
```

Tests compare required headings/field names rather than byte-for-byte rendering.

- [ ] **Step 6: Run CLI and artifact tests**

```bash
python3 -m unittest tests.test_project_review -v
```

Expected: adapter, dry-run, write, update, hash-integrity, rendering, and CLI parser tests pass.

- [ ] **Step 7: Commit the local review artifact surface**

```bash
git add scripts/project_review.py tests/test_project_review.py templates/reviews
git commit -m "feat: persist verified review intake artifacts" -m "Issue: 089-verified-code-review-intake-and-remediation-routing"
```

## Task 6: Upstream Adapter Registry, Policy Overlay, Validation, And Command Routing

**Files:**
- Create: `adapters/github-review.yaml`
- Create: `adapters/security-review.yaml`
- Modify: `adapters/superpowers.yaml`
- Create: `overlays/review-policy.yaml`
- Modify: `vendor.lock.json`
- Modify: `scripts/validate_moduflow.py`
- Modify: `tests/test_validation_distribution.py`
- Modify: `commands/product-review.md`
- Modify: `skills/index/SKILL.md`

- [ ] **Step 1: Write failing package and command-surface tests**

Add a validator test that removes each new required file from a copied package fixture and expects it in `missing`. Add static assertions that `vendor.lock.json` contains `codex-github`, `adapters/superpowers.yaml` contains `receiving code review`, and `commands/product-review.md` contains `--intake`, Router AI, Verifier, and the no-GitHub-write boundary.

```python
def test_review_intake_surface_is_required(self):
    validator = load_module("validate_moduflow_review", "scripts/validate_moduflow.py")
    required = {
        "scripts/review_intake.py",
        "scripts/project_review.py",
        "adapters/github-review.yaml",
        "adapters/security-review.yaml",
        "overlays/review-policy.yaml",
        "templates/reviews/review-intake.json",
        "templates/reviews/review-summary.ko.md",
        "templates/reviews/review-candidates.md",
    }
    self.assertTrue(required.issubset(set(validator.REQUIRED_FILES)))
```

- [ ] **Step 2: Run the RED slice**

```bash
python3 -m unittest tests.test_validation_distribution -v
```

Expected: the new required-surface test fails.

- [ ] **Step 3: Add adapter metadata and policy IDs**

Create `adapters/github-review.yaml`:

```yaml
id: github-review
source: codex-github
source_url: local:codex-plugin/github
role: pull_request_review_source
moduflow_use:
  - pull request metadata
  - unresolved review threads
  - inline file and line anchors
  - resolved and outdated state
source_of_truth: git
reads:
  - GitHub pull request metadata through the connector
  - thread-aware GraphQL snapshots through gh
writes:
  - none by default
write_policy: Reply, resolve, review submission, and issue publication require an explicit separate user-approved GitHub action.
swap_policy: Replaceable if thread identity, resolution state, file anchors, reviewer provenance, and write safety remain explicit.
```

Create `adapters/security-review.yaml`:

```yaml
id: security-review
source: github-code-scanning
source_url: https://github.com/github/codeql-action # reference upstream
role: security_finding_source
moduflow_use:
  - CodeQL alert intake
  - SARIF result intake
  - stable rule and fingerprint mapping
  - severity, location, state, and dismissal evidence
source_of_truth: git
reads:
  - exported CodeQL alert JSON
  - SARIF 2.1 JSON
writes:
  - workspace/reviews/*.json
  - workspace/reviews/*.md
swap_policy: Replaceable if rule identity, fingerprint, severity, location, tool version, and disposition evidence remain explicit.
```

Update `adapters/superpowers.yaml` by adding `receiving code review` under `moduflow_use` and append this reviewed note without changing the existing upstream pin:

```yaml
  - receiving code review
```

```text
Issue 089 maps receiving-code-review into verify-before-implement evidence and disposition rules. Upstream skill files remain unchanged; ModuFlow owns only the adapter and packet contract.
```

`overlays/review-policy.yaml` must expose the exact policy IDs used in Python:

```yaml
id: review-policy-v1
default_retention: reference
lanes:
  - security
  - pre_release
  - post_release_refactor
rules:
  - sensitive_path
  - elevated_severity
  - no_risk_evidence_missing
  - high_risk_reject_requires_human
  - target_commit_mismatch
write_policy:
  local_packet_requires: --write
  github_write: explicit_external_workflow_only
```

- [ ] **Step 4: Register the installed GitHub plugin source**

Append this source object to `vendor.lock.json` without changing existing source order/content:

```json
{
  "id": "codex-github",
  "name": "Codex GitHub",
  "url": "local:codex-plugin/github",
  "type": "local-plugin",
  "pin": "0.1.8-2841cf9749ae",
  "role": "repository, pull-request thread, issue, CI, and publish workflow adapter"
}
```

- [ ] **Step 5: Require the new distribution surface**

Add these exact entries to `scripts/validate_moduflow.py::REQUIRED_FILES`:

```python
"scripts/review_intake.py",
"scripts/project_review.py",
"adapters/github-review.yaml",
"adapters/security-review.yaml",
"overlays/review-policy.yaml",
"templates/reviews/review-intake.json",
"templates/reviews/review-summary.ko.md",
"templates/reviews/review-candidates.md",
```

Add `"codex-github"` to the existing required source-ID loop. Do not add runtime network or plugin-availability checks to package validation.

- [ ] **Step 6: Document `product:review --intake` routing**

Add an intake section before the existing post-implementation workflow:

```markdown
## Intake Mode

Use `product:review --intake <source>` when review feedback already exists.

1. Preserve source provenance and default external material to reference + SHA-256.
2. Route the source through only the required adapter.
3. Have Router AI propose finding type, verification needs, lane, and CognitiveDemand.
4. Require a logically independent Verifier for disputed or medium/high-risk findings.
5. Apply deterministic policy before final disposition.
6. Write only local packet/candidate artifacts after explicit `--write`; never reply, resolve, publish, implement, or bypass release from intake mode.
```

Update `skills/index/SKILL.md` so “외부 코드리뷰 접수”, “리뷰 의견 검증”, and “보안 리뷰 결과 접수” route to intake mode. Keep plain implementation completion review mapped to the existing staged review.

Add this routing bullet to the natural-language section:

```markdown
- `@ModuFlow 외부 코드리뷰 접수`, `리뷰 의견 검증`, `보안 리뷰 결과 접수`: `product:review --intake`; plain implementation-completion `review` remains the staged post-implementation review.
```

- [ ] **Step 7: Run distribution and command tests**

```bash
python3 -m unittest tests.test_validation_distribution tests.test_review_intake tests.test_project_review -v
python3 scripts/validate_moduflow.py .
```

Expected: tests pass and package validation reports no missing files or sources.

- [ ] **Step 8: Commit adapter registration and command routing**

```bash
git add adapters/github-review.yaml adapters/security-review.yaml adapters/superpowers.yaml overlays/review-policy.yaml vendor.lock.json scripts/validate_moduflow.py tests/test_validation_distribution.py commands/product-review.md skills/index/SKILL.md
git commit -m "feat: register review intake adapters" -m "Issue: 089-verified-code-review-intake-and-remediation-routing"
```

## Task 7: Integrated Verification, Dogfood Without Source Copy, And Handoff

**Files:**
- Modify: `issues/089-verified-code-review-intake-and-remediation-routing.md`
- Modify: `specs/089-verified-code-review-intake-and-remediation-routing/tasks.md`
- Create: `specs/089-verified-code-review-intake-and-remediation-routing/status.md`

- [ ] **Step 1: Run a dry-run manual intake against synthetic structured findings**

Create temporary files outside the repository containing a two-finding synthetic review and normalized findings. Run:

```bash
python3 scripts/project_review.py . --new \
  --review-id 2026-07-16-089-dogfood \
  --adapter manual \
  --source /private/tmp/moduflow-089-synthetic-review.md \
  --findings-file /private/tmp/moduflow-089-synthetic-findings.json \
  --source-kind human --provider external-reviewer --source-identity unknown \
  --retention reference \
  --target-repository github.com/dongwonlee222/moduflow \
  --target-commit "$(git rev-parse HEAD)"
```

Expected: JSON preview contains `action: preview`, `moduflow.review-intake.v1`, reference hash, invoked manual/Superpowers adapters, skipped GitHub/security/Spec Kit adapters, and no new `workspace/reviews` files.

- [ ] **Step 2: Verify GitHub and SARIF adapters with fixtures, not live writes**

```bash
python3 -m unittest tests.test_project_review.SourceAdapterTests -v
```

Expected: unresolved/current GitHub threads and SARIF fingerprint tests pass; no network call or GitHub write occurs.

- [ ] **Step 3: Run focused review intake tests**

```bash
python3 -m unittest tests.test_review_intake tests.test_project_review -v
```

Expected: all review-intake tests pass with zero failures.

- [ ] **Step 4: Run complete project verification**

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
python3 scripts/spec_consistency.py . --issue-id 089-verified-code-review-intake-and-remediation-routing
python3 scripts/validate_moduflow.py .
python3 scripts/validate_project_artifacts.py .
python3 scripts/release_check.py .
```

Expected: full tests and all validators pass; spec consistency has no error/warn findings.

- [ ] **Step 5: Record implementation evidence and workflow state**

Update the issue workflow tasks and `tasks.md` only for work actually completed. Create `status.md` with changed files, test counts, dry-run evidence, adapter invocation evidence, known limitations, no external source copy confirmation, and next command `product:review 089-verified-code-review-intake-and-remediation-routing`.

- [ ] **Step 6: Commit verified implementation state**

```bash
git add issues/089-verified-code-review-intake-and-remediation-routing.md specs/089-verified-code-review-intake-and-remediation-routing/tasks.md specs/089-verified-code-review-intake-and-remediation-routing/status.md
git commit -m "docs: record issue 089 verification" -m "Issue: 089-verified-code-review-intake-and-remediation-routing"
```

## Acceptance Coverage

- AC1–AC4 packet/source/finding/verification contracts → Tasks 1, 3, 5
- AC5–AC6 final dispositions and no-risk evidence → Task 3
- AC7–AC10 Router/Verifier/policy and lazy invocation → Tasks 2–3, 6
- AC11–AC12 upstream adapter mappings and source policy → Task 6
- AC13–AC16 remediation lanes, candidates, deduplication, and trace → Task 4
- AC17 explicit GitHub writes and Issue 088 gate boundary → Tasks 2, 5–6
- AC18 Issue 094 boundary → Tasks 3, 6–7
- AC19 focused tests → Tasks 1–6
- AC20 complete validation → Task 7

## Rollback

Revert the Issue 089 implementation commits in reverse order. No rollback script is needed because Issue 089 does not mutate source review files, application code in downstream projects, GitHub review threads, GitHub issues, repository settings, or releases. Downstream JSON/Markdown review packets can remain as inert artifacts or be removed by their project owners.

## Execution Order

`Task 1 → Task 2 → Task 3 → Task 4 → Task 5 → Task 6 → Task 7`

The sequence is intentionally serial because Tasks 2–5 depend on the same packet/finding contracts and Tasks 5–6 both define the public command/distribution surface. Subagent-driven execution may still use a fresh worker per task with review checkpoints; parallel implementation is not recommended.

## Next Command

After choosing an execution method: `product:execute 089-verified-code-review-intake-and-remediation-routing`
