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
import time

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
    
    def profile_exists(self, display_name: str) -> bool:
        """检查Profile显示名称是否已存在"""
        # 检查当前已扫描的profiles的显示名称
        for profile in self.profiles:
            if profile.display_name == display_name:
                return True
        
        # 重新扫描确保最新状态
        self.scan_profiles()
        for profile in self.profiles:
            if profile.display_name == display_name:
                return True
        
        return False
    
    def create_profile(self, name: str, display_name: str = None) -> bool:
        """创建新的Profile（符合Chrome标准）"""
        try:
            if not display_name:
                display_name = name
            
            # 检查显示名称是否已存在
            if self.profile_exists(display_name):
                print(f"Profile显示名称 '{display_name}' 已存在")
                return False
            
            # 获取Chrome用户数据目录
            if not self.chrome_paths:
                print("未找到Chrome用户数据目录")
                return False
            
            chrome_path = self.chrome_paths[0]  # 使用第一个找到的路径
            
            # 自动分配Profile目录名称
            actual_profile_name = self._get_next_profile_name(chrome_path)
            
            # 创建Profile目录
            profile_path = os.path.join(chrome_path, actual_profile_name)
            
            print(f"正在创建Profile: {display_name} -> {profile_path}")
            
            # 确保目录不存在
            if os.path.exists(profile_path):
                print(f"Profile目录已存在: {profile_path}")
                return False
            
            # 创建Profile目录
            os.makedirs(profile_path, exist_ok=True)
            
            # 创建基本的Preferences文件
            self._create_initial_preferences(profile_path, display_name)
            
            # 更新Chrome的Local State文件
            self._update_local_state(chrome_path, actual_profile_name, display_name)
            
            print(f"成功创建Profile: {display_name} ({actual_profile_name})")
            print(f"Profile路径: {profile_path}")
            
            return True
            
        except Exception as e:
            print(f"创建Profile失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _create_initial_preferences(self, profile_path: str, display_name: str):
        """创建初始的Preferences文件（基于Chrome标准结构）"""
        import json
        from datetime import datetime
        
        # 创建一个最小但完整的Preferences配置
        # 基于真实Chrome Profile的必要字段
        preferences = {
            "browser": {
                "window_placement": {
                    "maximized": False,
                    "left": 100,
                    "top": 100,
                    "right": 1380,
                    "bottom": 820
                }
            },
            "bookmark_bar": {
                "show_on_all_tabs": True
            },
            "profile": {
                "name": display_name,
                "created_by_version": "137.0.7151.69",  # 当前Chrome版本
                "creation_time": datetime.now().strftime("%Y%m%d%H%M%S%f")[:-3],  # Chrome时间格式
                "exit_type": "None",
                "content_settings": {
                    "exceptions": {}
                }
            },
            "extensions": {
                "settings": {}
            },
            "session": {
                "restore_on_startup": 1
            },
            "download": {
                "prompt_for_download": True
            },
            "search": {
                "suggest_enabled": True
            },
            "translate": {
                "enabled": True
            },
            "intl": {
                "accept_languages": "zh-CN,zh,en",
                "charset_default": "UTF-8"
            },
            "safebrowsing": {
                "enabled": True
            },
            "autofill": {
                "profile_enabled": True,
                "credit_card_enabled": True
            },
            "privacy": {
                "network_prediction_options": 1
            },
            "password_manager": {
                "profile_store_login_db": True
            }
        }
        
        # 写入Preferences文件
        preferences_path = os.path.join(profile_path, "Preferences")
        with open(preferences_path, 'w', encoding='utf-8') as f:
            json.dump(preferences, f, indent=2, ensure_ascii=False)
        
        print(f"已创建完整的Preferences文件: {preferences_path}")
        
        # 创建其他必要的基础文件
        self._create_essential_files(profile_path)
    
    def _create_essential_files(self, profile_path: str):
        """创建Chrome Profile的其他必要文件"""
        import sqlite3
        
        # 创建基本的SQLite数据库文件
        essential_dbs = [
            ("History", self._create_history_db),
            ("Cookies", self._create_cookies_db),
            ("Web Data", self._create_web_data_db),
            ("Login Data", self._create_login_data_db)
        ]
        
        for db_name, create_func in essential_dbs:
            db_path = os.path.join(profile_path, db_name)
            try:
                create_func(db_path)
                print(f"已创建数据库: {db_name}")
            except Exception as e:
                print(f"创建数据库 {db_name} 失败: {e}")
        
        # 创建Bookmarks文件
        self._create_bookmarks_file(profile_path)
    
    def _create_history_db(self, db_path: str):
        """创建History数据库"""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 创建基本的History表结构
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS urls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url LONGVARCHAR,
                title LONGVARCHAR,
                visit_count INTEGER DEFAULT 0,
                typed_count INTEGER DEFAULT 0,
                last_visit_time INTEGER,
                hidden INTEGER DEFAULT 0
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS visits (
                id INTEGER PRIMARY KEY,
                url INTEGER,
                visit_time INTEGER,
                from_visit INTEGER,
                transition INTEGER DEFAULT 0,
                segment_id INTEGER,
                visit_duration INTEGER DEFAULT 0
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _create_cookies_db(self, db_path: str):
        """创建Cookies数据库"""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cookies (
                creation_utc INTEGER NOT NULL,
                host_key TEXT NOT NULL,
                top_frame_site_key TEXT NOT NULL,
                name TEXT NOT NULL,
                value TEXT NOT NULL,
                encrypted_value BLOB DEFAULT '',
                path TEXT NOT NULL,
                expires_utc INTEGER NOT NULL,
                is_secure INTEGER NOT NULL,
                is_httponly INTEGER NOT NULL,
                last_access_utc INTEGER NOT NULL,
                has_expires INTEGER NOT NULL,
                is_persistent INTEGER NOT NULL,
                priority INTEGER NOT NULL,
                samesite INTEGER NOT NULL,
                source_scheme INTEGER NOT NULL,
                source_port INTEGER NOT NULL,
                is_same_party INTEGER NOT NULL
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _create_web_data_db(self, db_path: str):
        """创建Web Data数据库（自动填充等）"""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS autofill (
                name VARCHAR,
                value VARCHAR,
                value_lower VARCHAR,
                date_created INTEGER DEFAULT 0,
                date_last_used INTEGER DEFAULT 0,
                count INTEGER DEFAULT 1
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS credit_cards (
                guid VARCHAR PRIMARY KEY,
                name_on_card VARCHAR,
                expiration_month INTEGER,
                expiration_year INTEGER,
                card_number_encrypted BLOB,
                date_modified INTEGER NOT NULL DEFAULT 0
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _create_login_data_db(self, db_path: str):
        """创建Login Data数据库"""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS logins (
                origin_url VARCHAR NOT NULL,
                action_url VARCHAR,
                username_element VARCHAR,
                username_value VARCHAR,
                password_element VARCHAR,
                password_value BLOB,
                submit_element VARCHAR,
                signon_realm VARCHAR NOT NULL,
                date_created INTEGER NOT NULL,
                blacklisted_by_user INTEGER NOT NULL,
                scheme INTEGER NOT NULL,
                password_type INTEGER,
                times_used INTEGER,
                form_data BLOB,
                date_synced INTEGER,
                display_name VARCHAR,
                icon_url VARCHAR,
                federation_url VARCHAR,
                skip_zero_click INTEGER,
                generation_upload_status INTEGER,
                possible_username_pairs BLOB,
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date_last_used INTEGER,
                moving_blocked_for BLOB,
                date_password_modified INTEGER
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _create_bookmarks_file(self, profile_path: str):
        """创建Bookmarks文件"""
        import json
        
        bookmarks = {
            "checksum": "0000000000000000000000000000000000000000",
            "roots": {
                "bookmark_bar": {
                    "children": [],
                    "date_added": "13393900000000000",
                    "date_modified": "0",
                    "id": "1",
                    "name": "书签栏",
                    "type": "folder"
                },
                "other": {
                    "children": [],
                    "date_added": "13393900000000000",
                    "date_modified": "0",
                    "id": "2",
                    "name": "其他书签",
                    "type": "folder"
                },
                "synced": {
                    "children": [],
                    "date_added": "13393900000000000",
                    "date_modified": "0",
                    "id": "3",
                    "name": "移动设备书签",
                    "type": "folder"
                }
            },
            "version": 1
        }
        
        bookmarks_path = os.path.join(profile_path, "Bookmarks")
        with open(bookmarks_path, 'w', encoding='utf-8') as f:
            json.dump(bookmarks, f, indent=2, ensure_ascii=False)
        
        print(f"已创建Bookmarks文件: {bookmarks_path}")
    
    def _update_local_state(self, chrome_path: str, profile_name: str, display_name: str):
        """更新Chrome的Local State文件以注册新Profile"""
        import json
        from datetime import datetime
        import shutil
        import time
        
        local_state_path = os.path.join(chrome_path, "Local State")
        backup_path = local_state_path + ".backup"
        
        try:
            # 创建备份
            if os.path.exists(local_state_path):
                shutil.copy2(local_state_path, backup_path)
                print(f"已创建Local State备份: {backup_path}")
            
            # 读取现有的Local State
            local_state = {}
            if os.path.exists(local_state_path):
                try:
                    with open(local_state_path, 'r', encoding='utf-8') as f:
                        local_state = json.load(f)
                    print(f"成功读取Local State文件，大小: {len(json.dumps(local_state))} 字符")
                except (json.JSONDecodeError, UnicodeDecodeError) as e:
                    print(f"Local State文件损坏: {e}，将创建新的")
                    local_state = {}
            else:
                print("Local State文件不存在，将创建新的")
            
            # 确保profile字段存在
            if "profile" not in local_state:
                local_state["profile"] = {}
                print("创建profile字段")
            
            if "info_cache" not in local_state["profile"]:
                local_state["profile"]["info_cache"] = {}
                print("创建info_cache字段")
            
            # 检查Profile是否已存在
            if profile_name in local_state["profile"]["info_cache"]:
                print(f"Profile {profile_name} 已在Local State中存在，将更新")
            else:
                print(f"将添加新Profile {profile_name} 到Local State")
            
            # 添加新Profile信息
            current_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            
            # 使用Chrome标准的Profile配置格式
            profile_info = {
                "avatar_icon": "chrome://theme/IDR_PROFILE_AVATAR_0",
                "background_apps": False,
                "created_time": current_time,
                "name": display_name,
                "signin_required": False,
                "supervised_user_id": "",
                "is_ephemeral": False,
                "using_default_name": False,
                "using_default_avatar": True,
                "is_omitted_from_desktop_shortcut": False,
                "theme_color": 4279125008,  # 默认蓝色主题
                "managed_user_id": "",
                "shortcut_name": display_name,
                "user_name": display_name,
                "gaia_name": display_name,
                "local_profile_name": display_name,
                "gaia_given_name": "",  # 清空可能冲突的字段
                "gaia_id": "",
                "is_using_default_name": False
            }
            
            local_state["profile"]["info_cache"][profile_name] = profile_info
            
            # 更新其他相关字段
            if "last_used" not in local_state["profile"]:
                local_state["profile"]["last_used"] = profile_name
            
            # 确保profiles_order存在并更新
            if "profiles_order" not in local_state["profile"]:
                local_state["profile"]["profiles_order"] = []
            
            if profile_name not in local_state["profile"]["profiles_order"]:
                local_state["profile"]["profiles_order"].append(profile_name)
            
            # 尝试写入文件，重试机制
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    # 写入临时文件，然后重命名（原子操作）
                    temp_path = local_state_path + ".tmp"
                    with open(temp_path, 'w', encoding='utf-8') as f:
                        json.dump(local_state, f, indent=2, ensure_ascii=False)
                    
                    # 原子替换
                    if os.path.exists(local_state_path):
                        if platform.system() == "Windows":
                            os.remove(local_state_path)
                        os.rename(temp_path, local_state_path)
                    else:
                        os.rename(temp_path, local_state_path)
                    
                    print(f"成功更新Local State文件: {local_state_path}")
                    print(f"已注册Profile: {profile_name} -> {display_name}")
                    
                    # 验证写入是否成功
                    try:
                        with open(local_state_path, 'r', encoding='utf-8') as f:
                            verify_data = json.load(f)
                        if profile_name in verify_data.get("profile", {}).get("info_cache", {}):
                            print(f"✅ 验证成功：Profile {profile_name} 已在Local State中")
                            return True
                        else:
                            print(f"❌ 验证失败：Profile {profile_name} 未在Local State中找到")
                    except Exception as e:
                        print(f"验证失败: {e}")
                    
                    break
                    
                except Exception as e:
                    print(f"写入尝试 {attempt + 1} 失败: {e}")
                    if attempt < max_retries - 1:
                        time.sleep(0.5)  # 等待0.5秒后重试
                    else:
                        raise
            
        except Exception as e:
            print(f"更新Local State失败: {e}")
            import traceback
            traceback.print_exc()
            
            # 尝试恢复备份
            if os.path.exists(backup_path):
                try:
                    shutil.copy2(backup_path, local_state_path)
                    print("已从备份恢复Local State文件")
                except Exception as restore_e:
                    print(f"恢复备份失败: {restore_e}")
            
            return False
        
        return True
    
    def _get_next_profile_name(self, chrome_path: str) -> str:
        """获取下一个可用的Profile目录名称"""
        try:
            # 扫描现有的Profile目录
            existing_profile_numbers = []
            
            if os.path.exists(chrome_path):
                for item in os.listdir(chrome_path):
                    if item.startswith("Profile "):
                        try:
                            # 提取数字部分
                            number_part = item[8:]  # 移除"Profile "前缀
                            if number_part.isdigit():
                                existing_profile_numbers.append(int(number_part))
                        except:
                            continue
            
            # 找到下一个可用的数字
            if not existing_profile_numbers:
                next_number = 1
            else:
                next_number = max(existing_profile_numbers) + 1
            
            return f"Profile {next_number}"
            
        except Exception as e:
            print(f"获取Profile名称时出错: {e}")
            # 回退到时间戳方式
            return f"Profile {int(time.time() % 10000)}"
    
    def update_profile_display_name(self, profile_name: str, new_display_name: str) -> bool:
        """更新Profile的显示名称"""
        try:
            # 找到Profile路径
            profile_path = None
            for chrome_path in self.chrome_paths:
                if profile_name == "Default":
                    test_path = os.path.join(chrome_path, "Default")
                else:
                    test_path = os.path.join(chrome_path, profile_name)
                
                if os.path.exists(test_path):
                    profile_path = test_path
                    chrome_data_path = chrome_path
                    break
            
            if not profile_path:
                print(f"未找到Profile: {profile_name}")
                return False
            
            # 更新Preferences文件
            prefs_file = os.path.join(profile_path, "Preferences")
            if os.path.exists(prefs_file):
                with open(prefs_file, 'r', encoding='utf-8') as f:
                    prefs = json.load(f)
                
                # 更新各个可能的名称字段
                if 'profile' not in prefs:
                    prefs['profile'] = {}
                
                prefs['profile']['name'] = new_display_name
                prefs['profile']['local_profile_name'] = new_display_name
                
                # 保存更新后的Preferences
                with open(prefs_file, 'w', encoding='utf-8') as f:
                    json.dump(prefs, f, indent=2, ensure_ascii=False)
            
            # 更新Local State文件
            local_state_file = os.path.join(chrome_data_path, "Local State")
            if os.path.exists(local_state_file):
                with open(local_state_file, 'r', encoding='utf-8') as f:
                    local_state = json.load(f)
                
                # 更新Profile信息缓存
                profile_info_cache = local_state.get('profile', {}).get('info_cache', {})
                if profile_name in profile_info_cache:
                    profile_info_cache[profile_name]['name'] = new_display_name
                    profile_info_cache[profile_name]['user_name'] = new_display_name
                    profile_info_cache[profile_name]['shortcut_name'] = new_display_name
                
                # 保存Local State
                with open(local_state_file, 'w', encoding='utf-8') as f:
                    json.dump(local_state, f, indent=2, ensure_ascii=False)
            
            print(f"成功更新Profile显示名称: {profile_name} -> {new_display_name}")
            
            # 重新扫描以更新列表
            self.scan_profiles()
            
            return True
            
        except Exception as e:
            print(f"更新Profile显示名称失败: {e}")
            return False
    
    def delete_profile(self, profile_name: str) -> bool:
        """删除Profile"""
        try:
            import shutil
            
            # 找到Profile路径
            profile_path = None
            chrome_data_path = None
            
            for chrome_path in self.chrome_paths:
                if profile_name == "Default":
                    test_path = os.path.join(chrome_path, "Default")
                else:
                    test_path = os.path.join(chrome_path, profile_name)
                
                if os.path.exists(test_path):
                    profile_path = test_path
                    chrome_data_path = chrome_path
                    break
            
            if not profile_path:
                print(f"未找到Profile: {profile_name}")
                return False
            
            # 不允许删除默认Profile
            if profile_name == "Default":
                print("不允许删除默认Profile")
                return False
            
            # 删除Profile目录
            shutil.rmtree(profile_path)
            print(f"已删除Profile目录: {profile_path}")
            
            # 从Local State中移除Profile信息
            local_state_file = os.path.join(chrome_data_path, "Local State")
            if os.path.exists(local_state_file):
                try:
                    with open(local_state_file, 'r', encoding='utf-8') as f:
                        local_state = json.load(f)
                    
                    # 从Profile信息缓存中移除
                    profile_info_cache = local_state.get('profile', {}).get('info_cache', {})
                    if profile_name in profile_info_cache:
                        del profile_info_cache[profile_name]
                    
                    # 保存Local State
                    with open(local_state_file, 'w', encoding='utf-8') as f:
                        json.dump(local_state, f, indent=2, ensure_ascii=False)
                    
                    print(f"已从Local State中移除Profile信息: {profile_name}")
                    
                except Exception as e:
                    print(f"更新Local State时出错: {e}")
            
            print(f"成功删除Profile: {profile_name}")
            
            # 重新扫描以更新列表
            self.scan_profiles()
            
            return True
            
        except Exception as e:
            print(f"删除Profile失败: {e}")
            return False 