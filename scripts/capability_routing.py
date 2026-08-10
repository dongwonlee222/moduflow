#!/usr/bin/env python3
"""Deterministic, read-only capability routing for ModuFlow."""

import argparse
import json
import re
import sys
from pathlib import Path


REGISTRY_SCHEMA = "moduflow.capability-registry.v1"
PERMISSIONS = {"read", "write-local", "write-external"}
ROUTING_SCHEMA = "moduflow.capability-routing.v1"
ERROR_SCHEMA = "moduflow.capability-routing-error.v1"
ISSUE_ID_PATTERN = re.compile(r"^[A-Za-z0-9]+(?:[._-][A-Za-z0-9]+)*$")
REQUIRED_HANDOFF_FIELDS = {
    "adapter_id",
    "reason_code",
    "permission",
    "permission_state",
    "availability",
    "output_artifact",
    "gate_after",
}
GLOBAL_LIST_FIELDS = (
    "lifecycle_triggers",
    "sequence_markers",
    "external_write_triggers",
)
CAPABILITY_FIELDS = (
    "id",
    "adapter_path",
    "purpose",
    "triggers",
    "explicit_triggers",
    "exclusions",
    "default_available",
    "permission",
    "output_artifact",
    "setup_recommendation",
)


class RegistryError(ValueError):
    """Raised when the capability registry cannot be trusted."""


def _nonempty_strings(value):
    return (
        isinstance(value, list)
        and bool(value)
        and all(isinstance(item, str) and item.strip() for item in value)
    )


def _string_list(value):
    return isinstance(value, list) and all(
        isinstance(item, str) and item.strip() for item in value
    )


def _adapter_path(root, raw_path):
    adapters_root = (root / "adapters").resolve()
    candidate = (root / raw_path).resolve()
    try:
        candidate.relative_to(adapters_root)
    except ValueError as exc:
        raise RegistryError(f"adapter_path escapes adapters/: {raw_path}") from exc
    if not candidate.is_file():
        raise RegistryError(f"adapter_path does not exist: {raw_path}")
    return candidate


def validate_registry(payload, root):
    root = Path(root).resolve()
    if not isinstance(payload, dict):
        raise RegistryError("registry must be a JSON object")
    if payload.get("schema") != REGISTRY_SCHEMA:
        raise RegistryError(f"schema must be {REGISTRY_SCHEMA}")
    for field in GLOBAL_LIST_FIELDS:
        if not _nonempty_strings(payload.get(field)):
            raise RegistryError(f"{field} must be a non-empty string list")

    capabilities = payload.get("capabilities")
    if not isinstance(capabilities, list) or not capabilities:
        raise RegistryError("capabilities must be a non-empty list")

    seen = set()
    for index, descriptor in enumerate(capabilities):
        if not isinstance(descriptor, dict):
            raise RegistryError(f"capabilities[{index}] must be an object")
        missing = [field for field in CAPABILITY_FIELDS if field not in descriptor]
        if missing:
            raise RegistryError(
                f"capabilities[{index}] missing fields: {', '.join(missing)}"
            )
        capability_id = descriptor["id"]
        if not isinstance(capability_id, str) or not capability_id.strip():
            raise RegistryError(f"capabilities[{index}].id must be a non-empty string")
        if capability_id in seen:
            raise RegistryError(f"duplicate capability id: {capability_id}")
        seen.add(capability_id)

        for field in ("adapter_path", "purpose", "output_artifact", "setup_recommendation"):
            if not isinstance(descriptor[field], str) or not descriptor[field].strip():
                raise RegistryError(f"{capability_id}.{field} must be a non-empty string")
        _adapter_path(root, descriptor["adapter_path"])
        if not _nonempty_strings(descriptor["triggers"]):
            raise RegistryError(f"{capability_id}.triggers must be a non-empty string list")
        if not _nonempty_strings(descriptor["explicit_triggers"]):
            raise RegistryError(
                f"{capability_id}.explicit_triggers must be a non-empty string list"
            )
        if not _string_list(descriptor["exclusions"]):
            raise RegistryError(f"{capability_id}.exclusions must be a string list")
        if not isinstance(descriptor["default_available"], bool):
            raise RegistryError(f"{capability_id}.default_available must be boolean")
        if descriptor["permission"] not in PERMISSIONS:
            raise RegistryError(
                f"{capability_id}.permission must be one of {sorted(PERMISSIONS)}"
            )
        if "{issue_id}" not in descriptor["output_artifact"]:
            raise RegistryError(
                f"{capability_id}.output_artifact must contain {{issue_id}}"
            )
    return payload


