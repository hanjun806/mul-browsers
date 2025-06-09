#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
浏览器进程管理器
负责启动、关闭和监控Chrome浏览器实例
"""

import os
import platform
import subprocess
import psutil
import time
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from .profile_manager import ProfileInfo

@dataclass
class BrowserInstance:
    """浏览器实例信息"""
    profile_name: str
    process_id: int
    process: psutil.Process
    start_time: float
    user_data_dir: str
    command_line: List[str]

class BrowserManager:
    """浏览器进程管理器"""
    
    def __init__(self):
        self.running_instances: Dict[str, BrowserInstance] = {}
        self.chrome_executable = self._find_chrome_executable()
    
    def _find_chrome_executable(self) -> Optional[str]:
        """查找Chrome可执行文件路径"""
        system = platform.system()
        
        if system == "Darwin":  # macOS
            chrome_paths = [
                "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                "/Applications/Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary",
            ]
        elif system == "Windows":
            chrome_paths = [
                "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
                "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
                os.path.expanduser("~\\AppData\\Local\\Google\\Chrome\\Application\\chrome.exe"),
            ]
        elif system == "Linux":
            chrome_paths = [
                "/usr/bin/google-chrome",
                "/usr/bin/google-chrome-stable",
                "/usr/bin/chromium-browser",
            ]
        else:
            return None
        
        for path in chrome_paths:
            if os.path.exists(path):
                return path
        
        return None
    
    def start_browser(self, profile: ProfileInfo, 
                     language: str = None,
                     proxy_config: Dict = None,
                     window_size: Tuple[int, int] = None,
                     custom_args: List[str] = None) -> bool:
        """启动浏览器实例"""
        
        if not self.chrome_executable:
            print("错误: 未找到Chrome可执行文件")
            return False
        
        if profile.name in self.running_instances:
            print(f"Profile '{profile.display_name}' 已经在运行中")
            return False
        
        # 构建启动命令
        cmd = [self.chrome_executable]
        
        # 用户数据目录
        user_data_dir = os.path.dirname(profile.path)
        if profile.is_default:
            cmd.extend([f"--user-data-dir={user_data_dir}"])
        else:
            cmd.extend([f"--user-data-dir={user_data_dir}", f"--profile-directory={profile.name}"])
        
        # 语言设置
        if language:
            cmd.append(f"--lang={language}")
        
        # 代理设置
        if proxy_config:
            proxy_type = proxy_config.get('type', 'http')
            proxy_server = proxy_config.get('server', '')
            proxy_port = proxy_config.get('port', 8080)
            
            if proxy_server:  # 只有在设置了服务器地址时才添加代理参数
                if proxy_type in ['http', 'https']:
                    cmd.append(f"--proxy-server=http://{proxy_server}:{proxy_port}")
                elif proxy_type == 'socks5':
                    cmd.append(f"--proxy-server=socks5://{proxy_server}:{proxy_port}")
                elif proxy_type == 'socks4':
                    cmd.append(f"--proxy-server=socks4://{proxy_server}:{proxy_port}")
            
            # 代理认证
            if proxy_config.get('username') and proxy_config.get('password'):
                # 注意: Chrome不直接支持代理认证，需要使用扩展程序
                pass
        
        # 窗口大小
        if window_size:
            cmd.append(f"--window-size={window_size[0]},{window_size[1]}")
        
        # 自定义参数
        if custom_args:
            cmd.extend(custom_args)
        
        # 添加一些常用的启动参数
        cmd.extend([
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-default-apps",
        ])
        
        try:
            print(f"启动命令: {' '.join(cmd)}")
            
            # 启动进程
            process = subprocess.Popen(cmd, 
                                     stdout=subprocess.DEVNULL, 
                                     stderr=subprocess.DEVNULL)
            
            print(f"进程已启动，PID: {process.pid}")
            
            # 等待进程稳定启动（增加等待时间）
            time.sleep(3)
            
            # 检查进程是否还在运行
            poll_result = process.poll()
            print(f"进程状态检查: {poll_result}")
            
            if poll_result is None:
                # 进程仍在运行，创建实例记录
                try:
                    psutil_process = psutil.Process(process.pid)
                    
                    # 再次确认进程确实在运行
                    if psutil_process.is_running():
                        instance = BrowserInstance(
                            profile_name=profile.name,
                            process_id=process.pid,
                            process=psutil_process,
                            start_time=time.time(),
                            user_data_dir=user_data_dir,
                            command_line=cmd
                        )
                        
                        self.running_instances[profile.name] = instance
                        print(f"成功启动浏览器实例: {profile.display_name} (PID: {process.pid})")
                        return True
                    else:
                        print(f"进程已退出: {profile.display_name}")
                        return False
                        
                except psutil.NoSuchProcess:
                    print(f"无法找到进程: {process.pid}")
                    return False
            else:
                print(f"启动浏览器实例失败: {profile.display_name} (退出码: {poll_result})")
                return False
                
        except Exception as e:
            print(f"启动浏览器时出错: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def close_browser(self, profile_name: str, force: bool = False) -> bool:
        """关闭浏览器实例"""
        if profile_name not in self.running_instances:
            print(f"Profile '{profile_name}' 未在运行")
            return False
        
        instance = self.running_instances[profile_name]
        
        try:
            if force:
                # 强制终止
                instance.process.kill()
                print(f"强制终止浏览器实例: {profile_name}")
            else:
                # 优雅关闭
                instance.process.terminate()
                
                # 等待进程结束
                try:
                    instance.process.wait(timeout=10)
                    print(f"优雅关闭浏览器实例: {profile_name}")
                except psutil.TimeoutExpired:
                    # 超时后强制关闭
                    instance.process.kill()
                    print(f"超时后强制关闭浏览器实例: {profile_name}")
            
            # 从运行实例中移除
            del self.running_instances[profile_name]
            return True
            
        except psutil.NoSuchProcess:
            # 进程已经不存在
            del self.running_instances[profile_name]
            return True
        except Exception as e:
            print(f"关闭浏览器时出错: {e}")
            return False
    
    def close_all_browsers(self) -> bool:
        """关闭所有浏览器实例"""
        success = True
        profile_names = list(self.running_instances.keys())
        
        for profile_name in profile_names:
            if not self.close_browser(profile_name):
                success = False
        
        return success
    
    def is_browser_running(self, profile_name: str) -> bool:
        """检查浏览器实例是否在运行"""
        if profile_name not in self.running_instances:
            return False
        
        instance = self.running_instances[profile_name]
        try:
            # 检查进程是否还存在
            return instance.process.is_running()
        except psutil.NoSuchProcess:
            # 进程已经不存在，从列表中移除
            del self.running_instances[profile_name]
            return False
    
    def get_browser_info(self, profile_name: str) -> Optional[Dict]:
        """获取浏览器实例信息"""
        if not self.is_browser_running(profile_name):
            return None
        
        instance = self.running_instances[profile_name]
        
        try:
            memory_info = instance.process.memory_info()
            cpu_percent = instance.process.cpu_percent()
            
            return {
                'pid': instance.process_id,
                'start_time': instance.start_time,
                'memory_usage': memory_info.rss,  # 物理内存使用量
                'memory_percent': instance.process.memory_percent(),
                'cpu_percent': cpu_percent,
                'status': instance.process.status(),
                'command_line': instance.command_line
            }
        except Exception as e:
            print(f"获取浏览器信息时出错: {e}")
            return None
    
    def get_all_running_browsers(self) -> Dict[str, Dict]:
        """获取所有运行中的浏览器信息"""
        running_browsers = {}
        
        # 清理已经停止的实例
        stopped_profiles = []
        for profile_name in self.running_instances:
            if not self.is_browser_running(profile_name):
                stopped_profiles.append(profile_name)
        
        for profile_name in stopped_profiles:
            if profile_name in self.running_instances:
                del self.running_instances[profile_name]
        
        # 获取运行中的浏览器信息
        for profile_name in self.running_instances:
            browser_info = self.get_browser_info(profile_name)
            if browser_info:
                running_browsers[profile_name] = browser_info
        
        return running_browsers
    
    def restart_browser(self, profile: ProfileInfo, **kwargs) -> bool:
        """重启浏览器实例"""
        if self.is_browser_running(profile.name):
            if not self.close_browser(profile.name):
                return False
            
            # 等待进程完全关闭
            time.sleep(2)
        
        return self.start_browser(profile, **kwargs)
    
    def format_memory_usage(self, memory_bytes: int) -> str:
        """格式化内存使用量显示"""
        if memory_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        size = float(memory_bytes)
        
        while size >= 1024.0 and i < len(size_names) - 1:
            size /= 1024.0
            i += 1
        
        return f"{size:.1f} {size_names[i]}" 