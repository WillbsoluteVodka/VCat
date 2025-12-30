#!/bin/bash

cd "$(dirname "$0")"

# 确保 uv 在 PATH 中
export PATH="$HOME/.local/bin:$PATH"

# 检查 uv 是否安装
if ! command -v uv &> /dev/null; then
    echo "uv 未安装，正在安装..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
    echo "uv 安装完成"
fi

# 设置环境变量
export SUPABASE_URL="https://qamgefqejxydheqabdxo.supabase.co"
export SUPABASE_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFhbWdlZnFlanh5ZGhlcWFiZHhvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjY0NTE5NjAsImV4cCI6MjA4MjAyNzk2MH0.g2t5nlqUuOzu0z3adJFkvqNLwztljL3d3fE6SHOtx7I"

# 运行命令
uv run python src/connection.py "$@"