def load_registry(root):
    root = Path(root).resolve()
    path = root / "adapters" / "capability-routing.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RegistryError(f"registry read failed: {exc}") from exc
    return validate_registry(payload, root)


def normalize_text(text):
    return re.sub(r"\s+", " ", str(text or "").strip().lower())


def matched_positions(text, phrases):
    matches = []
    for phrase in phrases:
        normalized = normalize_text(phrase)
        if normalized.isascii():
            prefix = r"(?<![a-z0-9])" if normalized[0].isalnum() else ""
            suffix = r"(?![a-z0-9])" if normalized[-1].isalnum() else ""
            match = re.search(prefix + re.escape(normalized) + suffix, text)
            position = match.start() if match else -1
        else:
            position = text.find(normalized)
        if position >= 0:
            matches.append((position, normalized))
    return sorted(set(matches))


def _candidate(text, descriptor, registry_index):
    if matched_positions(text, descriptor.get("exclusions", [])):
        return None
    explicit = matched_positions(
        text, [descriptor["id"], *descriptor["explicit_triggers"]]
    )
    triggers = matched_positions(text, descriptor["triggers"])
    matches = explicit or triggers
    if not matches:
        return None
    return {
        "descriptor": descriptor,
        "position": matches[0][0],
        "reason_code": "explicit_adapter" if explicit else "trigger_match",
        "registry_index": registry_index,
    }


def _is_ordered_sequence(text, candidates, sequence_markers):
    if len(candidates) < 2:
        return False
    marker_positions = matched_positions(text, sequence_markers)
    if not marker_positions:
        return False
    for left, right in zip(candidates, candidates[1:]):
        if not any(left["position"] < position < right["position"] for position, _ in marker_positions):
            return False
    return True


def _permission_for(text, registry, descriptor, approved_permissions):
    external = bool(matched_positions(text, registry["external_write_triggers"]))
    permission = "write-external" if external else descriptor["permission"]
    if permission == "write-external" and permission not in approved_permissions:
        return permission, "requires_approval"
    return permission, "allowed"


def _build_stage(
    descriptor,
    issue_id,
    *,
    reason_code,
    permission,
    permission_state,
    available,
    target_root,
):
    output_artifact = descriptor["output_artifact"].format(issue_id=issue_id)
    specs_root = (Path(target_root).resolve() / "specs").resolve()
    output_path = (Path(target_root).resolve() / output_artifact).resolve()
    try:
        output_path.relative_to(specs_root)
    except ValueError as exc:
        raise RegistryError(
            f"output_artifact escapes target specs/: {output_artifact}"
        ) from exc
    return {
        "adapter_id": descriptor["id"],
        "reason_code": reason_code,
        "permission": permission,
        "permission_state": permission_state,
        "availability": "available" if available else "unavailable",
        "output_artifact": output_path.relative_to(Path(target_root).resolve()).as_posix(),
        "gate_after": None,
    }


def _base_result(request, issue_id, outcome):
    return {
        "schema": ROUTING_SCHEMA,
        "request": request,
        "issue_id": issue_id,
        "outcome": outcome,
        "stages": [],
        "current_stage": None,
        "sequence_state": "not_applicable",
        "clarification": None,
        "fallback": None,
    }


