#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理器
负责保存和加载每个Profile的启动配置
"""

import os
import json
import time
from typing import Dict, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path

@dataclass
class ProfileConfig:
    """Profile启动配置"""
    profile_name: str
    language: str = "zh-CN"
    proxy_enabled: bool = False
    proxy_type: str = "http"
    proxy_server: str = ""
    proxy_port: int = 8080
    proxy_username: str = ""
    proxy_password: str = ""
    window_width: int = 1280
    window_height: int = 720
    custom_args: list = None
    
    def __post_init__(self):
        if self.custom_args is None:
            self.custom_args = []

class ConfigManager:
    """配置管理器"""
    
    def __init__(self):
        self.config_dir = self._get_config_dir()
        self._ensure_config_dir()
    
    def _get_config_dir(self) -> str:
        """获取配置文件目录"""
        # 在应用程序目录下创建configs文件夹
        app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_dir = os.path.join(app_dir, "configs")
        return config_dir
    
    def _ensure_config_dir(self):
        """确保配置目录存在"""
        os.makedirs(self.config_dir, exist_ok=True)
    
    def _get_config_file_path(self, profile_name: str) -> str:
        """获取指定Profile的配置文件路径"""
        # 将Profile名称中的特殊字符替换为安全字符
        safe_name = profile_name.replace("/", "_").replace("\\", "_").replace(":", "_")
        filename = f"{safe_name}.json"
        return os.path.join(self.config_dir, filename)
    
    def save_config(self, config: ProfileConfig) -> bool:
        """保存Profile配置"""
        try:
            config_file = self._get_config_file_path(config.profile_name)
            
            # 转换为字典
            config_dict = asdict(config)
            
            # 保存到文件
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, indent=2, ensure_ascii=False)
            
            print(f"配置已保存: {config_file}")
            return True
            
        except Exception as e:
            print(f"保存配置失败: {e}")
            return False
    
    def load_config(self, profile_name: str) -> ProfileConfig:
        """加载Profile配置，如果不存在则返回默认配置"""
        try:
            config_file = self._get_config_file_path(profile_name)
            
            if not os.path.exists(config_file):
                # 返回默认配置
                print(f"配置文件不存在，使用默认配置: {profile_name}")
                return ProfileConfig(profile_name=profile_name)
            
            # 从文件加载配置
            with open(config_file, 'r', encoding='utf-8') as f:
                config_dict = json.load(f)
            
            # 创建配置对象，确保包含所有必要字段
            config = ProfileConfig(
                profile_name=config_dict.get('profile_name', profile_name),
                language=config_dict.get('language', 'zh-CN'),
                proxy_enabled=config_dict.get('proxy_enabled', False),
                proxy_type=config_dict.get('proxy_type', 'http'),
                proxy_server=config_dict.get('proxy_server', ''),
                proxy_port=config_dict.get('proxy_port', 8080),
                proxy_username=config_dict.get('proxy_username', ''),
                proxy_password=config_dict.get('proxy_password', ''),
                window_width=config_dict.get('window_width', 1280),
                window_height=config_dict.get('window_height', 720),
                custom_args=config_dict.get('custom_args', [])
            )
            
            print(f"配置已加载: {config_file}")
            return config
            
        except Exception as e:
            print(f"加载配置失败: {e}")
            # 返回默认配置
            return ProfileConfig(profile_name=profile_name)
    
    def delete_config(self, profile_name: str) -> bool:
        """删除Profile配置"""
        try:
            config_file = self._get_config_file_path(profile_name)
            
            if os.path.exists(config_file):
                os.remove(config_file)
                print(f"配置已删除: {config_file}")
                return True
            else:
                print(f"配置文件不存在: {profile_name}")
                return True
                
        except Exception as e:
            print(f"删除配置失败: {e}")
            return False
    
    def list_configs(self) -> list:
        """列出所有已保存的配置"""
        try:
            if not os.path.exists(self.config_dir):
                return []
            
            configs = []
            for filename in os.listdir(self.config_dir):
                if filename.endswith('.json'):
                    profile_name = filename[:-5]  # 移除.json后缀
                    configs.append(profile_name)
            
            return configs
            
        except Exception as e:
            print(f"列出配置失败: {e}")
            return []
    
    def export_config(self, profile_name: str, export_path: str) -> bool:
        """导出Profile配置到指定路径"""
        try:
            config = self.load_config(profile_name)
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(asdict(config), f, indent=2, ensure_ascii=False)
            
            print(f"配置已导出: {export_path}")
            return True
            
        except Exception as e:
            print(f"导出配置失败: {e}")
            return False
    
    def import_config(self, import_path: str) -> Optional[ProfileConfig]:
        """从指定路径导入Profile配置"""
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                config_dict = json.load(f)
            
            config = ProfileConfig(**config_dict)
            
            # 保存导入的配置
            self.save_config(config)
            
            print(f"配置已导入: {import_path}")
            return config
            
        except Exception as e:
            print(f"导入配置失败: {e}")
            return None
    
    def get_config_dict(self, profile_name: str) -> Dict[str, Any]:
        """获取配置的字典形式，用于传递给browser_manager"""
        config = self.load_config(profile_name)
        
        result = {
            'language': config.language,
            'window_size': (config.window_width, config.window_height),
            'custom_args': config.custom_args
        }
        
        # 只有启用代理时才添加代理配置
        if config.proxy_enabled and config.proxy_server:
            result['proxy_config'] = {
                'type': config.proxy_type,
                'server': config.proxy_server,
                'port': config.proxy_port,
                'username': config.proxy_username if config.proxy_username else None,
                'password': config.proxy_password if config.proxy_password else None
            }
        
        return result
    
    def save_profile_order(self, profile_order: list) -> bool:
        """保存Profile排序"""
        try:
            order_file = os.path.join(self.config_dir, "profile_order.json")
            
            order_data = {
                'order': profile_order,
                'timestamp': time.time()
            }
            
            with open(order_file, 'w', encoding='utf-8') as f:
                json.dump(order_data, f, indent=2, ensure_ascii=False)
            
            print(f"Profile排序已保存: {order_file}")
            return True
            
        except Exception as e:
            print(f"保存Profile排序失败: {e}")
            return False
    
    def load_profile_order(self) -> list:
        """加载Profile排序"""
        try:
            order_file = os.path.join(self.config_dir, "profile_order.json")
            
            if not os.path.exists(order_file):
                print("Profile排序文件不存在，使用默认排序")
                return []
            
            with open(order_file, 'r', encoding='utf-8') as f:
                order_data = json.load(f)
            
            order = order_data.get('order', [])
            print(f"Profile排序已加载: {len(order)} 个")
            return order
            
        except Exception as e:
            print(f"加载Profile排序失败: {e}")
            return [] 