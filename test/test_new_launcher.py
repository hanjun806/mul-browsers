#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试新的多实例启动机制
"""

from core.browser_manager import BrowserManager
from core.profile_manager import ProfileManager
import time

def test_multi_instance_launch():
    print("=== 测试新的多实例启动机制 ===")
    
    # 创建管理器
    bm = BrowserManager()
    pm = ProfileManager()
    
    # 获取Profile列表
    profiles = pm.scan_profiles()
    print('可用的Profile:')
    for i, profile in enumerate(profiles):
        print(f'  {i+1}. {profile.display_name} ({profile.name})')
    
    if len(profiles) < 2:
        print('需要至少2个Profile来测试多实例启动')
        return
    
    # 测试启动第一个Profile
    print(f'\n=== 启动第一个Profile: {profiles[0].display_name} ===')
    success1 = bm.start_browser(profiles[0], language='zh-CN', window_size=(1280, 720))
    print(f'第一个Profile启动结果: {"成功" if success1 else "失败"}')
    
    if success1:
        print(f'当前运行的实例: {list(bm.running_instances.keys())}')
        
        # 等待一点时间
        print('\n等待5秒后启动第二个Profile...')
        time.sleep(5)
        
        # 测试启动第二个Profile
        print(f'\n=== 启动第二个Profile: {profiles[1].display_name} ===')
        success2 = bm.start_browser(profiles[1], language='zh-CN', window_size=(1280, 720))
        print(f'第二个Profile启动结果: {"成功" if success2 else "失败"}')
        
        print(f'\n最终运行的实例: {list(bm.running_instances.keys())}')
        
        # 检查实际的Chrome进程
        print('\n=== 检查实际Chrome进程 ===')
        import psutil
        chrome_processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['name'] == 'Google Chrome':
                    cmdline = proc.info['cmdline']
                    if cmdline and not any('--type=' in arg for arg in cmdline):
                        chrome_processes.append({
                            'pid': proc.info['pid'],
                            'cmdline': ' '.join(cmdline)
                        })
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        
        # print(f'发现 {len(chrome_processes)} 个Chrome主进程:')
        for i, proc in enumerate(chrome_processes, 1):
            print(f'  {i}. PID: {proc["pid"]}')
            # 提取用户数据目录
            cmdline = proc['cmdline']
            if '--user-data-dir=' in cmdline:
                start = cmdline.find('--user-data-dir=') + len('--user-data-dir=')
                end = cmdline.find(' ', start)
                if end == -1:
                    end = len(cmdline)
                user_data_dir = cmdline[start:end]
                print(f'     用户数据目录: {user_data_dir}')
        
        if len(chrome_processes) >= 2:
            print('\n✅ 成功启动了多个独立的Chrome实例！')
        else:
            print('\n❌ 仍然只有一个Chrome实例在运行')
    
    else:
        print('第一个Profile启动失败，无法继续测试')

if __name__ == "__main__":
    test_multi_instance_launch() 