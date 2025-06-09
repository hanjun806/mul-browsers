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
                            QFrame, QSizePolicy, QTreeWidget, QTreeWidgetItem)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QSize, QTime
from PyQt5.QtGui import QIcon, QFont, QPalette, QColor, QPixmap

# 导入核心模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.profile_manager import ProfileManager, ProfileInfo
from core.browser_manager import BrowserManager
from core.config_manager import ConfigManager, ProfileConfig
from gui.icon_helper import get_application_icon

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
                background: transparent;
            }
            QListWidget::item:hover {
                background: transparent;
            }
        """)
    
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
        self.profile_manager = ProfileManager()
        self.browser_manager = BrowserManager()
        self.config_manager = ConfigManager()
        
        # 初始化外部检查时间戳
        self._last_external_check = 0
        
        # 设置窗口图标
        self.setWindowIcon(get_application_icon())
        
        self.setup_ui()
        self.setup_timer()
        self.load_profiles()
        
        # 在日志中提示用户可以拖拽排序
        self.status_monitor.add_log("💡 提示：可以拖拽Profile来调整排序，排序会自动保存")
    
    def setup_ui(self):
        """设置用户界面"""
        self.setWindowTitle("多开浏览器管理工具")
        self.setGeometry(100, 100, 1200, 800)
        
        # 设置窗口图标（再次确保设置成功）
        self.setWindowIcon(get_application_icon())
        
        # 创建中央控件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主要布局
        main_layout = QHBoxLayout()
        
        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        
        # 左侧Profile列表
        self.profile_list = ProfileListWidget()
        self.profile_list.itemClicked.connect(self.on_profile_selected)
        self.profile_list.itemDoubleClicked.connect(self.on_profile_double_clicked)
        self.profile_list.orderChanged.connect(self.on_profile_order_changed)
        
        # 中间详细信息
        self.profile_info = ProfileInfoWidget()
        
        # 右侧状态监控
        self.status_monitor = StatusMonitorWidget()
        
        # 添加到分割器
        splitter.addWidget(self.profile_list)
        splitter.addWidget(self.profile_info)
        splitter.addWidget(self.status_monitor)
        
        # 设置分割器比例
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        splitter.setStretchFactor(2, 1)
        
        main_layout.addWidget(splitter)
        central_widget.setLayout(main_layout)
        
        # 创建菜单栏
        self.create_menu_bar()
        
        # 创建状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # 创建状态栏的各个部分
        self.status_message = QLabel("就绪")
        self.total_profiles_label = QLabel("总Profile: 0")
        self.running_profiles_label = QLabel("运行中: 0")
        self.total_memory_label = QLabel("内存: 0 MB")
        
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
        
        # 添加到状态栏
        self.status_bar.addWidget(self.status_message, 1)  # 拉伸因子为1，占据剩余空间
        self.status_bar.addPermanentWidget(self.total_profiles_label)
        self.status_bar.addPermanentWidget(self.running_profiles_label)
        self.status_bar.addPermanentWidget(self.total_memory_label)
    
    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu('文件')
        
        refresh_action = QAction('刷新Profile列表', self)
        refresh_action.setShortcut('F5')
        refresh_action.triggered.connect(self.load_profiles)
        file_menu.addAction(refresh_action)
        
        reset_order_action = QAction('重置Profile排序', self)
        reset_order_action.triggered.connect(self.reset_profile_order)
        file_menu.addAction(reset_order_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('退出', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 浏览器菜单
        browser_menu = menubar.addMenu('浏览器')
        
        close_all_action = QAction('关闭所有浏览器', self)
        close_all_action.triggered.connect(self.close_all_browsers)
        browser_menu.addAction(close_all_action)
        
        # 帮助菜单
        help_menu = menubar.addMenu('帮助')
        
        about_action = QAction('关于', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def setup_timer(self):
        """设置定时器，用于更新状态"""
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_status)
        self.timer.start(1000)  # 每1秒更新一次（提高频率）
        
        # 添加一个更频繁的定时器来检测浏览器状态变化
        self.status_check_timer = QTimer()
        self.status_check_timer.timeout.connect(self.check_browser_status)
        self.status_check_timer.start(500)  # 每0.5秒检查一次浏览器状态（大幅提高频率）
    
    def load_profiles(self):
        """加载Profile列表"""
        self.status_message.setText("正在扫描Profile...")
        profiles = self.profile_manager.scan_profiles()
        
        # 应用保存的排序
        profiles = self.sort_profiles_by_saved_order(profiles)
        
        # 获取当前运行中的浏览器实例（包括外部启动的）
        running_browsers = self.browser_manager.get_all_running_browsers(profiles)
        
        # 创建Profile名称到Profile对象的映射
        profile_map = {profile.name: profile for profile in profiles}
        
        self.profile_list.clear()
        
        # 先处理已知的Profile
        for profile in profiles:
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
        
        # 处理外部发现的但不在已知Profile列表中的浏览器（如Default Profile）
        for browser_name, browser_info in running_browsers.items():
            if browser_info.get('discovered') and browser_name not in profile_map:
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
        
        total_profiles = len(profiles) + len([b for b in running_browsers.values() if b.get('discovered') and b not in profile_map])
        self.status_message.setText(f"找到 {total_profiles} 个Profile")
        self.status_monitor.add_log(f"📊 扫描完成，找到 {len(profiles)} 个Profile，检测到 {len(running_browsers)} 个运行中的浏览器")
    
    def on_profile_selected(self, item):
        """Profile被选中时的处理"""
        profile = item.data(Qt.UserRole)
        if profile:
            self.profile_info.update_profile_info(profile)
    
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