#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试多种Chrome启动方法
"""

import subprocess
import time
import psutil
import os

def get_chrome_processes():
    """获取Chrome主进程"""
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
    return chrome_processes

def extract_profile_from_cmdline(cmdline_list):
    """从命令行中提取Profile名称"""
    for i, arg in enumerate(cmdline_list):
        if arg == '--profile-directory' and i + 1 < len(cmdline_list):
            return cmdline_list[i + 1]
        elif arg.startswith('--profile-directory='):
            return arg.split('=', 1)[1]
    return "Default"

print("=== 测试多种Chrome启动方法 ===")

print("1. 检查当前Chrome进程:")
initial_processes = get_chrome_processes()
for proc in initial_processes:
    cmdline_list = proc['cmdline'].split()
    profile = extract_profile_from_cmdline(cmdline_list)
    print(f"   PID: {proc['pid']}, Profile: {profile}")

print(f"当前Chrome主进程数: {len(initial_processes)}")

# 方法1：直接调用Chrome可执行文件
print("\n2. 方法1: 直接调用Chrome可执行文件...")

chrome_executable = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
user_data_dir = "/Users/zmj/Library/Application Support/Google/Chrome"

cmd1 = [
    chrome_executable,
    f"--user-data-dir={user_data_dir}",
    "--profile-directory=Profile 2",
    "--lang=zh-CN",
    "--window-size=1280,720",
    "--no-first-run",
    "--no-default-browser-check",
    "--new-window"
]

print(f"启动命令: {' '.join(cmd1)}")

try:
    process1 = subprocess.Popen(cmd1, 
                               stdout=subprocess.PIPE, 
                               stderr=subprocess.PIPE,
                               start_new_session=True)
    
    print(f"启动进程PID: {process1.pid}")
    
    # 等待Chrome启动
    print("等待Chrome启动...")
    for i in range(8):
        time.sleep(1)
        current_processes = get_chrome_processes()
        
        print(f"第{i+1}次检查: 找到{len(current_processes)}个Chrome主进程")
        
        for proc in current_processes:
            cmdline_list = proc['cmdline'].split()
            profile = extract_profile_from_cmdline(cmdline_list)
            is_new = proc['pid'] not in [p['pid'] for p in initial_processes]
            marker = " [新]" if is_new else ""
            print(f"   PID: {proc['pid']}, Profile: {profile}{marker}")
        
        # 检查启动进程状态
        try:
            poll_result = process1.poll()
            if poll_result is not None:
                stdout, stderr = process1.communicate()
                print(f"启动进程已退出，返回码: {poll_result}")
                if stdout:
                    print(f"stdout: {stdout.decode()}")
                if stderr:
                    print(f"stderr: {stderr.decode()}")
                break
        except:
            pass
        
        print()

except Exception as e:
    print(f"方法1启动失败: {e}")

# 方法2：使用不同的用户数据目录
print("\n3. 方法2: 使用独立的用户数据目录...")

temp_user_data_dir = "/tmp/chrome_profile2_test"
cmd2 = [
    chrome_executable,
    f"--user-data-dir={temp_user_data_dir}",
    "--lang=zh-CN",
    "--window-size=1280,720",
    "--no-first-run",
    "--no-default-browser-check",
    "--new-window"
]

print(f"启动命令: {' '.join(cmd2)}")

try:
    process2 = subprocess.Popen(cmd2, 
                               stdout=subprocess.PIPE, 
                               stderr=subprocess.PIPE,
                               start_new_session=True)
    
    print(f"启动进程PID: {process2.pid}")
    
    # 等待Chrome启动
    print("等待Chrome启动...")
    for i in range(5):
        time.sleep(1)
        current_processes = get_chrome_processes()
        
        print(f"第{i+1}次检查: 找到{len(current_processes)}个Chrome主进程")
        
        for proc in current_processes:
            cmdline_list = proc['cmdline'].split()
            profile = extract_profile_from_cmdline(cmdline_list)
            user_data = "temp" if temp_user_data_dir in proc['cmdline'] else "normal"
            is_new = proc['pid'] not in [p['pid'] for p in initial_processes]
            marker = " [新]" if is_new else ""
            print(f"   PID: {proc['pid']}, Profile: {profile}, 数据目录: {user_data}{marker}")
        
        # 检查启动进程状态
        try:
            poll_result = process2.poll()
            if poll_result is not None:
                stdout, stderr = process2.communicate()
                print(f"启动进程已退出，返回码: {poll_result}")
                if stdout:
                    print(f"stdout: {stdout.decode()}")
                if stderr:
                    print(f"stderr: {stderr.decode()}")
                break
        except:
            pass
        
        print()

except Exception as e:
    print(f"方法2启动失败: {e}")

print("\n4. 最终状态:")
final_processes = get_chrome_processes()
for proc in final_processes:
    cmdline_list = proc['cmdline'].split()
    profile = extract_profile_from_cmdline(cmdline_list)
    user_data = "temp" if "/tmp/chrome_profile2_test" in proc['cmdline'] else "normal"
    print(f"   PID: {proc['pid']}, Profile: {profile}, 数据目录: {user_data}")

print(f"最终Chrome主进程数: {len(final_processes)}")

# 清理临时目录
import shutil
if os.path.exists(temp_user_data_dir):
    try:
        shutil.rmtree(temp_user_data_dir)
        print(f"已清理临时目录: {temp_user_data_dir}")
    except:
        print(f"无法清理临时目录: {temp_user_data_dir}") 