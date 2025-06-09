#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试GUI启动问题的脚本
模拟GUI程序的启动流程，验证修复效果
"""

import time
from core.browser_manager import BrowserManager
from core.profile_manager import ProfileManager

def test_gui_startup_flow():
    """测试GUI启动流程"""
    print("=== 测试GUI启动流程 ===")
    
    # 创建管理器（模拟GUI初始化）
    bm = BrowserManager()
    pm = ProfileManager()
    
    # 获取Profile列表
    profiles = pm.scan_profiles()
    print(f"发现 {len(profiles)} 个Profile")
    
    if len(profiles) < 2:
        print("需要至少2个Profile来测试")
        return
    
    # 选择前两个Profile进行测试
    profile1 = profiles[0]
    profile2 = profiles[1]
    
    print(f"\n=== 测试Profile 1: {profile1.display_name} ===")
    
    # 步骤1：GUI程序首先检查是否已经在运行
    print("1. 检查Profile是否已在运行...")
    is_running_before = bm.is_browser_running(profile1.name)
    print(f"   检查结果: {'是' if is_running_before else '否'}")
    
    if is_running_before:
        print("   ❌ GUI会显示'浏览器已在运行中'，不会启动")
        return
    else:
        print("   ✅ 可以启动")
    
    # 步骤2：启动第一个Profile
    print("2. 启动第一个Profile...")
    success1 = bm.start_browser(profile1, language='zh-CN', window_size=(1280, 720))
    print(f"   启动结果: {'成功' if success1 else '失败'}")
    
    if not success1:
        print("   ❌ 第一个Profile启动失败")
        return
    
    # 步骤3：等待一段时间
    print("3. 等待3秒...")
    time.sleep(3)
    
    print(f"\n=== 测试Profile 2: {profile2.display_name} ===")
    
    # 步骤4：检查第二个Profile是否在运行（这里应该返回False）
    print("4. 检查第二个Profile是否已在运行...")
    is_running_profile2 = bm.is_browser_running(profile2.name)
    print(f"   检查结果: {'是' if is_running_profile2 else '否'}")
    
    if is_running_profile2:
        print("   ❌ GUI会误认为Profile 2已在运行，不会启动")
        print("   这就是bug的原因！")
        
        # 让我们详细分析一下为什么会误报
        print("\n=== 详细诊断 ===")
        print("检查当前的Chrome进程...")
        
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
        
        for i, proc in enumerate(chrome_processes, 1):
            print(f"Chrome进程 {i}:")
            print(f"  PID: {proc['pid']}")
            # 提取用户数据目录
            cmdline = proc['cmdline']
            if '--user-data-dir=' in cmdline:
                start = cmdline.find('--user-data-dir=') + len('--user-data-dir=')
                end = cmdline.find(' ', start)
                if end == -1:
                    end = len(cmdline)
                user_data_dir = cmdline[start:end]
                print(f"  用户数据目录: {user_data_dir}")
            print()
        
        return
    else:
        print("   ✅ 可以启动第二个Profile")
    
    # 步骤5：启动第二个Profile
    print("5. 启动第二个Profile...")
    success2 = bm.start_browser(profile2, language='zh-CN', window_size=(1280, 720))
    print(f"   启动结果: {'成功' if success2 else '失败'}")
    
    if success2:
        print("   ✅ 第二个Profile启动成功！问题已修复！")
        
        # 显示最终状态
        print("\n=== 最终状态 ===")
        running_instances = list(bm.running_instances.keys())
        print(f"Browser Manager中的运行实例: {running_instances}")
        
        # 检查实际Chrome进程
        import psutil
        chrome_count = 0
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['name'] == 'Google Chrome':
                    cmdline = proc.info['cmdline']
                    if cmdline and not any('--type=' in arg for arg in cmdline):
                        chrome_count += 1
            except:
                continue
        
        print(f"实际Chrome主进程数: {chrome_count}")
        
        if chrome_count >= 2:
            print("✅ 成功启动了多个独立的Chrome实例！GUI问题已修复！")
        else:
            print("❌ 仍然只有一个Chrome实例")
    else:
        print("   ❌ 第二个Profile启动失败")

def main():
    print("GUI启动问题修复验证")
    print("=" * 30)
    
    try:
        test_gui_startup_flow()
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 