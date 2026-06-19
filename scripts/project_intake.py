#!/usr/bin/env python3
import argparse
import json
import re
from datetime import date
from pathlib import Path


INTAKE_SCHEMA = "moduflow.intake-routing.v1"

DOMAIN_KEYWORDS = {
    "dev": {
        "bug", "fix", "error", "login", "api", "code", "implement", "build",
        "버그", "고쳐", "수정", "로그인", "에러", "오류", "구현", "개발", "기능", "결제",
    },
    "planning": {
        "plan", "roadmap", "priority", "milestone", "schedule",
        "계획", "로드맵", "우선순위", "일정", "마일스톤",
    },
    "design": {
        "design", "ux", "ui", "prototype", "landing", "wireframe",
        "디자인", "프로토타입", "랜딩", "화면", "와이어프레임",
    },
    "data": {
        "metric", "analytics", "dashboard", "data", "kpi", "report",
        "분석", "데이터", "지표", "대시보드", "리포트", "보고서",
    },
    "docs": {
        "doc", "docs", "write", "memo", "guide", "readme", "report",
        "문서", "정리", "작성", "가이드", "메모", "리포트", "보고서",
    },
    "ops": {
        "deploy", "release", "ci", "monitor", "incident", "ops",
        "배포", "릴리즈", "운영", "모니터링", "장애", "설정",
    },
    "research": {
        "research", "benchmark", "competitor", "survey", "market",
        "조사", "리서치", "벤치마크", "경쟁사", "시장",
    },
    "business": {
        "business", "canvas", "lean", "pitch", "persona", "model",
        "사업", "사업계획서", "린", "캔버스", "비즈니스", "피치덱", "페르소나", "모델",
    },
}

STOPWORDS = {
    "the", "and", "for", "with", "this", "that", "please", "make", "create",
    "이거", "해줘", "해주세요", "만들어줘", "좀", "하고", "그리고", "및", "새",
}

TOKEN_ALIASES = {
    "로그인": {"login", "auth"},
    "login": {"로그인", "auth"},
    "버그": {"bug", "error"},
    "bug": {"버그", "오류"},
    "오류": {"error", "bug"},
    "에러": {"error", "bug"},
    "결제": {"payment", "billing"},
    "payment": {"결제", "billing"},
    "리포트": {"report"},
    "보고서": {"report"},
    "사업계획서": {"business", "plan", "canvas"},
    "캔버스": {"canvas", "business"},
}

DOMAIN_TITLES = {
    "dev": "implementation work",
    "planning": "planning work",
    "design": "design work",
    "data": "data analysis work",
    "docs": "documentation work",
    "ops": "operations work",
    "research": "research work",
    "business": "business planning work",
}


def base_tokens(text):
    raw_tokens = re.findall(r"[0-9A-Za-z가-힣]+", (text or "").lower())
    return [token for token in raw_tokens if token not in STOPWORDS and len(token) > 1]


def tokenize(text):
    tokens = base_tokens(text)
    expanded = []
    for token in tokens:
        expanded.append(token)
        expanded.extend(sorted(TOKEN_ALIASES.get(token, set())))
    return expanded


def classify_request(text):
    tokens = tokenize(text)
    scores = {domain: 0 for domain in DOMAIN_KEYWORDS}
    lowered = (text or "").lower()
    for domain, keywords in DOMAIN_KEYWORDS.items():
        for keyword in keywords:
            keyword_lower = keyword.lower()
            if keyword_lower in lowered:
                scores[domain] += 2 if len(keyword_lower) > 2 else 1
        scores[domain] += sum(1 for token in tokens if token in keywords)
    primary = max(scores, key=lambda domain: (scores[domain], -list(DOMAIN_KEYWORDS).index(domain)))
    if scores[primary] == 0:
        primary = "planning"
    return {"primary": primary, "scores": scores}


def request_size(text, classification=None):
    classification = classification or classify_request(text)
    matched_domains = [
        domain for domain, score in classification.get("scores", {}).items() if score > 0
    ]
    connectors = len(re.findall(r"\b(and|plus)\b|그리고|하고|및|랑|와|과", text or "", re.IGNORECASE))
    if len(matched_domains) >= 3 or connectors >= 2 or len(tokenize(text)) >= 12:
        return "large"
    return "small"


def issue_files(root):
    issues_dir = Path(root).resolve() / "issues"
    if not issues_dir.exists():
        return []
    return sorted(issues_dir.glob("*.md"))


def issue_id_from_path(path):
    return path.stem


def load_issue_summaries(root):
    summaries = []
    for path in issue_files(root):
        text = path.read_text(encoding="utf-8")
        title = ""
        for line in text.splitlines():
            if line.startswith("# "):
                title = line.lstrip("# ").strip()
                break
        summaries.append({
            "issue_id": issue_id_from_path(path),
            "title": title or issue_id_from_path(path),
            "text": text,
            "tokens": set(tokenize(f"{title}\n{text}")),
        })
    return summaries


