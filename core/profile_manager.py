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
            # 首先从Local State中获取显示名称
            display_name = self._get_profile_name_from_local_state(name, path)
            
            # 如果Local State中没有找到，再从Preferences中读取
            if display_name == name:
                prefs_file = os.path.join(path, "Preferences")
                if os.path.exists(prefs_file):
                    try:
                        with open(prefs_file, 'r', encoding='utf-8') as f:
                            prefs = json.load(f)
                        
                        # 获取显示名称 - Chrome存储在不同的位置
                        profile_section = prefs.get('profile', {})
                        
                        # 尝试多个可能的名称字段
                        possible_name_fields = ['name', 'local_profile_name', 'user_name']
                        for field in possible_name_fields:
                            if field in profile_section and profile_section[field]:
                                display_name = profile_section[field]
                                break
                        
                        # 如果还是没有找到名称，尝试从account_info中获取
                        account_info = prefs.get('account_info', {})
                        if not display_name or display_name == name:
                            if 'full_name' in account_info and account_info['full_name']:
                                display_name = account_info['full_name']
                            elif 'given_name' in account_info and account_info['given_name']:
                                display_name = account_info['given_name']
                        
                        # 最后尝试从signin相关信息获取
                        if not display_name or display_name == name:
                            signin_info = prefs.get('signin', {})
                            if 'allowed_username' in signin_info and signin_info['allowed_username']:
                                display_name = signin_info['allowed_username']
                        
                    except (json.JSONDecodeError, KeyError) as e:
                        print(f"读取Preferences文件出错: {e}")
                        pass
            
            # 获取时间信息
            created_time = None
            last_used_time = None
            prefs_file = os.path.join(path, "Preferences")
            if os.path.exists(prefs_file):
                try:
                    stats = os.stat(prefs_file)
                    created_time = datetime.fromtimestamp(stats.st_ctime)
                    last_used_time = datetime.fromtimestamp(stats.st_mtime)
                except Exception:
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
    
    def _get_profile_name_from_local_state(self, profile_name: str, profile_path: str) -> str:
        """从Local State文件中获取Profile名称"""
        try:
            # Local State文件在Chrome用户数据目录的根目录
            chrome_dir = os.path.dirname(profile_path)
            local_state_file = os.path.join(chrome_dir, "Local State")
            
            if os.path.exists(local_state_file):
                with open(local_state_file, 'r', encoding='utf-8') as f:
                    local_state = json.load(f)
                
                # 在profile.info_cache中查找
                profile_info_cache = local_state.get('profile', {}).get('info_cache', {})
                
                # 查找对应的profile
                for profile_key, profile_data in profile_info_cache.items():
                    if profile_key == profile_name or profile_key.endswith(profile_name):
                        # 尝试获取名称
                        if 'name' in profile_data and profile_data['name']:
                            return profile_data['name']
                        elif 'user_name' in profile_data and profile_data['user_name']:
                            return profile_data['user_name']
                        elif 'gaia_name' in profile_data and profile_data['gaia_name']:
                            return profile_data['gaia_name']
            
        except Exception as e:
            print(f"读取Local State文件出错: {e}")
        
        return profile_name  # 如果都失败了，返回原始名称
    
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