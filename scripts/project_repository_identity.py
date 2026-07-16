#!/usr/bin/env python3
"""Canonical repository identity parsing and normalization for ModuFlow."""

import argparse
import json
import re
from pathlib import Path
from urllib.parse import urlsplit


ALLOWED_MODES = {"remote", "local_only"}
ALLOWED_PROVIDERS = {"github", "generic"}
ALLOWED_LIFECYCLES = {"active", "read_only", "archived"}
SCP_URL_RE = re.compile(r"^(?:[^@/:]+@)?(?P<host>[^/:]+):(?P<path>.+)$")
GITHUB_ARTIFACT_URL_RE = re.compile(
    r"https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+(?:/[^\s<>()`\]]*)?"
)
OPERATION_CAPABILITIES = {
    "doctor": "read",
    "status": "read",
    "validate": "read",
    "execute": "execute",
    "commit": "commit",
    "github_api_commit": "github_write",
    "push": "push",
    "github_issue": "github_write",
    "pr": "github_write",
    "release": "release",
}
MISMATCH_REASONS = {
    "git_root_mismatch",
    "fetch_remote_mismatch",
    "push_remote_mismatch",
    "provider_repository_mismatch",
    "provider_default_branch_mismatch",
    "provider_repository_is_fork",
    "provider_archive_state_mismatch",
    "artifact_write_repository_mismatch",
}


class IdentityConfigError(ValueError):
    """Raised when repository identity input cannot be safely normalized."""


def _reason(code, message):
    return {"code": code, "message": message}


def _invalid_url(message):
    raise IdentityConfigError(message)


def _split_host_path(value):
    text = str(value or "").strip()
    if not text or text.startswith(("/", "./", "../", "~")):
        _invalid_url("Repository URL must be an absolute network repository URL.")

    if "://" in text:
        parsed = urlsplit(text)
        if parsed.scheme not in {"https", "ssh", "git"}:
            _invalid_url("Repository URL uses an unsupported scheme.")
        if not parsed.hostname:
            _invalid_url("Repository URL is missing a host.")
        try:
            port = parsed.port
        except ValueError:
            _invalid_url("Repository URL has an invalid port.")
        default_port = (
            (parsed.scheme == "https" and port == 443)
            or (parsed.scheme == "ssh" and port == 22)
            or port is None
        )
        host = parsed.hostname.lower()
        if not default_port:
            host = f"{host}:{port}"
        path = parsed.path
    else:
        scp_match = SCP_URL_RE.match(text)
        if scp_match:
            host = scp_match.group("host").lower()
            path = scp_match.group("path")
        else:
            host, separator, path = text.partition("/")
            if not separator or not host or not path or "." not in host:
                _invalid_url("Repository identity must contain a host and repository path.")
            host = host.lower()

    normalized_path = path.strip("/")
    if normalized_path.endswith(".git"):
        normalized_path = normalized_path[:-4]
    if not normalized_path or normalized_path.startswith(("./", "../")):
        _invalid_url("Repository URL is missing a valid repository path.")
    return host, normalized_path


def normalize_git_url(value, provider):
    """Return a credential-free comparable host/path repository identity."""
    if provider not in ALLOWED_PROVIDERS:
        raise IdentityConfigError("Repository provider must be github or generic.")

    host, path = _split_host_path(value)
    parts = path.split("/")

    if provider == "github":
        if host != "github.com":
            raise IdentityConfigError("GitHub repository identity must use github.com.")
        if len(parts) != 2 or not all(parts):
            raise IdentityConfigError("GitHub repository identity must be owner/repository.")
        path = "/".join(part.lower() for part in parts)

    return f"{host}/{path}"


def repository_from_github_artifact_url(value):
    """Resolve the repository identity from a GitHub issue/PR/release URL."""
    parsed = urlsplit(str(value or "").strip())
    if parsed.scheme != "https" or (parsed.hostname or "").lower() != "github.com":
        raise IdentityConfigError("GitHub artifact URL must use https://github.com.")
    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) < 4 or parts[2] not in {"issues", "pull", "releases"}:
        raise IdentityConfigError("GitHub artifact URL is not an issue, pull, or release URL.")
    return normalize_git_url(f"github.com/{parts[0]}/{parts[1]}", "github")