def similarity(left_tokens, right_tokens):
    left = set(left_tokens)
    right = set(right_tokens)
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


def find_related_issues(root, text, threshold=0.08):
    request_tokens = set(tokenize(text))
    related = []
    for issue in load_issue_summaries(root):
        score = similarity(request_tokens, issue["tokens"])
        if score >= threshold:
            relationship = "duplicate_candidate" if score >= 0.18 else "related"
            related.append({
                "issue_id": issue["issue_id"],
                "title": issue["title"],
                "relationship": relationship,
                "score": round(score, 3),
            })
    return sorted(related, key=lambda item: item["score"], reverse=True)


def slugify(text, fallback="work"):
    tokens = tokenize(text)
    ascii_tokens = [token for token in tokens if re.fullmatch(r"[a-z0-9]+", token)]
    if ascii_tokens:
        slug = "-".join(ascii_tokens[:6])
    else:
        domain = classify_request(text)["primary"]
        slug = DOMAIN_TITLES.get(domain, fallback).replace(" ", "-")
    return re.sub(r"-+", "-", slug).strip("-") or fallback


def next_issue_number(root):
    max_number = 0
    for path in issue_files(root):
        match = re.match(r"(\d+)-", path.stem)
        if match:
            max_number = max(max_number, int(match.group(1)))
    return max_number + 1


def candidate_title(text, domain):
    cleaned = " ".join(base_tokens(text))
    if cleaned:
        return cleaned[:80]
    return DOMAIN_TITLES.get(domain, "new work")


def split_issue_candidates(root, text, classification=None):
    classification = classification or classify_request(text)
    matched_domains = [
        domain for domain, score in classification.get("scores", {}).items() if score > 0
    ] or [classification["primary"]]
    base_number = next_issue_number(root)
    candidates = []
    for offset, domain in enumerate(matched_domains):
        title = candidate_title(text, domain)
        issue_id = f"{base_number + offset:03d}-{slugify(domain + ' ' + title)}"
        candidates.append({
            "issue_id": issue_id,
            "title": title,
            "domain": domain,
            "relationship": "new",
            "next_command": f"product:issue {issue_id}",
        })
    return candidates


def load_active_loop(root):
    path = Path(root).resolve() / "workspace" / "loop-state.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def active_issue_matches(active_issue, related_issues):
    return bool(active_issue) and any(
        item["issue_id"] == active_issue for item in related_issues
    )


def append_inbox_record(root, routed):
    inbox_path = Path(root).resolve() / "workspace" / "inbox.md"
    inbox_path.parent.mkdir(parents=True, exist_ok=True)
    if inbox_path.exists():
        existing = inbox_path.read_text(encoding="utf-8")
    else:
        existing = "# Inbox\n\n"
    record = (
        f"## Intake {date.today().isoformat()}\n\n"
        f"```json\n{json.dumps(routed, ensure_ascii=False, indent=2)}\n```\n\n"
    )
    inbox_path.write_text(existing.rstrip() + "\n\n" + record, encoding="utf-8")
    return inbox_path


def route_intake(root, request, write=False):
    root = Path(root).resolve()
    classification = classify_request(request)
    size = request_size(request, classification)
    loop = load_active_loop(root)
    active_issue = loop.get("active_issue_id") or loop.get("issue_id")
    active_goal = loop.get("goal_id")
    related = find_related_issues(root, request)

    if size == "large":
        action = "create_goal_with_issues"
        candidates = split_issue_candidates(root, request, classification)
        next_command = "product:goal"
    elif active_issue_matches(active_issue, related):
        action = "attach_active_issue"
        candidates = []
        next_command = loop.get("next_command") or f"product:issue {active_issue}"
    else:
        action = "create_issue"
        candidates = split_issue_candidates(root, request, classification)[:1]
        next_command = candidates[0]["next_command"] if candidates else "product:issue"

    routed = {
        "schema": INTAKE_SCHEMA,
        "request": request,
        "classification": classification,
        "size": size,
        "active_goal": active_goal,
        "active_issue": active_issue,
        "recommended_action": action,
        "related_issues": related,
        "issue_candidates": candidates,
        "next_command": next_command,
        "updated_at": date.today().isoformat(),
    }
    if write:
        append_inbox_record(root, routed)
    return routed


def main():
    parser = argparse.ArgumentParser(description="Route a loose request into a ModuFlow goal or issue graph.")
    parser.add_argument("request")
    parser.add_argument("project_path", nargs="?", default=".")
    parser.add_argument("--write", action="store_true", help="Append the routing record to workspace/inbox.md.")
    args = parser.parse_args()
    routed = route_intake(args.project_path, args.request, write=args.write)
    print(json.dumps(routed, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
