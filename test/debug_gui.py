#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Debug版本的GUI，用于查看按钮显示问题
"""

import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QPushButton
from PyQt5.QtCore import Qt

# 导入核心模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.profile_manager import ProfileManager

class DebugProfileItemWidget(QWidget):
    """Debug版本的Profile项目控件"""
    
    def __init__(self, profile):
        super().__init__()
        self.profile = profile
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Profile名称
        name_label = QLabel(self.profile.display_name)
        layout.addWidget(name_label)
        
        # 测试按钮 - 使用纯文本而不是emoji
        self.test_button = QPushButton("START")
        self.test_button.setFixedSize(80, 30)
        layout.addWidget(self.test_button)
        
        # 测试emoji按钮
        self.emoji_button = QPushButton("▶️ 启动")
        self.emoji_button.setFixedSize(80, 30)
        layout.addWidget(self.emoji_button)
        
        # 显示按钮文本的标签
        self.text_display = QLabel()
        layout.addWidget(self.text_display)
        
        self.setLayout(layout)
        
        # 连接信号
        self.test_button.clicked.connect(self.on_test_click)
        self.emoji_button.clicked.connect(self.on_emoji_click)
        
        # 更新显示
        self.update_display()
    
    def on_test_click(self):
        """切换普通按钮"""
        if self.test_button.text() == "START":
            self.test_button.setText("STOP")
        else:
            self.test_button.setText("START")
        self.update_display()
    
    def on_emoji_click(self):
        """切换emoji按钮"""
        if "启动" in self.emoji_button.text():
            self.emoji_button.setText("⏹️ 关闭")
        else:
            self.emoji_button.setText("▶️ 启动")
        self.update_display()
    
    def update_display(self):
        """更新文本显示"""
        text = f"普通按钮: '{self.test_button.text()}'\nEmoji按钮: '{self.emoji_button.text()}'"
        self.text_display.setText(text)

class DebugMainWindow(QMainWindow):
    """Debug主窗口"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        self.setWindowTitle("Debug 按钮显示问题")
        self.setGeometry(100, 100, 500, 600)
        
        # 获取Profile数据
        pm = ProfileManager()
        profiles = pm.scan_profiles()
        
        # 创建中央控件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        
        # 添加说明
        info_label = QLabel("Debug按钮显示问题：")
        layout.addWidget(info_label)
        
        # 为每个Profile创建debug项目
        for i, profile in enumerate(profiles[:3]):  # 只显示前3个
            widget = DebugProfileItemWidget(profile)
            layout.addWidget(widget)
            
            if i >= 2:  # 最多显示3个
                break
        
        central_widget.setLayout(layout)

def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    window = DebugMainWindow()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 