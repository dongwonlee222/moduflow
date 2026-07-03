#!/usr/bin/env python3
import argparse
from pathlib import Path


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


def build_pr_handoff(root, issue_id, branch="", pr="", reviewer="Reviewer"):
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


def write_pr_handoff(root, issue_id, branch="", pr="", reviewer="Reviewer"):
    root = Path(root).resolve()
    target = root / "specs" / issue_id / "pr.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(build_pr_handoff(root, issue_id, branch=branch, pr=pr, reviewer=reviewer), encoding="utf-8")
    return target


def main():
    parser = argparse.ArgumentParser(description="Generate ModuFlow draft PR handoff artifacts.")
    parser.add_argument("project_path", nargs="?", default=".")
    parser.add_argument("--issue-id", required=True)
    parser.add_argument("--branch", default="")
    parser.add_argument("--pr", default="")
    parser.add_argument("--reviewer", default="Reviewer")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    if args.write:
        path = write_pr_handoff(
            args.project_path,
            args.issue_id,
            branch=args.branch,
            pr=args.pr,
            reviewer=args.reviewer,
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
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
