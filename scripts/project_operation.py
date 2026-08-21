#!/usr/bin/env python3
"""Side-effect-free project operation policy and enforcing guard."""

import json
from functools import wraps


AUTHORIZATION_SCHEMA = "moduflow.project-operation-authorization.v1"
OPERATIONS = ("read", "write", "execute", "publish")
_OPERATION_SET = frozenset(OPERATIONS)
_KNOWN_STATUSES = frozenset({"active", "archived"})
_KNOWN_TRUST_SCOPES = frozenset({"internal", "read-only"})


_REASONS = {
    "PROJECT_OPERATION_ALLOWED": (
        "Project policy allows this operation.",
        "Continue with all downstream operation gates.",
    ),
    "PROJECT_READ_ALLOWED_DIAGNOSTIC": (
        "Project policy allows diagnostic reads only.",
        "Continue without mutating project, Git, or external state.",
    ),
    "PROJECT_OPERATION_DENIED_ARCHIVED": (
        "Archived projects are read-only.",
        "Reactivate the project through an approved registry change before performing this operation.",
    ),
    "PROJECT_OPERATION_DENIED_READ_ONLY": (
        "The project trust scope is read-only.",
        "Change trust_scope through an approved registry change before performing this operation.",
    ),
    "PROJECT_OPERATION_DENIED_STATUS_UNKNOWN": (
        "The project status is missing or unsupported.",
        "Set project status to active through an approved registry change before performing this operation.",
    ),
    "PROJECT_OPERATION_DENIED_TRUST_UNKNOWN": (
        "The project trust scope is missing or unsupported.",
        "Set trust_scope to internal through an approved registry change before performing this operation.",
    ),
    "PROJECT_CONTEXT_UNAVAILABLE": (
        "A resolved project context is required.",
        "Resolve one unambiguous project context before requesting an operation.",
    ),
    "PROJECT_CAPABILITY_UNAVAILABLE": (
        "The resolved project context does not contain this capability decision.",
        "Resolve the project again with a capability-aware ModuFlow runtime.",
    ),
    "PROJECT_OPERATION_UNKNOWN": (
        "The requested project operation is unsupported.",
        "Declare the operation as read, write, execute, or publish.",
    ),
}


class ProjectOperationDenied(PermissionError):
    """Typed stop condition carrying the stable authorization decision."""

    def __init__(self, decision):
        self.decision = decision
        super().__init__(decision.get("message") or "Project operation denied.")


def _source_value(value):
    if value is None:
        return None
    return value


def _normalized(value, allowed):
    normalized = str(value or "").strip().lower()
    return normalized if normalized in allowed else "unknown"


def _reason(reason_code):
    message, recommendation = _REASONS[reason_code]
    return {
        "reason_code": reason_code,
        "message": message,
        "recommendation": recommendation,
    }


def _mutation_denial_reason(project_status, trust_scope):
    if project_status == "archived":
        return "PROJECT_OPERATION_DENIED_ARCHIVED"
    if trust_scope == "read-only":
        return "PROJECT_OPERATION_DENIED_READ_ONLY"
    if project_status == "unknown":
        return "PROJECT_OPERATION_DENIED_STATUS_UNKNOWN"
    if trust_scope == "unknown":
        return "PROJECT_OPERATION_DENIED_TRUST_UNKNOWN"
    return "PROJECT_CAPABILITY_UNAVAILABLE"


def compute_project_policy(
    project_status_source,
    trust_scope_source,
    *,
    resolution_status="resolved",
    explicit_root_compatibility=False,
):
    """Return additive normalized policy fields for one resolution result."""
    if explicit_root_compatibility:
        project_status = "active"
        trust_scope = "internal"
    else:
        project_status = _normalized(project_status_source, _KNOWN_STATUSES)
        trust_scope = _normalized(trust_scope_source, _KNOWN_TRUST_SCOPES)

    policy_inputs = {
        "project_status_source": _source_value(project_status_source),
        "trust_scope_source": _source_value(trust_scope_source),
    }
    if resolution_status != "resolved":
        capabilities = {operation: False for operation in OPERATIONS}
        capability_reasons = {
            operation: _reason("PROJECT_CONTEXT_UNAVAILABLE")
            for operation in OPERATIONS
        }
    else:
        full_access = project_status == "active" and trust_scope == "internal"
        capabilities = {
            "read": True,
            "write": full_access,
            "execute": full_access,
            "publish": full_access,
        }
        read_reason = (
            "PROJECT_OPERATION_ALLOWED"
            if full_access
            else "PROJECT_READ_ALLOWED_DIAGNOSTIC"
        )
        denied_reason = _mutation_denial_reason(project_status, trust_scope)
        capability_reasons = {"read": _reason(read_reason)}
        for operation in OPERATIONS[1:]:
            capability_reasons[operation] = _reason(
                "PROJECT_OPERATION_ALLOWED" if full_access else denied_reason
            )

    return {
        "project_status": project_status,
        "policy_trust_scope": trust_scope,
        "policy_inputs": policy_inputs,
        "capabilities": capabilities,
        "capability_reasons": capability_reasons,
    }


def _decision(project_context, operation, allowed, reason_code):
    context = project_context if isinstance(project_context, dict) else {}
    reason = _reason(reason_code)
    return {
        "schema": AUTHORIZATION_SCHEMA,
        "allowed": allowed,
        "operation": operation,
        "project_id": context.get("project_id", ""),
        "project_status": context.get("project_status", "unknown"),
        "policy_trust_scope": context.get("policy_trust_scope", "unknown"),
        "policy_inputs": dict(context.get("policy_inputs") or {}),
        **reason,
    }


def authorize_project_operation(project_context, operation):
    """Return one deterministic authorization decision without side effects."""
    if not isinstance(project_context, dict) or project_context.get("status") != "resolved":
        return _decision(
            project_context,
            operation,
            False,
            "PROJECT_CONTEXT_UNAVAILABLE",
        )
    if operation not in _OPERATION_SET:
        return _decision(
            project_context,
            operation,
            False,
            "PROJECT_OPERATION_UNKNOWN",
        )

    capabilities = project_context.get("capabilities")
    capability_reasons = project_context.get("capability_reasons")
    if not isinstance(capabilities, dict) or operation not in capabilities:
        return _decision(
            project_context,
            operation,
            False,
            "PROJECT_CAPABILITY_UNAVAILABLE",
        )
    allowed = capabilities[operation] is True
    reason = capability_reasons.get(operation) if isinstance(capability_reasons, dict) else None
    reason_code = reason.get("reason_code") if isinstance(reason, dict) else ""
    if reason_code not in _REASONS:
        reason_code = "PROJECT_CAPABILITY_UNAVAILABLE"
        allowed = False
    return _decision(project_context, operation, allowed, reason_code)


def require_project_capability(project_context, operation):
    """Return an allowed decision or raise a typed denial before side effects."""
    decision = authorize_project_operation(project_context, operation)
    if not decision["allowed"]:
        raise ProjectOperationDenied(decision)
    return decision


def denial_exit_payload(error):
    """Return a typed denial's stable JSON payload."""
    if not isinstance(error, ProjectOperationDenied):
        raise TypeError("error must be ProjectOperationDenied")
    return error.decision


def cli_denial_boundary(function):
    """Render only typed policy denials as traceback-free CLI JSON."""
    @wraps(function)
    def wrapped(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except ProjectOperationDenied as error:
            print(
                json.dumps(
                    denial_exit_payload(error),
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return 2

    return wrapped
