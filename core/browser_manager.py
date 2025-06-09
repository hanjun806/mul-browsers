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
        
        # 使用原始的Profile路径
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
        
        # 添加启动参数，重点是支持多实例
        cmd.extend([
            "--no-first-run",
            "--no-default-browser-check",
        ])
        
        # macOS特定的多实例支持参数
        if platform.system() == "Darwin":
            cmd.extend([
                "--new-window",  # 在新窗口中打开
            ])
        
        try:
            print(f"启动命令: {' '.join(cmd)}")
            
            # 对于macOS，使用open命令的特殊方式
            if platform.system() == "Darwin":
                # 使用open命令启动新的Chrome实例
                # open -n 强制启动新实例，即使应用已经运行
                open_cmd = ["open", "-n", "-a", "Google Chrome", "--args"] + cmd[1:]
                print(f"macOS启动命令: {' '.join(open_cmd)}")
                
                process = subprocess.Popen(open_cmd, 
                                         stdout=subprocess.DEVNULL, 
                                         stderr=subprocess.DEVNULL,
                                         start_new_session=True)
            elif platform.system() == "Windows":
                # Windows特殊处理
                process = subprocess.Popen(cmd, 
                                         stdout=subprocess.DEVNULL, 
                                         stderr=subprocess.DEVNULL,
                                         creationflags=subprocess.DETACHED_PROCESS)
            else:
                # Linux
                process = subprocess.Popen(cmd, 
                                         stdout=subprocess.DEVNULL, 
                                         stderr=subprocess.DEVNULL,
                                         start_new_session=True)
            
            print(f"进程已启动，PID: {process.pid}")
            
            # 等待Chrome启动并稳定
            time.sleep(3)
            
            # Chrome启动机制特殊：初始进程可能会退出，但Chrome会继续运行
            # 我们需要通过检查是否有Chrome进程在使用指定的Profile来判断启动是否成功
            chrome_started = self._check_chrome_running_for_profile(profile, user_data_dir)
            
            if chrome_started:
                # 找到运行中的Chrome进程
                running_process = self._find_chrome_process_for_profile(profile, user_data_dir)
                
                if running_process:
                    instance = BrowserInstance(
                        profile_name=profile.name,
                        process_id=running_process.pid,
                        process=running_process,
                        start_time=time.time(),
                        user_data_dir=user_data_dir,
                        command_line=cmd
                    )
                    
                    self.running_instances[profile.name] = instance
                    print(f"成功启动浏览器实例: {profile.display_name} (PID: {running_process.pid})")
                    return True
                else:
                    print(f"Chrome已启动但无法找到对应进程: {profile.display_name}")
                    return True  # Chrome确实在运行，即使找不到精确的进程
            else:
                print(f"启动浏览器实例失败: {profile.display_name}")
                return False
                
        except Exception as e:
            print(f"启动浏览器时出错: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _check_chrome_running_for_profile(self, profile: ProfileInfo, user_data_dir: str) -> bool:
        """检查是否有Chrome进程在使用指定的Profile"""
        try:
            print(f"开始检查Chrome进程，Profile: {profile.name}, 用户数据目录: {user_data_dir}")
            
            # 等待一段时间让Chrome完全启动
            for attempt in range(15):  # 最多等待7.5秒，每次0.5秒
                time.sleep(0.5)
                print(f"第 {attempt + 1} 次检查...")
                
                # 遍历所有Chrome进程
                chrome_processes = []
                for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                    try:
                        if proc.info['name'] and ('chrome' in proc.info['name'].lower() or 'google chrome' in proc.info['name'].lower()):
                            cmdline = proc.info['cmdline']
                            if cmdline:
                                cmdline_str = ' '.join(cmdline)
                                chrome_processes.append({
                                    'pid': proc.info['pid'],
                                    'cmdline': cmdline_str
                                })
                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                        continue
                
                print(f"找到 {len(chrome_processes)} 个Chrome进程")
                
                # 检查是否有进程使用我们的Profile
                for proc_info in chrome_processes:
                    cmdline = proc_info['cmdline']
                    
                    # 检查用户数据目录
                    if user_data_dir.replace(' ', '\\ ') in cmdline or user_data_dir in cmdline:
                        # 对于默认Profile，只需要包含用户数据目录且没有profile-directory参数
                        if profile.is_default:
                            if '--profile-directory=' not in cmdline:
                                print(f"找到默认Profile的Chrome进程: PID={proc_info['pid']}")
                                return True
                        else:
                            # 对于非默认Profile，需要包含正确的profile-directory
                            if f'--profile-directory={profile.name}' in cmdline:
                                print(f"找到Profile {profile.name} 的Chrome进程: PID={proc_info['pid']}")
                                return True
                            # 也尝试检查是否有引号包围的情况
                            elif f'--profile-directory="{profile.name}"' in cmdline:
                                print(f"找到Profile {profile.name} 的Chrome进程: PID={proc_info['pid']}")
                                return True
                
                # 如果是前几次检查，等待更长时间
                if attempt < 5:
                    print("Chrome可能还在启动中，继续等待...")
                elif attempt < 10:
                    print("检查更多进程...")
            
            print("未找到匹配的Chrome进程")
            return False
            
        except Exception as e:
            print(f"检查Chrome进程时出错: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _find_chrome_process_for_profile(self, profile: ProfileInfo, user_data_dir: str) -> Optional[psutil.Process]:
        """查找使用指定Profile的Chrome进程"""
        try:
            print(f"查找Profile {profile.name} 对应的Chrome进程...")
            
            # 遍历所有Chrome进程
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['name'] and ('chrome' in proc.info['name'].lower() or 'google chrome' in proc.info['name'].lower()):
                        cmdline = proc.info['cmdline']
                        if cmdline:
                            cmdline_str = ' '.join(cmdline)
                            
                            # 检查用户数据目录
                            if user_data_dir.replace(' ', '\\ ') in cmdline_str or user_data_dir in cmdline_str:
                                # 对于默认Profile
                                if profile.is_default:
                                    if '--profile-directory=' not in cmdline_str:
                                        print(f"找到默认Profile的进程: PID={proc.info['pid']}")
                                        return psutil.Process(proc.info['pid'])
                                else:
                                    # 对于非默认Profile
                                    if f'--profile-directory={profile.name}' in cmdline_str or f'--profile-directory="{profile.name}"' in cmdline_str:
                                        print(f"找到Profile {profile.name} 的进程: PID={proc.info['pid']}")
                                        return psutil.Process(proc.info['pid'])
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            
            print("未找到对应的进程")
            return None
            
        except Exception as e:
            print(f"查找Chrome进程时出错: {e}")
            return None
    
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
    
    def discover_external_browsers(self, profiles: list) -> Dict[str, Dict]:
        """发现外部启动的Chrome浏览器实例"""
        external_browsers = {}
        
        try:
            # 获取Chrome用户数据目录
            if platform.system() == "Darwin":  # macOS
                base_user_data_dir = os.path.expanduser("~/Library/Application Support/Google/Chrome")
            elif platform.system() == "Windows":
                base_user_data_dir = os.path.expanduser("~/AppData/Local/Google/Chrome/User Data")
            else:  # Linux
                base_user_data_dir = os.path.expanduser("~/.config/google-chrome")
            
            # 创建Profile名称到Profile对象的映射
            profile_map = {profile.name: profile for profile in profiles}
            
            # 遍历所有Chrome进程
            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time']):
                try:
                    if not proc.info['name']:
                        continue
                    
                    process_name = proc.info['name'].lower()
                    # 识别Google Chrome主进程
                    if proc.info['name'] != 'Google Chrome':
                        continue
                    
                    cmdline = proc.info['cmdline']
                    if not cmdline:
                        continue
                    
                    cmdline_str = ' '.join(cmdline)
                    
                    # 跳过子进程（Helper, GPU等）
                    if any(skip_type in cmdline_str for skip_type in ['--type=', 'Helper', 'GPU', 'Renderer', 'Plugin']):
                        continue
                    
                    # 检查命令行中是否指定了特定的Profile
                    profile_name = "Default"  # 默认值
                    
                    # 查找--profile-directory参数
                    import re
                    profile_match = re.search(r'--profile-directory[=\s]+"?([^"\s]+)"?', cmdline_str)
                    if profile_match:
                        profile_name = profile_match.group(1)
                    
                    # 对于macOS，如果只找到简单的Chrome启动命令
                    if len(cmdline) == 1 and cmdline[0].endswith('Google Chrome'):
                        # 假设正在使用Default Profile（在Chrome中通常对应最后一次使用的Profile）
                        # 我们可以根据实际需要调整这个逻辑
                        profile_name = "Default"
                        
                        # 检查是否已经在运行实例中
                        if profile_name not in self.running_instances:
                            self._create_browser_instance(profile_name, proc.info, external_browsers, base_user_data_dir, cmdline)
                    else:
                        # 有明确指定Profile的情况
                        if profile_name in profile_map and profile_name not in self.running_instances:
                            self._create_browser_instance(profile_name, proc.info, external_browsers, base_user_data_dir, cmdline)
                
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
                except Exception as e:
                    continue
        
        except Exception as e:
            print(f"发现外部浏览器时出错: {e}")
        
        return external_browsers
    
    def _create_browser_instance(self, profile_name: str, proc_info: dict, external_browsers: dict, base_user_data_dir: str, cmdline: list):
        """创建浏览器实例"""
        # 检查是否已经在我们的运行实例中（避免重复添加）
        if profile_name in self.running_instances:
            return
        
        # 获取进程对象
        process = psutil.Process(proc_info['pid'])
        
        # 创建浏览器实例信息
        browser_instance = BrowserInstance(
            profile_name=profile_name,
            process_id=proc_info['pid'],
            process=process,
            start_time=proc_info['create_time'],
            user_data_dir=base_user_data_dir,
            command_line=cmdline
        )
        
        # 添加到运行实例中（这样就可以管理外部启动的浏览器了）
        self.running_instances[profile_name] = browser_instance
        
        # 获取浏览器信息
        try:
            memory_info = process.memory_info()
            external_browsers[profile_name] = {
                'pid': proc_info['pid'],
                'start_time': proc_info['create_time'],
                'memory_usage': memory_info.rss,
                'memory_percent': process.memory_percent(),
                'cpu_percent': 0.0,  # 初始CPU使用率为0
                'status': process.status(),
                'command_line': cmdline,
                'discovered': True  # 标记为外部发现的
            }
            
            print(f"发现外部Chrome实例: {profile_name} (PID: {proc_info['pid']})")
            
        except Exception as e:
            print(f"获取外部浏览器进程信息时出错: {e}")
    
    def get_all_running_browsers(self, profiles: list = None) -> Dict[str, Dict]:
        """获取所有运行中的浏览器信息（包括外部启动的）"""
        running_browsers = {}
        
        # 首先发现外部启动的浏览器（如果提供了profiles列表）
        if profiles:
            external_browsers = self.discover_external_browsers(profiles)
            running_browsers.update(external_browsers)
        
        # 检查并清理已经停止的实例
        stopped_profiles = []
        for profile_name in list(self.running_instances.keys()):
            instance = self.running_instances[profile_name]
            try:
                # 检查进程是否还存在并运行
                if not instance.process.is_running():
                    print(f"检测到浏览器进程已停止: {profile_name} (PID: {instance.process_id})")
                    stopped_profiles.append(profile_name)
                else:
                    # 进程存在，获取其信息
                    browser_info = self.get_browser_info(profile_name)
                    if browser_info:
                        running_browsers[profile_name] = browser_info
                    else:
                        # 无法获取进程信息，可能进程已经结束
                        print(f"无法获取浏览器进程信息，可能已停止: {profile_name} (PID: {instance.process_id})")
                        stopped_profiles.append(profile_name)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                # 进程已经不存在
                print(f"浏览器进程不存在: {profile_name} (PID: {instance.process_id})")
                stopped_profiles.append(profile_name)
            except Exception as e:
                print(f"检查浏览器进程状态时出错: {profile_name} - {e}")
                stopped_profiles.append(profile_name)
        
        # 清理已停止的进程
        for profile_name in stopped_profiles:
            if profile_name in self.running_instances:
                del self.running_instances[profile_name]
                print(f"已清理停止的浏览器实例: {profile_name}")
        
        return running_browsers
    
    def check_and_cleanup_stopped_browsers(self) -> list:
        """检查并清理已停止的浏览器，返回停止的浏览器列表"""
        stopped_browsers = []
        
        for profile_name in list(self.running_instances.keys()):
            instance = self.running_instances[profile_name]
            try:
                if not instance.process.is_running():
                    stopped_browsers.append(profile_name)
                    del self.running_instances[profile_name]
                    print(f"清理已停止的浏览器: {profile_name} (PID: {instance.process_id})")
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                stopped_browsers.append(profile_name)
                del self.running_instances[profile_name]
                print(f"清理不存在的浏览器进程: {profile_name} (PID: {instance.process_id})")
            except Exception as e:
                print(f"检查浏览器进程时出错: {profile_name} - {e}")
        
        return stopped_browsers
    
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