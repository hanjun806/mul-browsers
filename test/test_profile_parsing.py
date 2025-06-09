#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试Profile名称解析逻辑
"""

import re

def test_profile_parsing():
    # 模拟真实的命令行参数
    cmdline = [
        '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
        '--user-data-dir=/Users/zmj/Library/Application Support/Google/Chrome',
        '--profile-directory=Profile 1',
        '--lang=zh-CN',
        '--window-size=1280,720',
        '--no-first-run',
        '--no-default-browser-check',
        '--new-window'
    ]
    
    cmdline_str = ' '.join(cmdline)
    
    print("=== 测试Profile名称解析 ===")
    print(f"命令行字符串: {cmdline_str}")
    print()
    
    # 测试当前的正则表达式
    print("1. 测试正则表达式方法:")
    
    # 先尝试匹配带引号的情况: --profile-directory="Profile 1"
    profile_match = re.search(r'--profile-directory[=\s]+"([^"]+)"', cmdline_str)
    if profile_match:
        profile_name = profile_match.group(1)
        print(f"   带引号匹配成功: {profile_name}")
    else:
        print("   带引号匹配失败")
        
        # 再尝试匹配不带引号但用等号的情况: --profile-directory=Profile 1
        profile_match = re.search(r'--profile-directory=([^\s]+(?:\\\s[^\s]*)*)', cmdline_str)
        if profile_match:
            profile_name = profile_match.group(1)
            profile_name = profile_name.replace('\\ ', ' ')
            print(f"   等号+转义匹配成功: {profile_name}")
        else:
            print("   等号+转义匹配失败")
            
            # 最后尝试更简单的方法：匹配到空格前
            profile_match = re.search(r'--profile-directory=([^\s]+)', cmdline_str)
            if profile_match:
                profile_name = profile_match.group(1)
                print(f"   简单等号匹配成功: {profile_name} (这就是问题所在!)")
            else:
                print("   简单等号匹配失败")
    
    print()
    print("2. 测试命令行数组方法:")
    
    profile_name = None
    for i, arg in enumerate(cmdline):
        if arg == '--profile-directory' and i + 1 < len(cmdline):
            profile_name = cmdline[i + 1]
            print(f"   分离参数匹配成功: {profile_name}")
            break
        elif arg.startswith('--profile-directory='):
            profile_name = arg.split('=', 1)[1]
            print(f"   等号连接匹配成功: {profile_name}")
            break
    
    if not profile_name:
        print("   命令行数组方法匹配失败")
    
    print()
    print("3. 正确的正则表达式应该是:")
    
    # 正确的正则表达式，处理等号后面有空格的情况
    profile_match = re.search(r'--profile-directory=(.+?)(?:\s--|\s-[^-]|$)', cmdline_str)
    if profile_match:
        profile_name = profile_match.group(1).strip()
        print(f"   改进正则匹配成功: {profile_name}")
    else:
        print("   改进正则匹配失败")

if __name__ == "__main__":
    test_profile_parsing() 