def _repository_artifact_paths(root):
    root = Path(root)
    paths = []
    issues_dir = root / "issues"
    if issues_dir.is_dir():
        paths.extend(sorted(issues_dir.glob("*.md")))
    specs_dir = root / "specs"
    if specs_dir.is_dir():
        for name in ["spec.md", "plan.md", "status.md", "review.md", "pr.md", "release.md"]:
            paths.extend(sorted(specs_dir.glob(f"*/{name}")))
    for relative in ["status.md", "workspace/status.md"]:
        target = root / relative
        if target.is_file():
            paths.append(target)
    return sorted(set(paths))


def audit_repository_links(root, canonical_repository=None):
    """Classify GitHub repository links in Git-native execution artifacts."""
    root = Path(root).resolve()
    if canonical_repository is None:
        config = load_repository_identity(root)
        identity = config.get("identity") or {}
        canonical_repository = identity.get("canonical_repository")
    if not canonical_repository:
        return []

    findings = []
    for path in _repository_artifact_paths(root):
        heading = ""
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if line.startswith("## "):
                heading = line[3:].strip()
            for match in GITHUB_ARTIFACT_URL_RE.finditer(line):
                url = match.group(0).rstrip(".,;:")
                try:
                    repository = repository_from_github_artifact_url(url)
                except IdentityConfigError:
                    parts = urlsplit(url).path.strip("/").split("/")
                    if len(parts) < 2:
                        continue
                    repository = normalize_git_url(
                        f"github.com/{parts[0]}/{parts[1]}",
                        "github",
                    )
                context = f"{heading} {line}".lower()
                if repository == canonical_repository:
                    classification = "canonical"
                    role = "canonical"
                elif "mirror" in context:
                    classification = "mirror"
                    role = "mirror"
                elif any(token in context for token in ["reference", "benchmark", "example"]):
                    classification = "reference"
                    role = "reference"
                else:
                    classification = "mismatch"
                    role = None
                write_handoff = path.name in {"pr.md", "release.md"} or bool(
                    re.search(r"(?:github|target)\s*(?:pr|issue|release)?\s*:", line, re.I)
                )
                findings.append(
                    {
                        "artifact": str(path.relative_to(root)),
                        "line": line_number,
                        "url": url,
                        "repository": repository,
                        "role": role,
                        "classification": classification,
                        "write_handoff": write_handoff,
                    }
                )
    return findings


def _unconfigured(message="Canonical repository identity is not configured."):
    return {
        "schema": "moduflow.repository-identity-config.v1",
        "configured": False,
        "identity": None,
        "reasons": [_reason("canonical_identity_missing", message)],
    }


def _invalid_config(message):
    return {
        "schema": "moduflow.repository-identity-config.v1",
        "configured": False,
        "identity": None,
        "reasons": [_reason("canonical_identity_invalid", message)],
    }


def load_repository_identity(root):
    """Load and validate `.moduflow/config.json` canonical Git identity."""
    config_path = Path(root).resolve() / ".moduflow" / "config.json"
    if not config_path.is_file():
        return _unconfigured()

    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return _invalid_config(".moduflow/config.json is unreadable or invalid JSON.")

    git_config = config.get("git")
    identity = git_config.get("identity") if isinstance(git_config, dict) else None
    if not isinstance(identity, dict):
        return _unconfigured()

    mode = identity.get("mode")
    provider = identity.get("provider")
    base_branch = identity.get("base_branch")
    lifecycle = identity.get("lifecycle")

    if mode not in ALLOWED_MODES:
        return _invalid_config("git.identity.mode must be remote or local_only.")
    if provider not in ALLOWED_PROVIDERS:
        return _invalid_config("git.identity.provider must be github or generic.")
    if not isinstance(base_branch, str) or not base_branch.strip():
        return _invalid_config("git.identity.base_branch must be a non-empty string.")
    if lifecycle not in ALLOWED_LIFECYCLES:
        return _invalid_config(
            "git.identity.lifecycle must be active, read_only, or archived."
        )

    normalized = {
        "mode": mode,
        "provider": provider,
        "base_branch": base_branch.strip(),
        "lifecycle": lifecycle,
    }

    if mode == "remote":
        canonical_repository = identity.get("canonical_repository")
        remote_name_hint = identity.get("remote_name_hint")
        if not isinstance(canonical_repository, str) or not canonical_repository.strip():
            return _invalid_config(
                "git.identity.canonical_repository is required in remote mode."
            )
        if not isinstance(remote_name_hint, str) or not remote_name_hint.strip():
            return _invalid_config(
                "git.identity.remote_name_hint is required in remote mode."
            )
        try:
            normalized["canonical_repository"] = normalize_git_url(
                canonical_repository,
                provider,
            )
        except IdentityConfigError as exc:
            return _invalid_config(f"git.identity.canonical_repository is invalid: {exc}")
        normalized["remote_name_hint"] = remote_name_hint.strip()

    return {
        "schema": "moduflow.repository-identity-config.v1",
        "configured": True,
        "identity": normalized,
        "reasons": [],
    }


