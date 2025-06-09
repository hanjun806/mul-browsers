#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图标生成器
将SVG图标转换为不同尺寸的PNG格式
"""

import os
from PyQt5.QtSvg import QSvgRenderer
from PyQt5.QtGui import QPixmap, QPainter
from PyQt5.QtCore import QSize

def create_icon_from_svg(svg_path: str, output_dir: str, sizes: list = None):
    """
    从SVG文件创建不同尺寸的PNG图标
    
    Args:
        svg_path: SVG文件路径
        output_dir: 输出目录
        sizes: 要生成的尺寸列表，默认为[16, 32, 48, 64, 128, 256]
    """
    if sizes is None:
        sizes = [16, 32, 48, 64, 128, 256]
    
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 加载SVG
    renderer = QSvgRenderer(svg_path)
    
    for size in sizes:
        # 创建指定尺寸的QPixmap
        pixmap = QPixmap(size, size)
        pixmap.fill()  # 填充透明背景
        
        # 创建画家对象
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 渲染SVG到pixmap
        renderer.render(painter)
        painter.end()
        
        # 保存PNG文件
        output_path = os.path.join(output_dir, f"icon_{size}x{size}.png")
        pixmap.save(output_path)
        print(f"生成图标: {output_path}")

def generate_icons():
    """生成所有需要的图标"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    
    svg_path = os.path.join(project_root, "assets", "icon.svg")
    output_dir = os.path.join(project_root, "assets", "icons")
    
    if os.path.exists(svg_path):
        create_icon_from_svg(svg_path, output_dir)
        print("图标生成完成!")
    else:
        print(f"SVG文件不存在: {svg_path}")

if __name__ == "__main__":
    generate_icons() 