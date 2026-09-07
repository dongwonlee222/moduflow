#!/usr/bin/env python3
import collections
import importlib.util
import json
import re
import sys
from pathlib import Path

try:
    from scripts.project_repository_identity import audit_repository_links
except ModuleNotFoundError:
    from project_repository_identity import audit_repository_links

try:
    from scripts import project_analysis_run, project_artifact_registry, project_operation, project_registry
except ImportError:  # pragma: no cover - direct script execution fallback
    import project_analysis_run
    import project_artifact_registry
    import project_operation
    import project_registry


REQUIRED_PATHS = [
    ".moduflow/config.json",
    ".moduflow/state.json",
]

# ---------------------------------------------------------------------------
# 129: section content rules.
#
# Sections that a reader depends on were named and never checked. A bug issue's
# cause could be an unverified guess — issue 126 labelled its guess honestly and
# still sent the next reader to the wrong function — and a spec's decision
# request could be four noun phrases with nothing to decide with (112 §15).
#
# The rules below are data. Adding one is appending a row, not adding a branch;
# tests/test_section_content_rules.py asserts that by appending one at runtime.
# ---------------------------------------------------------------------------

TYPE_TOKENS = ("bug", "feature", "chore", "spike")

# Scoped to `## 원인` on purpose. `~것 같` is ordinary Korean everywhere else,
# so an unscoped ban would be unusable. The section had to exist first.
HEDGE_PHRASES = (
    "추측",
    "~것 같",
    "~로 보임",
    "hypothesis",
    "suspicion",
    "likely",
    "probably",
)

DECISION_SLOTS = (
    "왜 이 결정이 필요한가요?",
    "지금 무엇이 잘못되고 있나요?",
    "실제로 측정된 예시",
    "다른 선택지와 그 비용",
    "승인하면 무엇이 달라지나요?",
)

SectionRule = collections.namedtuple(
    "SectionRule",
    "kind type_token section required message content",
)
SectionRule.__new__.__defaults__ = (None,)


def parse_type_token(text):
    """`- Type: bug — reported 2026-09-06` -> ("bug", "reported 2026-09-06").

    The tail is kept because today's field holds provenance, not kind, and
    replacing it outright would delete the only information it carries. A value
    whose first token is not one of TYPE_TOKENS yields None: 107 legacy issues
    have prose there and must be skipped rather than failed.
    """
    match = re.search(r"^- Type:\s*(.+)$", text, re.M)
    if not match:
        return (None, "")
    value = match.group(1).strip()
    head, separator, tail = value.partition("—")
    token = head.strip().lower()
    if token not in TYPE_TOKENS:
        return (None, value)
    return (token, tail.strip() if separator else "")


def section_body(text, heading):
    """Body of one `## Heading` section, or None when it is absent.

    A leading section number is optional: specs 103 and 112 write
    `## 17. Human Review Decisions` and `## 15. Human Review Decisions`, and
    both are the same heading.
    """
    title = re.escape(heading.lstrip("# ").strip())
    match = re.search(
        rf"^##\s+(?:\d+\.\s+)?{title}\s*$(.*?)(?=^## |\Z)",
        text,
        re.M | re.S,
    )
    return match.group(1) if match else None


def cause_content(body, source):
    findings = []
    if body.strip() != "원인 미상" and "```" not in body:
        findings.append(
            f"{source}: `## 원인`에는 실제 실행 출력(``` 블록)이나 `원인 미상`만 "
            "씁니다. 재현하지 못했으면 `원인 미상`으로 남기세요."
        )
    for hedge in HEDGE_PHRASES:
        needle = hedge.lstrip("~")
        if needle in body:
            findings.append(
                f'{source}: `## 원인`에 추측 표현 "{needle}"이 있습니다. '
                "확인한 것만 쓰거나 `원인 미상`으로 남기세요."
            )
    return findings


def decision_content(body, source):
    findings = []
    for match in re.finditer(r"^- (.+?)(?=^- |\Z)", body, re.M | re.S):
        block = match.group(1)
        head = block.splitlines()[0].strip()
        if head.startswith("[확인만]") or "[approved" in head:
            continue
        if not head.startswith("[사장님 결정]"):
            findings.append(
                f'{source}: 결정 "{head[:40]}"에 표시가 없습니다. '
                "`[사장님 결정]` 또는 `[확인만]`을 붙이세요."
            )
            continue
        for slot in DECISION_SLOTS:
            if slot not in block:
                findings.append(
                    f'{source}: 결정 "{head[:40]}"에 `{slot}` 칸이 없습니다.'
                )
    return findings