def _default_runner(args, cwd):
    try:
        from scripts.project_sync import run_command
    except ModuleNotFoundError:
        from project_sync import run_command

    return run_command(args, cwd)


def _run(runner, args, root):
    try:
        return runner(args, root)
    except (OSError, RuntimeError) as exc:
        return type(
            "CommandFailure",
            (),
            {"returncode": 1, "stdout": "", "stderr": type(exc).__name__},
        )()


def _default_github_provider_check(canonical_repository, root, runner):
    owner_repo = canonical_repository.split("/", 1)[1]
    result = _run(
        runner,
        [
            "gh",
            "repo",
            "view",
            owner_repo,
            "--json",
            "nameWithOwner,defaultBranchRef,isArchived,isFork",
        ],
        root,
    )
    if result.returncode != 0:
        return {
            "ok": False,
            "reason": "provider_unavailable",
            "detail": f"gh repo view failed with exit code {result.returncode}.",
        }
    try:
        payload = json.loads(result.stdout or "{}")
        default_branch = payload.get("defaultBranchRef")
        if isinstance(default_branch, dict):
            default_branch = default_branch.get("name")
        repository = normalize_git_url(
            f"github.com/{payload.get('nameWithOwner', '')}",
            "github",
        )
    except (json.JSONDecodeError, IdentityConfigError, TypeError):
        return {
            "ok": False,
            "reason": "provider_unavailable",
            "detail": "gh repo view returned invalid repository evidence.",
        }
    return {
        "ok": True,
        "repository": repository,
        "default_branch": default_branch,
        "archived": bool(payload.get("isArchived")),
        "fork": bool(payload.get("isFork")),
    }


def _output_lines(result):
    if result.returncode != 0:
        return []
    return [line.strip() for line in (result.stdout or "").splitlines() if line.strip()]


def _normalized_urls(values, provider, invalid_code, reasons):
    normalized = []
    for value in values:
        try:
            normalized.append(normalize_git_url(value, provider))
        except IdentityConfigError:
            reasons.append(
                _reason(invalid_code, "Observed repository URL could not be safely normalized.")
            )
    return normalized


def _has_reason(reasons, code):
    return any(reason["code"] == code for reason in reasons)


def _base_ref(root, runner, identity):
    base_branch = identity["base_branch"]
    candidates = []
    if identity["mode"] == "remote":
        candidates.append(
            f"refs/remotes/{identity['remote_name_hint']}/{base_branch}"
        )
    candidates.append(f"refs/heads/{base_branch}")
    for candidate in candidates:
        result = _run(
            runner,
            ["git", "show-ref", "--verify", "--quiet", candidate],
            root,
        )
        if result.returncode == 0:
            return candidate
    return None


def _unconfigured_result(root, config_result):
    return {
        "schema": "moduflow.repository-identity.v1",
        "status": "unconfigured",
        "expected": {},
        "observed": {
            "git_root": None,
            "fetch_repositories": [],
            "push_repositories": [],
            "current_branch": None,
            "base_ref": None,
            "provider_repository": None,
            "provider_default_branch": None,
            "provider_archived": None,
            "provider_fork": None,
            "artifact_link_mismatches": [],
        },
        "capabilities": {
            "read": True,
            "execute": False,
            "commit": False,
            "push": False,
            "github_write": False,
            "release": False,
        },
        "reasons": list(config_result["reasons"]),
        "project_root": str(Path(root).resolve()),
    }


