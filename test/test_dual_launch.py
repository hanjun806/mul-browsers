#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试双Profile启动
"""

import subprocess
import time
import psutil

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

print("=== 测试双Profile启动 ===")

print("1. 检查当前Chrome进程:")
initial_processes = get_chrome_processes()
for proc in initial_processes:
    cmdline_list = proc['cmdline'].split()
    profile = extract_profile_from_cmdline(cmdline_list)
    print(f"   PID: {proc['pid']}, Profile: {profile}")

print(f"当前Chrome主进程数: {len(initial_processes)}")

print("\n2. 尝试启动Profile 2...")

# 启动Profile 2
cmd = [
    "open", "-n", "-a", "Google Chrome", "--args",
    "--user-data-dir=/Users/zmj/Library/Application Support/Google/Chrome",
    "--profile-directory=Profile 2",
    "--lang=zh-CN",
    "--window-size=1280,720",
    "--no-first-run",
    "--no-default-browser-check",
    "--new-window"
]

print(f"启动命令: {' '.join(cmd)}")

try:
    process = subprocess.Popen(cmd, 
                             stdout=subprocess.PIPE, 
                             stderr=subprocess.PIPE)
    
    print(f"启动进程PID: {process.pid}")
    
    # 等待Chrome启动
    print("等待Chrome启动...")
    for i in range(10):
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
            if process.poll() is not None:
                stdout, stderr = process.communicate()
                print(f"启动进程已退出，返回码: {process.returncode}")
                if stdout:
                    print(f"stdout: {stdout.decode()}")
                if stderr:
                    print(f"stderr: {stderr.decode()}")
                break
        except:
            pass
        
        print()

except Exception as e:
    print(f"启动失败: {e}")

print("\n3. 最终状态:")
final_processes = get_chrome_processes()
for proc in final_processes:
    cmdline_list = proc['cmdline'].split()
    profile = extract_profile_from_cmdline(cmdline_list)
    print(f"   PID: {proc['pid']}, Profile: {profile}")

print(f"最终Chrome主进程数: {len(final_processes)}") 