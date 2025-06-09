#!/bin/bash
# Mac应用构建脚本
# 自动化打包多开浏览器管理工具为macOS应用

set -e  # 遇到错误时退出

echo "🚀 开始构建 Mac 应用..."
echo "=================================="

# 检查Python环境
echo "📋 检查Python环境..."
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到 python3"
    exit 1
fi

# 安装py2app（如果未安装）
echo "📦 检查并安装 py2app..."
pip3 install py2app

# 安装项目依赖
echo "📦 安装项目依赖..."
pip3 install -r requirements.txt

# 清理之前的构建
echo "🧹 清理之前的构建文件..."
if [ -d "build" ]; then
    rm -rf build
fi
if [ -d "dist" ]; then
    rm -rf dist
fi

# 构建应用
echo "🔨 开始构建应用..."
python3 setup.py py2app

# 检查构建结果
if [ -d "dist/多开浏览器管理工具.app" ]; then
    echo "✅ 构建成功!"
    echo "📍 应用位置: $(pwd)/dist/多开浏览器管理工具.app"
    echo ""
    echo "🎉 您现在可以："
    echo "   1. 在访达中双击运行应用"
    echo "   2. 将应用拖拽到应用程序文件夹"
    echo "   3. 从启动台启动应用"
    echo ""
    echo "📂 打开应用所在文件夹..."
    open dist
else
    echo "❌ 构建失败，请检查错误信息"
    exit 1
fi

echo "✨ 构建完成!" 