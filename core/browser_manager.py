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
        
        # ✨ 关键修改：为每个Profile创建独立的用户数据目录
        # 这样可以确保多个Chrome实例完全独立运行
        original_user_data_dir = os.path.dirname(profile.path)
        independent_user_data_dir = os.path.join(
            os.path.dirname(original_user_data_dir), 
            f"Chrome_Instance_{profile.name}"
        )
        
        # 确保独立用户数据目录存在
        os.makedirs(independent_user_data_dir, exist_ok=True)
        
        # 复制原Profile到独立目录（如果还不存在）
        independent_profile_path = os.path.join(independent_user_data_dir, "Default")
        if not os.path.exists(independent_profile_path):
            import shutil
            try:
                if os.path.exists(profile.path):
                    shutil.copytree(profile.path, independent_profile_path)
                    print(f"已复制Profile数据: {profile.path} -> {independent_profile_path}")
                else:
                    # 创建基本的Profile目录结构
                    os.makedirs(independent_profile_path, exist_ok=True)
                    print(f"已创建新的Profile目录: {independent_profile_path}")
            except Exception as e:
                print(f"复制Profile数据时出错: {e}")
                # 继续执行，Chrome会创建默认的Profile
        
        # 使用独立的用户数据目录（无需指定profile-directory，因为我们复制到了Default）
        cmd.extend([f"--user-data-dir={independent_user_data_dir}"])
        
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
            
            # 使用直接调用Chrome可执行文件的方法（更可靠）
            if platform.system() == "Darwin":
                # macOS: 直接调用Chrome可执行文件
                process = subprocess.Popen(cmd, 
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
            
            # Chrome启动机制特殊：检查是否有Chrome进程在使用指定的独立用户数据目录
            chrome_started = self._check_chrome_running_for_independent_dir(profile, independent_user_data_dir)
            
            if chrome_started:
                # 找到运行中的Chrome进程
                running_process = self._find_chrome_process_for_independent_dir(profile, independent_user_data_dir)
                
                if running_process:
                    instance = BrowserInstance(
                        profile_name=profile.name,
                        process_id=running_process.pid,
                        process=running_process,
                        start_time=time.time(),
                        user_data_dir=independent_user_data_dir,  # 使用独立目录
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
    
    def _check_chrome_running_for_independent_dir(self, profile: ProfileInfo, independent_user_data_dir: str) -> bool:
        """检查是否有Chrome进程在使用指定的独立用户数据目录"""
        try:
            print(f"开始检查Chrome进程，独立用户数据目录: {independent_user_data_dir}")
            
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
                
                # 检查是否有进程使用我们的独立用户数据目录
                for proc_info in chrome_processes:
                    cmdline = proc_info['cmdline']
                    
                    # 检查独立用户数据目录
                    if independent_user_data_dir.replace(' ', '\\ ') in cmdline or independent_user_data_dir in cmdline:
                        # 确保这是主进程（不是Helper进程）
                        if '--type=' not in cmdline:
                            print(f"找到使用独立目录的Chrome进程: PID={proc_info['pid']}")
                            return True
                
                if attempt >= 4:  # 从第5次开始，检查更多进程
                    print("检查更多进程...")
                
            print("未找到匹配的Chrome进程")
            return False
            
        except Exception as e:
            print(f"检查Chrome进程时出错: {e}")
            return False
    
    def _find_chrome_process_for_independent_dir(self, profile: ProfileInfo, independent_user_data_dir: str) -> Optional[psutil.Process]:
        """查找使用指定独立用户数据目录的Chrome进程"""
        try:
            print(f"查找独立用户数据目录 {independent_user_data_dir} 对应的Chrome进程...")
            
            # 遍历所有Chrome进程
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['name'] == 'Google Chrome':
                        cmdline = proc.info['cmdline']
                        if cmdline:
                            cmdline_str = ' '.join(cmdline)
                            
                            # 检查独立用户数据目录
                            if independent_user_data_dir.replace(' ', '\\ ') in cmdline_str or independent_user_data_dir in cmdline_str:
                                # 确保这是主进程
                                if '--type=' not in cmdline_str:
                                    actual_proc = psutil.Process(proc.info['pid'])
                                    print(f"找到Profile {profile.name} 的进程: PID={proc.info['pid']}")
                                    return actual_proc
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            
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
        # 首先检查已知的运行实例
        if profile_name in self.running_instances:
            instance = self.running_instances[profile_name]
            try:
                # 检查进程是否还存在
                return instance.process.is_running()
            except psutil.NoSuchProcess:
                # 进程已经不存在，从列表中移除
                del self.running_instances[profile_name]
                return False
        
        # 如果在已知实例中没有找到，尝试发现外部启动的浏览器
        # 为了准确检测，我们需要获取profiles列表
        # 这里使用一个简化的检测方法，或者让调用者传入profiles
        return self._quick_check_external_browser_running(profile_name)
    
    def _quick_check_external_browser_running(self, profile_name: str) -> bool:
        """快速检查是否有外部Chrome进程在使用指定的Profile"""
        try:
            # ✨ 关键修复：检查独立用户数据目录
            # 这要与start_browser方法中使用的目录结构保持一致
            
            # 获取标准Chrome用户数据目录
            if platform.system() == "Darwin":  # macOS
                base_user_data_dir = os.path.expanduser("~/Library/Application Support/Google/Chrome")
            elif platform.system() == "Windows":
                base_user_data_dir = os.path.expanduser("~/AppData/Local/Google/Chrome/User Data")
            else:  # Linux
                base_user_data_dir = os.path.expanduser("~/.config/google-chrome")
            
            # 计算独立用户数据目录（与start_browser方法保持一致）
            independent_user_data_dir = os.path.join(
                os.path.dirname(base_user_data_dir), 
                f"Chrome_Instance_{profile_name}"
            )
            
            # 检查所有Chrome进程
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['name'] and 'chrome' in proc.info['name'].lower():
                        cmdline = proc.info['cmdline']
                        if not cmdline:
                            continue
                        
                        cmdline_str = ' '.join(cmdline)
                        
                        # 方法1：检查是否使用了我们的独立用户数据目录（新逻辑）
                        if independent_user_data_dir in cmdline_str:
                            # 确保这是主进程（不是Helper进程）
                            if '--type=' not in cmdline_str:
                                print(f"检测到Profile {profile_name}的独立实例在运行 (PID: {proc.info['pid']})")
                                return True
                        
                        # 方法2：检查标准Chrome Profile目录（兼容旧逻辑）
                        elif base_user_data_dir in cmdline_str:
                            # 检查Profile匹配
                            if profile_name == "Default":
                                # 对于Default Profile，不应该有--profile-directory参数
                                if '--profile-directory=' not in cmdline_str:
                                    return True
                            else:
                                # 对于其他Profile，检查是否匹配
                                # 使用多种方法检查
                                profile_patterns = [
                                    f'--profile-directory={profile_name}',
                                    f'--profile-directory="{profile_name}"',
                                ]
                                
                                for pattern in profile_patterns:
                                    if pattern in cmdline_str:
                                        return True
                                
                                # 使用命令行数组检查（更准确）
                                for i, arg in enumerate(cmdline):
                                    if arg == '--profile-directory' and i + 1 < len(cmdline):
                                        if cmdline[i + 1] == profile_name:
                                            return True
                                    elif arg.startswith('--profile-directory='):
                                        extracted_profile = arg.split('=', 1)[1]
                                        if extracted_profile == profile_name:
                                            return True
                
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            
            return False
            
        except Exception as e:
            print(f"快速检查外部浏览器时出错: {e}")
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
            
            # 收集所有Chrome主进程
            chrome_main_processes = []
            
            # 遍历所有Chrome进程
            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time']):
                try:
                    if not proc.info['name']:
                        continue
                    
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
                    
                    chrome_main_processes.append({
                        'proc_info': proc.info,
                        'cmdline': cmdline,
                        'cmdline_str': cmdline_str
                    })
                
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
                except Exception as e:
                    continue
            
            # print(f"发现 {len(chrome_main_processes)} 个Chrome主进程")
            
            # 处理每个Chrome主进程
            for chrome_proc in chrome_main_processes:
                proc_info = chrome_proc['proc_info']
                cmdline = chrome_proc['cmdline']
                cmdline_str = chrome_proc['cmdline_str']
                
                # 查找--profile-directory参数
                profile_name = None
                
                # 方法1：从命令行参数数组中直接查找（最可靠）
                for i, arg in enumerate(cmdline):
                    if arg == '--profile-directory' and i + 1 < len(cmdline):
                        profile_name = cmdline[i + 1]
                        print(f"从命令行参数中找到Profile: {profile_name} (PID: {proc_info['pid']})")
                        break
                    elif arg.startswith('--profile-directory='):
                        profile_name = arg.split('=', 1)[1]
                        print(f"从命令行参数中找到Profile: {profile_name} (PID: {proc_info['pid']})")
                        break
                
                # 方法2：如果上面没找到，尝试正则表达式（备用）
                if not profile_name:
                    import re
                    # 使用改进的正则表达式，能正确处理包含空格的Profile名称
                    profile_match = re.search(r'--profile-directory=(.+?)(?:\s--|\s-[^-]|$)', cmdline_str)
                    if profile_match:
                        profile_name = profile_match.group(1).strip()
                        print(f"通过正则表达式找到Profile: {profile_name} (PID: {proc_info['pid']})")
                
                if profile_name:
                    print(f"✅ 最终识别的Profile: {profile_name} (PID: {proc_info['pid']})")
                # 如果以上都没有匹配到，尝试从cmdline数组中直接提取
                elif '--profile-directory' in cmdline_str:
                    try:
                        # 从命令行参数数组中查找
                        for i, arg in enumerate(cmdline):
                            if arg == '--profile-directory' and i + 1 < len(cmdline):
                                profile_name = cmdline[i + 1]
                                print(f"从命令行参数中找到Profile: {profile_name} (PID: {proc_info['pid']})")
                                break
                            elif arg.startswith('--profile-directory='):
                                profile_name = arg.split('=', 1)[1]
                                print(f"从命令行参数中找到Profile: {profile_name} (PID: {proc_info['pid']})")
                                break
                    except:
                        pass
                
                # 对于macOS上的简单Chrome启动（没有明确Profile参数）
                elif len(cmdline) == 1 and cmdline[0].endswith('Google Chrome'):
                    print(f"发现简单Chrome启动 (PID: {proc_info['pid']})，需要智能匹配Profile")
                    
                    # 智能推测正在使用的Profile
                    profile_name = self._guess_profile_for_simple_chrome(proc_info['pid'], profiles, external_browsers)
                    
                    if profile_name:
                        print(f"推测Chrome进程 {proc_info['pid']} 正在使用Profile: {profile_name}")
                    else:
                        print(f"无法推测Chrome进程 {proc_info['pid']} 的Profile，跳过")
                        continue
                
                # 如果找到了有效的Profile名称，且该Profile存在，且未被检测
                if profile_name and profile_name in profile_map and profile_name not in self.running_instances:
                    self._create_browser_instance(profile_name, proc_info, external_browsers, base_user_data_dir, cmdline)
        
        except Exception as e:
            print(f"发现外部浏览器时出错: {e}")
        
        return external_browsers
    
    def _guess_profile_for_simple_chrome(self, chrome_pid: int, profiles: list, already_detected: dict) -> str:
        """
        智能推测简单Chrome启动使用的Profile
        通过检查Chrome进程打开的文件来推测正在使用的Profile
        """
        try:
            import psutil
            import os
            
            # 获取Chrome进程对象
            chrome_process = psutil.Process(chrome_pid)
            
            # 尝试通过打开的文件推测Profile
            try:
                open_files = chrome_process.open_files()
                
                # 分析打开的文件路径
                chrome_data_dir = os.path.expanduser("~/Library/Application Support/Google/Chrome")
                
                for file_info in open_files:
                    file_path = file_info.path
                    
                    # 检查是否是Chrome Profile相关的文件
                    if chrome_data_dir in file_path:
                        # 提取Profile目录名
                        relative_path = file_path.replace(chrome_data_dir, '').lstrip('/')
                        
                        # 检查路径格式，例如: "Profile 3/Preferences" 或 "Default/Preferences"
                        path_parts = relative_path.split('/')
                        if len(path_parts) >= 2:
                            potential_profile = path_parts[0]
                            
                            # 验证这是否是一个已知的Profile
                            for profile in profiles:
                                if profile.name == potential_profile:
                                    # 确保这个Profile还没有被检测到
                                    if potential_profile not in already_detected:
                                        print(f"通过文件路径匹配到Profile: {potential_profile} (文件: {file_path})")
                                        return potential_profile
                
            except (psutil.AccessDenied, OSError):
                # 如果无法访问文件列表，使用备用方法
                pass
            
            # 备用方法：按创建时间顺序分配给未检测的Profile
            # 这里我们假设Chrome实例按启动顺序对应Profile顺序
            available_profiles = []
            for profile in profiles:
                if profile.name not in already_detected and profile.name not in self.running_instances:
                    available_profiles.append(profile)
            
            if available_profiles:
                # 按Profile名称排序，优先分配Default，然后按数字顺序
                available_profiles.sort(key=lambda p: (p.name != "Default", p.name))
                selected_profile = available_profiles[0]
                print(f"使用备用方法分配Profile: {selected_profile.name}")
                return selected_profile.name
            
            return None
            
        except Exception as e:
            print(f"推测Profile时出错: {e}")
            return None
    
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