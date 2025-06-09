#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
全面的Profile环境测试脚本
扫描所有Profile并依次启动测试，诊断问题
"""

import os
import time
import psutil
from typing import List, Dict
from core.browser_manager import BrowserManager
from core.profile_manager import ProfileManager

class ProfileTester:
    def __init__(self):
        self.bm = BrowserManager()
        self.pm = ProfileManager()
        self.test_results = {}
        
    def scan_all_profiles(self) -> List:
        """扫描所有可用的Profile"""
        print("=== 扫描系统中的所有Profile ===")
        profiles = self.pm.scan_profiles()
        
        print(f"发现 {len(profiles)} 个Profile:")
        for i, profile in enumerate(profiles, 1):
            print(f"  {i:2d}. {profile.display_name} ({profile.name})")
            print(f"      路径: {profile.path}")
            print(f"      是否默认: {profile.is_default}")
            
            # 检查Profile目录状态
            if os.path.exists(profile.path):
                try:
                    files = os.listdir(profile.path)
                    important_files = ['Preferences', 'History', 'Bookmarks', 'Cookies']
                    existing_files = [f for f in important_files if f in files]
                    print(f"      重要文件: {existing_files}")
                except Exception as e:
                    print(f"      无法读取目录: {e}")
            else:
                print(f"      ⚠️  Profile目录不存在")
            print()
        
        return profiles
    
    def get_current_chrome_processes(self) -> List[Dict]:
        """获取当前所有Chrome主进程"""
        chrome_processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time', 'memory_info']):
            try:
                if proc.info['name'] == 'Google Chrome':
                    cmdline = proc.info['cmdline']
                    if cmdline and not any('--type=' in arg for arg in cmdline):
                        # 提取用户数据目录
                        user_data_dir = "unknown"
                        cmdline_str = ' '.join(cmdline)
                        if '--user-data-dir=' in cmdline_str:
                            start = cmdline_str.find('--user-data-dir=') + len('--user-data-dir=')
                            end = cmdline_str.find(' ', start)
                            if end == -1:
                                end = len(cmdline_str)
                            user_data_dir = cmdline_str[start:end]
                        
                        chrome_processes.append({
                            'pid': proc.info['pid'],
                            'cmdline': cmdline,
                            'cmdline_str': cmdline_str,
                            'user_data_dir': user_data_dir,
                            'create_time': proc.info['create_time'],
                            'memory_mb': round(proc.info['memory_info'].rss / 1024 / 1024, 1)
                        })
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        
        return chrome_processes
    
    def print_chrome_status(self, title: str):
        """打印当前Chrome进程状态"""
        print(f"\n=== {title} ===")
        processes = self.get_current_chrome_processes()
        
        if not processes:
            print("没有找到Chrome主进程")
        else:
            print(f"发现 {len(processes)} 个Chrome主进程:")
            for i, proc in enumerate(processes, 1):
                print(f"  {i}. PID: {proc['pid']}")
                print(f"     内存: {proc['memory_mb']} MB")
                print(f"     用户数据目录: {proc['user_data_dir']}")
                print(f"     启动时间: {time.strftime('%H:%M:%S', time.localtime(proc['create_time']))}")
                print()
    
    def test_single_profile(self, profile, test_index: int, total_tests: int) -> Dict:
        """测试单个Profile的启动"""
        print(f"\n{'='*60}")
        print(f"测试 {test_index}/{total_tests}: {profile.display_name} ({profile.name})")
        print(f"{'='*60}")
        
        # 记录测试开始时间
        start_time = time.time()
        
        # 检查Profile是否已经在运行
        if self.bm.is_browser_running(profile.name):
            print(f"⚠️  Profile {profile.display_name} 已经在运行中")
            return {
                'status': 'already_running',
                'message': 'Profile已经在运行',
                'duration': 0
            }
        
        # 记录启动前的Chrome进程
        before_processes = self.get_current_chrome_processes()
        print(f"启动前Chrome进程数: {len(before_processes)}")
        
        # 尝试启动Profile
        print(f"🚀 正在启动 {profile.display_name}...")
        success = self.bm.start_browser(
            profile, 
            language='zh-CN', 
            window_size=(1280, 720)
        )
        
        # 计算启动耗时
        duration = time.time() - start_time
        
        # 等待一段时间让Chrome稳定
        if success:
            print("⏳ 等待Chrome稳定...")
            time.sleep(3)
        
        # 记录启动后的Chrome进程
        after_processes = self.get_current_chrome_processes()
        new_processes = [p for p in after_processes if p['pid'] not in [bp['pid'] for bp in before_processes]]
        
        print(f"启动后Chrome进程数: {len(after_processes)}")
        print(f"新增进程数: {len(new_processes)}")
        
        if success:
            if new_processes:
                new_proc = new_processes[0]
                print(f"✅ 启动成功!")
                print(f"   PID: {new_proc['pid']}")
                print(f"   用户数据目录: {new_proc['user_data_dir']}")
                print(f"   内存使用: {new_proc['memory_mb']} MB")
                print(f"   启动耗时: {duration:.1f}秒")
                
                return {
                    'status': 'success',
                    'pid': new_proc['pid'],
                    'user_data_dir': new_proc['user_data_dir'],
                    'memory_mb': new_proc['memory_mb'],
                    'duration': duration,
                    'message': '启动成功'
                }
            else:
                print(f"⚠️  启动成功但未检测到新Chrome进程")
                return {
                    'status': 'success_no_new_process',
                    'duration': duration,
                    'message': '启动成功但未检测到新进程'
                }
        else:
            print(f"❌ 启动失败")
            print(f"   启动耗时: {duration:.1f}秒")
            
            return {
                'status': 'failed',
                'duration': duration,
                'message': '启动失败'
            }
    
    def test_all_profiles(self, delay_between_tests: int = 5):
        """测试所有Profile的启动"""
        profiles = self.scan_all_profiles()
        
        if not profiles:
            print("没有找到任何Profile，测试结束")
            return
        
        # 显示初始Chrome状态
        self.print_chrome_status("测试开始前的Chrome进程状态")
        
        # 依次测试每个Profile
        total_tests = len(profiles)
        for i, profile in enumerate(profiles, 1):
            # 测试单个Profile
            result = self.test_single_profile(profile, i, total_tests)
            self.test_results[profile.name] = {
                'profile': profile,
                'result': result
            }
            
            # 如果不是最后一个测试，等待一段时间
            if i < total_tests:
                print(f"\n⏳ 等待 {delay_between_tests} 秒后测试下一个Profile...")
                time.sleep(delay_between_tests)
        
        # 显示最终状态
        self.print_chrome_status("所有测试完成后的Chrome进程状态")
        
        # 生成测试报告
        self.generate_test_report()
    
    def generate_test_report(self):
        """生成测试报告"""
        print(f"\n{'='*80}")
        print("测试报告")
        print(f"{'='*80}")
        
        success_count = 0
        failed_count = 0
        already_running_count = 0
        
        print(f"{'Profile名称':<20} {'状态':<15} {'PID':<8} {'内存(MB)':<10} {'耗时(秒)':<8} {'说明'}")
        print("-" * 80)
        
        for profile_name, test_data in self.test_results.items():
            profile = test_data['profile']
            result = test_data['result']
            
            status = result['status']
            pid = result.get('pid', '-')
            memory = result.get('memory_mb', '-')
            duration = f"{result['duration']:.1f}" if result['duration'] > 0 else '-'
            message = result['message']
            
            # 状态图标
            if status == 'success':
                status_icon = "✅ 成功"
                success_count += 1
            elif status == 'failed':
                status_icon = "❌ 失败"
                failed_count += 1
            elif status == 'already_running':
                status_icon = "⚠️  已运行"
                already_running_count += 1
            else:
                status_icon = "❓ 未知"
            
            print(f"{profile.display_name:<20} {status_icon:<15} {pid:<8} {memory:<10} {duration:<8} {message}")
        
        print("-" * 80)
        print(f"总计: {len(self.test_results)} 个Profile")
        print(f"✅ 成功启动: {success_count}")
        print(f"❌ 启动失败: {failed_count}")
        print(f"⚠️  已在运行: {already_running_count}")
        
        # 显示运行中的实例
        running_instances = list(self.bm.running_instances.keys())
        print(f"\n当前Browser Manager中的运行实例: {len(running_instances)}")
        for instance in running_instances:
            print(f"  - {instance}")
        
        # 问题分析
        if failed_count > 0:
            print(f"\n{'='*40}")
            print("失败原因分析")
            print(f"{'='*40}")
            
            for profile_name, test_data in self.test_results.items():
                if test_data['result']['status'] == 'failed':
                    profile = test_data['profile']
                    print(f"\n❌ {profile.display_name} ({profile.name}):")
                    print(f"   - 检查Profile目录是否完整: {profile.path}")
                    print(f"   - 检查是否有权限访问Profile目录")
                    print(f"   - 检查Chrome是否正确安装")
                    print(f"   - 查看系统日志获取更多信息")
        
        print(f"\n测试完成! 🎉")

def main():
    """主函数"""
    print("Chrome Profile 全面测试工具")
    print("=" * 50)
    
    # 检查Chrome是否安装
    tester = ProfileTester()
    
    if not tester.bm.chrome_executable:
        print("❌ 错误: 未找到Chrome可执行文件")
        print("请确保Chrome已正确安装")
        return
    
    print(f"✅ Chrome可执行文件: {tester.bm.chrome_executable}")
    
    # 开始测试
    try:
        tester.test_all_profiles(delay_between_tests=3)
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被用户中断")
        tester.print_chrome_status("中断时的Chrome进程状态")
    except Exception as e:
        print(f"\n\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 