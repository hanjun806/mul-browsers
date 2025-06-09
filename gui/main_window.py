#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主GUI窗口
实现多开浏览器管理工具的用户界面
"""

import sys
import os
import time
from PyQt5.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
                            QSplitter, QListWidget, QListWidgetItem, QLabel, 
                            QPushButton, QGroupBox, QGridLayout, QTextEdit,
                            QComboBox, QSpinBox, QLineEdit, QCheckBox, 
                            QProgressBar, QStatusBar, QMenuBar, QAction,
                            QMessageBox, QInputDialog, QTabWidget, QScrollArea,
                            QFrame, QSizePolicy, QTreeWidget, QTreeWidgetItem,
                            QDialog, QDialogButtonBox, QFormLayout, QFileDialog)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QSize, QTime
from PyQt5.QtGui import QIcon, QFont, QPalette, QColor, QPixmap

# 导入核心模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.profile_manager import ProfileManager, ProfileInfo
from core.browser_manager import BrowserManager
from core.config_manager import ConfigManager, ProfileConfig
from gui.icon_helper import get_application_icon

class ProfileEditDialog(QDialog):
    """Profile编辑对话框"""
    
    def __init__(self, parent=None, profile=None, profile_manager=None):
        super().__init__(parent)
        self.profile = profile  # 如果为None则是新建，否则是编辑
        self.profile_manager = profile_manager
        self.is_edit_mode = profile is not None
        
        self.setup_ui()
        self.load_profile_data()
    
    def setup_ui(self):
        """设置UI"""
        title = "编辑Profile" if self.is_edit_mode else "新建Profile"
        self.setWindowTitle(title)
        self.setFixedSize(600, 500) if self.is_edit_mode else self.setFixedSize(500, 400)  # 增加窗口大小
        
        layout = QVBoxLayout()
        layout.setSpacing(10)  # 增加间距
        
        # 标题区域
        title_widget = QWidget()
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(10, 10, 10, 10)  # 增加边距
        
        title_icon = QLabel("⚙️" if self.is_edit_mode else "➕")
        title_icon.setFixedSize(32, 32)
        title_icon.setAlignment(Qt.AlignCenter)
        title_icon.setStyleSheet("font-size: 20px;")
        
        title_label = QLabel(title)
        title_label.setFont(QFont("", 14, QFont.Bold))
        
        title_layout.addWidget(title_icon)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        title_widget.setLayout(title_layout)
        title_widget.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                margin-bottom: 10px;
            }
        """)
        
        layout.addWidget(title_widget)
        
        # 创建表单
        form_widget = QWidget()
        form_layout = QFormLayout()
        form_layout.setSpacing(10)  # 增加表单间距
        
        # Profile名称
        self.name_edit = QLineEdit()
        self.name_edit.setMinimumHeight(30)  # 设置最小高度
        self.name_edit.setPlaceholderText("例如: work, personal, test")
        self.name_edit.textChanged.connect(self.validate_input)
        form_layout.addRow("Profile名称*:", self.name_edit)
        
        # 显示名称
        self.display_name_edit = QLineEdit()
        self.display_name_edit.setMinimumHeight(30)  # 设置最小高度
        self.display_name_edit.setPlaceholderText("例如: 工作环境, 个人使用, 测试环境")
        form_layout.addRow("显示名称:", self.display_name_edit)
        
        # 如果是编辑模式，显示更多信息
        if self.is_edit_mode:
            self.name_edit.setEnabled(False)
            self.name_edit.setStyleSheet("background-color: #f5f5f5; color: #666;")
            
            # 添加Profile详细信息
            info_group = QGroupBox("Profile信息")
            info_layout = QGridLayout()
            info_layout.setSpacing(8)  # 增加间距
            
            self.path_label = QLabel()
            self.path_label.setWordWrap(True)
            self.path_label.setStyleSheet("color: #666; font-size: 11px; padding: 5px;")
            
            self.size_label = QLabel()
            self.bookmarks_label = QLabel()
            self.extensions_label = QLabel()
            self.created_label = QLabel()
            
            info_layout.addWidget(QLabel("路径:"), 0, 0)
            info_layout.addWidget(self.path_label, 0, 1, 1, 3)  # 跨3列
            info_layout.addWidget(QLabel("大小:"), 1, 0)
            info_layout.addWidget(self.size_label, 1, 1)
            info_layout.addWidget(QLabel("书签:"), 1, 2)
            info_layout.addWidget(self.bookmarks_label, 1, 3)
            info_layout.addWidget(QLabel("扩展:"), 2, 0)
            info_layout.addWidget(self.extensions_label, 2, 1)
            info_layout.addWidget(QLabel("创建时间:"), 2, 2)
            info_layout.addWidget(self.created_label, 2, 3)
            
            info_group.setLayout(info_layout)
            layout.addWidget(info_group)
        
        # 添加表单到布局
        form_widget.setLayout(form_layout)
        layout.addWidget(form_widget)
        
        # 说明文字
        info_label = QLabel()
        if self.is_edit_mode:
            info_label.setText("💡 提示：Profile名称不可修改，只能修改显示名称")
        else:
            info_label.setText("💡 提示：Profile名称用于文件夹命名，建议使用英文\n📝 显示名称用于界面显示，可以使用中文")
        
        info_label.setStyleSheet("""
            QLabel {
                color: #666;
                font-size: 11px;
                padding: 8px;
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                margin: 5px 0;
            }
        """)
        info_label.setWordWrap(True)
        
        layout.addLayout(form_layout)
        layout.addWidget(info_label)
        
        # 输入验证提示
        self.validation_label = QLabel()
        self.validation_label.setStyleSheet("""
            QLabel {
                color: #dc3545;
                font-size: 11px;
                font-weight: bold;
                padding: 5px;
            }
        """)
        self.validation_label.hide()
        layout.addWidget(self.validation_label)
        
        # 按钮
        button_layout = QHBoxLayout()
        
        if self.is_edit_mode:
            # 删除按钮（左侧）
            self.delete_button = QPushButton("🗑️ 删除Profile")
            self.delete_button.setStyleSheet("""
                QPushButton {
                    background-color: #dc3545;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #c82333;
                }
                QPushButton:pressed {
                    background-color: #bd2130;
                }
            """)
            self.delete_button.clicked.connect(self.delete_profile)
            button_layout.addWidget(self.delete_button)
            
            button_layout.addStretch()
        
        # 右侧按钮组
        button_box = QDialogButtonBox()
        
        action_text = "保存" if self.is_edit_mode else "创建"
        self.save_button = button_box.addButton(action_text, QDialogButtonBox.AcceptRole)
        cancel_button = button_box.addButton("取消", QDialogButtonBox.RejectRole)
        
        self.save_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:pressed {
                background-color: #1e7e34;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        
        button_box.accepted.connect(self.save_profile)
        button_box.rejected.connect(self.reject)
        
        if self.is_edit_mode:
            button_layout.addWidget(button_box)
            layout.addLayout(button_layout)
        else:
            layout.addStretch()
            layout.addWidget(button_box)
        
        self.setLayout(layout)
    
    def validate_input(self):
        """验证输入"""
        if self.is_edit_mode:
            return True
        
        name = self.name_edit.text().strip()
        
        # 检查是否为空
        if not name:
            self.validation_label.hide()
            self.save_button.setEnabled(True)
            return True
        
        # 检查格式
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', name):
            self.validation_label.setText("❌ Profile名称只能包含字母、数字、下划线和连字符")
            self.validation_label.show()
            self.save_button.setEnabled(False)
            return False
        
        # 检查长度
        if len(name) > 50:
            self.validation_label.setText("❌ Profile名称不能超过50个字符")
            self.validation_label.show()
            self.save_button.setEnabled(False)
            return False
        
        # 检查是否为保留名称
        reserved_names = ['con', 'prn', 'aux', 'nul', 'com1', 'com2', 'com3', 'com4', 'com5', 'com6', 'com7', 'com8', 'com9', 'lpt1', 'lpt2', 'lpt3', 'lpt4', 'lpt5', 'lpt6', 'lpt7', 'lpt8', 'lpt9']
        if name.lower() in reserved_names:
            self.validation_label.setText("❌ 不能使用系统保留名称")
            self.validation_label.show()
            self.save_button.setEnabled(False)
            return False
        
        # 验证通过
        self.validation_label.hide()
        self.save_button.setEnabled(True)
        return True
    
    def load_profile_data(self):
        """加载Profile数据"""
        if self.is_edit_mode and self.profile:
            self.name_edit.setText(self.profile.name)
            self.display_name_edit.setText(self.profile.display_name)
            
            # 加载详细信息
            self.path_label.setText(self.profile.path)
            
            from core.profile_manager import ProfileManager
            pm = ProfileManager()
            self.size_label.setText(pm.format_size(self.profile.storage_size))
            self.bookmarks_label.setText(str(self.profile.bookmarks_count))
            self.extensions_label.setText(str(self.profile.extensions_count))
            
            if self.profile.created_time:
                self.created_label.setText(self.profile.created_time.strftime("%Y-%m-%d %H:%M:%S"))
            else:
                self.created_label.setText("未知")
    
    def _is_chrome_running(self):
        """检查Chrome是否正在运行"""
        import psutil
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if 'chrome' in proc.info['name'].lower():
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return False
    
    def save_profile(self):
        """保存Profile"""
        name = self.name_edit.text().strip()
        display_name = self.display_name_edit.text().strip()
        
        # 验证输入
        if not name:
            QMessageBox.warning(self, "错误", "请输入Profile名称")
            return
        
        # 验证Profile名称格式（只允许字母、数字、下划线、连字符）
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', name):
            QMessageBox.warning(self, "错误", "Profile名称只能包含字母、数字、下划线和连字符")
            return
        
        if not display_name:
            display_name = name
        
        # 如果是新建模式，检查Chrome是否正在运行
        if not self.is_edit_mode:
            if self._is_chrome_running():
                reply = QMessageBox.question(
                    self, "Chrome正在运行", 
                    "检测到Chrome浏览器正在运行！\n\n"
                    "为了确保Profile能够正确创建并在Chrome中显示，\n"
                    "建议您先完全关闭Chrome浏览器。\n\n"
                    "是否继续创建Profile？\n"
                    "（如果Chrome未完全关闭，新Profile可能不会立即显示）",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                if reply == QMessageBox.No:
                    return
        
        try:
            if self.is_edit_mode:
                # 编辑模式：只更新显示名称
                success = self.profile_manager.update_profile_display_name(self.profile.name, display_name)
                if success:
                    QMessageBox.information(self, "成功", "Profile信息已更新")
                    self.accept()
                else:
                    QMessageBox.critical(self, "错误", "更新Profile失败")
            else:
                # 新建模式
                # 检查显示名称是否已存在
                if self.profile_manager.profile_exists(display_name):
                    QMessageBox.warning(self, "错误", f"Profile显示名称 '{display_name}' 已存在")
                    return
                
                # 创建新Profile
                success = self.profile_manager.create_profile(name, display_name)
                if success:
                    # 显示成功消息和后续步骤提示
                    msg = f"成功创建Profile: {display_name}\n\n"
                    msg += "📝 后续步骤：\n"
                    msg += "1. 完全关闭所有Chrome窗口\n"
                    msg += "2. 重新启动Chrome浏览器\n"
                    msg += "3. 点击Chrome右上角的头像按钮\n"
                    msg += "4. 新Profile应该会出现在列表中\n\n"
                    msg += "💡 提示：如果新Profile没有立即显示，请等待几秒钟或重启Chrome。"
                    
                    QMessageBox.information(self, "创建成功", msg)
                    self.accept()
                else:
                    QMessageBox.critical(self, "错误", "创建Profile失败")
        
        except Exception as e:
            QMessageBox.critical(self, "错误", f"操作失败: {str(e)}")
    
    def delete_profile(self):
        """删除Profile"""
        if not self.profile:
            return
        
        # 检查是否是默认Profile
        if self.profile.name == "Default":
            QMessageBox.warning(
                self, "无法删除",
                "⚠️ 无法删除默认Profile\n\n"
                "默认Profile是Chrome的核心Profile，删除可能导致Chrome无法正常工作。"
            )
            return
        
        # 检查Chrome是否正在运行
        if self._is_chrome_running():
            reply = QMessageBox.question(
                self, "Chrome正在运行",
                "⚠️ 检测到Chrome浏览器正在运行！\n\n"
                "为了安全起见，建议您先完全关闭Chrome浏览器，\n"
                "然后再删除Profile。\n\n"
                "是否继续删除？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.No:
                return
        
        # 创建详细的删除确认对话框
        dialog = QDialog(self)
        dialog.setWindowTitle("确认删除Profile")
        dialog.setFixedSize(500, 450)
        dialog.setModal(True)
        
        layout = QVBoxLayout()
        
        # 警告标题
        warning_widget = QWidget()
        warning_layout = QHBoxLayout()
        warning_layout.setContentsMargins(10, 10, 10, 10)
        
        warning_icon = QLabel("⚠️")
        warning_icon.setStyleSheet("font-size: 32px;")
        warning_icon.setFixedSize(40, 40)
        warning_icon.setAlignment(Qt.AlignCenter)
        
        warning_title = QLabel("危险操作：删除Profile")
        warning_title.setFont(QFont("", 14, QFont.Bold))
        warning_title.setStyleSheet("color: #dc3545;")
        
        warning_layout.addWidget(warning_icon)
        warning_layout.addWidget(warning_title)
        warning_layout.addStretch()
        
        warning_widget.setLayout(warning_layout)
        warning_widget.setStyleSheet("""
            QWidget {
                background-color: #f8d7da;
                border: 1px solid #f5c6cb;
                border-radius: 6px;
                margin-bottom: 15px;
            }
        """)
        
        layout.addWidget(warning_widget)
        
        # Profile信息
        info_label = QLabel(f"您即将删除Profile: <b>{self.profile.display_name}</b>")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # 详细信息
        details_group = QGroupBox("将要删除的数据")
        details_layout = QVBoxLayout()
        
        # 计算要删除的数据
        from core.profile_manager import ProfileManager
        pm = ProfileManager()
        size_str = pm.format_size(self.profile.storage_size)
        
        delete_items = [
            f"📁 整个Profile目录 ({size_str})",
            f"📚 所有书签 ({self.profile.bookmarks_count} 个)",
            f"🔌 所有扩展程序 ({self.profile.extensions_count} 个)",
            "🔒 所有已保存的登录信息和密码",
            "🕒 完整的浏览历史记录",
            "🍪 所有Cookie和网站数据",
            "📥 下载历史记录",
            "⚙️ 所有个人设置和偏好",
            "📝 自动填充数据",
            "🔐 已保存的信用卡信息",
            "📱 同步数据（如果已启用）",
            "🎨 主题和自定义设置"
        ]
        
        for item in delete_items:
            item_label = QLabel(f"• {item}")
            item_label.setStyleSheet("margin: 2px 0; color: #495057;")
            details_layout.addWidget(item_label)
        
        details_group.setLayout(details_layout)
        layout.addWidget(details_group)
        
        # 最终警告
        final_warning = QLabel(
            "🚨 <b>此操作无法撤销！</b><br>"
            "🔥 所有数据将被永久删除<br>"
            "📱 如果此Profile已与Google账号同步，本地删除不会影响云端数据"
        )
        final_warning.setWordWrap(True)
        final_warning.setStyleSheet("""
            QLabel {
                background-color: #fff3cd;
                border: 1px solid #ffeaa7;
                border-radius: 4px;
                padding: 10px;
                margin: 10px 0;
                color: #856404;
            }
        """)
        layout.addWidget(final_warning)
        
        # 确认输入
        confirm_layout = QHBoxLayout()
        confirm_label = QLabel("请输入Profile名称以确认删除:")
        self.confirm_input = QLineEdit()
        self.confirm_input.setPlaceholderText(f"输入: {self.profile.display_name}")
        
        confirm_layout.addWidget(confirm_label)
        confirm_layout.addWidget(self.confirm_input)
        layout.addLayout(confirm_layout)
        
        # 按钮
        button_layout = QHBoxLayout()
        
        cancel_btn = QPushButton("取消")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 8px 20px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        
        delete_btn = QPushButton("🗑️ 确认删除")
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                padding: 8px 20px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        delete_btn.setEnabled(False)
        
        # 验证输入
        def validate_confirm_input():
            if self.confirm_input.text().strip() == self.profile.display_name:
                delete_btn.setEnabled(True)
            else:
                delete_btn.setEnabled(False)
        
        self.confirm_input.textChanged.connect(validate_confirm_input)
        
        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(delete_btn)
        
        layout.addLayout(button_layout)
        dialog.setLayout(layout)
        
        # 连接按钮事件
        cancel_btn.clicked.connect(dialog.reject)
        
        def perform_delete():
            try:
                success = self.profile_manager.delete_profile(self.profile.name)
                if success:
                    QMessageBox.information(
                        self, "删除成功", 
                        f"✅ Profile '{self.profile.display_name}' 已成功删除\n\n"
                        "建议重启Chrome以确保完全生效。"
                    )
                    dialog.accept()
                    self.accept()  # 关闭编辑对话框
                else:
                    QMessageBox.critical(self, "删除失败", "❌ 删除Profile失败，请检查权限或重试")
            except Exception as e:
                QMessageBox.critical(self, "删除错误", f"❌ 删除失败: {str(e)}")
        
        delete_btn.clicked.connect(perform_delete)
        
        # 显示对话框
        dialog.exec_()

class ProfileItemWidget(QWidget):
    """自定义Profile列表项控件"""
    
    # 定义信号
    startRequested = pyqtSignal(object)  # 启动信号
    closeRequested = pyqtSignal(object)  # 关闭信号
    
    def __init__(self, profile, is_running=False, browser_info=None):
        super().__init__()
        self.profile = profile
        self.is_running = is_running
        self.browser_info = browser_info
        self.is_transitioning = False  # 添加过渡状态标志
        self.transition_type = None  # 'starting' 或 'stopping'
        self.setup_ui()
        self.update_button_states()
    
    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)
        
        # 主信息行
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # 状态和名称
        info_layout = QVBoxLayout()
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(2)
        
        # 状态指示器和名称
        status_layout = QHBoxLayout()
        status_layout.setContentsMargins(0, 0, 0, 0)
        
        self.status_label = QLabel("⚪")
        self.status_label.setFixedSize(16, 16)
        
        self.name_label = QLabel(self.profile.display_name)
        self.name_label.setFont(QFont("", 12, QFont.Bold))
        
        status_layout.addWidget(self.status_label)
        status_layout.addWidget(self.name_label)
        status_layout.addStretch()
        
        info_layout.addLayout(status_layout)
        
        # Profile文件夹信息
        profile_folder = self.profile.name if self.profile.name != "Default" else "默认Profile"
        folder_label = QLabel(f"📁 {profile_folder}")
        folder_label.setStyleSheet("color: #666; font-size: 10px;")
        info_layout.addWidget(folder_label)
        
        # 书签和扩展信息
        stats_label = QLabel(f"📚 书签: {self.profile.bookmarks_count} | 🧩 扩展: {self.profile.extensions_count}")
        stats_label.setStyleSheet("color: #666; font-size: 10px;")
        info_layout.addWidget(stats_label)
        
        # 运行信息（如果正在运行）
        self.runtime_label = QLabel("")
        self.runtime_label.setStyleSheet("color: #007bff; font-size: 10px;")
        info_layout.addWidget(self.runtime_label)
        
        main_layout.addLayout(info_layout, 1)  # 拉伸因子为1
        
        # 操作按钮 - 只保留一个切换按钮
        button_layout = QVBoxLayout()
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(2)
        
        # 启动/关闭切换按钮
        self.toggle_button = QPushButton("启动")
        self.toggle_button.setFixedSize(80, 30)
        self.toggle_button.clicked.connect(self.on_toggle_clicked)
        
        button_layout.addWidget(self.toggle_button)
        button_layout.addStretch()  # 垂直居中
        
        main_layout.addLayout(button_layout)
        
        layout.addLayout(main_layout)
        
        self.setLayout(layout)
        
        # 设置样式
        self.setStyleSheet("""
            ProfileItemWidget {
                background-color: white;
                border: 1px solid #e9ecef;
                border-radius: 6px;
                margin: 2px;
            }
            ProfileItemWidget:hover {
                background-color: #f8f9fa;
                border-color: #007bff;
            }
            QPushButton {
                background-color: #f8f9fa;
                border: 1px solid #ccc;
                border-radius: 3px;
                font-size: 10px;
                padding: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e9ecef;
            }
            QPushButton:pressed {
                background-color: #dee2e6;
            }
        """)
    
    def set_selected(self, selected):
        """设置选中状态的样式"""
        if selected:
            self.setStyleSheet("""
                ProfileItemWidget {
                    background-color: #e8f4fd;
                    border: 2px solid #2196f3;
                    border-radius: 6px;
                    margin: 2px;
                }
                ProfileItemWidget:hover {
                    background-color: #e8f4fd;
                    border-color: #1976d2;
                }
                QPushButton {
                    background-color: #f8f9fa;
                    border: 1px solid #ccc;
                    border-radius: 3px;
                    font-size: 10px;
                    padding: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #e9ecef;
                }
                QPushButton:pressed {
                    background-color: #dee2e6;
                }
            """)
        else:
            self.setStyleSheet("""
                ProfileItemWidget {
                    background-color: white;
                    border: 1px solid #e9ecef;
                    border-radius: 6px;
                    margin: 2px;
                }
                ProfileItemWidget:hover {
                    background-color: #f8f9fa;
                    border-color: #007bff;
                }
                QPushButton {
                    background-color: #f8f9fa;
                    border: 1px solid #ccc;
                    border-radius: 3px;
                    font-size: 10px;
                    padding: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #e9ecef;
                }
                QPushButton:pressed {
                    background-color: #dee2e6;
                }
            """)
    
    def on_toggle_clicked(self):
        """切换按钮点击处理"""
        if self.is_transitioning:
            # 如果正在过渡中，忽略点击
            return
            
        if self.is_running:
            # 当前运行中，执行关闭
            self.set_transition_state('stopping')
            self.closeRequested.emit(self.profile)
        else:
            # 当前未运行，执行启动
            self.set_transition_state('starting')
            self.startRequested.emit(self.profile)
    
    def set_transition_state(self, transition_type):
        """设置过渡状态"""
        self.is_transitioning = True
        self.transition_type = transition_type
        self.update_button_states()
    
    def clear_transition_state(self):
        """清除过渡状态"""
        self.is_transitioning = False
        self.transition_type = None
        self.update_button_states()
    
    def update_status(self, is_running, browser_info=None):
        """更新运行状态"""
        # 清除过渡状态
        if self.is_transitioning:
            self.clear_transition_state()
            
        self.is_running = is_running
        self.browser_info = browser_info
        
        if is_running:
            self.status_label.setText("🟢")
            
            if browser_info:
                memory_mb = browser_info['memory_usage'] / (1024 * 1024)
                pid_text = f"🆔 PID: {browser_info['pid']}"
                if browser_info.get('discovered'):
                    pid_text += " 📡"
                self.runtime_label.setText(f"💾 内存: {memory_mb:.1f}MB | {pid_text}")
            else:
                self.runtime_label.setText("🟢 运行中")
        else:
            self.status_label.setText("⚪")
            self.runtime_label.setText("")
        
        self.update_button_states()
    
    def update_button_states(self):
        """更新按钮状态"""
        if self.is_transitioning:
            # 过渡状态 - 显示黄色并禁用
            self.toggle_button.setEnabled(False)
            if self.transition_type == 'starting':
                self.toggle_button.setText("启动中")
                self.status_label.setText("🟡")
            elif self.transition_type == 'stopping':
                self.toggle_button.setText("关闭中")
                self.status_label.setText("🟡")
            
            self.toggle_button.setStyleSheet("""
                QPushButton {
                    background-color: #ffc107;
                    color: #212529;
                    border: 1px solid #ffc107;
                    border-radius: 3px;
                    font-size: 10px;
                    padding: 4px;
                    font-weight: bold;
                }
                QPushButton:disabled {
                    background-color: #ffc107;
                    color: #6c757d;
                }
            """)
        elif self.is_running:
            # 运行中状态 - 显示关闭按钮
            self.toggle_button.setEnabled(True)
            self.toggle_button.setText("关闭")
            self.toggle_button.setStyleSheet("""
                QPushButton {
                    background-color: #dc3545;
                    color: white;
                    border: 1px solid #dc3545;
                    border-radius: 3px;
                    font-size: 10px;
                    padding: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #c82333;
                }
                QPushButton:pressed {
                    background-color: #bd2130;
                }
            """)
        else:
            # 停止状态 - 显示启动按钮
            self.toggle_button.setEnabled(True)
            self.toggle_button.setText("启动")
            self.toggle_button.setStyleSheet("""
                QPushButton {
                    background-color: #28a745;
                    color: white;
                    border: 1px solid #28a745;
                    border-radius: 3px;
                    font-size: 10px;
                    padding: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #218838;
                }
                QPushButton:pressed {
                    background-color: #1e7e34;
                }
            """)

class ProfileListWidget(QListWidget):
    """自定义Profile列表控件"""
    
    # 添加信号，当排序改变时发出
    orderChanged = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.setMinimumWidth(350)  # 增加宽度以容纳按钮
        self.setMaximumWidth(450)
        
        # 启用拖拽排序
        self.setDragDropMode(QListWidget.InternalMove)
        self.setDefaultDropAction(Qt.MoveAction)
        
        # 跟踪当前选中的项目
        self.current_selected_item = None
        
        # 连接选中状态变化信号
        self.itemSelectionChanged.connect(self.on_selection_changed)
        
        # 设置样式
        self.setStyleSheet("""
            QListWidget {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 5px;
            }
            QListWidget::item {
                background: transparent;
                border: none;
                padding: 0px;
                margin: 3px;
            }
            QListWidget::item:selected {
                background-color: #e3f2fd;
                border: 2px solid #2196f3;
                border-radius: 8px;
            }
            QListWidget::item:hover {
                background-color: #f5f5f5;
                border: 1px solid #bdbdbd;
                border-radius: 8px;
            }
        """)
    
    def on_selection_changed(self):
        """处理选中状态变化"""
        # 清除之前选中项的样式
        if self.current_selected_item:
            old_widget = self.itemWidget(self.current_selected_item)
            if isinstance(old_widget, ProfileItemWidget):
                old_widget.set_selected(False)
        
        # 设置新选中项的样式
        selected_items = self.selectedItems()
        if selected_items:
            self.current_selected_item = selected_items[0]
            new_widget = self.itemWidget(self.current_selected_item)
            if isinstance(new_widget, ProfileItemWidget):
                new_widget.set_selected(True)
        else:
            self.current_selected_item = None
    
    def dropEvent(self, event):
        """处理拖拽放置事件"""
        super().dropEvent(event)
        # 拖拽完成后发出信号
        self.orderChanged.emit()

class ProfileInfoWidget(QWidget):
    """Profile详细信息控件（移除操作按钮）"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.current_profile = None
        self.config_manager = ConfigManager()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Profile基本信息
        info_group = QGroupBox("Profile信息")
        info_layout = QGridLayout()
        
        self.name_label = QLabel("未选择Profile")
        self.name_label.setFont(QFont("", 14, QFont.Bold))
        
        self.path_label = QLabel("")
        self.path_label.setWordWrap(True)
        
        self.created_label = QLabel("")
        self.used_label = QLabel("")
        self.bookmarks_label = QLabel("")
        self.extensions_label = QLabel("")
        self.size_label = QLabel("")
        
        info_layout.addWidget(QLabel("名称:"), 0, 0)
        info_layout.addWidget(self.name_label, 0, 1)
        info_layout.addWidget(QLabel("路径:"), 1, 0)
        info_layout.addWidget(self.path_label, 1, 1)
        info_layout.addWidget(QLabel("创建时间:"), 2, 0)
        info_layout.addWidget(self.created_label, 2, 1)
        info_layout.addWidget(QLabel("最后使用:"), 3, 0)
        info_layout.addWidget(self.used_label, 3, 1)
        info_layout.addWidget(QLabel("书签数量:"), 4, 0)
        info_layout.addWidget(self.bookmarks_label, 4, 1)
        info_layout.addWidget(QLabel("扩展程序:"), 5, 0)
        info_layout.addWidget(self.extensions_label, 5, 1)
        info_layout.addWidget(QLabel("存储大小:"), 6, 0)
        info_layout.addWidget(self.size_label, 6, 1)
        
        info_group.setLayout(info_layout)
        
        # 配置选项
        config_group = QGroupBox("启动配置")
        config_layout = QGridLayout()
        
        # 语言选择
        self.language_combo = QComboBox()
        self.language_combo.addItems(["zh-CN", "en-US", "ja", "ko"])
        self.language_combo.currentTextChanged.connect(self.on_config_changed)
        
        # 代理配置
        self.proxy_enabled = QCheckBox("启用代理")
        self.proxy_enabled.stateChanged.connect(self.on_proxy_enabled_changed)
        self.proxy_enabled.stateChanged.connect(self.on_config_changed)
        
        self.proxy_type_combo = QComboBox()
        self.proxy_type_combo.addItems(["http", "socks5", "socks4"])
        self.proxy_type_combo.currentTextChanged.connect(self.on_config_changed)
        
        self.proxy_server_edit = QLineEdit()
        self.proxy_server_edit.setPlaceholderText("例如: 127.0.0.1")
        self.proxy_server_edit.textChanged.connect(self.on_config_changed)
        
        self.proxy_port_spin = QSpinBox()
        self.proxy_port_spin.setRange(1, 65535)
        self.proxy_port_spin.setValue(8080)
        self.proxy_port_spin.valueChanged.connect(self.on_config_changed)
        
        # 代理认证
        self.proxy_username_edit = QLineEdit()
        self.proxy_username_edit.setPlaceholderText("用户名（可选）")
        self.proxy_username_edit.textChanged.connect(self.on_config_changed)
        
        self.proxy_password_edit = QLineEdit()
        self.proxy_password_edit.setPlaceholderText("密码（可选）")
        self.proxy_password_edit.setEchoMode(QLineEdit.Password)
        self.proxy_password_edit.textChanged.connect(self.on_config_changed)
        
        # 窗口大小
        self.window_width_spin = QSpinBox()
        self.window_width_spin.setRange(800, 3840)
        self.window_width_spin.setValue(1280)
        self.window_width_spin.valueChanged.connect(self.on_config_changed)
        
        self.window_height_spin = QSpinBox()
        self.window_height_spin.setRange(600, 2160)
        self.window_height_spin.setValue(720)
        self.window_height_spin.valueChanged.connect(self.on_config_changed)
        
        config_layout.addWidget(QLabel("语言:"), 0, 0)
        config_layout.addWidget(self.language_combo, 0, 1)
        
        config_layout.addWidget(self.proxy_enabled, 1, 0, 1, 2)
        config_layout.addWidget(QLabel("代理类型:"), 2, 0)
        config_layout.addWidget(self.proxy_type_combo, 2, 1)
        config_layout.addWidget(QLabel("代理服务器:"), 3, 0)
        config_layout.addWidget(self.proxy_server_edit, 3, 1)
        config_layout.addWidget(QLabel("端口:"), 4, 0)
        config_layout.addWidget(self.proxy_port_spin, 4, 1)
        config_layout.addWidget(QLabel("用户名:"), 5, 0)
        config_layout.addWidget(self.proxy_username_edit, 5, 1)
        config_layout.addWidget(QLabel("密码:"), 6, 0)
        config_layout.addWidget(self.proxy_password_edit, 6, 1)
        
        config_layout.addWidget(QLabel("窗口宽度:"), 7, 0)
        config_layout.addWidget(self.window_width_spin, 7, 1)
        config_layout.addWidget(QLabel("窗口高度:"), 8, 0)
        config_layout.addWidget(self.window_height_spin, 8, 1)
        
        config_group.setLayout(config_layout)
        
        # 配置操作按钮
        config_button_layout = QHBoxLayout()
        self.save_config_button = QPushButton("💾 保存配置")
        self.load_config_button = QPushButton("📂 加载配置")
        self.reset_config_button = QPushButton("🔄 重置配置")
        
        self.save_config_button.setStyleSheet("""
            QPushButton {
                background-color: #17a2b8;
                color: white;
                border: none;
                padding: 5px 15px;
                border-radius: 3px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #138496;
            }
        """)
        
        self.load_config_button.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 5px 15px;
                border-radius: 3px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #545b62;
            }
        """)
        
        self.reset_config_button.setStyleSheet("""
            QPushButton {
                background-color: #fd7e14;
                color: white;
                border: none;
                padding: 5px 15px;
                border-radius: 3px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #e85d12;
            }
        """)
        
        self.save_config_button.clicked.connect(self.save_current_config)
        self.load_config_button.clicked.connect(self.load_profile_config)
        self.reset_config_button.clicked.connect(self.reset_to_default_config)
        
        config_button_layout.addWidget(self.save_config_button)
        config_button_layout.addWidget(self.load_config_button)
        config_button_layout.addWidget(self.reset_config_button)
        config_button_layout.addStretch()
        
        layout.addWidget(info_group)
        layout.addWidget(config_group)
        layout.addLayout(config_button_layout)
        layout.addStretch()
        
        self.setLayout(layout)
        
        # 初始状态下禁用代理相关控件
        self.on_proxy_enabled_changed()
    
    def on_proxy_enabled_changed(self):
        """代理启用状态改变时的处理"""
        enabled = self.proxy_enabled.isChecked()
        self.proxy_type_combo.setEnabled(enabled)
        self.proxy_server_edit.setEnabled(enabled)
        self.proxy_port_spin.setEnabled(enabled)
        self.proxy_username_edit.setEnabled(enabled)
        self.proxy_password_edit.setEnabled(enabled)
    
    def on_config_changed(self):
        """配置改变时的处理（自动保存）"""
        if self.current_profile and hasattr(self, '_config_loaded'):
            # 延时保存，避免频繁保存
            if not hasattr(self, '_save_timer'):
                self._save_timer = QTimer()
                self._save_timer.setSingleShot(True)
                self._save_timer.timeout.connect(self.auto_save_config)
            
            self._save_timer.stop()
            self._save_timer.start(1000)  # 1秒后自动保存
    
    def auto_save_config(self):
        """自动保存配置"""
        if self.current_profile:
            config = self.get_current_config()
            self.config_manager.save_config(config)
    
    def get_current_config(self) -> ProfileConfig:
        """获取当前界面配置"""
        if not self.current_profile:
            return ProfileConfig("unknown")
        
        return ProfileConfig(
            profile_name=self.current_profile.name,
            language=self.language_combo.currentText(),
            proxy_enabled=self.proxy_enabled.isChecked(),
            proxy_type=self.proxy_type_combo.currentText(),
            proxy_server=self.proxy_server_edit.text().strip(),
            proxy_port=self.proxy_port_spin.value(),
            proxy_username=self.proxy_username_edit.text().strip(),
            proxy_password=self.proxy_password_edit.text(),
            window_width=self.window_width_spin.value(),
            window_height=self.window_height_spin.value()
        )
    
    def apply_config(self, config: ProfileConfig):
        """应用配置到界面"""
        # 临时阻止信号，避免触发自动保存
        self._config_loaded = False
        
        self.language_combo.setCurrentText(config.language)
        self.proxy_enabled.setChecked(config.proxy_enabled)
        self.proxy_type_combo.setCurrentText(config.proxy_type)
        self.proxy_server_edit.setText(config.proxy_server)
        self.proxy_port_spin.setValue(config.proxy_port)
        self.proxy_username_edit.setText(config.proxy_username)
        self.proxy_password_edit.setText(config.proxy_password)
        self.window_width_spin.setValue(config.window_width)
        self.window_height_spin.setValue(config.window_height)
        
        self.on_proxy_enabled_changed()
        
        # 恢复信号
        self._config_loaded = True
    
    def save_current_config(self):
        """手动保存当前配置"""
        if not self.current_profile:
            QMessageBox.warning(self, "警告", "请先选择一个Profile")
            return
        
        config = self.get_current_config()
        if self.config_manager.save_config(config):
            QMessageBox.information(self, "成功", f"配置已保存\n\nProfile: {self.current_profile.display_name}")
        else:
            QMessageBox.critical(self, "错误", "保存配置失败")
    
    def load_profile_config(self):
        """手动加载配置"""
        if not self.current_profile:
            QMessageBox.warning(self, "警告", "请先选择一个Profile")
            return
        
        config = self.config_manager.load_config(self.current_profile.name)
        self.apply_config(config)
        QMessageBox.information(self, "成功", f"配置已加载\n\nProfile: {self.current_profile.display_name}")
    
    def reset_to_default_config(self):
        """重置为默认配置"""
        if not self.current_profile:
            QMessageBox.warning(self, "警告", "请先选择一个Profile")
            return
        
        reply = QMessageBox.question(self, "确认", "确定要重置为默认配置吗？\n当前配置将被覆盖。",
                                   QMessageBox.Yes | QMessageBox.No,
                                   QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            default_config = ProfileConfig(profile_name=self.current_profile.name)
            self.apply_config(default_config)
            self.config_manager.save_config(default_config)
            QMessageBox.information(self, "成功", "已重置为默认配置")
    
    def update_profile_info(self, profile: ProfileInfo):
        """更新Profile信息显示"""
        self.current_profile = profile
        
        self.name_label.setText(profile.display_name)
        self.path_label.setText(profile.path)
        
        if profile.created_time:
            self.created_label.setText(profile.created_time.strftime("%Y-%m-%d %H:%M:%S"))
        else:
            self.created_label.setText("未知")
        
        if profile.last_used_time:
            self.used_label.setText(profile.last_used_time.strftime("%Y-%m-%d %H:%M:%S"))
        else:
            self.used_label.setText("未知")
        
        self.bookmarks_label.setText(str(profile.bookmarks_count))
        self.extensions_label.setText(str(profile.extensions_count))
        
        # 格式化存储大小
        from core.profile_manager import ProfileManager
        pm = ProfileManager()
        self.size_label.setText(pm.format_size(profile.storage_size))
        
        # 自动加载配置
        config = self.config_manager.load_config(profile.name)
        self.apply_config(config)

class StatusMonitorWidget(QWidget):
    """状态监控控件"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.setMinimumWidth(300)
        self.setMaximumWidth(400)
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # 运行状态
        status_group = QGroupBox("运行状态")
        self.status_tree = QTreeWidget()
        self.status_tree.setHeaderLabels(["Profile", "状态", "PID", "内存"])
        status_group_layout = QVBoxLayout()
        status_group_layout.addWidget(self.status_tree)
        status_group.setLayout(status_group_layout)
        
        # 操作日志
        log_group = QGroupBox("操作日志")
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(200)  # 增加日志区域高度
        self.log_text.setReadOnly(True)
        log_group_layout = QVBoxLayout()
        log_group_layout.addWidget(self.log_text)
        log_group.setLayout(log_group_layout)
        
        layout.addWidget(status_group)
        layout.addWidget(log_group)
        
        self.setLayout(layout)
    
    def update_status(self, running_browsers: dict):
        """更新状态显示（移除了total_profiles参数，因为系统信息现在在状态栏）"""
        self.status_tree.clear()
        
        for profile_name, browser_info in running_browsers.items():
            item = QTreeWidgetItem()
            item.setText(0, profile_name)
            
            # 检查是否是外部发现的浏览器
            if browser_info.get('discovered'):
                item.setText(1, "🟢 运行中 📡")  # 添加天线图标表示外部发现
            else:
                item.setText(1, "🟢 运行中")
            
            item.setText(2, str(browser_info['pid']))
            
            memory_mb = browser_info['memory_usage'] / (1024 * 1024)
            item.setText(3, f"{memory_mb:.1f} MB")
            
            # 设置运行中的项目为绿色
            item.setForeground(1, QColor(0, 128, 0))
            
            self.status_tree.addTopLevelItem(item)
        
        # 如果没有运行中的浏览器，显示提示信息
        if not running_browsers:
            item = QTreeWidgetItem()
            item.setText(0, "无运行中的浏览器")
            item.setText(1, "⚪ 空闲")
            item.setText(2, "-")
            item.setText(3, "-")
            item.setForeground(1, QColor(128, 128, 128))
            self.status_tree.addTopLevelItem(item)
    
    def add_log(self, message: str):
        """添加日志消息"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")

class MainWindow(QMainWindow):
    """主窗口"""
    
    def __init__(self):
        super().__init__()
        print("开始初始化主窗口...")
        
        self.profile_manager = ProfileManager()
        self.browser_manager = BrowserManager()
        self.config_manager = ConfigManager()
        
        # 初始化外部检查时间戳
        self._last_external_check = 0
        
        print("设置窗口图标...")
        # 设置窗口图标
        self.setWindowIcon(get_application_icon())
        
        print("设置UI...")
        self.setup_ui()
        
        print("设置定时器...")
        self.setup_timer()
        
        print("开始加载Profile...")
        # 临时简化加载过程
        try:
            self.load_profiles_simple()
        except Exception as e:
            print(f"加载Profile失败: {e}")
            import traceback
            traceback.print_exc()
        
        print("主窗口初始化完成")
        
        # 在日志中提示用户可以拖拽排序
        self.status_monitor.add_log("💡 提示：可以拖拽Profile来调整排序，排序会自动保存")
        self.status_monitor.add_log("📝 提示：选中Profile后可点击'✏️ 编辑Profile'按钮来编辑或删除Profile")
    
    def setup_ui(self):
        """设置用户界面"""
        print("开始设置UI - 设置窗口标题和几何信息...")
        self.setWindowTitle("多开浏览器管理工具")
        self.setGeometry(100, 100, 1200, 800)
        
        print("开始设置UI - 设置窗口图标...")
        # 设置窗口图标（再次确保设置成功）
        self.setWindowIcon(get_application_icon())
        
        print("开始设置UI - 创建中央控件...")
        # 创建中央控件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        print("开始设置UI - 创建主要布局...")
        # 创建主要布局
        main_layout = QHBoxLayout()
        
        print("开始设置UI - 创建左侧面板...")
        # 左侧Profile列表
        left_panel = QWidget()
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(5)
        
        print("开始设置UI - 创建Profile操作工具栏...")
        # Profile操作工具栏
        profile_toolbar = QWidget()
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setContentsMargins(5, 5, 5, 5)
        toolbar_layout.setSpacing(8)
        
        print("开始设置UI - 创建左侧按钮组...")
        # 左侧按钮组
        left_button_group = QWidget()
        left_layout_buttons = QHBoxLayout()
        left_layout_buttons.setContentsMargins(0, 0, 0, 0)
        left_layout_buttons.setSpacing(8)
        
        print("开始设置UI - 创建新建Profile按钮...")
        # 新建Profile按钮
        self.new_profile_button = QPushButton("新建")
        self.new_profile_button.setFixedHeight(28)
        self.new_profile_button.setMinimumWidth(60)  # 调整宽度
        self.new_profile_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 11px;
                font-weight: bold;
                text-align: center;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:pressed {
                background-color: #1e7e34;
            }
        """)
        print("开始设置UI - 连接新建Profile按钮信号...")
        self.new_profile_button.clicked.connect(self.new_profile)
        
        print("开始设置UI - 添加新建按钮到左侧布局...")
        left_layout_buttons.addWidget(self.new_profile_button)
        left_button_group.setLayout(left_layout_buttons)
        
        print("开始设置UI - 创建右侧按钮组...")
        # 右侧按钮组
        right_button_group = QWidget()
        right_layout_buttons = QHBoxLayout()
        right_layout_buttons.setContentsMargins(0, 0, 0, 0)
        right_layout_buttons.setSpacing(6)  # 减小间距
        
        print("开始设置UI - 创建编辑Profile按钮...")
        # 编辑Profile按钮
        self.edit_profile_button = QPushButton("编辑")
        self.edit_profile_button.setFixedHeight(28)
        self.edit_profile_button.setMinimumWidth(60)  # 调整宽度
        self.edit_profile_button.setStyleSheet("""
            QPushButton {
                background-color: #ffc107;
                color: #212529;
                border: none;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 11px;
                font-weight: bold;
                text-align: center;
            }
            QPushButton:hover {
                background-color: #e0a800;
            }
            QPushButton:pressed {
                background-color: #d39e00;
            }
            QPushButton:disabled {
                background-color: #6c757d;
                color: #fff;
            }
        """)
        print("开始设置UI - 连接编辑Profile按钮信号...")
        self.edit_profile_button.clicked.connect(self.edit_profile)
        self.edit_profile_button.setEnabled(False)  # 初始禁用
        
        print("开始设置UI - 创建删除Profile按钮...")
        # 删除Profile按钮
        self.delete_profile_button = QPushButton("删除")
        self.delete_profile_button.setFixedHeight(28)
        self.delete_profile_button.setMinimumWidth(60)  # 调整宽度
        self.delete_profile_button.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 11px;
                font-weight: bold;
                text-align: center;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
            QPushButton:pressed {
                background-color: #bd2130;
            }
            QPushButton:disabled {
                background-color: #6c757d;
                color: #fff;
            }
        """)
        print("开始设置UI - 连接删除Profile按钮信号...")
        self.delete_profile_button.clicked.connect(self.delete_selected_profile)
        self.delete_profile_button.setEnabled(False)  # 初始禁用
        
        print("开始设置UI - 添加按钮到右侧布局...")
        right_layout_buttons.addWidget(self.edit_profile_button)
        right_layout_buttons.addWidget(self.delete_profile_button)
        right_button_group.setLayout(right_layout_buttons)
        
        print("开始设置UI - 组装工具栏...")
        # 添加到主工具栏布局
        toolbar_layout.addWidget(left_button_group)
        toolbar_layout.addStretch()  # 添加弹性空间
        toolbar_layout.addWidget(right_button_group)
        
        profile_toolbar.setLayout(toolbar_layout)
        profile_toolbar.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                margin-bottom: 5px;
            }
        """)
        
        print("开始设置UI - 创建Profile列表...")
        # Profile列表
        self.profile_list = ProfileListWidget()
        print("开始设置UI - 连接Profile列表信号...")
        self.profile_list.itemClicked.connect(self.on_profile_selected)
        self.profile_list.itemDoubleClicked.connect(self.on_profile_double_clicked)
        self.profile_list.orderChanged.connect(self.on_profile_order_changed)
        
        print("开始设置UI - 组装左侧面板...")
        left_layout.addWidget(profile_toolbar)
        left_layout.addWidget(self.profile_list)
        left_panel.setLayout(left_layout)
        
        print("开始设置UI - 创建中间详细信息...")
        # 中间详细信息
        self.profile_info = ProfileInfoWidget()
        
        print("开始设置UI - 创建右侧状态监控...")
        # 右侧状态监控
        self.status_monitor = StatusMonitorWidget()
        
        print("开始设置UI - 创建分割器...")
        # 添加到分割器
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(self.profile_info)
        splitter.addWidget(self.status_monitor)
        
        # 设置分割器比例
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        splitter.setStretchFactor(2, 1)
        
        print("开始设置UI - 添加到主布局...")
        main_layout.addWidget(splitter)
        central_widget.setLayout(main_layout)
        
        print("开始设置UI - 创建菜单栏...")
        # 创建菜单栏
        self.create_menu_bar()
        
        print("开始设置UI - 创建状态栏...")
        # 创建状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        print("开始设置UI - 创建状态栏组件...")
        # 创建状态栏的各个部分
        self.status_message = QLabel("就绪")
        self.total_profiles_label = QLabel("总Profile: 0")
        self.running_profiles_label = QLabel("运行中: 0")
        self.total_memory_label = QLabel("内存: 0 MB")
        
        print("开始设置UI - 设置状态栏样式...")
        # 设置标签样式
        info_style = """
            QLabel {
                padding: 2px 8px;
                border: 1px solid #ccc;
                border-radius: 3px;
                background-color: #f8f9fa;
                margin: 2px;
            }
        """
        self.total_profiles_label.setStyleSheet(info_style)
        self.running_profiles_label.setStyleSheet(info_style)
        self.total_memory_label.setStyleSheet(info_style)
        
        print("开始设置UI - 添加组件到状态栏...")
        # 添加到状态栏
        self.status_bar.addWidget(self.status_message, 1)  # 拉伸因子为1，占据剩余空间
        self.status_bar.addPermanentWidget(self.total_profiles_label)
        self.status_bar.addPermanentWidget(self.running_profiles_label)
        self.status_bar.addPermanentWidget(self.total_memory_label)
        
        print("UI设置完成！")
    
    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu('文件')
        
        refresh_action = QAction('刷新Profile列表', self)
        refresh_action.setShortcut('F5')
        refresh_action.triggered.connect(self.load_profiles)
        file_menu.addAction(refresh_action)
        
        file_menu.addSeparator()
        
        # Profile管理子菜单
        profile_menu = file_menu.addMenu('Profile管理')
        
        new_profile_action = QAction('新建Profile', self)
        new_profile_action.setShortcut('Ctrl+N')
        new_profile_action.triggered.connect(self.new_profile)
        profile_menu.addAction(new_profile_action)
        
        edit_profile_action = QAction('编辑Profile', self)
        edit_profile_action.setShortcut('Ctrl+E')
        edit_profile_action.triggered.connect(self.edit_profile)
        profile_menu.addAction(edit_profile_action)
        
        profile_menu.addSeparator()
        
        # 批量操作子菜单
        batch_menu = profile_menu.addMenu('批量操作')
        
        close_all_action = QAction('关闭所有浏览器', self)
        close_all_action.setShortcut('Ctrl+Shift+Q')
        close_all_action.triggered.connect(self.close_all_browsers)
        batch_menu.addAction(close_all_action)
        
        batch_delete_action = QAction('批量删除Profile', self)
        batch_delete_action.triggered.connect(self.batch_delete_profiles)
        batch_menu.addAction(batch_delete_action)
        
        batch_menu.addSeparator()
        
        cleanup_action = QAction('清理无效Profile', self)
        cleanup_action.triggered.connect(self.cleanup_invalid_profiles)
        batch_menu.addAction(cleanup_action)
        
        # 导入导出子菜单
        import_export_menu = profile_menu.addMenu('导入/导出')
        
        export_profiles_action = QAction('导出Profile列表', self)
        export_profiles_action.triggered.connect(self.export_profiles_list)
        import_export_menu.addAction(export_profiles_action)
        
        import_bookmarks_action = QAction('导入书签到Profile', self)
        import_bookmarks_action.triggered.connect(self.import_bookmarks_to_profile)
        import_export_menu.addAction(import_bookmarks_action)
        
        profile_menu.addSeparator()
        
        # Profile排序
        sort_menu = profile_menu.addMenu('排序')
        
        sort_by_name_action = QAction('按名称排序', self)
        sort_by_name_action.triggered.connect(lambda: self.sort_profiles('name'))
        sort_menu.addAction(sort_by_name_action)
        
        sort_by_size_action = QAction('按大小排序', self)
        sort_by_size_action.triggered.connect(lambda: self.sort_profiles('size'))
        sort_menu.addAction(sort_by_size_action)
        
        sort_by_date_action = QAction('按创建时间排序', self)
        sort_by_date_action.triggered.connect(lambda: self.sort_profiles('date'))
        sort_menu.addAction(sort_by_date_action)
        
        sort_menu.addSeparator()
        
        reset_order_action = QAction('重置为默认排序', self)
        reset_order_action.triggered.connect(self.reset_profile_order)
        sort_menu.addAction(reset_order_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('退出', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 工具菜单
        tools_menu = menubar.addMenu('工具')
        
        open_chrome_data_action = QAction('打开Chrome数据目录', self)
        open_chrome_data_action.triggered.connect(self.open_chrome_data_directory)
        tools_menu.addAction(open_chrome_data_action)
        
        system_info_action = QAction('系统信息', self)
        system_info_action.triggered.connect(self.show_system_info)
        tools_menu.addAction(system_info_action)
        
        tools_menu.addSeparator()
        
        preferences_action = QAction('偏好设置', self)
        preferences_action.setShortcut('Ctrl+,')
        preferences_action.triggered.connect(self.show_preferences)
        tools_menu.addAction(preferences_action)
        
        # 帮助菜单
        help_menu = menubar.addMenu('帮助')
        
        shortcuts_action = QAction('快捷键', self)
        shortcuts_action.setShortcut('F1')
        shortcuts_action.triggered.connect(self.show_shortcuts)
        help_menu.addAction(shortcuts_action)
        
        about_action = QAction('关于', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def setup_timer(self):
        """设置定时器，用于更新状态"""
        # 临时禁用定时器来排查CPU占用问题
        print("定时器已临时禁用")
        return
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_status)
        self.timer.start(1000)  # 每1秒更新一次（提高频率）
        
        # 添加一个更频繁的定时器来检测浏览器状态变化
        self.status_check_timer = QTimer()
        self.status_check_timer.timeout.connect(self.check_browser_status)
        self.status_check_timer.start(500)  # 每0.5秒检查一次浏览器状态（大幅提高频率）
    
    def load_profiles_simple(self):
        """简化的Profile加载方法"""
        print("开始简化加载Profile...")
        self.status_message.setText("正在扫描Profile...")
        
        try:
            profiles = self.profile_manager.scan_profiles()
            print(f"扫描到{len(profiles)}个Profile")
            
            self.profile_list.clear()
            
            # 只加载基本的Profile，不检查运行状态
            for profile in profiles:
                print(f"加载Profile: {profile.display_name}")
                
                # 创建ProfileItemWidget，初始状态为未运行
                item_widget = ProfileItemWidget(profile, False, None)
                
                # 连接信号
                item_widget.startRequested.connect(self.start_browser_from_profile)
                item_widget.closeRequested.connect(self.close_browser_from_profile)
                
                # 创建列表项
                item = QListWidgetItem()
                item.setData(Qt.UserRole, profile)
                
                # 设置项目大小
                item.setSizeHint(item_widget.sizeHint())
                
                # 添加到列表
                self.profile_list.addItem(item)
                self.profile_list.setItemWidget(item, item_widget)
            
            self.status_message.setText(f"找到 {len(profiles)} 个Profile")
            print("Profile加载完成")
            
        except Exception as e:
            print(f"加载Profile出错: {e}")
            import traceback
            traceback.print_exc()
            self.status_message.setText("加载Profile失败")
    
    def on_profile_selected(self, item):
        """Profile被选中时的处理"""
        profile = item.data(Qt.UserRole)
        if profile:
            self.profile_info.update_profile_info(profile)
            # 启用编辑和删除按钮（但如果是外部检测的虚拟Profile则不启用）
            if hasattr(profile, 'is_default') and profile.is_default:
                # 默认Profile，不允许编辑和删除
                self.edit_profile_button.setEnabled(False)
                self.delete_profile_button.setEnabled(False)
            elif hasattr(profile, 'path') and "外部检测" in profile.path:
                # 外部检测的Profile，不允许编辑和删除
                self.edit_profile_button.setEnabled(False)
                self.delete_profile_button.setEnabled(False)
            else:
                # 正常的Profile，允许编辑和删除
                self.edit_profile_button.setEnabled(True)
                self.delete_profile_button.setEnabled(True)
        else:
            # 没有选中任何Profile，禁用编辑和删除按钮
            self.edit_profile_button.setEnabled(False)
            self.delete_profile_button.setEnabled(False)
    
    def on_profile_double_clicked(self, item):
        """Profile被双击时启动浏览器"""
        profile = item.data(Qt.UserRole)
        if profile:
            self.start_browser_from_profile(profile)
    
    def on_profile_order_changed(self):
        """Profile顺序改变时的处理"""
        # 获取当前列表中的Profile顺序
        profile_order = []
        for i in range(self.profile_list.count()):
            item = self.profile_list.item(i)
            profile = item.data(Qt.UserRole)
            if profile:
                profile_order.append(profile.name)
        
        # 保存新的排序
        self.config_manager.save_profile_order(profile_order)
        
        # 更新日志
        self.status_monitor.add_log(f"📋 Profile排序已更新")
        self.status_message.setText("Profile排序已保存")
    
    def sort_profiles_by_saved_order(self, profiles: list) -> list:
        """根据保存的排序对Profile列表进行排序"""
        saved_order = self.config_manager.load_profile_order()
        
        if not saved_order:
            # 没有保存的排序，返回原始列表
            return profiles
        
        # 创建Profile名称到Profile对象的映射
        profile_map = {profile.name: profile for profile in profiles}
        
        # 按保存的顺序重新排列
        sorted_profiles = []
        
        # 首先添加按保存顺序排列的Profile
        for profile_name in saved_order:
            if profile_name in profile_map:
                sorted_profiles.append(profile_map[profile_name])
                del profile_map[profile_name]  # 移除已处理的
        
        # 添加新的Profile（不在保存的排序中的）
        for profile in profile_map.values():
            sorted_profiles.append(profile)
        
        return sorted_profiles
    
    def reset_profile_order(self):
        """重置Profile排序为默认顺序"""
        reply = QMessageBox.question(self, "重置排序", "确定要重置Profile排序为默认顺序吗？",
                                   QMessageBox.Yes | QMessageBox.No,
                                   QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            # 删除排序文件
            order_file = os.path.join(self.config_manager.config_dir, "profile_order.json")
            if os.path.exists(order_file):
                try:
                    os.remove(order_file)
                    self.status_monitor.add_log("📋 Profile排序已重置")
                    self.status_message.setText("Profile排序已重置")
                    
                    # 重新加载Profile列表
                    self.load_profiles()
                    
                    QMessageBox.information(self, "成功", "Profile排序已重置为默认顺序")
                except Exception as e:
                    QMessageBox.critical(self, "错误", f"重置排序失败: {e}")
            else:
                QMessageBox.information(self, "提示", "当前使用的就是默认排序")
    
    def start_browser(self):
        """启动浏览器"""
        if not self.profile_info.current_profile:
            QMessageBox.warning(self, "警告", "请先选择一个Profile")
            return
        
        profile = self.profile_info.current_profile
        
        # 检查Chrome是否可用
        if not self.browser_manager.chrome_executable:
            QMessageBox.critical(self, "错误", "未找到Chrome浏览器！\n请确保已正确安装Google Chrome。")
            return
        
        # 检查是否已经在运行
        if self.browser_manager.is_browser_running(profile.name):
            QMessageBox.information(self, "提示", f"浏览器已在运行中\n\nProfile: {profile.display_name}")
            return
        
        # 先保存当前配置
        current_config = self.profile_info.get_current_config()
        self.config_manager.save_config(current_config)
        
        # 获取配置字典用于启动浏览器
        config_dict = self.config_manager.get_config_dict(profile.name)
        
        # 验证代理配置
        if 'proxy_config' in config_dict:
            proxy_config = config_dict['proxy_config']
            if not proxy_config.get('server'):
                QMessageBox.warning(self, "警告", "请输入代理服务器地址")
                return
        
        # 显示启动状态
        self.status_message.setText(f"正在启动浏览器: {profile.display_name}...")
        self.status_monitor.add_log(f"🚀 尝试启动浏览器: {profile.display_name}")
        
        # 使用QTimer延迟执行启动，避免界面卡顿
        QTimer.singleShot(100, lambda: self._do_start_browser_with_config(profile, config_dict))
    
    def _do_start_browser_with_config(self, profile, config_dict):
        """使用配置启动浏览器"""
        try:
            # 启动浏览器
            success = self.browser_manager.start_browser(profile, **config_dict)
            
            if success:
                self.status_monitor.add_log(f"✅ 成功启动浏览器: {profile.display_name}")
                self.status_message.setText(f"✅ 已启动: {profile.display_name}")
                
                # 刷新Profile列表显示状态
                self.load_profiles()
            else:
                # 启动失败，清除过渡状态
                self.clear_profile_transition_state(profile.name)
                self.status_monitor.add_log(f"❌ 启动浏览器失败: {profile.display_name}")
                self.status_message.setText(f"❌ 启动失败: {profile.display_name}")
                
                # 提供更详细的错误信息
                error_msg = f"启动浏览器失败！\n\nProfile: {profile.display_name}\n\n可能的原因：\n"
                error_msg += "• Profile正在被其他Chrome实例使用\n"
                error_msg += "• Chrome浏览器权限问题\n"
                error_msg += "• 代理设置错误\n\n"
                error_msg += "建议：\n• 关闭所有Chrome窗口后重试\n• 检查代理设置是否正确"
                
                QMessageBox.critical(self, "启动失败", error_msg)
        
        except Exception as e:
            # 异常情况，清除过渡状态
            self.clear_profile_transition_state(profile.name)
            self.status_monitor.add_log(f"❌ 启动浏览器异常: {profile.display_name} - {str(e)}")
            self.status_message.setText(f"❌ 启动异常: {profile.display_name}")
            QMessageBox.critical(self, "启动异常", f"启动浏览器时发生异常：\n{str(e)}")
        
        finally:
            # 刷新Profile列表以更新状态
            self.load_profiles()
    
    def close_browser(self):
        """关闭浏览器"""
        if not self.profile_info.current_profile:
            QMessageBox.warning(self, "警告", "请先选择一个Profile")
            return
        
        profile = self.profile_info.current_profile
        
        # 检查浏览器是否在运行
        if not self.browser_manager.is_browser_running(profile.name):
            QMessageBox.information(self, "提示", f"浏览器未在运行\n\nProfile: {profile.display_name}")
            return
        
        self.status_message.setText(f"正在关闭浏览器: {profile.display_name}...")
        success = self.browser_manager.close_browser(profile.name)
        
        if success:
            self.status_monitor.add_log(f"✅ 成功关闭浏览器: {profile.display_name}")
            self.status_message.setText(f"已关闭: {profile.display_name}")
        else:
            self.status_monitor.add_log(f"❌ 关闭浏览器失败: {profile.display_name}")
            QMessageBox.warning(self, "警告", f"关闭浏览器失败: {profile.display_name}")
    
    def update_status(self):
        """更新状态显示"""
        # 传递profiles参数以便发现外部浏览器
        profiles = self.profile_manager.profiles if hasattr(self.profile_manager, 'profiles') else []
        running_browsers = self.browser_manager.get_all_running_browsers(profiles)
        total_profiles = len(profiles)
        
        # 更新状态监控面板
        self.status_monitor.update_status(running_browsers)
        
        # 计算总内存使用
        total_memory = 0
        for browser_info in running_browsers.values():
            total_memory += browser_info['memory_usage'] / (1024 * 1024)
        
        # 更新状态栏的系统信息
        self.total_profiles_label.setText(f"总Profile: {total_profiles}")
        self.running_profiles_label.setText(f"运行中: {len(running_browsers)}")
        self.total_memory_label.setText(f"内存: {total_memory:.1f} MB")
    
    def check_browser_status(self):
        """检查浏览器状态变化，处理外部关闭的情况"""
        # 检查并清理已停止的浏览器
        stopped_browsers = self.browser_manager.check_and_cleanup_stopped_browsers()
        
        # 标记是否需要更新界面
        need_update_ui = False
        
        # 如果有浏览器被外部关闭，更新界面和日志
        if stopped_browsers:
            need_update_ui = True
            for profile_name in stopped_browsers:
                # 查找对应的Profile显示名称
                display_name = profile_name
                for profile in self.profile_manager.profiles:
                    if profile.name == profile_name:
                        display_name = profile.display_name
                        break
                
                # 记录日志
                self.status_monitor.add_log(f"🔴 检测到浏览器被外部关闭: {display_name}")
                
                # 更新状态栏
                self.status_message.setText(f"浏览器已关闭: {display_name}")
                
                # 更新对应的列表项状态
                self.update_profile_item_status(profile_name, False)
        
        # 检查是否有新的外部浏览器启动（每隔一段时间检查一次）
        if not hasattr(self, '_last_external_check') or (time.time() - self._last_external_check) > 5:  # 缩短检查间隔到5秒
            self._last_external_check = time.time()
            # 发现新的外部浏览器
            if hasattr(self.profile_manager, 'profiles'):
                external_browsers = self.browser_manager.discover_external_browsers(self.profile_manager.profiles)
                if external_browsers:
                    need_update_ui = True
                    for profile_name in external_browsers:
                        # 查找对应的Profile显示名称
                        display_name = profile_name
                        for profile in self.profile_manager.profiles:
                            if profile.name == profile_name:
                                display_name = profile.display_name
                                break
                        
                        self.status_monitor.add_log(f"📡 检测到外部启动的浏览器: {display_name}")
        
        # 如果检测到状态变化，更新界面
        if need_update_ui:
            # 刷新Profile列表显示状态
            self.load_profiles()
            
            # 立即更新状态监控
            self.update_status()
        else:
            # 即使没有重大变化，也定期更新运行状态（内存使用等）
            self.update_running_profile_items()
    
    def update_profile_item_status(self, profile_name, is_running, browser_info=None):
        """更新特定Profile列表项的状态"""
        for i in range(self.profile_list.count()):
            item = self.profile_list.item(i)
            profile = item.data(Qt.UserRole)
            if profile and profile.name == profile_name:
                item_widget = self.profile_list.itemWidget(item)
                if isinstance(item_widget, ProfileItemWidget):
                    item_widget.update_status(is_running, browser_info)
                break
    
    def update_running_profile_items(self):
        """更新所有运行中Profile的状态信息（内存使用等）"""
        if hasattr(self.profile_manager, 'profiles'):
            running_browsers = self.browser_manager.get_all_running_browsers(self.profile_manager.profiles)
            
            for i in range(self.profile_list.count()):
                item = self.profile_list.item(i)
                profile = item.data(Qt.UserRole)
                if profile:
                    item_widget = self.profile_list.itemWidget(item)
                    if isinstance(item_widget, ProfileItemWidget):
                        is_running = profile.name in running_browsers
                        browser_info = running_browsers.get(profile.name) if is_running else None
                        
                        # 只有状态发生变化时才更新
                        if item_widget.is_running != is_running:
                            item_widget.update_status(is_running, browser_info)
                        elif is_running and browser_info:
                            # 更新运行时信息（内存使用等）
                            item_widget.update_status(is_running, browser_info)
    
    def show_about(self):
        """显示关于对话框"""
        QMessageBox.about(self, "关于", 
                         "多开浏览器管理工具 v1.0\n\n"
                         "基于Python和PyQt5开发的Chrome浏览器Profile管理工具\n"
                         "支持多个浏览器实例的独立管理和配置")
    
    def closeEvent(self, event):
        """程序关闭时的处理"""
        # 停止定时器
        if hasattr(self, 'timer'):
            self.timer.stop()
        if hasattr(self, 'status_check_timer'):
            self.status_check_timer.stop()
        
        reply = QMessageBox.question(self, "确认退出", "退出前是否关闭所有运行中的浏览器？",
                                   QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                                   QMessageBox.Yes)
        
        if reply == QMessageBox.Yes:
            self.browser_manager.close_all_browsers()
            event.accept()
        elif reply == QMessageBox.No:
            event.accept()
        else:
            # 如果取消退出，重新启动定时器
            if hasattr(self, 'timer'):
                self.timer.start(1000)
            if hasattr(self, 'status_check_timer'):
                self.status_check_timer.start(500)
            event.ignore()

    def start_browser_from_profile(self, profile):
        """从Profile对象启动浏览器"""
        # 设置当前Profile以便获取配置
        self.profile_info.current_profile = profile
        self.profile_info.update_profile_info(profile)
        
        # 调用原有的启动方法
        self.start_browser()
    
    def close_browser_from_profile(self, profile):
        """从Profile对象关闭浏览器"""
        # 检查浏览器是否在运行
        if not self.browser_manager.is_browser_running(profile.name):
            # 清除按钮的过渡状态
            self.clear_profile_transition_state(profile.name)
            QMessageBox.information(self, "提示", f"浏览器未在运行\n\nProfile: {profile.display_name}")
            return
        
        self.status_message.setText(f"正在关闭浏览器: {profile.display_name}...")
        success = self.browser_manager.close_browser(profile.name)
        
        if success:
            self.status_monitor.add_log(f"✅ 成功关闭浏览器: {profile.display_name}")
            self.status_message.setText(f"已关闭: {profile.display_name}")
            # 立即刷新列表
            self.load_profiles()
        else:
            # 操作失败，清除过渡状态
            self.clear_profile_transition_state(profile.name)
            self.status_monitor.add_log(f"❌ 关闭浏览器失败: {profile.display_name}")
            QMessageBox.warning(self, "警告", f"关闭浏览器失败: {profile.display_name}")
    
    def clear_profile_transition_state(self, profile_name):
        """清除特定Profile的过渡状态"""
        for i in range(self.profile_list.count()):
            item = self.profile_list.item(i)
            profile = item.data(Qt.UserRole)
            if profile and profile.name == profile_name:
                item_widget = self.profile_list.itemWidget(item)
                if isinstance(item_widget, ProfileItemWidget):
                    item_widget.clear_transition_state()
                break
    
    def close_all_browsers(self):
        """关闭所有浏览器"""
        reply = QMessageBox.question(self, "确认", "确定要关闭所有运行中的浏览器吗？",
                                   QMessageBox.Yes | QMessageBox.No,
                                   QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            success = self.browser_manager.close_all_browsers()
            if success:
                self.status_monitor.add_log("关闭所有浏览器")
                self.status_message.setText("已关闭所有浏览器")
            else:
                QMessageBox.warning(self, "警告", "部分浏览器关闭失败")
    
    def new_profile(self):
        """新建Profile"""
        dialog = ProfileEditDialog(self, None, self.profile_manager)
        if dialog.exec_() == QDialog.Accepted:
            # 重新扫描Profile（强制刷新）
            self.profile_manager.scan_profiles()
            # 重新加载Profile列表
            self.load_profiles()
            self.status_monitor.add_log("📋 Profile列表已刷新（新建Profile）")
    
    def edit_profile(self):
        """编辑Profile"""
        # 获取当前选中的Profile
        selected_items = self.profile_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "警告", "请先选择一个Profile")
            return
        
        profile = selected_items[0].data(Qt.UserRole)
        if not profile:
            return
        
        # 检查是否是外部检测的Profile
        if hasattr(profile, 'path') and "外部检测" in profile.path:
            QMessageBox.information(self, "提示", "外部检测的Profile无法编辑")
            return
        
        dialog = ProfileEditDialog(self, profile, self.profile_manager)
        if dialog.exec_() == QDialog.Accepted:
            # 重新加载Profile列表
            self.load_profiles()
            self.status_monitor.add_log(f"📋 Profile已更新: {profile.display_name}")
    
    def close_all_browsers(self):
        """关闭所有浏览器"""
        reply = QMessageBox.question(self, "确认", "确定要关闭所有运行中的浏览器吗？",
                                   QMessageBox.Yes | QMessageBox.No,
                                   QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            success = self.browser_manager.close_all_browsers()
            if success:
                self.status_monitor.add_log("关闭所有浏览器")
                self.status_message.setText("已关闭所有浏览器")
            else:
                QMessageBox.warning(self, "警告", "部分浏览器关闭失败")
    
    def update_running_profile_items(self):
        """更新所有运行中Profile的状态信息（内存使用等）"""
        if hasattr(self.profile_manager, 'profiles'):
            running_browsers = self.browser_manager.get_all_running_browsers(self.profile_manager.profiles)
            
            for i in range(self.profile_list.count()):
                item = self.profile_list.item(i)
                profile = item.data(Qt.UserRole)
                if profile:
                    item_widget = self.profile_list.itemWidget(item)
                    if isinstance(item_widget, ProfileItemWidget):
                        is_running = profile.name in running_browsers
                        browser_info = running_browsers.get(profile.name) if is_running else None
                        
                        # 只有状态发生变化时才更新
                        if item_widget.is_running != is_running:
                            item_widget.update_status(is_running, browser_info)
                        elif is_running and browser_info:
                            # 更新运行时信息（内存使用等）
                            item_widget.update_status(is_running, browser_info) 
    
    def batch_delete_profiles(self):
        """批量删除Profile"""
        # 获取所有非默认Profile
        profiles = self.profile_manager.scan_profiles()
        deletable_profiles = [p for p in profiles if p.name != "Default" and not ("外部检测" in p.path)]
        
        if not deletable_profiles:
            QMessageBox.information(self, "提示", "没有可删除的Profile")
            return
        
        # 创建选择对话框
        dialog = QDialog(self)
        dialog.setWindowTitle("批量删除Profile")
        dialog.setFixedSize(600, 500)
        
        layout = QVBoxLayout()
        
        # 警告
        warning_label = QLabel("⚠️ 危险操作：批量删除Profile")
        warning_label.setStyleSheet("""
            QLabel {
                background-color: #f8d7da;
                color: #721c24;
                padding: 10px;
                border: 1px solid #f5c6cb;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }
        """)
        layout.addWidget(warning_label)
        
        # 说明
        info_label = QLabel("请选择要删除的Profile（默认Profile和外部检测的Profile不能删除）：")
        layout.addWidget(info_label)
        
        # Profile列表
        self.profile_checkboxes = []
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout()
        
        for profile in deletable_profiles:
            checkbox = QCheckBox(f"{profile.display_name} ({profile.name})")
            
            # 添加Profile信息
            from core.profile_manager import ProfileManager
            pm = ProfileManager()
            size_str = pm.format_size(profile.storage_size)
            info_text = f"  📁 {size_str} | 📚 {profile.bookmarks_count} 书签 | 🔌 {profile.extensions_count} 扩展"
            
            profile_widget = QWidget()
            profile_layout = QVBoxLayout()
            profile_layout.setContentsMargins(0, 5, 0, 5)
            profile_layout.addWidget(checkbox)
            
            info_label = QLabel(info_text)
            info_label.setStyleSheet("color: #666; font-size: 11px; margin-left: 20px;")
            profile_layout.addWidget(info_label)
            
            profile_widget.setLayout(profile_layout)
            scroll_layout.addWidget(profile_widget)
            
            self.profile_checkboxes.append((checkbox, profile))
        
        scroll_widget.setLayout(scroll_layout)
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)
        
        # 全选/取消全选
        select_layout = QHBoxLayout()
        select_all_btn = QPushButton("全选")
        select_none_btn = QPushButton("取消全选")
        
        def select_all():
            for checkbox, _ in self.profile_checkboxes:
                checkbox.setChecked(True)
        
        def select_none():
            for checkbox, _ in self.profile_checkboxes:
                checkbox.setChecked(False)
        
        select_all_btn.clicked.connect(select_all)
        select_none_btn.clicked.connect(select_none)
        
        select_layout.addWidget(select_all_btn)
        select_layout.addWidget(select_none_btn)
        select_layout.addStretch()
        layout.addLayout(select_layout)
        
        # 按钮
        button_layout = QHBoxLayout()
        cancel_btn = QPushButton("取消")
        delete_btn = QPushButton("🗑️ 删除选中的Profile")
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        
        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(delete_btn)
        layout.addLayout(button_layout)
        
        dialog.setLayout(layout)
        
        def perform_batch_delete():
            selected_profiles = [profile for checkbox, profile in self.profile_checkboxes if checkbox.isChecked()]
            
            if not selected_profiles:
                QMessageBox.warning(dialog, "提示", "请选择要删除的Profile")
                return
            
            # 最终确认
            profile_names = [p.display_name for p in selected_profiles]
            reply = QMessageBox.question(
                dialog, "最终确认",
                f"确定要删除以下 {len(selected_profiles)} 个Profile吗？\n\n" +
                "\n".join(f"• {name}" for name in profile_names) +
                "\n\n⚠️ 此操作无法撤销！",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                success_count = 0
                failed_profiles = []
                
                for profile in selected_profiles:
                    try:
                        if self.profile_manager.delete_profile(profile.name):
                            success_count += 1
                        else:
                            failed_profiles.append(profile.display_name)
                    except Exception as e:
                        failed_profiles.append(f"{profile.display_name} ({str(e)})")
                
                # 显示结果
                if failed_profiles:
                    msg = f"批量删除完成\n\n成功删除: {success_count} 个\n失败: {len(failed_profiles)} 个\n\n失败的Profile:\n"
                    msg += "\n".join(f"• {name}" for name in failed_profiles)
                    QMessageBox.warning(dialog, "部分成功", msg)
                else:
                    QMessageBox.information(dialog, "成功", f"成功删除 {success_count} 个Profile")
                
                dialog.accept()
                self.load_profiles()  # 刷新列表
        
        cancel_btn.clicked.connect(dialog.reject)
        delete_btn.clicked.connect(perform_batch_delete)
        
        dialog.exec_()
    
    def cleanup_invalid_profiles(self):
        """清理无效Profile"""
        reply = QMessageBox.question(
            self, "清理无效Profile",
            "此功能将检查并清理以下无效的Profile:\n\n"
            "• Local State中存在但目录不存在的Profile\n"
            "• 损坏的Profile目录\n"
            "• 空的Profile目录\n\n"
            "是否继续？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # 这里可以添加清理逻辑
                QMessageBox.information(self, "功能开发中", "清理功能正在开发中，敬请期待！")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"清理失败: {str(e)}")
    
    def export_profiles_list(self):
        """导出Profile列表"""
        try:
            import json
            from PyQt5.QtWidgets import QFileDialog
            
            # 选择保存位置
            file_path, _ = QFileDialog.getSaveFileName(
                self, "导出Profile列表", 
                "profile_list.json", 
                "JSON文件 (*.json);;所有文件 (*)"
            )
            
            if file_path:
                profiles_data = []
                for profile in self.profile_manager.profiles:
                    profile_data = {
                        'name': profile.name,
                        'display_name': profile.display_name,
                        'path': profile.path,
                        'is_default': profile.is_default,
                        'created_time': profile.created_time.isoformat() if profile.created_time else None,
                        'last_used_time': profile.last_used_time.isoformat() if profile.last_used_time else None,
                        'bookmarks_count': profile.bookmarks_count,
                        'extensions_count': profile.extensions_count,
                        'storage_size': profile.storage_size
                    }
                    profiles_data.append(profile_data)
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump({
                        'export_time': datetime.now().isoformat(),
                        'profiles': profiles_data
                    }, f, indent=2, ensure_ascii=False)
                
                QMessageBox.information(self, "成功", f"Profile列表已导出到:\n{file_path}")
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出失败: {str(e)}")
    
    def import_bookmarks_to_profile(self):
        """导入书签到Profile"""
        QMessageBox.information(self, "功能开发中", "书签导入功能正在开发中，敬请期待！")
    
    def sort_profiles(self, sort_by):
        """排序Profile"""
        profiles = []
        for i in range(self.profile_list.count()):
            item = self.profile_list.item(i)
            profile = item.data(Qt.UserRole)
            if profile:
                profiles.append(profile)
        
        if sort_by == 'name':
            profiles.sort(key=lambda p: p.display_name.lower())
        elif sort_by == 'size':
            profiles.sort(key=lambda p: p.storage_size, reverse=True)
        elif sort_by == 'date':
            profiles.sort(key=lambda p: p.created_time or datetime.min, reverse=True)
        
        # 重新排列列表
        self.profile_list.clear()
        running_browsers = self.browser_manager.get_running_browsers()
        
        for profile in profiles:
            is_running = any(browser.profile_name == profile.name for browser in running_browsers)
            browser_info = next((browser for browser in running_browsers if browser.profile_name == profile.name), None)
            
            item_widget = ProfileItemWidget(profile, is_running, browser_info)
            item_widget.startRequested.connect(self.start_browser_from_profile)
            item_widget.closeRequested.connect(self.close_browser_from_profile)
            
            item = QListWidgetItem()
            item.setData(Qt.UserRole, profile)
            item.setSizeHint(item_widget.sizeHint())
            
            self.profile_list.addItem(item)
            self.profile_list.setItemWidget(item, item_widget)
        
        sort_names = {'name': '名称', 'size': '大小', 'date': '日期'}
        self.status_monitor.add_log(f"📋 Profile已按{sort_names[sort_by]}排序")
    
    def open_chrome_data_directory(self):
        """打开Chrome数据目录"""
        import subprocess
        import platform
        
        if self.profile_manager.chrome_paths:
            chrome_path = self.profile_manager.chrome_paths[0]
            try:
                if platform.system() == "Darwin":  # macOS
                    subprocess.run(["open", chrome_path])
                elif platform.system() == "Windows":
                    subprocess.run(["explorer", chrome_path])
                else:  # Linux
                    subprocess.run(["xdg-open", chrome_path])
                
                self.status_monitor.add_log(f"📁 已打开Chrome数据目录: {chrome_path}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"无法打开目录: {str(e)}")
        else:
            QMessageBox.warning(self, "警告", "未找到Chrome数据目录")
    
    def show_system_info(self):
        """显示系统信息"""
        import platform
        import psutil
        
        dialog = QDialog(self)
        dialog.setWindowTitle("系统信息")
        dialog.setFixedSize(500, 400)
        
        layout = QVBoxLayout()
        
        info_text = f"""
🖥️ 系统信息
─────────────────────────
操作系统: {platform.system()} {platform.release()}
架构: {platform.machine()}
Python版本: {platform.python_version()}

💾 内存信息
─────────────────────────
总内存: {psutil.virtual_memory().total // (1024**3)} GB
可用内存: {psutil.virtual_memory().available // (1024**3)} GB
内存使用率: {psutil.virtual_memory().percent}%

📁 Chrome路径
─────────────────────────
"""
        
        for i, path in enumerate(self.profile_manager.chrome_paths, 1):
            info_text += f"路径 {i}: {path}\n"
        
        if not self.profile_manager.chrome_paths:
            info_text += "未找到Chrome安装路径\n"
        
        info_text += f"""
📊 Profile统计
─────────────────────────
总Profile数量: {len(self.profile_manager.profiles)}
运行中的浏览器: {len(self.browser_manager.get_all_running_browsers())}
"""
        
        text_edit = QTextEdit()
        text_edit.setPlainText(info_text)
        text_edit.setReadOnly(True)
        text_edit.setStyleSheet("""
            QTextEdit {
                font-family: 'Courier New', monospace;
                font-size: 12px;
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 10px;
            }
        """)
        
        layout.addWidget(text_edit)
        
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.setLayout(layout)
        dialog.exec_()
    
    def show_preferences(self):
        """显示偏好设置"""
        QMessageBox.information(self, "功能开发中", "偏好设置功能正在开发中，敬请期待！")
    
    def show_shortcuts(self):
        """显示快捷键"""
        dialog = QDialog(self)
        dialog.setWindowTitle("快捷键")
        dialog.setFixedSize(500, 400)
        
        layout = QVBoxLayout()
        
        shortcuts_text = """
⌨️ 快捷键列表
─────────────────────────

🔧 Profile管理
Ctrl+N          新建Profile
Ctrl+E          编辑Profile
F5              刷新Profile列表

🌐 浏览器操作
Ctrl+Shift+Q    关闭所有浏览器
双击Profile      启动浏览器

🔧 应用程序
Ctrl+Q          退出程序
Ctrl+,          偏好设置
F1              显示快捷键

💡 提示
───────────────────────── 
• 可以拖拽Profile来调整排序
• 右键点击Profile查看更多选项
• 选中Profile后点击编辑按钮可修改或删除
"""
        
        text_edit = QTextEdit()
        text_edit.setPlainText(shortcuts_text)
        text_edit.setReadOnly(True)
        text_edit.setStyleSheet("""
            QTextEdit {
                font-family: 'Courier New', monospace;
                font-size: 12px;
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 10px;
            }
        """)
        
        layout.addWidget(text_edit)
        
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.setLayout(layout)
        dialog.exec_()
    
    def show_about(self):
        """显示关于"""
        QMessageBox.about(self, "关于", 
                         "🔥 多开浏览器管理工具\n\n"
                         "版本: 2.0\n"
                         "作者: Assistant\n\n"
                         "功能特点:\n"
                         "• 管理Chrome Profile\n"
                         "• 多浏览器实例启动\n"
                         "• 实时状态监控\n"
                         "• 拖拽排序\n"
                         "• 批量操作\n\n"
                         "感谢使用！")

    def delete_selected_profile(self):
        """删除选中的Profile"""
        # 获取当前选中的Profile
        selected_items = self.profile_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "警告", "请先选择一个Profile")
            return
        
        profile = selected_items[0].data(Qt.UserRole)
        if not profile:
            return
        
        # 检查是否是默认Profile
        if profile.name == "Default":
            QMessageBox.warning(
                self, "无法删除",
                "⚠️ 无法删除默认Profile\n\n"
                "默认Profile是Chrome的核心Profile，删除可能导致Chrome无法正常工作。"
            )
            return
        
        # 检查是否是外部检测的Profile
        if hasattr(profile, 'path') and "外部检测" in profile.path:
            QMessageBox.information(self, "提示", "外部检测的Profile无法删除")
            return
        
        # 检查Chrome是否正在运行
        if self.browser_manager.is_browser_running(profile.name):
            reply = QMessageBox.question(
                self, "Chrome正在运行",
                "⚠️ 检测到此Profile的Chrome浏览器正在运行！\n\n"
                "为了安全起见，建议您先关闭浏览器，\n"
                "然后再删除Profile。\n\n"
                "是否继续删除？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.No:
                return
        
        # 创建详细的删除确认对话框
        dialog = QDialog(self)
        dialog.setWindowTitle("确认删除Profile")
        dialog.setFixedSize(500, 450)
        dialog.setModal(True)
        
        layout = QVBoxLayout()
        
        # 警告标题
        warning_widget = QWidget()
        warning_layout = QHBoxLayout()
        warning_layout.setContentsMargins(10, 10, 10, 10)
        
        warning_icon = QLabel("⚠️")
        warning_icon.setStyleSheet("font-size: 32px;")
        warning_icon.setFixedSize(40, 40)
        warning_icon.setAlignment(Qt.AlignCenter)
        
        warning_title = QLabel("危险操作：删除Profile")
        warning_title.setFont(QFont("", 14, QFont.Bold))
        warning_title.setStyleSheet("color: #dc3545;")
        
        warning_layout.addWidget(warning_icon)
        warning_layout.addWidget(warning_title)
        warning_layout.addStretch()
        
        warning_widget.setLayout(warning_layout)
        warning_widget.setStyleSheet("""
            QWidget {
                background-color: #f8d7da;
                border: 1px solid #f5c6cb;
                border-radius: 6px;
                margin-bottom: 15px;
            }
        """)
        
        layout.addWidget(warning_widget)
        
        # Profile信息
        info_label = QLabel(f"您即将删除Profile: <b>{profile.display_name}</b>")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # 详细信息
        details_group = QGroupBox("将要删除的数据")
        details_layout = QVBoxLayout()
        
        # 计算要删除的数据
        from core.profile_manager import ProfileManager
        pm = ProfileManager()
        size_str = pm.format_size(profile.storage_size)
        
        delete_items = [
            f"📁 整个Profile目录 ({size_str})",
            f"📚 所有书签 ({profile.bookmarks_count} 个)",
            f"🔌 所有扩展程序 ({profile.extensions_count} 个)",
            "🔒 所有已保存的登录信息和密码",
            "🕒 完整的浏览历史记录",
            "🍪 所有Cookie和网站数据",
            "📥 下载历史记录",
            "⚙️ 所有个人设置和偏好",
            "📝 自动填充数据",
            "🔐 已保存的信用卡信息",
            "📱 同步数据（如果已启用）",
            "🎨 主题和自定义设置"
        ]
        
        for item in delete_items:
            item_label = QLabel(f"• {item}")
            item_label.setStyleSheet("margin: 2px 0; color: #495057;")
            details_layout.addWidget(item_label)
        
        details_group.setLayout(details_layout)
        layout.addWidget(details_group)
        
        # 最终警告
        final_warning = QLabel(
            "🚨 <b>此操作无法撤销！</b><br>"
            "🔥 所有数据将被永久删除<br>"
            "📱 如果此Profile已与Google账号同步，本地删除不会影响云端数据"
        )
        final_warning.setWordWrap(True)
        final_warning.setStyleSheet("""
            QLabel {
                background-color: #fff3cd;
                border: 1px solid #ffeaa7;
                border-radius: 4px;
                padding: 10px;
                margin: 10px 0;
                color: #856404;
            }
        """)
        layout.addWidget(final_warning)
        
        # 确认输入
        confirm_layout = QHBoxLayout()
        confirm_label = QLabel("请输入Profile名称以确认删除:")
        self.confirm_input = QLineEdit()
        self.confirm_input.setPlaceholderText(f"输入: {profile.display_name}")
        
        confirm_layout.addWidget(confirm_label)
        confirm_layout.addWidget(self.confirm_input)
        layout.addLayout(confirm_layout)
        
        # 按钮
        button_layout = QHBoxLayout()
        
        cancel_btn = QPushButton("取消")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 8px 20px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        
        delete_btn = QPushButton("🗑️ 确认删除")
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                padding: 8px 20px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        delete_btn.setEnabled(False)
        
        # 验证输入
        def validate_confirm_input():
            if self.confirm_input.text().strip() == profile.display_name:
                delete_btn.setEnabled(True)
            else:
                delete_btn.setEnabled(False)
        
        self.confirm_input.textChanged.connect(validate_confirm_input)
        
        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(delete_btn)
        
        layout.addLayout(button_layout)
        dialog.setLayout(layout)
        
        # 连接按钮事件
        cancel_btn.clicked.connect(dialog.reject)
        
        def perform_delete():
            try:
                success = self.profile_manager.delete_profile(profile.name)
                if success:
                    QMessageBox.information(
                        self, "删除成功", 
                        f"✅ Profile '{profile.display_name}' 已成功删除\n\n"
                        "建议重启Chrome以确保完全生效。"
                    )
                    dialog.accept()
                    # 重新加载Profile列表
                    self.load_profiles()
                else:
                    QMessageBox.critical(self, "删除失败", "❌ 删除Profile失败，请检查权限或重试")
            except Exception as e:
                QMessageBox.critical(self, "删除错误", f"❌ 删除失败: {str(e)}")
        
        delete_btn.clicked.connect(perform_delete)
        
        # 显示对话框
        dialog.exec_()

    def load_profiles(self):
        """加载Profile列表"""
        print("开始加载Profile...")
        self.status_message.setText("正在扫描Profile...")
        
        try:
            profiles = self.profile_manager.scan_profiles()
            print(f"扫描到{len(profiles)}个Profile")
            
            # 应用保存的排序
            print("应用保存的排序...")
            profiles = self.sort_profiles_by_saved_order(profiles)
            
            # 获取当前运行中的浏览器实例（包括外部启动的）
            print("检查运行中的浏览器...")
            running_browsers = self.browser_manager.get_all_running_browsers(profiles)
            print(f"检测到{len(running_browsers)}个运行中的浏览器")
            
            # 创建Profile名称到Profile对象的映射
            profile_map = {profile.name: profile for profile in profiles}
            
            self.profile_list.clear()
            
            # 先处理已知的Profile
            print("处理已知Profile...")
            for i, profile in enumerate(profiles):
                print(f"处理Profile {i+1}/{len(profiles)}: {profile.display_name}")
                
                # 检查运行状态
                is_running = profile.name in running_browsers
                browser_info = running_browsers.get(profile.name) if is_running else None
                
                # 创建ProfileItemWidget
                item_widget = ProfileItemWidget(profile, is_running, browser_info)
                
                # 连接信号
                item_widget.startRequested.connect(self.start_browser_from_profile)
                item_widget.closeRequested.connect(self.close_browser_from_profile)
                
                # 创建列表项
                item = QListWidgetItem()
                item.setData(Qt.UserRole, profile)
                
                # 设置项目大小
                item.setSizeHint(item_widget.sizeHint())
                
                # 添加到列表
                self.profile_list.addItem(item)
                self.profile_list.setItemWidget(item, item_widget)
            
            # 处理外部发现的但不在已知Profile列表中的浏览器
            print("处理外部发现的浏览器...")
            discovered_profiles = 0
            for browser_name, browser_info in running_browsers.items():
                if browser_info.get('discovered') and browser_name not in profile_map:
                    discovered_profiles += 1
                    print(f"发现外部浏览器: {browser_name}")
                    
                    # 创建一个虚拟的Profile对象
                    class VirtualProfile:
                        def __init__(self, name):
                            self.name = name
                            self.display_name = f"{name} (外部检测)"
                            self.path = f"外部检测的{name}Profile"
                            self.bookmarks_count = 0
                            self.extensions_count = 0
                            self.storage_size = 0
                            self.created_time = None
                            self.last_used_time = None
                            self.is_default = (name == "Default")
                    
                    virtual_profile = VirtualProfile(browser_name)
                    
                    # 创建ProfileItemWidget
                    item_widget = ProfileItemWidget(virtual_profile, True, browser_info)
                    
                    # 连接信号
                    item_widget.startRequested.connect(self.start_browser_from_profile)
                    item_widget.closeRequested.connect(self.close_browser_from_profile)
                    
                    # 创建列表项
                    item = QListWidgetItem()
                    item.setData(Qt.UserRole, virtual_profile)
                    
                    # 设置项目大小
                    item.setSizeHint(item_widget.sizeHint())
                    
                    # 添加到列表
                    self.profile_list.addItem(item)
                    self.profile_list.setItemWidget(item, item_widget)
            
            total_profiles = len(profiles) + discovered_profiles
            self.status_message.setText(f"找到 {total_profiles} 个Profile")
            self.status_monitor.add_log(f"📊 扫描完成，找到 {len(profiles)} 个Profile，检测到 {len(running_browsers)} 个运行中的浏览器")
            print("Profile加载完成")
            
        except Exception as e:
            print(f"加载Profile出错: {e}")
            import traceback
            traceback.print_exc()
            self.status_message.setText("加载Profile失败")