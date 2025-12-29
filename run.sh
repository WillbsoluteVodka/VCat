#!/bin/bash
# VCat 桌面宠物启动脚本

cd "$(dirname "$0")"

# 检查虚拟环境是否存在
if [ ! -d "venv" ]; then
    echo "虚拟环境不存在，正在创建..."
    python3 -m venv venv
    echo "虚拟环境创建完成"
fi

# 激活虚拟环境
source venv/bin/activate

# 检查依赖是否已安装
if ! python -c "import PyQt5" 2>/dev/null; then
    echo "正在安装依赖..."
    pip install -r requirements.txt
    echo "依赖安装完成"
fi

# 设置 PYTHONPATH 并运行应用
export PYTHONPATH=$(pwd)
echo "正在启动 VCat 桌面宠物..."
python src/main_window.py

