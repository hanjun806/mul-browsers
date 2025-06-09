#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Chrome进程检测诊断脚本
用于诊断为什么检测机制无法识别已运行的浏览器
"""

import psutil
import os
import platform
from core.browser_manager import BrowserManager
from core.profile_manager import ProfileManager

def debug_chrome_processes():
    """详细分析所有Chrome相关进程"""
    print("=== Chrome进程诊断 ===")
    print(f"操作系统: {platform.system()}")
    
    # 获取Chrome用户数据目录
    if platform.system() == "Darwin":  # macOS
        base_user_data_dir = os.path.expanduser("~/Library/Application Support/Google/Chrome")
    elif platform.system() == "Windows":
        base_user_data_dir = os.path.expanduser("~/AppData/Local/Google/Chrome/User Data")
    else:  # Linux
        base_user_data_dir = os.path.expanduser("~/.config/google-chrome")
    
    print(f"Chrome用户数据目录: {base_user_data_dir}")
    print()
    
    # 收集所有可能的Chrome进程
    chrome_processes = []
    all_processes = []
    
    print("=== 扫描所有进程 ===")
    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time']):
        try:
            if not proc.info['name']:
                continue
                
            process_name = proc.info['name'].lower()
            
            # 收集所有进程信息用于分析
            all_processes.append({
                'pid': proc.info['pid'],
                'name': proc.info['name'],
                'cmdline': proc.info['cmdline'] or []
            })
            
            # 识别Chrome相关进程（更宽泛的匹配）
            if any(keyword in process_name for keyword in ['chrome', 'google']):
                cmdline = proc.info['cmdline'] or []
                cmdline_str = ' '.join(cmdline) if cmdline else ''
                
                chrome_processes.append({
                    'pid': proc.info['pid'],
                    'name': proc.info['name'],
                    'cmdline': cmdline,
                    'cmdline_str': cmdline_str,
                    'create_time': proc.info['create_time']
                })
                
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    
    print(f"找到 {len(chrome_processes)} 个Chrome相关进程:")
    print()
    
    # 详细分析每个Chrome进程
    main_processes = []
    helper_processes = []
    
    for i, proc_info in enumerate(chrome_processes):
        print(f"进程 {i+1}:")
        print(f"  PID: {proc_info['pid']}")
        print(f"  名称: {proc_info['name']}")
        print(f"  命令行参数数量: {len(proc_info['cmdline'])}")
        
        if proc_info['cmdline']:
            print(f"  完整命令行: {proc_info['cmdline_str']}")
            
            # 分析是否是主进程还是子进程
            is_helper = any(helper_type in proc_info['cmdline_str'] for helper_type in 
                          ['--type=', 'Helper', 'GPU', 'Renderer', 'Plugin', 'Utility'])
            
            if is_helper:
                helper_processes.append(proc_info)
                print(f"  类型: 子进程/Helper")
            else:
                main_processes.append(proc_info)
                print(f"  类型: 主进程")
                
                # 分析Profile信息
                if '--user-data-dir=' in proc_info['cmdline_str']:
                    import re
                    user_data_match = re.search(r'--user-data-dir=([^\s]+)', proc_info['cmdline_str'])
                    if user_data_match:
                        user_data_path = user_data_match.group(1)
                        print(f"  用户数据目录: {user_data_path}")
                
                if '--profile-directory=' in proc_info['cmdline_str']:
                    import re
                    profile_match = re.search(r'--profile-directory=([^\s]+)', proc_info['cmdline_str'])
                    if profile_match:
                        profile_name = profile_match.group(1)
                        print(f"  Profile目录: {profile_name}")
                    else:
                        print(f"  Profile目录: Default (未指定)")
                else:
                    print(f"  Profile目录: Default (默认)")
        else:
            print(f"  命令行: 空")
            # 对于macOS上的简单Chrome启动
            if proc_info['name'] == 'Google Chrome':
                main_processes.append(proc_info)
                print(f"  类型: 主进程 (简单启动)")
                print(f"  Profile目录: Default (推测)")
        
        print()
    
    print(f"=== 分析结果 ===")
    print(f"总Chrome进程数: {len(chrome_processes)}")
    print(f"主进程数: {len(main_processes)}")
    print(f"子进程数: {len(helper_processes)}")
    print()
    
    # 测试当前的检测逻辑
    print("=== 测试当前检测逻辑 ===")
    browser_manager = BrowserManager()
    profile_manager = ProfileManager()
    
    profiles = profile_manager.scan_profiles()
    print(f"找到 {len(profiles)} 个Profile")
    
    # 测试discover_external_browsers方法
    external_browsers = browser_manager.discover_external_browsers(profiles)
    print(f"discover_external_browsers检测到: {len(external_browsers)} 个")
    for name, info in external_browsers.items():
        print(f"  - {name}: PID={info['pid']}")
    
    # 测试get_all_running_browsers方法
    all_running = browser_manager.get_all_running_browsers(profiles)
    print(f"get_all_running_browsers检测到: {len(all_running)} 个")
    for name, info in all_running.items():
        print(f"  - {name}: PID={info['pid']}")
    
    print()
    
    # 分析为什么检测失败
    print("=== 检测失败原因分析 ===")
    
    if len(main_processes) > 0 and len(external_browsers) == 0:
        print("发现主进程但未被检测到，可能的原因:")
        
        for proc in main_processes:
            print(f"\n分析进程 PID {proc['pid']}:")
            
            # 检查进程名匹配
            if proc['name'] != 'Google Chrome':
                print(f"  ❌ 进程名不匹配: '{proc['name']}' != 'Google Chrome'")
            else:
                print(f"  ✅ 进程名匹配: '{proc['name']}'")
            
            # 检查命令行匹配
            if not proc['cmdline']:
                print(f"  ⚠️  空命令行，可能是简单启动")
            else:
                cmdline_str = proc['cmdline_str']
                
                # 检查是否包含用户数据目录
                if base_user_data_dir in cmdline_str:
                    print(f"  ✅ 包含用户数据目录")
                else:
                    print(f"  ❌ 不包含用户数据目录")
                    print(f"      期望: {base_user_data_dir}")
                    print(f"      实际: {cmdline_str}")
                
                # 检查是否是子进程
                if any(skip_type in cmdline_str for skip_type in ['--type=', 'Helper', 'GPU', 'Renderer', 'Plugin']):
                    print(f"  ❌ 被识别为子进程")
                else:
                    print(f"  ✅ 不是子进程")

if __name__ == "__main__":
    debug_chrome_processes() 