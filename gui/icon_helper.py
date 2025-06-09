#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图标辅助函数
用于创建和设置程序图标
"""

import os
from PyQt5.QtGui import QPixmap, QPainter, QIcon, QColor, QPen, QBrush
from PyQt5.QtCore import Qt, QRect

def create_default_icon(size: int = 64) -> QPixmap:
    """
    创建默认的程序图标
    
    Args:
        size: 图标尺寸
        
    Returns:
        QPixmap对象
    """
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    
    # 背景圆形
    background_color = QColor("#007bff")
    border_color = QColor("#0056b3")
    painter.setBrush(QBrush(background_color))
    painter.setPen(QPen(border_color, 2))
    painter.drawEllipse(2, 2, size-4, size-4)
    
    # 浏览器窗口
    window_color = QColor("#ffffff")
    painter.setBrush(QBrush(window_color))
    painter.setPen(QPen(QColor("#dee2e6"), 1))
    
    # 主窗口
    main_window = QRect(size//4, size//3, size//2, int(size//2.3))
    painter.drawRoundedRect(main_window, 3, 3)
    
    # 标题栏
    title_bar = QRect(size//4, size//3, size//2, size//10)
    painter.setBrush(QBrush(QColor("#f8f9fa")))
    painter.drawRoundedRect(title_bar, 3, 3)
    
    # 浏览器按钮
    button_y = size//3 + size//20
    button_size = max(1, size//32)
    
    # 红色按钮
    painter.setBrush(QBrush(QColor("#ff6b6b")))
    painter.setPen(Qt.NoPen)
    painter.drawEllipse(size//4 + size//16, button_y, button_size, button_size)
    
    # 黄色按钮
    painter.setBrush(QBrush(QColor("#feca57")))
    painter.drawEllipse(size//4 + size//12, button_y, button_size, button_size)
    
    # 蓝色按钮
    painter.setBrush(QBrush(QColor("#48dbfb")))
    painter.drawEllipse(size//4 + size//8, button_y, button_size, button_size)
    
    # 地址栏
    address_bar = QRect(size//4 + size//6, button_y - button_size//4, size//4, int(button_size*1.5))
    painter.setBrush(QBrush(QColor("#e9ecef")))
    painter.drawRoundedRect(address_bar, button_size//2, button_size//2)
    
    # 内容区域
    content_y = size//3 + size//6
    content_height = max(1, size//20)
    painter.setBrush(QBrush(QColor("#ced4da")))
    
    # 内容线条
    for i in range(3):
        line_width = max(1, int(size//2.5 - i * size//20))
        content_rect = QRect(size//4 + size//20, content_y + i * size//15, line_width, content_height//2)
        painter.drawRect(content_rect)
    
    painter.end()
    return pixmap

def get_application_icon() -> QIcon:
    """
    获取应用程序图标
    
    Returns:
        QIcon对象
    """
    # 尝试从assets目录加载图标
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    
    icon_paths = [
        os.path.join(project_root, "assets", "icons", "icon_64x64.png"),
        os.path.join(project_root, "assets", "icons", "icon_32x32.png"),
        os.path.join(project_root, "assets", "icon.png"),
    ]
    
    # 尝试加载现有图标文件
    for icon_path in icon_paths:
        if os.path.exists(icon_path):
            return QIcon(icon_path)
    
    # 如果没有找到图标文件，创建默认图标
    icon = QIcon()
    
    # 添加不同尺寸的图标
    for size in [16, 32, 48, 64, 128]:
        pixmap = create_default_icon(size)
        icon.addPixmap(pixmap)
    
    return icon

def save_default_icons():
    """保存默认图标到文件"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    
    # 创建assets目录
    assets_dir = os.path.join(project_root, "assets")
    icons_dir = os.path.join(assets_dir, "icons")
    os.makedirs(icons_dir, exist_ok=True)
    
    # 生成不同尺寸的图标
    sizes = [16, 32, 48, 64, 128, 256]
    
    for size in sizes:
        pixmap = create_default_icon(size)
        icon_path = os.path.join(icons_dir, f"icon_{size}x{size}.png")
        pixmap.save(icon_path)
        print(f"保存图标: {icon_path}")
    
    # 保存主图标
    main_icon_path = os.path.join(assets_dir, "icon.png")
    create_default_icon(64).save(main_icon_path)
    print(f"保存主图标: {main_icon_path}")

if __name__ == "__main__":
    # 需要先创建QApplication才能使用QPixmap
    from PyQt5.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    save_default_icons()
    print("图标生成完成!") 