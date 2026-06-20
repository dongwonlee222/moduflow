#!/usr/bin/env python3
import json
import sys
from pathlib import Path

# Add project root to sys.path to resolve scripts module importing
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts.issue_generator import get_next_issue_number, generate_issues_from_goal, write_issue_file

def read_json_input():
    try:
        input_data = sys.stdin.read()
        if not input_data.strip():
            return None
        return json.loads(input_data)
    except Exception:
        return None

def main():
    # Basic standard IO MCP implementation
    # Responds to JSON-RPC tools list and call requests
    req = read_json_input()
    if not req:
        # Defaults to tools definition schema if no input is provided
        tools = [
            {
                "name": "moduflow_status",
                "description": "ModuFlow의 현재 활성 루프 및 이슈 상태를 조회합니다.",
                "input_schema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "moduflow_decompose_goal",
                "description": "사용자가 설정한 상위 목표(Goal)를 벤치마킹하여 다중 하위 이슈로 자동 분해 및 작성합니다.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "goal": {
                            "type": "string",
                            "description": "구현하려는 목표 제품 스펙"
                        }
                    },
                    "required": ["goal"]
                }
            }
        ]
        print(json.dumps({"tools": tools}, ensure_ascii=False))
        return

    method = req.get("method")
    params = req.get("params", {})
    req_id = req.get("id")

    if method == "tools/list":
        tools = [
            {
                "name": "moduflow_status",
                "description": "ModuFlow의 현재 활성 루프 및 이슈 상태를 조회합니다.",
                "input_schema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "moduflow_decompose_goal",
                "description": "사용자가 설정한 상위 목표(Goal)를 벤치마킹하여 다중 하위 이슈로 자동 분해 및 작성합니다.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "goal": {
                            "type": "string",
                            "description": "구현하려는 목표 제품 스펙"
                        }
                    },
                    "required": ["goal"]
                }
            }
        ]
        print(json.dumps({"id": req_id, "result": {"tools": tools}}, ensure_ascii=False))
    elif method == "tools/call":
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if tool_name == "moduflow_status":
            loop_state_file = ROOT / "workspace" / "loop-state.json"
            if loop_state_file.exists():
                state_data = json.loads(loop_state_file.read_text(encoding="utf-8"))
                result = {
                    "content": [
                        {
                            "type": "text",
                            "text": f"ModuFlow Active Goal: {state_data.get('goal_id')}\nActive Issue: {state_data.get('active_issue_id')}\nPhase: {state_data.get('phase')}\nStatus: {state_data.get('status')}"
                        }
                    ]
                }
            else:
                result = {
                    "content": [
                        {"type": "text", "text": "No active ModuFlow loop-state.json found."}
                    ]
                }
            print(json.dumps({"id": req_id, "result": result}, ensure_ascii=False))
            
        elif tool_name == "moduflow_decompose_goal":
            goal = arguments.get("goal")
            if not goal:
                error = {"code": -32602, "message": "Missing 'goal' parameter"}
                print(json.dumps({"id": req_id, "error": error}, ensure_ascii=False))
                return
            
            next_num = get_next_issue_number(ROOT / "issues")
            issues = generate_issues_from_goal(goal)
            created_files = []
            for i, issue_data in enumerate(issues):
                num = next_num + i
                fpath = write_issue_file(ROOT, num, issue_data)
                created_files.append(str(fpath.relative_to(ROOT)))
                
            result = {
                "content": [
                    {
                        "type": "text",
                        "text": f"Successfully decomposed goal into {len(created_files)} issues:\n" + "\n".join(created_files)
                    }
                ]
            }
            print(json.dumps({"id": req_id, "result": result}, ensure_ascii=False))
        else:
            error = {"code": -32601, "message": f"Tool '{tool_name}' not found"}
            print(json.dumps({"id": req_id, "error": error}, ensure_ascii=False))
    else:
        error = {"code": -32601, "message": "Method not found"}
        print(json.dumps({"id": req_id, "error": error}, ensure_ascii=False))

if __name__ == "__main__":
    main()