# 2026-09-07: written, then taken back out of SECTION_RULES within the hour.
# Requiring `## 안 고치면` on every issue fired on 35 test fixtures across the
# suite — every fixture that builds a minimal issue would have to carry the
# section. The rule is right and the scoping was wrong; it goes back in once
# workspace/goal.md is rewritten into something an issue can actually be
# measured against, with a scope that does not catch fixtures.
def blocked_without_this_content(body, source):
    findings = []
    text = body.strip()
    if not text or text.startswith("{{") or "TODO" in text:
        findings.append(
            f"{source}: `## 안 고치면` 칸이 비어 있습니다. "
            "이걸 안 고치면 누가 무엇을 못 하는지 한 문장으로 쓰세요."
        )
    return findings


SECTION_RULES = [
    SectionRule(
        kind="issue",
        type_token="bug",
        section="## 원인",
        required=True,
        message=(
            "{source}: `- Type: bug` 이슈에는 `## 원인` 섹션이 필요합니다. "
            "실행 출력을 붙이거나 `원인 미상`이라고 쓰세요."
        ),
        content=cause_content,
    ),
    SectionRule(
        kind="issue",
        type_token="spike",
        section="## Goal",
        required=True,
        message="{source}: `- Type: spike` 이슈에는 `## Goal`이 필요합니다 (무엇을 알아낼 것인가).",
    ),
    SectionRule(
        kind="issue",
        type_token="spike",
        section="## Findings",
        required=True,
        message="{source}: `- Type: spike` 이슈에는 `## Findings`가 필요합니다 (알아낸 것).",
    ),
    SectionRule(
        kind="spec",
        type_token=None,
        section="## Human Review Decisions",
        required=False,
        message="",
        content=decision_content,
    ),
]


def check_sections(text, source, errors, *, kind="issue"):
    """Apply every SECTION_RULES row that matches this artifact."""
    token, _ = parse_type_token(text)
    for rule in SECTION_RULES:
        if rule.kind != kind:
            continue
        if rule.kind == "issue" and token is None:
            continue
        if rule.type_token is not None and rule.type_token != token:
            continue
        body = section_body(text, rule.section)
        if body is None:
            if rule.required:
                errors.append(rule.message.format(source=source))
            continue
        if rule.content is not None:
            errors.extend(rule.content(body, source))

OPTIONAL_CAPABILITY_PATHS = {
    "profile": [
        ".moduflow/project-profile.md",
        ".moduflow/environments.json",
        ".moduflow/integrations.json",
    ],
    "knowledge": [
        "knowledge/index.md",
        "knowledge/decisions",
        "knowledge/benchmarks",
        "knowledge/reports",
        "knowledge/research",
        "knowledge/data-notes",
        "knowledge/references",
    ],
    "memory": [
        "memory/index.md",
        "memory/deliverables",
        "memory/decisions",
        "memory/evidence",
        "memory/meetings",
        "memory/releases",
        "memory/notes",
        "memory/references",
    ],
    "workflow": [
        "workflow/review-gates.md",
        "workflow/approval-policy.md",
        "workflow/release-policy.md",
        "workflow/handoff.md",
        "workflow/risks.md",
    ],
}

JSON_FILES = [
    ".moduflow/config.json",
    ".moduflow/state.json",
]

OPTIONAL_JSON_FILES = [
    ".moduflow/environments.json",
    ".moduflow/integrations.json",
    "workflow/team-state.json",
]


