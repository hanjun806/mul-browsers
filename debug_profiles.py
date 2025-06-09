#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试Chrome Profile信息
用于查看Profile名称存储的具体位置
"""

import os
import json
import platform

def debug_chrome_profiles():
    """调试Chrome Profile信息"""
    
    # 获取Chrome用户数据目录
    system = platform.system()
    if system == "Darwin":  # macOS
        chrome_dir = os.path.expanduser("~/Library/Application Support/Google/Chrome")
    elif system == "Windows":
        appdata = os.environ.get('LOCALAPPDATA', '')
        chrome_dir = os.path.join(appdata, 'Google', 'Chrome', 'User Data')
    else:  # Linux
        chrome_dir = os.path.expanduser("~/.config/google-chrome")
    
    if not os.path.exists(chrome_dir):
        print(f"Chrome目录不存在: {chrome_dir}")
        return
    
    print(f"Chrome用户数据目录: {chrome_dir}")
    print("=" * 60)
    
    # 读取Local State文件
    local_state_file = os.path.join(chrome_dir, "Local State")
    if os.path.exists(local_state_file):
        print("\n📄 Local State 文件内容:")
        try:
            with open(local_state_file, 'r', encoding='utf-8') as f:
                local_state = json.load(f)
            
            # 显示Profile信息缓存
            profile_info_cache = local_state.get('profile', {}).get('info_cache', {})
            print(f"找到 {len(profile_info_cache)} 个Profile缓存:")
            
            for profile_key, profile_data in profile_info_cache.items():
                print(f"\n  Profile Key: {profile_key}")
                print(f"    名称 (name): {profile_data.get('name', 'N/A')}")
                print(f"    用户名 (user_name): {profile_data.get('user_name', 'N/A')}")
                print(f"    Gaia名称 (gaia_name): {profile_data.get('gaia_name', 'N/A')}")
                print(f"    给定名称 (gaia_given_name): {profile_data.get('gaia_given_name', 'N/A')}")
                print(f"    邮箱 (gaia_id): {profile_data.get('gaia_id', 'N/A')}")
                
        except Exception as e:
            print(f"读取Local State文件出错: {e}")
    
    # 扫描各个Profile目录
    print(f"\n📁 Profile目录扫描:")
    
    # 检查默认Profile
    default_profile = os.path.join(chrome_dir, "Default")
    if os.path.exists(default_profile):
        print(f"\n  📂 Default Profile:")
        debug_profile_preferences(default_profile)
    
    # 检查其他Profile
    for item in os.listdir(chrome_dir):
        if item.startswith("Profile "):
            profile_path = os.path.join(chrome_dir, item)
            if os.path.isdir(profile_path):
                print(f"\n  📂 {item}:")
                debug_profile_preferences(profile_path)

def debug_profile_preferences(profile_path):
    """调试单个Profile的Preferences文件"""
    prefs_file = os.path.join(profile_path, "Preferences")
    
    if not os.path.exists(prefs_file):
        print("    ❌ Preferences文件不存在")
        return
    
    try:
        with open(prefs_file, 'r', encoding='utf-8') as f:
            prefs = json.load(f)
        
        print(f"    路径: {profile_path}")
        
        # 检查profile部分
        profile_section = prefs.get('profile', {})
        print(f"    Profile.name: {profile_section.get('name', 'N/A')}")
        print(f"    Profile.local_profile_name: {profile_section.get('local_profile_name', 'N/A')}")
        print(f"    Profile.user_name: {profile_section.get('user_name', 'N/A')}")
        
        # 检查account_info部分
        account_info = prefs.get('account_info', {})
        print(f"    Account.full_name: {account_info.get('full_name', 'N/A')}")
        print(f"    Account.given_name: {account_info.get('given_name', 'N/A')}")
        
        # 检查signin部分
        signin_info = prefs.get('signin', {})
        print(f"    Signin.allowed_username: {signin_info.get('allowed_username', 'N/A')}")
        
        # 检查Google服务
        google_services = prefs.get('google', {}).get('services', {})
        print(f"    Google.signin_scoped_device_id: {google_services.get('signin_scoped_device_id', 'N/A')}")
        
    except Exception as e:
        print(f"    ❌ 读取Preferences出错: {e}")

if __name__ == "__main__":
    debug_chrome_profiles() 