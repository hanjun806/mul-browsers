#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Chrome Profile 管理器
负责发现、扫描和管理Chrome浏览器的Profile
"""

import os
import json
import platform
import sqlite3
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime

@dataclass
class ProfileInfo:
    """Profile信息数据类"""
    name: str
    path: str
    display_name: str
    is_default: bool
    created_time: Optional[datetime]
    last_used_time: Optional[datetime]
    bookmarks_count: int = 0
    extensions_count: int = 0
    storage_size: int = 0
    is_running: bool = False

class ProfileManager:
    """Chrome Profile管理器"""
    
    def __init__(self):
        self.profiles: List[ProfileInfo] = []
        self.chrome_paths = self._get_chrome_paths()
    
    def _get_chrome_paths(self) -> List[str]:
        """获取不同操作系统下Chrome的用户数据目录路径"""
        system = platform.system()
        paths = []
        
        if system == "Darwin":  # macOS
            base_path = os.path.expanduser("~/Library/Application Support/Google/Chrome")
            if os.path.exists(base_path):
                paths.append(base_path)
        elif system == "Windows":
            # Windows下的路径
            appdata = os.environ.get('LOCALAPPDATA', '')
            if appdata:
                chrome_path = os.path.join(appdata, 'Google', 'Chrome', 'User Data')
                if os.path.exists(chrome_path):
                    paths.append(chrome_path)
        elif system == "Linux":
            # Linux下的路径
            home = os.path.expanduser("~")
            chrome_path = os.path.join(home, '.config', 'google-chrome')
            if os.path.exists(chrome_path):
                paths.append(chrome_path)
        
        return paths
    
    def scan_profiles(self) -> List[ProfileInfo]:
        """扫描所有Chrome Profile"""
        self.profiles.clear()
        
        for chrome_path in self.chrome_paths:
            self._scan_chrome_directory(chrome_path)
        
        return self.profiles
    
    def _scan_chrome_directory(self, chrome_path: str):
        """扫描Chrome目录下的所有Profile"""
        if not os.path.exists(chrome_path):
            return
        
        # 扫描默认Profile
        default_profile_path = os.path.join(chrome_path, "Default")
        if os.path.exists(default_profile_path):
            profile_info = self._create_profile_info("Default", default_profile_path, True)
            if profile_info:
                self.profiles.append(profile_info)
        
        # 扫描其他Profile目录
        for item in os.listdir(chrome_path):
            if item.startswith("Profile "):
                profile_path = os.path.join(chrome_path, item)
                if os.path.isdir(profile_path):
                    profile_info = self._create_profile_info(item, profile_path, False)
                    if profile_info:
                        self.profiles.append(profile_info)
    
    def _create_profile_info(self, name: str, path: str, is_default: bool) -> Optional[ProfileInfo]:
        """创建Profile信息对象"""
        try:
            # 读取Profile的偏好设置
            prefs_file = os.path.join(path, "Preferences")
            display_name = name
            created_time = None
            last_used_time = None
            
            if os.path.exists(prefs_file):
                try:
                    with open(prefs_file, 'r', encoding='utf-8') as f:
                        prefs = json.load(f)
                    
                    # 获取显示名称
                    profile_info = prefs.get('profile', {})
                    if 'name' in profile_info:
                        display_name = profile_info['name']
                    
                    # 获取时间信息
                    stats = os.stat(prefs_file)
                    created_time = datetime.fromtimestamp(stats.st_ctime)
                    last_used_time = datetime.fromtimestamp(stats.st_mtime)
                    
                except (json.JSONDecodeError, KeyError):
                    pass
            
            # 计算书签数量
            bookmarks_count = self._count_bookmarks(path)
            
            # 计算扩展程序数量
            extensions_count = self._count_extensions(path)
            
            # 计算存储大小
            storage_size = self._calculate_storage_size(path)
            
            return ProfileInfo(
                name=name,
                path=path,
                display_name=display_name,
                is_default=is_default,
                created_time=created_time,
                last_used_time=last_used_time,
                bookmarks_count=bookmarks_count,
                extensions_count=extensions_count,
                storage_size=storage_size
            )
            
        except Exception as e:
            print(f"创建Profile信息时出错: {e}")
            return None
    
    def _count_bookmarks(self, profile_path: str) -> int:
        """统计书签数量"""
        bookmarks_file = os.path.join(profile_path, "Bookmarks")
        if not os.path.exists(bookmarks_file):
            return 0
        
        try:
            with open(bookmarks_file, 'r', encoding='utf-8') as f:
                bookmarks_data = json.load(f)
            
            def count_recursive(node):
                count = 0
                if node.get('type') == 'url':
                    count = 1
                elif node.get('type') == 'folder':
                    children = node.get('children', [])
                    for child in children:
                        count += count_recursive(child)
                return count
            
            total_count = 0
            roots = bookmarks_data.get('roots', {})
            for root_name, root_data in roots.items():
                if isinstance(root_data, dict):
                    total_count += count_recursive(root_data)
            
            return total_count
            
        except (json.JSONDecodeError, KeyError):
            return 0
    
    def _count_extensions(self, profile_path: str) -> int:
        """统计扩展程序数量"""
        extensions_dir = os.path.join(profile_path, "Extensions")
        if not os.path.exists(extensions_dir):
            return 0
        
        try:
            return len([d for d in os.listdir(extensions_dir) 
                       if os.path.isdir(os.path.join(extensions_dir, d))])
        except:
            return 0
    
    def _calculate_storage_size(self, profile_path: str) -> int:
        """计算Profile存储大小（字节）"""
        total_size = 0
        try:
            for dirpath, dirnames, filenames in os.walk(profile_path):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    try:
                        total_size += os.path.getsize(filepath)
                    except:
                        continue
        except:
            pass
        return total_size
    
    def get_profile_by_name(self, name: str) -> Optional[ProfileInfo]:
        """根据名称获取Profile"""
        for profile in self.profiles:
            if profile.name == name:
                return profile
        return None
    
    def refresh_profiles(self):
        """刷新Profile列表"""
        self.scan_profiles()
    
    def format_size(self, size_bytes: int) -> str:
        """格式化文件大小显示"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        size = float(size_bytes)
        
        while size >= 1024.0 and i < len(size_names) - 1:
            size /= 1024.0
            i += 1
        
        return f"{size:.1f} {size_names[i]}" 