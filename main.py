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
from gui.main_window import MainWindow
from gui.icon_helper import get_application_icon

def main():
    """主程序入口"""
    app = QApplication(sys.argv)
    
    # 设置应用程序属性
    app.setApplicationName("多开浏览器管理工具")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Chrome Profile Manager")
    
    # 设置应用程序图标
    app.setWindowIcon(get_application_icon())
    
    # 设置高DPI支持
    app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    # 创建主窗口
    window = MainWindow()
    window.show()
    
    # 运行应用程序
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 