#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "ModuFlow vendor sync helper"
echo "Root: ${ROOT}"
echo
echo "This helper intentionally does not auto-edit overlays or adapters."
echo "Review vendor.lock.json, update vendor snapshots, then run:"
echo "  python3 scripts/validate_moduflow.py ."

