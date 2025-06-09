#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主GUI窗口
实现多开浏览器管理工具的用户界面
"""

import sys
import os
from PyQt5.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
                            QSplitter, QListWidget, QListWidgetItem, QLabel, 
                            QPushButton, QGroupBox, QGridLayout, QTextEdit,
                            QComboBox, QSpinBox, QLineEdit, QCheckBox, 
                            QProgressBar, QStatusBar, QMenuBar, QAction,
                            QMessageBox, QInputDialog, QTabWidget, QScrollArea,
                            QFrame, QSizePolicy, QTreeWidget, QTreeWidgetItem)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QSize
from PyQt5.QtGui import QIcon, QFont, QPalette, QColor, QPixmap

# 导入核心模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.profile_manager import ProfileManager, ProfileInfo
from core.browser_manager import BrowserManager
from gui.icon_helper import get_application_icon

class ProfileListWidget(QListWidget):
    """自定义Profile列表控件"""
    
    def __init__(self):
        super().__init__()
        self.setMinimumWidth(300)
        self.setMaximumWidth(400)
        
        # 设置样式
        self.setStyleSheet("""
            QListWidget {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 5px;
            }
            QListWidget::item {
                background-color: white;
                border: 1px solid #e9ecef;
                border-radius: 6px;
                padding: 10px;
                margin: 3px;
            }
            QListWidget::item:selected {
                background-color: #007bff;
                color: white;
            }
            QListWidget::item:hover {
                background-color: #e3f2fd;
            }
        """)

class ProfileInfoWidget(QWidget):
    """Profile详细信息控件"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.current_profile = None
    
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
        
        # 代理配置
        self.proxy_enabled = QCheckBox("启用代理")
        self.proxy_type_combo = QComboBox()
        self.proxy_type_combo.addItems(["http", "socks5", "socks4"])
        self.proxy_server_edit = QLineEdit()
        self.proxy_port_spin = QSpinBox()
        self.proxy_port_spin.setRange(1, 65535)
        self.proxy_port_spin.setValue(8080)
        
        # 窗口大小
        self.window_width_spin = QSpinBox()
        self.window_width_spin.setRange(800, 3840)
        self.window_width_spin.setValue(1280)
        
        self.window_height_spin = QSpinBox()
        self.window_height_spin.setRange(600, 2160)
        self.window_height_spin.setValue(720)
        
        config_layout.addWidget(QLabel("语言:"), 0, 0)
        config_layout.addWidget(self.language_combo, 0, 1)
        
        config_layout.addWidget(self.proxy_enabled, 1, 0, 1, 2)
        config_layout.addWidget(QLabel("代理类型:"), 2, 0)
        config_layout.addWidget(self.proxy_type_combo, 2, 1)
        config_layout.addWidget(QLabel("代理服务器:"), 3, 0)
        config_layout.addWidget(self.proxy_server_edit, 3, 1)
        config_layout.addWidget(QLabel("端口:"), 4, 0)
        config_layout.addWidget(self.proxy_port_spin, 4, 1)
        
        config_layout.addWidget(QLabel("窗口宽度:"), 5, 0)
        config_layout.addWidget(self.window_width_spin, 5, 1)
        config_layout.addWidget(QLabel("窗口高度:"), 6, 0)
        config_layout.addWidget(self.window_height_spin, 6, 1)
        
        config_group.setLayout(config_layout)
        
        # 操作按钮
        button_layout = QHBoxLayout()
        self.start_button = QPushButton("启动浏览器")
        self.close_button = QPushButton("关闭浏览器")
        self.restart_button = QPushButton("重启浏览器")
        
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        
        self.close_button.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        
        self.restart_button.setStyleSheet("""
            QPushButton {
                background-color: #ffc107;
                color: black;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e0a800;
            }
        """)
        
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.close_button)
        button_layout.addWidget(self.restart_button)
        
        layout.addWidget(info_group)
        layout.addWidget(config_group)
        layout.addLayout(button_layout)
        layout.addStretch()
        
        self.setLayout(layout)
    
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
        
        # 系统信息
        system_group = QGroupBox("系统信息")
        system_layout = QGridLayout()
        
        self.total_profiles_label = QLabel("0")
        self.running_profiles_label = QLabel("0")
        self.total_memory_label = QLabel("0 MB")
        
        system_layout.addWidget(QLabel("总Profile数:"), 0, 0)
        system_layout.addWidget(self.total_profiles_label, 0, 1)
        system_layout.addWidget(QLabel("运行中:"), 1, 0)
        system_layout.addWidget(self.running_profiles_label, 1, 1)
        system_layout.addWidget(QLabel("总内存使用:"), 2, 0)
        system_layout.addWidget(self.total_memory_label, 2, 1)
        
        system_group.setLayout(system_layout)
        
        # 操作日志
        log_group = QGroupBox("操作日志")
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(150)
        self.log_text.setReadOnly(True)
        log_group_layout = QVBoxLayout()
        log_group_layout.addWidget(self.log_text)
        log_group.setLayout(log_group_layout)
        
        layout.addWidget(status_group)
        layout.addWidget(system_group)
        layout.addWidget(log_group)
        
        self.setLayout(layout)
    
    def update_status(self, running_browsers: dict, total_profiles: int):
        """更新状态显示"""
        self.status_tree.clear()
        
        total_memory = 0
        for profile_name, browser_info in running_browsers.items():
            item = QTreeWidgetItem()
            item.setText(0, profile_name)
            item.setText(1, "运行中")
            item.setText(2, str(browser_info['pid']))
            
            memory_mb = browser_info['memory_usage'] / (1024 * 1024)
            item.setText(3, f"{memory_mb:.1f} MB")
            total_memory += memory_mb
            
            self.status_tree.addTopLevelItem(item)
        
        self.total_profiles_label.setText(str(total_profiles))
        self.running_profiles_label.setText(str(len(running_browsers)))
        self.total_memory_label.setText(f"{total_memory:.1f} MB")
    
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
        
        # 设置窗口图标
        self.setWindowIcon(get_application_icon())
        
        self.setup_ui()
        self.setup_timer()
        self.load_profiles()
    
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
        
        # 中间详细信息
        self.profile_info = ProfileInfoWidget()
        self.profile_info.start_button.clicked.connect(self.start_browser)
        self.profile_info.close_button.clicked.connect(self.close_browser)
        self.profile_info.restart_button.clicked.connect(self.restart_browser)
        
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
        self.status_bar.showMessage("就绪")
    
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
        self.timer.start(2000)  # 每2秒更新一次
    
    def load_profiles(self):
        """加载Profile列表"""
        self.status_bar.showMessage("正在扫描Profile...")
        profiles = self.profile_manager.scan_profiles()
        
        self.profile_list.clear()
        for profile in profiles:
            item = QListWidgetItem()
            
            # 检查运行状态
            is_running = self.browser_manager.is_browser_running(profile.name)
            status_indicator = "🟢 " if is_running else "⚪ "
            
            display_text = f"{status_indicator}{profile.display_name}"
            display_text += f"\n📁 路径: {profile.path}"
            display_text += f"\n📚 书签: {profile.bookmarks_count} | 🧩 扩展: {profile.extensions_count}"
            
            # 如果正在运行，添加运行信息
            if is_running:
                browser_info = self.browser_manager.get_browser_info(profile.name)
                if browser_info:
                    memory_mb = browser_info['memory_usage'] / (1024 * 1024)
                    display_text += f"\n💾 内存: {memory_mb:.1f}MB | 🆔 PID: {browser_info['pid']}"
            
            item.setText(display_text)
            item.setData(Qt.UserRole, profile)
            self.profile_list.addItem(item)
        
        self.status_bar.showMessage(f"找到 {len(profiles)} 个Profile")
        self.status_monitor.add_log(f"📊 扫描完成，找到 {len(profiles)} 个Profile")
    
    def on_profile_selected(self, item):
        """Profile被选中时的处理"""
        profile = item.data(Qt.UserRole)
        if profile:
            self.profile_info.update_profile_info(profile)
    
    def on_profile_double_clicked(self, item):
        """Profile被双击时启动浏览器"""
        self.start_browser()
    
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
        
        # 获取配置
        language = self.profile_info.language_combo.currentText()
        
        proxy_config = None
        if self.profile_info.proxy_enabled.isChecked():
            proxy_server = self.profile_info.proxy_server_edit.text().strip()
            if not proxy_server:
                QMessageBox.warning(self, "警告", "请输入代理服务器地址")
                return
                
            proxy_config = {
                'type': self.profile_info.proxy_type_combo.currentText(),
                'server': proxy_server,
                'port': self.profile_info.proxy_port_spin.value()
            }
        
        window_size = (
            self.profile_info.window_width_spin.value(),
            self.profile_info.window_height_spin.value()
        )
        
        # 显示启动状态
        self.status_bar.showMessage(f"正在启动浏览器: {profile.display_name}...")
        self.status_monitor.add_log(f"尝试启动浏览器: {profile.display_name}")
        
        # 启动浏览器
        success = self.browser_manager.start_browser(
            profile, 
            language=language,
            proxy_config=proxy_config,
            window_size=window_size
        )
        
        if success:
            self.status_monitor.add_log(f"✅ 成功启动浏览器: {profile.display_name}")
            self.status_bar.showMessage(f"已启动: {profile.display_name}")
            QMessageBox.information(self, "成功", f"浏览器已启动！\n\nProfile: {profile.display_name}\n语言: {language}")
        else:
            self.status_monitor.add_log(f"❌ 启动浏览器失败: {profile.display_name}")
            self.status_bar.showMessage(f"启动失败: {profile.display_name}")
            
            # 提供更详细的错误信息
            error_msg = f"启动浏览器失败！\n\nProfile: {profile.display_name}\n\n可能的原因：\n"
            error_msg += "• Profile正在被其他Chrome实例使用\n"
            error_msg += "• Chrome浏览器权限问题\n"
            error_msg += "• 代理设置错误\n\n"
            error_msg += "建议：\n• 关闭所有Chrome窗口后重试\n• 检查代理设置是否正确"
            
            QMessageBox.critical(self, "启动失败", error_msg)
    
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
        
        self.status_bar.showMessage(f"正在关闭浏览器: {profile.display_name}...")
        success = self.browser_manager.close_browser(profile.name)
        
        if success:
            self.status_monitor.add_log(f"✅ 成功关闭浏览器: {profile.display_name}")
            self.status_bar.showMessage(f"已关闭: {profile.display_name}")
        else:
            self.status_monitor.add_log(f"❌ 关闭浏览器失败: {profile.display_name}")
            QMessageBox.warning(self, "警告", f"关闭浏览器失败: {profile.display_name}")
    
    def restart_browser(self):
        """重启浏览器"""
        if not self.profile_info.current_profile:
            QMessageBox.warning(self, "警告", "请先选择一个Profile")
            return
        
        profile = self.profile_info.current_profile
        
        # 获取配置（与启动浏览器相同）
        language = self.profile_info.language_combo.currentText()
        
        proxy_config = None
        if self.profile_info.proxy_enabled.isChecked():
            proxy_config = {
                'type': self.profile_info.proxy_type_combo.currentText(),
                'server': self.profile_info.proxy_server_edit.text(),
                'port': self.profile_info.proxy_port_spin.value()
            }
        
        window_size = (
            self.profile_info.window_width_spin.value(),
            self.profile_info.window_height_spin.value()
        )
        
        success = self.browser_manager.restart_browser(
            profile,
            language=language,
            proxy_config=proxy_config,
            window_size=window_size
        )
        
        if success:
            self.status_monitor.add_log(f"重启浏览器: {profile.display_name}")
            self.status_bar.showMessage(f"已重启: {profile.display_name}")
        else:
            QMessageBox.critical(self, "错误", f"重启浏览器失败: {profile.display_name}")
    
    def close_all_browsers(self):
        """关闭所有浏览器"""
        reply = QMessageBox.question(self, "确认", "确定要关闭所有运行中的浏览器吗？",
                                   QMessageBox.Yes | QMessageBox.No,
                                   QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            success = self.browser_manager.close_all_browsers()
            if success:
                self.status_monitor.add_log("关闭所有浏览器")
                self.status_bar.showMessage("已关闭所有浏览器")
            else:
                QMessageBox.warning(self, "警告", "部分浏览器关闭失败")
    
    def update_status(self):
        """更新状态显示"""
        running_browsers = self.browser_manager.get_all_running_browsers()
        total_profiles = len(self.profile_manager.profiles)
        
        self.status_monitor.update_status(running_browsers, total_profiles)
    
    def show_about(self):
        """显示关于对话框"""
        QMessageBox.about(self, "关于", 
                         "多开浏览器管理工具 v1.0\n\n"
                         "基于Python和PyQt5开发的Chrome浏览器Profile管理工具\n"
                         "支持多个浏览器实例的独立管理和配置")
    
    def closeEvent(self, event):
        """程序关闭时的处理"""
        reply = QMessageBox.question(self, "确认退出", "退出前是否关闭所有运行中的浏览器？",
                                   QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                                   QMessageBox.Yes)
        
        if reply == QMessageBox.Yes:
            self.browser_manager.close_all_browsers()
            event.accept()
        elif reply == QMessageBox.No:
            event.accept()
        else:
            event.ignore() 