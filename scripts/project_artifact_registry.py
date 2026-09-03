#!/usr/bin/env python3
"""Canonical material metadata. No source crawling or external retrieval."""
import json
import os
import re
import stat
import uuid
from collections import Counter
from datetime import date
from pathlib import Path, PurePosixPath, PureWindowsPath
from urllib.parse import parse_qsl, unquote, urlsplit

try:
    from scripts import project_issue_schema, project_operation, project_registry
    from scripts.project_sync import run_command
except ImportError:  # pragma: no cover - packaged direct-script import
    import project_operation
    import project_registry
    import project_issue_schema
    from project_sync import run_command

SCHEMA = "moduflow.artifacts.v1"
READ_SCHEMA = "moduflow.artifact-registry-read.v1"
ID_RE = re.compile(r"art-[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\Z")
FIELDS = frozenset(("id", "name", "kind", "summary", "read_when", "as_of", "updated_at",
    "period", "state", "owner", "issue_ids", "local_path", "external_url", "private_ref",
    "source_requirement", "unavailable_reason", "review_after", "approval_ref", "superseded_by"))
KINDS = frozenset(("definition", "rule", "source", "report", "decision", "memory", "template", "reference"))


def diagnostic(code, field="", artifact_id="", severity="error", *, location=""):
    return {"code": code, "severity": severity,
            "artifact_id": artifact_id if isinstance(artifact_id, str) and ID_RE.fullmatch(artifact_id) else "",
            "field": field, "location": location if safe_relative_path(location) else "",
            "next_action": "Review the named registry field or source in the selected project."}


def safe_relative_path(value):
    if not isinstance(value, str) or not value or "\\" in value or any(ord(c) < 32 for c in value):
        return False
    if PurePosixPath(value).is_absolute() or PureWindowsPath(value).drive:
        return False
    parts = value.split("/")
    return not any(p in ("", ".", "..", ".git", ".moduflow") for p in parts)


def _iso_date(value):
    try:
        return isinstance(value, str) and bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", value)) and date.fromisoformat(value) is not None
    except ValueError:
        return False


def _safe_url(value):
    try:
        decoded = unquote(value)
        url = urlsplit(decoded)
        return (url.scheme == "https" and bool(url.hostname) and not url.username and not url.password
                and not any(ord(c) < 33 for c in decoded)
                and not any(re.search(r"token|secret|password|signature|credential|api.?key|authorization|x-amz|x-goog|^sig$", k, re.I)
                            for k, _ in [*parse_qsl(url.query, keep_blank_values=True),
                                         *parse_qsl(url.fragment, keep_blank_values=True)]))
    except (ValueError, TypeError):
        return False


