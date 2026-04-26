#!/bin/bash
# 高企小巨人智能申报系统 - 后端启动脚本
# Usage: ./start-backend.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"
BACKEND_DIR="$SCRIPT_DIR/backend"

# Create virtualenv if missing
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv "$VENV_DIR"
    "$VENV_DIR/bin/pip" install -r "$BACKEND_DIR/requirements.txt"
fi

echo "Starting backend server on http://localhost:8100 ..."
cd "$BACKEND_DIR"
PYTHONPATH="$BACKEND_DIR" "$VENV_DIR/bin/python" -m uvicorn main:app --host 127.0.0.1 --port 8100 --reload