def route_request(
    request,
    registry,
    *,
    issue_id="unassigned",
    target_root=".",
    availability=None,
    approved_permissions=None,
    completed_artifacts=None,
):
    """Resolve routing metadata without loading or invoking a specialist."""
    text = normalize_text(request)
    if not isinstance(issue_id, str) or not ISSUE_ID_PATTERN.fullmatch(issue_id):
        raise RegistryError(f"invalid issue_id: {issue_id!r}")
    availability = dict(availability or {})
    approved_permissions = set(approved_permissions or set())
    completed_artifacts = set(completed_artifacts or set())

    capability_ids = {item["id"] for item in registry["capabilities"]}
    unknown_availability = set(availability) - capability_ids
    if unknown_availability:
        raise RegistryError(
            f"unknown capability availability: {sorted(unknown_availability)}"
        )
    for capability_id, available in availability.items():
        if not isinstance(available, bool):
            raise RegistryError(f"{capability_id} availability must be boolean")

    explicit_candidates = []
    for index, descriptor in enumerate(registry["capabilities"]):
        candidate = _candidate(text, descriptor, index)
        if candidate and candidate["reason_code"] == "explicit_adapter":
            explicit_candidates.append(candidate)

    if matched_positions(text, registry["lifecycle_triggers"]) and not explicit_candidates:
        return _base_result(request, issue_id, "none")

    candidates = []
    for index, descriptor in enumerate(registry["capabilities"]):
        candidate = _candidate(text, descriptor, index)
        if candidate:
            candidates.append(candidate)
    candidates.sort(key=lambda item: (item["position"], item["registry_index"]))

    if not candidates:
        return _base_result(request, issue_id, "none")
    if len(candidates) == 1:
        outcome = "delegate"
    elif _is_ordered_sequence(text, candidates, registry["sequence_markers"]):
        outcome = "sequence"
    else:
        result = _base_result(request, issue_id, "clarify")
        result["clarification"] = "어느 결과를 먼저 만들까요?"
        return result

    result = _base_result(request, issue_id, outcome)
    unavailable_recommendations = []
    for candidate in candidates:
        descriptor = candidate["descriptor"]
        available = availability.get(
            descriptor["id"], descriptor["default_available"]
        )
        permission, permission_state = _permission_for(
            text, registry, descriptor, approved_permissions
        )
        stage = _build_stage(
            descriptor,
            issue_id,
            reason_code=candidate["reason_code"],
            permission=permission,
            permission_state=permission_state,
            available=available,
            target_root=target_root,
        )
        result["stages"].append(stage)
        if not available:
            unavailable_recommendations.append(descriptor["setup_recommendation"])

    if outcome == "sequence":
        for stage in result["stages"][:-1]:
            stage["gate_after"] = stage["output_artifact"]
        pending_indexes = [
            index
            for index, stage in enumerate(result["stages"])
            if stage["output_artifact"] not in completed_artifacts
        ]
        if not pending_indexes:
            result["sequence_state"] = "complete"
        else:
            candidate_index = pending_indexes[0]
            predecessor_artifacts = {
                stage["output_artifact"] for stage in result["stages"][:candidate_index]
            }
            candidate_stage = result["stages"][candidate_index]
            eligible = (
                predecessor_artifacts <= completed_artifacts
                and candidate_stage["availability"] == "available"
                and candidate_stage["permission_state"] == "allowed"
            )
            result["sequence_state"] = "ready" if eligible else "blocked"
            if eligible:
                result["current_stage"] = candidate_index
    else:
        first = result["stages"][0]
        if first["availability"] == "available" and first["permission_state"] == "allowed":
            result["current_stage"] = 0
    if unavailable_recommendations:
        result["fallback"] = " ".join(unavailable_recommendations)
    return result


def main():
    parser = argparse.ArgumentParser(
        description="Resolve a ModuFlow request to capability routing metadata."
    )
    parser.add_argument("request")
    parser.add_argument("project_path", nargs="?", default=".")
    parser.add_argument("--issue-id", default="unassigned")
    parser.add_argument("--available", action="append", default=[])
    parser.add_argument("--unavailable", action="append", default=[])
    parser.add_argument("--completed-artifact", action="append", default=[])
    parser.add_argument(
        "--approve", action="append", choices=sorted(PERMISSIONS), default=[]
    )
    args = parser.parse_args()

    try:
        overlap = set(args.available) & set(args.unavailable)
        if overlap:
            raise RegistryError(f"conflicting availability: {sorted(overlap)}")
        package_root = Path(__file__).resolve().parents[1]
        registry = load_registry(package_root)
        availability = {capability_id: True for capability_id in args.available}
        availability.update(
            {capability_id: False for capability_id in args.unavailable}
        )
        result = route_request(
            args.request,
            registry,
            issue_id=args.issue_id,
            target_root=args.project_path,
            availability=availability,
            approved_permissions=set(args.approve),
            completed_artifacts=set(args.completed_artifact),
        )
    except (RegistryError, OSError, ValueError) as exc:
        print(
            json.dumps({"schema": ERROR_SCHEMA, "error": str(exc)}, ensure_ascii=False),
            file=sys.stderr,
        )
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
