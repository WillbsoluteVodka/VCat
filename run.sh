#!/bin/bash
# VCat 桌面宠物启动脚本

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

# 同步依赖（如果需要）
if [ ! -d ".venv" ]; then
    echo "虚拟环境不存在，正在创建并安装依赖..."
    uv sync
    echo "依赖安装完成"
fi

# 设置 PYTHONPATH 并使用 uv 运行应用
export PYTHONPATH=$(pwd)
echo "正在启动 VCat 桌面宠物..."
uv run python src/main_window.py

