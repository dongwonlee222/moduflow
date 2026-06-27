#!/usr/bin/env python3
import argparse
import re
import sys
from pathlib import Path

# Matches checkboxes: - [ ] or - [x] or - [/]
CHECKBOX_RE = re.compile(r"^(?P<indent>\s*)-\s+\[(?P<status>[ xX/])\]\s+(?P<text>.+?)\s*$")
METADATA_RE = re.compile(r"\s*\[(files|globs|depends|shared_state|group):\s*[^\]]*\]", re.IGNORECASE)
PREFIX_RE = re.compile(r"^(pm|product|spec|roadmap|design|ux|data|qa|release|implementation|code)\s*:\s*", re.IGNORECASE)

def clean_task_text(text):
    # Remove metadata brackets
    text = METADATA_RE.sub("", text).strip()
    # Remove category prefix (e.g. PM: )
    text = PREFIX_RE.sub("", text).strip()
    return text.lower()

def parse_file_tasks(path):
    tasks = []
    if not path.exists():
        return tasks
    
    for line in path.read_text(encoding="utf-8").splitlines():
        match = CHECKBOX_RE.match(line)
        if match:
            raw_text = match.group("text").strip()
            clean_text = clean_task_text(raw_text)
            tasks.append({
                "line": line,
                "status": match.group("status").lower(),
                "raw_text": raw_text,
                "clean_text": clean_text
            })
    return tasks

def merge_statuses(status1, status2):
    s1, s2 = status1.lower(), status2.lower()
    if s1 == "x" or s2 == "x":
        return "x"
    if s1 == "/" or s2 == "/":
        return "/"
    return " "

def detect_task_drift(host_path, git_path):
    host_tasks = parse_file_tasks(host_path)
    git_tasks = parse_file_tasks(git_path)
    
    git_map = {t["clean_text"]: t["status"] for t in git_tasks}
    
    for ht in host_tasks:
        gt_status = git_map.get(ht["clean_text"])
        if gt_status is not None and ht["status"] != gt_status:
            return True
    return False

def sync_tasks_bidirectional(host_path, git_path):
    host_tasks = parse_file_tasks(host_path)
    git_tasks = parse_file_tasks(git_path)
    
    # Map from clean task text to its status
    host_map = {t["clean_text"]: t["status"] for t in host_tasks}
    git_map = {t["clean_text"]: t["status"] for t in git_tasks}
    
    # Merge statuses for all matched clean texts
    merged_map = {}
    all_clean_texts = set(host_map.keys()) | set(git_map.keys())
    for clean in all_clean_texts:
        hs = host_map.get(clean, " ")
        gs = git_map.get(clean, " ")
        merged_map[clean] = merge_statuses(hs, gs)
        
    # Helper to rewrite file lines
    def rewrite_file(path):
        if not path.exists():
            return
        lines = path.read_text(encoding="utf-8").splitlines()
        new_lines = []
        for line in lines:
            match = CHECKBOX_RE.match(line)
            if match:
                raw_text = match.group("text").strip()
                clean = clean_task_text(raw_text)
                merged_status = merged_map.get(clean, match.group("status"))
                # Reconstruct line with same indent and formatting
                indent = match.group("indent")
                new_line = f"{indent}- [{merged_status}] {raw_text}"
                new_lines.append(new_line)
            else:
                new_lines.append(line)
        path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")

    rewrite_file(host_path)
    rewrite_file(git_path)

def main():
    parser = argparse.ArgumentParser(description="Sync Antigravity planning artifacts with ModuFlow.")
    parser.add_argument("--host", required=True, help="Path to host task.md")
    parser.add_argument("--git", required=True, help="Path to ModuFlow tasks.md")
    parser.add_argument("--drift", action="store_true", help="Only check for drift")
    args = parser.parse_args()

    host_path = Path(args.host)
    git_path = Path(args.git)

    if args.drift:
        drifted = detect_task_drift(host_path, git_path)
        print(json.dumps({"drifted": drifted}))
        return 0

    sync_tasks_bidirectional(host_path, git_path)
    print(json.dumps({"ok": True}))
    return 0

if __name__ == "__main__":
    import json
    sys.exit(main())
