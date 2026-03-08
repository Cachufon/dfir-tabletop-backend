#!/bin/bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

echo "============================================================"
echo "TTX Launcher (Local)"
echo "Repo: $REPO_ROOT"
echo "============================================================"
echo ""

# Create venv if missing
if [ ! -x "$REPO_ROOT/.venv/bin/python" ]; then
  echo "[*] Creating virtualenv at .venv"
  python3 -m venv "$REPO_ROOT/.venv"
fi

PY="$REPO_ROOT/.venv/bin/python"
PIP="$REPO_ROOT/.venv/bin/pip"

echo "[*] Installing dependencies (best effort; may take a minute)..."
if [ -f "dfir_backend/ttx/scripts/requirements.txt" ]; then
  "$PIP" install -r dfir_backend/ttx/scripts/requirements.txt || true
fi
if [ -f "dfir_backend/ttx/ui/requirements.txt" ]; then
  "$PIP" install -r dfir_backend/ttx/ui/requirements.txt || true
fi

echo ""
echo "[*] Starting workflow menu..."
echo ""

"$PY" tools/ttx_launcher.py

echo ""
echo "Launcher finished. You can close this window."
read -r -p "Press Enter to exit..."
