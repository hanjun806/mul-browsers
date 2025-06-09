#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试浏览器状态检测功能
"""

import time
from core.browser_manager import BrowserManager
from core.profile_manager import ProfileManager

def test_browser_detection():
    """测试浏览器检测功能"""
    
    print("=== 浏览器状态检测测试 ===")
    
    # 初始化管理器
    browser_manager = BrowserManager()
    profile_manager = ProfileManager()
    
    print(f"Chrome可执行文件: {browser_manager.chrome_executable}")
    
    # 扫描profiles
    profiles = profile_manager.scan_profiles()
    print(f"找到 {len(profiles)} 个Profile:")
    for profile in profiles:
        print(f"  - {profile.display_name} ({profile.name})")
    
    print("\n=== 当前运行状态 ===")
    running_browsers = browser_manager.get_all_running_browsers()
    print(f"运行中的浏览器: {len(running_browsers)}")
    for name, info in running_browsers.items():
        print(f"  - {name}: PID={info['pid']}, 内存={info['memory_usage']/(1024*1024):.1f}MB")
    
    print("\n=== 开始监控模式 ===")
    print("手动关闭浏览器窗口，观察检测结果...")
    print("按 Ctrl+C 退出监控")
    
    try:
        while True:
            # 检查状态变化
            stopped_browsers = browser_manager.check_and_cleanup_stopped_browsers()
            
            if stopped_browsers:
                print(f"\n🔴 检测到浏览器关闭: {stopped_browsers}")
                
                # 显示当前状态
                current_running = browser_manager.get_all_running_browsers()
                print(f"   当前运行中: {len(current_running)} 个")
                for name, info in current_running.items():
                    print(f"     - {name}: PID={info['pid']}")
            
            time.sleep(2)  # 每2秒检查一次
            
    except KeyboardInterrupt:
        print("\n\n监控已停止")
        
        # 最终状态
        final_running = browser_manager.get_all_running_browsers()
        print(f"最终运行中的浏览器: {len(final_running)} 个")

if __name__ == "__main__":
    test_browser_detection() 