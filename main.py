#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多开浏览器管理工具
主程序入口
"""

import sys
import os

# 设置Qt环境变量
if getattr(sys, 'frozen', False):
    # 如果是打包的应用程序
    bundle_dir = os.path.dirname(sys.executable)
    qt_plugin_path = os.path.join(bundle_dir, '..', 'Resources', 'lib', 'python3.9', 'PyQt5', 'Qt5', 'plugins')
    os.environ['QT_PLUGIN_PATH'] = qt_plugin_path
    os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = qt_plugin_path
    # 强制使用cocoa平台
    os.environ['QT_QPA_PLATFORM'] = 'cocoa'

try:
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtCore import Qt
    from gui.main_window import MainWindow
    from gui.icon_helper import get_application_icon
except ImportError as e:
    print(f"导入模块失败: {e}")
    sys.exit(1)

def main():
    """主程序入口"""
    try:
        app = QApplication(sys.argv)
        
        # 设置应用程序属性
        app.setApplicationName("多开浏览器管理工具")
        app.setApplicationVersion("1.0.0")
        app.setOrganizationName("Chrome Profile Manager")
        
        # 设置应用程序图标
        try:
            app.setWindowIcon(get_application_icon())
        except Exception as e:
            print(f"设置图标失败: {e}")
        
        # 设置高DPI支持
        app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
        
        # 创建主窗口
        window = MainWindow()
        window.show()
        
        # 运行应用程序
        sys.exit(app.exec_())
        
    except Exception as e:
        print(f"应用程序启动失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 