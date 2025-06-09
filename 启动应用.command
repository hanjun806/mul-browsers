#!/bin/bash
# 简单启动脚本 - 双击即可运行

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

echo "🚀 正在启动多开浏览器管理工具..."

# 检查并安装依赖
if ! python3 -c "import PyQt5" 2>/dev/null; then
    echo "📦 正在安装依赖包..."
    pip3 install -r requirements.txt
fi

# 启动应用
python3 main.py 