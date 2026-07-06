#!/usr/bin/env python3
import argparse
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass
class CommandResult:
    returncode: int
    stdout: str = ""
    stderr: str = ""


def _read_if_exists(path):
    path = Path(path)
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _default_branch(issue_id):
    return f"codex/{issue_id}"


def _default_pr(issue_id):
    return f"local:{issue_id}:draft-pr-ready"


def _section(text, heading):
    lines = text.splitlines()
    capture = False
    captured = []
    for line in lines:
        if line.strip() == heading:
            capture = True
            continue
        if capture and line.startswith("## "):
            break
        if capture:
            captured.append(line)
    return "\n".join(captured).strip()


def _evidence_or_fallback(text, fallback):
    text = text.strip()
    return text if text else fallback


def _run_command(args, cwd):
    try:
        completed = subprocess.run(
            args,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
    except FileNotFoundError as exc:
        return CommandResult(127, "", str(exc))
    except subprocess.TimeoutExpired as exc:
        return CommandResult(124, exc.stdout or "", exc.stderr or "command timed out")
    return CommandResult(completed.returncode, completed.stdout, completed.stderr)


def github_pr_preflight(root, runner=None):
    root = Path(root).resolve()
    run = runner or _run_command
    result = {
        "schema": "moduflow.github-pr-preflight.v1",
        "project_root": str(root),
        "ok": False,
        "mode": "local-pr-ready",
        "checks": {
            "gh_auth": {"ok": False, "returncode": None, "detail": ""},
            "github_api": {"ok": False, "returncode": None, "detail": ""},
        },
        "errors": [],
        "recommendations": [],
    }

    auth = run(["gh", "auth", "status"], cwd=root)
    result["checks"]["gh_auth"] = {
        "ok": auth.returncode == 0,
        "returncode": auth.returncode,
        "detail": (auth.stderr or auth.stdout).strip(),
    }
    if auth.returncode != 0:
        result["errors"].append("gh auth status failed; GitHub Draft PR creation is unavailable.")
        result["recommendations"].append("Use local PR-ready marker and keep pr.md/human-review.ko.md current.")
        return result

    api = run(["gh", "api", "rate_limit"], cwd=root)
    result["checks"]["github_api"] = {
        "ok": api.returncode == 0,
        "returncode": api.returncode,
        "detail": (api.stderr or api.stdout).strip(),
    }
    if api.returncode != 0:
        detail = (api.stderr or api.stdout).strip() or "GitHub API connectivity check failed."
        result["errors"].append(f"GitHub API preflight failed: {detail}")
        result["recommendations"].append("Do not run gh pr create in this environment; record local PR-ready state instead.")
        return result

    result["ok"] = True
    result["mode"] = "github-draft-pr"
    result["recommendations"].append("GitHub CLI and API are reachable; Draft PR creation may proceed.")
    return result


def _load_ko_descriptions(root):
    path = Path(root) / "workspace" / "issue-descriptions.ko.json"
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    if not isinstance(data, dict):
        return {}
    return {str(k): str(v).strip() for k, v in data.items() if str(v).strip()}


def _title_from_issue(text, issue_id):
    match = re.search(r"^#\s+(.+)$", text or "", re.M)
    if not match:
        return issue_id
    title = re.sub(r"^Issue:\s*", "", match.group(1).strip())
    return title.replace("`", "").strip() or issue_id


def _artifact_check_rows(spec_dir):
    artifacts = [
        ("spec.md", "스펙"),
        ("plan.md", "계획"),
        ("tasks.md", "작업"),
        ("design.md", "화면/설계"),
        ("status.md", "상태/검증"),
        ("review.md", "리뷰"),
        ("pr.md", "PR 핸드오프"),
    ]
    rows = []
    for filename, label in artifacts:
        path = spec_dir / filename
        ko = spec_dir / (filename[:-3] + ".ko.md")
        rows.append((filename, label, path.is_file(), ko.is_file()))
    rows.append(("human-review.ko.md", "한글 검토 패킷", True, True))
    return rows


def _no_issue_declaration_lines(root):
    """Korean packet section body listing releases/no-issue-declarations.md
    entries (issue 075). Declarations are the auditable escape hatch for
    behavior changes shipping without an issue; the human packet is the
    surface where a human actually reads them."""
    path = Path(root) / "releases" / "no-issue-declarations.md"
    if not path.exists():
        return ["- 선언 없음 (선언 파일 미생성)."]
    entries = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith((">", "`")):
            continue
        entries.append(f"- {stripped}")
    if not entries:
        return ["- 선언 없음 — 모든 동작 변경이 이슈에 연결되어 있습니다."]
    header = [
        "다음 변경은 이슈 없이 출시가 선언되었습니다. 각 항목은 인간 git 신원의 blame 검증 대상입니다.",
        "",
    ]
    return header + entries


def build_human_review_packet_ko(root, issue_id, branch="", pr="", reviewer="Reviewer"):
    root = Path(root).resolve()
    spec_dir = root / "specs" / issue_id
    issue_path = root / "issues" / f"{issue_id}.md"
    status_path = spec_dir / "status.md"
    review_path = spec_dir / "review.md"
    branch = branch or _default_branch(issue_id)
    pr = pr or _default_pr(issue_id)
    issue_text = _read_if_exists(issue_path)
    status_text = _read_if_exists(status_path)
    review_text = _read_if_exists(review_path)
    descriptions = _load_ko_descriptions(root)
    title = _title_from_issue(issue_text, issue_id)
    summary = descriptions.get(issue_id) or _evidence_or_fallback(
        _section(issue_text, "## Outcome") or _section(issue_text, "## Summary"),
        "이 이슈의 한글 요약이 아직 등록되지 않았습니다. 상세 페이지의 English 탭과 PR diff를 함께 확인하세요.",
    )
    verification = _evidence_or_fallback(
        _section(status_text, "## Verification"),
        "- 검증 기록이 아직 `status.md`에 정리되지 않았습니다.",
    )
    findings = _evidence_or_fallback(
        _section(review_text, "## Findings") or _section(review_text, "## Subagent Findings"),
        "- 리뷰 결과가 아직 `review.md`에 정리되지 않았습니다.",
    )
    rows = _artifact_check_rows(spec_dir)
    artifact_lines = [
        "| 산출물 | 용도 | 원문 | 한글 보기 |",
        "| --- | --- | --- | --- |",
    ]
    for filename, label, exists, has_ko in rows:
        original = f"`specs/{issue_id}/{filename}`" if exists else "없음"
        ko_status = "가능" if has_ko else "요약/상세 한글 개요로 대체"
        artifact_lines.append(f"| `{filename}` | {label} | {original} | {ko_status} |")

    lines = [
        f"# 한글 검토 패킷: {issue_id}",
        "",
        "> 영어 산출물은 canonical입니다. 이 파일은 사람이 PR을 검토하기 위한 한국어 읽기용 패킷입니다.",
        "",
        "## 먼저 볼 것",
        "",
        f"- 대시보드: `memory/dashboard.html#issue-db`",
        f"- 이슈 상세: `memory/issue-{issue_id}.html`",
        f"- PR/로컬 마커: `{pr}`",
        f"- 브랜치: `{branch}`",
        f"- 리뷰어: `{reviewer}`",
        "",
        "## 이슈 요약",
        "",
        f"- 제목: {title}",
        f"- 설명: {summary}",
        "",
        "## 사람이 확인할 내용",
        "",
        "- 대시보드 DB에서 상태, 설명, 산출물 누락, 검증 플래그를 확인합니다.",
        "- 이슈 상세 페이지에서 `한글` 탭을 먼저 보고, 필요한 경우 `English` 원문으로 내려갑니다.",
        "- GitHub PR이 있으면 diff, conversation, status checks를 확인합니다.",
        "- 아래 보류 조건에 해당하면 승인하지 말고 수정 요청합니다.",
        "",
        "## 산출물 체크",
        "",
        *artifact_lines,
        "",
        "## 검증 요약",
        "",
        verification,
        "",
        "## no-issue 선언 (issue 075)",
        "",
        *_no_issue_declaration_lines(root),
        "",
        "## 리뷰 결과",
        "",
        findings,
        "",
        "## 보류 조건",
        "",
        "- 테스트 또는 release check가 실패했습니다.",
        "- 대시보드/상세 페이지가 생성되지 않았거나 최신 변경을 반영하지 않습니다.",
        "- PR diff가 이슈 범위를 벗어났습니다.",
        "- 사람이 이해할 수 있는 한글 개요 또는 검토 패킷이 없습니다.",
        "- 검토 패킷이 최신 PR diff 또는 로컬 변경 범위를 반영하지 않습니다.",
        "- merge/release 승인자와 승인 근거가 명확하지 않습니다.",
        "",
        "## 승인 체크리스트",
        "",
        "- [ ] 대시보드 DB에서 이슈 상태와 설명을 확인했습니다.",
        "- [ ] 이슈 상세 페이지의 `한글` 탭을 확인했습니다.",
        "- [ ] PR diff 또는 로컬 변경 범위를 확인했습니다.",
        "- [ ] 검증 결과가 통과했거나 실패 사유를 이해했습니다.",
        "- [ ] release 대상이면 rollback/post-release check와 승인 기록을 확인했습니다.",
        "- [ ] 보류 조건에 해당하지 않습니다.",
        "",
        "## 다음 액션",
        "",
        f"- 승인 가능하면 PR에서 approve 또는 로컬에 승인 기록을 남깁니다.",
        f"- 보류하면 `product:review {issue_id}`로 되돌려 수정합니다.",
        "",
    ]
    return "\n".join(lines)


def build_pr_handoff(root, issue_id, branch="", pr="", reviewer="Reviewer", commit_mode="", commit_reason=""):
    root = Path(root).resolve()
    spec_dir = root / "specs" / issue_id
    issue_path = root / "issues" / f"{issue_id}.md"
    spec_path = spec_dir / "spec.md"
    status_path = spec_dir / "status.md"
    review_path = spec_dir / "review.md"
    branch = branch or _default_branch(issue_id)
    pr = pr or _default_pr(issue_id)
    dashboard_path = "memory/dashboard.html"
    issue_html_path = f"memory/issue-{issue_id}.html"

    issue_text = _read_if_exists(issue_path)
    spec_text = _read_if_exists(spec_path)
    status_text = _read_if_exists(status_path)
    review_text = _read_if_exists(review_path)
    verification_evidence = _evidence_or_fallback(
        _section(status_text, "## Verification"),
        "- Verification evidence has not been recorded yet.",
    )
    review_evidence = _evidence_or_fallback(
        _section(review_text, "## Findings") or _section(review_text, "## Subagent Findings"),
        "- Review findings have not been recorded yet.",
    )
    visual_evidence = _evidence_or_fallback(
        _section(review_text, "## Visual Handoff") or _section(status_text, "## Visual Handoff"),
        f"- Dashboard: `{dashboard_path}`.\n- Issue drill-down: `{issue_html_path}`.",
    )
    fallback_reason = ""
    if pr.startswith("local:"):
        fallback_reason = (
            "GitHub Draft PR URL is not recorded yet. This local PR-ready marker preserves review state "
            "until GitHub sync creates or mirrors the PR."
        )

    lines = [
        f"# PR Handoff: {issue_id}",
        "",
        "## Purpose",
        "",
        "Make the pull request the visible review surface instead of waiting until all local review work is finished.",
        "Use a Draft PR or a local PR-ready marker early, then attach review, verification, and dashboard evidence to it as work progresses.",
        "",
        "## Draft PR",
        "",
        f"- Branch: `{branch}`",
        f"- PR: `{pr}`",
        f"- Reviewer: `{reviewer}`",
        f"- Fallback reason: {fallback_reason or 'GitHub Draft PR URL is available or expected to be supplied by the workflow.'}",
        "- Preferred timing: create a Draft PR after the first meaningful commit, or record a local PR-ready marker when GitHub write access is unavailable.",
        "- Do not merge from this handoff. Merge remains gated by Human approval, required reviews, and Required status checks.",
        f"- Commit mode: `{commit_mode or 'local-git-write'}`"
        + (f" — {commit_reason}" if commit_mode and commit_mode != "local-git-write" and commit_reason else ""),
        "",
        "## Commands",
        "",
        f"```bash\npython3 scripts/project_pr.py . --issue-id {issue_id} --write\n```",
        "",
        "```bash\npython3 scripts/project_workflow.py . --pr-state --issue-id "
        f"{issue_id} --pr \"{pr}\" --reviewer \"{reviewer}\"\n```",
        "",
        f"- Continue review: `product:review {issue_id}`",
        f"- Refresh PR handoff: `product:pr {issue_id}`",
        "",
        "## PR Body Contract",
        "",
        "- Summary: what changed and why.",
        "- Verification: local tests, release checks, CI/status checks, and known gaps.",
        f"- Dashboard: `{dashboard_path}`.",
        f"- Issue drill-down: `{issue_html_path}`.",
        f"- Korean human-review packet: `specs/{issue_id}/human-review.ko.md`.",
        "- Review findings: implementation, QA, and PM/spec review results.",
        "- Human approval: who reviewed the dashboard, PR diff, and merge readiness.",
        "",
        "## Evidence To Mirror",
        "",
        "### Verification",
        "",
        verification_evidence,
        "",
        "### Review Findings",
        "",
        review_evidence,
        "",
        "### Visual Evidence",
        "",
        visual_evidence,
        "",
        "## Approval Record",
        "",
        f"- Dashboard reviewer: `{reviewer}` or assigned reviewer before merge.",
        f"- PR diff reviewer: `{reviewer}` or assigned reviewer before merge.",
        "- Merge approver: human approval required; not granted by this handoff.",
        "- Deployment approver: required only when a protected deployment environment is configured.",
        "",
        "## Human Checkpoints",
        "",
        "- Spec/plan approval before implementation starts.",
        "- Dashboard and issue drill-down inspection after review.",
        "- GitHub PR diff, conversation, and status checks before approval.",
        "- Merge and deployment approval through protected branch or environment gates.",
        "",
        "## GitHub Gate Alignment",
        "",
        "- PR review can approve, comment, or request changes.",
        "- Required status checks must pass before merge when branch protection is configured.",
        "- Required reviewers or CODEOWNERS remain the merge authority.",
        "- Deployment environments may add a separate approval gate after merge or before release.",
        "",
    ]
    if issue_text or spec_text or status_text or review_text:
        lines.extend(
            [
                "## Source Snapshot",
                "",
                f"- Issue bytes: {len(issue_text.encode('utf-8'))}",
                f"- Spec bytes: {len(spec_text.encode('utf-8'))}",
                f"- Status bytes: {len(status_text.encode('utf-8'))}",
                f"- Review bytes: {len(review_text.encode('utf-8'))}",
                "",
            ]
        )
    return "\n".join(lines)


def write_pr_handoff(root, issue_id, branch="", pr="", reviewer="Reviewer", commit_mode="", commit_reason=""):
    root = Path(root).resolve()
    target = root / "specs" / issue_id / "pr.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        build_pr_handoff(
            root, issue_id, branch=branch, pr=pr, reviewer=reviewer,
            commit_mode=commit_mode, commit_reason=commit_reason,
        ),
        encoding="utf-8",
    )
    human_target = target.parent / "human-review.ko.md"
    human_target.write_text(
        build_human_review_packet_ko(root, issue_id, branch=branch, pr=pr, reviewer=reviewer),
        encoding="utf-8",
    )
    return target


