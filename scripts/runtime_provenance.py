#!/usr/bin/env python3
"""Read-only package evidence and explicitly observed process snapshots (111)."""
import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path


RECEIPT_NAME = ".moduflow-package.json"
RECEIPT_SCHEMA = "moduflow.package-provenance.v1"
EVIDENCE_FIELDS = ("source_commit", "source_dirty", "installed_at", "payload_sha256")


def _object(path):
    if path.is_symlink() or not path.is_file():
        raise ValueError("metadata must be a regular file")
    if path.stat().st_size > 65536:
        raise ValueError("metadata exceeds 65536 bytes")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("metadata must be an object")
    return value


def _timestamp(value):
    if not isinstance(value, str):
        return False
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).utcoffset() is not None
    except ValueError:
        return False


def _version(manifest):
    value = manifest.get("version")
    if manifest.get("name") != "moduflow" or not isinstance(value, str) or not value.strip():
        raise ValueError("ModuFlow manifest requires name and version")
    return value


def inspect_package(package_root):
    root = Path(package_root).resolve()
    result = {
        "schema": "moduflow.package-evidence.v1", "package_version": None,
        "package_path": str(root), **{key: None for key in EVIDENCE_FIELDS},
        "receipt_state": "missing", "provenance_source": {"package_path": "resolved_package_path"},
        "unavailable_reasons": {}, "error_codes": [], "warnings": [],
    }
    versions = {}
    try:
        for role in ("claude", "codex"):
            path = root / f".{role}-plugin/plugin.json"
            if path.exists() or path.is_symlink():
                versions[role] = _version(_object(path))
        if not versions:
            raise ValueError("package manifest missing")
        role = "claude" if "claude" in versions else "codex"
        result["package_version"] = versions[role]
        result["provenance_source"]["package_version"] = f"{role}_manifest"
    except (OSError, ValueError, UnicodeError) as exc:
        result["error_codes"].append("PACKAGE_MANIFEST_INVALID")
        result["warnings"].append(str(exc))
        result["unavailable_reasons"]["package_version"] = "manifest_invalid"

    receipt_path = root / RECEIPT_NAME
    reason = "receipt_missing"
    if receipt_path.exists() or receipt_path.is_symlink():
        reason = "receipt_invalid"
        result["receipt_state"] = "invalid"
        try:
            receipt = _object(receipt_path)
            sources, reasons = receipt.get("provenance_source"), receipt.get("unavailable_reasons")
            if receipt.get("schema") != RECEIPT_SCHEMA or not isinstance(sources, dict) or not isinstance(reasons, dict):
                raise ValueError("receipt schema or evidence maps invalid")
            published = receipt.get("package_version")
            if (result["error_codes"] or published not in versions.values()
                    or ("claude" in versions and published.split("+", 1)[0] != versions["claude"].split("+", 1)[0])):
                raise ValueError("receipt and manifest versions disagree")
            for key in ("package_version", *EVIDENCE_FIELDS):
                if key not in receipt:
                    raise ValueError(f"receipt missing {key}")
                value = receipt[key]
                explanation = reasons.get(key) if value is None else sources.get(key)
                if not isinstance(explanation, str) or not explanation.strip():
                    raise ValueError(f"receipt missing evidence/reason for {key}")
                if value is None:
                    if key in {"package_version", "payload_sha256"}:
                        raise ValueError(f"receipt requires {key}")
                    continue
                valid = True
                if key == "source_commit":
                    valid = isinstance(value, str) and re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", value)
                elif key == "source_dirty":
                    valid = type(value) is bool
                elif key == "installed_at":
                    valid = _timestamp(value)
                elif key == "payload_sha256":
                    valid = isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value)
                if not valid:
                    raise ValueError(f"receipt invalid {key}")
            for key in ("package_version", *EVIDENCE_FIELDS):
                result[key] = receipt[key]
                if receipt[key] is None:
                    result["unavailable_reasons"][key] = reasons[key]
                else:
                    result["provenance_source"][key] = f"package_receipt:{sources[key]}"
            result["receipt_state"] = "valid"
        except (OSError, ValueError, TypeError, UnicodeError) as exc:
            result["error_codes"].append("PROVENANCE_INVALID")
            result["warnings"].append(str(exc))
    else:
        result["warnings"].append("PROVENANCE_MISSING: legacy package has no installation receipt")
    for key in EVIDENCE_FIELDS:
        if result[key] is None:
            result["unavailable_reasons"].setdefault(key, reason)
    return result


