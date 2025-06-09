#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多开浏览器管理工具
主程序入口
"""

import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from gui.main_window import MainWindow

# 设置Qt环境变量
if getattr(sys, 'frozen', False):
    # 如果是打包的应用程序
    bundle_dir = os.path.dirname(sys.executable)
    qt_plugin_path = os.path.join(bundle_dir, '..', 'Resources', 'lib', 'python3.9', 'PyQt5', 'Qt5', 'plugins')
    os.environ['QT_PLUGIN_PATH'] = qt_plugin_path
    os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = qt_plugin_path
    # 强制使用cocoa平台
    os.environ['QT_QPA_PLATFORM'] = 'cocoa'

def main():
    """主程序入口"""
    try:
        # 必须在创建QApplication之前设置
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
        
        app = QApplication(sys.argv)
        
        # 设置应用程序属性
        app.setApplicationName("多开浏览器管理工具")
        app.setApplicationVersion("1.0.0")
        app.setOrganizationName("Chrome Profile Manager")
        
        # 设置应用程序图标
        try:
            icon_path = os.path.join(os.path.dirname(__file__), "assets", "icon.png")
            if os.path.exists(icon_path):
                app.setWindowIcon(QIcon(icon_path))
        except Exception as e:
            print(f"设置图标失败: {e}")
        
        # 创建主窗口
        window = MainWindow()
        window.show()
        
        return app.exec_()
    except Exception as e:
        print(f"程序启动失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main()) 