def main():
    parser = argparse.ArgumentParser(description="Generate ModuFlow draft PR handoff artifacts.")
    parser.add_argument("project_path", nargs="?", default=".")
    parser.add_argument("--issue-id", default="")
    parser.add_argument("--branch", default="")
    parser.add_argument("--pr", default="")
    parser.add_argument("--reviewer", default="Reviewer")
    parser.add_argument("--commit-mode", default="", help="local-git-write | github-api-commit | blocked")
    parser.add_argument("--commit-reason", default="")
    parser.add_argument("--write", action="store_true")
    parser.add_argument(
        "--github-preflight",
        action="store_true",
        help="Check gh auth and GitHub API reachability before attempting Draft PR creation.",
    )
    args = parser.parse_args()

    if args.github_preflight:
        result = github_pr_preflight(args.project_path)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["ok"] else 2

    if not args.issue_id:
        parser.error("--issue-id is required unless --github-preflight is used")

    if args.write:
        path = write_pr_handoff(
            args.project_path,
            args.issue_id,
            branch=args.branch,
            pr=args.pr,
            reviewer=args.reviewer,
            commit_mode=args.commit_mode,
            commit_reason=args.commit_reason,
        )
        print(path)
    else:
        print(
            build_pr_handoff(
                args.project_path,
                args.issue_id,
                branch=args.branch,
                pr=args.pr,
                reviewer=args.reviewer,
                commit_mode=args.commit_mode,
                commit_reason=args.commit_reason,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