def load_project_loop():
    path = Path(__file__).resolve().parent / "project_loop.py"
    spec = importlib.util.spec_from_file_location("project_loop", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_project_lifecycle():
    path = Path(__file__).resolve().parent / "project_lifecycle.py"
    spec = importlib.util.spec_from_file_location("project_lifecycle", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_project_issue_schema():
    path = Path(__file__).resolve().parent / "project_issue_schema.py"
    spec = importlib.util.spec_from_file_location("project_issue_schema", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_project_production():
    path = Path(__file__).resolve().parent / "project_production.py"
    spec = importlib.util.spec_from_file_location("project_production_validation", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


LINK_RE = re.compile(r"`(?P<path>[^`]+)`")


def read_text_if_exists(path):
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def artifact_paths(root, errors, *, project_context=None):
    context = project_registry.context_for_operation(
        root,
        project_context=project_context,
    )
    return dict(context["relative_paths"])


def active_loop_state(root, project_loop, *, project_context=None):
    context = project_registry.context_for_operation(
        root,
        project_context=project_context,
    )
    path = project_registry.canonical_child_path(
        context,
        "workspace",
        "loop-state.json",
    )
    if not path.exists():
        return None
    return project_loop.load_loop_state(root, project_context=context)


# 147: a Workflow Tasks row is a plan, not a manifest. The checklist names all
# four artifacts an issue *will* produce, and reading it as files that must
# already exist meant an issue could not start until it was finished — issue 104
# was refused for a missing review.md, which is written last.
#
# The rule is what the checkbox already meant: a checked row's artifact must
# exist, an unchecked row's must not be required. Links elsewhere in the issue
# keep today's behaviour, because `## Links` and `## Entry Points` name things
# that exist.
_WORKFLOW_SECTION_RE = re.compile(r"^##\s+Workflow Tasks\s*$(.*?)(?=^## |\Z)", re.M | re.S)
_UNCHECKED_ROW_RE = re.compile(r"^- \[ \].*(?:\n(?![-#]).*)*", re.M)


def _without_unfinished_workflow_rows(issue_text):
    """Blank out unchecked Workflow Tasks rows before links are collected."""
    match = _WORKFLOW_SECTION_RE.search(issue_text)
    if not match:
        return issue_text
    body = match.group(1)
    pruned = _UNCHECKED_ROW_RE.sub("", body)
    return issue_text[: match.start(1)] + pruned + issue_text[match.end(1) :]


def linked_artifacts(issue_text, project_paths=None):
    issue_text = _without_unfinished_workflow_rows(issue_text)
    project_paths = project_paths or {
        "specs": "specs",
        "workspace": "workspace",
        "memory": "memory",
    }
    prefixes = tuple(
        project_paths[role].rstrip("/") + "/"
        for role in ("specs", "workspace", "memory")
    )
    linked = []
    for match in LINK_RE.finditer(issue_text):
        value = match.group("path").strip()
        if any(ch in value for ch in "<>{}"):
            continue  # placeholder path (e.g. specs/<id>/{spec,plan,tasks}.md), not a real link
        if value.startswith(prefixes):
            linked.append(value)
    return linked


def iter_memory_markdown(root, *, project_context=None):
    context = project_registry.context_for_operation(
        root,
        project_context=project_context,
    )
    memory_root = project_registry.canonical_path(context, "memory")
    if not memory_root.exists():
        return []
    return sorted(path for path in memory_root.glob("*/*.md") if path.is_file())


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


def validate_memory_links(root, errors, *, project_context=None):
    context = project_registry.context_for_operation(
        root,
        project_context=project_context,
    )
    for memory_file in iter_memory_markdown(root, project_context=context):
        metadata = parse_frontmatter(memory_file.read_text(encoding="utf-8"))
        relative_memory = str(memory_file.relative_to(root))
        for linked in parse_list_value(metadata.get("source_artifacts", "[]")):
            if linked and not (root / linked).exists():
                errors.append(f"{relative_memory}: broken source_artifacts link: {linked}")
        candidate_prefix = project_registry.canonical_relative_path(
            context,
            "memory",
            ".candidates",
        ).rstrip("/") + "/"
        if relative_memory.startswith(candidate_prefix) and metadata.get("status") != "candidate":
            errors.append(f"{relative_memory}: candidate memory must have status: candidate")


def validate_team_workflow_state(root, errors, *, project_context=None):
    context = project_registry.context_for_operation(
        root,
        project_context=project_context,
    )
    team_state_path = project_registry.canonical_child_path(
        context,
        "workflow",
        "team-state.json",
    )
    workflow_label = project_registry.canonical_relative_path(
        context,
        "workflow",
        "team-state.json",
    )
    if not team_state_path.exists():
        return
    state = read_json(team_state_path, errors)
    if not state:
        return
    if state.get("schema") != "moduflow.team-state.v1":
        errors.append(f"{workflow_label}: schema must be moduflow.team-state.v1")
        return
    items = state.get("items")
    if not isinstance(items, list):
        errors.append(f"{workflow_label}: items must be a list")
        return
    for item in items:
        issue_id = item.get("issue_id")
        status = item.get("status")
        if not issue_id:
            errors.append(f"{workflow_label}: item missing issue_id")
            continue
        if not project_registry.canonical_child_path(
            context,
            "issues",
            f"{issue_id}.md",
        ).exists():
            errors.append(f"{workflow_label}: item references missing issue {issue_id}")
        if status == "active" and not item.get("branch"):
            errors.append(f"{workflow_label}: active state for {issue_id} requires branch")
        if status == "active" and not (item.get("assignee") or item.get("locked_by")):
            errors.append(f"{workflow_label}: active state for {issue_id} requires assignee or locked_by")
        if status == "review" and not (item.get("reviewer") and item.get("pr")):
            errors.append(f"{workflow_label}: review state requires reviewer and pr for {issue_id}")


def validate_active_issue_links(
    root,
    issue_id,
    errors,
    project_paths,
    *,
    project_context=None,
):
    context = project_registry.context_for_operation(
        root,
        project_context=project_context,
    )
    issue_file = project_registry.canonical_child_path(
        context,
        "issues",
        f"{issue_id}.md",
    )
    if not issue_file.exists():
        return
    try:
        issue_text = issue_file.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return
    for relative in linked_artifacts(issue_text, project_paths):
        if not (root / relative).exists():
            source = issue_file.relative_to(root).as_posix()
            errors.append(f"{source}: linked artifact missing: {relative}")


def validate_active_state_views(
    root,
    active_issue_id,
    next_command,
    errors,
    project_paths,
    *,
    project_context=None,
):
    # 048: lifecycle canonical is the issue file Status; .moduflow/state.json is the
    # live summary. The dashboard must mention the active issue. (next_command is NOT
    # checked here — the dashboard's "## Next Command" is fixed to product:status by a
    # separate rule; coupling it to state.next_command was the retired loop-state gate.
    # roadmap.md is a narrative roadmap, not an active-issue tracker — not gated.)
    if not active_issue_id:
        return
    context = project_registry.context_for_operation(
        root,
        project_context=project_context,
    )
    dashboard = project_registry.canonical_child_path(
        context,
        "workspace",
        "dashboard.md",
    )
    dashboard_text = read_text_if_exists(dashboard)
    if dashboard.exists() and active_issue_id not in dashboard_text:
        source = dashboard.relative_to(root).as_posix()
        errors.append(f"{source}: missing active_issue_id {active_issue_id}")


def validate_next_command_matches_phase(root, loop_state, project_loop, errors):
    if not loop_state:
        return
    active_issue_id = loop_state.get("active_issue_id")
    if not active_issue_id:
        return
    phase = project_loop.infer_issue_phase(root, active_issue_id)
    expected = project_loop.recommend_next_command(active_issue_id, phase)
    actual = loop_state.get("next_command")
    if actual != expected:
        errors.append(f"workspace/loop-state.json: next_command {actual} should be {expected}")


def validate_schema_gates(
    root,
    issue_evaluation,
    errors,
    project_paths,
    *,
    project_context=None,
):
    context = project_registry.context_for_operation(
        root,
        project_context=project_context,
    )
    # 048: gate keys off .moduflow/state.json (live summary), not loop-state.json
    # (retired/dormant — frozen at issue 040, a prior goal). loop-state's
    # next_command/phase coupling is no longer a lifecycle gate.
    state = read_json(root / ".moduflow" / "state.json", errors)
    if not state:
        return []
    active_issue_id = (state.get("active_issue") or "").strip()
    if active_issue_id:
        validate_active_issue_links(
            root,
            active_issue_id,
            errors,
            project_paths,
            project_context=context,
        )
    validate_active_state_views(
        root,
        active_issue_id,
        state.get("next_command"),
        errors,
        project_paths,
        project_context=context,
    )
    # 048: retain only consensus drift here. Shared issue diagnostics are emitted
    # once from issue_evaluation below, so lifecycle translation must not duplicate
    # schema, projection, or dependency diagnostics.
    try:
        lifecycle_drift = load_project_lifecycle().consensus_drift(
            root,
            issue_evaluation,
            project_context=context,
        )
        for d in lifecycle_drift:
            errors.append(f"lifecycle drift: {d} (run project_lifecycle.py --sync)")
    except Exception:
        lifecycle_drift = []
    return lifecycle_drift


def validate_issue_status_lines(
    root,
    warnings,
    project_paths,
    *,
    project_context=None,
):
    # 066 follow-up: every issue file must carry the canonical `**Status: ...**`
    # line or project_lifecycle.py silently defaults it to backlog. Warning, not
    # error — target projects mid-adoption may still carry legacy files.
    context = project_registry.context_for_operation(
        root,
        project_context=project_context,
    )
    try:
        issues_dir = project_registry.canonical_path(context, "issues")
    except ValueError:
        # The shared issue-schema evaluation below owns the actionable
        # containment diagnostic. Do not follow or expose an unsafe root.
        return
    if not issues_dir.is_dir():
        return
    for issue_file in sorted(issues_dir.glob("*.md")):
        try:
            issue_text = issue_file.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            continue
        if not re.search(r"\*\*Status:", issue_text):
            source = issue_file.relative_to(root).as_posix()
            warnings.append(
                f"{source}: missing canonical `**Status: ...**` line "
                "(lifecycle parser will report it as backlog)"
            )


def validate_section_content(root, errors, *, project_context=None):
    # 129: run SECTION_RULES over every issue and spec. Issues whose `- Type:`
    # holds prose rather than a token are skipped by check_sections — 107 of
    # them predate the closed set, and failing history is how a rule gets
    # switched off.
    context = project_registry.context_for_operation(
        root,
        project_context=project_context,
    )
    try:
        issues_dir = project_registry.canonical_path(context, "issues")
        specs_dir = project_registry.canonical_path(context, "specs")
    except ValueError:
        # The shared issue-schema evaluation owns the containment diagnostic.
        return
    # Only open work is checked. A `done` or `superseded` artifact is history:
    # its decisions were settled by whatever standard applied then, and failing
    # it now would make the whole rule something to switch off rather than fix.
    def is_open(issue_id):
        path = issues_dir / f"{issue_id}.md"
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            return False
        match = re.search(r"\*\*Status:\s*([a-z-]+)", text)
        return bool(match) and match.group(1) in {"backlog", "active"}

    targets = []
    if issues_dir.is_dir():
        for path in sorted(issues_dir.glob("*.md")):
            if is_open(path.stem):
                targets.append((path, "issue"))
    if specs_dir.is_dir():
        for path in sorted(specs_dir.glob("*/spec.md")):
            if is_open(path.parent.name):
                targets.append((path, "spec"))
    for path, kind in targets:
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            continue
        check_sections(text, path.relative_to(root).as_posix(), errors, kind=kind)


def validate_repository_links(root, errors, warnings, *, project_context=None):
    for finding in audit_repository_links(
        root,
        project_context=project_context,
    ):
        if finding["classification"] != "mismatch":
            continue
        location = f"{finding['artifact']}:{finding['line']}"
        if finding["write_handoff"]:
            errors.append(
                f"{location}: non-canonical repository link is unsafe for a write handoff "
                f"({finding['repository']})"
            )
        else:
            warnings.append(
                f"{location}: non-canonical repository link needs an explicit mirror/reference role "
                f"({finding['repository']})"
            )


def read_json(path, errors):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"{path}: invalid JSON ({exc})")
        return None


def read_config_paths(root, errors):
    config_path = root / ".moduflow" / "config.json"
    if not config_path.exists():
        return {}
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    paths = config.get("paths", {})
    return paths if isinstance(paths, dict) else {}


def required_paths(root, errors, project_paths=None):
    paths = project_paths or read_config_paths(root, errors)
    issues = paths.get("issues", "issues")
    specs = paths.get("specs", "specs")
    workspace = paths.get("workspace", "workspace")
    return REQUIRED_PATHS + [
        issues,
        specs,
        f"{workspace}/inbox.md",
        f"{workspace}/opportunities.md",
        f"{workspace}/roadmap.md",
        f"{workspace}/dashboard.md",
    ]


def issue_schema_summary(evaluation):
    unique = {}
    for issue in evaluation.get("issues", []):
        for diagnostic in issue.get("diagnostics", []):
            normalized = dict(diagnostic)
            identity = (
                normalized.get("severity"),
                normalized.get("code"),
                normalized.get("source_path"),
                normalized.get("field"),
                repr(normalized.get("current")),
                repr(normalized.get("expected")),
                normalized.get("message"),
                normalized.get("recommendation"),
            )
            unique.setdefault(identity, normalized)
    diagnostics = sorted(
        unique.values(),
        key=lambda diagnostic: (
            0 if diagnostic.get("severity") == "error" else 1,
            diagnostic.get("source_path") or "",
            diagnostic.get("issue_id") or "",
            diagnostic.get("code") or "",
            diagnostic.get("field") or "",
            diagnostic.get("message") or "",
            diagnostic.get("recommendation") or "",
        ),
    )
    return {
        "errors": sum(
            diagnostic.get("severity") == "error"
            for diagnostic in diagnostics
        ),
        "warnings": sum(
            diagnostic.get("severity") == "warning"
            for diagnostic in diagnostics
        ),
        "codes": sorted(
            {
                diagnostic.get("code")
                for diagnostic in diagnostics
                if diagnostic.get("code")
            }
        ),
        "diagnostics": diagnostics,
    }


def format_issue_diagnostic(diagnostic):
    details = []
    if diagnostic.get("field") is not None:
        details.append(f"Field: {diagnostic['field']}.")
    if diagnostic.get("current") is not None:
        details.append(
            "Current: "
            + json.dumps(
                diagnostic["current"],
                ensure_ascii=False,
                sort_keys=True,
            )
            + "."
        )
    if diagnostic.get("expected") is not None:
        details.append(
            "Expected: "
            + json.dumps(
                diagnostic["expected"],
                ensure_ascii=False,
                sort_keys=True,
            )
            + "."
        )
    detail_text = (" " + " ".join(details)) if details else ""
    return (
        f"{diagnostic.get('code') or 'ISSUE_DIAGNOSTIC'} "
        f"[{diagnostic.get('source_path') or 'unknown source'}]: "
        f"{diagnostic.get('message') or 'Issue schema diagnostic.'}"
        f"{detail_text} "
        f"Recommendation: "
        f"{diagnostic.get('recommendation') or 'Run product:doctor.'}"
    )


def deduplicate_messages(messages):
    return list(dict.fromkeys(messages))


def validate_artifact_registry(root, context):
    """Use the canonical metadata reader, including links beyond the UI-sized limit."""
    try:
        read = project_artifact_registry.read_artifact_registry(root, project_context=context, limit=sys.maxsize)
    except (ValueError, project_operation.ProjectOperationDenied):
        return {"initialized": False, "metadata_valid": False, "total": 0, "entries": [],
                "diagnostics": [project_artifact_registry.diagnostic("REGISTRY_READ_UNAVAILABLE")]}
    missing_codes = {"REGISTRY_NOT_INITIALIZED", "KNOWLEDGE_HOME_MISSING"}
    return {"initialized": not any(d["code"] in missing_codes for d in read["diagnostics"]),
            "metadata_valid": read["metadata_valid"], "total": read["total"],
            "entries": [{k: entry[k] for k in ("id", "metadata_valid", "source_availability", "freshness", "share_status")}
                        for entry in read["entries"]], "diagnostics": read["diagnostics"]}


def validate_analysis_runs(root, context):
    """Use the canonical analysis-run reader (working view), including the full list."""
    try:
        read = project_analysis_run.read_analysis_runs(root, project_context=context, limit=sys.maxsize)
    except (ValueError, project_operation.ProjectOperationDenied):
        return {"initialized": False, "metadata_valid": False, "total": 0, "entries": [],
                "diagnostics": [project_analysis_run.diagnostic("RUNS_READ_UNAVAILABLE")]}
    # RUNS_NOT_INITIALIZED must surface as a warning (missing workspace/analysis-runs.md
    # is a "not set up yet" signal, not a defect), mirroring REGISTRY_NOT_INITIALIZED.
    diagnostics = [
        dict(item, severity="warning") if item["code"] == "RUNS_NOT_INITIALIZED" else item
        for item in read["diagnostics"]
    ]
    not_initialized = any(item["code"] == "RUNS_NOT_INITIALIZED" for item in diagnostics)
    metadata_valid = not not_initialized and not any(item["severity"] == "error" for item in diagnostics)
    return {"initialized": not not_initialized, "metadata_valid": metadata_valid, "total": read["total"],
            "entries": [{k: entry[k] for k in ("id", "issue_id", "run_state", "validation_state",
                                                 "approval_state", "decision_state")}
                        for entry in read["entries"]], "diagnostics": diagnostics}


def validate_project(path, *, project_context=None):
    root = Path(path).resolve()
    errors = []
    warnings = []
    context = project_registry.context_for_operation(
        root,
        project_context=project_context,
    )
    issue_schema_module = load_project_issue_schema()
    project_paths = dict(context["relative_paths"])

    for relative in required_paths(root, errors, project_paths):
        if not (root / relative).exists():
            errors.append(f"Missing required project artifact: {relative}")

    for capability, paths in OPTIONAL_CAPABILITY_PATHS.items():
        missing = []
        for relative in paths:
            role = capability if capability in {"knowledge", "memory", "workflow"} else None
            if role:
                suffix = Path(relative).relative_to(role)
                target = project_registry.canonical_child_path(context, role, suffix)
                label = project_registry.canonical_relative_path(context, role, suffix)
            else:
                target = root / relative
                label = relative
            if not target.exists():
                missing.append(label)
        if missing:
            warnings.append(
                f"Optional project capability not initialized: {capability} ({', '.join(missing)})"
            )

    parsed = {}
    json_targets = [(relative, root / relative) for relative in JSON_FILES]
    json_targets.extend(
        (relative, root / relative)
        for relative in OPTIONAL_JSON_FILES
        if Path(relative).parts[0] != "workflow"
    )
    workflow_state = project_registry.canonical_child_path(
        context,
        "workflow",
        "team-state.json",
    )
    json_targets.append((workflow_state.relative_to(root).as_posix(), workflow_state))
    for relative, target in json_targets:
        if target.exists():
            parsed[relative] = read_json(target, errors)

    config = parsed.get(".moduflow/config.json")
    if config and config.get("schema") != "moduflow.config.v1":
        errors.append(".moduflow/config.json: schema must be moduflow.config.v1")

    state = parsed.get(".moduflow/state.json")
    if state:
        if state.get("schema") != "moduflow.state.v1":
            errors.append(".moduflow/state.json: schema must be moduflow.state.v1")
        if "phase" not in state:
            errors.append(".moduflow/state.json: missing phase")
        if "next_command" not in state:
            errors.append(".moduflow/state.json: missing next_command")

    issue_evaluation = issue_schema_module.evaluate_project(
        root,
        project_paths=project_paths,
    )
    issue_schema = issue_schema_summary(issue_evaluation)
    for diagnostic in issue_schema["diagnostics"]:
        rendered = format_issue_diagnostic(diagnostic)
        if diagnostic.get("severity") == "warning":
            warnings.append(rendered)
        else:
            errors.append(rendered)

    project_loop = load_project_loop()
    errors.extend(project_loop.validate_loop_state(root, project_context=context))
    lifecycle_drift = validate_schema_gates(
        root,
        issue_evaluation,
        errors,
        project_paths,
        project_context=context,
    )
    validate_memory_links(root, errors, project_context=context)
    production = load_project_production().validate_production_project(
        root,
        project_context=context,
    )
    errors.extend(production["errors"])
    warnings.extend(production["warnings"])
    validate_team_workflow_state(root, errors, project_context=context)
    validate_issue_status_lines(
        root,
        warnings,
        project_paths,
        project_context=context,
    )
    validate_section_content(root, errors, project_context=context)
    validate_repository_links(
        root,
        errors,
        warnings,
        project_context=context,
    )
    artifact_registry = validate_artifact_registry(root, context)
    for finding in artifact_registry["diagnostics"]:
        message = f"{finding['code']} [{finding['artifact_id']}:{finding['field']}]: {finding['next_action']}"
        if finding["severity"] == "error":
            errors.append(message)
        elif finding["severity"] == "warning":
            warnings.append(message)
    analysis_runs = validate_analysis_runs(root, context)
    for finding in analysis_runs["diagnostics"]:
        message = (
            f"{finding['code']} [{finding.get('run_id', '')}:{finding['field']}]: "
            "Review workspace/analysis-runs.md diagnostics; run product:doctor for next steps."
        )
        if finding["severity"] == "error":
            errors.append(message)
        elif finding["severity"] == "warning":
            warnings.append(message)
    errors = deduplicate_messages(errors)
    warnings = deduplicate_messages(warnings)

    return {
        "schema": "moduflow.project-validation.v1",
        "project_root": str(root),
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
        "issue_schema": issue_schema,
        "lifecycle_drift": lifecycle_drift,
        "artifact_registry": artifact_registry,
        "analysis_runs": analysis_runs,
    }


def main():
    result = validate_project(sys.argv[1] if len(sys.argv) > 1 else ".")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
