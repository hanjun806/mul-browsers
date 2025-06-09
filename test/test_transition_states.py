#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试按钮过渡状态功能
"""

import sys
import os
import time
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import Qt, QTimer

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

class TransitionTestWidget(QWidget):
    """过渡状态测试控件"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # 标题
        title = QLabel("过渡状态测试")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        layout.addWidget(title)
        
        # 创建Profile项目
        profile = TestProfile("测试Profile")
        self.profile_widget = ProfileItemWidget(profile, is_running=False)
        layout.addWidget(self.profile_widget)
        
        # 连接信号
        self.profile_widget.startRequested.connect(self.on_start_requested)
        self.profile_widget.closeRequested.connect(self.on_close_requested)
        
        # 控制按钮
        control_layout = QVBoxLayout()
        
        self.test_success_btn = QPushButton("模拟成功操作")
        self.test_success_btn.clicked.connect(self.test_success_operation)
        control_layout.addWidget(self.test_success_btn)
        
        self.test_failure_btn = QPushButton("模拟失败操作")
        self.test_failure_btn.clicked.connect(self.test_failure_operation)
        control_layout.addWidget(self.test_failure_btn)
        
        self.reset_btn = QPushButton("重置状态")
        self.reset_btn.clicked.connect(self.reset_state)
        control_layout.addWidget(self.reset_btn)
        
        layout.addLayout(control_layout)
        
        # 状态显示
        self.status_label = QLabel("状态: 准备就绪")
        self.status_label.setStyleSheet("margin: 10px; padding: 5px; background: #f0f0f0;")
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)
        self.setWindowTitle("过渡状态测试")
        self.setGeometry(100, 100, 400, 300)
    
    def on_start_requested(self, profile):
        """启动请求处理"""
        self.status_label.setText("状态: 收到启动请求，按钮应显示为黄色'启动中'")
        print(f"启动请求: {profile.display_name}")
        
        # 等待用户选择测试类型
        self.pending_operation = 'start'
    
    def on_close_requested(self, profile):
        """关闭请求处理"""
        self.status_label.setText("状态: 收到关闭请求，按钮应显示为黄色'关闭中'")
        print(f"关闭请求: {profile.display_name}")
        
        # 等待用户选择测试类型
        self.pending_operation = 'close'
    
    def test_success_operation(self):
        """测试成功操作"""
        if not hasattr(self, 'pending_operation'):
            self.status_label.setText("状态: 请先点击Profile的启动/关闭按钮")
            return
        
        if self.pending_operation == 'start':
            # 模拟启动成功
            self.status_label.setText("状态: 模拟启动成功，按钮应变为红色'关闭'")
            QTimer.singleShot(1000, lambda: self.profile_widget.update_status(True))
        elif self.pending_operation == 'close':
            # 模拟关闭成功
            self.status_label.setText("状态: 模拟关闭成功，按钮应变为绿色'启动'")
            QTimer.singleShot(1000, lambda: self.profile_widget.update_status(False))
        
        del self.pending_operation
    
    def test_failure_operation(self):
        """测试失败操作"""
        if not hasattr(self, 'pending_operation'):
            self.status_label.setText("状态: 请先点击Profile的启动/关闭按钮")
            return
        
        # 模拟操作失败，清除过渡状态
        self.status_label.setText("状态: 模拟操作失败，按钮应恢复原状态")
        QTimer.singleShot(1000, lambda: self.profile_widget.clear_transition_state())
        
        del self.pending_operation
    
    def reset_state(self):
        """重置状态"""
        self.profile_widget.update_status(False)
        self.status_label.setText("状态: 已重置为未运行状态")
        if hasattr(self, 'pending_operation'):
            del self.pending_operation

def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    window = TransitionTestWidget()
    window.show()
    
    print("=== 过渡状态测试 ===")
    print("1. 点击Profile的'启动'按钮，观察按钮变为黄色'启动中'")
    print("2. 点击'模拟成功操作'或'模拟失败操作'")
    print("3. 观察按钮状态变化")
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 