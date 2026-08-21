#!/usr/bin/env python3
"""Explicit multi-project registry and deterministic project context boundary."""

import json
import re
import unicodedata
from datetime import datetime
from pathlib import Path

try:
    from scripts import project_issue_schema
except ImportError:  # pragma: no cover - direct script execution fallback
    import project_issue_schema


REGISTRY_READ_SCHEMA = "moduflow.project-registry-read.v1"
REGISTRY_V1 = "moduflow.projects.v1"
REGISTRY_V2 = "moduflow.projects.v2"
RESOLUTION_SCHEMA = "moduflow.project-resolution.v1"
SELECTION_SCHEMA = "moduflow.project-selection.v1"
SELECTION_READ_SCHEMA = "moduflow.project-selection-read.v1"
MIGRATION_PROPOSAL_SCHEMA = "moduflow.projects-migration-proposal.v1"
CANONICAL_PATH_DEFAULTS = {
    "issues": "issues",
    "specs": "specs",
    "workspace": "workspace",
    "knowledge": "knowledge",
    "memory": "memory",
    "production_records": "memory/production-records",
    "playbooks": "playbooks",
    "workflow": "workflow",
}

_PROJECT_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
_TRUST_SCOPE_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$")


def normalize_project_label(value):
    """Return a stable Unicode-aware label used by the resolver."""
    normalized = unicodedata.normalize("NFKC", str(value or "")).casefold()
    return " ".join(re.findall(r"[0-9a-z가-힣._-]+", normalized))


def _diagnostic(
    code,
    *,
    project_id="",
    field="",
    current=None,
    message,
    recommendation,
    severity="error",
):
    return {
        "code": code,
        "severity": severity,
        "project_id": project_id,
        "field": field,
        "current": current,
        "message": message,
        "recommendation": recommendation,
    }


def _empty_result(registry_path, source_schema=""):
    return {
        "schema": REGISTRY_READ_SCHEMA,
        "valid": False,
        "source_schema": source_schema,
        "registry_path": str(Path(registry_path).resolve()),
        "projects": [],
        "diagnostics": [],
        "migration_proposal": None,
    }


