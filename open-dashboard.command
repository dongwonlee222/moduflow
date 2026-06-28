#!/bin/bash
# Double-click in Finder to regenerate and open the ModuFlow decision-graph dashboard.
cd "$(dirname "$0")" || exit 1
python3 scripts/project_memory.py . --dashboard
open memory/dashboard.html