def inspect_repository_identity(root, runner=None, provider_check=None):
    """Collect canonical, Git, and provider evidence without performing writes."""
    root = Path(root).resolve()
    runner = runner or _default_runner
    config_result = load_repository_identity(root)
    if not config_result["configured"]:
        return _unconfigured_result(root, config_result)

    identity = config_result["identity"]
    expected = {
        "mode": identity["mode"],
        "provider": identity["provider"],
        "base_branch": identity["base_branch"],
        "lifecycle": identity["lifecycle"],
    }
    if identity["mode"] == "remote":
        expected["repository"] = identity["canonical_repository"]
        expected["remote_name_hint"] = identity["remote_name_hint"]

    reasons = []
    observed = {
        "git_root": None,
        "fetch_repositories": [],
        "push_repositories": [],
        "current_branch": None,
        "base_ref": None,
        "provider_repository": None,
        "provider_default_branch": None,
        "provider_archived": None,
        "provider_fork": None,
        "artifact_link_mismatches": [],
    }

    git_root_result = _run(runner, ["git", "rev-parse", "--show-toplevel"], root)
    if git_root_result.returncode == 0 and (git_root_result.stdout or "").strip():
        observed["git_root"] = (git_root_result.stdout or "").strip()
        if Path(observed["git_root"]).resolve() != root:
            reasons.append(
                _reason(
                    "git_root_mismatch",
                    "Observed Git root does not match the requested project root.",
                )
            )
    else:
        reasons.append(_reason("git_root_unavailable", "Git repository root is unavailable."))

    branch_result = _run(runner, ["git", "rev-parse", "--abbrev-ref", "HEAD"], root)
    if branch_result.returncode == 0:
        observed["current_branch"] = (branch_result.stdout or "").strip() or None

    if observed["git_root"]:
        observed["base_ref"] = _base_ref(root, runner, identity)
        if not observed["base_ref"]:
            reasons.append(
                _reason(
                    "base_branch_missing",
                    "Configured base branch does not exist in local or remote refs.",
                )
            )

    if identity["mode"] == "remote":
        remote_name = identity["remote_name_hint"]
        fetch_result = _run(
            runner,
            ["git", "remote", "get-url", "--all", remote_name],
            root,
        )
        fetch_values = _output_lines(fetch_result)
        if not fetch_values:
            reasons.append(
                _reason("fetch_remote_missing", "Configured fetch remote is unavailable.")
            )
        observed["fetch_repositories"] = _normalized_urls(
            fetch_values,
            identity["provider"],
            "fetch_remote_invalid",
            reasons,
        )
        if observed["fetch_repositories"] and any(
            repository != identity["canonical_repository"]
            for repository in observed["fetch_repositories"]
        ):
            reasons.append(
                _reason(
                    "fetch_remote_mismatch",
                    "Observed fetch repository does not match the canonical repository.",
                )
            )

        push_result = _run(
            runner,
            ["git", "remote", "get-url", "--push", "--all", remote_name],
            root,
        )
        push_values = _output_lines(push_result)
        if not push_values:
            reasons.append(
                _reason("push_remote_missing", "Configured push remote is unavailable.")
            )
        observed["push_repositories"] = _normalized_urls(
            push_values,
            identity["provider"],
            "push_remote_invalid",
            reasons,
        )
        if observed["push_repositories"] and any(
            repository != identity["canonical_repository"]
            for repository in observed["push_repositories"]
        ):
            reasons.append(
                _reason(
                    "push_remote_mismatch",
                    "Observed push repository does not match the canonical repository.",
                )
            )

        if identity["provider"] == "github":
            check = provider_check or _default_github_provider_check
            provider = check(identity["canonical_repository"], root, runner)
            if not provider.get("ok"):
                reasons.append(
                    _reason(
                        provider.get("reason", "provider_unavailable"),
                        provider.get("detail", "Repository provider evidence is unavailable."),
                    )
                )
            else:
                observed["provider_repository"] = provider.get("repository")
                observed["provider_default_branch"] = provider.get("default_branch")
                observed["provider_archived"] = bool(provider.get("archived"))
                observed["provider_fork"] = bool(provider.get("fork"))
                if observed["provider_repository"] != identity["canonical_repository"]:
                    reasons.append(
                        _reason(
                            "provider_repository_mismatch",
                            "Provider repository does not match the canonical repository.",
                        )
                    )
                if observed["provider_default_branch"] != identity["base_branch"]:
                    reasons.append(
                        _reason(
                            "provider_default_branch_mismatch",
                            "Provider default branch does not match the configured base branch.",
                        )
                    )
                if observed["provider_archived"] and identity["lifecycle"] != "archived":
                    reasons.append(
                        _reason(
                            "provider_archive_state_mismatch",
                            "Provider reports the repository as archived.",
                        )
                    )
                if observed["provider_fork"]:
                    reasons.append(
                        _reason(
                            "provider_repository_is_fork",
                            "Provider reports the canonical repository as a fork.",
                        )
                    )

    if identity["lifecycle"] == "read_only":
        reasons.append(_reason("repository_read_only", "Repository lifecycle is read_only."))
    elif identity["lifecycle"] == "archived":
        reasons.append(_reason("repository_archived", "Repository lifecycle is archived."))

    if identity["mode"] == "remote":
        link_findings = audit_repository_links(root, identity["canonical_repository"])
        observed["artifact_link_mismatches"] = [
            finding for finding in link_findings if finding["classification"] == "mismatch"
        ]
        if any(
            finding["write_handoff"]
            for finding in observed["artifact_link_mismatches"]
        ):
            reasons.append(
                _reason(
                    "artifact_write_repository_mismatch",
                    "A write-handoff artifact targets a non-canonical repository.",
                )
            )
    reason_code_set = {reason["code"] for reason in reasons}
    active = identity["lifecycle"] == "active"
    local_base_ok = bool(
        observed["git_root"]
        and observed["base_ref"]
        and "git_root_mismatch" not in reason_code_set
    )
    fetch_ok = identity["mode"] == "local_only" or not reason_code_set.intersection(
        {"fetch_remote_missing", "fetch_remote_invalid", "fetch_remote_mismatch"}
    )
    push_ok = identity["mode"] == "remote" and not reason_code_set.intersection(
        {"push_remote_missing", "push_remote_invalid", "push_remote_mismatch"}
    )
    provider_ok = identity["provider"] != "github" or not reason_code_set.intersection(
        {
            "provider_unavailable",
            "provider_repository_mismatch",
            "provider_default_branch_mismatch",
            "provider_archive_state_mismatch",
            "provider_repository_is_fork",
            "artifact_write_repository_mismatch",
        }
    )
    execute_ok = active and local_base_ok and fetch_ok
    if identity["mode"] == "local_only":
        commit_ok = execute_ok
        push_capability = False
        github_write = False
        release = False
    else:
        commit_ok = execute_ok and push_ok
        push_capability = commit_ok
        github_write = (
            push_capability and identity["provider"] == "github" and provider_ok
        )
        release = github_write

    if identity["lifecycle"] == "read_only":
        status = "read_only"
    elif identity["lifecycle"] == "archived":
        status = "archived"
    elif reason_code_set.intersection(MISMATCH_REASONS):
        status = "mismatch"
    elif reasons:
        status = "unverifiable"
    elif identity["mode"] == "local_only":
        status = "local_only"
    else:
        status = "match"

    return {
        "schema": "moduflow.repository-identity.v1",
        "status": status,
        "expected": expected,
        "observed": observed,
        "capabilities": {
            "read": True,
            "execute": execute_ok,
            "commit": commit_ok,
            "push": push_capability,
            "github_write": github_write,
            "release": release,
        },
        "reasons": reasons,
        "project_root": str(root),
    }