def inspect_validation_target(path, *, requested_role):
    if requested_role not in {"source", "installed", "project", "auto"}:
        raise ValueError("unsupported validation role")
    root = Path(path).resolve()
    receipt = root / RECEIPT_NAME
    packaged = receipt.exists() or receipt.is_symlink()
    manifest = False
    for host in ("claude", "codex"):
        candidate = root / f".{host}-plugin/plugin.json"
        if candidate.exists() or candidate.is_symlink():
            try:
                manifest = manifest or _object(candidate).get("name") == "moduflow"
            except (OSError, ValueError, UnicodeError):
                manifest = True  # Package-looking, but not safe to treat as a project.
    git = (root / ".git").exists()
    role = requested_role
    if role == "auto":
        role = "installed" if packaged or not git else "source"
    result = {"requested_role": requested_role, "validation_role": role,
              "role_source": "compatibility_inference" if requested_role == "auto" else "explicit",
              "valid": True, "error_codes": [], "recommendation": []}
    code = None
    if role == "source" and (packaged or not manifest or not git):
        code = "TARGET_ROLE_MISMATCH"
    elif role == "project" and packaged:
        code = "TARGET_ROLE_MISMATCH"
    elif role == "project" and manifest and not git:
        runtime_layout = (root / ".mcp.json").is_file() and (root / "scripts/mcp_server.py").is_file()
        code = "TARGET_ROLE_MISMATCH" if runtime_layout else "TARGET_ROLE_AMBIGUOUS"
    if code:
        result.update(valid=False, error_codes=[code], recommendation=[
            "Run validate_moduflow.py with --mode installed for a package, or select a source/project root."
        ])
    return result


def capture_runtime(package_root, *, runtime_kind, observed_at=None, host=None, session_id=None):
    if runtime_kind not in {"cli_process", "mcp_process", "host_session"}:
        raise ValueError("unsupported runtime kind")
    if observed_at is not None and not _timestamp(observed_at):
        raise ValueError("startup timestamp must include timezone")
    for value in (host, session_id):
        if value is not None and (not isinstance(value, str) or not value.strip()):
            raise ValueError("host/session observation must be a nonempty string or null")
    evidence = inspect_package(package_root)
    fields = ("package_version", "package_path", "source_commit", "source_dirty", "installed_at")
    result = {"schema": "moduflow.runtime-provenance.v1",
              **{key: evidence[key] for key in fields}, "loaded_at": observed_at,
              "runtime_kind": runtime_kind, "host": host, "session_id": session_id,
              "provenance_source": {key: value for key, value in evidence["provenance_source"].items() if key in fields},
              "unavailable_reasons": {key: value for key, value in evidence["unavailable_reasons"].items() if key in fields},
              "error_codes": list(evidence["error_codes"])}
    for key, reason in (("loaded_at", "startup_not_observed"), ("host", "host_not_observed"), ("session_id", "session_not_observed")):
        if result[key] is None:
            result["unavailable_reasons"][key] = reason
        else:
            result["provenance_source"][key] = "entrypoint_observation"
    result["provenance_source"]["runtime_kind"] = "entrypoint"
    return result


def package_payload_sha256(package_root):
    root = Path(package_root).resolve()
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if "__pycache__" in relative.parts or path.suffix == ".pyc" or relative.as_posix() == RECEIPT_NAME:
            continue
        if path.is_symlink():
            raise ValueError(f"package payload contains symlink: {relative}")
        if path.is_dir():
            continue
        if not path.is_file():
            raise ValueError(f"package payload is not regular: {relative}")
        digest.update(relative.as_posix().encode("utf-8") + b"\0")
        digest.update(hashlib.sha256(path.read_bytes()).digest())
    return digest.hexdigest()


def main():
    argparse.ArgumentParser(description="Report this CLI process's package, not the AI host's skill loading.").parse_args()
    result = capture_runtime(Path(__file__).resolve().parent.parent, runtime_kind="cli_process",
                             observed_at=datetime.now(timezone.utc).isoformat())
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result["error_codes"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