def validate_entry(entry):
    """Validate one record without reading locators or disclosing rejected values."""
    if not isinstance(entry, dict):
        return [diagnostic("REGISTRY_RECORD_INVALID")]
    findings = []
    def bad(field, code="REGISTRY_FIELD_INVALID"):
        findings.append(diagnostic(code, field, entry.get("id")))
    if set(entry) != FIELDS:
        bad("record", "REGISTRY_FIELDS_INVALID")
    for field in ("name", "owner", "summary", "read_when"):
        value = entry.get(field)
        if (not isinstance(value, str) or not value.strip() or any(ord(c) < 32 for c in value)
                or (field in ("summary", "read_when") and len(value) > 240)):
            bad(field)
    if not isinstance(entry.get("id"), str) or not ID_RE.fullmatch(entry["id"]):
        bad("id")
    if not isinstance(entry.get("kind"), str) or entry["kind"] not in KINDS:
        bad("kind")
    if entry.get("state") not in ("draft", "approved", "superseded"):
        bad("state")
    for field in ("as_of", "updated_at"):
        if not _iso_date(entry.get(field)):
            bad(field)
    if entry.get("review_after") is not None and not _iso_date(entry["review_after"]):
        bad("review_after")
    period = entry.get("period")
    if not isinstance(period, dict) or set(period) != {"start", "end", "label"}:
        bad("period")
    elif not isinstance(period["label"], str) or not period["label"].strip():
        bad("period")
    elif not (period["start"] is None and period["end"] is None):
        if not (_iso_date(period["start"]) and _iso_date(period["end"]) and period["start"] <= period["end"]):
            bad("period")
    issues = entry.get("issue_ids")
    if not isinstance(issues, list) or any(not project_issue_schema.validate_issue_id(i) for i in issues):
        bad("issue_ids")
    elif len(issues) != len(set(issues)):
        bad("issue_ids")
    elif not issues and entry.get("state") != "draft" and entry.get("kind") != "reference":
        bad("issue_ids")
    for field in ("local_path", "approval_ref"):
        if entry.get(field) is not None and not safe_relative_path(entry[field]):
            bad(field, "UNSAFE_SOURCE_LINK")
    if entry.get("external_url") is not None and not _safe_url(entry["external_url"]):
        bad("external_url", "UNSAFE_SOURCE_LINK")
    private = entry.get("private_ref")
    if private is not None and (not isinstance(private, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,99}", private)):
        bad("private_ref", "UNSAFE_SOURCE_LINK")
    if entry.get("source_requirement") not in ("required", "optional"):
        bad("source_requirement")
    if not any(entry.get(k) for k in ("local_path", "external_url", "private_ref")):
        if entry.get("source_requirement") == "required":
            bad("local_path", "REQUIRED_LINK_MISSING")
        elif not isinstance(entry.get("unavailable_reason"), str) or not entry["unavailable_reason"].strip():
            bad("unavailable_reason")
    if entry.get("unavailable_reason") is not None and not isinstance(entry["unavailable_reason"], str):
        bad("unavailable_reason")
    if entry.get("state") == "approved" and not entry.get("approval_ref"):
        bad("approval_ref", "REGISTRY_APPROVAL_REQUIRED")
    if entry.get("state") == "draft" and entry.get("approval_ref") is not None:
        bad("approval_ref")
    target = entry.get("superseded_by")
    if entry.get("state") == "superseded":
        if not isinstance(target, str) or not ID_RE.fullmatch(target) or target == entry.get("id"):
            bad("superseded_by", "REGISTRY_SUPERSESSION_INVALID")
    elif target is not None:
        bad("superseded_by", "REGISTRY_SUPERSESSION_INVALID")
    return findings


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def _registry_blocks(text):
    """One block grammar shared by parsing and explicit entry amendment."""
    headings = list(re.finditer(r"^## ([^\n]+)(?:\n|\Z)", text, re.M))
    for index, heading in enumerate(headings):
        end = headings[index + 1].start() if index + 1 < len(headings) else len(text)
        yield heading.group(1).strip(), heading.start(), end, text[heading.end():end]


def parse_artifact_registry(text):
    findings, candidates = [], []
    seen_ids = []
    result = {"schema": SCHEMA, "entries": [], "diagnostics": findings, "metadata_valid": False}
    if not isinstance(text, str) or not re.match(r"\A---\nschema: moduflow\.artifacts\.v1\n---(?:\n|\Z)", text):
        findings.append(diagnostic("REGISTRY_SCHEMA_UNSUPPORTED", "schema"))
        return result
    parsed_fences = 0
    for header, _, _, body in _registry_blocks(text):
        blocks = list(re.finditer(r"^```json\n(.*?)^```[ \t]*$", body, re.M | re.S))
        parsed_fences += len(blocks)
        if not header.startswith("art-") and not blocks:
            continue  # Curated human prose outside record sections is not metadata.
        if len(blocks) != 1:
            findings.append(diagnostic("REGISTRY_RECORD_INVALID", "record", header))
            continue
        try:
            entry = json.loads(blocks[0].group(1), object_pairs_hook=_unique_object,
                               parse_constant=lambda _: (_ for _ in ()).throw(ValueError("nonfinite")))
        except (ValueError, RecursionError):
            findings.append(diagnostic("REGISTRY_JSON_INVALID", "record", header))
            continue
        errors = validate_entry(entry)
        if isinstance(entry, dict) and isinstance(entry.get("id"), str) and ID_RE.fullmatch(entry["id"]):
            seen_ids.append(entry["id"])
        if isinstance(entry, dict) and header != entry.get("id"):
            errors.append(diagnostic("REGISTRY_HEADING_MISMATCH", "id", entry.get("id")))
        findings.extend(errors)
        if not errors:
            candidates.append(entry)
    if parsed_fences != len(re.findall(r"^```json[ \t]*$", text, re.M)):
        findings.append(diagnostic("REGISTRY_RECORD_INVALID", "record"))
    counts = Counter(seen_ids)
    duplicate_ids = {key for key, count in counts.items() if count > 1}
    for key in sorted(duplicate_ids):
        findings.append(diagnostic("REGISTRY_DUPLICATE_ID", "id", key))
    entries = {e["id"]: e for e in candidates if e["id"] not in duplicate_ids}
    invalid = set()
    for key, entry in entries.items():
        seen, target = {key}, entry["superseded_by"]
        while target:
            if target in seen or target not in entries:
                findings.append(diagnostic("REGISTRY_SUPERSESSION_INVALID", "superseded_by", key))
                invalid.add(key)
                break
            seen.add(target)
            target = entries[target]["superseded_by"]
    result["entries"] = [e for key, e in entries.items() if key not in invalid]
    result["metadata_valid"] = not findings
    return result


def render_artifact_entry(entry):
    if validate_entry(entry):
        raise ValueError("REGISTRY_RECORD_INVALID")
    return f"## {entry['id']}\n\n```json\n{json.dumps(entry, ensure_ascii=False, indent=2)}\n```\n\n"


class RegistryReadError(ValueError):
    def __init__(self, code):
        super().__init__(code)
        self.code = code


def _local_file(root, relative, *, content=False):
    """No-follow descriptor walk; reject symlinks, special files and races to foreign parents."""
    if not safe_relative_path(relative):
        raise RegistryReadError("UNSAFE_SOURCE_LINK")
    descriptors = []
    try:
        fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        descriptors.append(fd)
        parts = relative.split("/")
        for part in parts[:-1]:
            fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            descriptors.append(fd)
        info = os.stat(parts[-1], dir_fd=fd, follow_symlinks=False)
        if not stat.S_ISREG(info.st_mode):
            raise RegistryReadError("UNSAFE_SOURCE_LINK")
        if not content:
            return True
        leaf = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
        descriptors.append(leaf)
        if not stat.S_ISREG(os.fstat(leaf).st_mode):
            raise RegistryReadError("UNSAFE_SOURCE_LINK")
        chunks = []
        while True:
            chunk = os.read(leaf, 65536)
            if not chunk:
                break
            chunks.append(chunk)
        try:
            return b"".join(chunks).decode("utf-8")
        except UnicodeError as exc:
            raise RegistryReadError("SOURCE_FORMAT_UNSUPPORTED") from exc
    except FileNotFoundError:
        return None if content else False
    except OSError as exc:
        raise RegistryReadError("UNSAFE_SOURCE_LINK") from exc
    finally:
        for descriptor in reversed(descriptors):
            os.close(descriptor)


class _Snapshot:
    def __init__(self, root, context, view, ref, runner):
        self.root, self.context, self.view = root, context, view
        self.runner = runner or run_command
        self.commit = None
        self.trace = []
        self.tree = {}
        if view not in ("working", "shared"):
            raise ValueError("view must be working or shared")
        if view == "shared":
            if not isinstance(ref, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._/-]*", ref) or ".." in ref:
                raise RegistryReadError("GIT_SNAPSHOT_UNAVAILABLE")
            result = self.git(["rev-parse", "--verify", "--end-of-options", ref + "^{commit}"])
            oid = result.stdout.strip()
            if result.returncode or not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", oid):
                raise RegistryReadError("GIT_SNAPSHOT_UNAVAILABLE")
            self.commit = oid

    def git(self, args):
        try:
            result = self.runner(["git", *args], self.root)
            if not isinstance(result.returncode, int) or not isinstance(result.stdout, str):
                raise ValueError("invalid runner")
            return result
        except (OSError, ValueError, TypeError, AttributeError, UnicodeError) as exc:
            raise RegistryReadError("GIT_SNAPSHOT_UNAVAILABLE") from exc

    def tree_entry(self, relative):
        if not safe_relative_path(relative):
            raise RegistryReadError("UNSAFE_SOURCE_LINK")
        if relative not in self.tree:
            result = self.git(["ls-tree", "-z", self.commit, "--", relative])
            if result.returncode:
                raise RegistryReadError("GIT_SNAPSHOT_UNAVAILABLE")
            exact = [r for r in result.stdout.split("\0") if "\t" in r and r.split("\t", 1)[1] == relative]
            if not exact:
                self.tree[relative] = None
            else:
                values = exact[0].split("\t", 1)[0].split()
                if len(exact) != 1 or len(values) != 3 or values[0] not in ("100644", "100755") or values[1] != "blob":
                    raise RegistryReadError("UNSAFE_SOURCE_LINK")
                self.tree[relative] = values[2]
        return self.tree[relative]

    def exists(self, relative):
        self.trace.append({"path": relative, "operation": "link-stat"})
        return bool(self.tree_entry(relative)) if self.commit else _local_file(self.root, relative)

    def read(self, relative, operation):
        self.trace.append({"path": relative, "operation": operation})
        if self.commit:
            blob = self.tree_entry(relative)
            if not blob:
                return None
            result = self.git(["cat-file", "blob", blob])
            if result.returncode:
                raise RegistryReadError("GIT_SNAPSHOT_UNAVAILABLE")
            return result.stdout
        return _local_file(self.root, relative, content=True)


def _entry_diagnostics(snapshot, entry, today):
    findings = []
    def add(code, field, severity="error"):
        findings.append(diagnostic(code, field, entry["id"], severity))
    local, unsafe = False, False
    if entry["local_path"]:
        try:
            local = snapshot.exists(entry["local_path"])
        except RegistryReadError as exc:
            add(exc.code, "local_path")
            unsafe = True
        if not local and not unsafe:
            severity = "error" if entry["source_requirement"] == "required" and not (entry["external_url"] or entry["private_ref"]) else "warning"
            add("LOCAL_LINK_BROKEN", "local_path", severity)
        if snapshot.commit and not unsafe:
            # Git diff examines working content, never returns it or substitutes it for the pinned tree.
            try:
                if not local and _local_file(snapshot.root, entry["local_path"]):
                    add("SOURCE_UNCOMMITTED", "local_path", "warning")
                elif local:
                    delta = snapshot.git(["diff", "--quiet", "--no-ext-diff", "--no-textconv", snapshot.commit, "--", entry["local_path"]])
                    if delta.returncode == 1:
                        add("SOURCE_DIRTY", "local_path", "warning")
                    elif delta.returncode != 0:
                        add("GIT_SNAPSHOT_UNAVAILABLE", "local_path", "warning")
            except RegistryReadError as exc:
                add(exc.code, "local_path", "warning")
    if entry["external_url"]:
        add("EXTERNAL_SOURCE_UNCHECKED", "external_url", "info")
    if not local and not entry["external_url"] and not unsafe:
        optional = entry["source_requirement"] == "optional"
        add("OPTIONAL_SOURCE_UNAVAILABLE" if optional else "REQUIRED_SOURCE_UNAVAILABLE", "private_ref",
            "info" if optional else "warning")
    for issue in entry["issue_ids"]:
        relative = snapshot.context["relative_paths"]["issues"] + "/" + issue + ".md"
        try:
            if not snapshot.exists(relative):
                add("REGISTRY_ISSUE_LINK_MISSING", "issue_ids")
        except RegistryReadError as exc:
            add(exc.code, "issue_ids")
    if entry["approval_ref"]:
        try:
            if not snapshot.exists(entry["approval_ref"]):
                add("REGISTRY_APPROVAL_LINK_MISSING", "approval_ref")
        except RegistryReadError as exc:
            add(exc.code, "approval_ref")
    freshness = "unknown" if entry["review_after"] is None else ("stale" if today > date.fromisoformat(entry["review_after"]) else "current")
    if freshness == "stale":
        add("ARTIFACT_STALE", "review_after", "warning")
    valid = not any(d["severity"] == "error" for d in findings)
    availability = "available" if local else ("unchecked" if entry["external_url"] and not unsafe else "unavailable")
    shared = "unknown"
    if snapshot.commit:
        shared = "blocked" if not valid else ("ready" if local else "metadata_only")
    return {**entry, "metadata_valid": valid, "source_availability": availability, "freshness": freshness,
            "share_status": shared, "diagnostics": findings, "registry_anchor": "#" + entry["id"]}


def _read_registry_snapshot(root, *, project_context, view, ref, query, artifact_ids, limit, runner, today):
    root = Path(root).resolve()
    context = project_registry.context_for_operation(root, project_context=project_context)
    project_operation.require_project_capability(context, "read")
    if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
        raise ValueError("limit must be a positive integer")
    if isinstance(artifact_ids, str) or any(not isinstance(key, str) or not ID_RE.fullmatch(key) for key in artifact_ids):
        raise ValueError("artifact_ids must contain stable artifact IDs")
    project_id = context.get("project_id")
    if project_id == "" and context.get("reason_code") == "explicit_root":
        project_id = None
    if project_id is not None and (not isinstance(project_id, str) or not re.fullmatch(r"[a-z0-9][a-z0-9._-]*", project_id)):
        raise ValueError("project_id must be a resolved registry ID")
    # Use lexical relative roles for tree reads; do not resolve through the working tree's symlinks.
    workspace = context["relative_paths"]["workspace"]
    paths = {"knowledge_path": workspace + "/knowledge.md", "registry_path": workspace + "/artifacts.md"}
    result = {"schema": READ_SCHEMA, "project_id": project_id, "identity_status": "bound" if project_id else "unbound",
              "view": view, "snapshot_commit": None, **paths, "sections": [], "entries": [], "diagnostics": [],
              "metadata_valid": False, "total": 0, "returned": 0, "omitted": 0, "truncated": False,
              "home_truncated": False, "omitted_sections": [], "read_trace": []}
    snapshot = None
    try:
        snapshot = _Snapshot(root, context, view, ref, runner)
        result["snapshot_commit"] = snapshot.commit
        result["read_trace"] = snapshot.trace
        wiki = snapshot.read(paths["knowledge_path"], "metadata-content")
        catalog = snapshot.read(paths["registry_path"], "metadata-content")
        if wiki is None:
            result["diagnostics"].append(diagnostic("KNOWLEDGE_HOME_MISSING", "knowledge_path", severity="warning", location=paths["knowledge_path"]))
        else:
            budget = 4000
            for header, _, _, body in _registry_blocks(wiki):
                section_id = project_registry.normalize_project_label(header).replace(" ", "-")
                text = body.strip()
                shown = text[:budget]
                result["sections"].append({"id": section_id, "title": header, "guidance": shown})
                if len(text) > budget:
                    result["omitted_sections"].append(section_id)
                budget = max(0, budget - len(shown))
            result["home_truncated"] = bool(result["omitted_sections"])
        if catalog is None:
            result["diagnostics"].append(diagnostic("REGISTRY_NOT_INITIALIZED", "registry_path", severity="warning", location=paths["registry_path"]))
            return result, snapshot
        parsed = parse_artifact_registry(catalog)
        result["diagnostics"].extend(parsed["diagnostics"])
        result["metadata_valid"] = parsed["metadata_valid"]
        ids = set(artifact_ids)
        existing = {e["id"] for e in parsed["entries"]}
        for missing in sorted(ids - existing):
            result["diagnostics"].append(diagnostic("REGISTRY_ID_NOT_FOUND", "id", missing))
        tokens = project_registry.normalize_project_label(query).split()
        entries = []
        for entry in sorted(parsed["entries"], key=lambda e: e["id"]):
            haystack = project_registry.normalize_project_label(" ".join(str(entry[k]) for k in ("name", "summary", "read_when", "kind", "issue_ids")))
            if (ids and entry["id"] not in ids) or any(token not in haystack for token in tokens):
                continue
            entries.append(entry)
        result["total"] = len(entries)
        result["returned"] = min(len(entries), limit)
        result["omitted"] = max(0, len(entries) - limit)
        result["truncated"] = bool(result["omitted"] or result["home_truncated"])
        for entry in entries[:limit]:
            enriched = _entry_diagnostics(snapshot, entry, today or date.today())
            enriched["match_reasons"] = ["query: " + token for token in tokens]
            result["entries"].append(enriched)
            result["diagnostics"].extend(enriched["diagnostics"])
        if wiki is None:
            for entry in result["entries"]:
                entry["share_status"] = "blocked" if snapshot.commit else "unknown"
    except RegistryReadError as exc:
        result["entries"] = []
        result["metadata_valid"] = False
        result["diagnostics"].append(diagnostic(exc.code))
    located_entries = {entry["id"]: entry for entry in result["entries"]}
    for finding in result["diagnostics"]:
        if finding["location"]:
            continue
        entry = located_entries.get(finding["artifact_id"], {})
        local = entry.get(finding["field"]) if finding["field"] in ("local_path", "approval_ref") else None
        finding["location"] = local if safe_relative_path(local) else paths["registry_path"]
    return result, snapshot


def read_artifact_registry(root, *, project_context, view="working", ref="HEAD", query="", artifact_ids=(), limit=20, runner=None, today=None):
    result, _ = _read_registry_snapshot(root, project_context=project_context, view=view, ref=ref, query=query,
                                      artifact_ids=artifact_ids, limit=limit, runner=runner, today=today)
    return result


def read_artifact_sources(root, artifact_ids, *, project_context, view="working", ref="HEAD", runner=None):
    if not artifact_ids:
        raise ValueError("Source reads require explicit artifact IDs")
    result, snapshot = _read_registry_snapshot(root, project_context=project_context, view=view, ref=ref,
                                             query="", artifact_ids=artifact_ids, limit=len(artifact_ids), runner=runner, today=None)
    result["sources"] = []
    for entry in result["entries"]:
        source = {"artifact_id": entry["id"], "locator": entry["local_path"] or entry["external_url"] or entry["private_ref"],
                  "availability": entry["source_availability"], "content": None, "handoff": None}
        if entry["metadata_valid"] and entry["source_availability"] == "available":
            if Path(entry["local_path"]).suffix.lower() not in (".md", ".txt"):
                source["handoff"] = "manual-open"
            else:
                try:
                    source["content"] = snapshot.read(entry["local_path"], "source-content")
                    if source["content"] is None:
                        source["availability"] = "unavailable"
                        result["diagnostics"].append(diagnostic("LOCAL_LINK_BROKEN", "local_path", entry["id"], location=entry["local_path"]))
                except RegistryReadError as exc:
                    source["availability"] = "unavailable"
                    result["diagnostics"].append(diagnostic(exc.code, "local_path", entry["id"], location=entry["local_path"]))
        elif entry["metadata_valid"] and (entry["external_url"] or entry["private_ref"]):
            source["handoff"] = "authorized-external-tool-required"
        result["sources"].append(source)
    return result


def _transaction_module():
    # Match the engine's existing direct-script/package loading convention.
    try:
        import project_lifecycle_transaction
    except ImportError:
        from scripts import project_lifecycle_transaction
    return project_lifecycle_transaction


def render_registration(catalog, entry, *, amend=False):
    """Pure, bounded insertion/amendment; never rewrites unrelated prose/records."""
    parsed = parse_artifact_registry(catalog)
    if not parsed["metadata_valid"] or validate_entry(entry):
        raise ValueError("REGISTRY_RECORD_INVALID")
    existing = next((item for item in parsed["entries"] if item["id"] == entry["id"]), None)
    if existing == entry:
        return catalog
    if existing and not amend:
        raise ValueError("REGISTRY_ID_CONFLICT")
    block = render_artifact_entry(entry)
    if existing:
        _, start, end, _ = next(item for item in _registry_blocks(catalog) if item[0] == entry["id"])
        match = re.search(r"^```json\n.*?^```[ \t]*$", catalog[start:end], re.M | re.S)
        # Replace only heading + metadata fence; retain trailing human prose.
        updated = catalog[:start] + block.rstrip() + catalog[start + match.end():]
    else:
        updated = catalog + ("\n" if catalog.endswith("\n") else "\n\n") + block
    if not parse_artifact_registry(updated)["metadata_valid"]:
        raise ValueError("REGISTRY_SUPERSESSION_INVALID")
    return updated


def plan_artifact_registration(root, entry, *, issue_id, project_context, new_knowledge=None, runner=None, amend=False):
    context = project_registry.context_for_operation(root, project_context=project_context)
    project_operation.require_project_capability(context, "read")
    entry = json.loads(json.dumps(entry))
    if not isinstance(entry, dict):
        raise ValueError("REGISTRY_RECORD_INVALID")
    if not entry.get("id"):
        entry["id"] = "art-" + str(uuid.uuid4())
    transaction = _transaction_module()
    intent = transaction.LifecycleIntent(issue_id=issue_id, action="artifact-register", actor="authorized-user",
        source_event="artifact-register:" + entry["id"], artifact_change={"entry": entry,
            "new_knowledge": new_knowledge, "amend": amend, "expected": None})
    return transaction.plan_lifecycle_transaction(root, intent, project_context=context)


def apply_artifact_registration(root, plan, *, project_context, runner=None):
    context = project_registry.context_for_operation(root, project_context=project_context)
    project_operation.require_project_capability(context, "write")
    transaction = _transaction_module()
    result = transaction.apply_artifact_registration_plan(root, plan, project_context=context)
    return {**result, "artifact_id": plan._artifact_change["entry"]["id"],
            "registered": result["status"] in ("applied", "noop")}