def operation_decision(result, operation):
    """Evaluate one operation against a fresh repository identity result."""
    capability = OPERATION_CAPABILITIES.get(operation)
    if capability is None:
        return {
            "schema": "moduflow.repository-operation-decision.v1",
            "operation": operation,
            "capability": None,
            "allowed": False,
            "reasons": [
                _reason("unsupported_operation", "Repository operation is not supported.")
            ],
            "identity": result,
        }

    allowed = bool(result.get("capabilities", {}).get(capability, False))
    reasons = [] if allowed else list(result.get("reasons", []))
    if not allowed and not reasons:
        reasons.append(
            _reason(
                "capability_not_available",
                f"Repository capability '{capability}' is not available.",
            )
        )
    return {
        "schema": "moduflow.repository-operation-decision.v1",
        "operation": operation,
        "capability": capability,
        "allowed": allowed,
        "reasons": reasons,
        "identity": result,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Inspect canonical repository identity and evaluate one operation."
    )
    parser.add_argument("project_path", nargs="?", default=".")
    parser.add_argument("--operation", choices=sorted(OPERATION_CAPABILITIES))
    parser.add_argument(
        "--provider-check",
        action="store_true",
        help="Request explicit provider evidence (provider-backed operations already require it).",
    )
    args = parser.parse_args()

    result = inspect_repository_identity(args.project_path)
    if args.operation:
        decision = operation_decision(result, args.operation)
        print(json.dumps(decision, ensure_ascii=False, indent=2))
        return 0 if decision["allowed"] else 3

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
