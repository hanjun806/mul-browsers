#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
启动脚本
用于测试和运行多开浏览器管理工具
"""

import sys
import os

def check_dependencies():
    """检查依赖包是否安装"""
    missing_packages = []
    
    try:
        import PyQt5
    except ImportError:
        missing_packages.append("PyQt5")
    
    try:
        import psutil
    except ImportError:
        missing_packages.append("psutil")
    
    if missing_packages:
        print("错误: 缺少以下依赖包:")
        for package in missing_packages:
            print(f"  - {package}")
        print("\n请运行以下命令安装依赖:")
        print("pip install -r requirements.txt")
        return False
    
    return True

def main():
    """主函数"""
    print("多开浏览器管理工具 v1.0")
    print("=" * 40)
    
    # 检查依赖
    if not check_dependencies():
        return 1
    
    # 检查Chrome是否安装
    from core.browser_manager import BrowserManager
    browser_manager = BrowserManager()
    
    if not browser_manager.chrome_executable:
        print("警告: 未找到Chrome浏览器可执行文件")
        print("请确保已安装Google Chrome浏览器")
    else:
        print(f"发现Chrome: {browser_manager.chrome_executable}")
    
    # 启动GUI应用程序
    try:
        from main import main as app_main
        print("正在启动GUI应用程序...")
        app_main()
        return 0
    except Exception as e:
        print(f"启动应用程序时出错: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 