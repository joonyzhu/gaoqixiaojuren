#!/bin/bash
# 高企小巨人智能申报系统 - 前端启动脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
FRONTEND_DIR="$SCRIPT_DIR/frontend"

if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
    echo "Installing frontend dependencies..."
    cd "$FRONTEND_DIR" && npm install
fi

echo "Starting frontend dev server on http://localhost:5178 ..."
cd "$FRONTEND_DIR" && npm run dev
