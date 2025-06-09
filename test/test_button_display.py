#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试按钮显示问题
"""

import sys
import os
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout
from PyQt5.QtCore import Qt

# 导入核心模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from gui.main_window import ProfileItemWidget

# 创建虚拟Profile对象
class TestProfile:
    def __init__(self, name):
        self.name = name
        self.display_name = f"测试{name}"
        self.bookmarks_count = 10
        self.extensions_count = 5

def test_button_display():
    """测试按钮显示"""
    app = QApplication(sys.argv)
    
    # 创建测试窗口
    window = QWidget()
    window.setWindowTitle("测试按钮显示")
    window.setGeometry(100, 100, 400, 300)
    
    layout = QVBoxLayout()
    
    # 创建两个测试Profile项目
    profile1 = TestProfile("Profile1")
    profile2 = TestProfile("Profile2")
    
    # 创建未运行状态的按钮
    widget1 = ProfileItemWidget(profile1, is_running=False)
    layout.addWidget(widget1)
    
    # 创建运行中状态的按钮
    widget2 = ProfileItemWidget(profile2, is_running=True)
    layout.addWidget(widget2)
    
    window.setLayout(layout)
    window.show()
    
    print("按钮1文本:", widget1.toggle_button.text())
    print("按钮2文本:", widget2.toggle_button.text())
    
    # 测试状态切换
    print("\n测试状态切换...")
    widget1.update_status(True)
    widget2.update_status(False)
    
    print("切换后按钮1文本:", widget1.toggle_button.text())
    print("切换后按钮2文本:", widget2.toggle_button.text())
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    test_button_display() 