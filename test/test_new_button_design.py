#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试新的切换按钮设计
验证启动/关闭合并按钮是否正常工作
"""

import time
from core.browser_manager import BrowserManager
from core.profile_manager import ProfileManager

def test_new_button_design():
    """测试新的按钮设计"""
    print("=== 测试新的切换按钮设计 ===")
    
    # 创建管理器
    bm = BrowserManager()
    pm = ProfileManager()
    
    # 获取Profile列表
    profiles = pm.scan_profiles()
    if not profiles:
        print("没有找到Profile")
        return
    
    profile = profiles[0]
    print(f"使用Profile: {profile.display_name}")
    
    print("\n1. 测试启动功能...")
    
    # 检查初始状态
    is_running_before = bm.is_browser_running(profile.name)
    print(f"启动前状态: {'运行中' if is_running_before else '未运行'}")
    
    if not is_running_before:
        # 测试启动
        print("执行启动操作...")
        success = bm.start_browser(profile, language='zh-CN', window_size=(1280, 720))
        
        if success:
            print("✅ 启动成功")
            time.sleep(2)  # 等待浏览器启动
            
            # 验证状态
            is_running_after = bm.is_browser_running(profile.name)
            print(f"启动后状态: {'运行中' if is_running_after else '未运行'}")
            
            if is_running_after:
                print("\n2. 测试关闭功能...")
                
                # 测试关闭
                print("执行关闭操作...")
                close_success = bm.close_browser(profile.name)
                
                if close_success:
                    print("✅ 关闭成功")
                    time.sleep(1)  # 等待关闭完成
                    
                    # 验证状态
                    is_running_final = bm.is_browser_running(profile.name)
                    print(f"关闭后状态: {'运行中' if is_running_final else '未运行'}")
                    
                    if not is_running_final:
                        print("\n🎉 切换按钮功能测试成功！")
                        print("- 启动功能: ✅")
                        print("- 关闭功能: ✅")
                        print("- 状态检测: ✅")
                    else:
                        print("\n❌ 关闭功能测试失败")
                else:
                    print("❌ 关闭操作失败")
            else:
                print("❌ 启动状态验证失败")
        else:
            print("❌ 启动操作失败")
    else:
        print("Profile已在运行中，先关闭再测试")
        bm.close_browser(profile.name)
        time.sleep(2)
        test_new_button_design()  # 递归重试

if __name__ == "__main__":
    test_new_button_design() 