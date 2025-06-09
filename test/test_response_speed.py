#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试界面响应速度改进
验证当浏览器被外部关闭时，GUI的响应时间
"""

import time
import psutil
from core.browser_manager import BrowserManager
from core.profile_manager import ProfileManager

def test_response_speed():
    """测试响应速度"""
    print("=== 测试界面响应速度改进 ===")
    
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
    
    # 启动浏览器
    print("1. 启动浏览器...")
    success = bm.start_browser(profile, language='zh-CN', window_size=(1280, 720))
    
    if not success:
        print("启动失败")
        return
    
    print("✅ 浏览器启动成功")
    time.sleep(3)
    
    # 检查当前状态
    print("2. 检查当前状态...")
    is_running_before = bm.is_browser_running(profile.name)
    print(f"运行状态: {'运行中' if is_running_before else '未运行'}")
    
    if not is_running_before:
        print("❌ 浏览器未在运行")
        return
    
    # 获取Chrome进程PID
    instance = bm.running_instances.get(profile.name)
    if not instance:
        print("❌ 未找到浏览器实例")
        return
    
    chrome_pid = instance.process_id
    print(f"Chrome PID: {chrome_pid}")
    
    # 模拟用户外部关闭浏览器
    print("3. 模拟外部关闭浏览器...")
    try:
        chrome_process = psutil.Process(chrome_pid)
        chrome_process.terminate()
        print(f"✅ 已向Chrome进程 {chrome_pid} 发送终止信号")
    except Exception as e:
        print(f"❌ 终止进程失败: {e}")
        return
    
    # 等待进程真正结束
    print("4. 等待进程结束...")
    wait_time = 0
    max_wait = 10  # 最多等待10秒
    
    while wait_time < max_wait:
        try:
            if not chrome_process.is_running():
                print(f"✅ Chrome进程已结束 (等待时间: {wait_time:.1f}秒)")
                break
        except psutil.NoSuchProcess:
            print(f"✅ Chrome进程已结束 (等待时间: {wait_time:.1f}秒)")
            break
        
        time.sleep(0.1)
        wait_time += 0.1
    
    if wait_time >= max_wait:
        print("❌ Chrome进程未在预期时间内结束")
        return
    
    # 测试检测速度
    print("5. 测试检测速度...")
    detection_start = time.time()
    
    # 循环检查直到系统检测到浏览器已关闭
    max_detection_time = 2.0  # 最多等待2秒
    detected = False
    
    while (time.time() - detection_start) < max_detection_time:
        # 调用check_and_cleanup_stopped_browsers方法
        stopped_browsers = bm.check_and_cleanup_stopped_browsers()
        
        if stopped_browsers and profile.name in stopped_browsers:
            detection_time = time.time() - detection_start
            print(f"✅ 检测到浏览器关闭 (检测时间: {detection_time:.2f}秒)")
            detected = True
            break
        
        # 或者检查is_browser_running状态
        if not bm.is_browser_running(profile.name):
            detection_time = time.time() - detection_start
            print(f"✅ 状态检查检测到关闭 (检测时间: {detection_time:.2f}秒)")
            detected = True
            break
        
        time.sleep(0.1)  # 每100ms检查一次
    
    if detected:
        if detection_time < 0.5:
            print("🎉 响应速度: 极快 (< 0.5秒)")
        elif detection_time < 1.0:
            print("✅ 响应速度: 快 (< 1秒)")
        elif detection_time < 2.0:
            print("⚠️  响应速度: 一般 (< 2秒)")
        else:
            print("❌ 响应速度: 慢 (>= 2秒)")
    else:
        print("❌ 检测失败：系统未能在2秒内检测到浏览器关闭")
    
    # 最终状态确认
    print("6. 最终状态确认...")
    final_status = bm.is_browser_running(profile.name)
    running_instances = list(bm.running_instances.keys())
    
    print(f"最终运行状态: {'运行中' if final_status else '未运行'}")
    print(f"运行实例列表: {running_instances}")
    
    if not final_status and profile.name not in running_instances:
        print("✅ 状态正确：浏览器已完全清理")
    else:
        print("❌ 状态错误：浏览器状态不一致")

def main():
    print("GUI响应速度测试")
    print("=" * 30)
    
    try:
        test_response_speed()
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 