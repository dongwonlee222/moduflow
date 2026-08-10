#!/usr/bin/env python3
"""Deterministic, read-only capability routing for ModuFlow."""

import json
from pathlib import Path


REGISTRY_SCHEMA = "moduflow.capability-registry.v1"
PERMISSIONS = {"read", "write-local", "write-external"}
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