def _load_json(registry_path, result):
    try:
        return json.loads(Path(registry_path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        result["diagnostics"].append(
            _diagnostic(
                "PROJECT_REGISTRY_MALFORMED",
                field="registry",
                current=str(registry_path),
                message="The project registry could not be read as JSON.",
                recommendation="Provide a readable UTF-8 JSON project registry.",
            )
        )
        return None


def _validate_scalar(project, index, field, pattern=None):
    value = project.get(field)
    valid = isinstance(value, str) and bool(value.strip())
    if valid and pattern is not None:
        valid = pattern.fullmatch(value) is not None
    if valid:
        return value.strip(), None
    code = {
        "id": "PROJECT_ID_INVALID",
        "name": "PROJECT_NAME_INVALID",
        "trust_scope": "PROJECT_TRUST_SCOPE_INVALID",
    }[field]
    return "", _diagnostic(
        code,
        project_id=str(project.get("id") or ""),
        field=f"projects[{index}].{field}",
        current=value,
        message=f"Project {field} must be a non-empty supported value.",
        recommendation=f"Set {field} to a non-empty lowercase slug."
        if pattern is not None
        else f"Set {field} to a non-empty string.",
    )


def _canonical_root(registry_path, raw_root, project_id, index):
    if not isinstance(raw_root, str) or not raw_root.strip():
        return None, _diagnostic(
            "PROJECT_ROOT_INVALID",
            project_id=project_id,
            field=f"projects[{index}].root",
            current=raw_root,
            message="Project root must be a non-empty path string.",
            recommendation="Set root to an absolute path or a registry-relative path.",
        )
    candidate = Path(raw_root)
    if not candidate.is_absolute():
        candidate = Path(registry_path).resolve().parent / candidate
    try:
        return candidate.resolve(), None
    except (OSError, RuntimeError) as exc:
        return None, _diagnostic(
            "PROJECT_ROOT_INVALID",
            project_id=project_id,
            field=f"projects[{index}].root",
            current=raw_root,
            message=f"Project root could not be normalized: {exc}",
            recommendation="Use a resolvable absolute or registry-relative root.",
        )


def _normalize_paths(project, index, project_id, root, diagnostics):
    raw_paths = project.get("paths")
    if not isinstance(raw_paths, dict):
        diagnostics.append(
            _diagnostic(
                "PROJECT_PATHS_INVALID",
                project_id=project_id,
                field=f"projects[{index}].paths",
                current=raw_paths,
                message="Project paths must be an object.",
                recommendation="Declare every canonical path key as a relative path.",
            )
        )
        return {}, {}

    expected = set(CANONICAL_PATH_DEFAULTS)
    for key in sorted(expected - set(raw_paths)):
        diagnostics.append(
            _diagnostic(
                "PROJECT_PATH_MISSING",
                project_id=project_id,
                field=f"paths.{key}",
                current=None,
                message="A canonical project path is missing.",
                recommendation=f"Add the relative path for {key}.",
            )
        )
    for key in sorted(set(raw_paths) - expected):
        diagnostics.append(
            _diagnostic(
                "PROJECT_PATH_UNKNOWN",
                project_id=project_id,
                field=f"paths.{key}",
                current=raw_paths[key],
                message="The registry contains an unknown canonical path key.",
                recommendation="Remove the unknown key or use a supported canonical key.",
            )
        )

    relative_paths = {}
    paths = {}
    if root is None:
        return relative_paths, paths
    for key in CANONICAL_PATH_DEFAULTS:
        value = raw_paths.get(key)
        if not isinstance(value, str) or not value.strip():
            if key in raw_paths:
                diagnostics.append(
                    _diagnostic(
                        "PROJECT_PATH_INVALID",
                        project_id=project_id,
                        field=f"paths.{key}",
                        current=value,
                        message="Configured project path must be a non-empty relative path.",
                        recommendation="Use a non-empty project-relative path.",
                    )
                )
            continue
        relative = Path(value)
        try:
            if relative.is_absolute():
                raise ValueError("absolute path")
            resolved = (root / relative).resolve()
            normalized = resolved.relative_to(root)
        except (OSError, RuntimeError, ValueError):
            diagnostics.append(
                _diagnostic(
                    "PROJECT_PATH_OUTSIDE_ROOT",
                    project_id=project_id,
                    field=f"paths.{key}",
                    current=value,
                    message="Configured project path escapes the canonical root.",
                    recommendation="Use a project-relative path contained by the registered root.",
                )
            )
            continue
        relative_paths[key] = normalized.as_posix() or "."
        paths[key] = str(resolved)
    return relative_paths, paths


def _normalize_v2_project(project, index, registry_path, diagnostics):
    if not isinstance(project, dict):
        diagnostics.append(
            _diagnostic(
                "PROJECT_ENTRY_INVALID",
                field=f"projects[{index}]",
                current=project,
                message="Each project entry must be an object.",
                recommendation="Replace the entry with a projects.v2 project object.",
            )
        )
        return None

    project_id, error = _validate_scalar(project, index, "id", _PROJECT_ID_RE)
    if error:
        diagnostics.append(error)
    name, error = _validate_scalar(project, index, "name")
    if error:
        diagnostics.append(error)
    trust_scope, error = _validate_scalar(
        project, index, "trust_scope", _TRUST_SCOPE_RE
    )
    if error:
        diagnostics.append(error)
    root, error = _canonical_root(
        registry_path, project.get("root"), project_id, index
    )
    if error:
        diagnostics.append(error)
    relative_paths, paths = _normalize_paths(
        project, index, project_id, root, diagnostics
    )

    raw_aliases = project.get("aliases", [])
    if not isinstance(raw_aliases, list) or not all(
        isinstance(alias, str) and alias.strip() for alias in raw_aliases
    ):
        diagnostics.append(
            _diagnostic(
                "PROJECT_ALIASES_INVALID",
                project_id=project_id,
                field=f"projects[{index}].aliases",
                current=raw_aliases,
                message="Project aliases must be a list of non-empty strings.",
                recommendation="Use a JSON list containing only non-empty alias strings.",
            )
        )
        raw_aliases = []
    aliases = sorted(
        {
            normalized
            for normalized in (
                normalize_project_label(value)
                for value in [project_id, name, *raw_aliases]
            )
            if normalized
        }
    )
    return {
        "id": project_id,
        "name": name,
        "root": str(root) if root is not None else "",
        "aliases": aliases,
        "relative_paths": relative_paths,
        "paths": paths,
        "trust_scope": trust_scope,
        "status": str(project.get("status") or "active"),
        "owner": str(project.get("owner") or ""),
        "source_schema": REGISTRY_V2,
    }


def _normalize_v1_project(project, index, registry_path, diagnostics):
    if not isinstance(project, dict):
        diagnostics.append(
            _diagnostic(
                "PROJECT_ENTRY_INVALID",
                field=f"projects[{index}]",
                current=project,
                message="Each project entry must be an object.",
                recommendation="Replace the entry with a projects.v1 project object.",
            )
        )
        return None
    project_id, error = _validate_scalar(project, index, "id", _PROJECT_ID_RE)
    if error:
        diagnostics.append(error)
    name, error = _validate_scalar(project, index, "name")
    if error:
        diagnostics.append(error)
    root, error = _canonical_root(
        registry_path, project.get("path"), project_id, index
    )
    if error:
        diagnostics.append(error)
    aliases = sorted(
        {
            normalized
            for normalized in (
                normalize_project_label(value)
                for value in [
                    project_id,
                    name,
                    *(project.get("aliases") or []),
                ]
            )
            if normalized
        }
    )
    relative_paths = dict(CANONICAL_PATH_DEFAULTS)
    paths = {
        key: str((root / value).resolve())
        for key, value in relative_paths.items()
    } if root is not None else {}
    return {
        "id": project_id,
        "name": name,
        "root": str(root) if root is not None else "",
        "aliases": aliases,
        "relative_paths": relative_paths,
        "paths": paths,
        "trust_scope": str(project.get("trust_scope") or "internal"),
        "status": str(project.get("status") or "active"),
        "owner": str(project.get("owner") or ""),
        "source_schema": REGISTRY_V1,
    }


def _migration_proposal(result):
    return {
        "schema": MIGRATION_PROPOSAL_SCHEMA,
        "from_schema": REGISTRY_V1,
        "to_schema": REGISTRY_V2,
        "registry_path": result["registry_path"],
        "projects": [
            {
                "id": project["id"],
                "name": project["name"],
                "root": project["root"],
                "aliases": project["aliases"],
                "paths": dict(CANONICAL_PATH_DEFAULTS),
                "trust_scope": project["trust_scope"],
                "status": project["status"],
                "owner": project["owner"],
            }
            for project in result["projects"]
        ],
        "automatic_write": False,
    }


def load_project_registry(registry_path):
    """Return a normalized registry; malformed input becomes diagnostics."""
    result = _empty_result(registry_path)
    payload = _load_json(registry_path, result)
    if payload is None:
        return result
    if not isinstance(payload, dict):
        result["diagnostics"].append(
            _diagnostic(
                "PROJECT_REGISTRY_MALFORMED",
                field="registry",
                current=payload,
                message="The project registry root must be an object.",
                recommendation="Use a JSON object with schema and projects fields.",
            )
        )
        return result

    source_schema = payload.get("schema")
    result["source_schema"] = source_schema if isinstance(source_schema, str) else ""
    if not source_schema:
        result["diagnostics"].append(
            _diagnostic(
                "PROJECT_REGISTRY_SCHEMA_MISSING",
                field="schema",
                current=source_schema,
                message="The project registry schema is missing.",
                recommendation=f"Set schema to {REGISTRY_V2}.",
            )
        )
        return result
    if source_schema not in {REGISTRY_V1, REGISTRY_V2}:
        result["diagnostics"].append(
            _diagnostic(
                "PROJECT_REGISTRY_SCHEMA_UNSUPPORTED",
                field="schema",
                current=source_schema,
                message="The project registry schema is not supported.",
                recommendation=f"Use {REGISTRY_V2}.",
            )
        )
        return result

    projects = payload.get("projects")
    if not isinstance(projects, list):
        result["diagnostics"].append(
            _diagnostic(
                "PROJECTS_NOT_LIST",
                field="projects",
                current=projects,
                message="The projects field must be a list.",
                recommendation="Set projects to a JSON list.",
            )
        )
        return result

    seen_ids = set()
    for index, project in enumerate(projects):
        normalizer = (
            _normalize_v2_project
            if source_schema == REGISTRY_V2
            else _normalize_v1_project
        )
        normalized = normalizer(project, index, registry_path, result["diagnostics"])
        if normalized is None:
            continue
        if normalized["id"] in seen_ids:
            result["diagnostics"].append(
                _diagnostic(
                    "PROJECT_ID_DUPLICATE",
                    project_id=normalized["id"],
                    field=f"projects[{index}].id",
                    current=normalized["id"],
                    message="Project IDs must be unique within the registry.",
                    recommendation="Assign each registered project a unique ID.",
                )
            )
        seen_ids.add(normalized["id"])
        result["projects"].append(normalized)

    result["valid"] = not any(
        diagnostic["severity"] == "error"
        for diagnostic in result["diagnostics"]
    )
    if source_schema == REGISTRY_V1 and result["valid"]:
        result["migration_proposal"] = _migration_proposal(result)
    return result


def _candidate_view(project):
    return {"id": project["id"], "name": project["name"]}


def _resolution_base(status, reason_code, *, candidates=None, warnings=None, question=""):
    return {
        "schema": RESOLUTION_SCHEMA,
        "status": status,
        "project_id": "",
        "reason_code": reason_code,
        "candidates": list(candidates or []),
        "canonical_root": "",
        "relative_paths": {},
        "paths": {},
        "trust_scope": "",
        "warnings": list(warnings or []),
        "question": question,
    }


def _unresolved(reason_code, question, warnings=None):
    return _resolution_base(
        "unresolved",
        reason_code,
        warnings=warnings,
        question=question,
    )


def _ambiguous(projects, reason_code, question, warnings=None):
    return _resolution_base(
        "ambiguous",
        reason_code,
        candidates=[_candidate_view(project) for project in projects],
        warnings=warnings,
        question=question,
    )


def _resolved(project, reason_code, warnings=None):
    root = Path(project["root"])
    if not root.is_dir():
        return _unresolved(
            "project_root_missing",
            "등록된 프로젝트 루트를 확인해 주세요.",
            [*(warnings or []), "PROJECT_ROOT_MISSING"],
        )
    result = _resolution_base(
        "resolved",
        reason_code,
        candidates=[_candidate_view(project)],
        warnings=warnings,
    )
    result.update(
        {
            "project_id": project["id"],
            "canonical_root": project["root"],
            "relative_paths": dict(project["relative_paths"]),
            "paths": dict(project["paths"]),
            "trust_scope": project["trust_scope"],
        }
    )
    return result


def _project_label_matches(project, request_text):
    request_label = normalize_project_label(request_text)
    if not request_label:
        return False
    padded_request = f" {request_label} "
    return any(
        f" {alias} " in padded_request
        for alias in project.get("aliases", [])
        if alias
    )


def _cwd_matches(projects, cwd):
    if cwd is None:
        return []
    try:
        resolved_cwd = Path(cwd).resolve()
    except (OSError, RuntimeError):
        return []
    matches = []
    for project in projects:
        try:
            resolved_cwd.relative_to(Path(project["root"]))
        except (OSError, RuntimeError, ValueError):
            continue
        matches.append(project)
    return matches


def _signal_conflicts(selected_id, *, cwd_matches, alias_matches, active, recent):
    signaled_ids = {
        project["id"]
        for project in [*cwd_matches, *alias_matches]
        if project["id"] != selected_id
    }
    for project in (active, recent):
        if project is not None and project["id"] != selected_id:
            signaled_ids.add(project["id"])
    return ["PROJECT_SIGNAL_CONFLICT"] if signaled_ids else []


def resolve_loaded_registry(
    registry,
    *,
    explicit_project_id="",
    cwd=None,
    request_text="",
    active_project_id="",
    recent_selection=None,
):
    """Resolve one project using only an already normalized registry."""
    if not isinstance(registry, dict) or not registry.get("valid"):
        return _unresolved(
            "registry_invalid",
            "유효한 프로젝트 레지스트리를 확인해 주세요.",
            ["PROJECT_REGISTRY_INVALID"],
        )
    projects = list(registry.get("projects") or [])
    by_id = {project["id"]: project for project in projects}

    cwd_projects = _cwd_matches(projects, cwd)
    alias_projects = [
        project
        for project in projects
        if _project_label_matches(project, request_text)
    ]
    active = by_id.get(str(active_project_id or ""))
    recent_id = ""
    if isinstance(recent_selection, dict):
        recent_id = str(recent_selection.get("project_id") or "")
    recent = by_id.get(recent_id)

    if explicit_project_id:
        selected = by_id.get(str(explicit_project_id))
        if selected is None:
            return _unresolved(
                "explicit_id_not_registered",
                "등록된 프로젝트 ID를 지정해 주세요.",
                ["PROJECT_ID_NOT_REGISTERED"],
            )
        warnings = _signal_conflicts(
            selected["id"],
            cwd_matches=cwd_projects,
            alias_matches=alias_projects,
            active=active,
            recent=recent,
        )
        return _resolved(selected, "explicit_id", warnings)

    if len(cwd_projects) > 1:
        return _ambiguous(
            cwd_projects,
            "cwd_root_ambiguous",
            "현재 경로가 둘 이상의 등록 프로젝트에 포함됩니다. 프로젝트를 선택해 주세요.",
        )
    if len(cwd_projects) == 1:
        selected = cwd_projects[0]
        warnings = _signal_conflicts(
            selected["id"],
            cwd_matches=[],
            alias_matches=alias_projects,
            active=active,
            recent=recent,
        )
        return _resolved(selected, "cwd_root", warnings)

    if len(alias_projects) > 1:
        return _ambiguous(
            alias_projects,
            "request_alias_ambiguous",
            "요청과 일치하는 프로젝트가 여러 개입니다. 프로젝트를 선택해 주세요.",
        )
    if len(alias_projects) == 1:
        selected = alias_projects[0]
        warnings = _signal_conflicts(
            selected["id"],
            cwd_matches=[],
            alias_matches=[],
            active=active,
            recent=recent,
        )
        return _resolved(selected, "request_alias", warnings)

    if active is not None:
        warnings = _signal_conflicts(
            active["id"],
            cwd_matches=[],
            alias_matches=[],
            active=None,
            recent=recent,
        )
        return _resolved(active, "active_project", warnings)
    if active_project_id:
        active_warning = ["ACTIVE_PROJECT_NOT_REGISTERED"]
    else:
        active_warning = []

    if recent is not None:
        return _resolved(recent, "recent_selection", active_warning)
    if recent_id:
        active_warning.append("RECENT_PROJECT_NOT_REGISTERED")

    if len(projects) == 1:
        return _resolved(projects[0], "single_registered_project", active_warning)
    if projects:
        return _ambiguous(
            projects,
            "multiple_projects",
            "작업할 프로젝트를 선택해 주세요.",
            active_warning,
        )
    return _unresolved(
        "no_registered_projects",
        "프로젝트를 레지스트리에 등록해 주세요.",
        active_warning,
    )


def _configured_context_paths(project_root):
    root = Path(project_root).resolve()
    relative_paths = project_issue_schema.configured_project_paths(root)
    paths = {
        key: str((root / value).resolve())
        for key, value in relative_paths.items()
    }
    violations = project_issue_schema._configured_path_violations(root)
    warnings = [
        "PROJECT_CONFIG_PATH_OUTSIDE_ROOT"
        for _key in sorted(violations)
    ]
    return relative_paths, paths, warnings


def _materialize_selected_context(result, registry):
    selected = next(
        (
            project
            for project in registry.get("projects", [])
            if project.get("id") == result.get("project_id")
        ),
        None,
    )
    if selected is None or selected.get("source_schema") != REGISTRY_V1:
        return result
    relative_paths, paths, warnings = _configured_context_paths(
        result["canonical_root"]
    )
    materialized = dict(result)
    materialized["relative_paths"] = relative_paths
    materialized["paths"] = paths
    materialized["warnings"] = [*result.get("warnings", []), *warnings]
    return materialized


def resolve_project(
    registry_path,
    *,
    explicit_project_id="",
    cwd=None,
    request_text="",
    active_project_id="",
    recent_selection=None,
):
    """Load a registry, resolve one project, and materialize its safe context."""
    registry = load_project_registry(registry_path)
    if recent_selection is None:
        recent_selection = load_recent_selection(registry_path)
    result = resolve_loaded_registry(
        registry,
        explicit_project_id=explicit_project_id,
        cwd=cwd,
        request_text=request_text,
        active_project_id=active_project_id,
        recent_selection=recent_selection,
    )
    if result["status"] != "resolved":
        return result
    return _materialize_selected_context(result, registry)


def project_context_for_root(project_root):
    """Return a compatibility context for one explicitly supplied project root."""
    root = Path(project_root).resolve()
    if not root.is_dir():
        return _unresolved(
            "project_root_missing",
            "프로젝트 루트를 확인해 주세요.",
            ["PROJECT_ROOT_MISSING"],
        )
    relative_paths, paths, warnings = _configured_context_paths(root)
    result = _resolution_base(
        "resolved",
        "explicit_root",
        warnings=warnings,
    )
    result.update(
        {
            "canonical_root": str(root),
            "relative_paths": relative_paths,
            "paths": paths,
            "trust_scope": "project-local",
        }
    )
    return result


def canonical_path(project_context, key):
    """Return one canonical contained path from a resolved project context."""
    if not isinstance(project_context, dict) or project_context.get("status") != "resolved":
        raise ValueError("project context must be resolved")
    if key not in CANONICAL_PATH_DEFAULTS:
        raise KeyError(key)
    value = project_context.get("paths", {}).get(key)
    if not value:
        raise ValueError(f"canonical path is unavailable: {key}")
    root = Path(project_context["canonical_root"]).resolve()
    candidate = Path(value).resolve()
    try:
        candidate.relative_to(root)
    except (OSError, RuntimeError, ValueError) as exc:
        raise ValueError(f"canonical path escapes project root: {key}") from exc
    return candidate


def context_for_operation(project_root, *, project_context=None):
    """Return one resolved context bound to the explicit operation root."""
    root = Path(project_root).resolve()
    context = (
        project_context_for_root(project_root)
        if project_context is None
        else project_context
    )
    if not isinstance(context, dict) or context.get("status") != "resolved":
        raise ValueError("project context must be resolved")
    canonical_root = context.get("canonical_root")
    if not canonical_root:
        raise ValueError("project context canonical root is unavailable")
    if Path(canonical_root).resolve() != root:
        raise ValueError("project context does not match project root")
    return context


def canonical_child_path(project_context, key, *parts):
    """Return a safe child path below one canonical role root."""
    role_root = canonical_path(project_context, key)
    if not parts:
        return role_root

    clean_parts = []
    for part in parts:
        raw = str(part)
        candidate_part = Path(raw)
        if not raw or raw == "." or candidate_part.is_absolute():
            raise ValueError(f"unsafe canonical child component: {raw!r}")
        segments = candidate_part.parts
        if not segments or any(segment in {"", ".", ".."} for segment in segments):
            raise ValueError(f"unsafe canonical child component: {raw!r}")
        clean_parts.extend(segments)

    candidate = role_root.joinpath(*clean_parts).resolve()
    project_root = Path(project_context["canonical_root"]).resolve()
    try:
        candidate.relative_to(role_root)
        candidate.relative_to(project_root)
    except (OSError, RuntimeError, ValueError) as exc:
        raise ValueError(f"canonical child path escapes role root: {key}") from exc
    return candidate


def canonical_relative_path(project_context, key, *parts):
    """Return a canonical child as a project-root-relative POSIX path."""
    root = Path(project_context.get("canonical_root", "")).resolve()
    child = canonical_child_path(project_context, key, *parts)
    try:
        return child.relative_to(root).as_posix()
    except (OSError, RuntimeError, ValueError) as exc:
        raise ValueError(f"canonical path escapes project root: {key}") from exc


def _empty_selection(warnings=None):
    return {
        "schema": SELECTION_READ_SCHEMA,
        "valid": False,
        "project_id": "",
        "selected_at": "",
        "warnings": list(warnings or []),
    }


def _valid_iso_time(value):
    if not isinstance(value, str) or not value.strip():
        return False
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def load_recent_selection(registry_path):
    """Read the adjacent explicit recent selection without project-local access."""
    selection_path = Path(registry_path).resolve().parent / "project-selection.json"
    if not selection_path.exists():
        return _empty_selection()
    try:
        payload = json.loads(selection_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return _empty_selection(["PROJECT_SELECTION_MALFORMED"])
    if not isinstance(payload, dict) or payload.get("schema") != SELECTION_SCHEMA:
        return _empty_selection(["PROJECT_SELECTION_MALFORMED"])
    project_id = payload.get("project_id")
    selected_at = payload.get("selected_at")
    if not _valid_iso_time(selected_at):
        return _empty_selection(["PROJECT_SELECTION_TIME_INVALID"])
    registry = load_project_registry(registry_path)
    if not registry.get("valid"):
        return _empty_selection(["PROJECT_REGISTRY_INVALID"])
    if project_id not in {project["id"] for project in registry["projects"]}:
        return _empty_selection(["PROJECT_SELECTION_NOT_REGISTERED"])
    return {
        "schema": SELECTION_READ_SCHEMA,
        "valid": True,
        "project_id": project_id,
        "selected_at": selected_at,
        "warnings": [],
    }


def record_recent_selection(registry_path, project_id, selected_at):
    """Atomically record an explicit registered-project selection."""
    registry = load_project_registry(registry_path)
    if not registry.get("valid"):
        raise ValueError("cannot select from an invalid project registry")
    if project_id not in {project["id"] for project in registry["projects"]}:
        raise ValueError(f"project is not registered: {project_id}")
    if not _valid_iso_time(selected_at):
        raise ValueError("selected_at must be an ISO-8601 timestamp")
    payload = {
        "schema": SELECTION_SCHEMA,
        "project_id": project_id,
        "selected_at": selected_at,
    }
    content = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    selection_path = Path(registry_path).resolve().parent / "project-selection.json"
    try:
        if selection_path.read_text(encoding="utf-8") == content:
            return {"action": "noop", "path": str(selection_path)}
    except (OSError, UnicodeError):
        pass
    temporary_path = selection_path.with_name("project-selection.json.tmp")
    temporary_path.write_text(content, encoding="utf-8")
    temporary_path.replace(selection_path)
    return {"action": "written", "path": str(selection_path)}
